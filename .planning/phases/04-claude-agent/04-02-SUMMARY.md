---
phase: 04-claude-agent
plan: "02"
subsystem: agent
tags: [anthropic, asyncio, tool-use, agent-loop, fastapi]

# Dependency graph
requires:
  - phase: 04-claude-agent
    plan: "01"
    provides: history.append_message/get_messages, tools.py 10 async tool functions

provides:
  - agent.run(user_id, user, message) — single public entry point for one user turn
  - TOOL_SCHEMAS — list of 10 Anthropic tool definitions for the API call
  - _TOOL_REGISTRY — maps tool name strings to async tool functions
  - _dispatch_tool() — safe tool dispatcher (unknown tools return failure dict, never raise)
  - MAX_TURNS = 10 — hard cap enforced by the loop (T-04-06 mitigation)

affects:
  - 04-03 (chat endpoint — calls agent.run() directly)
  - 04-04 (tracer — wraps agent.run() calls with Langfuse)

# Tech tracking
tech-stack:
  added:
    - anthropic>=0.96.0 (added to pyproject.toml, uv.lock)
  patterns:
    - "Tool-use loop: for _ in range(MAX_TURNS) with break on end_turn — hard cap, no infinite loop"
    - "tool_result always appended after tool dispatch — even on exception (D-13)"
    - "Intermediate tool-use turns mutate local messages copy — not stored in history"
    - "_dispatch_tool returns failure dict for unknown names — T-04-07 registry gating"
    - "user_id only from function parameter — never parsed from message string (D-15)"

key-files:
  created:
    - app/lib/agent/agent.py
  modified:
    - pyproject.toml
    - uv.lock

key-decisions:
  - "anthropic added as explicit pyproject.toml dependency — was missing from project config"
  - "Intermediate tool-use assistant/user turns live only in local messages list — history stores only user message + final assistant reply"
  - "messages list is history.get_messages() copy — safe to mutate during loop without corrupting stored history"
  - "_dispatch_tool wraps tool call in try/except to guarantee it never raises to caller (belt+suspenders with run()'s own guard)"

patterns-established:
  - "Agent loop: append user → get copy → loop(call API → end_turn: store reply / tool_use: dispatch+append results)"
  - "Tool dispatch gate: _TOOL_REGISTRY.get(name) → None → UNKNOWN_TOOL dict (T-04-07)"
  - "Exception containment: API errors → AGENT_ERROR response; tool errors → failure dict as tool_result content"

requirements-completed:
  - CHAT-01
  - CHAT-02
  - CHAT-03
  - CHAT-05

# Metrics
duration: 7min
completed: "2026-04-19"
---

# Phase 4 Plan 02: Claude Agent Loop Summary

**AsyncAnthropic tool-use loop with 10-tool registry, MAX_TURNS=10 hard cap, and always-appended tool_result blocks — the core engine connecting history + tools into a single async run() entry point**

## Performance

- **Duration:** 7 min
- **Started:** 2026-04-19T22:07:00Z
- **Completed:** 2026-04-19T22:14:06Z
- **Tasks:** 1
- **Files modified:** 1 created, 2 modified (pyproject.toml, uv.lock)

## Accomplishments

- agent.run() orchestrates the full Anthropic tool-use conversation loop in a single async function
- MAX_TURNS = 10 hard cap prevents runaway loops regardless of LLM behavior (T-04-06)
- _dispatch_tool() gates on _TOOL_REGISTRY — unknown tool names return failure dict without executing anything (T-04-07)
- tool_result always appended after each tool dispatch (double-guarded in _dispatch_tool and run()) — prevents Anthropic API crash (D-13)
- Intermediate tool-use turns are NOT stored in history — only the initial user message and final assistant reply are persisted
- Added anthropic>=0.96.0 to pyproject.toml (was missing from project dependencies)

## Task Commits

Each task was committed atomically:

1. **Task 1: agent.py — AsyncAnthropic tool-use loop with tool registry** - `0336e70` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `app/lib/agent/agent.py` — AsyncAnthropic tool-use loop: run(), _build_system_prompt(), _dispatch_tool(), _extract_text(), TOOL_SCHEMAS (10 entries), _TOOL_REGISTRY (10 entries), MAX_TURNS=10
- `pyproject.toml` — Added anthropic>=0.96.0 dependency
- `uv.lock` — Updated lockfile with anthropic 0.96.0 + transitive deps (distro, docstring-parser, jiter, sniffio)

## Decisions Made

- `anthropic` package was not listed in `pyproject.toml` — added via `uv add` as a deviation (Rule 3 - blocking). The package is a required runtime dependency for the agent loop to import.
- Intermediate tool-use assistant/user turns mutate only the local `messages` copy from `history.get_messages()`. This is intentional — history stores only the user message and final assistant reply, keeping history clean for future turns.
- `_dispatch_tool` wraps the tool call in its own try/except (in addition to the outer guard in `run()`) to guarantee it never raises to the caller — belt-and-suspenders for D-13 compliance.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added anthropic>=0.96.0 to pyproject.toml**
- **Found during:** Task 1 (importing AsyncAnthropic)
- **Issue:** `anthropic` package not listed in pyproject.toml dependencies; import would fail at runtime
- **Fix:** Ran `uv add "anthropic>=0.96.0"` — added to pyproject.toml and updated uv.lock
- **Files modified:** pyproject.toml, uv.lock
- **Verification:** Import confirmed working via `arch -x86_64 .venv/bin/python -c "from anthropic import AsyncAnthropic"`
- **Committed in:** 0336e70 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 3 - blocking dependency)
**Impact on plan:** Essential fix — agent loop cannot run without the anthropic package. No scope creep.

## Issues Encountered

- The project venv has x86_64 pydantic_core binaries on an arm64 machine; Python runs under Rosetta x86_64 emulation. Tests pass correctly under the existing test runner. Verification commands were run with `arch -x86_64` to match the Rosetta execution environment.
- Pre-existing `passlib.exc.MissingBackendError: bcrypt` in unit tests — unrelated to this plan. 87 passed, 26 xpassed, same as Wave 1 baseline.

## User Setup Required

None - no external service configuration required. `ANTHROPIC_API_KEY` is read from environment at runtime by `AsyncAnthropic()` — not required for import or unit test execution.

## Threat Surface Scan

No new network endpoints, auth paths, or trust boundaries introduced beyond those documented in the plan's threat model. All T-04-06 through T-04-10 mitigations implemented as specified.

## Next Phase Readiness

- `agent.run(user_id, user, message)` is ready for the chat route handler (Plan 04-03) to call
- TOOL_SCHEMAS and _TOOL_REGISTRY are module-level exports usable for introspection or testing
- No blockers. Plan 04-03 (chat endpoint) can proceed immediately.

---
*Phase: 04-claude-agent*
*Completed: 2026-04-19*
