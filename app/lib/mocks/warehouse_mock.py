# app/lib/mocks/warehouse_mock.py
# Warehouse mock adapter with configurable failure injection.
# CRITICAL: Read FAILURE_CONFIG at call time (never at import time).
# Mutations from [root]: token in Phase 5 must take effect without restart.
import random

from config import FAILURE_CONFIG


def get_available_quantity(product_id: str) -> dict:
    """Return mock available quantity for a product.

    Args:
        product_id: The product to check.

    Returns:
        Success dict with quantity field.
    """
    return {"success": True, "data": {"product_id": product_id, "quantity": 100}}


def reserve_inventory(order_id: str, items: list[dict]) -> dict:
    """Simulate inventory reservation with out_of_stock failure injection.

    Args:
        order_id: The order reserving inventory.
        items: List of dicts with product_id and quantity keys.

    Returns:
        Success dict with reservation_id, or failure dict with code OUT_OF_STOCK.
    """
    failure_prob = FAILURE_CONFIG.get("warehouse", {}).get("out_of_stock", 0.0)
    if random.random() < failure_prob:
        return {
            "success": False,
            "code": "OUT_OF_STOCK",
            "message": "Mock warehouse failure: inventory unavailable",
            "retryable": True,
        }
    return {"success": True, "data": {"reservation_id": f"res_{order_id}"}}


def ship_order(order_id: str) -> dict:
    """Simulate order shipment (no failure injection — always succeeds in demo).

    Args:
        order_id: The order to ship.

    Returns:
        Success dict with tracking_id.
    """
    return {"success": True, "data": {"tracking_id": f"track_{order_id}"}}


def cancel_order(order_id: str) -> dict:
    """Simulate warehouse-side order cancellation with failure injection.

    Args:
        order_id: The order to cancel in the warehouse system.

    Returns:
        Success dict with order_id, or failure dict with code FAILED_TO_CANCEL_ORDER.
    """
    failure_prob = FAILURE_CONFIG.get("warehouse", {}).get("failed_to_cancel_order", 0.0)
    if random.random() < failure_prob:
        return {
            "success": False,
            "code": "FAILED_TO_CANCEL_ORDER",
            "message": "Mock warehouse failure: cancel failed",
            "retryable": True,
        }
    return {"success": True, "data": {"order_id": order_id}}
