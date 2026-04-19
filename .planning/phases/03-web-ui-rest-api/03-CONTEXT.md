# Phase 3: Web UI & REST API - Context

**Gathered:** 2026-04-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Build warehouse and payment mock adapters with configurable failure injection, wire all REST API routers (auth, catalog, cart, checkout, orders), and deliver complete Jinja2 web pages for the full browser-based purchase lifecycle — product browse/search, add to cart, single-page checkout, order management (view, cancel, return). Phase is complete when a browser user can complete the full purchase flow and failure injection scenarios are demonstrable.

</domain>

<decisions>
## Implementation Decisions

### Auth Web Session
- **D-01:** JWT in httpOnly cookie. Login/register endpoints issue JWT via `Set-Cookie` (httpOnly, SameSite=Lax). FastAPI `Depends()` reads cookie for all web and API routes. Single auth mechanism for both web pages and REST API. itsdangerous stays in pyproject.toml but is not used for session management.
- **D-02:** Auth pages in scope: login, register, password reset (two pages: request-reset and reset-confirm), logout endpoint.
- **D-03:** Unauthenticated access to protected pages (cart, checkout, orders) redirects to `/login?next=<original_url>`. After login, redirect back to the original URL.
- **D-04:** Password reset token is returned directly in the API response body (no email server) — this is intentional for demo purposes; code comment makes it explicit.

### UI Styling
- **D-05:** Bootstrap 5 loaded from CDN via `<link>` tag in `base.html`. No build step required.
- **D-06:** Functional + clean polish level: Bootstrap defaults with minimal customization. Navbar, product cards, clean forms. Professional without extra effort. No custom brand colors or logo in Phase 3.

### Checkout Flow
- **D-07:** Single-page checkout: cart page has payment method selector (radio buttons: Credit Card / PayPal / Apple Pay) and a Checkout button. One POST to checkout endpoint places the order. No multi-step wizard.
- **D-08:** Order confirmation page shows: order ID, list of items, total amount, payment method used, current order status, and a link to the orders page.
- **D-09:** Cancel and Return actions live on the individual order detail page (`/orders/{id}`). Buttons are conditionally rendered based on order status eligibility (cancel: placed/paid; return: paid/processing/shipped).

### Catalog Search
- **D-10:** Keyword search uses case-insensitive substring match across product name, description, and category. Returns all products where any of these fields contains the search term.
- **D-11:** Product list page supports category filter tabs/links: All / Running / Hiking / Slides / Sandals / Socks. Search and category filter can combine (keyword search within a selected category).
- **D-12:** Product detail page shows name, description, price, inventory, category, and a variant selector (size/color dropdowns). Add to Cart is a POST form. On success, redirects to cart page.

### Mock Adapters
- **D-13:** Warehouse mock (`app/lib/mocks/warehouse_mock.py`) implements: `get_available_quantity`, `reserve_inventory`, `ship_order`, `cancel_order`. Reads `FAILURE_CONFIG["warehouse"]` at call time (not import time) to allow live mutation.
- **D-14:** Payment mock (`app/lib/mocks/payment_mock.py`) implements: `charge`, `refund`. Reads `FAILURE_CONFIG["payment"]` at call time. Failure key pattern: `failed_to_charge_{method}`, `failed_to_refund_{method}`.
- **D-15:** Default FAILURE_CONFIG failure probabilities start at 0.0 (no failures by default). Demo operator can raise them via root token (Phase 5) or by manually editing config.py.

### Pages Inventory
- **D-16:** Web pages in scope: home/index redirect to product list, product list (`/products`), product detail (`/products/{id}`), cart (`/cart`), order confirmation (`/orders/{id}/confirmation`), orders list (`/orders`), order detail (`/orders/{id}`), login (`/login`), register (`/register`), password reset request (`/auth/reset-request`), password reset confirm (`/auth/reset-confirm`).

### Claude's Discretion
- Exact Bootstrap component choices (card vs. list-group for products, etc.)
- Navbar links and layout
- Flash message / alert approach for errors (Bootstrap alerts are fine)
- Whether to use Jinja2 `url_for` for static assets or inline CDN links
- Catalog service implementation details (function signatures, module location)
- Whether `catalog_service.py` lives at `app/lib/catalog/catalog_service.py` or `app/lib/catalog/service.py`
- Quantity selector behavior on the product detail page (default qty 1, allow increment)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Spec
- `/Users/matthew/Downloads/spec_python.md` — canonical requirements source; Phase 3 covers CAT-02, CAT-03, CHK-01–04, ORD-01–03, MOCK-01–02

### Planning
- `.planning/REQUIREMENTS.md` — Phase 3 requirements: CAT-02, CAT-03, CHK-01, CHK-02, CHK-03, CHK-04, ORD-01, ORD-02, ORD-03, MOCK-01, MOCK-02
- `.planning/ROADMAP.md` — Phase 3 success criteria (6 items)
- `.planning/codebase/CONVENTIONS.md` — error response shape, mock adapter patterns, route handler pattern, failure injection pattern
- `.planning/codebase/STRUCTURE.md` — where routers, templates, and mocks live

### Phase 1 & 2 Artifacts (patterns to follow)
- `.planning/phases/01-domain-foundation/01-CONTEXT.md` — packaging, store pattern, test isolation
- `.planning/phases/02-auth-core-services/02-CONTEXT.md` — JWT design (D-01–D-03), cart service rules (D-07–D-10), order eligibility rules (D-11–D-13)
- `app/lib/auth/auth_service.py` — register, login, verify_token, reset_request, reset_confirm (already implemented)
- `app/lib/cart/cart_service.py` — add/update/remove/total/clear (already implemented)
- `app/lib/orders/order_service.py` — place/cancel/return/get/list with ownership (already implemented)
- `app/lib/catalog/models.py` — Product and Variant dataclasses
- `app/lib/catalog/store.py` — products_db dict

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/lib/auth/auth_service.py` — all auth business logic is done; Phase 3 adds routers + templates only
- `app/lib/cart/cart_service.py` — cart logic done; Phase 3 wires it to HTTP endpoints and templates
- `app/lib/orders/order_service.py` — order logic done; Phase 3 wires it to HTTP endpoints and templates
- `app/lib/catalog/models.py` — Product and Variant dataclasses ready
- `app/lib/catalog/store.py` — products_db populated by seed() at startup
- `app/lib/seed/seed.py` — 15 products seeded (3 per category), alice@example.com and bob@example.com users

### Established Patterns
- Route handlers are thin: `result = service_fn(...); if not result["success"]: raise HTTPException(...)`
- Error shape: `{"success": bool, "code": str, "message": str, "retryable": bool}`
- Pydantic `BaseModel` for request/response schemas; plain `@dataclass` for domain objects
- `asyncio.Lock` already wired in cart and order services — no additional locking needed in routers
- `from config import FAILURE_CONFIG` read at call time in mock adapters

### Integration Points
- `main.py` — needs `app.include_router(...)` for each new router
- `app/api/` — new router files: `auth_router.py`, `catalog_router.py`, `cart_router.py`, `orders_router.py`
- `app/web/` — new Jinja2 templates: `base.html` + per-page templates
- `app/lib/catalog/` — new `catalog_service.py` (search, get_product)
- `app/lib/mocks/` — new `warehouse_mock.py`, `payment_mock.py`
- `config.py` — FAILURE_CONFIG already scaffolded; verify it has warehouse and payment keys

</code_context>

<specifics>
## Specific Ideas

- The JWT cookie dependency should be a single reusable `Depends(get_current_user)` that works for both web page routes (raises redirect on failure) and API routes (raises 401 on failure). Two variants: `get_current_user_web` (redirects) and `get_current_user_api` (401), or a single one with a flag.
- Product cards on the list page should show name, category, price, and an "View Details" link — not an inline Add to Cart (that lives on the detail page with the variant selector).
- The orders list page should show order ID (truncated), status badge (colored by status), total, date, and a "View Details" link.
- alice@example.com / bob@example.com are the canonical test users — login form can hint at these credentials in a demo note.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-web-ui-rest-api*
*Context gathered: 2026-04-19*
