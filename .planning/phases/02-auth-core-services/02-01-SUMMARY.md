---
phase: 02-auth-core-services
plan: 01
subsystem: auth
tags: [jwt, bcrypt, password-reset, auth-service, pyjwt]
dependency_graph:
  requires: []
  provides:
    - app/lib/auth/auth_service.py (register, login, verify_token, reset_request, reset_confirm)
    - app/lib/auth/store.py (users_db, reset_tokens_db)
    - config.py (JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES)
  affects:
    - Phase 3 auth routers (depend on auth_service functions)
    - Phase 4 agent (depends on verify_token for session resolution)
tech_stack:
  added:
    - PyJWT 2.12.1 (JWT encode/decode)
  patterns:
    - TDD RED/GREEN/REFACTOR for all three tasks
    - Structured dict returns (success/failure shape) — no exceptions for expected failures
    - In-memory dict stores keyed by UUID or email
key_files:
  created:
    - app/lib/auth/auth_service.py
    - tests/unit/test_auth_service.py
    - tests/unit/test_auth_store.py
    - tests/unit/test_config_jwt.py
  modified:
    - config.py (added JWT constants)
    - app/lib/auth/store.py (added reset_tokens_db)
    - pyproject.toml (added PyJWT dependency)
    - uv.lock (updated)
decisions:
  - "PyJWT over python-jose: CVE-2024-33664 unpatched; PyJWT 2.12.1 used"
  - "datetime.now(timezone.utc) over deprecated utcnow() throughout"
  - "Demo reset token returned in response body — intentional, no email server"
  - "INVALID_CREDENTIALS returned for both wrong-password and no-user — prevents user enumeration (T-02-01)"
metrics:
  duration_seconds: 209
  completed_date: "2026-04-19"
  tasks_completed: 3
  files_created: 4
  files_modified: 4
---

# Phase 2 Plan 1: Auth Service Summary

**One-liner:** JWT auth with bcrypt password hashing and 15-minute expiring reset tokens using PyJWT and passlib.

---

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Extend config.py with JWT constants | 9f54d22 | config.py |
| 2 | Extend auth store with reset_tokens_db | fe8638d | app/lib/auth/store.py |
| 3 | Implement auth_service.py | 8432fbb | app/lib/auth/auth_service.py |

---

## What Was Built

**config.py** — Three JWT constants appended after `DEMO_MODE`:
- `JWT_SECRET = "dev-secret-change-in-prod"`
- `JWT_ALGORITHM = "HS256"`
- `JWT_EXPIRE_MINUTES = 30`

**app/lib/auth/store.py** — Extended with `reset_tokens_db`:
- `dict[str, dict[str, str | datetime]]` keyed by email
- In-memory only, resets on restart

**app/lib/auth/auth_service.py** — Five public functions:
- `register(email, password)` — bcrypt hash, UUID id, duplicate email rejection
- `login(email, password)` — JWT encode with expiry, user enumeration prevention
- `verify_token(token)` — PyJWT decode, structured error codes for expiry vs tampering
- `reset_request(email)` — 15-minute expiring token, demo token-in-body pattern, identical message whether email exists or not
- `reset_confirm(token, new_password)` — expiry enforcement, single-use token deletion

---

## Test Coverage

24 new unit tests across 3 files (61 total passing):
- `tests/unit/test_config_jwt.py` — 3 tests
- `tests/unit/test_auth_store.py` — 3 tests
- `tests/unit/test_auth_service.py` — 18 tests covering all five functions, including security properties (enumeration prevention, expiry enforcement, token single-use)

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] PyJWT missing from pyproject.toml**
- **Found during:** Task 3 setup
- **Issue:** `PyJWT` not listed in `pyproject.toml` dependencies; `import jwt` would fail at runtime
- **Fix:** Added `pyjwt>=2.12.0` to `[project.dependencies]` in pyproject.toml, ran `uv add` to install and update uv.lock
- **Files modified:** pyproject.toml, uv.lock
- **Commit:** e71b952

**2. [Rule 1 - Bug] Ruff import ordering and line length in auth_service.py**
- **Found during:** Task 3 post-implementation lint
- **Issue:** `from config import ...` was not sorted after third-party imports per isort rules; two docstring lines exceeded 88 chars
- **Fix:** `ruff check --fix` corrected import order; docstring lines manually wrapped
- **Files modified:** app/lib/auth/auth_service.py
- **Commit:** included in 8432fbb

---

## Security Properties Implemented

Per threat model mitigations:

| Threat ID | Mitigation | Status |
|-----------|-----------|--------|
| T-02-01 | INVALID_CREDENTIALS returned for both wrong-pass and no-user | Implemented + tested |
| T-02-02 | jwt.decode() verifies HS256 signature; InvalidTokenError caught | Implemented + tested |
| T-02-04 | password_hash never in any return value | Implemented + tested |
| T-02-05 | reset_request response identical whether email exists or not | Implemented + tested |
| T-02-06 | Expired tokens deleted on detection; 15-min window | Implemented + tested |

---

## Known Stubs

None — all five functions are fully wired to the in-memory stores.

---

## Threat Flags

None — no new network endpoints, auth paths, or schema changes beyond what the plan's threat model covers.

---

## TDD Gate Compliance

All three tasks followed RED/GREEN/REFACTOR:
- RED commits: 25bb00b, 9df7547, c62406c
- GREEN commits: 9f54d22, fe8638d, 8432fbb
- No REFACTOR commits needed (code was clean after GREEN)

## Self-Check: PASSED
