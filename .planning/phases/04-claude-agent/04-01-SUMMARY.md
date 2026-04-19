---
phase: 04-claude-agent
plan: "01"
subsystem: agent
tags: [guardrails, regex, asyncio, conversation-history, tool-functions, anthropic]

# Dependency graph
requires:
  - phase: 03-web-ui-rest-api
    provides: cart_service, order_service, catalog_service, auth_service — the services tools.py wraps
  - phase: 02-auth-core-services
    provides: users_db, reset_request, reset_confirm — used by reset_password tool

provides:
  - guardrails.check_message() — prompt injection detection with 5 compiled regex patterns
  - history.append_message/get_messages/clear_history — per-user async conversation store with asyncio.Lock
  - tools.py — 10 async agent tool functions wrapping all existing services

affects:
  - 04-02 (agent loop — imports from guardrails, history, tools)
  - 04-03 (chat endpoint — uses guardrails before agent.run)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Tool functions wrap service layer — tools.py calls service functions, converts dataclasses to dicts"
    - "user_id as first param on all tool functions — enforces D-15 ownership from authenticated session"
    - "asyncio.Lock on all history reads and writes — T-04-01 mitigation"
    - "get_messages returns a copy — prevents external mutation of stored history"
    - "reset_password chains reset_request then reset_confirm using user_id from JWT, never user message"

key-files:
  created:
    - app/lib/guardrails/guardrails.py
    - app/lib/agent/history.py
    - app/lib/agent/tools.py
  modified: []

key-decisions:
  - "5 compiled regex injection patterns at module load — static, never mutate, checked on every message before agent"
  - "get_messages() returns list copy — callers cannot mutate stored history outside the lock"
  - "view_cart adapts get_cart() shape — extracts items/total from cart_service.get_cart data dict"
  - "checkout() validates payment_method before calling order_service — INVALID_PAYMENT_METHOD returned cleanly"
  - "reset_password chains reset_request+reset_confirm using user.email from users_db — email never from user message"

patterns-established:
  - "Tool wrapper pattern: async def tool_fn(user_id: str, ...) -> dict — service call → serialize → return dict"
  - "Injection detection: compile patterns at module top, iterate in check_message, return on first match"
  - "History store: module-level dict + asyncio.Lock, get returns copy, clear sets to [] not del"

requirements-completed:
  - CHAT-01
  - CHAT-02
  - CHAT-03
  - CHAT-04
  - CHAT-05

# Metrics
duration: 3min
completed: "2026-04-19"
---

# Phase 4 Plan 01: Claude Agent Foundation Summary

**Injection-detecting guardrails, asyncio-locked per-user history store, and 10 async tool functions wrapping all existing shoe store services — the complete foundation for the Plan 02 agent loop**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-19T22:03:45Z
- **Completed:** 2026-04-19T22:06:34Z
- **Tasks:** 3
- **Files modified:** 3 created

## Accomplishments

- Guardrails module with 5 compiled regex patterns catches prompt injection before it reaches the agent loop
- Per-user conversation history with asyncio.Lock guards against concurrent request corruption (T-04-01)
- All 10 tool functions implemented with user_id-first signatures, service delegation, and ownership enforcement

## Task Commits

Each task was committed atomically:

1. **Task 1: guardrails.py — injection detection and scope refusal** - `b2488fd` (feat)
2. **Task 2: history.py — per-user conversation store with asyncio.Lock** - `c5a7989` (feat)
3. **Task 3: tools.py — 10 agent tool functions wrapping existing services** - `e3223be` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `app/lib/guardrails/guardrails.py` — 5 compiled injection regex patterns + check_message() returning structured success/failure dicts
- `app/lib/agent/history.py` — In-memory per-user history dict, asyncio.Lock on all ops, get returns copy
- `app/lib/agent/tools.py` — 10 async tool functions: search_products, get_product_details, add_to_cart, view_cart, checkout, place_order, check_order_status, cancel_order, return_order, reset_password

## Decisions Made

- `view_cart` extracts items/total from `cart_service.get_cart()` response dict rather than calling two separate functions — simpler and consistent with existing get_cart return shape
- `place_order` implemented as a direct alias calling `checkout()` — both are valid conversational synonyms
- `reset_password` chains `reset_request` then `reset_confirm` in one tool call — user never provides email, only new_password; email resolved from users_db by user_id from JWT (T-04-05)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Pre-existing `passlib.exc.MissingBackendError: bcrypt` in unit test runner (tests/unit/test_auth_service.py, tests/unit/test_seed.py) — unrelated to this plan. 87 passed + 26 xpassed tests are unaffected by these changes. Documented for visibility but not fixed (out of scope).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All three foundational modules (guardrails, history, tools) import cleanly with no circular dependencies
- Plan 02 (agent loop) can import directly: `from app.lib.guardrails.guardrails import check_message`, `from app.lib.agent import history`, `from app.lib.agent import tools`
- No blockers. Plan 02 can proceed immediately.

---
*Phase: 04-claude-agent*
*Completed: 2026-04-19*
