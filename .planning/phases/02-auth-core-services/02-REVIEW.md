---
phase: 02-auth-core-services
reviewed: 2026-04-19T00:00:00Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - app/lib/auth/auth_service.py
  - app/lib/auth/store.py
  - app/lib/cart/cart_service.py
  - app/lib/orders/order_service.py
  - config.py
  - pyproject.toml
  - tests/unit/test_auth_service.py
  - tests/unit/test_cart_service.py
  - tests/unit/test_order_service.py
findings:
  critical: 2
  warning: 3
  info: 3
  total: 8
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-04-19
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

Phase 02 delivers auth (register/login/verify/reset), cart, and order services with consistent structured-dict return shapes and thorough unit test coverage. The overall design is clean and well-structured. Two critical issues are present: a hardcoded JWT secret in source and a missing `KeyError` guard in `verify_token` that can crash the process. Three warnings cover a subtle inventory quantity gap, an unprotected delegation path in `update_quantity`, and the `place_order` function lacking concurrency protection. Three info items address test duplication, the reset-token-in-response pattern, and a type annotation imprecision.

---

## Critical Issues

### CR-01: Hardcoded JWT Secret in Source

**File:** `config.py:23`
**Issue:** `JWT_SECRET = "dev-secret-change-in-prod"` is a plain string literal checked into source. Any JWT signed with this key can be forged by anyone who reads the repo. Even for a demo project, this is the class of mistake that leaks into production unchanged.
**Fix:** Read from an environment variable with a safe fallback that fails loudly in non-dev environments:
```python
import os
JWT_SECRET: str = os.environ.get("JWT_SECRET", "dev-secret-change-in-prod")
# In production guard: assert JWT_SECRET != "dev-secret-change-in-prod"
```
Or use `pydantic-settings` (already a dependency) to enforce this at startup.

---

### CR-02: Unguarded `payload["user_id"]` Key Access in `verify_token`

**File:** `app/lib/auth/auth_service.py:109`
**Issue:** After a successful `jwt.decode()`, the code accesses `payload["user_id"]` directly. A valid JWT signed with the same secret but missing the `user_id` claim (e.g., a token from a different service, or a manually crafted one) raises an unhandled `KeyError`, crashing the request with a 500 rather than returning a structured failure.
**Fix:**
```python
payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
user_id = payload.get("user_id")
if not user_id:
    return {
        "success": False,
        "code": "INVALID_TOKEN",
        "message": "Token is invalid",
        "retryable": False,
    }
return {"success": True, "data": {"user_id": user_id}}
```

---

## Warnings

### WR-01: `add_item` Only Rejects Zero Inventory, Not Insufficient Inventory

**File:** `app/lib/cart/cart_service.py:60`
**Issue:** The stock check inside the lock is `if product.inventory == 0`. A caller can add `quantity=100` to a product with `inventory=1` and it succeeds. The guard is logically incomplete — it prevents adding an out-of-stock item, but does not enforce that the cart quantity respects available stock.
**Note:** Whether to enforce this depends on project requirements (some stores allow reserving more than current stock). If the intent is to enforce stock limits, the fix is:
```python
if product.inventory < quantity:
    return {
        "success": False,
        "code": "INSUFFICIENT_STOCK",
        "message": f"Only {product.inventory} unit(s) available",
        "retryable": False,
    }
```
If over-reservation is intentional, add a comment clarifying this.

---

### WR-02: `update_quantity` Delegates to `remove_item` Outside the Lock

**File:** `app/lib/cart/cart_service.py:121`
**Issue:** When `quantity <= 0`, `update_quantity` calls the synchronous `remove_item()` at line 121 before acquiring `_cart_lock`. The lock is only acquired at line 123 for the happy path. This means the removal path has no concurrency protection. Two concurrent callers — one calling `update_quantity(..., 0)` and another calling `update_quantity(..., 5)` — could both read the same `item` reference before either modifies it, leading to inconsistent state.
**Fix:** Acquire the lock before branching on `quantity <= 0`, or inline the removal logic inside the lock:
```python
async with _cart_lock:
    if quantity <= 0:
        cart.items = [i for i in cart.items if i.product_id != product_id]
    else:
        item.quantity = quantity
```

---

### WR-03: `place_order` is Synchronous with No Concurrency Guard

**File:** `app/lib/orders/order_service.py:53-113`
**Issue:** `place_order` reads `carts_db`, builds an order, writes to `orders_db`, and deletes from `carts_db` — all outside any lock. If two concurrent async tasks call `place_order` for the same user simultaneously (possible in an async FastAPI context), both can pass the cart check and create two orders from the same cart. This is the classic TOCTOU (time-of-check/time-of-use) problem.
**Fix:** Make `place_order` async and protect the read-delete-write sequence with an order-level lock (similar to `_cart_lock` in cart_service):
```python
_order_lock = asyncio.Lock()

async def place_order(user_id: str, payment_method: ...) -> dict:
    async with _order_lock:
        cart = carts_db.get(user_id)
        if not cart or not cart.items:
            ...
        # build and store order, clear cart
```

---

## Info

### IN-01: Reset Token Returned in API Response Body

**File:** `app/lib/auth/auth_service.py:155-161`
**Issue:** `reset_request()` returns the raw reset token in the response payload. This is explicitly documented as intentional for demo purposes (no email server). No action required — the comment at line 131-136 is adequate. Flagged here for visibility so it is not missed when this code is hardened for production use.

---

### IN-02: Significant Test Duplication in Cart and Order Test Files

**File:** `tests/unit/test_cart_service.py:256-344`, `tests/unit/test_order_service.py:300-436`
**Issue:** Both test files have two sets of tests covering the same scenarios: an earlier set (lines 1–248 / 1–294) and a second "named aliases" section at the bottom that re-tests the same behaviors with slightly different fixture helpers. This adds ~90 lines of duplicate test code with no additional coverage.
**Fix:** Consolidate into a single set of well-named tests per behavior. The duplication does not affect correctness but makes the test suite harder to maintain.

---

### IN-03: `reset_tokens_db` Type Annotation Allows `str` for `expires_at`

**File:** `app/lib/auth/store.py:14`
**Issue:** The annotation `dict[str, dict[str, str | datetime]]` allows `expires_at` to be either a `str` or a `datetime`. In practice it is always a `datetime` object (set at `auth_service.py:152`). The looser union type could mask future bugs where a string is stored and the `>` comparison at `auth_service.py:197` silently fails or raises a `TypeError`.
**Fix:** Narrow the type to `datetime` only, or define a typed dataclass/TypedDict for the reset token entry:
```python
from typing import TypedDict
class ResetEntry(TypedDict):
    token: str
    expires_at: datetime

reset_tokens_db: dict[str, ResetEntry] = {}
```

---

_Reviewed: 2026-04-19_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
