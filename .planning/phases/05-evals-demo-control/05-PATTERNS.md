# Phase 5: Evals & Demo Control - Pattern Map

**Mapped:** 2026-04-19
**Files analyzed:** 6
**Analogs found:** 6 / 6

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `app/lib/guardrails/root_instruction.py` | utility | request-response | `app/lib/guardrails/guardrails.py` | exact |
| `app/api/chat_router.py` (modify) | controller | request-response | `app/api/chat_router.py` (current) | self |
| `app/lib/evals/datasets/positive.py` | utility | transform | `app/lib/evals/__init__.py` + test parametrize patterns | role-match |
| `app/lib/evals/datasets/negative.py` | utility | transform | same as positive | role-match |
| `app/lib/evals/datasets/adversarial.py` | utility | transform | same as positive | role-match |
| `tests/evals/test_smoke.py` | test | request-response | `tests/integration/test_chat_router.py` | role-match |

---

## Pattern Assignments

### `app/lib/guardrails/root_instruction.py` (utility, request-response)

**Analog:** `app/lib/guardrails/guardrails.py`

**Imports pattern** (guardrails.py lines 1-5):
```python
# app/lib/guardrails/root_instruction.py
# Pure-function root instruction parser for the ShoeStore demo operator interface.
# Patterns compiled once at module load — deterministic, no API calls.
# Source: .planning/phases/05-evals-demo-control/05-CONTEXT.md D-01–D-04
import logging
import re
```

**Module-level compiled patterns** (guardrails.py lines 8-15):
```python
# Compile all patterns once at import — never inside the function
_PAYMENT_PATTERN = re.compile(
    r"payment\s+fail\s+(\d+)%(?:\s+(credit\s+card|paypal|apple\s+pay))?",
    re.IGNORECASE,
)
_WAREHOUSE_STOCK_PATTERN = re.compile(
    r"warehouse\s+out_of_stock\s+(\d+)%", re.IGNORECASE
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

logger = logging.getLogger(__name__)
```

**Core pure-function pattern** (guardrails.py lines 24-52):
```python
def parse_root_instruction(text: str) -> dict:
    """Parse a [root]: operator instruction into FAILURE_CONFIG mutations.

    Pure function — reads text, returns result dict with mutations to apply.
    Caller (chat_router.py) applies mutations to config.FAILURE_CONFIG.

    Args:
        text: Instruction text with [root]: prefix already stripped.

    Returns:
        Success dict:
            {"success": True, "mutations": dict, "message": str}
        Failure dict:
            {"success": False, "mutations": {}, "message": str}
    """
    normalized = text.lower().strip()
    # ... match patterns, build mutations dict ...
    return {"success": True, "mutations": mutations, "message": summary}
    # or on no match:
    return {"success": False, "mutations": {}, "message": f"Unknown root instruction: {text!r}"}
```

**Return shape to copy exactly** (guardrails.py lines 39-52):
```python
# Success shape — mirrors guardrails.py's {"success": True, "data": {...}} but
# uses "mutations" key per D-03 spec:
{"success": True, "mutations": {"warehouse": {"out_of_stock": 0.5}}, "message": "Applied: warehouse out_of_stock 50%"}

# Failure shape — mirrors project error shape from CONVENTIONS.md:
{"success": False, "mutations": {}, "message": "Unknown root instruction: 'set everything to chaos'"}
```

---

### `app/api/chat_router.py` (controller, request-response) — MODIFY

**Analog:** current `app/api/chat_router.py` (self-referential — replace the Phase 4 stub)

**New imports to add** (after existing imports at lines 1-16):
```python
import config  # import the module, not the dict, so mutations are in-place
from app.lib.guardrails.root_instruction import parse_root_instruction
```

**Replace stub block** (current lines 78-85) with real parse+apply flow:
```python
    if DEMO_MODE and user_message.startswith("[root]:"):
        raw_instruction = user_message[len("[root]:"):].strip()
        logger.warning(
            "Root instruction received from user_id=%s: %r",
            current_user.id,
            raw_instruction,
        )
        if not raw_instruction:
            return JSONResponse({"reply": "Root instruction received but was empty."})

        result = parse_root_instruction(raw_instruction)
        if result["success"]:
            # Apply mutations to FAILURE_CONFIG in-place (config module import)
            for section, keys in result["mutations"].items():
                for key, value in keys.items():
                    config.FAILURE_CONFIG[section][key] = value
            logger.warning(
                "FAILURE_CONFIG mutated by user_id=%s: %r",
                current_user.id,
                result["mutations"],
            )
        else:
            logger.warning(
                "Unrecognized root instruction from user_id=%s: %r",
                current_user.id,
                raw_instruction,
            )
        return JSONResponse({"reply": result["message"]})
```

**Key**: import `config` as a module (not `from config import FAILURE_CONFIG`) so mutations to `config.FAILURE_CONFIG[section][key]` are visible to mock adapters that also imported the module-level dict. The dict is mutated in-place — no reassignment needed.

**Existing patterns to preserve** (lines 88-112 — do not touch):
```python
    # D-06: Layer 1 guardrail — injection pattern check
    guard = check_message(user_message)
    if not guard["success"]:
        ...
    result = await agent.run(user_id=current_user.id, user=current_user, message=user_message)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("message", "Agent error"))
    return JSONResponse({"reply": result["data"]["reply"]})
```

---

### `app/lib/evals/datasets/positive.py` (utility, transform)

**Analog:** `tests/unit/test_guardrails.py` parametrize list + CONTEXT.md D-07–D-09

**File structure pattern:**
```python
# app/lib/evals/datasets/positive.py
# Positive eval cases — successful happy-path agent interactions.
# Format: {input, expected_trajectory, expected_output, tags}
# Source: .planning/REQUIREMENTS.md TEST-01, CONTEXT.md D-09
from deepeval.dataset import EvaluationDataset

CASES: list[dict] = [
    {
        "input": "Show me running shoes",
        "expected_trajectory": ["search_products"],
        "expected_output": "Here are some running shoes",
        "tags": ["positive", "search", "TEST-01"],
    },
    {
        "input": "Add the Nike Air Max size 10 to my cart",
        "expected_trajectory": ["search_products", "get_product_details", "add_to_cart"],
        "expected_output": "added to your cart",
        "tags": ["positive", "cart", "TEST-01"],
    },
    {
        "input": "Check out my cart with credit card",
        "expected_trajectory": ["view_cart", "checkout"],
        "expected_output": "order confirmed",
        "tags": ["positive", "checkout", "TEST-01"],
    },
    {
        "input": "What's the status of my order?",
        "expected_trajectory": ["get_order_status"],
        "expected_output": "your order",
        "tags": ["positive", "order-status", "TEST-01"],
    },
    {
        "input": "Cancel my order",
        "expected_trajectory": ["cancel_order"],
        "expected_output": "cancelled",
        "tags": ["positive", "cancel", "TEST-01"],
    },
]

dataset = EvaluationDataset(test_cases=[])  # populated by runner
```

---

### `app/lib/evals/datasets/negative.py` (utility, transform)

**Analog:** same as positive.py — identical structure, different case content (D-10)

**File structure:** identical to `positive.py` — same imports, same `CASES: list[dict]` + `dataset` pattern. Content covers: out-of-stock checkout, payment failure checkout, cancel without order ID, return on non-returnable order, wrong-user order access. Tags: `["negative", "<scenario>", "TEST-02"]`.

---

### `app/lib/evals/datasets/adversarial.py` (utility, transform)

**Analog:** same as positive.py — identical structure, different case content (D-11)

**File structure:** identical to `positive.py`. Content covers: prompt injection attempt, off-topic request (cookie recipe), typos ("Cansel odrer"), sarcasm after failure, all-caps input. Tags: `["adversarial", "<scenario>", "TEST-03"]`.

**Note:** The `__init__.py` for the `datasets/` subpackage follows the existing package marker pattern from `app/lib/guardrails/__init__.py` and `app/lib/evals/__init__.py`:
```python
# app.lib.evals.datasets package marker (Phase 5)
```

---

### `tests/evals/test_smoke.py` (test, request-response)

**Analog:** `tests/integration/test_chat_router.py` + `tests/integration/conftest.py`

**Imports pattern** (test_chat_router.py lines 1-7):
```python
# tests/evals/test_smoke.py
# Smoke runner: one real Anthropic API call per eval dataset (3 total).
# Requires ANTHROPIC_API_KEY in environment — skips if absent.
# Source: CONTEXT.md D-12, D-13
import logging
import os

import pytest

from app.lib.agent import agent
from app.lib.evals.datasets.positive import CASES as POSITIVE_CASES
from app.lib.evals.datasets.negative import CASES as NEGATIVE_CASES
from app.lib.evals.datasets.adversarial import CASES as ADVERSARIAL_CASES
from app.lib.seed.seed import seed
from app.lib.auth.store import users_db, reset_tokens_db
from app.lib.cart.store import carts_db
from app.lib.orders.store import orders_db
from app.lib.catalog.store import products_db
from app.lib.agent import history as agent_history

logger = logging.getLogger(__name__)
```

**Skip pattern when API key absent** (mirrors pytest.mark pattern seen in test_payment_mock.py):
```python
pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live eval smoke run",
)
```

**Store reset fixture** (conftest.py lines 13-29 — copy directly into test file since no shared evals conftest exists yet):
```python
@pytest.fixture(autouse=True)
def reset_stores():
    """Reset all in-memory stores and re-seed before each smoke test."""
    users_db.clear()
    reset_tokens_db.clear()
    carts_db.clear()
    orders_db.clear()
    products_db.clear()
    agent_history._history.clear()
    seed()
    yield
    users_db.clear()
    reset_tokens_db.clear()
    carts_db.clear()
    orders_db.clear()
    products_db.clear()
    agent_history._history.clear()
```

**Seeded user fixture** (conftest.py lines 37-51 — alice from seed data):
```python
@pytest.fixture
def smoke_user():
    """Return the seeded alice User object for agent.run() calls."""
    from app.lib.auth.store import users_db
    return next(u for u in users_db.values() if u.email == "alice@example.com")
```

**Core smoke test pattern** (test_chat_router.py lines 45-58 — async agent.run call):
```python
@pytest.mark.asyncio
async def test_smoke_positive(smoke_user):
    case = POSITIVE_CASES[0]
    logger.info("Smoke positive: input=%r", case["input"])
    result = await agent.run(
        user_id=smoke_user.id,
        user=smoke_user,
        message=case["input"],
    )
    assert "success" in result, f"agent.run returned no 'success' key: {result!r}"

@pytest.mark.asyncio
async def test_smoke_negative(smoke_user):
    case = NEGATIVE_CASES[0]
    logger.info("Smoke negative: input=%r", case["input"])
    result = await agent.run(
        user_id=smoke_user.id,
        user=smoke_user,
        message=case["input"],
    )
    assert "success" in result, f"agent.run returned no 'success' key: {result!r}"

@pytest.mark.asyncio
async def test_smoke_adversarial(smoke_user):
    case = ADVERSARIAL_CASES[0]
    logger.info("Smoke adversarial: input=%r", case["input"])
    result = await agent.run(
        user_id=smoke_user.id,
        user=smoke_user,
        message=case["input"],
    )
    assert "success" in result, f"agent.run returned no 'success' key: {result!r}"
```

**Note on `__init__.py`:** `tests/evals/` needs its own `__init__.py` — follow the pattern from `tests/unit/__init__.py` and `tests/integration/__init__.py` (empty package markers).

---

## Shared Patterns

### Return Shape (success/failure dicts)
**Source:** `app/lib/guardrails/guardrails.py` lines 39-52, `config.py` lines 7-20
**Apply to:** `root_instruction.py`
```python
# Success
{"success": True, "mutations": {...}, "message": "Applied: ..."}
# Failure / unknown instruction
{"success": False, "mutations": {}, "message": "Unknown root instruction: ..."}
```

### Warning Logger Pattern
**Source:** `app/api/chat_router.py` lines 79-83
**Apply to:** `root_instruction.py` (called at call site in router), `chat_router.py` (already in place)
```python
logger.warning(
    "Root instruction received from user_id=%s: %r",
    current_user.id,
    raw_instruction,
)
```

### Module-Level Compiled Regex
**Source:** `app/lib/guardrails/guardrails.py` lines 8-15
**Apply to:** `root_instruction.py`
```python
# Compile once at module load, never inside the parse function
_PATTERN_NAME = re.compile(r"...", re.IGNORECASE)
```

### FAILURE_CONFIG Mutation (in-place dict access)
**Source:** `config.py` lines 7-20 + `tests/unit/test_payment_mock.py` lines 7-8
**Apply to:** `chat_router.py` (apply mutations section)
```python
# Import the module, not the dict, to ensure in-place mutation is visible
import config
config.FAILURE_CONFIG[section][key] = value  # in-place, no reassignment
```

### Package Marker `__init__.py`
**Source:** `app/lib/guardrails/__init__.py`, `app/lib/evals/__init__.py`
**Apply to:** `app/lib/evals/datasets/__init__.py`, `tests/evals/__init__.py`
```python
# app.lib.evals.datasets package marker (Phase 5)
```

### Store Reset Fixture
**Source:** `tests/integration/conftest.py` lines 13-29
**Apply to:** `tests/evals/test_smoke.py` (inline — no shared evals conftest yet)

---

## No Analog Found

All files have analogs. No entries needed in this section.

---

## Metadata

**Analog search scope:** `app/lib/guardrails/`, `app/api/`, `app/lib/evals/`, `tests/unit/`, `tests/integration/`, `config.py`
**Files scanned:** 8 source files read
**Pattern extraction date:** 2026-04-19
