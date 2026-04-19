# ShoeStore AI Demo — Project Guide

## Project

Python/FastAPI demo shoe store with a Claude-powered chatbot and web UI. In-memory state only. Built for personal learning of agentic development workflows.

**Spec:** `/Users/matthew/Downloads/spec_python.md`
**Planning:** `.planning/` — PROJECT.md, ROADMAP.md, REQUIREMENTS.md, STATE.md

## GSD Workflow

This project uses the GSD (Get Shit Done) agentic development workflow.

**Start each session:**
```
/gsd-resume-work
```

**Phase lifecycle:**
1. `/gsd-discuss-phase N` — gather context
2. `/gsd-plan-phase N` — create execution plan
3. `/gsd-execute-phase N` — implement
4. `/gsd-verify-work` — verify phase goal achieved

**Check progress:** `/gsd-progress`

## Stack

- Python 3.12+, FastAPI 0.136, Pydantic v2
- AsyncAnthropic 0.96 (Claude) — tool-use agent
- Langfuse 4.3 — observability (Wave 4)
- PyJWT 2.12 — JWT auth (NOT python-jose — CVE)
- In-memory dicts/lists — no database
- pytest + playwright-python + deepeval

## Key Decisions

- **No python-jose** — use PyJWT (CVE-2024-33664)
- **No LangChain** — direct Anthropic SDK tool-use loop
- **AsyncAnthropic only** — sync client blocks event loop
- **Plain dataclasses** for domain objects — Pydantic only for API schemas
- **Global failure config** — resets on restart
- **Returns** allowed on paid/processing/shipped orders
- **`[root]:`** token parsed in route handler, never sent to LLM

## Architecture

```
app/
  api/          # FastAPI routers (auth, products, cart, orders, chat)
  web/          # Jinja2 templates
  lib/
    auth/       # JWT, password hashing
    catalog/    # Product search + detail
    cart/       # Cart service (asyncio.Lock)
    orders/     # Order lifecycle (asyncio.Lock)
    mocks/      # Payment + warehouse mock adapters
    agent/      # Claude agent runner + tool registry + guardrails
    observability/  # Langfuse tracer (isolated here only)
    seed/       # Startup seed data
    evals/      # Eval datasets
    guardrails/ # Scope enforcement, root token parser
main.py         # FastAPI app + lifespan (seed on startup)
config.py       # Settings, FAILURE_CONFIG
```

## Critical Pitfalls

1. **Inventory race** — `asyncio.Lock` on every check+decrement
2. **Agent loop runaway** — `for _ in range(MAX_TURNS=10)` hard cap
3. **Malformed tool_result** — always append even on exception
4. **Cross-user order access** — resolve `user_id` from session only
5. **Root token to LLM** — strip `[root]:` in route handler before messages array
