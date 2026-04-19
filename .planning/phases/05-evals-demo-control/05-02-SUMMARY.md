---
phase: 05-evals-demo-control
plan: 02
subsystem: testing
tags: [deepeval, evals, datasets, test-cases]

requires: []

provides:
  - app/lib/evals/datasets/ subpackage with 15 eval cases across 3 categories
  - EvaluationDataset instances for deepeval integration
  - Canonical {input, expected_trajectory, expected_output, tags} format for all cases

affects: [05-03]

tech-stack:
  added: [deepeval>=3.9.7]
  patterns: [CASES list + EvaluationDataset module pattern, goldens=[] constructor (deepeval v3.9+ API)]

key-files:
  created:
    - app/lib/evals/datasets/__init__.py
    - app/lib/evals/datasets/positive.py
    - app/lib/evals/datasets/negative.py
    - app/lib/evals/datasets/adversarial.py
  modified:
    - pyproject.toml (added deepeval>=3.9.7 to dev dependencies)

key-decisions:
  - "EvaluationDataset(goldens=[]) not test_cases=[] — API changed in deepeval v3.9+"
  - "deepeval added to dev deps only — not needed at runtime, only for evals"

patterns-established:
  - "Dataset module pattern: CASES list[dict] + dataset = EvaluationDataset(goldens=[]) at module level"

requirements-completed:
  - TEST-01
  - TEST-02
  - TEST-03
  - TEST-04

duration: 8min
completed: 2026-04-19
---

# Phase 05-02: Eval Datasets

**15 versioned eval cases across positive/negative/adversarial categories — TEST-01 through TEST-04 satisfied**

## Performance

- **Duration:** 8 min
- **Tasks:** 2 (Task 1: __init__ + positive.py; Task 2: negative.py + adversarial.py)
- **Files modified:** 5 (4 new dataset files + pyproject.toml)

## Accomplishments
- Created `app/lib/evals/datasets/` subpackage with 3 dataset modules (15 cases total)
- All cases follow canonical `{input, expected_trajectory, expected_output, tags}` format
- deepeval installed and wired; `EvaluationDataset` instances available for runner

## Task Commits

1. **All dataset files + deepeval dep** - `eacc48c` (feat)

## Files Created/Modified
- `app/lib/evals/datasets/__init__.py` — package marker
- `app/lib/evals/datasets/positive.py` — 5 happy-path cases (TEST-01)
- `app/lib/evals/datasets/negative.py` — 5 error-condition cases (TEST-02)
- `app/lib/evals/datasets/adversarial.py` — 5 hostile-input cases (TEST-03)
- `pyproject.toml` — added `deepeval>=3.9.7` to dev dependencies

## Decisions Made
- `EvaluationDataset(goldens=[])` — deepeval v3.9+ changed the constructor from `test_cases=` to `goldens=`. Deviation from plan's documented API, corrected by inspecting live constructor signature.

## Deviations from Plan
### Auto-fixed Issues
**1. deepeval API change — `test_cases` → `goldens`**
- **Found during:** Task 1 verification
- **Issue:** Plan documented `EvaluationDataset(test_cases=[])` but installed deepeval uses `goldens=[]`
- **Fix:** Updated constructor call in all 3 dataset files; also added deepeval to pyproject.toml (was missing)
- **Verification:** All 3 imports succeed; `uv run python -c "from ... import CASES"` exits 0

## Issues Encountered
- deepeval was missing from pyproject.toml despite plan claiming it was already added — installed and added to dev deps

## Next Phase Readiness
- All dataset modules importable; Plan 05-03 (smoke runner) can proceed

---
*Phase: 05-evals-demo-control*
*Completed: 2026-04-19*

## Self-Check: PASSED
