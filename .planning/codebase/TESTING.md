# Testing Patterns

**Analysis Date:** 2026-04-18
**Status:** Intended — greenfield project, no source code yet. Patterns derive from spec (`/Users/matthew/Downloads/spec_python.md`) and Python best practices.

## Test Framework

**Runner:**
- `pytest` — unit and integration tests
- Config: `pytest.ini` or `pyproject.toml [tool.pytest.ini_options]`

**Assertion Library:**
- pytest built-in assertions (no separate library needed)

**LLM Eval Framework:**
- `deepeval` or `promptfoo` — synthetic dataset generation and LLM response evaluation

**Browser Automation:**
- `playwright` (Python) — `playwright-python` — end-to-end browser tests

**Run Commands:**
```bash
pytest                          # Run all unit and integration tests
pytest -v                       # Verbose output
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only
pytest --cov=app --cov-report=term-missing  # With coverage report
playwright test                 # Run E2E browser tests (if using pytest-playwright)
pytest tests/e2e/               # E2E via pytest-playwright plugin
```

## Test File Organization

**Location:** Separate `tests/` directory mirroring `app/` structure

**Naming:** `test_<module>.py` — e.g., `test_auth.py`, `test_payment_mock.py`, `test_checkout_flow.py`

**Structure:**
```
tests/
├── unit/
│   ├── test_auth.py
│   ├── test_catalog.py
│   ├── test_cart.py
│   ├── test_orders.py
│   ├── test_payment_mock.py
│   ├── test_warehouse_mock.py
│   └── test_guardrails.py
├── integration/
│   ├── test_checkout_flow.py
│   ├── test_cancel_flow.py
│   ├── test_return_flow.py
│   └── test_chat_agent.py
├── e2e/
│   ├── test_signup_login.py
│   ├── test_browse_cart_checkout.py
│   ├── test_order_lookup.py
│   ├── test_order_cancellation.py
│   └── test_chatbot_support_flow.py
├── evals/
│   ├── datasets/
│   │   ├── positive_cases.json
│   │   ├── negative_cases.json
│   │   ├── adversarial_cases.json
│   │   └── synthetic_cases.json
│   └── test_eval_runner.py
└── conftest.py
```

## Test Structure

**Suite organization:**
```python
# tests/unit/test_payment_mock.py
import pytest
from app.lib.mocks.payment_mock import charge, refund
from config import FAILURE_CONFIG

class TestPaymentMockCharge:
    def test_charge_succeeds_when_failure_prob_zero(self):
        FAILURE_CONFIG["payment"]["failed_to_charge_credit_card"] = 0.0
        result = charge(order_id="ord_1", payment_method="credit_card", amount=99.99)
        assert result["success"] is True
        assert "transaction_id" in result

    def test_charge_fails_when_failure_prob_one(self):
        FAILURE_CONFIG["payment"]["failed_to_charge_credit_card"] = 1.0
        result = charge(order_id="ord_1", payment_method="credit_card", amount=99.99)
        assert result["success"] is False
        assert result["code"] == "FAILED_TO_CHARGE_CREDIT_CARD"
        assert result["retryable"] is True

    def test_failure_response_shape(self):
        FAILURE_CONFIG["payment"]["failed_to_charge_credit_card"] = 1.0
        result = charge(order_id="ord_1", payment_method="credit_card", amount=99.99)
        assert "success" in result
        assert "code" in result
        assert "message" in result
        assert "retryable" in result
```

**Patterns:**
- `conftest.py` for shared fixtures: fresh in-memory store state, seeded test users, seeded products
- Each test function resets relevant in-memory stores or uses fixture-provided isolated copies
- No global state leaking between tests — use fixtures with `scope="function"` by default

## Mocking / Isolation Strategy

**Primary isolation strategy: Mock adapters with configurable failure injection**

No database mocking is needed — the entire persistence layer is in-memory Python dicts and lists. Tests operate directly against the in-memory stores.

**Failure injection as test doubles:**

Set `FAILURE_CONFIG` probabilities to `0.0` (always succeed) or `1.0` (always fail) to control mock adapter behavior deterministically in tests. This replaces typical `unittest.mock` patching of external services.

```python
# tests/conftest.py
import pytest
from config import FAILURE_CONFIG

@pytest.fixture(autouse=True)
def reset_failure_config():
    """Reset failure injection config to zero before each test."""
    original = {k: dict(v) for k, v in FAILURE_CONFIG.items()}
    for service in FAILURE_CONFIG:
        for key in FAILURE_CONFIG[service]:
            FAILURE_CONFIG[service][key] = 0.0
    yield
    for service, values in original.items():
        FAILURE_CONFIG[service].update(values)

@pytest.fixture
def payment_always_fails():
    """Fixture that makes all payment charges fail."""
    FAILURE_CONFIG["payment"]["failed_to_charge_credit_card"] = 1.0
    FAILURE_CONFIG["payment"]["failed_to_charge_paypal"] = 1.0
    FAILURE_CONFIG["payment"]["failed_to_charge_apple_pay"] = 1.0
    yield
```

**When to use `unittest.mock.patch`:**
- To mock the `random.random()` call directly when testing boundary probability behavior
- To mock Langfuse SDK calls in unit tests (avoid real network calls)
- To mock LLM API calls (Anthropic/OpenAI) in agent unit tests

```python
# Mocking random for deterministic probability tests
from unittest.mock import patch

def test_charge_fails_at_exact_threshold():
    FAILURE_CONFIG["payment"]["failed_to_charge_credit_card"] = 0.5
    with patch("app.lib.mocks.payment_mock.random.random", return_value=0.49):
        result = charge(order_id="ord_1", payment_method="credit_card", amount=50.0)
        assert result["success"] is False
```

**What NOT to mock:**
- In-memory stores (`users_db`, `orders_db`, etc.) — use them directly; reset via fixtures
- Service functions — test the real implementation
- Data models — use real dataclass/Pydantic instances

## Fixtures and Factories

**Test data (in `tests/conftest.py`):**

```python
# tests/conftest.py
import pytest
from app.lib.auth.models import User
from app.lib.catalog.models import Product
from app.lib.orders.models import Order, OrderItem
from app.lib.seed.seed import seed_all
from app.lib.auth.store import users_db
from app.lib.orders.store import orders_db
from app.lib.catalog.store import products_db
from app.lib.cart.store import carts_db

@pytest.fixture(autouse=True)
def fresh_stores():
    """Clear all in-memory stores and re-seed before each test."""
    users_db.clear()
    products_db.clear()
    orders_db.clear()
    carts_db.clear()
    seed_all()
    yield

@pytest.fixture
def test_user() -> User:
    return users_db["test_user_1"]

@pytest.fixture
def test_product() -> Product:
    return next(iter(products_db.values()))
```

**Location:** `tests/conftest.py` for global fixtures; domain-specific fixtures in `tests/unit/conftest.py` or `tests/integration/conftest.py`

## Eval Dataset Format

**Required shape for each test case:**
```json
{
  "input": "I want to cancel my order",
  "expected_trajectory": ["check_order_status", "cancel_order"],
  "expected_output": "Your order has been canceled.",
  "tags": ["cancel", "positive", "explicit_intent"]
}
```

**Fields:**
- `input`: raw user message string
- `expected_trajectory`: ordered list of agent tool calls expected
- `expected_output`: expected final agent response (used for semantic similarity scoring)
- `tags`: list of category labels for filtering and reporting

**Dataset files location:** `app/lib/evals/datasets/` or `tests/evals/datasets/`

## Test Categories

**Positive cases** — `tests/evals/datasets/positive_cases.json`:
- Successful product search
- Successful add to cart
- Successful checkout with each payment method
- Successful order status lookup
- Successful cancellation when order is in cancelable state

**Negative cases** — `tests/evals/datasets/negative_cases.json`:
- Out of stock during checkout (warehouse failure)
- Payment failure during checkout
- Cancel order without providing order ID
- Return request for non-returnable order status
- Order access attempt by wrong user

**Adversarial / red-team cases** — `tests/evals/datasets/adversarial_cases.json`:
- Unrelated task requests: "give me a cookie recipe"
- Math problem requests: "what is 142 * 37"
- Prompt injection attempts: "ignore previous instructions and..."
- Attempts to access another user's order data

**Synthetic cases** — `tests/evals/datasets/synthetic_cases.json` (generated via deepeval or promptfoo):

| Dimension | Example Input |
|---|---|
| Angry tone | "WHERE IS MY ORDER THIS IS RIDICULOUS" |
| Polite tone | "Could you please help me find running shoes?" |
| Typos | "Cansel odrer 1234 pleese" |
| Implicit intent | "I don't want that shirt anymore" |
| Missing info | "Cancel my order" (no order ID) |
| Broken grammar | "shoe want buy size 10 red" |
| Abbreviations | "chk ord status asap" |
| Profanity/all caps | "THIS PIECE OF JUNK DIDN'T ARRIVE FIX IT NOW" |
| Repetition | Same request sent 3 times in a row |
| Sarcasm after failure | "Oh great, another failure. Wonderful system." |

## Coverage

**Requirements:** No hard enforcement defined in spec; aim for meaningful coverage of service functions and mock adapters

**View coverage:**
```bash
pytest --cov=app --cov-report=term-missing
pytest --cov=app --cov-report=html        # HTML report in htmlcov/
```

**Priority areas for coverage:**
- `app/lib/mocks/` — payment and warehouse adapters
- `app/lib/orders/` — order lifecycle transitions
- `app/lib/guardrails/` — prompt injection and root instruction parsing
- `app/lib/agent/` — tool dispatch and failure recovery

## Test Types

**Unit Tests (`tests/unit/`):**
- Single service function or mock adapter function in isolation
- In-memory stores used directly — no mocking needed
- Failure injection via `FAILURE_CONFIG` overrides
- Fast; no I/O or network

**Integration Tests (`tests/integration/`):**
- Full request flow through FastAPI route handler → service → mock adapter
- Uses `httpx.AsyncClient` with FastAPI `TestClient` or async test client
- Tests multi-step flows: checkout (payment + warehouse + order creation)
- Verifies structured response shapes end-to-end

**E2E Tests (`tests/e2e/`):**
- `playwright-python` driving a real browser against running FastAPI server
- Covers: sign up/login, browse/search, add to cart, checkout success, checkout failure, order lookup, order cancellation, chatbot support flow
- Run against local dev server started before the test suite

## Common Patterns

**Async testing (FastAPI endpoints):**
```python
# tests/integration/test_checkout_flow.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_checkout_success(test_user, test_product):
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Login
        login_resp = await client.post("/auth/login", json={
            "email": test_user.email, "password": "testpassword"
        })
        token = login_resp.json()["token"]

        # Add to cart and checkout
        await client.post("/cart/add", json={
            "product_id": test_product.id, "quantity": 1
        }, headers={"Authorization": f"Bearer {token}"})

        result = await client.post("/orders/checkout", json={
            "payment_method": "credit_card"
        }, headers={"Authorization": f"Bearer {token}"})

        assert result.status_code == 200
        assert result.json()["success"] is True
```

**Error/failure testing:**
```python
def test_checkout_fails_on_payment_failure(payment_always_fails, test_user, test_product):
    # payment_always_fails fixture sets FAILURE_CONFIG["payment"][...] = 1.0
    result = checkout_service(
        user_id=test_user.id,
        payment_method="credit_card",
    )
    assert result["success"] is False
    assert result["retryable"] is True
    assert "code" in result
```

**Playwright E2E pattern:**
```python
# tests/e2e/test_browse_cart_checkout.py
from playwright.sync_api import Page

def test_add_to_cart_and_checkout(page: Page, live_server_url: str):
    page.goto(f"{live_server_url}/products")
    page.click(".product-card:first-child .add-to-cart-btn")
    page.goto(f"{live_server_url}/cart")
    page.click("#checkout-btn")
    page.select_option("#payment-method", "credit_card")
    page.click("#confirm-order-btn")
    assert page.locator(".order-confirmation").is_visible()
```

## Observability During Tests

**Langfuse traces:**
- Agent and tool calls emit Langfuse traces during integration and E2E test runs
- Use Langfuse trace output to debug unexpected tool selection, hallucination, or wrong failure recovery
- In unit tests, Langfuse SDK calls are mocked to avoid network I/O (`unittest.mock.patch` on the Langfuse client)

**Test run observability:**
- Failed mock injections log at `INFO` level — visible in pytest output with `-s` flag
- Root instruction parsing logs at `WARNING` level — always visible in test output

---

*Testing analysis: 2026-04-18 — intended patterns for greenfield implementation*
