# app/lib/guardrails/guardrails.py
# Prompt injection detection for the ShoeStore chat agent.
# Patterns are compiled once at module load — they are static and never mutate.
# Source: .planning/phases/04-claude-agent/04-CONTEXT.md D-06, D-07
import re

# Compiled regex patterns that identify known prompt injection phrases.
# Order does not matter — all are checked on every message.
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(previous|prior|all)\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+your\s+system\s+prompt", re.IGNORECASE),
    re.compile(r"pretend\s+you\s+are", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+a", re.IGNORECASE),
    re.compile(r"forget\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
]

# Polite scope refusal message (D-07) — same text for all injection variants.
_SCOPE_REFUSAL = (
    "I can only help with ShoeStore shopping and orders. "
    "Is there something I can help you find or order?"
)


def check_message(message: str) -> dict:
    """Check a user message for prompt injection patterns.

    Iterates all compiled injection patterns and returns a failure dict on the
    first match. Returns a success dict if no patterns match.

    Guardrails always run regardless of DEMO_MODE — they are a security layer,
    not a demo feature. The [root]: token is stripped by the route handler
    (D-14) before this function is called.

    Args:
        message: Raw user message text (after [root]: stripping by route handler).

    Returns:
        Success dict if message is clean:
            {"success": True, "data": {"message": str}}
        Failure dict if injection detected:
            {"success": False, "code": "INJECTION_DETECTED",
             "message": str, "retryable": False}
    """
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(message):
            return {
                "success": False,
                "code": "INJECTION_DETECTED",
                "message": _SCOPE_REFUSAL,
                "retryable": False,
            }
    return {"success": True, "data": {"message": message}}
