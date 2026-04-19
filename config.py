# config.py
# Global configuration for ShoeStore AI Demo.
# Mock adapters read FAILURE_CONFIG at call time (never at import time) so that
# the [root]: token in demo mode can mutate probabilities mid-session (Phase 5).
# Source of shape: .planning/codebase/CONVENTIONS.md (Error Injection Pattern)

FAILURE_CONFIG: dict[str, dict[str, float]] = {
    "warehouse": {
        "out_of_stock": 0.10,
        "failed_to_cancel_order": 0.20,
    },
    "payment": {
        "failed_to_charge_credit_card": 0.03,
        "failed_to_refund_paypal": 0.08,
    },
}

# DEMO_MODE gates the [root]: instruction token parser (Phase 4+).
# When False, root tokens are ignored and treated as plain user input.
DEMO_MODE: bool = True
