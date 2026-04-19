---
phase: 03-web-ui-rest-api
plan: 02
subsystem: mocks, catalog, auth
tags: [mocks, failure-injection, catalog, auth-dependencies, fastapi]

# Dependency graph
requires:
  - phase: 03-01
    provides: "Wave 0 xfail test stubs for warehouse_mock, payment_mock, catalog_service"
  - phase: 02-auth-core-services
    provides: "auth_service.verify_token, users_db, User dataclass"
  - phase: 01-domain-foundation
    provides: "Product/Variant dataclasses, products_db store"
provides:
  - "warehouse_mock: get_available_quantity, reserve_inventory, ship_order, cancel_order"
  - "payment_mock: charge, refund with dynamic failure key per payment method"
  - "catalog_service: search_products (keyword + category), get_product"
  - "auth/dependencies: get_current_user_web (307 redirect), get_current_user_api (401)"
  - "FAILURE_CONFIG with all 6 payment keys at 0.0 defaults"
affects: [03-03, 03-04, 03-05, 03-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Failure injection via FAILURE_CONFIG.get at call time (never import time) — allows live mutation in Phase 5"
    - "Dynamic failure key pattern: f'failed_to_charge_{method}' / f'failed_to_refund_{method}'"
    - "FastAPI Cookie dependency with Annotated[str | None, Cookie()] for zero-overhead cookie extraction"
    - "Open redirect prevention: request.url.path (not str(request.url)) for ?next= param"
    - "_resolve_user shared helper pattern: single JWT decode path for both web and API variants"

key-files:
  created:
    - app/lib/mocks/warehouse_mock.py
    - app/lib/mocks/payment_mock.py
    - app/lib/catalog/catalog_service.py
    - app/lib/auth/dependencies.py
  modified:
    - config.py

key-decisions:
  - "FAILURE_CONFIG default probabilities reset to 0.0 (D-15) — demo runs without failures by default"
  - "request.url.path used for next= param (not full URL) to prevent open redirect T-03-01"
  - "get_current_user_web raises HTTPException(307) not returns RedirectResponse — FastAPI converts it"

# Metrics
duration: 3min
completed: 2026-04-19
---

# Phase 03 Plan 02: Foundation Modules Summary

**FAILURE_CONFIG fixed to 6 payment keys, warehouse/payment mock adapters with configurable failure injection, catalog service with keyword+category search, and FastAPI auth dependency pair — 157 unit tests passing (131 original + 26 xpassed)**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-04-19T19:44:13Z
- **Completed:** 2026-04-19T19:46:30Z
- **Tasks:** 2
- **Files created:** 4
- **Files modified:** 1

## Accomplishments

- Fixed config.py FAILURE_CONFIG: added 4 missing payment keys, reset all to 0.0 defaults per D-15
- Created warehouse_mock.py: 4 functions with failure injection via FAILURE_CONFIG read at call time
- Created payment_mock.py: charge/refund with dynamic key pattern `failed_to_{charge|refund}_{method}`
- Created catalog_service.py: search_products (case-insensitive substring, category filter, combinable) and get_product
- Created auth/dependencies.py: _resolve_user helper, get_current_user_web (307), get_current_user_api (401)
- All 26 xfail Wave 0 stubs now xpass; 131 prior tests still pass; 0 errors

## Task Commits

1. **Task 1: Fix config.py FAILURE_CONFIG + build mock adapters** - `67fb0c9` (feat)
2. **Task 2: Build catalog_service.py and auth/dependencies.py** - `e772c9a` (feat)

**Plan metadata:** (this commit)

## Files Created/Modified

- `config.py` — FAILURE_CONFIG expanded to 6 payment keys, all probabilities set to 0.0
- `app/lib/mocks/warehouse_mock.py` — get_available_quantity, reserve_inventory, ship_order, cancel_order
- `app/lib/mocks/payment_mock.py` — charge, refund with dynamic failure key per payment method
- `app/lib/catalog/catalog_service.py` — search_products, get_product
- `app/lib/auth/dependencies.py` — _resolve_user, get_current_user_web, get_current_user_api

## Test Results

```
uv run pytest tests/unit/ -x -q
131 passed, 26 xpassed, 10 warnings in 19.62s
```

All mock adapter tests (18), catalog service tests (8) now xpass. No regressions.

## Decisions Made

- All FAILURE_CONFIG probabilities reset to 0.0 (D-15): demo ships without artificial failures by default; Phase 5 root token raises them on demand
- Used `request.url.path` (not `str(request.url)`) for the `?next=` redirect parameter to strip the host and prevent open redirect attacks (T-03-01)
- `get_current_user_web` raises `HTTPException(307)` rather than returning `RedirectResponse` — FastAPI's exception handler converts it to the proper HTTP response, keeping the dependency clean

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all implemented modules are fully wired to real data (products_db, users_db, FAILURE_CONFIG).

## Threat Flags

None — T-03-01 open redirect mitigation applied as planned (request.url.path in next= param).

## Self-Check: PASSED

Files verified:
- app/lib/mocks/warehouse_mock.py: FOUND
- app/lib/mocks/payment_mock.py: FOUND
- app/lib/catalog/catalog_service.py: FOUND
- app/lib/auth/dependencies.py: FOUND
- config.py: FOUND (contains `failed_to_charge_paypal: 0.0`)

Commits verified:
- 67fb0c9: FOUND
- e772c9a: FOUND

---
*Phase: 03-web-ui-rest-api*
*Completed: 2026-04-19*
