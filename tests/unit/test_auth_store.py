# tests/unit/test_auth_store.py
# TDD tests for auth store extensions (Task 2, Plan 02-01).
from datetime import datetime


def test_users_db_exists_and_is_dict():
    from app.lib.auth.store import users_db

    assert isinstance(users_db, dict)


def test_reset_tokens_db_exists_and_is_dict():
    from app.lib.auth.store import reset_tokens_db

    assert isinstance(reset_tokens_db, dict)


def test_reset_tokens_db_accepts_email_keyed_entry():
    from app.lib.auth.store import reset_tokens_db

    # Should accept the expected value shape
    reset_tokens_db["test@example.com"] = {
        "token": "some-uuid",
        "expires_at": datetime(2026, 1, 1, 12, 0, 0),
    }
    entry = reset_tokens_db["test@example.com"]
    assert entry["token"] == "some-uuid"
    assert isinstance(entry["expires_at"], datetime)
    # Clean up
    del reset_tokens_db["test@example.com"]
