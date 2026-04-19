# Requirements — ShoeStore AI Demo

**Project:** ShoeStore AI Demo
**Milestone:** v1
**Date:** 2026-04-18
**Status:** Approved

---

## v1 Requirements

### Authentication (AUTH)

- [ ] **AUTH-01**: User can create an account with email and password
- [ ] **AUTH-02**: User can log in with email and password and remain authenticated across requests (JWT via PyJWT)
- [ ] **AUTH-03**: User can reset their password via a reset flow
- [ ] **AUTH-04**: Auth session is shared — web UI and chatbot both recognize the same authenticated user

### Catalog (CAT)

- [ ] **CAT-01**: App seeds 10–20 shoe products on startup (running, hiking, slides, sandals, socks) with name, description, unit price, inventory, category
- [ ] **CAT-02**: User can search for products by keyword via web UI and chatbot
- [ ] **CAT-03**: User can view product detail page (web) or ask for details (chat)
- [ ] **CAT-04**: Products support size/color variants

### Cart (CART)

- [ ] **CART-01**: User can add a product (with variant) to their cart
- [ ] **CART-02**: User can update item quantity in cart
- [ ] **CART-03**: User can remove an item from cart
- [ ] **CART-04**: User can view cart with line items and totals

### Checkout (CHK)

- [ ] **CHK-01**: User can check out with Credit Card (mock payment adapter)
- [ ] **CHK-02**: User can check out with PayPal (mock payment adapter)
- [ ] **CHK-03**: User can check out with Apple Pay (mock payment adapter)
- [ ] **CHK-04**: User receives order confirmation after successful checkout

### Orders (ORD)

- [ ] **ORD-01**: User can check the status of an order (placed → paid → processing → shipped → canceled)
- [ ] **ORD-02**: User can cancel an order; warehouse cancel mock runs; refund mock runs if payment captured
- [ ] **ORD-03**: User can request a return on any paid/processing/shipped order

### Chatbot (CHAT)

- [ ] **CHAT-01**: Chatbot (Claude via Anthropic SDK) handles all shopping flows conversationally: search, add to cart, view cart, checkout, place order
- [ ] **CHAT-02**: Chatbot handles all support flows: order status, cancel order, return order, password reset
- [ ] **CHAT-03**: Chatbot asks clarification questions when required info is missing (e.g. "Cancel my order" → asks which order)
- [ ] **CHAT-04**: Chatbot enforces scope — rejects off-topic requests (recipes, math), prompt injection attempts, and cross-user data access
- [ ] **CHAT-05**: Chatbot recovers gracefully from mock failures — surfaces what failed and suggests next steps

### Mock Adapters & Demo Control (MOCK)

- [ ] **MOCK-01**: Warehouse mock adapter supports configurable global failure injection: `out_of_stock` and `failed_to_cancel_order` probabilities
- [ ] **MOCK-02**: Payment mock adapter supports configurable global failure injection: `failed_to_charge_{method}` and `failed_to_refund_{method}` probabilities
- [ ] **MOCK-03**: `[root]:` instruction token (demo mode only) updates live failure config for the current run; every invocation is logged; not accessible to end users

### Seed Data (SEED)

- [ ] **SEED-01**: App seeds at least 2 test users on startup
- [ ] **SEED-02**: App seeds at least 1 prior paid order, 1 shipped order, and 1 canceled order for test users

### Evaluation & Testing (TEST)

- [ ] **TEST-01**: Eval dataset exists for positive cases (successful search, cart, checkout, status, cancel)
- [ ] **TEST-02**: Eval dataset exists for negative cases (out of stock, payment failure, wrong user, bad order ID)
- [ ] **TEST-03**: Eval dataset exists for adversarial cases (prompt injection, off-topic, typos, sarcasm, all-caps)
- [ ] **TEST-04**: Eval dataset format: `{input, expected_trajectory, expected_output, tags}`

---

## v2 Requirements (Deferred)

- Langfuse tracing (agent/tool/generation traces) — deferred from v1; add in a follow-on phase
- Playwright E2E browser automation — deferred; eval datasets cover the core testing need for now
- Admin debug panel for toggling failures without root prompt syntax
- Transcript replay viewer
- Product recommendations
- Downloadable order receipts
- Memory of last viewed items in session

---

## Out of Scope

- Production-grade database — in-memory only; by design
- Real payment or warehouse integration — mocked only
- OAuth / social login — email/password only
- Per-session failure config — global failure rates only (reset on restart)
- Multi-tenant complexity — single-tenant demo only
- Streaming token output in chatbot — conflicts with tool-use loop; return complete responses
- LangChain / LlamaIndex — direct Anthropic SDK only

---

## Traceability

| REQ-ID | Phase |
|--------|-------|
| AUTH-01 – AUTH-04 | TBD |
| CAT-01 – CAT-04 | TBD |
| CART-01 – CART-04 | TBD |
| CHK-01 – CHK-04 | TBD |
| ORD-01 – ORD-03 | TBD |
| CHAT-01 – CHAT-05 | TBD |
| MOCK-01 – MOCK-03 | TBD |
| SEED-01 – SEED-02 | TBD |
| TEST-01 – TEST-04 | TBD |

*Traceability updated by roadmapper.*
