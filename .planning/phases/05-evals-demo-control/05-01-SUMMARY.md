---
phase: 05-evals-demo-control
plan: 01
subsystem: api
tags: [regex, guardrails, demo-control, failure-injection]

requires:
  - phase: 04-claude-agent
    provides: chat_router.py with Phase 4 [root]: stub to replace

provides:
  - parse_root_instruction() pure function with 5 compiled regex patterns
  - Real [root]: demo control flow in chat router — mutates FAILURE_CONFIG in-place
  - Unit tests covering all 8 behavior cases (TDD RED/GREEN)

affects: [05-evals-demo-control]

tech-stack:
  added: []
  patterns: [module-level compiled regex, pure function returning mutation dict, in-place FAILURE_CONFIG mutation via config module reference]

key-files:
  created:
    - app/lib/guardrails/root_instruction.py
    - tests/unit/test_root_instruction.py
  modified:
    - app/api/chat_router.py

key-decisions:
  - "import config (module) not FAILURE_CONFIG (value) so in-place mutations are visible globally"
  - "Clamp percentage to [0.0, 1.0] in parser to handle values like 9999% safely (T-05-04)"
  - "Root block short-circuits before guardrails and agent.run() — normal flow never reached for [root]: messages"

patterns-established:
  - "Pure parser pattern: parse_root_instruction returns mutation dict, caller applies — no side effects in module"
  - "TDD RED/GREEN commits for business logic with input/output contracts"

requirements-completed:
  - MOCK-03

duration: 12min
completed: 2026-04-19
---

# Phase 05-01: Root Instruction Parser + Chat Router Wiring

**Regex-based demo control parser replacing Phase 4 stub — operators can mutate live failure rates via `[root]: warehouse out_of_stock 50%` in chat**

## Performance

- **Duration:** 12 min
- **Started:** 2026-04-19T00:00:00Z
- **Completed:** 2026-04-19T00:12:00Z
- **Tasks:** 2 (Task 1 TDD: 2 commits; Task 2: 1 commit)
- **Files modified:** 3

## Accomplishments
- Created `parse_root_instruction()` pure function with 5 compiled regex patterns covering all FAILURE_CONFIG keys (warehouse: 2, payment: 6)
- `disable all failures` resets all 8 keys to 0.0 in one call
- Phase 4 stub (`Phase 5 feature — no action taken`) fully replaced with real parse+apply flow

## Task Commits

1. **Task 1 RED: root instruction parser unit tests** - `5defbd3` (test)
2. **Task 1 GREEN: implement parse_root_instruction** - `cc36112` (feat)
3. **Task 2: wire parser into chat_router** - `e2238e4` (feat)

## Files Created/Modified
- `app/lib/guardrails/root_instruction.py` — pure parser with 5 regex patterns + _METHOD_ALIASES dict
- `tests/unit/test_root_instruction.py` — 8 unit test cases (TDD)
- `app/api/chat_router.py` — Phase 4 stub replaced; imports `config` module + `parse_root_instruction`

## Decisions Made
- Import `config` as a module (not `from config import FAILURE_CONFIG`) so in-place dict mutations are visible to mock adapters that also hold a reference to `config.FAILURE_CONFIG`
- Clamped percentage to `[0.0, 1.0]` in parser (T-05-04 mitigation) — values like "9999%" become 1.0, not a runaway float

## Deviations from Plan
None — plan executed exactly as written.

## Issues Encountered
None.

## Next Phase Readiness
- FAILURE_CONFIG can now be mutated live via chat; Plan 05-02 (datasets) and 05-03 (smoke runner) are unblocked

---
*Phase: 05-evals-demo-control*
*Completed: 2026-04-19*

## Self-Check: PASSED
