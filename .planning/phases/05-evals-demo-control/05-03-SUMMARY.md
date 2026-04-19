---
phase: 05-evals-demo-control
plan: 03
subsystem: testing
tags: [pytest, pytest-asyncio, evals, smoke-test, anthropic]

requires:
  - phase: 05-evals-demo-control (plan 02)
    provides: eval dataset CASES lists imported by smoke runner

provides:
  - tests/evals/ package with 3 async smoke tests (one per dataset)
  - Graceful skip when ANTHROPIC_API_KEY absent — CI-safe
  - Store reset fixture replicating integration conftest pattern

affects: []

tech-stack:
  added: []
  patterns: [pytestmark module-level skipif, autouse reset_stores fixture, smoke_user fixture from seeded store]

key-files:
  created:
    - tests/evals/__init__.py
    - tests/evals/test_smoke.py
  modified: []

key-decisions:
  - "pytestmark = pytest.mark.skipif(...) at module level skips all 3 tests together — cleaner than per-test decorators"
  - "Only assert 'success' in result — trajectory/output validation is v2 scope per D-13"

patterns-established:
  - "Eval smoke pattern: autouse reset_stores + smoke_user fixture + single assert on result key"

requirements-completed:
  - TEST-04

duration: 6min
completed: 2026-04-19
---

# Phase 05-03: Eval Smoke Runner

**3 async smoke tests — one per eval dataset — skip gracefully without ANTHROPIC_API_KEY**

## Performance

- **Duration:** 6 min
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments
- `tests/evals/test_smoke.py` collects exactly 3 tests: positive, negative, adversarial
- All 3 skip with exit code 0 when `ANTHROPIC_API_KEY` is unset
- Each test logs case tags and input for debuggability (D-12)
- No assertions beyond `"success" in result` — minimal smoke bar per D-13

## Task Commits

1. **smoke runner + evals package** - `ca9db7b` (feat)

## Files Created/Modified
- `tests/evals/__init__.py` — package marker
- `tests/evals/test_smoke.py` — 3 async smoke tests with module-level skipif

## Decisions Made
- Module-level `pytestmark` skipif applied to all tests in one line rather than repeating the decorator 3 times

## Deviations from Plan
None — plan executed exactly as written.

## Issues Encountered
None.

## Next Phase Readiness
- Phase 5 complete. All 3 plans done. Full test suite passing (196 passed, 1 skipped).

---
*Phase: 05-evals-demo-control*
*Completed: 2026-04-19*

## Self-Check: PASSED
