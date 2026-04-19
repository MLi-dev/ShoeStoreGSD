# Research: Stack — Python FastAPI + Claude AI Demo Store

**Date:** 2026-04-18
**Confidence:** HIGH (versions verified from live PyPI 2026-04-18)

---

## Verified Package Versions

| Package | Version | Notes |
|---------|---------|-------|
| `fastapi` | 0.136.0 | Requires Pydantic v2; Starlette 1.0.0 bundled |
| `anthropic` | 0.96.0 | `AsyncAnthropic` is native async; `messages.create` is `async def` |
| `langfuse` | 4.3.1 | **Major v4 breaking change** from v2/v3 — verify docs before use |
| `pydantic` | 2.13.2 | v2 only — no v1 compat shim in FastAPI 0.100+ |
| `pydantic-settings` | 2.13.1 | `BaseSettings` lives here, not in pydantic core |
| `passlib` | 1.7.4 | Unmaintained; bcrypt 5.x compat warning (hash still works) |
| `PyJWT` | 2.12.1 | Use this instead of python-jose (see security note below) |
| `itsdangerous` | 2.2.0 | For web UI signed session cookies |
| `bcrypt` | 5.0.0 | Direct use or via passlib |
| `uvicorn` | 0.44.0 | Use `uvicorn[standard]` |
| `jinja2` | 3.1.6 | Already in FastAPI dependency tree |
| `python-multipart` | 0.0.26 | Required for form POST parsing in FastAPI |
| `httpx` | 0.28.1 | Already installed as anthropic dependency |
| `pytest` | 9.0.3 | |
| `pytest-asyncio` | 1.3.0 | Requires `asyncio_mode = "auto"` in config |
| `playwright` | 1.58.0 | `playwright install chromium` needed separately |
| `deepeval` | 3.9.7 | LLM eval framework |

---

## Critical Library Decisions

### ❌ Do NOT use `python-jose`
CVE-2024-33664 (RSA key confusion) is unpatched and the project is unmaintained.

**Use instead:** `PyJWT==2.12.1` for JWT signing, `itsdangerous==2.2.0` for web UI session cookies.

### ⚠️ `passlib` warning
`passlib` is unmaintained since 2020. Emits a deprecation warning with `bcrypt >= 4.0` due to a removed private attribute. Hash functionality still works. Suppress with:
```python
import warnings
warnings.filterwarnings("ignore", ".*bcrypt.*")
```
Alternatively, replace with direct `bcrypt.hashpw()` / `bcrypt.checkpw()` calls — only 3 lines, no wrapper needed.

---

## Q&A: Key Decisions

### Anthropic SDK — Async/Sync Gotchas

- Use `AsyncAnthropic` — it's a native `async def` client. Use `await` directly in FastAPI routes.
- **Never use sync `Anthropic()` inside an async route** — it blocks the event loop. No need for `anyio.to_thread.run_sync()`.
- Tool dispatcher functions should be `async def` for consistency.
- Agent loop pattern:
  ```python
  while stop_reason == "tool_use":
      response = await client.messages.create(...)
      if response.stop_reason == "tool_use":
          tool_results = await dispatch_tools(response.content)
          messages.extend([assistant_msg, user_tool_results_msg])
  ```
- `stop_reason` values: `"end_turn"` | `"max_tokens"` | `"stop_sequence"` | `"tool_use"` | `"pause_turn"` | `"refusal"`

### Pydantic v2 for In-Memory State

- Use plain Python `dataclasses` for **domain objects** (User, Product, Order, Cart) — mutable, no validation overhead on every mutation.
- Use Pydantic `BaseModel` for **FastAPI request/response schemas only**.
- Convert dataclass → Pydantic response: `model_validate(instance)` with `model_config = {"from_attributes": True}`.
- Key v2 API changes vs v1:

| v1 | v2 |
|----|-----|
| `dict()` | `model_dump()` |
| `from_orm()` | `model_validate()` |
| `class Config:` | `model_config = ConfigDict(...)` |
| `@validator` | `@field_validator` (+ `@classmethod`) |

- ❌ Do NOT use `pydantic.dataclasses` for domain objects — they add validation overhead on every mutation.

### Langfuse v4 Integration

- v4 is a breaking change from v2/v3. The `@observe` decorator pattern is changed/removed.
- **Recommended:** manual tracing — `langfuse.trace()` → `trace.span()` → `span.generation()` → `generation.end()`
- Call `langfuse.flush()` explicitly — use a `finally` block in the route handler or FastAPI's `lifespan` shutdown hook.
- Use `lifespan` context manager (not deprecated `@app.on_event`) for startup seeding and shutdown flush.
- ⚠️ Confidence on v4 API: **MEDIUM** — verify against https://langfuse.com/docs/sdk/python before coding the observability module.

### pytest Setup

- Set `asyncio_mode = "auto"` in `pytest.ini` or `pyproject.toml` — required for pytest-asyncio 1.x. Without it, async tests silently skip.
- Use `TestClient` (sync, from `fastapi.testclient`) for ~90% of route tests — simpler and sufficient.
- Use `httpx.AsyncClient(transport=ASGITransport(app=app))` only for streaming or async-specific tests.
- Add an `autouse=True` fixture that calls `reset_stores(); seed()` before each test — critical to prevent test-order dependencies.
- Do NOT mark individual tests with `@pytest.mark.asyncio` when `asyncio_mode = "auto"` is set — redundant.

---

## Recommended `requirements.txt` Structure

```
# Core
fastapi==0.136.0
uvicorn[standard]==0.44.0
python-multipart==0.0.26
pydantic==2.13.2
pydantic-settings==2.13.1
jinja2==3.1.6

# Auth
PyJWT==2.12.1
itsdangerous==2.2.0
bcrypt==5.0.0
passlib==1.7.4

# LLM
anthropic==0.96.0

# Observability
langfuse==4.3.1

# Testing
pytest==9.0.3
pytest-asyncio==1.3.0
httpx==0.28.1
playwright==1.58.0
deepeval==3.9.7
```

---

## What NOT to Use

| Package | Reason |
|---------|--------|
| `python-jose` | CVE-2024-33664, unmaintained |
| `sqlalchemy` / any ORM | No DB — in-memory state only |
| `langchain` / `llamaindex` | Unnecessary abstraction — direct Anthropic SDK is simpler |
| `celery` / `redis` | No background jobs or message queue needed |
| `pydantic.dataclasses` | Validation overhead on domain object mutations |
| Sync `Anthropic()` client | Blocks event loop in async FastAPI routes |
