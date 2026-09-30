import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import request, g


# ---------------------------------------------------------
# SECRET KEY
# ---------------------------------------------------------

SECRET_KEY = os.environ.get(
    "EXAM_PORTAL_SECRET",
    "susl-exam-portal-secret-key"
)


# ---------------------------------------------------------
# BASE64 FUNCTIONS
# ---------------------------------------------------------

def base64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def base64url_decode(data):
    padding = "=" * (-len(data) % 4)

    return base64.urlsafe_b64decode(
        data + padding
    )


# ---------------------------------------------------------
# CREATE TOKEN
# ---------------------------------------------------------

def create_token(user):
    now = datetime.now(timezone.utc)

    payload = {
        "user_id": user["id"],
        "email": user["email"],
        "role": user["role"],
        "exp": int(
            (now + timedelta(hours=8)).timestamp()
        )
    }

    header = {
        "alg": "HS256",
        "typ": "JWT"
    }

    header_text = base64url_encode(
        json.dumps(
            header,
            separators=(",", ":")
        ).encode()
    )

    payload_text = base64url_encode(
        json.dumps(
            payload,
            separators=(",", ":")
        ).encode()
    )

    message = (
        header_text +
        "." +
        payload_text
    )

    signature = hmac.new(
        SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).digest()

    signature_text = base64url_encode(signature)

    return (
        message +
        "." +
        signature_text
    )


# ---------------------------------------------------------
# VERIFY TOKEN
# ---------------------------------------------------------

def verify_token(token):
    try:
        parts = token.split(".")

        if len(parts) != 3:
            return None

        header_text = parts[0]
        payload_text = parts[1]
        signature_text = parts[2]

        message = (
            header_text +
            "." +
            payload_text
        )

        expected_signature = hmac.new(
            SECRET_KEY.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()

        actual_signature = base64url_decode(
            signature_text
        )

        if not hmac.compare_digest(
            expected_signature,
            actual_signature
        ):
            return None

        payload = json.loads(
            base64url_decode(
                payload_text
            ).decode()
        )

        if "exp" not in payload:
            return None

        current_time = datetime.now(
            timezone.utc
        ).timestamp()

        if current_time > payload["exp"]:
            return None

        return payload

    except Exception:
        return None


# ---------------------------------------------------------
# GET TOKEN FROM REQUEST
# ---------------------------------------------------------

def get_token_from_request():
    authorization = request.headers.get(
        "Authorization",
        ""
    ).strip()

    if not authorization:
        return None

    parts = authorization.split(None, 1)

    if len(parts) != 2:
        return None

    scheme = parts[0].lower()
    token = parts[1].strip()

    if scheme != "bearer":
        return None

    if not token:
        return None

    return token


# ---------------------------------------------------------
# AUTHENTICATION DECORATOR
# ---------------------------------------------------------

def require_auth(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        from database import get_db

        token = get_token_from_request()

        if not token:
            return jsonify_response(
                "Authentication required.",
                401
            )

        payload = verify_token(token)

        if not payload:
            return jsonify_response(
                "Invalid or expired token.",
                401
            )

        user_id = payload.get("user_id")

        if not user_id:
            return jsonify_response(
                "Invalid token.",
                401
            )

        db = get_db()

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
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()

        if user is None:
            return jsonify_response(
                "User not found.",
                401
            )

        user_data = dict(user)

        user_data["sub"] = user_data["id"]

        g.current_user = user_data

        return func(*args, **kwargs)

    return wrapper


# ---------------------------------------------------------
# ROLE DECORATOR
# ---------------------------------------------------------

def require_role(required_role):

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            user = getattr(
                g,
                "current_user",
                None
            )

            if not user:
                return jsonify_response(
                    "Authentication required.",
                    401
                )

            actual_role = str(
                user.get("role", "")
            ).lower()

            expected_role = str(
                required_role
            ).lower()

            if actual_role != expected_role:
                return jsonify_response(
                    f"Only {required_role}s can access this endpoint.",
                    403
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator


# ---------------------------------------------------------
# JSON RESPONSE HELPER
# ---------------------------------------------------------

def jsonify_response(message, status_code):
    from flask import jsonify

    return jsonify({
        "success": False,
        "message": message
    }), status_code