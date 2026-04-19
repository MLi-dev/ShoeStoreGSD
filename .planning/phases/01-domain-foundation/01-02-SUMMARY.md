---
phase: 01-domain-foundation
plan: "02"
subsystem: domain
tags: [python, dataclasses, in-memory-store, domain-models, pytest]

# Dependency graph
requires:
  - phase: 01-domain-foundation/01-01
    provides: uv flat-layout scaffold with all app/lib/* package markers and pyproject.toml pytest config

provides:
  - User dataclass (id, email, password_hash, created_at — all str) in app/lib/auth/models.py
  - Variant and Product dataclasses with field(default_factory=list) for variants in app/lib/catalog/models.py
  - Cart and CartItem dataclasses with field(default_factory=list) for items in app/lib/cart/models.py
  - Order and OrderItem dataclasses with Literal status fields in app/lib/orders/models.py
  - users_db, products_db, carts_db, orders_db module-level empty dicts in respective store.py files
  - 21 passing unit tests: 11 model instantiation tests + 10 store CRUD tests with autouse fixture isolation
  - CAT-04 satisfied: Product.variants accepts list[Variant] with size/color

affects:
  - 01-03-PLAN.md (seed.py populates these stores at startup)
  - 01-04-PLAN.md (smoke test exercises the same stores via seed())
  - All Phase 2+ plans (every service layer, API router, and agent tool imports from these models and stores)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Plain Python @dataclass for domain objects — Pydantic reserved for FastAPI schemas only (CLAUDE.md)"
    - "field(default_factory=list) prevents shared mutable default bug on list fields"
    - "Module-level dict stores: dict[str, Model] = {} empty at import time, populated by seed()"
    - "str | None union syntax (Python 3.10+) — no Optional[] from typing"
    - "Built-in generics: list[...], dict[...] — no List, Dict from typing"
    - "autouse fixture clears all four stores pre- and post-yield for test isolation"

key-files:
  created:
    - app/lib/auth/models.py
    - app/lib/auth/store.py
    - app/lib/catalog/models.py
    - app/lib/catalog/store.py
    - app/lib/cart/models.py
    - app/lib/cart/store.py
    - app/lib/orders/models.py
    - app/lib/orders/store.py
    - tests/unit/test_models.py
    - tests/unit/test_stores.py
  modified: []

key-decisions:
  - "field(default_factory=list) is mandatory for all list fields — bare [] causes shared-mutable-default bug"
  - "Store dicts are empty at import time — seed() populates them in lifespan, never inline"
  - "Only from typing import Literal allowed — all other typing imports replaced by Python 3.12 built-ins"
  - "Test isolation via autouse fixture with pre-yield and post-yield clear() calls — prevents state bleed"

patterns-established:
  - "Domain models: pure @dataclass, no __post_init__, no validators, no methods — pure data shapes"
  - "Store pattern: from app.lib.<domain>.models import <Model>; <name>_db: dict[str, <Model>] = {}"
  - "Test pattern: autouse fixture clears all four stores both before and after each test"

requirements-completed: [CAT-04]

# Metrics
duration: 4min
completed: "2026-04-19"
---

# Phase 1 Plan 02: Domain Models and In-Memory Stores Summary

**Seven pure Python dataclasses (User, Variant, Product, Cart, CartItem, Order, OrderItem) with four module-level dict stores and 21 passing unit tests covering model instantiation and store CRUD with autouse fixture isolation**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-04-19T02:52:28Z
- **Completed:** 2026-04-19T02:56:31Z
- **Tasks:** 3 of 3
- **Files created:** 10 (4 models.py + 4 store.py + 2 test files)

## Accomplishments

- Created all four models.py files with exact dataclass shapes from CONVENTIONS.md — no redesign, no deviation from locked shapes
- Created all four store.py files as minimal 4-line modules with empty typed dicts at module level
- Created test_models.py (11 tests) and test_stores.py (10 tests) — 21 total, all passing
- Verified shared-mutable-default regression protection via field(default_factory=list) on Product.variants and Cart.items
- CAT-04 confirmed: Product.variants accepts list[Variant] with size: str | None and color: str | None

## Task Commits

Each task was committed atomically:

1. **Task 1: Create all four models.py files** - `abd6fc2` (feat)
2. **Task 2: Create all four store.py files** - `6dc66b2` (feat)
3. **Task 3: Create test_models.py and test_stores.py** - `19e8fb8` (test)

## Files Created/Modified

- `app/lib/auth/models.py` - User dataclass (id, email, password_hash, created_at — all str)
- `app/lib/auth/store.py` - users_db: dict[str, User] = {} module-level store
- `app/lib/catalog/models.py` - Variant and Product dataclasses with field(default_factory=list)
- `app/lib/catalog/store.py` - products_db: dict[str, Product] = {} module-level store
- `app/lib/cart/models.py` - Cart and CartItem dataclasses with field(default_factory=list)
- `app/lib/cart/store.py` - carts_db: dict[str, Cart] = {} module-level store
- `app/lib/orders/models.py` - Order and OrderItem dataclasses with Literal status fields
- `app/lib/orders/store.py` - orders_db: dict[str, Order] = {} module-level store
- `tests/unit/test_models.py` - 11 tests: instantiation + shared-mutable-default regression tests
- `tests/unit/test_stores.py` - 10 tests: CRUD for all four stores with autouse fixture isolation

## Decisions Made

- `field(default_factory=list)` is the only safe way to declare list fields on dataclasses — bare `= []` causes all instances to share the same list object (Python pitfall). Both Product.variants and Cart.items use factory form.
- Store dicts use built-in `dict[str, Model]` generic — no `from typing import Dict` (Python 3.12 makes these available as built-ins).
- autouse fixture clears all four stores both pre-yield (cleans dirty state from failed tests) and post-yield (clean teardown) — this double-clear pattern prevents any cross-test contamination.

## Deviations from Plan

None — plan executed exactly as written. All dataclass shapes copied verbatim from CONVENTIONS.md. No forbidden patterns (Optional, List, Dict) introduced.

## Issues Encountered

None. All 21 tests pass on first run with 0 failures.

## Test Results

```
21 passed in 0.06s
```

Individual verification:
- `uv run pytest tests/unit/test_models.py -x -q` → 11 passed
- `uv run pytest tests/unit/test_stores.py -x -q` → 10 passed
- `uv run pytest tests/unit/test_models.py tests/unit/test_stores.py -x -q` → 21 passed

## Threat Surface

No new security surface introduced. Plan 02 is pure in-process data shapes — no HTTP, no user input, no cryptographic operations. T-01-02-01 (shared mutable default) mitigated by field(default_factory=list) + regression tests. T-01-02-02 (module state leaks) mitigated by autouse fixture isolation.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- All domain models importable: `from app.lib.<domain>.models import <Model>` works
- All stores accessible: `from app.lib.<domain>.store import <name>_db` gives empty dict at import time
- Plan 03 (seed) can now populate these stores with realistic shoe data via seed()
- Plan 04 (smoke tests) can import from these models and verify seed counts

## Self-Check: PASSED

All 10 source/test files found on disk. All 3 task commits (abd6fc2, 6dc66b2, 19e8fb8) exist in git log.

---
*Phase: 01-domain-foundation*
*Completed: 2026-04-19*
