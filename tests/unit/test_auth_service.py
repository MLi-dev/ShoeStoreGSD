# tests/unit/test_auth_service.py
# TDD tests for auth_service.py (Task 3, Plan 02-01).
# Tests cover register, login, verify_token, reset_request, reset_confirm.
import pytest


# ---------------------------------------------------------------------------
# register()
# ---------------------------------------------------------------------------


def test_register_returns_success_with_user_id_and_email():
    from app.lib.auth.store import users_db
    from app.lib.auth.auth_service import register

    users_db.clear()
    result = register("new@example.com", "password123")
    assert result["success"] is True
    assert "user_id" in result["data"]
    assert result["data"]["email"] == "new@example.com"
    users_db.clear()


def test_register_stores_password_as_bcrypt_hash():
    from app.lib.auth.store import users_db
    from app.lib.auth.auth_service import register
    from passlib.context import CryptContext

    users_db.clear()
    register("hash@example.com", "mypassword")
    user = next(u for u in users_db.values() if u.email == "hash@example.com")
    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    assert pwd_ctx.verify("mypassword", user.password_hash)
    users_db.clear()


def test_register_rejects_duplicate_email():
    from app.lib.auth.store import users_db
    from app.lib.auth.auth_service import register

    users_db.clear()
    register("dupe@example.com", "pass1")
    result = register("dupe@example.com", "pass2")
    assert result["success"] is False
    assert result["code"] == "EMAIL_ALREADY_EXISTS"
    assert result["retryable"] is False
    users_db.clear()


def test_register_never_returns_password_hash():
    from app.lib.auth.store import users_db
    from app.lib.auth.auth_service import register

    users_db.clear()
    result = register("safe@example.com", "secret")
    assert "password_hash" not in str(result)
    users_db.clear()


# ---------------------------------------------------------------------------
# login()
# ---------------------------------------------------------------------------


def test_login_returns_token_on_valid_credentials():
    from app.lib.auth.store import users_db
    from app.lib.auth.auth_service import register, login

    users_db.clear()
    register("login@example.com", "goodpass")
    result = login("login@example.com", "goodpass")
    assert result["success"] is True
    assert "token" in result["data"]
    assert "user_id" in result["data"]
    users_db.clear()


def test_login_rejects_wrong_password():
    from app.lib.auth.store import users_db
    from app.lib.auth.auth_service import register, login

    users_db.clear()
    register("wp@example.com", "rightpass")
    result = login("wp@example.com", "wrongpass")
    assert result["success"] is False
    assert result["code"] == "INVALID_CREDENTIALS"
    assert result["retryable"] is False
    users_db.clear()


def test_login_rejects_unknown_email():
    from app.lib.auth.store import users_db
    from app.lib.auth.auth_service import login

    users_db.clear()
    result = login("nobody@example.com", "anypass")
    assert result["success"] is False
    assert result["code"] == "INVALID_CREDENTIALS"
    users_db.clear()


def test_login_wrong_password_and_missing_user_same_response():
    """User enumeration prevention: both failure cases return identical code."""
    from app.lib.auth.store import users_db
    from app.lib.auth.auth_service import register, login

    users_db.clear()
    register("enum@example.com", "realpass")
    r1 = login("enum@example.com", "wrongpass")
    r2 = login("ghost@example.com", "anypass")
    assert r1["code"] == r2["code"]
    assert r1["success"] == r2["success"]
    users_db.clear()


# ---------------------------------------------------------------------------
# verify_token()
# ---------------------------------------------------------------------------


def test_verify_token_returns_user_id_for_valid_token():
    from app.lib.auth.store import users_db
    from app.lib.auth.auth_service import register, login, verify_token

    users_db.clear()
    register("vt@example.com", "pass")
    token = login("vt@example.com", "pass")["data"]["token"]
    result = verify_token(token)
    assert result["success"] is True
    assert "user_id" in result["data"]
    users_db.clear()


def test_verify_token_rejects_invalid_token():
    from app.lib.auth.auth_service import verify_token

    result = verify_token("not.a.valid.token")
    assert result["success"] is False
    assert result["code"] == "INVALID_TOKEN"
    assert result["retryable"] is False


def test_verify_token_rejects_tampered_token():
    from app.lib.auth.store import users_db
    from app.lib.auth.auth_service import register, login, verify_token

    users_db.clear()
    register("tamper@example.com", "pass")
    token = login("tamper@example.com", "pass")["data"]["token"]
    tampered = token[:-5] + "XXXXX"
    result = verify_token(tampered)
    assert result["success"] is False
    assert result["code"] in ("INVALID_TOKEN", "TOKEN_EXPIRED")
    users_db.clear()


# ---------------------------------------------------------------------------
# reset_request()
# ---------------------------------------------------------------------------


def test_reset_request_returns_token_when_email_exists():
    from app.lib.auth.store import users_db, reset_tokens_db
    from app.lib.auth.auth_service import register, reset_request

    users_db.clear()
    reset_tokens_db.clear()
    register("reset@example.com", "pass")
    result = reset_request("reset@example.com")
    assert result["success"] is True
    assert result["data"]["token"] is not None
    users_db.clear()
    reset_tokens_db.clear()


def test_reset_request_returns_none_token_for_unknown_email():
    from app.lib.auth.store import users_db, reset_tokens_db
    from app.lib.auth.auth_service import reset_request

    users_db.clear()
    reset_tokens_db.clear()
    result = reset_request("ghost@example.com")
    assert result["success"] is True
    assert result["data"]["token"] is None
    users_db.clear()
    reset_tokens_db.clear()


def test_reset_request_same_message_regardless_of_email():
    """Info disclosure prevention: message is identical whether email exists or not."""
    from app.lib.auth.store import users_db, reset_tokens_db
    from app.lib.auth.auth_service import register, reset_request

    users_db.clear()
    reset_tokens_db.clear()
    register("exists@example.com", "pass")
    r1 = reset_request("exists@example.com")
    r2 = reset_request("notexists@example.com")
    assert r1["data"]["message"] == r2["data"]["message"]
    users_db.clear()
    reset_tokens_db.clear()


# ---------------------------------------------------------------------------
# reset_confirm()
# ---------------------------------------------------------------------------


def test_reset_confirm_updates_password():
    from app.lib.auth.store import users_db, reset_tokens_db
    from app.lib.auth.auth_service import register, reset_request, reset_confirm, login

    users_db.clear()
    reset_tokens_db.clear()
    register("confirm@example.com", "oldpass")
    token = reset_request("confirm@example.com")["data"]["token"]
    result = reset_confirm(token, "newpass")
    assert result["success"] is True
    # Old password should no longer work
    assert login("confirm@example.com", "oldpass")["success"] is False
    # New password should work
    assert login("confirm@example.com", "newpass")["success"] is True
    users_db.clear()
    reset_tokens_db.clear()


def test_reset_confirm_rejects_invalid_token():
    from app.lib.auth.auth_service import reset_confirm

    result = reset_confirm("nonexistent-token", "newpass")
    assert result["success"] is False
    assert result["code"] == "INVALID_RESET_TOKEN"
    assert result["retryable"] is False


def test_reset_confirm_rejects_expired_token():
    from datetime import datetime, timedelta, timezone
    from app.lib.auth.store import users_db, reset_tokens_db
    from app.lib.auth.auth_service import register, reset_request, reset_confirm

    users_db.clear()
    reset_tokens_db.clear()
    register("expired@example.com", "pass")
    token = reset_request("expired@example.com")["data"]["token"]
    # Force expiry by backdating the stored token
    reset_tokens_db["expired@example.com"]["expires_at"] = datetime.now(timezone.utc) - timedelta(minutes=1)
    result = reset_confirm(token, "newpass")
    assert result["success"] is False
    assert result["code"] == "INVALID_RESET_TOKEN"
    users_db.clear()
    reset_tokens_db.clear()


def test_reset_confirm_deletes_token_after_use():
    from app.lib.auth.store import users_db, reset_tokens_db
    from app.lib.auth.auth_service import register, reset_request, reset_confirm

    users_db.clear()
    reset_tokens_db.clear()
    register("del@example.com", "pass")
    token = reset_request("del@example.com")["data"]["token"]
    reset_confirm(token, "newpass")
    # Token should be consumed — reuse should fail
    result = reset_confirm(token, "anotherpass")
    assert result["success"] is False
    assert result["code"] == "INVALID_RESET_TOKEN"
    users_db.clear()
    reset_tokens_db.clear()
