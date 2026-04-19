# Architecture

**Analysis Date:** 2026-04-18
**Status:** Planned — no source code implemented yet. This document reflects the intended architecture as prescribed in the project spec (`/Users/matthew/Downloads/spec_python.md`).

## Pattern Overview

**Overall:** Monolithic FastAPI backend with modular internal library structure

**Key Characteristics:**
- Single FastAPI process serves both web UI and chat UI from the same application instance
- All state held in-memory using Python dicts and lists — no database required
- LLM agent layer dispatches to typed tool functions that call internal domain modules
- Mock adapters for warehouse and payment support configurable probabilistic failure injection
- Root instruction token mechanism allows demo operators to mutate failure config at runtime via chat input
- Langfuse SDK instruments every agent invocation, tool call, and LLM generation

## Layers

**API Layer:**
- Purpose: HTTP routing and request/response handling
- Location: `demo-store/app/api/`
- Contains: FastAPI routers organized by domain (auth, catalog, cart, orders, support, chat)
- Depends on: lib modules for business logic
- Used by: Web UI frontend, Chat UI frontend, external API consumers

**Web UI Layer:**
- Purpose: Jinja2 templates or static React build for traditional storefront
- Location: `demo-store/app/web/`
- Contains: HTML templates, static assets, page-level views
- Depends on: API layer (for SPA) or lib modules directly (for server-side rendering)
- Used by: End customer browsing the store

**Chat UI Layer:**
- Purpose: Conversational chat interface served from a dedicated route
- Location: `demo-store/app/chat/`
- Contains: Chat page template, frontend JS for transcript/input, websocket or polling client
- Depends on: API chat endpoint → agent layer
- Used by: End customer interacting via chatbot

**Domain Library Layer:**
- Purpose: All business logic, isolated from HTTP transport
- Location: `demo-store/app/lib/`
- Contains: Submodules — auth, catalog, cart, orders, mocks, agent, observability, seed, evals, guardrails
- Depends on: In-memory state stores (Python module-level dicts/lists), `config.py`
- Used by: API routers, agent tool functions

**Agent Layer:**
- Purpose: LLM orchestration — intent interpretation, tool dispatch, clarification loops, failure recovery
- Location: `demo-store/app/lib/agent/`
- Contains: Agent runner, tool registry, tool function implementations, conversation context manager
- Depends on: LLM SDK (Anthropic/OpenAI), all domain lib modules, observability, guardrails
- Used by: Chat API router

**Mock Adapter Layer:**
- Purpose: Simulate warehouse and payment external services with probabilistic failure injection
- Location: `demo-store/app/lib/mocks/`
- Contains: `warehouse_mock.py`, `payment_mock.py`, failure config reader
- Depends on: `FAILURE_CONFIG` dict from `config.py`, observability emitter
- Used by: Orders module (checkout, cancellation, return flows)

**Observability Layer:**
- Purpose: Langfuse instrumentation helpers wrapping agent, tool, and generation events
- Location: `demo-store/app/lib/observability/`
- Contains: Trace/span helpers, event emitters, session and request ID propagation utilities
- Depends on: `langfuse` Python SDK
- Used by: Agent layer, mock adapters, API routers

**Seed Layer:**
- Purpose: Populate in-memory stores with products, users, and sample orders at startup
- Location: `demo-store/app/lib/seed/`
- Contains: `seed.py` or `loader.py` with 10–20 product definitions and 2 test user records
- Depends on: Domain lib modules (catalog, orders, auth in-memory stores)
- Used by: `main.py` startup event

**Evals Layer:**
- Purpose: Evaluation datasets and test runners for agent behavior validation
- Location: `demo-store/app/lib/evals/`
- Contains: JSON/YAML eval datasets (`input`, `expected_trajectory`, `expected_output`, `tags`), eval runner scripts
- Depends on: `pytest`, `deepeval` or `promptfoo`, agent layer
- Used by: CI pipelines and demo operators

**Guardrails Layer:**
- Purpose: Prompt injection detection and scope enforcement before agent processes user input
- Location: `demo-store/app/lib/guardrails/`
- Contains: Input classifier, scope enforcement rules, injection pattern matchers
- Depends on: LLM or rule-based classifiers
- Used by: Agent layer as a pre-processing step before tool dispatch

## Data Flow

**Web Purchase Flow:**

1. User submits checkout form → POST to auth-protected API route in `demo-store/app/api/`
2. API router calls `cart` lib to retrieve items
3. `payment_mock.charge()` in `demo-store/app/lib/mocks/payment_mock.py` runs — inspects `FAILURE_CONFIG`, rolls `random.random()`, returns success or structured failure dict
4. On payment success, `warehouse_mock.reserve_inventory()` in `demo-store/app/lib/mocks/warehouse_mock.py` runs with same failure injection logic
5. `orders` lib creates `Order` record in in-memory dict, sets status to `placed` → `paid`
6. Observability layer emits tool call events to Langfuse with latency, outcome, and mock failure reason
7. API router returns confirmation or structured error to web UI

**Chat Purchase Flow:**

1. User sends message → POST to chat API route
2. Guardrails layer in `demo-store/app/lib/guardrails/` inspects input for injection attempts and out-of-scope requests
3. Root instruction parser checks for `[root]:` prefix — if present and dev mode enabled, mutates `FAILURE_CONFIG` in `config.py` and logs instruction
4. Agent runner in `demo-store/app/lib/agent/` sends conversation context + system prompt to LLM SDK
5. LLM returns tool call decision (e.g., `search_products`, `add_to_cart`, `checkout`)
6. Agent dispatches to matching tool function
7. Tool functions call domain lib modules (catalog, cart, orders, mocks)
8. Observability layer wraps each tool call with Langfuse span (latency, success/failure, mock failure reason)
9. Agent receives tool result, sends follow-up to LLM for user-facing response
10. Final agent response returned to chat UI

**Order Cancellation Flow:**

1. Request arrives via web form or chatbot tool call (`cancel_order`)
2. `orders` lib verifies order ownership (user_id match)
3. `orders` lib verifies order status is cancelable (not already shipped or canceled)
4. `warehouse_mock.cancel_order()` runs with probabilistic failure injection
5. If payment was captured, `payment_mock.refund()` runs
6. Order `order_status` updated to `canceled` in-memory
7. Observability event emitted with outcome

**State Management:**
- All state lives in module-level Python dicts/lists initialized at import time and populated by `seed.py` at startup
- No persistence between process restarts — each run starts fresh
- Session state for web UI managed via signed cookies (`itsdangerous`) or JWT (`python-jose`)
- Conversation context for chat agent held in-memory per session ID

## Key Abstractions

**In-Memory Stores:**
- Purpose: Centralized mutable state replacing a database
- Location: Within each lib module (e.g., `demo-store/app/lib/catalog/store.py`, `demo-store/app/lib/orders/store.py`)
- Pattern: Module-level dicts keyed by entity ID — `users: dict[str, User]`, `products: dict[str, Product]`, `orders: dict[str, Order]`, `carts: dict[str, Cart]`

**Data Models:**
- Purpose: Typed representations of domain entities with status constraints
- Location: Each lib submodule (e.g., `demo-store/app/lib/orders/models.py`)
- Pattern: Pydantic `BaseModel` or `@dataclass`; `Order.order_status` typed as `Literal["placed", "paid", "processing", "shipped", "canceled", "returned"]`; `Order.payment_status` typed as `Literal["pending", "paid", "failed", "refunded"]`

**Agent Tool Registry:**
- Purpose: Maps LLM tool names to Python callable functions
- Location: `demo-store/app/lib/agent/`
- Pattern: Dict of `{tool_name: callable}` or decorator-based registration; tool set includes `search_products`, `get_product_details`, `add_to_cart`, `view_cart`, `checkout`, `place_order`, `check_order_status`, `cancel_order`, `return_order`, `reset_password`, `set_failure_mode`

**FAILURE_CONFIG:**
- Purpose: Configurable failure probability dict for mock adapters, mutable at runtime
- Location: `demo-store/config.py`
- Pattern:
  ```python
  FAILURE_CONFIG = {
      "warehouse": {"out_of_stock": 0.10, "failed_to_cancel_order": 0.20},
      "payment": {"failed_to_charge_credit_card": 0.03, "failed_to_refund_paypal": 0.08},
  }
  ```

**Mock Failure Response Shape:**
- Purpose: Structured error dicts returned by mock adapters on injected failure
- Pattern:
  ```python
  {"success": False, "code": "FAILED_TO_CHARGE_CREDIT_CARD", "message": "...", "retryable": True}
  ```

**Root Instruction Parser:**
- Purpose: Parses `[root]: ...` prefix from chat input and updates `FAILURE_CONFIG`
- Location: `demo-store/app/lib/agent/` (pre-processing step before LLM call)
- Pattern: Regex match on input; active only in dev/demo mode; every invocation logged to observability; examples: `[root]: make payment fail 100% if payment type is credit card`, `[root]: disable all failures`

**Guardrails Check:**
- Purpose: Reject out-of-scope or adversarial inputs before LLM sees them
- Location: `demo-store/app/lib/guardrails/`
- Pattern: Pre-agent filter that checks for injection patterns, unrelated task requests (cookie recipes, math), and cross-user data access attempts; returns immediate rejection without invoking agent

## Entry Points

**Application Entry Point:**
- Location: `demo-store/main.py`
- Triggers: `uvicorn main:app` or `fastapi dev main.py`
- Responsibilities: Creates FastAPI app instance, registers all API routers from `app/api/`, fires `@app.on_event("startup")` to run seed loader

**Chat Endpoint:**
- Location: `demo-store/app/api/` (chat router)
- Triggers: POST from Chat UI at `/chat` route
- Responsibilities: Passes message through guardrails → root instruction parser → agent runner → returns agent response

**Seed Startup:**
- Location: `demo-store/app/lib/seed/`
- Triggers: FastAPI startup event registered in `main.py`
- Responsibilities: Populates all in-memory stores with 10–20 products, 2 test users, and at least 3 sample orders (paid, shipped, canceled)

## Error Handling

**Strategy:** Structured failure dicts from mock adapters propagate upward; agent layer handles `success: False` results and uses LLM to formulate recovery suggestions for the user

**Patterns:**
- Mock adapters return `{"success": False, "code": "...", "message": "...", "retryable": True/False}` on injected failure
- Agent layer detects failure in tool result and asks LLM to formulate recovery response (e.g., suggest alternative payment method)
- API routers return appropriate HTTP status codes (400, 422, 500) with JSON error bodies for web clients
- Guardrail violations return immediate rejection response without invoking agent or LLM

## Cross-Cutting Concerns

**Logging:** Every mock failure, root instruction, and guardrail rejection emitted via `demo-store/app/lib/observability/` to Langfuse with structured metadata: `request_id`, `session_id`, `user_id`, `tool_name`, `latency_ms`, `success`, `failure_reason`

**Validation:** Pydantic models on API request bodies provide automatic validation and OpenAPI schema generation; domain lib functions enforce business rules (order ownership check, status transition guards)

**Authentication:** `passlib` for password hashing at signup/login; `itsdangerous` signed cookies or `python-jose` JWT for session tokens; user identity propagated from session/token into agent context for authenticated tool calls; prompt-injection escalation from customer to root level is explicitly blocked

---

*Architecture analysis: 2026-04-18*
