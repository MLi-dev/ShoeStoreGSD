# tests/unit/test_order_service.py
# TDD RED phase: failing tests for order_service.py
import pytest

from app.lib.cart.models import Cart, CartItem
from app.lib.cart.store import carts_db
from app.lib.orders.models import Order
from app.lib.orders.store import orders_db


@pytest.fixture(autouse=True)
def clear_stores():
    """Reset in-memory stores before each test."""
    carts_db.clear()
    orders_db.clear()
    yield
    carts_db.clear()
    orders_db.clear()


def make_order(
    order_id: str = "ord-1",
    user_id: str = "user-1",
    order_status: str = "placed",
    payment_status: str = "pending",
) -> Order:
    return Order(
        id=order_id,
        user_id=user_id,
        items=[],
        total_amount=0.0,
        payment_method="credit_card",
        payment_status=payment_status,
        order_status=order_status,
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )


# --- place_order ---


def test_place_order_empty_cart():
    from app.lib.orders.order_service import place_order

    result = place_order("user-1", "credit_card")
    assert result["success"] is False
    assert result["code"] == "CART_EMPTY"
    assert result["retryable"] is False


def test_place_order_missing_cart():
    from app.lib.orders.order_service import place_order

    result = place_order("user-with-no-cart", "paypal")
    assert result["success"] is False
    assert result["code"] == "CART_EMPTY"


def test_place_order_success():
    from app.lib.orders.order_service import place_order

    cart = Cart(
        user_id="user-1",
        items=[CartItem("prod-1", 2, 50.0), CartItem("prod-2", 1, 30.0)],
    )
    carts_db["user-1"] = cart
    result = place_order("user-1", "credit_card")
    assert result["success"] is True
    data = result["data"]
    assert "order_id" in data
    assert data["total_amount"] == 130.0  # 2*50 + 1*30
    assert data["order_status"] == "placed"
    # Cart should be cleared after placing order
    assert "user-1" not in carts_db


def test_place_order_stores_in_orders_db():
    from app.lib.orders.order_service import place_order

    carts_db["user-1"] = Cart(user_id="user-1", items=[CartItem("prod-1", 1, 100.0)])
    result = place_order("user-1", "apple_pay")
    assert result["success"] is True
    order_id = result["data"]["order_id"]
    assert order_id in orders_db
    order = orders_db[order_id]
    assert order.user_id == "user-1"
    assert order.payment_method == "apple_pay"
    assert order.payment_status == "pending"


# --- cancel_order ---


def test_cancel_order_not_found():
    from app.lib.orders.order_service import cancel_order

    result = cancel_order("nonexistent", "user-1")
    assert result["success"] is False
    assert result["code"] == "ORDER_NOT_FOUND"


def test_cancel_order_wrong_user():
    """Ownership check before eligibility (D-13)."""
    from app.lib.orders.order_service import cancel_order

    orders_db["ord-1"] = make_order(order_id="ord-1", user_id="user-1")
    result = cancel_order("ord-1", "user-2")
    assert result["success"] is False
    assert result["code"] == "UNAUTHORIZED"


def test_cancel_order_placed_allowed():
    """Cancel allowed for 'placed' status (D-11)."""
    from app.lib.orders.order_service import cancel_order

    orders_db["ord-1"] = make_order(order_status="placed")
    result = cancel_order("ord-1", "user-1")
    assert result["success"] is True
    assert result["data"]["order_status"] == "canceled"


def test_cancel_order_paid_allowed():
    """Cancel allowed for 'paid' status (D-11)."""
    from app.lib.orders.order_service import cancel_order

    orders_db["ord-1"] = make_order(order_status="paid", payment_status="paid")
    result = cancel_order("ord-1", "user-1")
    assert result["success"] is True
    assert result["data"]["order_status"] == "canceled"


def test_cancel_order_processing_not_allowed():
    """Cancel NOT allowed for 'processing' status (D-11)."""
    from app.lib.orders.order_service import cancel_order

    orders_db["ord-1"] = make_order(order_status="processing")
    result = cancel_order("ord-1", "user-1")
    assert result["success"] is False
    assert result["code"] == "CANCEL_NOT_ALLOWED"


def test_cancel_order_shipped_not_allowed():
    """Cancel NOT allowed for 'shipped' status (D-11)."""
    from app.lib.orders.order_service import cancel_order

    orders_db["ord-1"] = make_order(order_status="shipped")
    result = cancel_order("ord-1", "user-1")
    assert result["success"] is False
    assert result["code"] == "CANCEL_NOT_ALLOWED"


def test_cancel_order_already_canceled():
    from app.lib.orders.order_service import cancel_order

    orders_db["ord-1"] = make_order(order_status="canceled")
    result = cancel_order("ord-1", "user-1")
    assert result["success"] is False
    assert result["code"] == "CANCEL_NOT_ALLOWED"


def test_cancel_order_updates_updated_at():
    from app.lib.orders.order_service import cancel_order

    orders_db["ord-1"] = make_order(order_status="placed")
    cancel_order("ord-1", "user-1")
    order = orders_db["ord-1"]
    assert order.order_status == "canceled"
    assert order.updated_at != "2026-01-01T00:00:00+00:00"


# --- request_return ---


def test_request_return_not_found():
    from app.lib.orders.order_service import request_return

    result = request_return("nonexistent", "user-1")
    assert result["success"] is False
    assert result["code"] == "ORDER_NOT_FOUND"


def test_request_return_wrong_user():
    """Ownership check before eligibility (D-13)."""
    from app.lib.orders.order_service import request_return

    orders_db["ord-1"] = make_order(user_id="user-1", order_status="shipped")
    result = request_return("ord-1", "user-2")
    assert result["success"] is False
    assert result["code"] == "UNAUTHORIZED"


def test_request_return_paid_allowed():
    """Return allowed for 'paid' status (D-12)."""
    from app.lib.orders.order_service import request_return

    orders_db["ord-1"] = make_order(order_status="paid", payment_status="paid")
    result = request_return("ord-1", "user-1")
    assert result["success"] is True
    assert result["data"]["order_status"] == "returned"


def test_request_return_processing_allowed():
    """Return allowed for 'processing' status (D-12)."""
    from app.lib.orders.order_service import request_return

    orders_db["ord-1"] = make_order(order_status="processing")
    result = request_return("ord-1", "user-1")
    assert result["success"] is True
    assert result["data"]["order_status"] == "returned"


def test_request_return_shipped_allowed():
    """Return allowed for 'shipped' status (D-12)."""
    from app.lib.orders.order_service import request_return

    orders_db["ord-1"] = make_order(order_status="shipped")
    result = request_return("ord-1", "user-1")
    assert result["success"] is True
    assert result["data"]["order_status"] == "returned"


def test_request_return_placed_not_allowed():
    """Return NOT allowed for 'placed' status (D-12)."""
    from app.lib.orders.order_service import request_return

    orders_db["ord-1"] = make_order(order_status="placed")
    result = request_return("ord-1", "user-1")
    assert result["success"] is False
    assert result["code"] == "RETURN_NOT_ALLOWED"


def test_request_return_canceled_not_allowed():
    """Return NOT allowed for 'canceled' status (D-12)."""
    from app.lib.orders.order_service import request_return

    orders_db["ord-1"] = make_order(order_status="canceled")
    result = request_return("ord-1", "user-1")
    assert result["success"] is False
    assert result["code"] == "RETURN_NOT_ALLOWED"


# --- get_order ---


def test_get_order_not_found():
    from app.lib.orders.order_service import get_order

    result = get_order("nonexistent", "user-1")
    assert result["success"] is False
    assert result["code"] == "ORDER_NOT_FOUND"


def test_get_order_wrong_user():
    from app.lib.orders.order_service import get_order

    orders_db["ord-1"] = make_order(user_id="user-1")
    result = get_order("ord-1", "user-2")
    assert result["success"] is False
    assert result["code"] == "UNAUTHORIZED"


def test_get_order_success():
    from app.lib.orders.order_service import get_order

    orders_db["ord-1"] = make_order()
    result = get_order("ord-1", "user-1")
    assert result["success"] is True
    assert result["data"]["order"]["id"] == "ord-1"
    assert result["data"]["order"]["user_id"] == "user-1"


# --- list_orders ---


def test_list_orders_empty():
    from app.lib.orders.order_service import list_orders

    result = list_orders("user-1")
    assert result["success"] is True
    assert result["data"]["orders"] == []


def test_list_orders_filters_by_user():
    from app.lib.orders.order_service import list_orders

    orders_db["ord-1"] = make_order(order_id="ord-1", user_id="user-1")
    orders_db["ord-2"] = make_order(order_id="ord-2", user_id="user-2")
    orders_db["ord-3"] = make_order(order_id="ord-3", user_id="user-1")
    result = list_orders("user-1")
    assert result["success"] is True
    ids = {o["id"] for o in result["data"]["orders"]}
    assert ids == {"ord-1", "ord-3"}
