---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: Phase 2 In Progress
stopped_at: Phase 1 complete — all 4 plans verified, uvicorn startup confirmed
last_updated: "2026-04-19T17:01:48.595Z"
progress:
  total_phases: 5
  completed_phases: 1
  total_plans: 7
  completed_plans: 5
  percent: 71
---

# STATE — ShoeStore AI Demo

*Project memory. Updated at every phase transition and plan completion.*

---

## Project Reference

**Core value:** A working end-to-end loop where a user can discover a shoe, buy it, and resolve an issue — through either the web UI or the chatbot — with every step traced and testable.

**Current focus:** Phase 2 — Auth & Core Services

---

## Current Position

| Field | Value |
|-------|-------|
| Phase | 2 — Auth & Core Services |
| Plan | 02-02 complete (2 of 3) |
| Status | Phase 2 In Progress |
| Mode | yolo |

**Progress:**

```
Phase 1 [##########] 100% ✓ Complete
Phase 2 [######    ] 67% (2/3 plans)
Phase 3 [          ] 0%
Phase 4 [          ] 0%
Phase 5 [          ] 0%
```

**Overall:** 1 / 5 phases complete

---

## Performance Metrics

| Metric | Value |
|--------|-------|
| Phases complete | 1 / 5 |
| Requirements delivered | 12 / 33 |
| Plans executed | 5 |
| Phases with issues | 0 |

---

## Accumulated Context

### Key Decisions (from research)

- **PyJWT** over python-jose — CVE-2024-33664 unpatched; python-jose unmaintained
- **Direct AsyncAnthropic SDK** — no LangChain/LlamaIndex; tool-use loop is ~30 lines
- **Plain Python `dataclasses`** for domain objects — Pydantic `BaseModel` for API schemas only
- **`asyncio.Lock`** on every in-memory check+decrement — prevents inventory oversell race
- **Tool dispatcher always emits `tool_result`** even on exception — prevents Anthropic API crash
- **`[root]:` stripped in route handler** before building messages array, gated on `DEMO_MODE`
- **No streaming token output** — conflicts with agentic tool-use loop; return complete responses
- **Returns allowed on paid/processing/shipped** — not restricted to shipped-only
- **`field(default_factory=list)`** mandatory for list fields on dataclasses — bare `= []` causes shared-mutable-default bug across all instances
- **Store dicts empty at import time** — `users_db/products_db/carts_db/orders_db = {}` populated only by `seed()` in lifespan (D-08)
- **`str | None` union syntax** throughout — no `Optional[]` from typing; built-in `list[]/dict[]` generics only

### Critical Pitfalls (from research)

1. Inventory oversell via async race → `asyncio.Lock` on every check+decrement
2. Agent loop with no hard stop → `for _ in range(MAX_TURNS=10)` with fallback
3. Malformed tool results crash Anthropic API → always append `tool_result` block, even on exception
4. Cross-user order access via agent tool → resolve `user_id` from session only, never from user message
5. Root token reaches LLM before parsing → strip `[root]:` in route handler, gate on `DEMO_MODE`
6. Langfuse v4 API changed from v3 → verify against live docs before implementing `tracer.py`

### Stack Versions (verified 2026-04-18)

| Package | Version |
|---------|---------|
| fastapi | 0.136.0 |
| uvicorn[standard] | 0.44.0 |
| pydantic | 2.13.2 |
| pydantic-settings | 2.13.1 |
| anthropic | 0.96.0 |
| PyJWT | 2.12.1 |
| itsdangerous | 2.2.0 |
| bcrypt | 4.3.0 |
| passlib | 1.7.4 |
| jinja2 | 3.1.6 |
| python-multipart | 0.0.26 |
| langfuse | 4.3.1 |
| pytest | 9.0.3 |
| pytest-asyncio | 1.3.0 |
| httpx | 0.28.1 |
| playwright | 1.58.0 |
| deepeval | 3.9.7 |

### Open Questions

- Langfuse v4 tracing API — must verify against https://langfuse.com/docs/sdk/python before Phase 5

### Todos

*(empty — populated during execution)*

### Blockers

*(none)*

---

## Session Continuity

**Last session:** 2026-04-19T17:06:15Z
**Stopped at:** Phase 2 Plan 02 complete — cart_service.py + order_service.py implemented and tested (42 TDD tests)
**Next action:** Execute 02-03-PLAN.md (unit tests gate: test_auth_service.py, test_cart_service.py, test_order_service.py)

---

*Last updated: 2026-04-18 by roadmapper*
