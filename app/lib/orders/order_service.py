# app/lib/orders/order_service.py
# Order lifecycle: place, cancel, return, get, list.
# Ownership and eligibility checks are enforced in the service layer (D-13).
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from app.lib.cart.store import carts_db
from app.lib.orders.models import Order, OrderItem
from app.lib.orders.store import orders_db

# Cancel is allowed only for these statuses (D-11)
_CANCELABLE_STATUSES = ("placed", "paid")

# Return is allowed only for these statuses (D-12)
_RETURNABLE_STATUSES = ("paid", "processing", "shipped")


def _now_iso() -> str:
    """Return current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _order_to_dict(order: Order) -> dict:
    """Serialize an Order to a plain dict.

    Args:
        order: The Order dataclass instance.

    Returns:
        Dict with all Order fields; items rendered as dicts.
    """
    return {
        "id": order.id,
        "user_id": order.user_id,
        "items": [
            {
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
            }
            for item in order.items
        ],
        "total_amount": order.total_amount,
        "payment_method": order.payment_method,
        "payment_status": order.payment_status,
        "order_status": order.order_status,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
    }


def place_order(
    user_id: str,
    payment_method: Literal["credit_card", "paypal", "apple_pay"],
) -> dict:
    """Create an order from the user's current cart.

    Converts CartItems to OrderItems, computes total, stores in orders_db,
    and clears the user's cart.

    Args:
        user_id: The authenticated user's ID.
        payment_method: Payment method selected by the user.

    Returns:
        Success dict with order_id, total_amount, and order_status,
        or failure dict if cart is empty or missing.
    """
    cart = carts_db.get(user_id)
    if not cart or not cart.items:
        return {
            "success": False,
            "code": "CART_EMPTY",
            "message": "Cart is empty",
            "retryable": False,
        }

    order_items = [
        OrderItem(
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
        )
        for item in cart.items
    ]
    total_amount = sum(item.quantity * item.unit_price for item in order_items)
    now = _now_iso()

    order = Order(
        id=str(uuid4()),
        user_id=user_id,
        items=order_items,
        total_amount=total_amount,
        payment_method=payment_method,
        payment_status="pending",
        order_status="placed",
        created_at=now,
        updated_at=now,
    )

    orders_db[order.id] = order
    # Clear cart after placing order
    del carts_db[user_id]

    return {
        "success": True,
        "data": {
            "order_id": order.id,
            "total_amount": order.total_amount,
            "order_status": order.order_status,
        },
    }


def cancel_order(order_id: str, user_id: str) -> dict:
    """Cancel an order if owned by the user and in a cancelable state.

    Ownership is checked before eligibility (D-13).
    Cancelable statuses: placed, paid (D-11).

    Args:
        order_id: ID of the order to cancel.
        user_id: Authenticated user's ID (from JWT session, never request body).

    Returns:
        Success dict with updated order_status, or failure dict with error code.
    """
    order = orders_db.get(order_id)
    if not order:
        return {
            "success": False,
            "code": "ORDER_NOT_FOUND",
            "message": "Order not found",
            "retryable": False,
        }

    # D-13: ownership check first
    if order.user_id != user_id:
        return {
            "success": False,
            "code": "UNAUTHORIZED",
            "message": "Access denied",
            "retryable": False,
        }

    # D-11: eligibility check
    if order.order_status not in _CANCELABLE_STATUSES:
        return {
            "success": False,
            "code": "CANCEL_NOT_ALLOWED",
            "message": f"Cannot cancel order in status '{order.order_status}'",
            "retryable": False,
        }

    order.order_status = "canceled"
    order.updated_at = _now_iso()

    return {
        "success": True,
        "data": {"order_id": order.id, "order_status": "canceled"},
    }


def request_return(order_id: str, user_id: str) -> dict:
    """Request a return for an order if owned by the user and in a returnable state.

    Ownership is checked before eligibility (D-13).
    Returnable statuses: paid, processing, shipped (D-12).

    Args:
        order_id: ID of the order to return.
        user_id: Authenticated user's ID (from JWT session, never request body).

    Returns:
        Success dict with updated order_status, or failure dict with error code.
    """
    order = orders_db.get(order_id)
    if not order:
        return {
            "success": False,
            "code": "ORDER_NOT_FOUND",
            "message": "Order not found",
            "retryable": False,
        }

    # D-13: ownership check first
    if order.user_id != user_id:
        return {
            "success": False,
            "code": "UNAUTHORIZED",
            "message": "Access denied",
            "retryable": False,
        }

    # D-12: eligibility check
    if order.order_status not in _RETURNABLE_STATUSES:
        return {
            "success": False,
            "code": "RETURN_NOT_ALLOWED",
            "message": f"Cannot return order in status '{order.order_status}'",
            "retryable": False,
        }

    order.order_status = "returned"
    order.updated_at = _now_iso()

    return {
        "success": True,
        "data": {"order_id": order.id, "order_status": "returned"},
    }


def get_order(order_id: str, user_id: str) -> dict:
    """Retrieve a single order for the authenticated user.

    Args:
        order_id: ID of the order to retrieve.
        user_id: Authenticated user's ID (from JWT session).

    Returns:
        Success dict with full order data, or failure dict with error code.
    """
    order = orders_db.get(order_id)
    if not order:
        return {
            "success": False,
            "code": "ORDER_NOT_FOUND",
            "message": "Order not found",
            "retryable": False,
        }

    if order.user_id != user_id:
        return {
            "success": False,
            "code": "UNAUTHORIZED",
            "message": "Access denied",
            "retryable": False,
        }

    return {"success": True, "data": {"order": _order_to_dict(order)}}


def list_orders(user_id: str) -> dict:
    """List all orders belonging to the authenticated user.

    Args:
        user_id: Authenticated user's ID (from JWT session).

    Returns:
        Success dict with list of order dicts (may be empty).
    """
    user_orders = [o for o in orders_db.values() if o.user_id == user_id]
    return {
        "success": True,
        "data": {"orders": [_order_to_dict(o) for o in user_orders]},
    }
