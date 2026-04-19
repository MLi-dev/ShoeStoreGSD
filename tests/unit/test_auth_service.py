# tests/unit/test_auth_service.py
# Unit tests for auth_service.py.
# Tests cover register, login, verify_token, reset_request, reset_confirm.
import pytest

from app.lib.auth.auth_service import (
    login,
    register,
    reset_confirm,
    reset_request,
    verify_token,
)
from app.lib.auth.store import reset_tokens_db, users_db
from app.lib.cart.store import carts_db
from app.lib.catalog.store import products_db
from app.lib.orders.store import orders_db


@pytest.fixture(autouse=True)
def clear_all_stores():
    users_db.clear()
    reset_tokens_db.clear()
    products_db.clear()
    carts_db.clear()
    orders_db.clear()
    yield
    users_db.clear()
    reset_tokens_db.clear()
    products_db.clear()
    carts_db.clear()
    orders_db.clear()


# ---------------------------------------------------------------------------
# register()
# ---------------------------------------------------------------------------


def test_register_new_user():
    result = register("alice@example.com", "secret")
    assert result["success"] is True
    assert "user_id" in result["data"]
    assert result["data"]["email"] == "alice@example.com"
    assert len(users_db) == 1


def test_register_duplicate_email():
    register("alice@example.com", "secret")
    result = register("alice@example.com", "other")
    assert result["success"] is False
    assert result["code"] == "EMAIL_ALREADY_EXISTS"


def test_register_returns_success_with_user_id_and_email():
    result = register("new@example.com", "password123")
    assert result["success"] is True
    assert "user_id" in result["data"]
    assert result["data"]["email"] == "new@example.com"
    assert len(users_db) == 1


def test_register_rejects_duplicate_email():
    register("dupe@example.com", "pass1")
    result = register("dupe@example.com", "pass2")
    assert result["success"] is False
    assert result["code"] == "EMAIL_ALREADY_EXISTS"
    assert result["retryable"] is False


def test_register_stores_password_as_bcrypt_hash():
    from passlib.context import CryptContext

    register("hash@example.com", "mypassword")
    user = next(u for u in users_db.values() if u.email == "hash@example.com")
    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    assert pwd_ctx.verify("mypassword", user.password_hash)


def test_register_never_returns_password_hash():
    result = register("safe@example.com", "secret")
    assert "password_hash" not in str(result)


# ---------------------------------------------------------------------------
# login()
# ---------------------------------------------------------------------------


def test_login_valid_credentials():
    register("alice@example.com", "secret")
    result = login("alice@example.com", "secret")
    assert result["success"] is True
    assert "token" in result["data"]
    assert "user_id" in result["data"]


def test_login_wrong_password():
    register("alice@example.com", "secret")
    result = login("alice@example.com", "wrongpass")
    assert result["success"] is False
    assert result["code"] == "INVALID_CREDENTIALS"


def test_login_unknown_email():
    result = login("nobody@example.com", "anypass")
    assert result["success"] is False
    assert result["code"] == "INVALID_CREDENTIALS"


def test_login_returns_token_on_valid_credentials():
    register("login@example.com", "goodpass")
    result = login("login@example.com", "goodpass")
    assert result["success"] is True
    assert "token" in result["data"]
    assert "user_id" in result["data"]


def test_login_rejects_wrong_password():
    register("wp@example.com", "rightpass")
    result = login("wp@example.com", "wrongpass")
    assert result["success"] is False
    assert result["code"] == "INVALID_CREDENTIALS"
    assert result["retryable"] is False


def test_login_rejects_unknown_email():
    result = login("nobody@example.com", "anypass")
    assert result["success"] is False
    assert result["code"] == "INVALID_CREDENTIALS"


def test_login_wrong_password_and_missing_user_same_response():
    """User enumeration prevention: both failure cases return identical code."""
    register("enum@example.com", "realpass")
    r1 = login("enum@example.com", "wrongpass")
    r2 = login("ghost@example.com", "anypass")
    assert r1["code"] == r2["code"]
    assert r1["success"] == r2["success"]


# ---------------------------------------------------------------------------
# verify_token()
# ---------------------------------------------------------------------------


def test_verify_token_valid():
    register("alice@example.com", "secret")
    token = login("alice@example.com", "secret")["data"]["token"]
    result = verify_token(token)
    assert result["success"] is True
    assert result["data"]["user_id"] != ""


def test_verify_token_invalid():
    result = verify_token("not-a-real-token")
    assert result["success"] is False
    assert result["code"] == "INVALID_TOKEN"


def test_verify_token_returns_user_id_for_valid_token():
    register("vt@example.com", "pass")
    token = login("vt@example.com", "pass")["data"]["token"]
    result = verify_token(token)
    assert result["success"] is True
    assert "user_id" in result["data"]


def test_verify_token_rejects_invalid_token():
    result = verify_token("not.a.valid.token")
    assert result["success"] is False
    assert result["code"] == "INVALID_TOKEN"
    assert result["retryable"] is False


def test_verify_token_rejects_tampered_token():
    register("tamper@example.com", "pass")
    token = login("tamper@example.com", "pass")["data"]["token"]
    tampered = token[:-5] + "XXXXX"
    result = verify_token(tampered)
    assert result["success"] is False
    assert result["code"] in ("INVALID_TOKEN", "TOKEN_EXPIRED")


# ---------------------------------------------------------------------------
# reset_request() + reset_confirm() end-to-end
# ---------------------------------------------------------------------------


def test_password_reset_end_to_end():
    register("alice@example.com", "oldpass")
    req = reset_request("alice@example.com")
    assert req["success"] is True
    token = req["data"]["token"]
    assert token is not None
    confirm = reset_confirm(token, "newpass")
    assert confirm["success"] is True
    assert confirm["data"]["message"] == "Password updated successfully"
    # New password works
    assert login("alice@example.com", "newpass")["success"] is True
    # Old password fails
    assert login("alice@example.com", "oldpass")["success"] is False


def test_reset_request_unknown_email():
    result = reset_request("nobody@example.com")
    assert result["success"] is True  # do not reveal whether email exists
    assert result["data"]["token"] is None


def test_reset_confirm_invalid_token():
    result = reset_confirm("totally-fake-token", "newpass")
    assert result["success"] is False
    assert result["code"] == "INVALID_RESET_TOKEN"


def test_reset_request_returns_token_when_email_exists():
    register("reset@example.com", "pass")
    result = reset_request("reset@example.com")
    assert result["success"] is True
    assert result["data"]["token"] is not None


def test_reset_request_returns_none_token_for_unknown_email():
    result = reset_request("ghost@example.com")
    assert result["success"] is True
    assert result["data"]["token"] is None


def test_reset_request_same_message_regardless_of_email():
    """Info disclosure prevention: message is identical whether email exists or not."""
    register("exists@example.com", "pass")
    r1 = reset_request("exists@example.com")
    r2 = reset_request("notexists@example.com")
    assert r1["data"]["message"] == r2["data"]["message"]


def test_reset_confirm_updates_password():
    register("confirm@example.com", "oldpass")
    token = reset_request("confirm@example.com")["data"]["token"]
    result = reset_confirm(token, "newpass")
    assert result["success"] is True
    # Old password should no longer work
    assert login("confirm@example.com", "oldpass")["success"] is False
    # New password should work
    assert login("confirm@example.com", "newpass")["success"] is True


def test_reset_confirm_rejects_invalid_token():
    result = reset_confirm("nonexistent-token", "newpass")
    assert result["success"] is False
    assert result["code"] == "INVALID_RESET_TOKEN"
    assert result["retryable"] is False


def test_reset_confirm_rejects_expired_token():
    from datetime import datetime, timedelta, timezone

    register("expired@example.com", "pass")
    token = reset_request("expired@example.com")["data"]["token"]
    # Force expiry by backdating the stored token
    reset_tokens_db["expired@example.com"]["expires_at"] = datetime.now(
        timezone.utc
    ) - timedelta(minutes=1)
    result = reset_confirm(token, "newpass")
    assert result["success"] is False
    assert result["code"] == "INVALID_RESET_TOKEN"


def test_reset_confirm_deletes_token_after_use():
    register("del@example.com", "pass")
    token = reset_request("del@example.com")["data"]["token"]
    reset_confirm(token, "newpass")
    # Token should be consumed — reuse should fail
    result = reset_confirm(token, "anotherpass")
    assert result["success"] is False
    assert result["code"] == "INVALID_RESET_TOKEN"
