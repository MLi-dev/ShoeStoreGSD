---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: Milestone Complete
stopped_at: Phase 5 complete (3/3 plans)
last_updated: "2026-04-19T00:00:00.000Z"
progress:
  total_phases: 5
  completed_phases: 5
  total_plans: 20
  completed_plans: 20
  percent: 100
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
| Phase | 5 — Evals & Demo Control |
| Plan | 05-03 complete (3 of 3) |
| Status | Phase 5 Complete — Milestone v1 Complete |
| Mode | yolo |

**Progress:**

```
Phase 1 [##########] 100% ✓ Complete
Phase 2 [##########] 100% ✓ Complete
Phase 3 [##########] 100% ✓ Complete
Phase 4 [##########] 100% ✓ Complete
Phase 5 [##########] 100% ✓ Complete
```

**Overall:** 5 / 5 phases complete — Milestone v1 Done

---

## Performance Metrics

| Metric | Value |
|--------|-------|
| Phases complete | 3 / 5 |
| Requirements delivered | 33 / 33 |
| Plans executed | 14 |
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
- **POST /cart/add in catalog_router** — form action on product detail page; cart_router owns GET /cart, POST /cart/update, /cart/remove, POST /checkout
- **`str | None` union syntax** throughout — no `Optional[]` from typing; built-in `list[]/dict[]` generics only
- **Tool functions wrap service layer** — tools.py calls service functions and converts dataclasses to serializable dicts; never returns dataclass instances
- **user_id as first param on all tool functions** — enforces D-15 ownership from authenticated session, never from message content
- **get_messages() returns a list copy** — prevents external mutation of stored history outside the asyncio.Lock (T-04-01)
- **reset_password chains reset_request+reset_confirm** — resolves email from users_db by user_id from JWT; email never from user message (T-04-05)
- **Intermediate tool-use turns not stored in history** — history stores only user message + final assistant reply; tool-use assistant/user turns live only in local messages copy for that call
- **anthropic added to pyproject.toml** — was missing from project dependencies; added via `uv add` during 04-02 execution
- **Guard rejections return HTTP 200 with reply message** — avoids leaking injection detection to attackers; HTTPException(500) only on genuine agent loop failures
- **Chat navbar link inside `{% if current_user %}` block** — hidden from unauthenticated users; consistent with existing auth-gated nav pattern

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

**Last session:** 2026-04-19T00:00:00.000Z
**Stopped at:** Phase 5 complete — Milestone v1 complete
**Next action:** None — all phases done

---

*Last updated: 2026-04-18 by roadmapper*
