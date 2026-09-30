from flask import Blueprint, request, jsonify, g

from database import get_db, verify_password
from auth_utils import create_token, require_auth


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

    data = request.get_json(silent=True) or {}

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


# =========================================================
# UPDATE ACCOUNT DETAILS
# =========================================================

@auth_bp.route("/profile", methods=["PUT"])
@require_auth
def update_profile():

    # -----------------------------------------------------
    # GET CURRENT LOGGED-IN USER
    # -----------------------------------------------------

    user = g.current_user

    user_id = user["id"]

    # -----------------------------------------------------
    # GET REQUEST DATA
    # -----------------------------------------------------

    data = request.get_json(silent=True) or {}

    name = str(
        data.get("name", "")
    ).strip()

    email = str(
        data.get("email", "")
    ).strip().lower()

    # -----------------------------------------------------
    # VALIDATE NAME
    # -----------------------------------------------------

    if not name:

        return jsonify({
            "success": False,
            "message": "Name is required."
        }), 400

    # -----------------------------------------------------
    # VALIDATE EMAIL
    # -----------------------------------------------------

    if not email:

        return jsonify({
            "success": False,
            "message": "Email is required."
        }), 400

    # -----------------------------------------------------
    # CONNECT TO DATABASE
    # -----------------------------------------------------

    db = get_db()

    # -----------------------------------------------------
    # CHECK WHETHER EMAIL IS ALREADY USED
    # -----------------------------------------------------

    existing_user = db.execute(
        """
        SELECT id
        FROM users
        WHERE LOWER(email) = ?
        AND id != ?
        """,
        (email, user_id)
    ).fetchone()

    if existing_user is not None:

        return jsonify({
            "success": False,
            "message": "This email is already used by another account."
        }), 409

    # -----------------------------------------------------
    # UPDATE USER
    # -----------------------------------------------------

    db.execute(
        """
        UPDATE users
        SET
            name = ?,
            email = ?
        WHERE id = ?
        """,
        (
            name,
            email,
            user_id
        )
    )

    db.commit()

    # -----------------------------------------------------
    # GET UPDATED USER
    # -----------------------------------------------------

    updated_user = db.execute(
        """
        SELECT
            id,
            name,
            email,
            role,
            department
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    # -----------------------------------------------------
    # CHECK UPDATED USER
    # -----------------------------------------------------

    if updated_user is None:

        return jsonify({
            "success": False,
            "message": "User account could not be found."
        }), 404

    # -----------------------------------------------------
    # RETURN UPDATED USER
    # -----------------------------------------------------

    return jsonify({
        "success": True,
        "message": "Account details updated successfully.",
        "user": {
            "id": updated_user["id"],
            "name": updated_user["name"],
            "email": updated_user["email"],
            "role": updated_user["role"],
            "department": updated_user["department"]
        }
    }), 200
