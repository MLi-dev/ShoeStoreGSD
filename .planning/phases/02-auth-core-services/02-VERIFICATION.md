---
phase: 02-auth-core-services
verified: 2026-04-19T00:00:00Z
status: human_needed
score: 4/5 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Register a new user via the web UI form, log in, then open the chat interface and confirm the same session is recognized without re-authenticating"
    expected: "Both the web page (Phase 3) and the chat endpoint (Phase 4) accept the same JWT issued at login — user does not need to log in twice"
    why_human: "Web UI routes (Phase 3) and chat endpoint (Phase 4) do not exist yet. verify_token() is implemented and tested in isolation, but the actual cross-surface session sharing cannot be verified until those surfaces are built."
deferred:
  - truth: "A registered user can log in and use a JWT that both the web UI and chat endpoint will recognize (AUTH-04 cross-surface)"
    addressed_in: "Phase 3 and Phase 4"
    evidence: "Phase 3 success criteria: 'User can check out using Credit Card, PayPal, or Apple Pay'; Phase 4 success criteria reference authenticated user session; web UI routes and chat endpoint that consume verify_token() are explicitly Phase 3/4 deliverables"
---

# Phase 2: Auth & Core Services Verification Report

**Phase Goal:** Users can register, log in, and use a JWT that both the web UI and chat endpoint will recognize; cart and order service logic is fully exercised by unit tests
**Verified:** 2026-04-19
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A new user can register with email and password; the password is stored as a bcrypt hash, never plaintext | VERIFIED | `auth_service.register()` hashes via passlib bcrypt; `test_register_stores_password_as_bcrypt_hash` passes; `test_register_never_returns_password_hash` passes |
| 2 | A registered user can log in and receive a JWT that remains valid across multiple requests (web and chat use the same token) | PARTIAL — service-layer verified; cross-surface deferred | `login()` issues PyJWT token; `verify_token()` decodes it; both tested. Web UI routes and chat endpoint don't exist yet — AUTH-04 cross-surface proof deferred to Phase 3/4 |
| 3 | A user can initiate a password reset flow and set a new password | VERIFIED | `reset_request()` issues token, `reset_confirm()` updates hash; `test_password_reset_end_to_end` passes; expired and invalid token paths tested |
| 4 | A unit test can add a product variant to a cart, update its quantity, remove it, and verify the cart total — no HTTP required | VERIFIED | `test_cart_service.py`: `test_add_item_success`, `test_update_quantity`, `test_remove_item`, `test_cart_total` all pass; 25 cart tests, all green |
| 5 | The cart rejects adding a product that has zero inventory | VERIFIED | `add_item()` checks `product.inventory == 0` inside `asyncio.Lock`; `test_add_item_zero_inventory_rejected` passes with `OUT_OF_STOCK` code |

**Score:** 4/5 truths verified (1 deferred — AUTH-04 cross-surface, addressed in Phase 3/4)

---

### Deferred Items

Items not yet met but explicitly addressed in later milestone phases.

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | JWT recognized by web UI and chat endpoint (AUTH-04 full surface coverage) | Phase 3 and Phase 4 | Phase 3 delivers web routers that will call `verify_token()`; Phase 4 delivers chat endpoint that resolves user from session via same function. The shared mechanism (`verify_token`) is fully implemented and tested at service layer. |

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `config.py` | JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES constants | VERIFIED | All three constants present; `JWT_ALGORITHM = "HS256"`, `JWT_EXPIRE_MINUTES = 30` |
| `app/lib/auth/store.py` | users_db and reset_tokens_db module-level stores | VERIFIED | Both dicts present with correct type annotations; `reset_tokens_db` keyed by email |
| `app/lib/auth/auth_service.py` | register, login, verify_token, reset_request, reset_confirm | VERIFIED | All five functions fully implemented, 210 lines, Google docstrings, PyJWT (not jose), passlib bcrypt |
| `app/lib/cart/cart_service.py` | add_item, update_quantity, remove_item, get_cart, get_cart_total, clear_cart | VERIFIED | All six functions; `add_item` and `update_quantity` are async; `_cart_lock = asyncio.Lock()` at module level |
| `app/lib/orders/order_service.py` | place_order, cancel_order, request_return, get_order, list_orders | VERIFIED | All five functions; D-11/D-12/D-13 enforced; ownership check precedes eligibility check |
| `tests/unit/test_auth_service.py` | Auth service unit tests | VERIFIED | 28 tests; autouse fixture clears all 5 stores; all required named tests present |
| `tests/unit/test_cart_service.py` | Cart service unit tests | VERIFIED | 25 tests; autouse fixture; all required named tests present |
| `tests/unit/test_order_service.py` | Order service unit tests | VERIFIED | 35 tests; autouse fixture; all required named tests present |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `auth_service.register()` | `users_db` | keyed by UUID user.id | WIRED | `users_db[user.id] = user` at line 47 |
| `auth_service.login()` | `jwt.encode()` | PyJWT with HS256 and JWT_SECRET | WIRED | `jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)` at line 90 |
| `auth_service.reset_request()` | `reset_tokens_db` | keyed by email | WIRED | `reset_tokens_db[email] = {"token": token, "expires_at": ...}` at line 150-153 |
| `cart_service.add_item()` | `products_db` | inventory check before inserting CartItem | WIRED | `products_db.get(product_id)` at line 50; `product.inventory == 0` check at line 60 |
| `cart_service.add_item()` | `asyncio.Lock` | inventory check+decrement guarded by lock | WIRED | `_cart_lock = asyncio.Lock()` at module level; `async with _cart_lock:` at line 59 |
| `order_service.cancel_order()` | `orders_db` | ownership check order.user_id == user_id before status mutation | WIRED | `order.user_id != user_id` check at line 139 before eligibility check at line 148 |
| `test_auth_service.py` | `app/lib/auth/auth_service` | direct function calls | WIRED | `from app.lib.auth.auth_service import login, register, reset_confirm, reset_request, verify_token` |
| `test_cart_service.py` | `app/lib/cart/cart_service` | direct async function calls | WIRED | `from app.lib.cart.cart_service import add_item` (per-test inline imports) |
| `test_order_service.py` | `app/lib/orders/order_service` | direct function calls | WIRED | `from app.lib.orders.order_service import place_order, cancel_order, request_return` (per-test inline imports) |

---

### Data-Flow Trace (Level 4)

Not applicable — no artifacts render dynamic UI data. All artifacts are pure-Python service layer functions with no rendering pipeline.

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full unit suite (131 tests) | `uv run python -m pytest tests/unit/ --tb=short` | 131 passed, 0 failed, 10 warnings (InsecureKeyLengthWarning — expected for dev secret) | PASS |
| config.py JWT constants importable | `uv run python -c "from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES"` | Imports cleanly | PASS |
| auth_service five functions importable | `uv run python -c "from app.lib.auth.auth_service import register, login, verify_token, reset_request, reset_confirm"` | Imports cleanly | PASS |
| cart_service six functions importable | `uv run python -c "from app.lib.cart.cart_service import add_item, update_quantity, remove_item, get_cart, get_cart_total, clear_cart"` | Imports cleanly | PASS |
| order_service five functions importable | `uv run python -c "from app.lib.orders.order_service import place_order, cancel_order, request_return, get_order, list_orders"` | Imports cleanly | PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| AUTH-01 | 02-01, 02-03 | User can create an account with email and password | SATISFIED | `register()` implemented and tested; `test_register_new_user` passes |
| AUTH-02 | 02-01, 02-03 | User can log in with email/password and remain authenticated via JWT (PyJWT) | SATISFIED | `login()` issues JWT; `verify_token()` decodes it; service layer fully tested; AUTH-04 cross-surface deferred to Phase 3/4 |
| AUTH-03 | 02-01, 02-03 | User can reset their password via a reset flow | SATISFIED | `reset_request()` + `reset_confirm()` end-to-end; expiry enforced; single-use token; all paths tested |
| AUTH-04 | 02-01, 02-03 | Auth session shared — web UI and chatbot both recognize same authenticated user | PARTIAL / DEFERRED | `verify_token()` is the shared mechanism and is tested; web UI routes and chat endpoint are Phase 3/4 deliverables; cross-surface wiring deferred |
| CART-01 | 02-02, 02-03 | User can add a product (with variant) to their cart | SATISFIED | `add_item()` implemented, asyncio.Lock guarded, OUT_OF_STOCK enforced; tested |
| CART-02 | 02-02, 02-03 | User can update item quantity in cart | SATISFIED | `update_quantity()` implemented (async); delegates to `remove_item()` when qty <= 0; tested |
| CART-03 | 02-02, 02-03 | User can remove an item from cart | SATISFIED | `remove_item()` implemented; ITEM_NOT_IN_CART and CART_NOT_FOUND paths tested |
| CART-04 | 02-02, 02-03 | User can view cart with line items and totals | SATISFIED | `get_cart()` returns items with computed total; `get_cart_total()` sums on-the-fly (D-09); tested |

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None found | — | — | — | — |

No TODO/FIXME/PLACEHOLDER comments found. No empty implementations (return null/return []). No hardcoded empty data passed to rendering. No jose import (correctly uses PyJWT throughout).

---

### Human Verification Required

#### 1. AUTH-04 Cross-Surface JWT Recognition

**Test:** Complete Phase 3 (web UI routes) and Phase 4 (chat endpoint). Register a user, log in via the web form, capture the JWT cookie/header. Then send a chat request to the chat endpoint using the same JWT. Verify the chat endpoint resolves the same user_id without requiring re-login.

**Expected:** Both surfaces call `verify_token(jwt_string)` and receive `{"success": True, "data": {"user_id": "..."}}` with the same user_id. No duplicate login required.

**Why human:** The web UI routes (Phase 3) and chat endpoint (Phase 4) do not exist yet. The `verify_token()` function is the shared mechanism and is fully implemented and tested, but the actual cross-surface wiring cannot be exercised until both surfaces exist.

---

### Gaps Summary

No blocking gaps. The phase goal is substantively achieved: register/login/JWT-verify/password-reset are all fully implemented and tested with 28 auth tests; cart service (6 functions, asyncio.Lock, OUT_OF_STOCK enforcement, D-08 merge, D-09 on-the-fly total) is fully implemented with 25 tests; order service (5 functions, D-11 cancel eligibility, D-12 return eligibility, D-13 ownership-before-eligibility) is fully implemented with 35 tests; all 131 unit tests pass.

The only open item is AUTH-04's cross-surface proof (same JWT recognized by web UI AND chat endpoint), which cannot be verified until Phase 3 and Phase 4 surfaces are built. This is an intentional phase boundary, not a gap in the current phase's deliverables.

---

_Verified: 2026-04-19_
_Verifier: Claude (gsd-verifier)_
