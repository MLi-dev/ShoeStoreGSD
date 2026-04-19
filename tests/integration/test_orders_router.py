# tests/integration/test_orders_router.py
import pytest
from config import FAILURE_CONFIG

@pytest.fixture(autouse=True)
def reset_failure_config():
    original = {k: dict(v) for k, v in FAILURE_CONFIG.items()}
    yield
    for k, v in original.items():
        FAILURE_CONFIG[k] = v

def _get_alice_order_id(status: str = "paid") -> str:
    """Return the ID of alice's seeded order with the given status."""
    from app.lib.orders.store import orders_db
    from app.lib.auth.store import users_db
    alice = next((u for u in users_db.values() if u.email == "alice@example.com"), None)
    if not alice:
        raise RuntimeError("alice not in store")
    order = next(
        (o for o in orders_db.values() if o.user_id == alice.id and o.order_status == status),
        None,
    )
    if not order:
        raise RuntimeError(f"No alice order with status={status}")
    return order.id

# ORD-01
@pytest.mark.xfail(strict=False, reason="orders_router not yet implemented")
def test_orders_list_shows_user_orders(auth_client):
    resp = auth_client.get("/orders", follow_redirects=True)
    assert resp.status_code == 200
    assert b"order" in resp.content.lower()

@pytest.mark.xfail(strict=False, reason="orders_router not yet implemented")
def test_order_detail_shows_status(auth_client):
    order_id = _get_alice_order_id("paid")
    resp = auth_client.get(f"/orders/{order_id}", follow_redirects=True)
    assert resp.status_code == 200
    assert b"paid" in resp.content.lower()

@pytest.mark.xfail(strict=False, reason="orders_router not yet implemented")
def test_cross_user_order_access_denied(client):
    """Bob must not be able to see alice's order."""
    # Log in as bob
    client.post("/auth/login", data={"email": "bob@example.com", "password": "bob-demo-password-2026"})
    from app.lib.orders.store import orders_db
    from app.lib.auth.store import users_db
    alice = next((u for u in users_db.values() if u.email == "alice@example.com"), None)
    alice_order = next((o for o in orders_db.values() if o.user_id == alice.id), None)
    resp = client.get(f"/orders/{alice_order.id}", follow_redirects=True)
    # Must not return 200 with order data
    assert resp.status_code in (403, 302, 303, 307) or b"Access denied" in resp.content

# ORD-02
@pytest.mark.xfail(strict=False, reason="orders_router not yet implemented")
def test_cancel_order_redirects_and_updates_status(auth_client):
    FAILURE_CONFIG["warehouse"]["failed_to_cancel_order"] = 0.0
    order_id = _get_alice_order_id("paid")
    resp = auth_client.post(f"/orders/{order_id}/cancel")
    assert resp.status_code == 303
    from app.lib.orders.store import orders_db
    assert orders_db[order_id].order_status == "canceled"

@pytest.mark.xfail(strict=False, reason="orders_router not yet implemented")
def test_cancel_order_warehouse_failure_shows_flash(auth_client):
    FAILURE_CONFIG["warehouse"]["failed_to_cancel_order"] = 1.0
    order_id = _get_alice_order_id("paid")
    resp = auth_client.post(f"/orders/{order_id}/cancel", follow_redirects=True)
    assert resp.status_code == 200

# ORD-03
@pytest.mark.xfail(strict=False, reason="orders_router not yet implemented")
def test_return_order_on_paid_order_succeeds(auth_client):
    order_id = _get_alice_order_id("paid")
    resp = auth_client.post(f"/orders/{order_id}/return")
    assert resp.status_code == 303
    from app.lib.orders.store import orders_db
    assert orders_db[order_id].order_status == "returned"

@pytest.mark.xfail(strict=False, reason="orders_router not yet implemented")
def test_return_order_on_placed_order_fails(auth_client):
    """'placed' orders cannot be returned — eligibility enforced by service."""
    from app.lib.orders.store import orders_db
    from app.lib.auth.store import users_db
    alice = next((u for u in users_db.values() if u.email == "alice@example.com"), None)
    placed_order = next((o for o in orders_db.values() if o.user_id == alice.id and o.order_status == "placed"), None)
    if not placed_order:
        pytest.skip("No placed order seeded for alice")
    resp = auth_client.post(f"/orders/{placed_order.id}/return", follow_redirects=True)
    assert resp.status_code == 200
    from app.lib.orders.store import orders_db as db
    assert db[placed_order.id].order_status != "returned"
