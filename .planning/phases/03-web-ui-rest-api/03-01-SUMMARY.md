---
phase: 03-web-ui-rest-api
plan: 01
subsystem: testing
tags: [pytest, xfail, integration, unit, catalog, warehouse, payment, mocks]

# Dependency graph
requires:
  - phase: 02-auth-core-services
    provides: "auth/cart/order services, seed data with alice/bob users and 3 orders"
  - phase: 01-domain-foundation
    provides: "Product/Variant dataclasses, store dicts, catalog models"
provides:
  - "Wave 0 test harness skeleton — 7 files, 45 total stubs for CI gate before implementation"
  - "tests/integration/conftest.py with TestClient + auth_client fixtures"
  - "Unit stubs for catalog_service (CAT-02, CAT-03)"
  - "Unit stubs for warehouse_mock (MOCK-01) and payment_mock (MOCK-02)"
  - "Integration stubs for auth router, checkout (CHK-01–04), and orders router (ORD-01–03)"
affects: [03-02, 03-03, 03-04, 03-05, 03-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "xfail stub pattern: pytest.mark.xfail(strict=False, reason='implementation pending') for pre-implementation test skeletons"
    - "Integration conftest pattern: autouse reset_stores clears and re-seeds all dicts before each test"
    - "FAILURE_CONFIG isolation: autouse fixture saves/restores original dict values around each test"

key-files:
  created:
    - tests/unit/test_catalog_service.py
    - tests/unit/test_warehouse_mock.py
    - tests/unit/test_payment_mock.py
    - tests/integration/conftest.py
    - tests/integration/test_auth_router.py
    - tests/integration/test_checkout.py
    - tests/integration/test_orders_router.py
  modified: []

key-decisions:
  - "xfail(strict=False) chosen over skip: stubs appear in pytest output as xfail (not invisible), making it easy to track which tests need implementation"
  - "auth_client fixture uses real POST /auth/login (not mock cookie injection): validates the full login flow works end-to-end when auth router is wired"
  - "conftest uses seed() not hardcoded data: integration tests run against the same 15 products and seeded users as production"

patterns-established:
  - "Stub isolation: FAILURE_CONFIG mutations in tests are always restored via autouse fixture — no cross-test state leakage"
  - "Password correctness: alice uses 'alice-demo-password-2026' and bob uses 'bob-demo-password-2026' (from seed.py, not generic 'password123')"

requirements-completed:
  - CAT-02
  - CAT-03
  - CHK-01
  - CHK-02
  - CHK-03
  - CHK-04
  - ORD-01
  - ORD-02
  - ORD-03
  - MOCK-01
  - MOCK-02

# Metrics
duration: 8min
completed: 2026-04-19
---

# Phase 03 Plan 01: Wave 0 Test Stubs Summary

**45-stub pytest harness skeleton (7 files) covering CAT-02/03, CHK-01–04, ORD-01–03, MOCK-01/02 with xfail markers so CI stays green while implementation waves proceed**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-04-19T19:37:18Z
- **Completed:** 2026-04-19T19:45:00Z
- **Tasks:** 2
- **Files created:** 7

## Accomplishments

- Created 3 unit stub files (26 test cases): catalog_service, warehouse_mock, payment_mock
- Created 4 integration files (19 test cases): conftest with fixtures, auth_router, checkout, orders_router
- Full unit suite still passes: 131 passed, 26 xfailed, 0 errors

## Task Commits

Each task was committed atomically:

1. **Task 1: Unit test stubs for catalog service and mock adapters** - `5d66ded` (test)
2. **Task 2: Integration conftest and integration stubs** - `065b752` (test)

**Plan metadata:** (this commit)

## Files Created/Modified

- `tests/unit/test_catalog_service.py` - 8 stubs for CAT-02 (search) and CAT-03 (get_product)
- `tests/unit/test_warehouse_mock.py` - 6 stubs for MOCK-01 (reserve/cancel/ship/quantity)
- `tests/unit/test_payment_mock.py` - 12 parametrized stubs for MOCK-02 (charge/refund x 3 methods)
- `tests/integration/conftest.py` - TestClient fixture + auth_client (alice login via real POST)
- `tests/integration/test_auth_router.py` - 6 stubs: login cookie, logout, register, open redirect protection
- `tests/integration/test_checkout.py` - 6 stubs: CHK-01/02/03 payment methods, CHK-04 confirmation, failure scenarios
- `tests/integration/test_orders_router.py` - 7 stubs: ORD-01 list/detail, ORD-02 cancel, ORD-03 return, cross-user access

## Decisions Made

- Used `xfail(strict=False)` rather than `skip` so stubs remain visible in pytest output as xfail — easier to track pending implementations
- `auth_client` fixture does a real `POST /auth/login` rather than injecting a cookie directly — validates the real auth flow once it is wired up

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed alice/bob credential mismatch in integration tests**
- **Found during:** Task 2 (Integration conftest and stubs)
- **Issue:** Plan's conftest and test_cross_user_order_access_denied used `"password123"` for alice/bob, but seed.py seeds `"alice-demo-password-2026"` / `"bob-demo-password-2026"`. The auth_client fixture would assert `resp.status_code == 303` and fail immediately.
- **Fix:** Updated conftest auth_client password to `"alice-demo-password-2026"` and test_orders_router bob password to `"bob-demo-password-2026"`
- **Files modified:** tests/integration/conftest.py, tests/integration/test_orders_router.py
- **Verification:** Collection passes; passwords match seed data
- **Committed in:** `065b752` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Required for correctness. The conftest fixture would have thrown an AssertionError on every integration test before any router was implemented.

## Issues Encountered

None — collection succeeded on first attempt for both unit and integration stubs.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Wave 0 test harness is complete. Subsequent plans (03-02 through 03-06) can immediately verify their implementations by running the relevant stub file.
- No blockers. All 131 prior unit tests still pass.

---
*Phase: 03-web-ui-rest-api*
*Completed: 2026-04-19*
