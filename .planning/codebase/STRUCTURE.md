# Codebase Structure

**Analysis Date:** 2026-04-18
**Status:** Planned — no source code implemented yet. This document reflects the intended structure as prescribed in the project spec (`/Users/matthew/Downloads/spec_python.md`).

## Directory Layout

```
demo-store/
├── main.py               # FastAPI app entry point — creates app, registers routers, fires startup seed
├── config.py             # FAILURE_CONFIG dict + env/settings (pydantic-settings or os.environ)
├── spec.md               # Project spec (source of truth for requirements)
├── README.md             # Setup and run instructions
└── app/
    ├── web/              # Jinja2 templates or static React build for storefront UI
    ├── chat/             # Chat UI route templates and frontend JS
    ├── api/              # FastAPI routers (one per domain)
    └── lib/
        ├── auth/         # Signup, login, password reset logic + in-memory user store
        ├── catalog/      # Product search, product details + in-memory product store
        ├── cart/         # Cart management (add, update, remove, totals) + in-memory cart store
        ├── orders/       # Order lifecycle (create, status, cancel, return) + in-memory order store
        ├── mocks/        # Warehouse and payment mock adapters with failure injection
        ├── agent/        # LLM agent runner, tool registry, root instruction parser
        ├── observability/ # Langfuse instrumentation helpers, event emitters
        ├── seed/         # Startup data loader — products, test users, sample orders
        ├── evals/        # Eval datasets (JSON/YAML) and eval runner scripts
        └── guardrails/   # Prompt injection detection and scope enforcement
```

## Directory Purposes

**`demo-store/app/api/`:**
- Purpose: FastAPI router modules, one per domain
- Contains: `auth_router.py`, `catalog_router.py`, `cart_router.py`, `orders_router.py`, `chat_router.py`, `support_router.py`
- Key files: Each router file uses `APIRouter` and is included in `main.py`

**`demo-store/app/web/`:**
- Purpose: Frontend assets for traditional storefront
- Contains: Jinja2 `.html` templates (sign-up, login, product list, product detail, cart, checkout, orders, support) or static React build output
- Key files: `templates/base.html`, `templates/products.html`, `templates/cart.html`, `templates/checkout.html`

**`demo-store/app/chat/`:**
- Purpose: Chat UI page and frontend interaction layer
- Contains: Chat page template, JavaScript for transcript display and message submission
- Key files: `templates/chat.html`

**`demo-store/app/lib/auth/`:**
- Purpose: Authentication and identity business logic
- Contains: Signup handler, login handler, password reset, session token creation/validation, in-memory user store
- Key files: `auth.py` or `service.py`, `models.py` (User dataclass/Pydantic model), `store.py` (module-level `users: dict[str, User]`)

**`demo-store/app/lib/catalog/`:**
- Purpose: Product catalog — search and detail retrieval
- Contains: Search function, product detail lookup, in-memory product store
- Key files: `catalog.py` or `service.py`, `models.py` (Product, Variant dataclasses), `store.py` (module-level `products: dict[str, Product]`)

**`demo-store/app/lib/cart/`:**
- Purpose: Shopping cart management
- Contains: Add item, update quantity, remove item, view totals
- Key files: `cart.py` or `service.py`, `models.py` (Cart, CartItem dataclasses), `store.py` (module-level `carts: dict[str, Cart]`)

**`demo-store/app/lib/orders/`:**
- Purpose: Order lifecycle management
- Contains: Create order, check status, cancel order, return order, status transition guards, ownership verification
- Key files: `orders.py` or `service.py`, `models.py` (Order, OrderItem dataclasses with Literal status types), `store.py` (module-level `orders: dict[str, Order]`)

**`demo-store/app/lib/mocks/`:**
- Purpose: Mock external service adapters with configurable probabilistic failure injection
- Contains: Warehouse mock, payment mock; each reads `FAILURE_CONFIG` from `config.py`, rolls `random.random()`, emits observability event
- Key files: `warehouse_mock.py`, `payment_mock.py`
- Warehouse interface: `get_available_quantity`, `reserve_inventory`, `ship_order`, `cancel_order`
- Payment interface: `charge`, `refund`

**`demo-store/app/lib/agent/`:**
- Purpose: LLM orchestration layer — intent interpretation, tool dispatch, clarification, failure recovery
- Contains: Agent runner, tool registry dict, individual tool function implementations, conversation context manager, root instruction parser
- Key files: `agent.py` (runner), `tools.py` (all tool functions), `root_instructions.py` (parser for `[root]:` prefix)
- Tool set: `search_products`, `get_product_details`, `add_to_cart`, `view_cart`, `checkout`, `place_order`, `check_order_status`, `cancel_order`, `return_order`, `reset_password`, `set_failure_mode`

**`demo-store/app/lib/observability/`:**
- Purpose: Langfuse instrumentation helpers
- Contains: Trace/span context managers, event emitter functions for agent/tool/generation steps
- Key files: `tracing.py`, `events.py`
- Telemetry captured: `request_id`, `session_id`, `user_id`, `agent_input`, `agent_output`, `tool_name`, `tool_latency_ms`, `tool_success`, `mock_failure_reason`, `model_metadata`

**`demo-store/app/lib/seed/`:**
- Purpose: Load initial data into all in-memory stores at app startup
- Contains: Product definitions (10–20 items, shoe or pet supplies categories), 2 test users, sample orders (at least 1 paid, 1 shipped, 1 canceled)
- Key files: `seed.py` or `loader.py`

**`demo-store/app/lib/evals/`:**
- Purpose: Evaluation datasets and automated eval runners for agent behavior
- Contains: JSON or YAML files with `input`, `expected_trajectory`, `expected_output`, `tags` fields; positive cases, negative cases, adversarial/red-team cases
- Key files: `positive_cases.json`, `negative_cases.json`, `adversarial_cases.json`, `run_evals.py`

**`demo-store/app/lib/guardrails/`:**
- Purpose: Pre-agent input safety checks
- Contains: Scope enforcement (reject cookie recipes, math problems), prompt injection detection, cross-user access attempt detection
- Key files: `guardrails.py`

## Key File Locations

**Entry Points:**
- `demo-store/main.py`: FastAPI app creation, router registration, startup event for seed
- `demo-store/config.py`: `FAILURE_CONFIG` dict, environment variable loading, dev/demo mode flag

**Configuration:**
- `demo-store/config.py`: All runtime configuration including failure injection probabilities and mode flags
- `demo-store/spec.md`: Project requirements reference

**Core Logic:**
- `demo-store/app/lib/agent/tools.py`: All agent-callable tool functions
- `demo-store/app/lib/agent/agent.py`: Agent runner loop, LLM SDK calls, tool dispatch
- `demo-store/app/lib/mocks/payment_mock.py`: Payment mock with failure injection
- `demo-store/app/lib/mocks/warehouse_mock.py`: Warehouse mock with failure injection
- `demo-store/app/lib/seed/seed.py`: Startup data population

**Testing:**
- Tests live adjacent to source or in a top-level `tests/` directory
- Playwright browser automation tests: `tests/e2e/`
- Pytest unit/integration tests: `tests/unit/`, `tests/integration/`
- Eval datasets: `demo-store/app/lib/evals/`

## Naming Conventions

**Files:**
- `snake_case.py` for all Python source files (e.g., `warehouse_mock.py`, `auth_router.py`, `seed.py`)
- `models.py` for dataclass/Pydantic model definitions within each lib submodule
- `store.py` for in-memory state dicts within each lib submodule
- `service.py` or module-named file (e.g., `auth.py`, `cart.py`) for business logic functions

**Directories:**
- All lowercase, no hyphens within `app/lib/` (e.g., `auth`, `catalog`, `guardrails`)
- Top-level project directory uses hyphen: `demo-store/`

**Python Identifiers:**
- Functions and variables: `snake_case`
- Classes and dataclasses: `PascalCase` (e.g., `User`, `Order`, `CartItem`)
- Constants and config dicts: `UPPER_SNAKE_CASE` (e.g., `FAILURE_CONFIG`)
- Type aliases: `PascalCase`

**Data Models:**
- Pydantic `BaseModel` or `@dataclass` — status fields use `Literal` type constraints
- Example: `order_status: Literal["placed", "paid", "processing", "shipped", "canceled", "returned"]`

## Where to Add New Code

**New API Endpoint:**
- Add router to `demo-store/app/api/` (e.g., `recommendations_router.py`)
- Register router in `demo-store/main.py` with `app.include_router(...)`

**New Domain Module:**
- Create subdirectory under `demo-store/app/lib/` (lowercase)
- Add `models.py`, `store.py` (if state needed), and a service file
- Import service functions into the relevant API router

**New Agent Tool:**
- Add function to `demo-store/app/lib/agent/tools.py`
- Register in agent tool registry in `demo-store/app/lib/agent/agent.py`
- Add positive and negative eval cases to `demo-store/app/lib/evals/`

**New Mock Failure Mode:**
- Add key/probability pair to `FAILURE_CONFIG` in `demo-store/config.py`
- Add failure roll logic inside the relevant mock function in `demo-store/app/lib/mocks/`
- Emit observability event with failure reason

**New Eval Case:**
- Add JSON object with `input`, `expected_trajectory`, `expected_output`, `tags` to appropriate file in `demo-store/app/lib/evals/`

**New Web Page:**
- Add Jinja2 template to `demo-store/app/web/` (or React component if using SPA)
- Add route handler to the relevant API router in `demo-store/app/api/`

**Shared Utilities:**
- Place in the most relevant lib submodule; if truly cross-cutting, create `demo-store/app/lib/utils.py`

## Special Directories

**`.planning/`:**
- Purpose: GSD planning documents and codebase maps
- Generated: By GSD commands (`/gsd-map-codebase`, `/gsd-plan-phase`)
- Committed: Yes (planning artifacts are version controlled)

**`demo-store/app/lib/evals/`:**
- Purpose: Eval datasets for automated agent quality testing
- Generated: Partially hand-authored, partially synthetic (via `deepeval` or `promptfoo`)
- Committed: Yes

---

*Structure analysis: 2026-04-18*
