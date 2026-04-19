# app/lib/guardrails/root_instruction.py
# Parses [root]: demo control instructions from the chat router.
# Pure function — reads no globals, mutates nothing. Caller applies mutations.
# Source: 05-CONTEXT.md D-01 through D-04; 05-PATTERNS.md
import logging
import re

_PAYMENT_PATTERN = re.compile(
    r"payment\s+fail\s+(\d+)%(?:\s+(credit\s+card|paypal|apple\s+pay))?",
    re.IGNORECASE,
)
_WAREHOUSE_STOCK_PATTERN = re.compile(
    r"warehouse\s+out[_\s]of[_\s]stock\s+(\d+)%", re.IGNORECASE
)
_WAREHOUSE_CANCEL_PATTERN = re.compile(
    r"warehouse\s+cancel\s+fail\s+(\d+)%", re.IGNORECASE
)
_REFUND_PATTERN = re.compile(
    r"refund\s+fail\s+(\d+)%(?:\s+(credit\s+card|paypal|apple\s+pay))?",
    re.IGNORECASE,
)
_DISABLE_ALL_PATTERN = re.compile(r"disable\s+all\s+failures", re.IGNORECASE)

_METHOD_ALIASES: dict[str, str] = {
    "credit card": "credit_card",
    "paypal": "paypal",
    "apple pay": "apple_pay",
}
_ALL_PAYMENT_METHODS: list[str] = ["credit_card", "paypal", "apple_pay"]

logger = logging.getLogger(__name__)


def parse_root_instruction(text: str) -> dict:
    """Parse a root instruction string and return mutations to apply.

    Args:
        text: The instruction text after stripping the '[root]:' prefix.

    Returns:
        Success dict: {"success": True, "mutations": {...}, "message": str}
        Failure dict: {"success": False, "mutations": {}, "message": str}
    """
    normalized = text.lower().strip()

    if _DISABLE_ALL_PATTERN.search(normalized):
        mutations = {
            "warehouse": {"out_of_stock": 0.0, "failed_to_cancel_order": 0.0},
            "payment": {
                "failed_to_charge_credit_card": 0.0,
                "failed_to_charge_paypal": 0.0,
                "failed_to_charge_apple_pay": 0.0,
                "failed_to_refund_credit_card": 0.0,
                "failed_to_refund_paypal": 0.0,
                "failed_to_refund_apple_pay": 0.0,
            },
        }
        return {"success": True, "mutations": mutations, "message": "Applied: all failures disabled"}

    m = _WAREHOUSE_STOCK_PATTERN.search(normalized)
    if m:
        pct = min(1.0, max(0.0, int(m.group(1)) / 100.0))
        return {
            "success": True,
            "mutations": {"warehouse": {"out_of_stock": pct}},
            "message": f"Applied: warehouse out_of_stock {m.group(1)}%",
        }

    m = _WAREHOUSE_CANCEL_PATTERN.search(normalized)
    if m:
        pct = min(1.0, max(0.0, int(m.group(1)) / 100.0))
        return {
            "success": True,
            "mutations": {"warehouse": {"failed_to_cancel_order": pct}},
            "message": f"Applied: warehouse cancel fail {m.group(1)}%",
        }

    m = _PAYMENT_PATTERN.search(normalized)
    if m:
        pct = min(1.0, max(0.0, int(m.group(1)) / 100.0))
        method_raw = m.group(2)
        if method_raw is None:
            mutations = {
                "payment": {f"failed_to_charge_{method}": pct for method in _ALL_PAYMENT_METHODS}
            }
            return {
                "success": True,
                "mutations": mutations,
                "message": f"Applied: payment fail {m.group(1)}% (all methods)",
            }
        method = _METHOD_ALIASES[method_raw.lower()]
        return {
            "success": True,
            "mutations": {"payment": {f"failed_to_charge_{method}": pct}},
            "message": f"Applied: payment fail {m.group(1)}% {method}",
        }

    m = _REFUND_PATTERN.search(normalized)
    if m:
        pct = min(1.0, max(0.0, int(m.group(1)) / 100.0))
        method_raw = m.group(2)
        if method_raw is None:
            mutations = {
                "payment": {f"failed_to_refund_{method}": pct for method in _ALL_PAYMENT_METHODS}
            }
            return {
                "success": True,
                "mutations": mutations,
                "message": f"Applied: refund fail {m.group(1)}% (all methods)",
            }
        method = _METHOD_ALIASES[method_raw.lower()]
        return {
            "success": True,
            "mutations": {"payment": {f"failed_to_refund_{method}": pct}},
            "message": f"Applied: refund fail {m.group(1)}% {method}",
        }

    return {"success": False, "mutations": {}, "message": f"Unknown root instruction: {text!r}"}
