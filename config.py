# config.py
# Global configuration for ShoeStore AI Demo.
# Mock adapters read FAILURE_CONFIG at call time (never at import time) so that
# the [root]: token in demo mode can mutate probabilities mid-session (Phase 5).
# Source of shape: .planning/codebase/CONVENTIONS.md (Error Injection Pattern)

FAILURE_CONFIG: dict[str, dict[str, float]] = {
    "warehouse": {
        "out_of_stock": 0.0,
        "failed_to_cancel_order": 0.0,
    },
    "payment": {
        "failed_to_charge_credit_card": 0.0,
        "failed_to_charge_paypal": 0.0,
        "failed_to_charge_apple_pay": 0.0,
        "failed_to_refund_credit_card": 0.0,
        "failed_to_refund_paypal": 0.0,
        "failed_to_refund_apple_pay": 0.0,
    },
}

# DEMO_MODE gates the [root]: instruction token parser (Phase 4+).
# When False, root tokens are ignored and treated as plain user input.
DEMO_MODE: bool = True

# JWT settings — used by app/lib/auth/auth_service.py
JWT_SECRET: str = "dev-secret-change-in-prod"
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRE_MINUTES: int = 30

# Langfuse observability — env-driven. When LANGFUSE_PUBLIC_KEY is unset the
# tracer becomes a no-op so local dev / tests run without external calls.
import os  # noqa: E402

LANGFUSE_PUBLIC_KEY: str | None = os.environ.get("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY: str | None = os.environ.get("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST: str = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")
