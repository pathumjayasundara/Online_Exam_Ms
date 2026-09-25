"""
Shared auth endpoints (not Team 02-specific, but the Student Module needs
them to exist for register/verify/login to work end to end).

Student ID format enforced here matches the frontend:
2-digit intake year + 3-letter programme code + 4-digit number, e.g. 22APP5678.
"""
import random
import re
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db
from models import EmailVerification, User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

STUDENT_ID_RE = re.compile(r"^(\d{2})([A-Za-z]{3})(\d{4})$")

# TODO: wire up Flask-Mail (or any SMTP/API provider) here.
# from flask_mail import Message
# from extensions import mail
def send_verification_email(to_email, token):
    """Send the 6-digit confirmation code. Currently just logs it — replace
    with a real Flask-Mail call before going to production."""
    print(f"[DEV] Verification token for {to_email}: {token}")


@auth_bp.post("/register")
def register():
    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    student_id = (data.get("studentId") or "").strip().upper()
    password = data.get("password") or ""

    if not all([name, email, student_id, password]):
        return jsonify(error="All fields are required."), 400
    m = STUDENT_ID_RE.match(student_id)
    if not m:
        return jsonify(error="Student ID must look like 22APP5678."), 400
    if User.query.filter((User.email == email) | (User.student_id == student_id)).first():
        return jsonify(error="An account with this email or student ID already exists."), 409

    user = User(
        role="student", full_name=name, email=email,
        password_hash=generate_password_hash(password),
        student_id=student_id, is_active=False,
        intake_year="20" + m.group(1), programme_code=m.group(2).upper(),
    )
    db.session.add(user)
    db.session.flush()  # get user.id before commit

    token = f"{random.randint(0, 999999):06d}"
    db.session.add(EmailVerification(
        user_id=user.id, token=token,
        expires_at=datetime.utcnow() + timedelta(minutes=15),
    ))
    db.session.commit()

    send_verification_email(email, token)
    return jsonify(message="Confirmation code sent."), 201


@auth_bp.post("/verify")
def verify():
    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").strip().lower()
    token = (data.get("token") or "").strip()

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify(error="No pending registration for this email."), 404

    verification = (
        EmailVerification.query.filter_by(user_id=user.id, token=token, consumed=False)
        .order_by(EmailVerification.id.desc()).first()
    )
    if not verification or verification.expires_at < datetime.utcnow():
        return jsonify(error="Incorrect or expired code."), 400

    verification.consumed = True
    user.is_active = True
    db.session.commit()
    return jsonify(message="Account confirmed. You can now log in."), 200


@auth_bp.post("/login")
def login():
    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    student_id = (data.get("studentId") or "").strip().upper()

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify(error="Invalid email or password."), 401
    if student_id and user.student_id != student_id:
        return jsonify(error="Student ID does not match this account."), 401
    if not user.is_active:
        return jsonify(error="Please confirm your email before logging in."), 403

    # Identity is the DB user id — every /api/student/* route resolves the
    # current student from this, never from a value the client can spoof.
    access_token = create_access_token(identity=user.id)
    return jsonify(access_token=access_token, role=user.role), 200
