# Coding Conventions

**Analysis Date:** 2026-04-18
**Status:** Intended — greenfield project, no source code yet. Conventions derive from spec (`/Users/matthew/Downloads/spec_python.md`) and Python best practices.

## Naming Patterns

**Files:**
- All lowercase with underscores (snake_case): `auth_service.py`, `order_router.py`, `payment_mock.py`
- Router files named after domain: `orders_router.py`, `cart_router.py`
- Service/library files use domain noun: `auth.py`, `catalog.py`, `orders.py`, `cart.py`
- Test files prefixed `test_`: `test_auth.py`, `test_checkout.py`, `test_payment_mock.py`
- Eval dataset files descriptive of category: `positive_cases.json`, `adversarial_cases.json`, `negative_cases.json`
- Config at project root: `config.py`
- Seed loader: `app/lib/seed/seed.py`

**Functions:**
- snake_case throughout: `search_products`, `add_to_cart`, `reserve_inventory`, `get_available_quantity`
- Mock adapter functions match spec interface exactly:
  - `get_available_quantity(product_id: str) -> int`
  - `reserve_inventory(order_id: str, items: list[dict]) -> dict`
  - `ship_order(order_id: str) -> dict`
  - `cancel_order(order_id: str) -> dict`
  - `charge(order_id: str, payment_method: str, amount: float) -> dict`
  - `refund(order_id: str, payment_method: str, amount: float) -> dict`
- Agent tool functions match spec tool set:
  - `search_products`, `get_product_details`, `add_to_cart`, `view_cart`, `checkout`
  - `place_order`, `check_order_status`, `cancel_order`, `return_order`
  - `reset_password`, `set_failure_mode`

**Variables:**
- snake_case: `order_id`, `payment_method`, `unit_price`, `failure_config`
- Module-level constants in SCREAMING_SNAKE_CASE: `FAILURE_CONFIG`, `DEMO_MODE`
- In-memory stores: `users_db`, `products_db`, `carts_db`, `orders_db` (plain dicts/lists)

**Types and Models:**
- Dataclass and Pydantic model names in PascalCase: `User`, `Product`, `Cart`, `CartItem`, `Order`, `OrderItem`, `Variant`
- Literal type aliases for constrained string fields
- Type hints required on all function signatures and model fields

## Data Models

**Preference:** Use `dataclasses` for internal domain objects; use Pydantic models for FastAPI request/response bodies requiring validation.

**Field naming:** snake_case always — `user_id`, `created_at`, `payment_status`, `order_status`, `unit_price`

**Required model shapes from spec:**

```python
# app/lib/auth/models.py
from dataclasses import dataclass

@dataclass
class User:
    id: str
    email: str
    password_hash: str
    created_at: str

# app/lib/catalog/models.py
from dataclasses import dataclass, field

@dataclass
class Variant:
    size: str | None = None
    color: str | None = None

@dataclass
class Product:
    id: str
    name: str
    description: str
    unit_price: float
    inventory: int
    category: str
    image_url: str | None = None
    variants: list[Variant] = field(default_factory=list)

# app/lib/cart/models.py
@dataclass
class CartItem:
    product_id: str
    quantity: int
    unit_price: float

@dataclass
class Cart:
    user_id: str
    items: list[CartItem] = field(default_factory=list)

# app/lib/orders/models.py
from typing import Literal

@dataclass
class OrderItem:
    product_id: str
    quantity: int
    unit_price: float

@dataclass
class Order:
    id: str
    user_id: str
    items: list[OrderItem]
    total_amount: float
    payment_method: Literal["credit_card", "paypal", "apple_pay"]
    payment_status: Literal["pending", "paid", "failed", "refunded"]
    order_status: Literal["placed", "paid", "processing", "shipped", "canceled", "returned"]
    created_at: str
    updated_at: str
```

## Code Style

**Formatting:**
- PEP 8 throughout
- Recommended formatter: `ruff format` (or `black`)
- Line length: 88 characters (black/ruff default)
- Imports sorted: `ruff check --select I` (or `isort`)

**Linting:**
- `ruff` for fast combined linting and import sorting
- Type checking: `mypy` or `pyright` in strict mode

**Type Hints:**
- Required on all function parameters and return types
- Use `str | None` union syntax (Python 3.10+ style) — not `Optional[str]`
- Use built-in generics: `list[dict]`, `dict[str, Any]` — not `List`, `Dict` from `typing`
- Python 3.12+ minimum

## Import Organization

**Order:**
1. Standard library: `os`, `random`, `dataclasses`, `typing`, `uuid`, `datetime`
2. Third-party: `fastapi`, `pydantic`, `langfuse`, `passlib`, `anthropic`
3. Internal — absolute imports from `app.*`

**Rules:**
- Use absolute imports: `from app.lib.orders.models import Order`
- No relative imports except within the same package when clearly scoped
- No wildcard imports (`from module import *`)

## FastAPI Route Handlers

**Location:** `app/api/` — one router file per domain area

**Pattern:**
```python
# app/api/orders_router.py
from fastapi import APIRouter, Depends, HTTPException
from app.lib.orders.service import get_order_service, cancel_order_service
from app.lib.auth.dependencies import get_current_user
from app.lib.auth.models import User

router = APIRouter(prefix="/orders", tags=["orders"])

@router.get("/{order_id}")
async def get_order_endpoint(
    order_id: str,
    current_user: User = Depends(get_current_user),
) -> dict:
    result = get_order_service(order_id=order_id, requesting_user_id=current_user.id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result
```

**Rules:**
- Route handlers are thin — all business logic lives in `app/lib/` service functions
- Validate user ownership in any route accessing user-scoped resources
- Use `Depends()` for auth injection
- Return structured dicts; let FastAPI serialize them

## Service Functions (app/lib/)

**Location:** `app/lib/<domain>/` — module-level functions; no classes required

**Pattern:**
```python
# app/lib/orders/service.py
from app.lib.orders.store import orders_db
from app.lib.orders.models import Order

def cancel_order_service(order_id: str, requesting_user_id: str) -> dict:
    """Cancel an order if owned by the requesting user and in a cancelable state.

    Args:
        order_id: The order to cancel.
        requesting_user_id: ID of the authenticated user making the request.

    Returns:
        Structured result dict with success/failure shape.
    """
    order = orders_db.get(order_id)
    if not order:
        return {
            "success": False,
            "code": "ORDER_NOT_FOUND",
            "message": "Order not found",
            "retryable": False,
        }
    if order.user_id != requesting_user_id:
        return {
            "success": False,
            "code": "UNAUTHORIZED",
            "message": "Access denied",
            "retryable": False,
        }
    # ... business logic
```

## Error Handling

**Structured failure responses — use everywhere a function can fail:**

```python
# Success shape
{"success": True, "data": {...}}

# Failure shape
{
    "success": False,
    "code": "FAILED_TO_CHARGE_CREDIT_CARD",
    "message": "Credit card charge failed in mock payment provider",
    "retryable": True,
}
```

**Rules:**
- Never raise exceptions inside service/lib functions for expected failure states — return structured dicts
- Reserve exceptions for truly unexpected errors (programming errors, missing config)
- FastAPI route handlers translate `success: False` into appropriate HTTP status codes
- `retryable` must always be set — `True` for transient failures (mock errors), `False` for validation or auth failures
- Error `code` values use SCREAMING_SNAKE_CASE strings matching the failure scenario

## Error Injection Pattern

**Config location:** `config.py` at project root

```python
# config.py
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
```

**Injection pattern in mock adapters:**
```python
# app/lib/mocks/payment_mock.py
import random
from config import FAILURE_CONFIG

def charge(order_id: str, payment_method: str, amount: float) -> dict:
    failure_key = f"failed_to_charge_{payment_method}"
    failure_prob = FAILURE_CONFIG.get("payment", {}).get(failure_key, 0.0)
    if random.random() < failure_prob:
        return {
            "success": False,
            "code": failure_key.upper(),
            "message": f"Mock payment failure: {failure_key}",
            "retryable": True,
        }
    return {"success": True, "transaction_id": f"txn_{order_id}"}
```

**Rules:**
- Always use `random.random()` for probability rolls — not `random.randint`, `random.choice`
- Always emit an observability event alongside injected failures
- Read `FAILURE_CONFIG` at call time, not at import time — config mutates via root instructions

## Root Instruction Token

**Parsing location:** `app/lib/guardrails/root_parser.py` — executed before LLM sees the prompt

**Token format:** `[root]: <instruction>`

**Examples:**
```
[root]: make payment fail 100% if payment type is credit card
[root]: warehouse out_of_stock 25%
[root]: disable all failures
```

**Rules:**
- Parse and strip root tokens before the prompt reaches the LLM or any normal request path
- Only process root tokens when `DEMO_MODE=true` environment variable is set
- Log every root instruction at `WARNING` level with acting user context
- Root instructions mutate `FAILURE_CONFIG` in place for the current session
- Never allow customer prompts to reach the root parsing path

## Prompt Path Separation (Guardrails)

**Three separate prompt paths — never merge:**
- `customer_prompt`: end user input — sanitized, scope-enforced, no special privileges
- `operator_prompt`: system-level context injected by the application, not user-controlled
- `root_instruction`: privileged demo/dev-mode override — extracted before LLM processes anything

**Implementation location:** `app/lib/guardrails/`

**Scope enforcement:** Agent rejects off-topic requests (cookie recipes, math problems, accessing other users' data, prompt injection attempts) via guardrail check before tool dispatch.

## Logging

**Framework:** Python standard `logging` module; structured JSON output preferred

**Patterns:**
- Root instruction applied: `WARNING` level, include full instruction text and user ID
- Mock failure triggered: `INFO` level, include failure code and relevant order/product context
- Agent tool call: `DEBUG` level, include inputs and outputs
- Langfuse SDK supplements standard logs for agent/tool/generation traces — both are used

## Comments

**When to comment:**
- Non-obvious probability math or business rule rationale
- Security-sensitive decisions (why a prompt path is isolated)
- Failure injection logic explaining demo intent

**Docstrings:**
- Required on all public service functions and mock adapter functions
- Google-style docstrings with `Args:`, `Returns:` sections
- Single-line docstring acceptable for trivial helpers

## Module Design

**Exports:**
- Each `app/lib/<domain>/` package exposes a clean public interface via `__init__.py`
- Route handlers import from the domain package, not from internal submodules directly

**Router registration:** Explicit in `main.py` — no auto-discovery

---

*Convention analysis: 2026-04-18 — intended conventions for greenfield implementation*
