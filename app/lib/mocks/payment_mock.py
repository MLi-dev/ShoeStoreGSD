# app/lib/mocks/payment_mock.py
# Payment mock adapter with configurable failure injection.
# CRITICAL: Read FAILURE_CONFIG at call time (never at import time).
# Dynamic key pattern: f"failed_to_charge_{payment_method}" and
# f"failed_to_refund_{payment_method}" — method is one of
# credit_card, paypal, apple_pay.
import random

from config import FAILURE_CONFIG


def charge(order_id: str, payment_method: str, amount: float) -> dict:
    """Simulate payment charge with configurable failure injection.

    Args:
        order_id: The order being charged.
        payment_method: One of credit_card, paypal, apple_pay.
        amount: Charge amount in dollars.

    Returns:
        Success dict with transaction_id, or failure dict with dynamic error code.
    """
    failure_key = f"failed_to_charge_{payment_method}"
    failure_prob = FAILURE_CONFIG.get("payment", {}).get(failure_key, 0.0)
    if random.random() < failure_prob:
        return {
            "success": False,
            "code": failure_key.upper(),
            "message": f"Mock payment failure: {failure_key}",
            "retryable": True,
        }
    return {"success": True, "data": {"transaction_id": f"txn_{order_id}"}}


def refund(order_id: str, payment_method: str, amount: float) -> dict:
    """Simulate payment refund with configurable failure injection.

    Args:
        order_id: The order being refunded.
        payment_method: One of credit_card, paypal, apple_pay.
        amount: Refund amount in dollars.

    Returns:
        Success dict with refund_id, or failure dict with dynamic error code.
    """
    failure_key = f"failed_to_refund_{payment_method}"
    failure_prob = FAILURE_CONFIG.get("payment", {}).get(failure_key, 0.0)
    if random.random() < failure_prob:
        return {
            "success": False,
            "code": failure_key.upper(),
            "message": f"Mock payment failure: {failure_key}",
            "retryable": True,
        }
    return {"success": True, "data": {"refund_id": f"ref_{order_id}"}}
