# app/lib/auth/auth_service.py
# Pure-Python auth service. No HTTP dependency — all functions are plain
# synchronous callables returning structured dicts.
# Source of return shape: .planning/codebase/CONVENTIONS.md (success/failure dict)
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from passlib.context import CryptContext

from app.lib.auth.models import User
from app.lib.auth.store import reset_tokens_db, users_db
from config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET

# Module-level bcrypt context (initialised once at import time).
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def register(email: str, password: str) -> dict:
    """Register a new user with email and password.

    Args:
        email: The user's email address.
        password: The user's plain-text password. Stored as a bcrypt hash.

    Returns:
        On success: {"success": True, "data": {"user_id": str, "email": str}}
        On failure: {"success": False, "code": str, "message": str, "retryable": bool}
    """
    # Reject duplicate emails (linear scan — demo scale only).
    for existing_user in users_db.values():
        if existing_user.email == email:
            return {
                "success": False,
                "code": "EMAIL_ALREADY_EXISTS",
                "message": "An account with this email already exists.",
                "retryable": False,
            }

    password_hash = pwd_context.hash(password)
    user = User(
        id=str(uuid4()),
        email=email,
        password_hash=password_hash,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    users_db[user.id] = user
    return {"success": True, "data": {"user_id": user.id, "email": user.email}}


def login(email: str, password: str) -> dict:
    """Authenticate a user and return a JWT on success.

    Never distinguishes between "user not found" and "wrong password" to
    prevent user enumeration (T-02-01).

    Args:
        email: The user's email address.
        password: The user's plain-text password.

    Returns:
        On success: {"success": True, "data": {"token": str, "user_id": str}}
        On failure: {"success": False, "code": "INVALID_CREDENTIALS",
            "message": str, "retryable": bool}
    """
    _invalid = {
        "success": False,
        "code": "INVALID_CREDENTIALS",
        "message": "Invalid email or password",
        "retryable": False,
    }

    # Find user by email (linear scan — demo scale only).
    found_user: User | None = None
    for u in users_db.values():
        if u.email == email:
            found_user = u
            break

    if found_user is None:
        return _invalid

    if not pwd_context.verify(password, found_user.password_hash):
        return _invalid

    payload = {
        "user_id": found_user.id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    token: str = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return {"success": True, "data": {"token": token, "user_id": found_user.id}}


def verify_token(token: str) -> dict:
    """Decode and validate a JWT, returning the embedded user_id.

    Handles both expiry and signature/format errors as structured failures
    (T-02-02).

    Args:
        token: A JWT string previously issued by login().

    Returns:
        On success: {"success": True, "data": {"user_id": str}}
        On failure: {"success": False, "code": str, "message": str, "retryable": bool}
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {"success": True, "data": {"user_id": payload["user_id"]}}
    except jwt.ExpiredSignatureError:
        return {
            "success": False,
            "code": "TOKEN_EXPIRED",
            "message": "Token has expired",
            "retryable": False,
        }
    except jwt.InvalidTokenError:
        return {
            "success": False,
            "code": "INVALID_TOKEN",
            "message": "Token is invalid",
            "retryable": False,
        }


def reset_request(email: str) -> dict:
    """Issue a password-reset token for the given email address.

    Always returns a success response regardless of whether the email exists,
    to prevent user enumeration (T-02-05).

    NOTE: The reset token is returned directly in the response body. This is
    intentional for demo purposes — the app has no email server. In a real
    production system the token would be sent via email and NEVER appear in
    the API response.

    Args:
        email: The email address to issue a reset token for.

    Returns:
        {"success": True, "data": {"token": str | None, "message": str}}
        token is None when the email is not found (message is identical either way).
    """
    token: str | None = None
    # Check if email belongs to a registered user (linear scan — demo scale).
    email_found = any(u.email == email for u in users_db.values())

    if email_found:
        token = str(uuid4())
        reset_tokens_db[email] = {
            "token": token,
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=15),
        }

    return {
        "success": True,
        "data": {
            "token": token,
            "message": "If the email exists, a reset token has been issued",
        },
    }


def reset_confirm(token: str, new_password: str) -> dict:
    """Consume a reset token and update the user's password.

    Expired tokens are deleted on detection and rejected (T-02-06).

    Args:
        token: The UUID reset token previously returned by reset_request().
        new_password: The new plain-text password to set.

    Returns:
        On success: {"success": True, "data": {"message": str}}
        On failure: {"success": False, "code": "INVALID_RESET_TOKEN",
            "message": str, "retryable": bool}
    """
    _invalid = {
        "success": False,
        "code": "INVALID_RESET_TOKEN",
        "message": "Reset token not found or expired",
        "retryable": False,
    }

    # Locate the entry whose token value matches.
    found_email: str | None = None
    for email_key, entry in reset_tokens_db.items():
        if entry["token"] == token:
            found_email = email_key
            break

    if found_email is None:
        return _invalid

    entry = reset_tokens_db[found_email]
    # Enforce expiry (T-02-06).
    if datetime.now(timezone.utc) > entry["expires_at"]:
        del reset_tokens_db[found_email]
        return _invalid

    # Find the user record and update the password hash.
    for user in users_db.values():
        if user.email == found_email:
            user.password_hash = pwd_context.hash(new_password)
            break

    # Consume the token — single use only.
    del reset_tokens_db[found_email]

    return {"success": True, "data": {"message": "Password updated successfully"}}
