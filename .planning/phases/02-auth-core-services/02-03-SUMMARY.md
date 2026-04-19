---
phase: 02-auth-core-services
plan: "03"
subsystem: unit-tests
tags: [unit-tests, auth, cart, orders, pytest, store-isolation]
dependency_graph:
  requires:
    - "02-01"
    - "02-02"
  provides:
    - tests/unit/test_auth_service.py (register, login, JWT verify, password reset end-to-end)
    - tests/unit/test_cart_service.py (add, merge, zero-inventory, update, remove, total, empty)
    - tests/unit/test_order_service.py (place, cancel, return, cross-user, list)
  affects:
    - Phase 3 (regression guard for routers built on these services)
    - Phase 4 (regression guard for agent tools)
tech_stack:
  added: []
  patterns:
    - autouse fixture per test file (clear all stores before and after each test)
    - Direct service function calls — no HTTP, no FastAPI test client
    - pytest-asyncio for async cart service tests
    - Seed helpers (_seed_product, _seed_cart, _seed_order) for readable test setup
key_files:
  created: []
  modified:
    - tests/unit/test_auth_service.py
    - tests/unit/test_cart_service.py
    - tests/unit/test_order_service.py
decisions:
  - "Added required named tests alongside existing comprehensive tests — no tests removed"
  - "autouse fixture added to test_auth_service.py clears all five stores (users, reset_tokens, products, carts, orders)"
  - "Duplicate test_list_orders_filters_by_user removed — original from plan 02-02 already covered the case"
metrics:
  duration_seconds: 420
  completed_date: "2026-04-19"
  tasks_completed: 2
  files_created: 0
  files_modified: 3
  tests_added: 28
---

# Phase 2 Plan 03: Unit Test Suite Summary

**One-liner:** Full unit test suite for auth, cart, and order services — 131 tests passing with per-test store isolation via autouse fixtures.

---

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Write test_auth_service.py | 8c57e21 | tests/unit/test_auth_service.py |
| 2 | Write test_cart_service.py and test_order_service.py | d524f18 | tests/unit/test_cart_service.py, tests/unit/test_order_service.py |

---

## What Was Built

### test_auth_service.py (28 tests)

The existing file from plan 02-01 had comprehensive tests but lacked: the `autouse=True` isolation fixture and the exact function names required by plan 02-03 acceptance criteria. Updated to add:

- `autouse=True` fixture clearing `users_db`, `reset_tokens_db`, `products_db`, `carts_db`, `orders_db` before/after each test
- `test_register_new_user`, `test_register_duplicate_email`
- `test_login_valid_credentials`, `test_login_wrong_password`, `test_login_unknown_email`
- `test_verify_token_valid`, `test_verify_token_invalid`
- `test_password_reset_end_to_end` (full flow: register → reset_request → reset_confirm → login with new/old password)
- `test_reset_request_unknown_email`, `test_reset_confirm_invalid_token`

All 18 existing tests preserved. Total: 28 tests.

### test_cart_service.py (25 tests)

The existing file from plan 02-02 had 18 tests with `autouse=True` fixture already in place. Added 7 required named tests:

- `test_add_item_success`, `test_add_item_zero_inventory_rejected`, `test_add_item_merge_same_product`
- `test_cart_total` (2 products × quantities = 190.0 total)
- `test_update_quantity`, `test_remove_item`, `test_get_cart_empty`

Also removed unused `import asyncio` (ruff F401 fix).

### test_order_service.py (35 tests, was 24)

The existing file from plan 02-02 had 24 tests with `autouse=True` fixture already in place. Added 11 required named tests using `_seed_cart` and `_seed_order` helpers:

- `test_place_order` (place + cart cleared + order_status == "placed")
- `test_cancel_order_eligible_placed`, `test_cancel_order_eligible_paid`
- `test_cancel_order_ineligible_processing`, `test_cancel_order_ineligible_shipped`
- `test_return_order_eligible_paid`, `test_return_order_eligible_processing`, `test_return_order_eligible_shipped`
- `test_return_order_ineligible_placed`
- `test_cross_user_cancel_rejected`, `test_cross_user_return_rejected`

The existing `test_list_orders_filters_by_user` already satisfied the plan requirement — duplicate removed.

---

## Test Results

```
pytest tests/unit/ — 131 passed, 0 failed, 10 warnings
```

Breakdown by file:
- `test_auth_service.py`: 28 passed
- `test_cart_service.py`: 25 passed
- `test_order_service.py`: 35 passed
- `test_stores.py`: 10 passed
- `test_auth_store.py`: 3 passed
- `test_config_jwt.py`: 3 passed
- `test_models.py`: 8 passed
- `test_seed.py`: 14 passed
- `test_stores.py`: 10 passed (included in above count)

The 10 warnings are `InsecureKeyLengthWarning` from PyJWT about the dev secret key length — expected, demo-only config.

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Unused asyncio import in test_cart_service.py**
- **Found during:** Task 2 ruff check
- **Issue:** `import asyncio` was left from plan 02-02 TDD setup but unused after pytest-asyncio handles async tests
- **Fix:** Removed the import
- **Files modified:** tests/unit/test_cart_service.py
- **Commit:** d524f18

**2. [Rule 1 - Bug] Line length violations and duplicate function in test_order_service.py**
- **Found during:** Task 2 ruff check
- **Issue:** Two helper function signatures exceeded 88 chars; `test_list_orders_filters_by_user` was duplicated (original from 02-02 already satisfies the plan requirement)
- **Fix:** Wrapped helper signatures to multi-line; removed duplicate test function
- **Files modified:** tests/unit/test_order_service.py
- **Commit:** d524f18

---

## Security Properties Tested

Per threat model:

| Threat ID | Test | Status |
|-----------|------|--------|
| T-02-12 (Spoofing cancel) | test_cross_user_cancel_rejected — UNAUTHORIZED returned | Passing |
| T-02-13 (Store isolation) | autouse fixture in all three files | Passing |

---

## Known Stubs

None — all tests exercise fully-wired service functions.

---

## Threat Flags

None — test files introduce no new network endpoints or trust boundaries.

---

## Self-Check: PASSED

| Item | Status |
|------|--------|
| tests/unit/test_auth_service.py | FOUND |
| tests/unit/test_cart_service.py | FOUND |
| tests/unit/test_order_service.py | FOUND |
| test_auth_service.py contains `def test_register_new_user(` | FOUND |
| test_auth_service.py contains `def test_login_valid_credentials(` | FOUND |
| test_auth_service.py contains `def test_verify_token_valid(` | FOUND |
| test_auth_service.py contains `def test_password_reset_end_to_end(` | FOUND |
| test_auth_service.py contains `autouse=True` | FOUND |
| test_cart_service.py contains `def test_add_item_success(` | FOUND |
| test_cart_service.py contains `def test_add_item_zero_inventory_rejected(` | FOUND |
| test_cart_service.py contains `def test_add_item_merge_same_product(` | FOUND |
| test_cart_service.py contains `def test_cart_total(` | FOUND |
| test_cart_service.py contains `OUT_OF_STOCK` | FOUND |
| test_order_service.py contains `def test_cancel_order_eligible_placed(` | FOUND |
| test_order_service.py contains `def test_cross_user_cancel_rejected(` | FOUND |
| test_order_service.py contains `UNAUTHORIZED` | FOUND |
| Commit 8c57e21 (Task 1) | FOUND |
| Commit d524f18 (Task 2) | FOUND |
| pytest tests/unit/ exits 0 (131 passed) | PASSED |
