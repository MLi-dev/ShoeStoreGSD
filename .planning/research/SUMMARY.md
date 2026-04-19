# Research Summary — Python FastAPI + Claude AI Demo Shoe Store

**Date:** 2026-04-18
**Sources synthesized:** STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md

---

## Executive Summary

This is a single-process FastAPI application with two client surfaces (Jinja2 web UI + agentic chat), an in-memory data layer, mock payment/warehouse adapters with injectable failure modes, and a Claude tool-use agent instrumented with Langfuse. The project is a demo, not production — no database, no background workers, no external queue. The entire system restarts fresh from seed data every run, which is a feature, not a limitation.

The recommended approach is to build in 4 waves, each independently runnable and testable: domain models first (no HTTP, no LLM), then REST routes + web UI, then the Claude agent + guardrails, then observability + evals. The agent loop is implemented directly against the Anthropic SDK — no LangChain, no LlamaIndex. This keeps the tool-call flow inspectable, traceable, and straightforward to test.

The key risks are concurrency bugs in in-memory state (two checkouts racing to zero inventory), security gaps in tool authorization (agent returning another user's orders), and a malformed tool-result messages array crashing the Anthropic API mid-conversation. All three are easily prevented with asyncio.Lock, session-scoped user_id injection, and a catch-all tool dispatcher. Langfuse v4 is the one area with meaningful uncertainty — its API changed significantly from v3 and must be verified against live docs before implementation.

---

## 1. Recommended Stack

| Package | Version | Rationale |
|---------|---------|-----------|
| `fastapi` | 0.136.0 | Current stable; requires Pydantic v2 |
| `uvicorn[standard]` | 0.44.0 | ASGI server |
| `pydantic` | 2.13.2 | v2 only — v1 compat shim is gone |
| `pydantic-settings` | 2.13.1 | `BaseSettings` lives here, not in pydantic core |
| `anthropic` | 0.96.0 | Use `AsyncAnthropic` — native async, no thread wrapping |
| `PyJWT` | 2.12.1 | JWT signing — replaces python-jose (CVE-2024-33664) |
| `itsdangerous` | 2.2.0 | Signed session cookies for web UI |
| `bcrypt` | 5.0.0 | Password hashing |
| `passlib` | 1.7.4 | Unmaintained but functional; suppress bcrypt warning |
| `jinja2` | 3.1.6 | Web UI templates; already in FastAPI dep tree |
| `python-multipart` | 0.0.26 | Required for form POST parsing |
| `langfuse` | 4.3.1 | Observability — v4 breaking change from v2/v3 |
| `pytest` | 9.0.3 | Set `asyncio_mode = "auto"` in config |
| `pytest-asyncio` | 1.3.0 | Required for async test support |
| `httpx` | 0.28.1 | Already installed as anthropic dependency |
| `playwright` | 1.58.0 | E2E tests; run `playwright install chromium` separately |
| `deepeval` | 3.9.7 | LLM eval framework |

**Do not use:** `python-jose` (CVE), `sqlalchemy` (no DB), `langchain`/`llamaindex` (unnecessary abstraction), sync `Anthropic()` client (blocks event loop).

---

## 2. Table Stakes Features

The chatbot is broken without these. Each one is a gap a live observer will immediately notice.

| Feature | Notes |
|---------|-------|
| Natural language product search | Maps vague intent to catalog query |
| Add to cart via conversation | Must resolve product ID from prior search context |
| Cart visibility in conversation | Required for conversational continuity |
| Checkout confirmation loop | Two-step: confirm intent → checkout; never auto-checkout |
| Order status lookup | Handle missing order ID gracefully |
| Cancel and return flows | Eligibility check + ownership verify before acting |
| Clarification questions for missing info | "Cancel my order" → ask which order |
| Graceful error recovery | Payment failed → suggest next step; no raw stack traces |
| Scope enforcement | Reject off-topic requests |
| Authenticated vs unauthenticated awareness | Cart/order actions fail gracefully when not logged in |
| Session-scoped conversation memory | Multi-turn shopping requires message history per session |
| Typo and broken grammar tolerance | System prompt must not overconstrain phrasing |

**Anti-features to skip:** streaming token output (breaks tool-use loop), persistent cross-session memory, auto-checkout without confirmation, verbose chain-of-thought in responses.

---

## 3. Architecture Pattern

Single FastAPI app. Three routers (Jinja2 web UI, REST API, chat endpoint). Domain services sit between routers and in-memory stores. Mock adapters (payment, warehouse) are injectable and probability-controlled via `FAILURE_CONFIG`. The Claude agent is a direct `for _ in range(MAX_TURNS)` loop against `AsyncAnthropic` — no framework. All Langfuse SDK calls are isolated in `lib/observability/tracer.py`.

**Key patterns:**
- Plain Python `dataclasses` for domain objects — Pydantic `BaseModel` only for API schemas
- `asyncio.Lock` per store module for multi-step read-modify-write sequences
- `TraceContext` dataclass created per request, passed as parameter — never module-level state
- Tool dispatcher always emits a `tool_result` block even on exception
- `[root]:` token parsed and stripped in route handler before building messages array

---

## 4. Top Pitfalls to Watch

| # | Pitfall | Severity | Prevention |
|---|---------|----------|------------|
| 1 | Inventory oversell via async race | Critical | `asyncio.Lock` on every check+decrement |
| 2 | Agent loop with no hard stop | Critical | `for _ in range(MAX_TURNS=10)` with fallback |
| 3 | Malformed tool results crash Anthropic API | Critical | Always append `tool_result` block, even on exception |
| 4 | Cross-user order access via agent tool | Critical | Resolve `user_id` from session only |
| 5 | Root token reaches LLM before parsing | Critical | Strip `[root]:` in route handler; gate on `DEMO_MODE` |
| 6 | Langfuse client failure crashes app | Moderate | `NoopSpan` fallback; wrap all SDK calls in try/except |
| 7 | Flaky tests from non-deterministic failure injection | Moderate | Injectable RNG — `rng=lambda: 0.0` forces failure |

---

## 5. Key Decisions Made

1. **PyJWT not python-jose** — CVE-2024-33664 is unpatched; python-jose is unmaintained.
2. **Direct Anthropic SDK, no LangChain** — The tool-use loop is 30 lines. Frameworks add no value.
3. **`AsyncAnthropic` only** — Sync client blocks the event loop.
4. **Plain `dataclasses` for domain objects** — Pydantic reserved for API schemas only.
5. **Manual Langfuse tracing** — v4 removed the `@observe` decorator; explicit tracing is reliable.
6. **No streaming token output** — Conflicts with the agentic tool-use loop; return complete responses.

---

## 6. Build Order (Waves)

| Wave | What Ships | Testable With |
|------|-----------|---------------|
| **Wave 1** | Models, stores, domain services, seed data, FastAPI skeleton | Pure Python unit tests — no HTTP, no LLM |
| **Wave 2** | Mock adapters, REST API routers, Jinja2 web UI | `TestClient` route tests, Playwright web UI |
| **Wave 3** | Tool registry, Claude agent runner, guardrails, chat endpoint | Agent unit tests with mocked client |
| **Wave 4** | Langfuse tracing, eval datasets, full Playwright E2E suite | Full E2E flows, eval runners |

---

## 7. Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack (versions) | HIGH | Verified from live PyPI 2026-04-18 |
| Features | HIGH | Grounded in spec |
| Architecture | HIGH | Standard FastAPI patterns |
| Langfuse v4 API | MEDIUM | Verify against live docs before Wave 4 |
| Pitfalls | HIGH | Specific, reproducible with code-level prevention |

**One gap:** Langfuse v4 tracing API must be verified against https://langfuse.com/docs/sdk/python before implementing `tracer.py`.

---

## Sources

- `/Users/matthew/Dev/ShoeStoreGSD/.planning/research/STACK.md`
- `/Users/matthew/Dev/ShoeStoreGSD/.planning/research/FEATURES.md`
- `/Users/matthew/Dev/ShoeStoreGSD/.planning/research/ARCHITECTURE.md`
- `/Users/matthew/Dev/ShoeStoreGSD/.planning/research/PITFALLS.md`
- Spec: `/Users/matthew/Downloads/spec_python.md`
