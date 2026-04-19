---
phase: 03-web-ui-rest-api
plan: 03
subsystem: auth-router, web-templates
tags: [auth, web-ui, jinja2, bootstrap, jwt-cookie, prg-pattern]

# Dependency graph
requires:
  - phase: 03-02
    provides: "auth/dependencies.py, catalog_service, mock adapters"
  - phase: 02-auth-core-services
    provides: "auth_service (login, register, reset_request, reset_confirm, verify_token)"
provides:
  - "auth_router: GET /login /register /auth/reset-request /auth/reset-confirm /"
  - "auth_router: POST /auth/login /auth/register /auth/logout /auth/reset-request /auth/reset-confirm"
  - "base.html: Bootstrap 5.3.3 CDN, navbar, session.pop() flash zone, block content"
  - "4 auth templates: login, register, reset_request, reset_confirm"
  - "SessionMiddleware registered in main.py"
  - "Stub routers: catalog_router, cart_router, orders_router"
affects: [03-04, 03-05, 03-06]

# Tech tracking
tech-stack:
  added:
    - "jinja2==3.1.6 (Jinja2Templates for server-side rendering)"
    - "python-multipart==0.0.26 (Form data parsing for FastAPI)"
  patterns:
    - "PRG pattern: all successful POSTs return 303 redirect (T-03-06)"
    - "_safe_next() guard: blocks absolute and protocol-relative URLs in ?next= (T-03-01)"
    - "httpOnly SameSite=Lax JWT cookie via set_cookie() (T-03-04, D-01)"
    - "Flash messages via request.session['flash'] dict + session.pop() in base.html (D-01)"
    - "Jinja2Templates(directory='app/web/templates') at module level in router"

key-files:
  created:
    - app/api/auth_router.py
    - app/web/templates/base.html
    - app/web/templates/auth/login.html
    - app/web/templates/auth/register.html
    - app/web/templates/auth/reset_request.html
    - app/web/templates/auth/reset_confirm.html
    - app/api/catalog_router.py
    - app/api/cart_router.py
    - app/api/orders_router.py
  modified:
    - main.py
    - pyproject.toml
    - uv.lock

key-decisions:
  - "jinja2 and python-multipart added as dependencies (were in pyproject.toml version pins but not installed)"
  - "_safe_next() validates ?next= starts with / and not // — fallback to /products"
  - "test_protected_route_redirects_to_login_when_unauthenticated remains xfail: /cart route built in Plan 04"

# Metrics
duration: 8min
completed: 2026-04-19
---

# Phase 03 Plan 03: Auth Router + Web Templates Summary

**Auth router (10 endpoints) wired to auth_service, base.html with Bootstrap 5.3.3 CDN and session flash zone, and 4 auth templates (login, register, reset-request, reset-confirm) — 131 passed + 31 xpassed (5 new auth router tests xpassing)**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-04-19T19:44:00Z
- **Completed:** 2026-04-19T19:52:35Z
- **Tasks:** 2
- **Files created:** 9
- **Files modified:** 3 (main.py, pyproject.toml, uv.lock)

## Accomplishments

- Updated main.py: SessionMiddleware + all 4 routers (auth, catalog, cart, orders) registered
- Created catalog_router.py, cart_router.py, orders_router.py as stubs (built in Plans 04-06)
- Created auth_router.py: 5 GET (form rendering) + 5 POST (form processing) endpoints
  - `_safe_next()` open redirect guard for ?next= parameter (T-03-01)
  - httpOnly SameSite=Lax cookie on login (T-03-04)
  - PRG pattern: 303 redirect on all successful POSTs (T-03-06)
  - Flash messages via request.session dict
- Created base.html: Bootstrap 5.3.3 + Bootstrap Icons 1.11.3 CDN, navbar, session.pop() flash zone
- Created login.html with demo credential hint (alice@example.com or bob@example.com)
- Created register.html, reset_request.html (shows token in demo mode D-04), reset_confirm.html
- Added jinja2==3.1.6 and python-multipart==0.0.26 to project dependencies

## Task Commits

1. **Task 1: Update main.py with SessionMiddleware and router stubs** - `15578d5` (feat)
2. **Task 2: Build auth_router.py + base.html + 4 auth templates** - `4d441fd` (feat)

**Plan metadata:** (this commit)

## Files Created/Modified

- `main.py` — SessionMiddleware added, all 4 routers imported and registered
- `app/api/auth_router.py` — 10 endpoints (5 GET + 5 POST), open redirect guard, PRG pattern
- `app/api/catalog_router.py` — stub (empty APIRouter)
- `app/api/cart_router.py` — stub (empty APIRouter)
- `app/api/orders_router.py` — stub (empty APIRouter)
- `app/web/templates/base.html` — Bootstrap 5.3.3 CDN, navbar, flash zone, block content
- `app/web/templates/auth/login.html` — login form with demo credential hint
- `app/web/templates/auth/register.html` — registration form
- `app/web/templates/auth/reset_request.html` — reset request form (shows token in demo mode)
- `app/web/templates/auth/reset_confirm.html` — reset confirm form with token prefill

## Test Results

```
uv run pytest tests/unit/ tests/integration/test_auth_router.py -x -q
131 passed, 1 xfailed, 31 xpassed, 13 warnings in 24.37s
```

5 new auth integration tests now xpass:
- test_login_sets_httponly_cookie (xpass)
- test_login_invalid_credentials_returns_form_with_error (xpass)
- test_logout_deletes_cookie (xpass)
- test_register_new_user_redirects (xpass)
- test_next_param_open_redirect_is_blocked (xpass)

1 still xfail (expected):
- test_protected_route_redirects_to_login_when_unauthenticated — requires /cart route (Plan 04)

## Decisions Made

- Added jinja2 and python-multipart as explicit dependencies (were referenced in pyproject.toml version table but not installed in venv)
- Used `Jinja2Templates(directory="app/web/templates")` at module level — path is relative to working directory (project root), where uvicorn/pytest run
- `_safe_next()` helper validates ?next= starts with `/` and not `//` — blocks protocol-relative URLs and absolute URLs; falls back to `/products`
- Stub router files created in Task 1 so main.py import succeeds before full routers are built

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Missing jinja2 and python-multipart dependencies**
- **Found during:** Task 2 verification (pytest run)
- **Issue:** `ImportError: jinja2 must be installed to use Jinja2Templates` and `RuntimeError: Form data requires "python-multipart"` — both packages were listed in STATE.md version table but not installed in the venv
- **Fix:** `uv add jinja2` and `uv add python-multipart` — pyproject.toml and uv.lock updated
- **Files modified:** pyproject.toml, uv.lock
- **Commit:** 4d441fd (included in Task 2 commit)

## Known Stubs

- `app/api/catalog_router.py` — empty APIRouter, built in Plan 04
- `app/api/cart_router.py` — empty APIRouter, built in Plan 04
- `app/api/orders_router.py` — empty APIRouter, built in Plan 05

These stubs exist solely to allow main.py to import without error. They are intentional and tracked for Plans 04-05.

## Threat Flags

None — all T-03-01 (open redirect), T-03-04 (httpOnly cookie), T-03-06 (PRG) mitigations applied as planned.

## Self-Check: PASSED

Files verified:
- app/api/auth_router.py: FOUND (contains set_cookie, _safe_next, login_post)
- app/web/templates/base.html: FOUND (contains bootstrap@5.3.3, session.pop)
- app/web/templates/auth/login.html: FOUND (contains alice@example.com)
- app/web/templates/auth/register.html: FOUND
- app/web/templates/auth/reset_request.html: FOUND
- app/web/templates/auth/reset_confirm.html: FOUND
- app/api/catalog_router.py: FOUND
- app/api/cart_router.py: FOUND
- app/api/orders_router.py: FOUND
- main.py: FOUND (contains SessionMiddleware, include_router)

Commits verified:
- 15578d5: FOUND
- 4d441fd: FOUND

---
*Phase: 03-web-ui-rest-api*
*Completed: 2026-04-19*
