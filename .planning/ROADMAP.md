# Roadmap — ShoeStore AI Demo

**Project:** ShoeStore AI Demo
**Milestone:** v1
**Granularity:** Standard (5 phases)
**Requirements mapped:** 33 / 33

---

## Phases

- [x] **Phase 1: Domain Foundation** - Scaffold the project, define all domain models, wire in-memory stores, and seed reference data — no HTTP, no LLM
- [x] **Phase 2: Auth & Core Services** - Shared JWT auth layer plus cart and order service logic verified by unit tests
- [ ] **Phase 3: Web UI & REST API** - Mock adapters with failure injection, REST routers, and all Jinja2 web pages deliver the complete web shopping experience
- [ ] **Phase 4: Claude Agent** - Tool registry, agentic loop, guardrails, and chat endpoint make every shopping and support flow available conversationally
- [ ] **Phase 5: Evals & Demo Control** - Root-token live config, eval datasets for positive/negative/adversarial cases, and the complete testable demo harness

---

## Phase Details

### Phase 1: Domain Foundation
**Goal**: The project skeleton exists and all domain data can be created, stored, and retrieved in pure Python — no HTTP server, no LLM calls required
**Depends on**: Nothing
**Requirements**: CAT-01, CAT-04, SEED-01, SEED-02
**Success Criteria** (what must be TRUE):
  1. Running the app seeds 10-20 shoe products covering running, hiking, slides, sandals, and socks categories with name, description, price, inventory, and at least one size/color variant each
  2. Running the app seeds at least 2 test users and 3 prior orders (one paid, one shipped, one canceled) accessible from the in-memory store
  3. A Python unit test can create, read, and list products and orders without starting an HTTP server
  4. The project directory structure, pyproject.toml (or requirements.txt), and FastAPI skeleton (no routes yet) are in place and `uvicorn` starts without errors
**Plans**: 4 plans

Plans:
- [x] 01-01-PLAN.md — Project scaffold: pyproject.toml (uv), main.py FastAPI skeleton, config.py, app/ and tests/ directory trees with __init__.py markers
- [x] 01-02-PLAN.md — Domain models and in-memory stores: User, Product, Variant, Cart, CartItem, Order, OrderItem dataclasses + users_db/products_db/carts_db/orders_db + unit tests for models and stores
- [x] 01-03-PLAN.md — Seed data and lifespan wiring: seed.py with 2 bcrypt-hashed users, 15 products (3 per category), 3 prior orders; main.py lifespan calls seed(); test_seed.py covers CAT-01, CAT-04, SEED-01, SEED-02
- [x] 01-04-PLAN.md — Phase 1 gate: pre-flight checks (full pytest suite, ruff), human-verify uvicorn startup, and phase summary for /gsd-verify-work

### Phase 2: Auth & Core Services
**Goal**: Users can register, log in, and use a JWT that both the web UI and chat endpoint will recognize; cart and order service logic is fully exercised by unit tests
**Depends on**: Phase 1
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, CART-01, CART-02, CART-03, CART-04
**Success Criteria** (what must be TRUE):
  1. A new user can register with email and password; the password is stored as a bcrypt hash, never plaintext
  2. A registered user can log in and receive a JWT that remains valid across multiple requests (web and chat use the same token)
  3. A user can initiate a password reset flow and set a new password
  4. A unit test can add a product variant to a cart, update its quantity, remove it, and verify the cart total — no HTTP required
  5. The cart rejects adding a product that has zero inventory
**Plans**: 3 plans

Plans:
- [x] 02-01-PLAN.md — JWT config constants + auth store extension (reset_tokens_db) + auth_service.py (register, login, verify_token, reset_request, reset_confirm)
- [x] 02-02-PLAN.md — cart_service.py (add/update/remove/total/clear with asyncio.Lock) + order_service.py (place/cancel/return/get/list with ownership enforcement)
- [x] 02-03-PLAN.md — Unit tests: test_auth_service.py, test_cart_service.py, test_order_service.py covering all D-14 scenarios with D-15 store isolation

### Phase 3: Web UI & REST API
**Goal**: A browser user can complete the full purchase lifecycle — browse, search, add to cart, check out, and manage orders — and mock adapters make failure scenarios injectable for demos
**Depends on**: Phase 2
**Requirements**: CAT-02, CAT-03, CHK-01, CHK-02, CHK-03, CHK-04, ORD-01, ORD-02, ORD-03, MOCK-01, MOCK-02
**Success Criteria** (what must be TRUE):
  1. User can search for shoes by keyword and see a results page; clicking a result shows a product detail page with variants
  2. User can check out using Credit Card, PayPal, or Apple Pay and receive an order confirmation page after successful payment
  3. User can view order status (placed → paid → processing → shipped → canceled) on an orders page
  4. User can cancel an eligible order; a warehouse cancel mock runs and a payment refund mock runs if payment was captured
  5. User can request a return on any paid, processing, or shipped order
  6. Setting the warehouse `out_of_stock` failure probability to 1.0 causes checkout to fail with a clear error; setting payment failure probability to 1.0 causes the charge to fail with a clear error
**Plans**: 6 plans

Plans:
- [x] 03-01-PLAN.md — Wave 0 test stubs: integration conftest + all 7 test files (unit + integration) with xfail markers covering CAT-02, CAT-03, CHK-01–04, ORD-01–03, MOCK-01–02
- [x] 03-02-PLAN.md — Foundation modules: config.py FAILURE_CONFIG fix (6 payment keys), warehouse_mock.py, payment_mock.py, catalog_service.py, auth/dependencies.py
- [x] 03-03-PLAN.md — Auth layer: main.py SessionMiddleware + router wiring, auth_router.py (6 endpoints), base.html + 4 auth templates
- [x] 03-04-PLAN.md — Catalog UI: catalog_router.py (GET /products, GET /products/{id}, POST /cart/add), products/list.html + products/detail.html
- [ ] 03-05-PLAN.md — Cart & checkout: cart_router.py (GET /cart, POST /cart/update, /cart/remove, POST /checkout), cart.html + orders/confirmation.html
- [ ] 03-06-PLAN.md — Orders UI: orders_router.py (GET /orders, GET /orders/{id}, GET /orders/{id}/confirmation, POST /cancel, POST /return), orders/list.html + orders/detail.html

### Phase 4: Claude Agent
**Goal**: Every shopping and support action available on the web is also available conversationally through a Claude-powered chat endpoint, with guardrails that prevent scope violations and graceful handling of mock failures
**Depends on**: Phase 3
**Requirements**: CHAT-01, CHAT-02, CHAT-03, CHAT-04, CHAT-05
**Success Criteria** (what must be TRUE):
  1. A logged-in user can search for shoes, add to cart, view cart, confirm checkout, and place an order entirely through the chat interface
  2. A logged-in user can ask for order status, cancel an order, or request a return through chat; the agent verifies ownership before acting
  3. When required information is missing (e.g. "cancel my order" with multiple orders), the agent asks a clarifying question rather than failing or guessing
  4. Requests for off-topic content (recipes, math), prompt injection attempts, and requests to access another user's data are rejected with a polite scope refusal — no stack trace, no raw error
  5. When a mock payment or warehouse failure occurs mid-conversation, the agent surfaces what failed and suggests a concrete next step (retry, try different payment method, contact support)
**Plans**: TBD
**UI hint**: yes

### Phase 5: Evals & Demo Control
**Goal**: The root token lets a demo operator reconfigure failure rates live without restarting; eval datasets cover positive, negative, and adversarial agent behaviors and are runnable
**Depends on**: Phase 4
**Requirements**: MOCK-03, TEST-01, TEST-02, TEST-03, TEST-04
**Success Criteria** (what must be TRUE):
  1. Prefixing a chat message with `[root]:` in demo mode updates the live failure config for the current run and is logged; the prefix is stripped before the message reaches the LLM; the config resets on process restart
  2. A positive eval dataset exists with cases for successful search, add-to-cart, checkout, order status, and cancel — each case has `input`, `expected_trajectory`, `expected_output`, and `tags` fields
  3. A negative eval dataset exists with cases for out-of-stock, payment failure, wrong user, and bad order ID scenarios
  4. An adversarial eval dataset exists with cases for prompt injection, off-topic requests, typos, sarcasm, and all-caps input
  5. All eval datasets can be loaded and a smoke-run of at least one case per dataset completes without an uncaught exception
**Plans**: TBD

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Domain Foundation | 4/4 | Complete | 2026-04-19 |
| 2. Auth & Core Services | 3/3 | Complete | 2026-04-19 |
| 3. Web UI & REST API | 4/6 | In Progress | - |
| 4. Claude Agent | 0/? | Not started | - |
| 5. Evals & Demo Control | 0/? | Not started | - |

---

*Last updated: 2026-04-19 by planner*
