# Phase 2: Auth & Core Services - Context

**Gathered:** 2026-04-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement the JWT auth layer (register, login, password reset) and cart/order service logic — all verified by unit tests with no HTTP server required. No routes yet (Phase 3). Phase is complete when a unit test can register a user, obtain a JWT, add items to cart, place and cancel an order in pure Python.

</domain>

<decisions>
## Implementation Decisions

### JWT Token Design
- **D-01:** JWT payload contains `user_id` only (UUID string). Service layer resolves the full User from `users_db` when needed. No email or role in token — avoids stale-data risk.
- **D-02:** Access token expiry: 30 minutes. No refresh tokens. User re-authenticates on expiry. Demo-appropriate simplicity.
- **D-03:** Use PyJWT (already a project dependency). Never python-jose (CVE-2024-33664).

### Password Reset Flow
- **D-04:** In-memory token store — module-level dict keyed by email, value is `{token: UUID, expires_at: datetime}`. Tokens expire after 15 minutes.
- **D-05:** Two endpoints (to be wired in Phase 3): POST `/auth/reset-request` stores token and returns it in the response body (no email server — demo only). POST `/auth/reset-confirm` accepts `{token, new_password}`, validates, updates hash.
- **D-06:** Reset token store is a plain module-level dict in `app/lib/auth/store.py` alongside `users_db`. Resets on process restart like all other in-memory state.

### Cart Service Rules
- **D-07:** Adding a product with zero inventory → reject with error immediately. Do not defer to checkout. Unit test asserts rejection.
- **D-08:** Adding the same product+variant twice → merge into existing CartItem (increment quantity). No duplicate lines.
- **D-09:** Cart total is computed on-the-fly by summing `item.quantity * item.unit_price` across all CartItems. No stored total field on Cart.
- **D-10:** `asyncio.Lock` on every inventory check+decrement to prevent oversell race (carried forward from Phase 1 decisions).

### Order Service Scope
- **D-11:** Cancel eligibility: `placed` and `paid` statuses only. Orders in `processing`, `shipped`, `canceled`, or `returned` cannot be canceled.
- **D-12:** Return eligibility: `paid`, `processing`, or `shipped` (per CLAUDE.md directive). Service enforces this.
- **D-13:** Cross-user ownership enforced in the service layer — `cancel_order(order_id, user_id)` and `request_return(order_id, user_id)` validate that `order.user_id == user_id` before acting. Cannot be bypassed by a router that forgets to check.

### Testing
- **D-14:** Unit tests cover: register+login+JWT verify, password reset flow end-to-end (request → confirm → login with new password), cart add/update/remove/total, cart inventory rejection, cart merge behavior, order cancel (eligible + ineligible statuses), order return (eligible + ineligible), cross-user rejection.
- **D-15:** Same autouse fixture pattern as Phase 1 — clear all stores before/after each test.

### Claude's Discretion
- Exact JWT secret key source (env var `JWT_SECRET` with a dev default in config.py, or hardcoded dev string — Claude decides)
- Whether `auth_service.py`, `cart_service.py`, `order_service.py` are separate files or methods on a service class
- Error response shape (follow the established `{"success": bool, "code": str, "message": str, "retryable": bool}` pattern from CONVENTIONS.md)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Spec
- `/Users/matthew/Downloads/spec_python.md` — canonical requirements source; Phase 2 covers AUTH-01–04, CART-01–04

### Planning
- `.planning/REQUIREMENTS.md` — AUTH-01, AUTH-02, AUTH-03, AUTH-04, CART-01, CART-02, CART-03, CART-04
- `.planning/ROADMAP.md` — Phase 2 success criteria
- `.planning/codebase/CONVENTIONS.md` — model shapes, error response pattern, import rules
- `.planning/codebase/STRUCTURE.md` — where service files live

### Phase 1 Artifacts (patterns to follow)
- `.planning/phases/01-domain-foundation/01-CONTEXT.md` — established decisions (dataclasses, store pattern, test isolation)
- `app/lib/auth/models.py` — User dataclass shape
- `app/lib/auth/store.py` — store pattern to follow
- `app/lib/cart/models.py` — Cart and CartItem shapes
- `app/lib/orders/models.py` — Order and OrderItem shapes, status Literals
- `tests/unit/test_stores.py` — test isolation fixture pattern to replicate

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/lib/auth/models.py` — User dataclass (id, email, password_hash, created_at)
- `app/lib/auth/store.py` — `users_db: dict[str, User] = {}` — extend with reset token store
- `app/lib/cart/models.py` — Cart and CartItem dataclasses
- `app/lib/cart/store.py` — `carts_db: dict[str, Cart] = {}` — service writes here
- `app/lib/orders/models.py` — Order and OrderItem with full status Literals
- `app/lib/orders/store.py` — `orders_db: dict[str, Order] = {}` — service writes here
- `app/lib/seed/seed.py` — seeded alice/bob users and 3 prior orders available for integration tests

### Established Patterns
- Plain `@dataclass` for domain objects, Pydantic only for FastAPI schemas (Phase 3+)
- Store pattern: module-level dict, empty at import, populated by seed() or service calls
- Test isolation: autouse fixture clears all stores before/after each test
- `field(default_factory=list)` mandatory for list fields on dataclasses
- `str | None` union syntax, built-in `list[]`/`dict[]` generics — no `Optional[]`

### Integration Points
- `app/lib/auth/` → new `auth_service.py` (register, login, verify_token, reset_request, reset_confirm)
- `app/lib/cart/` → new `cart_service.py` (add_item, update_quantity, remove_item, get_cart, clear_cart)
- `app/lib/orders/` → new `order_service.py` (place_order, cancel_order, request_return, get_order, list_orders)
- `config.py` → may add JWT_SECRET constant
- `tests/unit/` → new test files for auth, cart, orders services

</code_context>

<specifics>
## Specific Ideas

- The password reset token is returned directly in the API response (no email) — this is intentional for demo purposes. A comment in the code should make this explicit.
- alice@example.com and bob@example.com are the canonical test users — tests should reference these by importing from seed or using known credentials.
- The `asyncio.Lock` on cart/order mutations is critical for the inventory oversell pitfall identified in Phase 1 research.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-auth-core-services*
*Context gathered: 2026-04-19*
