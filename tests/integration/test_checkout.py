# tests/integration/test_checkout.py
import pytest
from config import FAILURE_CONFIG

@pytest.fixture(autouse=True)
def reset_failure_config():
    original = {k: dict(v) for k, v in FAILURE_CONFIG.items()}
    yield
    for k, v in original.items():
        FAILURE_CONFIG[k] = v

def _add_item_to_cart(auth_client, product_id: str, size: str = "10", color: str = "Black", qty: int = 1):
    """Helper: add a product to cart via POST /cart/add."""
    return auth_client.post(
        "/cart/add",
        data={"product_id": product_id, "size": size, "color": color, "quantity": qty},
    )

def _get_first_product_id(auth_client) -> str:
    """Helper: fetch first product id from store."""
    from app.lib.catalog.store import products_db
    return next(iter(products_db))

# CHK-01
@pytest.mark.xfail(strict=False, reason="cart_router/checkout not yet implemented")
def test_checkout_credit_card_creates_order_and_redirects(auth_client):
    FAILURE_CONFIG["payment"]["failed_to_charge_credit_card"] = 0.0
    FAILURE_CONFIG["warehouse"]["out_of_stock"] = 0.0
    product_id = _get_first_product_id(auth_client)
    _add_item_to_cart(auth_client, product_id)
    resp = auth_client.post("/checkout", data={"payment_method": "credit_card"})
    assert resp.status_code == 303
    assert "/orders/" in resp.headers.get("location", "")
    assert "/confirmation" in resp.headers.get("location", "")

# CHK-02
@pytest.mark.xfail(strict=False, reason="cart_router/checkout not yet implemented")
def test_checkout_paypal_creates_order(auth_client):
    FAILURE_CONFIG["payment"]["failed_to_charge_paypal"] = 0.0
    FAILURE_CONFIG["warehouse"]["out_of_stock"] = 0.0
    product_id = _get_first_product_id(auth_client)
    _add_item_to_cart(auth_client, product_id)
    resp = auth_client.post("/checkout", data={"payment_method": "paypal"})
    assert resp.status_code == 303
    assert "/confirmation" in resp.headers.get("location", "")

# CHK-03
@pytest.mark.xfail(strict=False, reason="cart_router/checkout not yet implemented")
def test_checkout_apple_pay_creates_order(auth_client):
    FAILURE_CONFIG["payment"]["failed_to_charge_apple_pay"] = 0.0
    FAILURE_CONFIG["warehouse"]["out_of_stock"] = 0.0
    product_id = _get_first_product_id(auth_client)
    _add_item_to_cart(auth_client, product_id)
    resp = auth_client.post("/checkout", data={"payment_method": "apple_pay"})
    assert resp.status_code == 303
    assert "/confirmation" in resp.headers.get("location", "")

# CHK-04
@pytest.mark.xfail(strict=False, reason="cart_router/checkout not yet implemented")
def test_confirmation_page_shows_order_details(auth_client):
    FAILURE_CONFIG["payment"]["failed_to_charge_credit_card"] = 0.0
    FAILURE_CONFIG["warehouse"]["out_of_stock"] = 0.0
    product_id = _get_first_product_id(auth_client)
    _add_item_to_cart(auth_client, product_id)
    resp = auth_client.post("/checkout", data={"payment_method": "credit_card"}, follow_redirects=True)
    assert resp.status_code == 200
    content = resp.content
    assert b"order" in content.lower()

@pytest.mark.xfail(strict=False, reason="cart_router/checkout not yet implemented")
def test_checkout_payment_failure_shows_error(auth_client):
    """Payment failure probability 1.0 must re-render cart with error — no order created."""
    FAILURE_CONFIG["payment"]["failed_to_charge_credit_card"] = 1.0
    FAILURE_CONFIG["warehouse"]["out_of_stock"] = 0.0
    product_id = _get_first_product_id(auth_client)
    _add_item_to_cart(auth_client, product_id)
    resp = auth_client.post("/checkout", data={"payment_method": "credit_card"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Payment failed" in resp.content or b"payment" in resp.content.lower()
    from app.lib.orders.store import orders_db
    assert len(orders_db) == 3  # only the 3 seeded orders; no new order created

@pytest.mark.xfail(strict=False, reason="cart_router/checkout not yet implemented")
def test_checkout_warehouse_failure_shows_error(auth_client):
    FAILURE_CONFIG["warehouse"]["out_of_stock"] = 1.0
    product_id = _get_first_product_id(auth_client)
    _add_item_to_cart(auth_client, product_id)
    resp = auth_client.post("/checkout", data={"payment_method": "credit_card"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"out of stock" in resp.content.lower() or b"unavailable" in resp.content.lower()
