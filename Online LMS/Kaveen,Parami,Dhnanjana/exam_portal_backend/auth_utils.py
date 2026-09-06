"""
auth_utils.py
-------------
A minimal signed-token auth scheme, used in place of Flask-JWT-Extended
(which needs `pip install` access this sandbox doesn't have). It's a real
HMAC-signed, expiring token -- not a toy -- just implemented with the
standard library instead of PyJWT. Swapping in real JWTs later only
touches this file.
"""
import base64
import hashlib
import hmac
import json
import time
from functools import wraps
from flask import request, jsonify

SECRET_KEY = "susl-exam-portal-dev-secret-change-me"
TOKEN_TTL_SECONDS = 60 * 60 * 8  # 8 hour session


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_token(user_id: int, role: str, full_name: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "name": full_name,
        "exp": int(time.time()) + TOKEN_TTL_SECONDS,
    }
    payload_b64 = _b64encode(json.dumps(payload).encode())
    signature = hmac.new(SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{signature}"


def decode_token(token: str):
    try:
        payload_b64, signature = token.split(".")
        expected_sig = hmac.new(SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None
        payload = json.loads(_b64decode(payload_b64))
        if payload["exp"] < time.time():
            return None
        return payload
    except Exception:
        return None


def require_role(*allowed_roles):
    """Decorator: validates the Authorization: Bearer <token> header and role."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return jsonify({"error": "Missing or invalid Authorization header"}), 401
            token = auth_header.split(" ", 1)[1]
            payload = decode_token(token)
            if not payload:
                return jsonify({"error": "Invalid or expired token"}), 401
            if allowed_roles and payload["role"] not in allowed_roles:
                return jsonify({"error": "Forbidden: insufficient role"}), 403
            request.user = payload  # {sub, role, name, exp}
            return fn(*args, **kwargs)
        return wrapper
    return decorator
