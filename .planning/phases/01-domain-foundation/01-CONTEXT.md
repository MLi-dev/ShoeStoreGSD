# Phase 1: Domain Foundation - Context

**Gathered:** 2026-04-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Set up the project skeleton, define all domain dataclass models, wire plain module-level in-memory stores, and seed realistic reference data — no HTTP server, no LLM calls. Phase is complete when `uvicorn` starts without errors and a unit test can create, read, and list products and orders in pure Python.

</domain>

<decisions>
## Implementation Decisions

### Packaging
- **D-01:** Use `pyproject.toml` + `uv` for dependency management. `uv.lock` for reproducible installs.
- **D-02:** Flat layout — `app/` at project root alongside `main.py` and `config.py` (no `src/` wrapper).
- **D-03:** Separate dependency groups: `[project.dependencies]` for runtime, `[dependency-groups] dev = [...]` for pytest, ruff, mypy, httpx, playwright.

### Seed Data
- **D-04:** Rich and demo-worthy product data — real-feeling shoe model names, compelling descriptions, realistic pricing ($49–$189). Each product should feel like it belongs in an actual store.
- **D-05:** 15 products, 3 per category: running, hiking, slides, sandals, socks. Each product has at least one size/color variant.
- **D-06:** 2 test users: `alice@example.com` and `bob@example.com`, each with a bcrypt-hashed password.
- **D-07:** 3 seeded prior orders: 1 paid, 1 shipped, 1 canceled — assigned to test users.

### Store Initialization
- **D-08:** In-memory stores are plain module-level dicts, e.g. `products_db: dict[str, Product] = {}` in each `store.py`. Empty at import time.
- **D-09:** Seed data is loaded by calling `seed()` inside the FastAPI `lifespan` async context manager — runs once on startup before any requests are served.

### Testing
- **D-10:** Tests live in a top-level `tests/` directory: `tests/unit/`, `tests/integration/`, `tests/e2e/`.
- **D-11:** Phase 1 unit tests cover: model instantiation, store CRUD operations (add/get/list), and a seed smoke test that calls `seed()` and asserts store counts and content.
- **D-12:** `pytest.ini` or `[tool.pytest.ini_options]` in `pyproject.toml` configures `testpaths = ["tests"]` and `asyncio_mode = "auto"`.

### Claude's Discretion
- Exact shoe model names, descriptions, and pricing within the rich/demo-worthy constraint.
- Specific password used for seeded test users (hashed — never plaintext in seed data).
- Whether `seed.py` exposes a `clear_and_reseed()` helper for test isolation (reasonable addition if it aids testing).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Spec
- `/Users/matthew/Downloads/spec_python.md` — canonical requirements source; Phase 1 covers project structure, domain models, seed data

### Codebase Maps (planning artifacts)
- `.planning/codebase/STRUCTURE.md` — intended directory layout, file naming, where to add new code
- `.planning/codebase/CONVENTIONS.md` — model shapes (already defined for User, Product, Variant, Cart, CartItem, Order, OrderItem), naming conventions, error handling pattern, import rules

### Planning
- `.planning/REQUIREMENTS.md` — CAT-01, CAT-04, SEED-01, SEED-02 are the Phase 1 requirements
- `.planning/ROADMAP.md` — Phase 1 success criteria (4 items)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — greenfield project, no source code exists yet.

### Established Patterns
- Model shapes for all domain objects are pre-defined in `.planning/codebase/CONVENTIONS.md` — planner should use these exactly, not redesign them.
- Error handling shape (`{"success": bool, "code": str, "message": str, "retryable": bool}`) is pre-established — apply to service functions from the start.

### Integration Points
- `main.py` lifespan → calls `seed()` from `app/lib/seed/seed.py`
- `config.py` → defines `FAILURE_CONFIG` dict (needed by later phases; scaffold in Phase 1)
- `tests/unit/` → imports directly from `app/lib/` without starting HTTP server

</code_context>

<specifics>
## Specific Ideas

- Seed data should feel like a real shoe store — think "TrailBlaze X9 Running Shoe" with a proper description, not "Product 1". Categories: running, hiking, slides, sandals, socks.
- `alice@example.com` and `bob@example.com` are the canonical test users — eval datasets in Phase 5 will reference these names, so they must be consistent from Phase 1.
- The FastAPI skeleton in Phase 1 has no routes — just `app = FastAPI()`, the lifespan hook, and empty router stubs (or no routers at all) so `uvicorn main:app` starts cleanly.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-domain-foundation*
*Context gathered: 2026-04-18*
