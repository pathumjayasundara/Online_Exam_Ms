from flask import Blueprint, request, jsonify

from database import get_db, verify_password
from auth_utils import create_token


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/auth"
)


# =========================================================
# LOGIN
# =========================================================

@auth_bp.route("/login", methods=["POST"])
def login():

    # -----------------------------------------------------
    # GET REQUEST DATA
    # -----------------------------------------------------

    data = request.get_json(
        silent=True
    ) or {}

    email = str(
        data.get("email", "")
    ).strip().lower()

    password = data.get(
        "password",
        ""
    )

    # -----------------------------------------------------
    # VALIDATE EMAIL
    # -----------------------------------------------------

    if not email:
        return jsonify({
            "success": False,
            "message": "Email is required."
        }), 400

    # -----------------------------------------------------
    # VALIDATE PASSWORD
    # -----------------------------------------------------

    if not password:
        return jsonify({
            "success": False,
            "message": "Password is required."
        }), 400

    # -----------------------------------------------------
    # CONNECT TO DATABASE
    # -----------------------------------------------------

    db = get_db()

    # -----------------------------------------------------
    # FIND USER
    # -----------------------------------------------------

    user = db.execute(
        """
        SELECT
            id,
            name,
            email,
            password_hash,
            role,
            department
        FROM users
        WHERE LOWER(email) = ?
        """,
        (email,)
    ).fetchone()

    # -----------------------------------------------------
    # USER NOT FOUND
    # -----------------------------------------------------

    if user is None:

        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401

    # -----------------------------------------------------
    # VERIFY PASSWORD
    # -----------------------------------------------------

    password_ok = verify_password(
        password,
        user["password_hash"]
    )

    # -----------------------------------------------------
    # INVALID PASSWORD
    # -----------------------------------------------------

    if not password_ok:

        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401

    # -----------------------------------------------------
    # CHECK USER ROLE
    # -----------------------------------------------------

    if str(user["role"]).lower() != "lecturer":

        return jsonify({
            "success": False,
            "message": "Only lecturers can access this portal."
        }), 403

    # -----------------------------------------------------
    # CREATE LOGIN TOKEN
    # -----------------------------------------------------

    token = create_token(user)

    # -----------------------------------------------------
    # SUCCESS RESPONSE
    # -----------------------------------------------------

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "token": token,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "department": user["department"]
        }
    }), 200