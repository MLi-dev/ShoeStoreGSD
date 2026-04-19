---
phase: 02-auth-core-services
plan: "02"
subsystem: cart-and-orders
tags: [cart, orders, service-layer, tdd, asyncio, ownership-check]
dependency_graph:
  requires: []
  provides:
    - app.lib.cart.cart_service
    - app.lib.orders.order_service
  affects:
    - Phase 3 routers (cart_router, orders_router)
    - Phase 4 agent tools (add_to_cart, place_order, cancel_order, return_order)
tech_stack:
  added: []
  patterns:
    - asyncio.Lock for inventory check+decrement (T-02-09)
    - structured dict returns (no exceptions for expected failures)
    - TDD red-green cycle with pytest-asyncio
key_files:
  created:
    - app/lib/cart/cart_service.py
    - app/lib/orders/order_service.py
    - tests/unit/test_cart_service.py
    - tests/unit/test_order_service.py
  modified: []
decisions:
  - "asyncio.Lock module-level singleton (_cart_lock) guards add_item and update_quantity"
  - "cancel_order eligibility set: ('placed', 'paid') per D-11"
  - "request_return eligibility set: ('paid', 'processing', 'shipped') per D-12"
  - "ownership check (order.user_id != user_id) precedes eligibility in cancel and return (D-13)"
  - "clear_cart uses del carts_db[user_id] — idempotent via guard"
  - "place_order deletes carts_db entry after order creation (not set to empty)"
metrics:
  duration_seconds: 200
  completed_date: "2026-04-19"
  tasks_completed: 2
  files_created: 4
  files_modified: 0
  tests_added: 42
---

# Phase 2 Plan 02: Cart and Order Services Summary

**One-liner:** Cart service (asyncio.Lock inventory guard) and order lifecycle service (ownership + eligibility enforcement) as pure-Python service layer.

## What Was Built

### Task 1: cart_service.py (TDD)

Six public functions in `app/lib/cart/cart_service.py`:

- `add_item(user_id, product_id, quantity)` — async; checks product exists, acquires `_cart_lock`, rejects zero-inventory with `OUT_OF_STOCK`, merges duplicate product_ids (D-08), creates cart on first add
- `update_quantity(user_id, product_id, quantity)` — async; delegates to `remove_item` when quantity <= 0
- `remove_item(user_id, product_id)` — sync; filters items in-place
- `get_cart(user_id)` — sync; returns cart with computed total (D-09)
- `get_cart_total(user_id)` — sync; `sum(q * p)` on-the-fly
- `clear_cart(user_id)` — sync; idempotent via `del carts_db[user_id]`

Module-level `_cart_lock = asyncio.Lock()` prevents inventory race (T-02-09).

### Task 2: order_service.py (TDD)

Five public functions in `app/lib/orders/order_service.py`:

- `place_order(user_id, payment_method)` — converts cart to order, clears cart, stores `payment_status="pending"`, `order_status="placed"`
- `cancel_order(order_id, user_id)` — ownership check first (D-13), then `placed/paid` eligibility (D-11)
- `request_return(order_id, user_id)` — ownership check first (D-13), then `paid/processing/shipped` eligibility (D-12)
- `get_order(order_id, user_id)` — ownership enforced
- `list_orders(user_id)` — filters `orders_db.values()` by user_id

## TDD Gate Compliance

| Gate   | Commit  | Message                                           |
|--------|---------|---------------------------------------------------|
| RED-1  | fbbdae0 | test(02-02): add failing tests for cart_service   |
| GREEN-1| cea0c41 | feat(02-02): implement cart_service with six...   |
| RED-2  | 86195c1 | test(02-02): add failing tests for order_service  |
| GREEN-2| 6e6b0a7 | feat(02-02): implement order_service with five... |

## Test Results

- `tests/unit/test_cart_service.py` — 18 tests, all passing
- `tests/unit/test_order_service.py` — 24 tests, all passing
- Full unit suite: 103 tests passing

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all functions fully implemented with no placeholder logic.

## Threat Flags

None — all threats in the plan's threat register are mitigated by the implementation:

| Threat | Mitigation |
|--------|-----------|
| T-02-07 (Spoofing cancel) | `order.user_id != user_id` check in `cancel_order` before eligibility |
| T-02-08 (Spoofing return) | Same ownership check in `request_return` |
| T-02-09 (DoS add_item race) | `async with _cart_lock` wraps inventory check+cart mutation |
| T-02-10 (Tampering cancel) | Eligibility check on `order_status` before mutation |
| T-02-11 (EoP place_order) | Accepted — in-memory demo; payment mocks in Phase 3 |

## Self-Check: PASSED

| Item | Status |
|------|--------|
| app/lib/cart/cart_service.py | FOUND |
| app/lib/orders/order_service.py | FOUND |
| tests/unit/test_cart_service.py | FOUND |
| tests/unit/test_order_service.py | FOUND |
| Commit fbbdae0 (test RED-1) | FOUND |
| Commit cea0c41 (feat GREEN-1) | FOUND |
| Commit 86195c1 (test RED-2) | FOUND |
| Commit 6e6b0a7 (feat GREEN-2) | FOUND |
