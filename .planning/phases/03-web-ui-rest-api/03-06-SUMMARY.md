---
phase: 03-web-ui-rest-api
plan: "06"
subsystem: orders
tags: [orders, router, templates, cancel, return, web-ui]
dependency_graph:
  requires:
    - "03-05"  # cart_router, confirmation.html
    - "03-04"  # catalog_router
  provides:
    - orders_router (GET /orders, GET /orders/{id}, GET /orders/{id}/confirmation, POST /orders/{id}/cancel, POST /orders/{id}/return)
    - orders/list.html
    - orders/detail.html
  affects:
    - main.py (orders_router already registered)
tech_stack:
  added: []
  patterns:
    - "Pre-read order before cancel to capture payment_status for conditional refund"
    - "Jinja2 dict key access via order['items'] (not order.items — conflicts with dict.items())"
    - "Badge helper function _status_badge() maps status strings to Bootstrap classes"
key_files:
  created:
    - app/web/templates/orders/list.html
    - app/web/templates/orders/detail.html
  modified:
    - app/api/orders_router.py
decisions:
  - "order['items'] not order.items in Jinja2 — dict.items() method shadowed key lookup (Rule 1 bug fix)"
  - "Refund runs only for payment_status in ('paid', 'captured') — placed orders have 'pending'"
  - "Warehouse cancel runs on every successful service-layer cancel; mock failures surface as warning flash (not hard error)"
metrics:
  duration: "~5 minutes"
  completed: "2026-04-19"
  tasks_completed: 2
  files_created: 2
  files_modified: 1
---

# Phase 3 Plan 06: Orders Router and Templates Summary

Orders router and templates implemented. Users can view order history with status badges, drill into order detail with conditional cancel/return buttons, cancel eligible orders (triggering warehouse + optional payment mocks), and request returns.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Build orders_router.py | 581530a | app/api/orders_router.py |
| 2 | Build orders/list.html and orders/detail.html | ea90403 | app/web/templates/orders/list.html, app/web/templates/orders/detail.html |

## Cancel Flow Sequence (ORD-02)

```
POST /orders/{id}/cancel
  1. order_service.get_order(order_id, user_id)  — pre-read to capture payment_status/method
     └─ UNAUTHORIZED → HTTPException(403)
     └─ ORDER_NOT_FOUND → HTTPException(404)
  2. order_service.cancel_order(order_id, user_id)  — ownership + eligibility check
     └─ UNAUTHORIZED → HTTPException(403)
     └─ CANCEL_NOT_ALLOWED → flash danger + redirect
     └─ success → continue
  3. warehouse_mock.cancel_order(order_id)  — always run on success
     └─ failure → flash warning + redirect (order remains canceled)
  4. payment_mock.refund()  — only if payment_status in ('paid', 'captured')
     └─ failure → flash warning + redirect (order remains canceled)
  5. flash success + RedirectResponse(303) to /orders/{id}
```

## Conditional Button Logic (D-09)

| Order Status | Cancel Button | Return Button |
|---|---|---|
| placed | shown (btn-danger) | not shown |
| paid | shown (btn-danger) | shown (btn-warning) |
| processing | not shown | shown (btn-warning) |
| shipped | not shown | shown (btn-warning) |
| canceled | not shown | not shown |
| returned | not shown | not shown |

## Status Badge Color Map

| Status | Bootstrap Classes |
|--------|------------------|
| placed | bg-secondary |
| paid | bg-info text-dark |
| processing | bg-warning text-dark |
| shipped | bg-primary |
| canceled | bg-danger |
| returned | bg-secondary |

## Test Results

```
uv run pytest tests/ -x -q
131 passed, 1 skipped, 1 xfailed, 43 xpassed, 38 warnings in 36.16s
```

Orders integration test breakdown:
- `test_orders_list_shows_user_orders` — XPASS (was xfail stub, now passing)
- `test_order_detail_shows_status` — XPASS
- `test_cross_user_order_access_denied` — XPASS (403 confirmed)
- `test_cancel_order_redirects_and_updates_status` — XPASS
- `test_cancel_order_warehouse_failure_shows_flash` — XPASS
- `test_return_order_on_paid_order_succeeds` — XPASS
- `test_return_order_on_placed_order_fails` — SKIPPED (no placed order seeded for alice after cancel tests mutate state)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Jinja2 dict key access for order items list**
- **Found during:** Task 2, running integration tests
- **Issue:** `{% for item in order.items %}` — Jinja2 resolves `order.items` to Python's `dict.items()` built-in method (returns key-value pairs), not the `'items'` key value (list of order line items). TypeError: 'builtin_function_or_method' object is not iterable.
- **Fix:** Changed to `{% for item in order['items'] %}` which forces dict key lookup in Jinja2.
- **Files modified:** app/web/templates/orders/detail.html (line 27)
- **Commit:** ea90403

## Known Stubs

None — all routes are fully wired to real service and mock layers.

## Threat Surface Scan

All routes enforce authentication via `Depends(get_current_user_web)`. Cross-user order access returns 403 via UNAUTHORIZED code path in order_service (T-03-05 mitigated). CSRF on cancel/return POSTs accepted per threat model (SameSite=Lax baseline). No new network endpoints beyond what the plan specified.

## Self-Check: PASSED

- app/api/orders_router.py: EXISTS
- app/web/templates/orders/list.html: EXISTS
- app/web/templates/orders/detail.html: EXISTS
- Commit 581530a (orders_router): EXISTS
- Commit ea90403 (templates): EXISTS
- Full test suite: 131 passed, 43 xpassed, no failures
