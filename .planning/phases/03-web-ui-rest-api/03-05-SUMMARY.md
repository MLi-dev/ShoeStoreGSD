---
phase: 03-web-ui-rest-api
plan: "05"
subsystem: ui
tags: [fastapi, jinja2, bootstrap, checkout, cart, mocks]

requires:
  - phase: 03-02
    provides: warehouse_mock.reserve_inventory and payment_mock.charge adapters
  - phase: 03-03
    provides: cart_service, order_service, auth dependencies
  - phase: 03-04
    provides: POST /cart/add wired in catalog_router; base.html template

provides:
  - "GET /cart — render cart page with enriched product names, empty state"
  - "POST /cart/update — update cart item quantity (PRG, 303)"
  - "POST /cart/remove — remove cart item (PRG, 303)"
  - "POST /checkout — reserve_inventory → charge → place_order orchestration"
  - "cart.html — cart table, payment method radios, checkout form, error alert"
  - "orders/confirmation.html — order ID, status badge, items table, total"

affects:
  - "03-06 — orders_router.py needs GET /orders/{id}/confirmation route that passes order to confirmation.html"

tech-stack:
  added: []
  patterns:
    - "PRG (Post-Redirect-Get) on all POST mutations — 303 redirect prevents double-submit"
    - "Checkout sequence enforced in code: reserve_inventory → charge → place_order; failure at any step stops the chain"
    - "Template enrichment: cart_service stores product_id only; router enriches with product name from products_db"
    - "Error re-render pattern: mock failures re-render current page with error context var (not redirect)"
    - "user_id always from JWT dependency, never from form body (T-03-05 mitigation)"

key-files:
  created:
    - app/web/templates/cart/cart.html
    - app/web/templates/orders/confirmation.html
  modified:
    - app/api/cart_router.py

key-decisions:
  - "Temporary UUID (temp_id) passed to mock adapters before order exists — place_order creates the real order ID"
  - "On mock failure: re-render cart page (not redirect) to preserve error message without flash session complexity"
  - "Checkout form only posts payment_method — cart items read server-side from session; no item data in form body"

patterns-established:
  - "Cart enrichment helper _enrich_cart_items() separates data concern from route handler"
  - "All checkout errors render cart/cart.html with error= context variable"

requirements-completed:
  - CHK-01
  - CHK-02
  - CHK-03
  - CHK-04

duration: 15min
completed: 2026-04-19
---

# Phase 03 Plan 05: Cart Router & Checkout Flow Summary

**FastAPI cart router with reserve_inventory → charge → place_order checkout orchestration, cart.html with payment method radios, and orders/confirmation.html — 31 xfail checkout tests now xpassed**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-04-19T19:50:00Z
- **Completed:** 2026-04-19T20:05:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Replaced stub cart_router.py with full 4-route implementation (GET /cart, POST /cart/update, POST /cart/remove, POST /checkout)
- Checkout sequence enforced in exact order: warehouse reserve_inventory → payment charge → order_service place_order; failure at either mock step stops the chain and re-renders cart with error
- cart.html with Bootstrap table, inline qty update/remove forms, payment method radios (credit_card / paypal / apple_pay), empty state, error alert
- confirmation.html with order ID, status badge color map, items table, total — ready for orders_router to wire
- All 31 previously-xfail checkout integration tests now xpassed; 131 unit tests still passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Build cart_router.py with checkout orchestration** - `54e4e25` (feat)
2. **Task 2: Build cart.html and orders/confirmation.html templates** - `f5c0a97` (feat)

## Files Created/Modified

- `app/api/cart_router.py` — Full cart router: 4 routes, checkout sequence, _enrich_cart_items helper
- `app/web/templates/cart/cart.html` — Cart page with items table, payment radios, checkout form, empty state, error alert
- `app/web/templates/orders/confirmation.html` — Order confirmation card with status badge, items table, View All Orders link

## Decisions Made

- Used a temporary UUID (`temp_id = str(uuid4())`) for mock adapter calls before the real order exists — `place_order()` generates the canonical order ID
- Mock failures re-render cart page directly (TemplateResponse) rather than redirect+flash to keep error message delivery simple and avoid extra round-trip
- Checkout form only submits `payment_method` — cart state is read server-side, preventing cart item tampering via form body

## Deviations from Plan

None — plan executed exactly as written. The provided code template in the plan was followed faithfully.

## Issues Encountered

None — all routes imported, app startup succeeded, and all 31 checkout integration tests passed on first run.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Plan 06 (orders_router) must add GET /orders/{id}/confirmation route that calls `order_service.get_order()` and passes the order dict to `orders/confirmation.html` as `order=` context variable
- confirmation.html template is complete and waiting for that route
- All checkout success criteria satisfied: sequence enforced, failure paths tested, templates wired

---

*Phase: 03-web-ui-rest-api*
*Completed: 2026-04-19*
