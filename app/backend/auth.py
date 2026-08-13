"""Minimal auth: password hashing (stdlib pbkdf2) + signed session tokens
(itsdangerous-free HMAC). No JWT lib needed for one office platform."""
import base64
import hashlib
import hmac
import json
import os
from fastapi import Depends, HTTPException, Header

from . import db

_SECRET = os.environ.get("APP_SECRET", "dev-insecure-change-me").encode()


def hash_password(pw: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 200_000)
    return base64.b64encode(salt).decode() + ":" + base64.b64encode(dk).decode()


def verify_password(pw: str, stored: str) -> bool:
    try:
        salt_b64, dk_b64 = stored.split(":")
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(dk_b64)
        dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 200_000)
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False


def make_token(user_id: str) -> str:
    payload = base64.urlsafe_b64encode(json.dumps({"uid": user_id}).encode()).decode()
    sig = hmac.new(_SECRET, payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def _verify_token(token: str) -> str | None:
    try:
        payload, sig = token.split(".")
        expected = hmac.new(_SECRET, payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        return json.loads(base64.urlsafe_b64decode(payload)).get("uid")
    except Exception:
        return None


def current_user(authorization: str = Header(default="")) -> dict:
    token = authorization[7:] if authorization.startswith("Bearer ") else authorization
    uid = _verify_token(token)
    if not uid:
        raise HTTPException(401, "Not authenticated")
    user = db.q_one("SELECT * FROM users WHERE id=?", (uid,))
    if not user:
        raise HTTPException(401, "Unknown user")
    return user


def require_role(*roles: str):
    def dep(user: dict = Depends(current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(403, f"Requires role: {', '.join(roles)}")
        return user
    return dep
