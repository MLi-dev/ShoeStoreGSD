# Phase 1: Domain Foundation - Pattern Map

**Mapped:** 2026-04-18
**Files analyzed:** 22 (new files in greenfield project)
**Analogs found:** 0 / 22 — greenfield project, no source code exists

---

## File Classification

| New File | Role | Data Flow | Closest Analog | Match Quality |
|----------|------|-----------|----------------|---------------|
| `pyproject.toml` | config | — | none | greenfield — no analog |
| `main.py` | config | request-response | none | greenfield — no analog |
| `config.py` | config | — | none | greenfield — no analog |
| `app/__init__.py` | config | — | none | greenfield — no analog |
| `app/lib/auth/__init__.py` | config | — | none | greenfield — no analog |
| `app/lib/auth/models.py` | model | — | none | greenfield — no analog |
| `app/lib/auth/store.py` | store | CRUD | none | greenfield — no analog |
| `app/lib/catalog/__init__.py` | config | — | none | greenfield — no analog |
| `app/lib/catalog/models.py` | model | — | none | greenfield — no analog |
| `app/lib/catalog/store.py` | store | CRUD | none | greenfield — no analog |
| `app/lib/cart/__init__.py` | config | — | none | greenfield — no analog |
| `app/lib/cart/models.py` | model | — | none | greenfield — no analog |
| `app/lib/cart/store.py` | store | CRUD | none | greenfield — no analog |
| `app/lib/orders/__init__.py` | config | — | none | greenfield — no analog |
| `app/lib/orders/models.py` | model | — | none | greenfield — no analog |
| `app/lib/orders/store.py` | store | CRUD | none | greenfield — no analog |
| `app/lib/seed/__init__.py` | config | — | none | greenfield — no analog |
| `app/lib/seed/seed.py` | utility | batch | none | greenfield — no analog |
| `tests/__init__.py` | config | — | none | greenfield — no analog |
| `tests/unit/__init__.py` | config | — | none | greenfield — no analog |
| `tests/unit/test_models.py` | test | — | none | greenfield — no analog |
| `tests/unit/test_stores.py` | test | CRUD | none | greenfield — no analog |
| `tests/unit/test_seed.py` | test | batch | none | greenfield — no analog |

---

## Pattern Assignments

All patterns below are sourced from CONVENTIONS.md, RESEARCH.md, and the project spec. There are no existing source files to copy from.

---

### `pyproject.toml` (config)

**Source:** RESEARCH.md Pattern 1 + Standard Stack section

**Full content pattern:**
```toml
[project]
name = "shoestore"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.136.0",
    "uvicorn[standard]>=0.44.0",
    "pydantic>=2.13.2",
    "pydantic-settings>=2.13.1",
    "passlib>=1.7.4",
    "bcrypt>=5.0.0",
    "itsdangerous>=2.2.0",
]

[dependency-groups]
dev = [
    "pytest>=9.0.3",
    "pytest-asyncio>=1.3.0",
    "ruff>=0.9.0",
    "mypy>=1.0.0",
    "httpx>=0.28.1",
    "playwright>=1.58.0",
]

[tool.uv]
package = false

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
pythonpath = ["."]

[tool.ruff]
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I"]
```

**Critical details:**
- `[tool.uv] package = false` is mandatory — prevents uv from trying to install `app/` as a distribution package in flat layout
- `pythonpath = ["."]` in `[tool.pytest.ini_options]` ensures `from app.lib...` absolute imports resolve when running `pytest` directly (belt-and-suspenders per RESEARCH.md Open Question 1)
- `asyncio_mode = "auto"` means no `@pytest.mark.asyncio` decorator needed on async test functions
- Runtime deps in `[project.dependencies]`, dev-only deps in `[dependency-groups] dev` — never mix them

---

### `main.py` (config, request-response)

**Source:** RESEARCH.md Pattern 2 + Code Examples section

**Full content pattern:**
```python
# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.lib.seed.seed import seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once before first request — populate all in-memory stores
    seed()
    yield
    # Shutdown: nothing to clean up for in-memory stores


app = FastAPI(title="ShoeStore AI Demo", lifespan=lifespan)
# No routers registered in Phase 1 — added in Phase 2+
```

**Critical details:**
- `lifespan` replaces deprecated `@app.on_event("startup")` — do not use the deprecated form
- `seed()` called before `yield` — any exception prevents app from starting
- No router registration in Phase 1 — `app` is a bare skeleton so `uvicorn main:app` starts cleanly

---

### `config.py` (config)

**Source:** RESEARCH.md Code Examples section + CONVENTIONS.md Error Injection Pattern

**Full content pattern:**
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

DEMO_MODE: bool = True  # Set False for production
```

**Critical details:**
- `FAILURE_CONFIG` shape is fixed — mock adapters (Phase 3+) read from it at call time, not import time
- Constants use `SCREAMING_SNAKE_CASE` per CONVENTIONS.md
- Type annotation `dict[str, dict[str, float]]` required — use built-in generics (no `Dict` from `typing`)
- Phase 1 scaffolds this file exactly; later phases add `pydantic-settings` Settings class if env-var loading is needed

---

### `app/lib/auth/models.py` (model)

**Source:** CONVENTIONS.md Data Models section

**Full content pattern:**
```python
# app/lib/auth/models.py
from dataclasses import dataclass


@dataclass
class User:
    id: str
    email: str
    password_hash: str
    created_at: str
```

**Critical details:**
- Plain `@dataclass` — not Pydantic. Pydantic is reserved for FastAPI request/response schemas
- All fields required (no defaults) — fine since fields with defaults come after fields without; none here
- `created_at: str` stores ISO-formatted UTC timestamp as string
- `password_hash` stores bcrypt hash string (e.g., `$2b$12$...`) — never plaintext password

---

### `app/lib/catalog/models.py` (model)

**Source:** CONVENTIONS.md Data Models section

**Full content pattern:**
```python
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
```

**Critical details:**
- `field(default_factory=list)` is mandatory for `variants` — never `variants: list[Variant] = []` (shared mutable default bug)
- Fields without defaults (`id`, `name`, etc.) must appear before fields with defaults (`image_url`, `variants`)
- Use `str | None` union syntax — not `Optional[str]`
- Use `list[Variant]` built-in generic — not `List[Variant]` from `typing`

---

### `app/lib/cart/models.py` (model)

**Source:** CONVENTIONS.md Data Models section

**Full content pattern:**
```python
# app/lib/cart/models.py
from dataclasses import dataclass, field


@dataclass
class CartItem:
    product_id: str
    quantity: int
    unit_price: float


@dataclass
class Cart:
    user_id: str
    items: list[CartItem] = field(default_factory=list)
```

**Critical details:**
- `field(default_factory=list)` for `items` — same mutable default rule as `Product.variants`
- `CartItem.unit_price` captures price at time of add-to-cart — not looked up live (avoids price drift)
- Phase 1 scaffolds these models; no cart service logic until Phase 2+

---

### `app/lib/orders/models.py` (model)

**Source:** CONVENTIONS.md Data Models section

**Full content pattern:**
```python
# app/lib/orders/models.py
from dataclasses import dataclass, field
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

**Critical details:**
- `Literal` is the only `typing` import needed here — status fields must use these exact string values
- `items: list[OrderItem]` has no default — caller must always provide the list
- `payment_status` and `order_status` are separate fields — payment can succeed while order is later canceled
- Per CLAUDE.md: Returns are allowed on paid/processing/shipped orders — the `order_status` Literal includes `"returned"`

---

### `app/lib/auth/store.py` (store, CRUD)

**Source:** CONVENTIONS.md + RESEARCH.md Pattern 4

**Full content pattern:**
```python
# app/lib/auth/store.py
from app.lib.auth.models import User

users_db: dict[str, User] = {}
```

**Critical details:**
- Module-level dict, empty at import time — populated only by `seed()` at startup
- Key is `user.id` (UUID string)
- Never inline data here: `users_db = {"abc": User(...)}` at module level is forbidden

---

### `app/lib/catalog/store.py` (store, CRUD)

**Source:** CONVENTIONS.md + RESEARCH.md Pattern 4

**Full content pattern:**
```python
# app/lib/catalog/store.py
from app.lib.catalog.models import Product

products_db: dict[str, Product] = {}
```

**Critical details:**
- Key is `product.id` (UUID string)
- Same empty-at-import rule as `users_db`

---

### `app/lib/cart/store.py` (store, CRUD)

**Source:** CONVENTIONS.md + RESEARCH.md Pattern 4

**Full content pattern:**
```python
# app/lib/cart/store.py
from app.lib.cart.models import Cart

carts_db: dict[str, Cart] = {}
```

**Critical details:**
- Key is `user_id` (one cart per user)
- Not populated by `seed()` in Phase 1 — empty until users add items via API (Phase 2+)

---

### `app/lib/orders/store.py` (store, CRUD)

**Source:** CONVENTIONS.md + RESEARCH.md Pattern 4

**Full content pattern:**
```python
# app/lib/orders/store.py
from app.lib.orders.models import Order

orders_db: dict[str, Order] = {}
```

**Critical details:**
- Key is `order.id` (UUID string)
- Populated by `seed()` with 3 prior orders (1 paid, 1 shipped, 1 canceled) per D-07

---

### `app/lib/seed/seed.py` (utility, batch)

**Source:** RESEARCH.md Pattern 5, Code Examples (seed.py structure), Patterns 3 and 7

**Imports pattern:**
```python
# app/lib/seed/seed.py
import uuid
from datetime import datetime, timezone
from passlib.context import CryptContext

from app.lib.auth.models import User
from app.lib.auth.store import users_db
from app.lib.catalog.models import Product, Variant
from app.lib.catalog.store import products_db
from app.lib.orders.models import Order, OrderItem
from app.lib.orders.store import orders_db
```

**Core structure pattern:**
```python
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed() -> None:
    """Populate all in-memory stores with demo data.

    Called once from FastAPI lifespan before serving requests.
    Idempotent if stores are cleared first.
    """
    _seed_users()
    _seed_products()
    _seed_orders()


def clear_and_reseed() -> None:
    """Clear all stores and re-run seed. Useful for test isolation."""
    users_db.clear()
    products_db.clear()
    orders_db.clear()
    seed()
```

**Password hashing pattern (inside `_seed_users`, not at module level):**
```python
def _seed_users() -> None:
    alice = User(
        id=str(uuid.uuid4()),
        email="alice@example.com",
        password_hash=_pwd_context.hash("alice-password"),
        created_at=datetime.now(tz=timezone.utc).isoformat(),
    )
    users_db[alice.id] = alice
```

**Product seed pattern (inside `_seed_products`):**
```python
def _seed_products() -> None:
    _add(Product(
        id=str(uuid.uuid4()),
        name="TrailBlaze X9",
        description="...",
        unit_price=129.99,
        inventory=42,
        category="running",
        variants=[
            Variant(size="10", color="midnight black"),
            Variant(size="11", color="midnight black"),
        ],
    ))
    # ... 14 more products

def _add(product: Product) -> None:
    products_db[product.id] = product
```

**Order seed pattern (inside `_seed_orders`, references user IDs stored in `_alice_id`/`_bob_id`):**
```python
def _seed_orders() -> None:
    # Lookup seeded users by email to get stable IDs
    alice = next(u for u in users_db.values() if u.email == "alice@example.com")
    bob = next(u for u in users_db.values() if u.email == "bob@example.com")
    now = datetime.now(tz=timezone.utc).isoformat()

    paid_order = Order(
        id=str(uuid.uuid4()),
        user_id=alice.id,
        items=[OrderItem(product_id="...", quantity=1, unit_price=89.99)],
        total_amount=89.99,
        payment_method="credit_card",
        payment_status="paid",
        order_status="paid",
        created_at=now,
        updated_at=now,
    )
    orders_db[paid_order.id] = paid_order
    # ... shipped order, canceled order
```

**Critical details:**
- `_pwd_context` is module-level (CryptContext object is cheap to create); `_pwd_context.hash(...)` is called inside `_seed_users()` body, not at module level — avoids slow bcrypt at import time
- `clear_and_reseed()` helper is included (per Claude's Discretion in D-CONTEXT) — aids test isolation
- Use `datetime.now(tz=timezone.utc).isoformat()` for all timestamps — UTC-aware, consistent format
- Use `str(uuid.uuid4())` for all IDs — not `random.randint` or sequential ints
- 15 products, 3 per category: running, hiking, slides, sandals, socks (per D-05)
- Canonical test user emails `alice@example.com` and `bob@example.com` must match exactly — eval datasets in Phase 5 reference these (per CONTEXT.md specifics)
- Product names should be demo-worthy: e.g., "TrailBlaze X9 Running Shoe", "Summit Pro Hiker", "CloudSlide Comfort" — not "Product 1"
- Import order: stdlib → third-party → internal (absolute `from app.lib...`)

---

### `tests/unit/test_models.py` (test)

**Source:** RESEARCH.md Validation Architecture + CONVENTIONS.md model shapes

**Pattern:**
```python
# tests/unit/test_models.py
from app.lib.auth.models import User
from app.lib.catalog.models import Product, Variant
from app.lib.cart.models import Cart, CartItem
from app.lib.orders.models import Order, OrderItem


def test_user_instantiation():
    user = User(id="u1", email="test@example.com", password_hash="$2b$...", created_at="2026-01-01T00:00:00+00:00")
    assert user.id == "u1"
    assert user.email == "test@example.com"


def test_product_variants_default_empty():
    product = Product(id="p1", name="Test Shoe", description="desc", unit_price=99.0, inventory=10, category="running")
    assert product.variants == []


def test_two_products_do_not_share_variants():
    p1 = Product(id="p1", name="A", description="", unit_price=1.0, inventory=1, category="running")
    p2 = Product(id="p2", name="B", description="", unit_price=1.0, inventory=1, category="running")
    p1.variants.append(Variant(size="10"))
    assert len(p2.variants) == 0  # Catches shared mutable default bug


def test_order_instantiation():
    order = Order(
        id="o1", user_id="u1",
        items=[OrderItem(product_id="p1", quantity=1, unit_price=89.99)],
        total_amount=89.99,
        payment_method="credit_card",
        payment_status="paid",
        order_status="paid",
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )
    assert order.order_status == "paid"
```

**Critical details:**
- Import models directly — no HTTP server or fixtures needed
- Test for shared mutable default bug explicitly (`test_two_products_do_not_share_variants`) — catches `variants = []` vs `field(default_factory=list)`
- Tests are sync (`def test_...` not `async def`) — model instantiation needs no async

---

### `tests/unit/test_stores.py` (test, CRUD)

**Source:** RESEARCH.md Pattern 7 + Validation Architecture

**Pattern:**
```python
# tests/unit/test_stores.py
import pytest
from app.lib.catalog.store import products_db
from app.lib.catalog.models import Product
from app.lib.orders.store import orders_db


@pytest.fixture(autouse=True)
def clear_stores():
    products_db.clear()
    orders_db.clear()
    yield
    products_db.clear()
    orders_db.clear()


def test_add_and_get_product():
    p = Product(id="p1", name="X", description="", unit_price=1.0, inventory=1, category="running")
    products_db["p1"] = p
    assert products_db.get("p1") is p


def test_list_products():
    for i in range(3):
        products_db[str(i)] = Product(id=str(i), name=f"P{i}", description="", unit_price=1.0, inventory=1, category="running")
    assert len(products_db) == 3


def test_missing_product_returns_none():
    assert products_db.get("nonexistent") is None
```

**Critical details:**
- `autouse=True` fixture clears stores before and after each test — prevents state bleed between tests
- Tests exercise store dict directly (add/get/list) — no service layer in Phase 1
- Both pre-yield and post-yield clears: pre-yield handles dirty state from a previous failed test

---

### `tests/unit/test_seed.py` (test, batch)

**Source:** RESEARCH.md Code Examples (unit test skeleton) + Pattern 7

**Pattern:**
```python
# tests/unit/test_seed.py
import pytest
from app.lib.auth.store import users_db
from app.lib.catalog.store import products_db
from app.lib.orders.store import orders_db
from app.lib.seed.seed import clear_and_reseed


@pytest.fixture(autouse=True)
def reset_stores():
    users_db.clear()
    products_db.clear()
    orders_db.clear()
    yield


def test_seed_product_count():
    clear_and_reseed()
    assert len(products_db) == 15


def test_seed_user_count():
    clear_and_reseed()
    assert len(users_db) == 2


def test_seed_order_statuses():
    clear_and_reseed()
    statuses = {o.order_status for o in orders_db.values()}
    assert "paid" in statuses
    assert "shipped" in statuses
    assert "canceled" in statuses


def test_products_have_variants():
    clear_and_reseed()
    for product in products_db.values():
        assert len(product.variants) >= 1, f"{product.name} has no variants"


def test_products_cover_all_categories():
    clear_and_reseed()
    categories = {p.category for p in products_db.values()}
    assert categories == {"running", "hiking", "slides", "sandals", "socks"}


def test_passwords_are_hashed():
    clear_and_reseed()
    for user in users_db.values():
        assert user.password_hash.startswith("$2b$"), "Password not bcrypt hashed"
        assert "password" not in user.password_hash.lower()


def test_alice_and_bob_seeded():
    clear_and_reseed()
    emails = {u.email for u in users_db.values()}
    assert "alice@example.com" in emails
    assert "bob@example.com" in emails


def test_products_have_required_fields():
    clear_and_reseed()
    for p in products_db.values():
        assert p.name and p.description
        assert p.unit_price > 0
        assert p.inventory >= 0
        assert p.category
```

**Critical details:**
- Uses `clear_and_reseed()` — not bare `seed()` — so tests are independent of any previous store state
- `autouse=True` fixture clears before each test; `clear_and_reseed()` inside each test then populates
- All 8 requirement-coverage test functions listed in RESEARCH.md Validation Architecture are included

---

### `__init__.py` files (all `app/`, `app/lib/*/`, `tests/`, `tests/unit/`)

**Source:** RESEARCH.md Open Question 2

**Content:** Empty file (or single `# package marker` comment)

**Critical details:**
- Required in every `app/` subdirectory and in `tests/` subdirectories to ensure absolute imports like `from app.lib.catalog.models import Product` resolve correctly in all environments
- Even with namespace packages (Python 3.3+), explicit `__init__.py` avoids subtle import resolution differences between `uv run pytest` and bare `pytest`

---

## Shared Patterns

### Import Organization
**Source:** CONVENTIONS.md Import Organization section
**Apply to:** All Python source files

```
1. Standard library: uuid, datetime, dataclasses, typing
2. Third-party: fastapi, pydantic, passlib, anthropic
3. Internal: absolute imports from app.*  (e.g., from app.lib.orders.models import Order)
```

Rules:
- No relative imports except within the same package when clearly scoped
- No wildcard imports (`from module import *`)
- All internal imports are absolute: `from app.lib.catalog.models import Product` — never `from .models import Product` across packages

---

### Type Annotation Style
**Source:** CONVENTIONS.md Code Style + Type Hints section
**Apply to:** All Python source files

```python
# CORRECT (Python 3.10+ syntax required)
def get_user(user_id: str) -> User | None: ...
items: list[CartItem] = field(default_factory=list)
config: dict[str, dict[str, float]] = {}

# FORBIDDEN
from typing import Optional, List, Dict
def get_user(user_id: str) -> Optional[User]: ...
items: List[CartItem] = field(default_factory=list)
```

---

### Structured Result Shape
**Source:** CONVENTIONS.md Error Handling section
**Apply to:** All service functions that can fail (Phase 2+; scaffold awareness in Phase 1 service stubs)

```python
# Success
{"success": True, "data": {...}}

# Failure
{
    "success": False,
    "code": "ORDER_NOT_FOUND",       # SCREAMING_SNAKE_CASE
    "message": "Order not found",    # Human-readable
    "retryable": False,              # True for transient mock failures, False for validation/auth
}
```

Note: Phase 1 has no service functions — this pattern is scaffolded for Phase 2+ awareness.

---

### Docstring Style
**Source:** CONVENTIONS.md Comments section
**Apply to:** All public service functions and `seed.py` public functions

```python
def seed() -> None:
    """Populate all in-memory stores with demo data.

    Called once from FastAPI lifespan before serving requests.
    Idempotent if stores are cleared first.
    """
```

Google-style with `Args:` and `Returns:` sections for non-trivial functions. Single-line acceptable for trivial helpers.

---

## No Analog Found

All files in this phase are new — the project is greenfield with no existing source code.

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| All 22 files listed above | various | various | Greenfield project — no source code exists yet |

All patterns above are derived from:
1. `.planning/codebase/CONVENTIONS.md` — model shapes, naming, import rules, error handling
2. `.planning/codebase/STRUCTURE.md` — directory layout and file naming
3. `01-RESEARCH.md` — verified library patterns with line citations
4. `01-CONTEXT.md` — locked decisions D-01 through D-12

---

## Metadata

**Analog search scope:** N/A — greenfield project
**Files scanned:** 0 source files (none exist)
**Planning artifacts read:** CONVENTIONS.md, STRUCTURE.md, 01-CONTEXT.md, 01-RESEARCH.md
**Pattern extraction date:** 2026-04-18
