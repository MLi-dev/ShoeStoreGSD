# Phase 5: Evals & Demo Control - Context

**Gathered:** 2026-04-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement the `[root]:` live failure config system so demo operators can reconfigure mock behavior mid-session without restarting the server. Create eval datasets (positive, negative, adversarial) in the required `{input, expected_trajectory, expected_output, tags}` format and a smoke runner that executes at least one real agent call per dataset without an uncaught exception. Phase is complete when all five success criteria in ROADMAP.md are satisfied.

</domain>

<decisions>
## Implementation Decisions

### Root Instruction Parsing
- **D-01:** Parse `[root]:` instructions with regex keyword rules — deterministic, ~5 patterns, no extra API call. Pattern set: `payment fail N% [method]`, `warehouse out_of_stock N%`, `warehouse cancel fail N%`, `refund fail N%`, `disable all failures`. Unrecognized instructions log a warning and return `"Unknown root instruction: ..."` to the operator.
- **D-02:** All 8 FAILURE_CONFIG keys are in scope: `warehouse.out_of_stock`, `warehouse.failed_to_cancel_order`, and all 6 `payment.failed_to_charge/refund_{credit_card|paypal|apple_pay}`. Parser maps method aliases (`credit card` → `credit_card`, `paypal` → `paypal`, `apple pay` → `apple_pay`) to config keys.
- **D-03:** Parser lives in a new `app/lib/guardrails/root_instruction.py` module (or `app/lib/agent/root_instruction.py`) — a pure function `parse_root_instruction(text: str) -> dict` returning `{success: bool, mutations: dict, message: str}`. Route handler in `chat_router.py` calls this directly and applies mutations to `FAILURE_CONFIG` before the agent runs.
- **D-04:** Every root instruction invocation is logged via `logger.warning(...)` with user_id and the raw instruction text — success or failure.

### set_failure_mode Placement
- **D-05:** Route handler only — `parse_root_instruction()` is called in `chat_router.py` after stripping the `[root]:` prefix (already implemented in Phase 4). The parsed mutations are applied directly to `config.FAILURE_CONFIG` in the route handler. Claude never sees root instructions and has **no `set_failure_mode` agent tool** — this prevents any agent-mediated demo control and keeps the security boundary clear.
- **D-06:** The Phase 4 stub (`"Root instruction received. (Phase 5 feature — no action taken.)"`) is replaced with the real parse + apply flow. Successful application returns a confirmation to the operator: `"Applied: {summary of mutations}"`.

### Eval Datasets
- **D-07:** Datasets live in `app/lib/evals/datasets/` — three files: `positive.py`, `negative.py`, `adversarial.py`. Each is a plain Python list of dicts matching `{input, expected_trajectory, expected_output, tags}`. This is the canonical format from REQUIREMENTS.md (TEST-04).
- **D-08:** deepeval used for dataset storage + import only — wrap each dataset in a `deepeval.EvaluationDataset` for loading. No deepeval metrics, no LLM-as-judge, no `@pytest.mark.parametrize` deepeval decorator. Plain pytest assertions in the smoke runner.
- **D-09:** Positive dataset: cases for successful search, add-to-cart, checkout, order status lookup, and cancellation (5 cases minimum, one per success criteria item TEST-01).
- **D-10:** Negative dataset: out-of-stock during checkout, payment failure during checkout, cancel without order ID, return on non-returnable order, wrong-user order access (5 cases covering TEST-02).
- **D-11:** Adversarial dataset: prompt injection attempt, off-topic request (cookie recipe), typos (`"Cansel odrer"`), sarcasm after failure, all-caps input (5 cases covering TEST-03).

### Eval Runner
- **D-12:** Smoke runner makes **real Anthropic API calls** — one case per dataset (3 total). Requires `ANTHROPIC_API_KEY` in environment. Runner is a pytest file `tests/evals/test_smoke.py` (or `app/lib/evals/runner.py` invoked via pytest). Success criterion: no uncaught exception for any of the 3 smoke calls.
- **D-13:** Runner loads all three datasets via `deepeval.EvaluationDataset`, picks the first case from each, calls `agent.run()` with the case's `input` field, and asserts that the result dict has a `success` key and no exception propagates. Expected trajectory and output are not validated in the smoke run — that is v2 scope.

### Claude's Discretion
- Exact regex patterns for root instruction parsing (variations like "set payment failure to 50%", "payment 50%", etc.)
- Whether `root_instruction.py` lives under `app/lib/guardrails/` or `app/lib/agent/`
- Exact wording of eval case `input` strings and `expected_trajectory` lists
- Whether the smoke runner is a standalone `runner.py` or a pytest file in `tests/evals/`
- Whether `ANTHROPIC_API_KEY` absence in the smoke runner causes a skip (via `pytest.mark.skipif`) or a hard fail

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Spec & Requirements
- `/Users/matthew/Downloads/spec_python.md` — canonical spec; §Root Agent Control Token (pp. 275–297) defines root instruction behavior; §Evaluation and Testing (pp. 463–530) defines dataset format and cases
- `.planning/REQUIREMENTS.md` — MOCK-03: root token behavior; TEST-01–TEST-04: eval dataset requirements

### Planning & Architecture
- `.planning/ROADMAP.md` — Phase 5 goal and all 5 success criteria (the acceptance bar)
- `.planning/codebase/CONVENTIONS.md` — error shape, FAILURE_CONFIG shape, DEMO_MODE flag, asyncio.Lock patterns

### Existing Code to Modify
- `config.py` — `FAILURE_CONFIG` dict (all 8 keys) + `DEMO_MODE` flag — root instruction parser mutates this
- `app/api/chat_router.py` — Phase 4 stub at line where `[root]:` is detected; Phase 5 replaces the stub with `parse_root_instruction()` call + FAILURE_CONFIG mutation
- `app/lib/evals/__init__.py` — evals package already exists (empty); datasets go under `app/lib/evals/datasets/`

### Prior Phase Context
- `.planning/phases/04-claude-agent/04-CONTEXT.md` — D-14 (root token stripped in route handler, gated on DEMO_MODE), deferred `set_failure_mode` to Phase 5

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `config.py` — `FAILURE_CONFIG` already structured with all 8 keys at float 0.0; mutate in-place at runtime
- `config.py` — `DEMO_MODE: bool = True` already gates root token behavior
- `app/api/chat_router.py` — root token strip + logging already implemented (Phase 4); stub response to replace
- `app/lib/agent/agent.py` — `agent.run(user_id, user, message)` — the call signature the smoke runner uses
- `app/lib/evals/__init__.py` — evals package exists; add `datasets/` subpackage

### Established Patterns
- `logger.warning(...)` pattern used throughout `chat_router.py` for root token events
- `{"success": bool, "code": str, "message": str, "retryable": bool}` error shape
- Pure-function helpers in `app/lib/` subdirectories (no side effects except at call site)
- Test files mirror app structure: `tests/unit/`, `tests/integration/`

### Integration Points
- `chat_router.py` POST `/chat/message` — replace stub with `parse_root_instruction()` + `FAILURE_CONFIG` mutation
- `app/lib/evals/datasets/` — new subpackage with `positive.py`, `negative.py`, `adversarial.py`
- `tests/evals/test_smoke.py` — new pytest file (or `tests/integration/test_evals_smoke.py`) for the 3-case smoke run

</code_context>

<specifics>
## Specific Ideas

- The regex parser should support `"disable all failures"` as a special case that resets all 8 FAILURE_CONFIG values to 0.0 in one call — useful for demo resets mid-session.
- For method alias mapping, normalize input to lowercase and strip punctuation before matching: `"credit card"` → `"credit_card"`, `"apple pay"` → `"apple_pay"`, `"paypal"` → `"paypal"`.
- The smoke runner should log which case it ran from each dataset so failures are debuggable without re-running.

</specifics>

<deferred>
## Deferred Ideas

- deepeval metrics (AnswerRelevancy, GEval trajectory checking) — v2 scope; not in Phase 5
- Playwright E2E browser automation — deferred to v2 per REQUIREMENTS.md
- Admin debug panel for toggling failures without root prompt syntax — v2 per REQUIREMENTS.md
- Langfuse tracing — deferred to v2 per REQUIREMENTS.md
- Dual-mode eval runner (--mock flag for CI) — Claude may add pytest.mark.skipif on missing ANTHROPIC_API_KEY if appropriate, but full dual-mode runner is not in scope

</deferred>

---

*Phase: 05-evals-demo-control*
*Context gathered: 2026-04-19*
