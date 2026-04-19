# Phase 5: Evals & Demo Control - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-19
**Phase:** 05-evals-demo-control
**Areas discussed:** Root instruction parsing, set_failure_mode placement, Eval runner, deepeval scope

---

## Root Instruction Parsing

| Option | Description | Selected |
|--------|-------------|----------|
| Regex keyword rules | ~5 deterministic patterns, no extra API call | ✓ |
| LLM-parsed (Claude) | Flexible natural language, costs extra API call | |
| You decide | Claude picks | |

**User's choice:** Regex keyword rules

---

| Option | Description | Selected |
|--------|-------------|----------|
| All 8 keys | All warehouse + payment keys matching FAILURE_CONFIG shape | ✓ |
| Simplified subset | Only most demo-useful keys | |
| You decide | Claude picks | |

**User's choice:** All 8 FAILURE_CONFIG keys in scope

---

## set_failure_mode Placement

| Option | Description | Selected |
|--------|-------------|----------|
| Route handler only | parse_root_instruction() in chat_router.py; Claude never sees root instructions | ✓ |
| Agent tool (as spec) | set_failure_mode registered as agent tool; Claude calls it | |
| You decide | Claude picks safest/simplest | |

**User's choice:** Route handler only — cleaner security boundary, Claude has no set_failure_mode tool

---

## Eval Runner

| Option | Description | Selected |
|--------|-------------|----------|
| Mock agent | Mocks agent.run(), CI-safe, validates runner logic only | |
| Real API calls (one case) | Real agent.run() call per dataset, requires ANTHROPIC_API_KEY | ✓ |
| Dual mode | --mock flag for CI, real calls by default | |

**User's choice:** Real API calls — one case per dataset

---

| Option | Description | Selected |
|--------|-------------|----------|
| app/lib/evals/ | Consistent with existing app/lib/ structure, directory exists | ✓ |
| Top-level evals/ | Cleaner separation from app code | |

**User's choice:** app/lib/evals/

---

## deepeval Usage Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Dataset storage + import only | Plain Python dicts, deepeval.EvaluationDataset as wrapper, plain pytest assertions | ✓ |
| Full deepeval metrics | LLMTestCase, GEval trajectory, AnswerRelevancy — full power | |
| Don't use deepeval | Ignore deepeval entirely, plain .py files only | |

**User's choice:** Dataset storage + import only — no LLM-as-judge in Phase 5

---

## Claude's Discretion

- Exact regex patterns (variations of root instruction phrasing)
- Module location for root_instruction.py (guardrails/ vs agent/)
- Exact wording of eval case inputs and expected trajectories
- Smoke runner file location (tests/evals/ vs tests/integration/)
- ANTHROPIC_API_KEY absence handling (skip vs hard fail)

## Deferred Ideas

- deepeval metrics (AnswerRelevancy, GEval) — v2
- Playwright E2E automation — v2
- Admin debug panel — v2
- Langfuse tracing — v2
- Dual-mode eval runner — not in scope
