# tests/integration/conftest.py
import pytest
from fastapi.testclient import TestClient

from main import app
from app.lib.auth.store import users_db, reset_tokens_db
from app.lib.cart.store import carts_db
from app.lib.orders.store import orders_db
from app.lib.catalog.store import products_db
from app.lib.seed.seed import seed

@pytest.fixture(autouse=True)
def reset_stores():
    """Reset all in-memory stores and re-seed before each test."""
    users_db.clear()
    reset_tokens_db.clear()
    carts_db.clear()
    orders_db.clear()
    products_db.clear()
    seed()
    yield
    users_db.clear()
    reset_tokens_db.clear()
    carts_db.clear()
    orders_db.clear()
    products_db.clear()

@pytest.fixture
def client():
    """Unauthenticated TestClient (follow_redirects=False to inspect 303s)."""
    return TestClient(app, follow_redirects=False)

@pytest.fixture
def auth_client(client):
    """TestClient pre-authenticated as alice@example.com.

    Performs a real POST /auth/login so the httpOnly cookie is set on
    the TestClient session.

    Note: password is the seeded demo password from app/lib/seed/seed.py.
    """
    resp = client.post(
        "/auth/login",
        data={"email": "alice@example.com", "password": "alice-demo-password-2026"},
    )
    # Login should redirect (303) and set the access_token cookie.
    assert resp.status_code == 303, f"Login failed: {resp.status_code}"
    return client
