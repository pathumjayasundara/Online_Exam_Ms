import random
import re
import secrets
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash

from database import get_db, verify_password
from auth_utils import create_token

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

STUDENT_ID_RE = re.compile(r"^(\d{2})([A-Za-z]{3})(\d{4})$")
OTP_TTL_MINUTES = 5
OTP_MAX_ATTEMPTS = 5


# NOTE: no SMTP/email provider is configured in this project, so codes are
# logged server-side AND returned to the caller as `devCode` so the demo
# works end to end without a mail server. Wire a real provider before going
# to production and drop `devCode` from every response — see README.
def send_email(to_email, label, code):
    print(f"[DEV] {label} for {to_email}: {code}")


def _log(db, category, title, text):
    db.execute(
        "INSERT INTO activity_log (category, title, text) VALUES (?, ?, ?)",
        (category, title, text),
    )


def _public_user(row):
    return {
        "id": row["id"], "name": row["full_name"], "email": row["email"], "role": row["role"],
        "studentId": row["student_id"], "department": row["department"],
    }


@auth_bp.post("/register")
def register():
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    student_id = (data.get("studentId") or "").strip().upper()
    password = data.get("password") or ""

    if not all([name, email, student_id, password]):
        return jsonify(error="All fields are required."), 400
    m = STUDENT_ID_RE.match(student_id)
    if not m:
        return jsonify(error="Student ID must look like 22APP5678."), 400
    if len(password) < 8:
        return jsonify(error="Password must be at least 8 characters."), 400

    db = get_db()
    if db.execute(
        "SELECT id FROM users WHERE email = ? OR student_id = ?", (email, student_id)
    ).fetchone():
        return jsonify(error="An account with this email or student ID already exists."), 409

    reg_no = f"20{m.group(1)}/{m.group(2).upper()}/{student_id[-4:]}"
    cur = db.execute(
        """
        INSERT INTO users
            (role, full_name, email, password_hash, is_active, status, student_id,
             intake_year, programme_code, registration_no, degree_programme, faculty, department)
        VALUES ('student', ?, ?, ?, 0, 'Active', ?, ?, ?, ?, ?, ?, ?)
        """,
        (name, email, generate_password_hash(password), student_id,
         "20" + m.group(1), m.group(2).upper(), reg_no,
         "BSc (Hons) in Computer Science & Technology",
         "Faculty of Applied Sciences", "Dept. of Physical Sciences & Technology"),
    )
    user_id = cur.lastrowid

    token = f"{random.randint(0, 999999):06d}"
    db.execute(
        "INSERT INTO email_verifications (user_id, token, expires_at) VALUES (?, ?, ?)",
        (user_id, token, (datetime.utcnow() + timedelta(minutes=15)).isoformat()),
    )
    db.commit()

    send_email(email, "Verification token", token)
    return jsonify(message="Confirmation code sent.", devCode=token), 201


@auth_bp.post("/verify")
def verify():
    data = request.get_json(force=True, silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    token = (data.get("token") or "").strip()

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not user:
        return jsonify(error="No pending registration for this email."), 404

    verification = db.execute(
        """
        SELECT * FROM email_verifications
        WHERE user_id = ? AND token = ? AND consumed = 0
        ORDER BY id DESC LIMIT 1
        """,
        (user["id"], token),
    ).fetchone()

    if not verification or datetime.fromisoformat(verification["expires_at"]) < datetime.utcnow():
        return jsonify(error="Incorrect or expired code."), 400

    db.execute("UPDATE email_verifications SET consumed = 1 WHERE id = ?", (verification["id"],))
    db.execute("UPDATE users SET is_active = 1 WHERE id = ?", (user["id"],))
    _log(db, "cyan", "Student account added", f"Registration: {user['student_id']}")
    db.commit()
    return jsonify(message="Account confirmed. You can now log in."), 200


@auth_bp.post("/login")
def login():
    data = request.get_json(force=True, silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    student_id = (data.get("studentId") or "").strip().upper()
    want_role = (data.get("role") or "").strip().lower()  # optional: restrict to a role, e.g. "admin"

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    if not user or not verify_password(password, user["password_hash"]):
        return jsonify(error="Invalid email or password."), 401
    if want_role and user["role"] != want_role:
        return jsonify(error=f"This account is not a {want_role} account."), 403
    if student_id and (user["student_id"] or "") != student_id:
        return jsonify(error="Student ID does not match this account."), 401
    if not user["is_active"]:
        return jsonify(error="Please confirm your email before logging in."), 403
    if user["status"] == "Suspended":
        return jsonify(error="This account has been suspended. Contact the administrator."), 403

    token = create_token(user)
    return jsonify(token=token, access_token=token, role=user["role"], user=_public_user(user)), 200


@auth_bp.post("/forgot-password")
def forgot_password():
    """Always answers the same way whether or not the email exists, so an
    attacker can't use this endpoint to discover registered accounts."""
    data = request.get_json(force=True, silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    generic_message = "If that email is registered, a code has been sent."

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not user:
        return jsonify(message=generic_message), 200

    otp = f"{random.randint(0, 999999):06d}"
    db.execute(
        "INSERT INTO password_resets (user_id, otp, expires_at) VALUES (?, ?, ?)",
        (user["id"], otp, (datetime.utcnow() + timedelta(minutes=OTP_TTL_MINUTES)).isoformat()),
    )
    db.commit()
    send_email(email, "Password-reset OTP", otp)

    return jsonify(message=generic_message, devCode=otp), 200


@auth_bp.post("/verify-otp")
def verify_otp():
    data = request.get_json(force=True, silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    otp = (data.get("otp") or "").strip()

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not user:
        return jsonify(error="Please request a new code."), 404

    pr = db.execute(
        "SELECT * FROM password_resets WHERE user_id = ? AND consumed = 0 ORDER BY id DESC LIMIT 1",
        (user["id"],),
    ).fetchone()

    if not pr:
        return jsonify(error="Please request a new code."), 400
    if datetime.fromisoformat(pr["expires_at"]) < datetime.utcnow():
        return jsonify(error="This code has expired. Please request a new one."), 400
    if pr["attempts"] >= OTP_MAX_ATTEMPTS:
        return jsonify(error="Too many incorrect attempts. Please request a new code."), 429

    if pr["otp"] != otp:
        db.execute("UPDATE password_resets SET attempts = attempts + 1 WHERE id = ?", (pr["id"],))
        db.commit()
        left = OTP_MAX_ATTEMPTS - (pr["attempts"] + 1)
        return jsonify(error=f"Incorrect code. {left} attempt(s) left."), 400

    reset_token = secrets.token_urlsafe(32)
    db.execute(
        "UPDATE password_resets SET verified = 1, reset_token = ? WHERE id = ?",
        (reset_token, pr["id"]),
    )
    db.commit()
    return jsonify(resetToken=reset_token), 200


@auth_bp.post("/reset-password")
def reset_password():
    data = request.get_json(force=True, silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    reset_token = (data.get("resetToken") or "").strip()
    new_password = data.get("newPassword") or ""

    if len(new_password) < 8:
        return jsonify(error="Password must be at least 8 characters."), 400

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not user:
        return jsonify(error="Invalid or expired reset request."), 400

    pr = db.execute(
        """
        SELECT * FROM password_resets
        WHERE user_id = ? AND reset_token = ? AND verified = 1 AND consumed = 0
        ORDER BY id DESC LIMIT 1
        """,
        (user["id"], reset_token),
    ).fetchone()

    if not pr or datetime.fromisoformat(pr["expires_at"]) < datetime.utcnow():
        return jsonify(error="Invalid or expired reset request. Please start again."), 400

    if verify_password(new_password, user["password_hash"]):
        return jsonify(error="Your new password must be different from your old one."), 400

    db.execute("UPDATE users SET password_hash = ? WHERE id = ?",
               (generate_password_hash(new_password), user["id"]))
    db.execute("UPDATE password_resets SET consumed = 1 WHERE id = ?", (pr["id"],))
    db.commit()
    return jsonify(message="Password changed successfully."), 200
