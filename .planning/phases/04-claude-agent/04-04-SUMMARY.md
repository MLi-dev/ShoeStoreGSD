---
phase: 04-claude-agent
plan: "04"
subsystem: tests
tags: [pytest, unit-tests, integration-tests, guardrails, agent-tools, chat-router, mock]

# Dependency graph
requires:
  - phase: 04-claude-agent
    plan: "01"
    provides: guardrails.check_message(), tools.py (10 async functions)
  - phase: 04-claude-agent
    plan: "02"
    provides: agent.run() — mocked in integration tests
  - phase: 04-claude-agent
    plan: "03"
    provides: chat_router.py (GET /chat, POST /chat/message)

provides:
  - tests/unit/test_guardrails.py — 19 tests proving injection detection + clean message pass-through
  - tests/unit/test_agent_tools.py — 28 tests proving all 10 tool signatures, return shapes, and ownership enforcement
  - tests/integration/test_chat_router.py — 10 tests proving auth gating, guardrails, mocked agent dispatch, error handling

affects:
  - Phase 5 (Langfuse observability) — no test impact expected

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Integration test mocking: patch('app.api.chat_router.agent.run') — target import path used by router, not origin"
    - "Async tool tests: async def test methods in classes with asyncio_mode=auto — no asyncio.run() needed"
    - "History isolation: conftest reset_stores clears agent_history._history (T-04-16)"

key-files:
  created:
    - tests/unit/test_guardrails.py
    - tests/unit/test_agent_tools.py
    - tests/integration/test_chat_router.py
  modified:
    - tests/integration/conftest.py

key-decisions:
  - "async def test methods used in class-based tests (not asyncio.run()) — compatible with asyncio_mode=auto in pyproject.toml"
  - "agent_history._history.clear() added to conftest reset_stores fixture — prevents cross-test history state leakage (T-04-16)"
  - "Integration tests patch app.api.chat_router.agent.run — must match the import path used by the router, not the module where run() is defined"

# Metrics
duration: 4min
completed: "2026-04-19"
---

# Phase 4 Plan 04: Test Suite — Guardrails, Agent Tools, Chat Router Summary

**19 guardrail unit tests, 28 agent tool unit tests, and 10 chat router integration tests — full automated test coverage for CHAT requirements with no real Anthropic API calls**

## Performance

- **Duration:** 4 min
- **Completed:** 2026-04-19
- **Tasks:** 2
- **Files modified:** 3 created, 1 modified

## Accomplishments

- test_guardrails.py: 8 injection patterns detected, 8 clean messages pass, result shape validated — 19 tests total
- test_agent_tools.py: all 10 tools verified async + user_id-first, search/product-details/checkout behavior proven, cross-user order access denied (UNAUTHORIZED)
- test_chat_router.py: GET /chat and POST /chat/message fully covered — auth gating (307), empty/missing body (400), mocked agent dispatch (200 with reply), injection refusal (200 scope refusal + agent.run not called), agent error (500), [root]: stripping
- conftest.py updated to clear agent_history._history between tests (T-04-16)
- Full suite: 188 passed, 1 skipped, 44 xpassed — zero regressions

## Task Commits

1. **Task 1: test_guardrails.py and test_agent_tools.py — unit tests** - `8375e35` (test)
2. **Task 2: test_chat_router.py — integration tests + conftest update** - `8f5b0df` (test)

## Files Created/Modified

- `tests/unit/test_guardrails.py` — 19 tests for check_message(): injection detection and clean message pass-through
- `tests/unit/test_agent_tools.py` — 28 tests: all 10 tools verified for async + user_id-first param, search/details/checkout/ownership behavior
- `tests/integration/test_chat_router.py` — 10 integration tests: auth gating, guardrails, mocked agent, error handling, [root]: stripping
- `tests/integration/conftest.py` — Added agent_history._history.clear() to reset_stores fixture for history isolation

## Decisions Made

- Used `async def` test methods (not `asyncio.run()`) in class-based unit tests — cleanest pattern with asyncio_mode=auto; avoids nested event loop issues
- Mocked `app.api.chat_router.agent.run` (router's import path) not `app.lib.agent.agent.run` (origin) — unittest.mock patches at the point of use
- `agent_history._history.clear()` called both before yield and after yield in reset_stores — symmetric cleanup prevents state leakage in both directions

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Adapted asyncio.run() pattern to async def methods**
- **Found during:** Task 1 — plan code used `asyncio.run()` inside sync class methods
- **Issue:** asyncio_mode=auto in pyproject.toml means pytest-asyncio manages the event loop; calling `asyncio.run()` inside a test causes "This event loop is already running" errors
- **Fix:** All async tool tests written as `async def` methods — pytest-asyncio handles them automatically
- **Files modified:** tests/unit/test_agent_tools.py
- **Commit:** 8375e35

## Known Stubs

None — tests exercise real implementation code (guardrails, tools, chat router). Agent is mocked in integration tests to avoid Anthropic API dependency, which is intentional and documented.

## Threat Surface Scan

No new trust boundaries introduced — test files only.

The T-04-16 mitigation (history isolation between tests) and T-04-17 mitigation (no real Anthropic API calls in tests) are both implemented and verified.

## Self-Check: PASSED

- tests/unit/test_guardrails.py: FOUND
- tests/unit/test_agent_tools.py: FOUND
- tests/integration/test_chat_router.py: FOUND
- Commit 8375e35: FOUND
- Commit 8f5b0df: FOUND
- Full suite 188 passed, 0 failures: VERIFIED

---
*Phase: 04-claude-agent*
*Completed: 2026-04-19*
