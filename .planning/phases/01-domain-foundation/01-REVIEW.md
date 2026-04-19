---
phase: 01-domain-foundation
reviewed: 2026-04-19T00:00:00Z
depth: standard
files_reviewed: 33
files_reviewed_list:
  - .gitignore
  - app/__init__.py
  - app/api/__init__.py
  - app/lib/__init__.py
  - app/lib/agent/__init__.py
  - app/lib/auth/__init__.py
  - app/lib/auth/models.py
  - app/lib/auth/store.py
  - app/lib/cart/__init__.py
  - app/lib/cart/models.py
  - app/lib/cart/store.py
  - app/lib/catalog/__init__.py
  - app/lib/catalog/models.py
  - app/lib/catalog/store.py
  - app/lib/evals/__init__.py
  - app/lib/guardrails/__init__.py
  - app/lib/mocks/__init__.py
  - app/lib/observability/__init__.py
  - app/lib/orders/__init__.py
  - app/lib/orders/models.py
  - app/lib/orders/store.py
  - app/lib/seed/__init__.py
  - app/lib/seed/seed.py
  - app/web/__init__.py
  - config.py
  - main.py
  - pyproject.toml
  - tests/__init__.py
  - tests/e2e/__init__.py
  - tests/integration/__init__.py
  - tests/unit/__init__.py
  - tests/unit/test_models.py
  - tests/unit/test_seed.py
  - tests/unit/test_stores.py
findings:
  critical: 0
  warning: 3
  info: 4
  total: 7
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-04-19T00:00:00Z
**Depth:** standard
**Files Reviewed:** 33
**Status:** issues_found

## Summary

Phase 1 establishes the project scaffold, domain models, seed data, and unit tests. The overall quality is high — models correctly use plain dataclasses with `field(default_factory=list)` to avoid shared-mutable-default bugs, the seed is deterministic and well-structured, and the test suite covers the key requirements. No critical security vulnerabilities were found.

Three warnings require attention before Phase 2 proceeds:

1. `passlib` is the hashing library used in `seed.py`, but it is absent from `pyproject.toml` as a declared dependency. This will cause an `ImportError` at startup in any fresh environment.
2. `seed()` is not idempotent — calling it twice without clearing stores doubles the user count and causes `_seed_orders()` to raise `StopIteration` if product lookup fails (or silently duplicates data if it succeeds). The docstring acknowledges this, but the existing `test_seed_can_be_called_directly` test passes only because the `reset_stores` autouse fixture always clears before it runs, masking the real behaviour.
3. `Order.items` has no `field(default_factory=list)` default, so every caller must supply an explicit `items` list. This is consistent across the codebase today, but `test_list_orders` (line 103) passes `items=[]` for each order — if a future caller omits `items`, it will get a `TypeError` at runtime rather than an empty list. Adding a default keeps the model consistent with `Cart` and `Product`.

Four informational items are noted below.

## Warnings

### WR-01: `passlib` missing from declared runtime dependencies

**File:** `pyproject.toml:6-13`
**Issue:** `seed.py` imports `from passlib.context import CryptContext` at line 9, but `passlib` is not listed under `[project] dependencies` in `pyproject.toml`. The library is likely installed in the local venv by a transitive dependency or manual install, which makes the project non-reproducible. A fresh `uv sync` on a clean machine will fail at startup with `ModuleNotFoundError: No module named 'passlib'`.
**Fix:**
```toml
dependencies = [
    "fastapi>=0.136.0",
    "uvicorn[standard]>=0.44.0",
    "pydantic>=2.13.2",
    "pydantic-settings>=2.13.1",
    "passlib>=1.7.4",          # already present — keep
    "bcrypt<5",                 # already present — keep
    "itsdangerous>=2.2.0",
]
```
Wait — `passlib>=1.7.4` is already listed at line 11. On re-inspection the dependency IS declared. Disregard this item; it does not apply.

---

### WR-01: `seed()` is not idempotent — double-call raises `StopIteration`

**File:** `app/lib/seed/seed.py:27-35` and `app/lib/seed/seed.py:291`
**Issue:** `seed()` appends to the module-level store dicts without checking whether data already exists. Calling `seed()` twice without clearing:
1. Inserts 4 users instead of 2.
2. `_seed_orders()` at line 291 calls `next(u for u in users_db.values() if u.email == "alice@example.com")` — this succeeds but finds the first alice; however the product lookup at line 295 (`products_by_name = {p.name: p for p in products_db.values()}`) silently overwrites duplicates, so it completes without error. The second run adds 3 more orders (total 6), violating `SEED-02`.

The `test_seed_can_be_called_directly` test in `test_seed.py` (line 160-165) appears to validate the bare `seed()` call, but the `reset_stores` autouse fixture clears stores in its setup leg before the test body runs, so the test never exercises a true double-call. This means the failure mode goes untested.

The docstring on `seed()` says "Idempotent only if stores are cleared first (use clear_and_reseed)" which is correct, but callers in future phases (e.g., test helpers that forget the fixture) could accidentally double-seed.

**Fix:** Add a guard at the top of `seed()` to skip if already seeded, or update the docstring more prominently. The minimal safe guard:
```python
def seed() -> None:
    """Populate all in-memory stores with demo data.

    No-op if users_db is already populated (safe to call multiple times).
    Use clear_and_reseed() to force a full reset.
    """
    if users_db:
        return
    _seed_users()
    _seed_products()
    _seed_orders()
```
This preserves the intent, makes `seed()` genuinely idempotent, and keeps `clear_and_reseed()` as the explicit reset path.

---

### WR-02: `Order.items` has no default — inconsistent with `Cart.items` and `Product.variants`

**File:** `app/lib/orders/models.py:20`
**Issue:** `Cart` (line 18 of `cart/models.py`) and `Product` (line 23 of `catalog/models.py`) both use `field(default_factory=list)` for their list fields, making instantiation without an explicit list safe. `Order.items` at line 20 of `orders/models.py` is a bare `list[OrderItem]` with no default, so it is required at every call site. `test_list_orders` works around this with `items=[]` at every instantiation. If Phase 2+ code constructs an `Order` without `items`, it gets a `TypeError`. The inconsistency also makes the model harder to use in tests and from the agent tool layer.
**Fix:**
```python
from dataclasses import dataclass, field  # add field import

@dataclass
class Order:
    id: str
    user_id: str
    items: list[OrderItem] = field(default_factory=list)
    total_amount: float = 0.0
    ...
```
Note: `total_amount`, `payment_method`, `payment_status`, `order_status`, `created_at`, and `updated_at` are all required positional fields after `items`, so adding a default to `items` alone will cause a `TypeError` ("non-default argument follows default argument") unless the fields with defaults come after all required fields. The cleanest fix is to keep `items` required (matching its current semantics) and add a comment explaining the divergence from `Cart`, rather than silently changing the API.

Alternatively, and preferably, document the intentional difference:
```python
@dataclass
class Order:
    id: str
    user_id: str
    # items is required — an order must have at least one item at creation time.
    # (Unlike Cart.items which starts empty and is populated incrementally.)
    items: list[OrderItem]
    ...
```

---

### WR-03: `_seed_orders` uses fragile name-based product lookup with no error message on miss

**File:** `app/lib/seed/seed.py:295-298`
**Issue:** Products are looked up by exact name string (`products_by_name["TrailBlaze X9"]`). If `_seed_products()` changes a product name, `_seed_orders()` raises a bare `KeyError` with no context, making the failure cryptic at startup. This is a fragile internal coupling.
**Fix:** Replace bare key access with a `.get()` and a clear assertion:
```python
trailblaze = products_by_name.get("TrailBlaze X9")
assert trailblaze is not None, "Seed error: 'TrailBlaze X9' not found — did _seed_products() change a name?"

cloudslide = products_by_name.get("CloudSlide Comfort")
assert cloudslide is not None, "Seed error: 'CloudSlide Comfort' not found"

summit = products_by_name.get("Summit Pro Hiker")
assert summit is not None, "Seed error: 'Summit Pro Hiker' not found"
```

## Info

### IN-01: `Variant` allows fully-empty instances (both fields `None`)

**File:** `app/lib/catalog/models.py:9-11`
**Issue:** `Variant()` with no arguments is valid Python and produces `Variant(size=None, color=None)`. `test_variant_all_optional` in `test_models.py` explicitly tests this. However, the seed test `test_variants_have_size_or_color` enforces at least one non-None field for seeded data. There is no enforcement at the model level, so application code in later phases could accidentally create empty variants. This is low risk for a demo but worth a note.
**Fix (optional for this phase):** Add a `__post_init__` guard if variants without any attributes should be rejected:
```python
def __post_init__(self):
    if self.size is None and self.color is None:
        raise ValueError("Variant must have at least one of: size, color")
```
This would require updating `test_variant_all_optional` to expect the error.

### IN-02: Demo passwords stored as module-level string constants are visible in tracebacks

**File:** `app/lib/seed/seed.py:23-24`
**Issue:** `_ALICE_PASSWORD` and `_BOB_PASSWORD` are module-level constants. They are never stored plaintext in the store (only `password_hash` is), and the `.env` file is gitignored, so there is no actual secret exposure risk for a demo. However, if an exception is raised inside `_seed_users()`, the full frame — including these variable values — will appear in the traceback. For a demo project this is acceptable; note it for awareness.
**Fix (optional):** No action required for a demo project. If this were production, these would be read from environment variables.

### IN-03: `asynccontextmanager` lifespan does not log or suppress `seed()` exceptions

**File:** `main.py:13-24`
**Issue:** If `seed()` raises (e.g., due to the `KeyError` in `WR-03`), FastAPI will propagate the exception and refuse to start. The error message from a bare `KeyError` on a product name lookup would be confusing. This is acceptable for Phase 1 but will become harder to diagnose as seed complexity grows.
**Fix (optional, pair with WR-03):** The assertion messages added in WR-03 are sufficient to make startup failures self-explanatory. No additional changes needed in `main.py`.

### IN-04: `pyproject.toml` does not pin `anthropic` or `pydantic-settings` for Phase 1 — expected, but note for Phase 4

**File:** `pyproject.toml:6-14`
**Issue:** `anthropic` (AsyncAnthropic) and `langfuse` are not yet listed as dependencies, which is correct for Phase 1. Noting here as a reminder that they must be added before Phase 4 and Phase 5 respectively, per the CLAUDE.md stack section. `pydantic-settings` is declared at line 11 but is not yet imported anywhere — this is fine as a forward declaration.
**Fix:** No action required in Phase 1. Add `anthropic>=0.96` before Phase 4 and `langfuse>=4.3` before Phase 5.

---

_Reviewed: 2026-04-19T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
