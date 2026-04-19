# Technology Stack

**Analysis Date:** 2026-04-18
**Status:** Planned/Intended — no source code implemented yet. This document reflects the spec-prescribed stack from `spec_python.md`.

## Languages

**Primary:**
- Python 3.12+ — entire backend, agent orchestration, tests, and tooling

**Secondary:**
- HTML/CSS via Jinja2 templates — server-rendered web UI (default per spec)
- JavaScript (minimal) — only as needed for chat UI interactivity within Jinja2 pages

## Runtime

**Environment:**
- CPython 3.12+

**Package Manager:**
- pip with `requirements.txt` (or `pyproject.toml` with uv)
- Lockfile: `requirements.txt` or `uv.lock`

## Frameworks

**Core:**
- FastAPI — primary web framework; REST API endpoints, Jinja2 template serving, auto-generated OpenAPI docs
- Uvicorn — ASGI server for development and production

**Templating:**
- Jinja2 — server-rendered HTML for web storefront and chat UI pages (via FastAPI `TemplateResponse`)

**Data Modeling:**
- Python `dataclasses` — domain models: `User`, `Product`, `Variant`, `Cart`, `CartItem`, `Order`, `OrderItem`
- Pydantic v2 — request/response validation on FastAPI endpoints; doubles as schema documentation

**Configuration:**
- `pydantic-settings` — typed environment variable loading from `.env` (preferred over plain `os.environ`)

**Auth:**
- `passlib[bcrypt]` — password hashing
- `python-jose[cryptography]` or `itsdangerous` — JWT tokens or signed session cookies for web UI session support

**LLM:**
- `anthropic` — Anthropic Python SDK; Claude model calls for all chatbot agent functionality

**Observability:**
- `langfuse` — Python SDK; LLM traces at agent, tool, and generation level

**Testing:**
- `pytest` — unit and integration test runner
- `pytest-asyncio` — async test support for FastAPI routes
- `httpx` — async HTTP client used with FastAPI `TestClient` for integration tests
- `playwright` (via `playwright-python`) — browser automation for end-to-end tests
- `deepeval` or `promptfoo` — LLM evaluation framework for agentic test datasets with `[input, trajectory, output]` format

**Build/Dev:**
- `uvicorn --reload` — development server
- No frontend build pipeline; Jinja2 templates and static assets served directly by FastAPI

## Key Dependencies

**Critical:**
- `fastapi` — web framework; core to all endpoint routing
- `anthropic` — LLM calls; required for chatbot agent
- `langfuse` — observability; required for trace capture on all agent/tool/generation steps
- `passlib[bcrypt]` — password hashing; required for auth module
- `python-jose[cryptography]` or `itsdangerous` — session/token signing; required for auth

**Infrastructure:**
- `uvicorn[standard]` — ASGI server
- `pydantic-settings` — env config loading
- `jinja2` — HTML templating (transitively included by FastAPI; list explicitly)
- `python-multipart` — required for FastAPI form data handling (login/signup forms)

**Testing:**
- `pytest` — test runner
- `pytest-asyncio` — async test support
- `httpx` — HTTP client for `TestClient` integration tests
- `playwright` — browser automation; requires `playwright install` for browser binaries
- `deepeval` — LLM eval dataset runner

## State Management

**Persistence:**
- None. All state is held in in-memory Python dicts and lists only.
- Every application restart clears all state.
- In-memory stores (module-level globals): `users: dict[str, User]`, `products: dict[str, Product]`, `carts: dict[str, Cart]`, `orders: dict[str, Order]`
- State is seeded at startup from `app/lib/seed/seed.py`

**Session State:**
- Chatbot conversation context: per-session in-memory dict keyed by session ID
- Web UI session: signed cookie or JWT (stateless; no server-side session store)

**Failure Config:**
- `FAILURE_CONFIG` dict in `config.py` is mutable at runtime via root instructions
- Keyed by mock component and failure type with float probability values

## Configuration

**Environment:**
- Loaded via `pydantic-settings` from `.env` file
- Key required vars (names only — never read `.env` contents):
  - `ANTHROPIC_API_KEY`
  - `LANGFUSE_PUBLIC_KEY`
  - `LANGFUSE_SECRET_KEY`
  - `LANGFUSE_HOST`
  - `SECRET_KEY` (cookie/JWT signing)
  - `APP_MODE` (`dev` or `prod`; controls root instruction availability)

**Failure Injection Config:**
- `config.py` — holds `FAILURE_CONFIG` dict (mutable at runtime)
- Format: `{"warehouse": {"out_of_stock": 0.10}, "payment": {"failed_to_charge_credit_card": 0.03}}`
- Can be loaded from JSON/YAML or hardcoded as Python dict

**Entry Point:**
- `main.py` — FastAPI app instantiation and startup

## Platform Requirements

**Development:**
- Python 3.12+
- `.env` file with `ANTHROPIC_API_KEY` and `LANGFUSE_*` keys
- Run `playwright install` to install browser binaries for E2E tests

**Production:**
- Any ASGI-capable host (Fly.io, Railway, Render, or local)
- Single-process deployment required (in-memory state is not shared across workers)
- No database, no Redis, no external queue required

---

*Stack analysis: 2026-04-18*
