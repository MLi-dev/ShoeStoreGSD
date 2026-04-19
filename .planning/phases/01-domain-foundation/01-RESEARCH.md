# Phase 1: Domain Foundation - Research

**Researched:** 2026-04-18
**Domain:** Python project scaffolding, dataclass domain models, in-memory stores, seed data, pytest-asyncio
**Confidence:** HIGH

---

## Summary

Phase 1 is a pure Python scaffolding phase — no HTTP routes, no LLM calls. The work is:
scaffold `pyproject.toml` with uv, write plain `@dataclass` domain models exactly as specified in CONVENTIONS.md, wire module-level dict stores, seed 15 demo-quality products and 2 test users with bcrypt-hashed passwords, wire `seed()` into a FastAPI lifespan context manager, and write unit tests that exercise model instantiation, store CRUD, and seed smoke test without starting an HTTP server.

All required package versions were verified against PyPI on 2026-04-18 and match what is recorded in STATE.md. The model shapes in CONVENTIONS.md exactly reproduce the spec — there is nothing to redesign. The main planning decisions are about file organization, `pyproject.toml` structure, and seed data content, all of which are locked by decisions D-01 through D-12.

**Primary recommendation:** Follow CONVENTIONS.md model shapes verbatim; use `[tool.uv] package = false` in `pyproject.toml` to skip build/install of the flat-layout project; configure `asyncio_mode = "auto"` under `[tool.pytest.ini_options]`.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Use `pyproject.toml` + `uv` for dependency management. `uv.lock` for reproducible installs.
- **D-02:** Flat layout — `app/` at project root alongside `main.py` and `config.py` (no `src/` wrapper).
- **D-03:** Separate dependency groups: `[project.dependencies]` for runtime, `[dependency-groups] dev = [...]` for pytest, ruff, mypy, httpx, playwright.
- **D-04:** Rich and demo-worthy product data — real-feeling shoe model names, compelling descriptions, realistic pricing ($49–$189).
- **D-05:** 15 products, 3 per category: running, hiking, slides, sandals, socks. Each product has at least one size/color variant.
- **D-06:** 2 test users: `alice@example.com` and `bob@example.com`, each with a bcrypt-hashed password.
- **D-07:** 3 seeded prior orders: 1 paid, 1 shipped, 1 canceled — assigned to test users.
- **D-08:** In-memory stores are plain module-level dicts, e.g. `products_db: dict[str, Product] = {}` in each `store.py`. Empty at import time.
- **D-09:** Seed data is loaded by calling `seed()` inside the FastAPI `lifespan` async context manager — runs once on startup before any requests are served.
- **D-10:** Tests live in a top-level `tests/` directory: `tests/unit/`, `tests/integration/`, `tests/e2e/`.
- **D-11:** Phase 1 unit tests cover: model instantiation, store CRUD operations (add/get/list), and a seed smoke test that calls `seed()` and asserts store counts and content.
- **D-12:** `[tool.pytest.ini_options]` in `pyproject.toml` configures `testpaths = ["tests"]` and `asyncio_mode = "auto"`.

### Claude's Discretion
- Exact shoe model names, descriptions, and pricing within the rich/demo-worthy constraint.
- Specific password used for seeded test users (hashed — never plaintext in seed data).
- Whether `seed.py` exposes a `clear_and_reseed()` helper for test isolation (reasonable addition if it aids testing).

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CAT-01 | App seeds 10–20 shoe products on startup (running, hiking, slides, sandals, socks) with name, description, unit price, inventory, category | Product dataclass + seed.py; 15 products at 3/category; seed() called from lifespan |
| CAT-04 | Products support size/color variants | `Variant` dataclass with `size: str \| None` and `color: str \| None`; `Product.variants: list[Variant]` with `field(default_factory=list)` |
| SEED-01 | App seeds at least 2 test users on startup | `User` dataclass; passlib CryptContext with bcrypt; alice + bob seeded in seed() |
| SEED-02 | App seeds at least 1 prior paid order, 1 shipped order, and 1 canceled order for test users | `Order` dataclass with Literal status fields; 3 seeded orders in seed() |
</phase_requirements>

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Domain model definitions | Python module (dataclasses) | — | Pure data shapes; no HTTP layer involved |
| In-memory stores | Python module-level dicts | — | Single-process in-memory state; no database tier needed |
| Seed data loading | FastAPI lifespan (app startup) | `app/lib/seed/seed.py` | Runs exactly once before any requests; lifespan is the modern hook |
| Password hashing at seed time | `app/lib/seed/seed.py` | passlib/bcrypt | Seed calls hash at construction time; no service layer needed yet |
| pytest configuration | `pyproject.toml` `[tool.pytest.ini_options]` | — | Standard Python tool config co-location |

---

## Standard Stack

### Core Runtime
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastapi | 0.136.0 | Web framework skeleton + lifespan hook | Locked; current latest [VERIFIED: PyPI 2026-04-18] |
| uvicorn[standard] | 0.44.0 | ASGI server | Locked; current latest [VERIFIED: PyPI 2026-04-18] |
| pydantic | 2.13.2 | API schema validation (Phase 1: indirect dep of fastapi) | Locked; current latest [VERIFIED: PyPI 2026-04-18] |
| pydantic-settings | 2.13.1 | Settings / env loading in config.py | Locked; current latest [VERIFIED: PyPI 2026-04-18] |
| passlib | 1.7.4 | CryptContext bcrypt wrapper for password hashing | Locked; latest (library is in maintenance) [VERIFIED: PyPI 2026-04-18] |
| bcrypt | 5.0.0 | Underlying bcrypt C extension used by passlib | Locked; current latest [VERIFIED: PyPI 2026-04-18] |
| itsdangerous | 2.2.0 | Signed sessions (scaffold in Phase 1, used in Phase 2) | Locked; current latest [VERIFIED: PyPI 2026-04-18] |

### Dev / Test
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 9.0.3 | Test runner | All unit tests [VERIFIED: PyPI 2026-04-18] |
| pytest-asyncio | 1.3.0 | Async test support | Any async test or fixture [VERIFIED: PyPI 2026-04-18] |
| ruff | latest | Linting + formatting + import sorting | All phases |
| mypy | latest | Type checking | All phases |
| httpx | 0.28.1 | HTTP test client (used Phase 2+) | Scaffold in dev deps now [VERIFIED: PyPI 2026-04-18] |

**Installation (uv):**
```bash
uv init --no-package
# or create pyproject.toml manually with [tool.uv] package = false
uv add fastapi "uvicorn[standard]" pydantic pydantic-settings passlib bcrypt itsdangerous
uv add --dev pytest pytest-asyncio ruff mypy httpx playwright
```

---

## Architecture Patterns

### System Architecture Diagram (Phase 1 scope)

```
Startup trigger (uvicorn)
        |
        v
FastAPI lifespan context manager (main.py)
        |
        v
seed() ──> app/lib/seed/seed.py
        |
        +──> hash passwords ──> passlib CryptContext
        |
        +──> populate users_db  (app/lib/auth/store.py)
        +──> populate products_db (app/lib/catalog/store.py)
        +──> populate orders_db  (app/lib/orders/store.py)
        |
        v
In-memory dicts ready for requests
(No HTTP requests served in Phase 1 tests — tests import stores directly)

Test path:
pytest ──> tests/unit/ ──> import app/lib/<domain>/ directly ──> assert store state
```

### Recommended Project Structure
```
ShoeStoreGSD/          # project root (flat layout, no src/)
├── pyproject.toml
├── uv.lock
├── main.py            # FastAPI app + lifespan
├── config.py          # FAILURE_CONFIG + Settings
├── CLAUDE.md
├── app/
│   ├── __init__.py
│   ├── api/           # empty stubs (Phase 2+)
│   ├── web/           # empty stubs (Phase 3+)
│   └── lib/
│       ├── auth/
│       │   ├── __init__.py
│       │   ├── models.py   # User dataclass
│       │   └── store.py    # users_db: dict[str, User] = {}
│       ├── catalog/
│       │   ├── __init__.py
│       │   ├── models.py   # Product, Variant dataclasses
│       │   └── store.py    # products_db: dict[str, Product] = {}
│       ├── cart/
│       │   ├── __init__.py
│       │   ├── models.py   # Cart, CartItem dataclasses
│       │   └── store.py    # carts_db: dict[str, Cart] = {}
│       ├── orders/
│       │   ├── __init__.py
│       │   ├── models.py   # Order, OrderItem dataclasses
│       │   └── store.py    # orders_db: dict[str, Order] = {}
│       └── seed/
│           ├── __init__.py
│           └── seed.py     # seed() + optional clear_and_reseed()
└── tests/
    ├── __init__.py
    ├── unit/
    │   ├── __init__.py
    │   ├── test_models.py
    │   ├── test_stores.py
    │   └── test_seed.py
    ├── integration/   # empty (Phase 2+)
    └── e2e/           # empty (Phase 3+)
```

### Pattern 1: pyproject.toml with uv flat layout

**What:** Non-packaged project using `[tool.uv] package = false` so uv doesn't try to build/install `app/` as a distribution package. Runtime and dev deps split per D-03.

**When to use:** Flat layout (no `src/`) where `app/` is not an installable package — scripts and applications, not libraries.

```toml
# Source: https://docs.astral.sh/uv/concepts/projects/config/ [VERIFIED: WebFetch 2026-04-18]
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

[tool.ruff]
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I"]
```

**Critical detail:** `[tool.uv] package = false` prevents uv from attempting to discover and install `app/` as a package. Without it, uv may error if the package name doesn't match a discoverable module. [VERIFIED: docs.astral.sh/uv/concepts/projects/config/]

### Pattern 2: FastAPI lifespan (modern async context manager)

**What:** `@asynccontextmanager` replaces the deprecated `@app.on_event("startup")` / `@app.on_event("shutdown")` decorators.

**When to use:** Always — startup/shutdown events are deprecated as of FastAPI 0.93+.

```python
# Source: https://fastapi.tiangolo.com/advanced/events/ [VERIFIED: WebFetch 2026-04-18]
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.lib.seed.seed import seed

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once before first request
    seed()
    yield
    # Runs on shutdown (nothing to clean up for in-memory stores)

app = FastAPI(lifespan=lifespan)
```

**Critical detail:** `seed()` is called before `yield`. Any exception in the pre-yield block prevents the app from starting. If `seed()` can raise, wrap in try/except or log and re-raise.

### Pattern 3: Domain models as plain dataclasses

**What:** All domain objects use `@dataclass`. Pydantic is reserved for FastAPI request/response schemas only.

**When to use:** Any domain object stored in the in-memory dicts (`User`, `Product`, `Variant`, `Cart`, `CartItem`, `Order`, `OrderItem`).

```python
# Source: CONVENTIONS.md + spec_python.md [VERIFIED: file read 2026-04-18]
from dataclasses import dataclass, field
from typing import Literal

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

**Critical detail:** Fields with defaults must come after fields without defaults. `field(default_factory=list)` is required for mutable defaults — never use `variants: list[Variant] = []` (shared mutable default bug).

### Pattern 4: In-memory store as module-level dict

**What:** Each domain package has a `store.py` with a module-level dict. Empty at import time; populated by `seed()` at startup.

```python
# app/lib/catalog/store.py
# Source: CONVENTIONS.md [VERIFIED: file read 2026-04-18]
from app.lib.catalog.models import Product

products_db: dict[str, Product] = {}
```

**Critical detail:** Dict is initialized empty — never inline `products_db = {...}` with data at module level. All data loaded by `seed()` at runtime.

### Pattern 5: Password hashing with passlib CryptContext

**What:** `CryptContext(schemes=["bcrypt"])` wraps bcrypt; use `.hash()` at seed time, `.verify()` at login time.

```python
# Source: https://passlib.readthedocs.io/en/stable/narr/context-tutorial.html [CITED]
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# At seed time (in seed.py):
password_hash = pwd_context.hash("test-password-alice")

# At login time (Phase 2, in auth service):
is_valid = pwd_context.verify(plain_password, stored_hash)
```

**Critical detail:** `deprecated="auto"` tells passlib to automatically upgrade legacy hashes on verify — not needed in Phase 1 but correct to set from the start.

### Pattern 6: pytest-asyncio 1.x auto mode

**What:** `asyncio_mode = "auto"` in `[tool.pytest.ini_options]` makes all `async def test_*` functions run as asyncio tests automatically. No `@pytest.mark.asyncio` decorator needed.

```python
# Source: pytest-asyncio docs + WebSearch [VERIFIED: multiple sources 2026-04-18]

# pyproject.toml:
# [tool.pytest.ini_options]
# asyncio_mode = "auto"
# testpaths = ["tests"]

# tests/unit/test_seed.py
async def test_seed_loads_products():
    from app.lib.seed.seed import seed
    from app.lib.catalog.store import products_db
    products_db.clear()
    seed()
    assert len(products_db) == 15
```

**Breaking change in 1.x vs 0.x:** `event_loop` fixture removed. Custom event loops must use `event_loop_policy` fixture instead. Phase 1 tests are simple enough that this doesn't apply. [VERIFIED: WebFetch thinhdanggroup.github.io]

### Pattern 7: Test isolation for in-memory stores

**What:** Because stores are module-level globals, tests that call `seed()` or write to stores will bleed state between tests unless explicitly cleared.

```python
# tests/unit/test_seed.py
import pytest
from app.lib.catalog.store import products_db
from app.lib.auth.store import users_db
from app.lib.orders.store import orders_db

@pytest.fixture(autouse=True)
def clear_stores():
    products_db.clear()
    users_db.clear()
    orders_db.clear()
    yield
    products_db.clear()
    users_db.clear()
    orders_db.clear()
```

Alternatively, `seed.py` can expose `clear_and_reseed()` (Claude's Discretion per CONTEXT.md) which both clears and repopulates, convenient for integration tests in later phases.

### Anti-Patterns to Avoid

- **`Optional[str]`:** Use `str | None` — Python 3.10+ union syntax is required per CONVENTIONS.md.
- **`List[dict]`, `Dict[str, Any]`:** Use `list[dict]`, `dict[str, Any]` — built-in generics per CONVENTIONS.md.
- **`@app.on_event("startup")`:** Deprecated; use `lifespan` context manager.
- **`variants: list[Variant] = []`:** Shared mutable default on dataclass; use `field(default_factory=list)`.
- **Plaintext passwords in seed data:** Always hash before storing. Never store `password = "secret"` in a User object.
- **Importing stores at module level in tests:** Import inside test functions or use autouse fixtures; avoids import-time side effects.
- **`from app.lib import *`:** Forbidden per CONVENTIONS.md. Use explicit absolute imports.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Password hashing | Custom bcrypt wrapper | `passlib.context.CryptContext` | Handles salt generation, cost factor, hash format, future algorithm upgrade; 72-byte truncation edge cases handled |
| Unique IDs | `str(random.randint(...))` | `str(uuid.uuid4())` | UUID4 is collision-resistant; `random` IDs are not |
| ISO timestamps | Custom datetime formatting | `datetime.utcnow().isoformat()` or `datetime.now(tz=timezone.utc).isoformat()` | Consistent format; UTC-aware avoids timezone bugs |
| Mutable dataclass defaults | `variants: list = []` | `field(default_factory=list)` | Python dataclass sharing bug — classic interview trap |

**Key insight:** The in-memory store pattern is deliberately trivial. Don't introduce complexity (ABC base classes, repository pattern, SQLAlchemy, etc.) — the spec explicitly calls for plain module-level dicts.

---

## Common Pitfalls

### Pitfall 1: Shared Mutable Default in Dataclass
**What goes wrong:** `@dataclass class Product: variants: list[Variant] = []` — all Product instances share the same list object.
**Why it happens:** Python dataclasses validate against this but only raise at class definition; older versions silently share.
**How to avoid:** Always use `field(default_factory=list)` for list/dict fields.
**Warning signs:** Test that creates two products and adds a variant to one sees the variant appear on the other.

### Pitfall 2: Module-level Store Sharing Between Tests
**What goes wrong:** Test A calls `seed()` and adds 15 products. Test B expects an empty store but finds 15 products.
**Why it happens:** Python module imports are cached — `products_db` is the same dict object across tests.
**How to avoid:** Use a `clear_stores` autouse fixture or `clear_and_reseed()` helper before each test that cares about store state.
**Warning signs:** Tests pass in isolation but fail when run together with `pytest`.

### Pitfall 3: uv package discovery on flat layout
**What goes wrong:** `uv sync` errors trying to find/install the project package because `[tool.uv] package = false` is missing.
**Why it happens:** uv by default treats projects as installable packages; flat layout without src/ confuses package discovery.
**How to avoid:** Set `[tool.uv] package = false` in `pyproject.toml`. [VERIFIED: docs.astral.sh/uv]
**Warning signs:** `uv sync` complains about missing `__init__.py` at root, or tries to install `shoestore` as a package.

### Pitfall 4: pytest-asyncio 1.x event_loop fixture removal
**What goes wrong:** Code copied from older tutorials uses `@pytest.fixture def event_loop(): ...` — this is removed in 1.0 and will error.
**Why it happens:** pytest-asyncio 1.0 dropped the `event_loop` fixture entirely.
**How to avoid:** Don't define a custom `event_loop` fixture. Phase 1 tests are pure sync or simple async — no custom loop scope needed.
**Warning signs:** `pytest` raises `PytestUnraisableExceptionWarning` or fixture conflict error mentioning `event_loop`.

### Pitfall 5: Absolute imports require PYTHONPATH or installed package
**What goes wrong:** `from app.lib.catalog.models import Product` fails with `ModuleNotFoundError` when running pytest.
**Why it happens:** Flat layout with `[tool.uv] package = false` means `app/` is not installed; Python needs to find it via `sys.path`.
**How to avoid:** Run tests from the project root (`uv run pytest` or `pytest` from root). uv adds the project root to `sys.path` automatically when `package = false`. Confirm with `uv run python -c "import app"`.
**Warning signs:** `ModuleNotFoundError: No module named 'app'` when running pytest.

### Pitfall 6: bcrypt password at import time in seed.py
**What goes wrong:** Hashing passwords at module-level (outside a function) means every import of `seed.py` runs bcrypt, which is intentionally slow (~100ms). This slows imports.
**Why it happens:** bcrypt work factor is designed to be slow for security.
**How to avoid:** Hash passwords inside the `seed()` function body, not at module level.
**Warning signs:** Noticeably slow import time for `seed.py` module.

---

## Code Examples

### Full pyproject.toml
```toml
# Verified structure for uv flat-layout non-package project
# Source: docs.astral.sh/uv/concepts/projects/config/ [VERIFIED 2026-04-18]
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

[tool.ruff]
line-length = 88
```

### Minimal main.py skeleton
```python
# main.py
# Source: fastapi.tiangolo.com/advanced/events/ [VERIFIED 2026-04-18]
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.lib.seed.seed import seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed()
    yield


app = FastAPI(title="ShoeStore AI Demo", lifespan=lifespan)
# No routers registered in Phase 1
```

### Minimal config.py skeleton
```python
# config.py
# Source: CONVENTIONS.md [VERIFIED: file read 2026-04-18]
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

### seed.py structure
```python
# app/lib/seed/seed.py
# Source: CONVENTIONS.md + decisions D-04 through D-09 [VERIFIED: file read 2026-04-18]
import uuid
from datetime import datetime, timezone
from passlib.context import CryptContext

from app.lib.auth.models import User
from app.lib.auth.store import users_db
from app.lib.catalog.models import Product, Variant
from app.lib.catalog.store import products_db
from app.lib.orders.models import Order, OrderItem
from app.lib.orders.store import orders_db

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


def _seed_users() -> None:
    alice = User(
        id=str(uuid.uuid4()),
        email="alice@example.com",
        password_hash=_pwd_context.hash("alice-password"),
        created_at=datetime.now(tz=timezone.utc).isoformat(),
    )
    bob = User(
        id=str(uuid.uuid4()),
        email="bob@example.com",
        password_hash=_pwd_context.hash("bob-password"),
        created_at=datetime.now(tz=timezone.utc).isoformat(),
    )
    users_db[alice.id] = alice
    users_db[bob.id] = bob
```

### Unit test skeleton
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


def test_passwords_are_hashed():
    clear_and_reseed()
    for user in users_db.values():
        assert user.password_hash.startswith("$2b$"), "Password not bcrypt hashed"
        assert "password" not in user.password_hash.lower()
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `@app.on_event("startup")` | `lifespan` async context manager | FastAPI 0.93 (2023) | Deprecated — do not use |
| `Optional[str]` from `typing` | `str \| None` union syntax | Python 3.10 (2021) | Built-in; `Optional` import not needed |
| `List[dict]` from `typing` | `list[dict]` built-in | Python 3.9 (2020) | Built-in; `List` import not needed |
| `pytest-asyncio` `@pytest.mark.asyncio` | `asyncio_mode = "auto"` auto detection | pytest-asyncio 0.21 | No decorator needed in auto mode |
| Custom `event_loop` fixture | `event_loop_policy` fixture | pytest-asyncio 1.0 (2025) | `event_loop` fixture removed entirely |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Specific passwords for alice/bob are Claude's discretion (any secure value) | seed.py structure | Low — CONTEXT.md explicitly grants this discretion |
| A2 | `[tool.uv] package = false` prevents all package discovery issues for this flat layout | Pitfall 3, Pattern 1 | Medium — if wrong, `uv sync` may error; fix is straightforward |
| A3 | `uv run pytest` adds project root to `sys.path` automatically when `package = false` | Pitfall 5 | Medium — if wrong, add `pythonpath = ["."]` to `[tool.pytest.ini_options]` |

---

## Open Questions (RESOLVED)

1. **`pythonpath` in pytest config needed?**
   - What we know: uv with `package = false` should add project root to sys.path; standard Python packaging guidance also says project root is on path for non-installed apps
   - What's unclear: Whether `uv run pytest` vs bare `pytest` behaves differently for sys.path
   - Recommendation: Add `pythonpath = ["."]` to `[tool.pytest.ini_options]` as a safe belt-and-suspenders measure; no downside

2. **`__init__.py` files required?**
   - What we know: Python 3 supports namespace packages (no `__init__.py`); pytest test discovery works with or without them
   - What's unclear: Whether absolute imports `from app.lib.catalog.models import Product` require `__init__.py` throughout the `app/` tree in a non-installed flat layout
   - Recommendation: Include `__init__.py` (even empty) in every `app/` subdirectory and in `tests/unit/` to be safe; avoids subtle import resolution differences between environments

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All | ✓ | 3.13.12 | — |
| uv | Dependency management | ✓ | 0.9.7 | pip + venv (not preferred) |
| fastapi | Web skeleton | Available on PyPI | 0.136.0 | — |
| passlib + bcrypt | Password hashing | Available on PyPI | 1.7.4 / 5.0.0 | — |
| pytest + pytest-asyncio | Unit tests | Available on PyPI | 9.0.3 / 1.3.0 | — |

**Note:** Python 3.13 is installed; project requires Python 3.12+. 3.13 satisfies this. [VERIFIED: `python3 --version` 2026-04-18]

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 + pytest-asyncio 1.3.0 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` — created in Wave 0 |
| Quick run command | `uv run pytest tests/unit/ -x -q` |
| Full suite command | `uv run pytest tests/ -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CAT-01 | 15 products seeded, all 5 categories present | unit | `uv run pytest tests/unit/test_seed.py::test_seed_product_count -x` | ❌ Wave 0 |
| CAT-01 | Products have name, description, unit_price, inventory, category | unit | `uv run pytest tests/unit/test_seed.py::test_products_have_required_fields -x` | ❌ Wave 0 |
| CAT-04 | Every product has ≥1 variant with size or color | unit | `uv run pytest tests/unit/test_seed.py::test_products_have_variants -x` | ❌ Wave 0 |
| SEED-01 | 2 users seeded: alice + bob | unit | `uv run pytest tests/unit/test_seed.py::test_seed_user_count -x` | ❌ Wave 0 |
| SEED-01 | Passwords are bcrypt hashed, never plaintext | unit | `uv run pytest tests/unit/test_seed.py::test_passwords_are_hashed -x` | ❌ Wave 0 |
| SEED-02 | Orders include paid, shipped, canceled statuses | unit | `uv run pytest tests/unit/test_seed.py::test_seed_order_statuses -x` | ❌ Wave 0 |
| D-11 | Model instantiation works (User, Product, Variant, Cart, CartItem, Order, OrderItem) | unit | `uv run pytest tests/unit/test_models.py -x` | ❌ Wave 0 |
| D-11 | Store CRUD: add/get/list for products and orders | unit | `uv run pytest tests/unit/test_stores.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/unit/ -x -q`
- **Per wave merge:** `uv run pytest tests/unit/ -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/__init__.py` — package marker
- [ ] `tests/unit/__init__.py` — package marker
- [ ] `tests/unit/test_models.py` — covers model instantiation (D-11)
- [ ] `tests/unit/test_stores.py` — covers store CRUD (D-11)
- [ ] `tests/unit/test_seed.py` — covers CAT-01, CAT-04, SEED-01, SEED-02

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no (Phase 1 scaffolds models only; auth logic is Phase 2) | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | no (no HTTP layer in Phase 1) | — |
| V6 Cryptography | yes — password hashing at seed time | passlib CryptContext with bcrypt |

### Known Threat Patterns for This Phase

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Plaintext password in seed data | Information Disclosure | Hash at seed time with CryptContext; assert hash format in tests |
| Weak bcrypt cost factor | Elevation of Privilege | passlib defaults to bcrypt cost 12; do not lower it |

---

## Project Constraints (from CLAUDE.md)

All directives enforced by the planner:

| Directive | Constraint |
|-----------|-----------|
| No python-jose | PyJWT only (CVE-2024-33664); python-jose not in pyproject.toml |
| No LangChain | Not installed; Phase 1 has no LLM calls anyway |
| AsyncAnthropic only | Not applicable Phase 1; note for Phase 4 |
| Plain dataclasses for domain objects | Confirmed — all models in CONVENTIONS.md use `@dataclass` |
| Pydantic only for API schemas | Phase 1 has no API schemas; Pydantic is indirect fastapi dep only |
| Global FAILURE_CONFIG | Scaffold `config.py` with the exact FAILURE_CONFIG shape from CONVENTIONS.md |
| `[root]:` parsed in route handler | Not applicable Phase 1; guardrails module stubbed only |
| In-memory state only | Module-level dicts; no database dependencies |
| bcrypt/passlib for password hashing | Confirmed — passlib + bcrypt in dependencies |
| pytest + pytest-asyncio for tests | Confirmed — in dev dependency group |
| asyncio_mode = "auto" | Confirmed — in `[tool.pytest.ini_options]` |

---

## Sources

### Primary (HIGH confidence)
- PyPI registry — all package versions verified via `pip3 index versions <pkg>` 2026-04-18
- `fastapi.tiangolo.com/advanced/events/` — FastAPI lifespan pattern verified via WebFetch
- `docs.astral.sh/uv/concepts/projects/dependencies/` — uv dependency groups syntax verified via WebFetch
- `docs.astral.sh/uv/concepts/projects/config/` — `[tool.uv] package = false` verified via WebFetch
- `.planning/codebase/CONVENTIONS.md` — all model shapes verified via file read
- `.planning/codebase/STRUCTURE.md` — directory layout verified via file read
- `/Users/matthew/Downloads/spec_python.md` — spec models verified via file read

### Secondary (MEDIUM confidence)
- `passlib.readthedocs.io/en/stable/narr/context-tutorial.html` — CryptContext pattern cited from official docs
- `pytest-asyncio.readthedocs.io` + WebSearch — `asyncio_mode = "auto"` config confirmed by multiple sources

### Tertiary (LOW confidence)
- None — all critical claims are verified or cited.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions verified against PyPI registry
- Architecture: HIGH — model shapes from CONVENTIONS.md + spec; lifespan pattern from official FastAPI docs
- Pitfalls: HIGH — dataclass mutable defaults and module-level test isolation are well-known Python patterns; uv flat-layout behavior verified from uv docs
- pytest-asyncio 1.x breaking changes: MEDIUM — verified from third-party migration guide; official docs returned 403

**Research date:** 2026-04-18
**Valid until:** 2026-07-18 (stable stack; fastapi/pydantic versions may bump but patterns are stable)
