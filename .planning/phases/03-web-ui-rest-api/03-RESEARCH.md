# Phase 3: Web UI & REST API - Research

**Researched:** 2026-04-19
**Domain:** FastAPI routers, Jinja2 templates, Bootstrap 5, mock adapters with failure injection, httpOnly JWT cookies
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** JWT in httpOnly cookie. Login/register endpoints issue JWT via `Set-Cookie` (httpOnly, SameSite=Lax). FastAPI `Depends()` reads cookie for all web and API routes. Single auth mechanism for both web pages and REST API. itsdangerous stays in pyproject.toml but is not used for session management.
- **D-02:** Auth pages in scope: login, register, password reset (two pages: request-reset and reset-confirm), logout endpoint.
- **D-03:** Unauthenticated access to protected pages (cart, checkout, orders) redirects to `/login?next=<original_url>`. After login, redirect back to the original URL.
- **D-04:** Password reset token is returned directly in the API response body (no email server) — intentional for demo; code comment makes it explicit.
- **D-05:** Bootstrap 5 loaded from CDN via `<link>` tag in `base.html`. No build step required.
- **D-06:** Functional + clean polish level: Bootstrap defaults with minimal customization. Navbar, product cards, clean forms. Professional without extra effort. No custom brand colors or logo in Phase 3.
- **D-07:** Single-page checkout: cart page has payment method selector (radio buttons: Credit Card / PayPal / Apple Pay) and a Checkout button. One POST to checkout endpoint places the order. No multi-step wizard.
- **D-08:** Order confirmation page shows: order ID, list of items, total amount, payment method used, current order status, and a link to the orders page.
- **D-09:** Cancel and Return actions live on the individual order detail page (`/orders/{id}`). Buttons are conditionally rendered based on order status eligibility (cancel: placed/paid; return: paid/processing/shipped).
- **D-10:** Keyword search uses case-insensitive substring match across product name, description, and category. Returns all products where any of these fields contains the search term.
- **D-11:** Product list page supports category filter tabs/links: All / Running / Hiking / Slides / Sandals / Socks. Search and category filter can combine.
- **D-12:** Product detail page shows name, description, price, inventory, category, and a variant selector (size/color dropdowns). Add to Cart is a POST form. On success, redirects to cart page.
- **D-13:** Warehouse mock (`app/lib/mocks/warehouse_mock.py`) implements: `get_available_quantity`, `reserve_inventory`, `ship_order`, `cancel_order`. Reads `FAILURE_CONFIG["warehouse"]` at call time.
- **D-14:** Payment mock (`app/lib/mocks/payment_mock.py`) implements: `charge`, `refund`. Reads `FAILURE_CONFIG["payment"]` at call time. Failure key pattern: `failed_to_charge_{method}`, `failed_to_refund_{method}`.
- **D-15:** Default FAILURE_CONFIG failure probabilities start at 0.0 (no failures by default).
- **D-16:** Web pages in scope: home/index redirect to product list, product list (`/products`), product detail (`/products/{id}`), cart (`/cart`), order confirmation (`/orders/{id}/confirmation`), orders list (`/orders`), order detail (`/orders/{id}`), login (`/login`), register (`/register`), password reset request (`/auth/reset-request`), password reset confirm (`/auth/reset-confirm`).

### Claude's Discretion

- Exact Bootstrap component choices (card vs. list-group for products, etc.)
- Navbar links and layout
- Flash message / alert approach for errors (Bootstrap alerts are fine)
- Whether to use Jinja2 `url_for` for static assets or inline CDN links
- Catalog service implementation details (function signatures, module location)
- Whether `catalog_service.py` lives at `app/lib/catalog/catalog_service.py` or `app/lib/catalog/service.py`
- Quantity selector behavior on the product detail page (default qty 1, allow increment)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CAT-02 | User can search for products by keyword via web UI and chatbot | catalog_service.search_products() with case-insensitive substring match across name/description/category (D-10); catalog_router.py GET /products?q= wires it to the template |
| CAT-03 | User can view product detail page (web) or ask for details (chat) | catalog_service.get_product(); products/detail.html template with variant dropdowns and Add to Cart form (D-12) |
| CHK-01 | User can check out with Credit Card (mock payment adapter) | payment_mock.charge() with `failed_to_charge_credit_card` failure key; cart page radio button selects `credit_card` method |
| CHK-02 | User can check out with PayPal (mock payment adapter) | Same payment_mock.charge(); PayPal radio button sends `paypal` method |
| CHK-03 | User can check out with Apple Pay (mock payment adapter) | Same payment_mock.charge(); Apple Pay radio button sends `apple_pay` method |
| CHK-04 | User receives order confirmation after successful checkout | orders/confirmation.html; checkout router POST redirects to /orders/{id}/confirmation after place_order() + charge() succeed |
| ORD-01 | User can check the status of an order (placed → paid → processing → shipped → canceled) | orders/list.html and orders/detail.html; status badge color-coded per UI-SPEC; orders_router GET /orders and GET /orders/{id} |
| ORD-02 | User can cancel an order; warehouse cancel mock runs; refund mock runs if payment captured | cancel_order() service already done; warehouse_mock.cancel_order() + payment_mock.refund() called from cancel endpoint; button gated by status |
| ORD-03 | User can request a return on any paid/processing/shipped order | request_return() service done; Return button on order detail page gated by status (D-09) |
| MOCK-01 | Warehouse mock adapter supports configurable global failure injection: `out_of_stock` and `failed_to_cancel_order` probabilities | warehouse_mock.py reads FAILURE_CONFIG["warehouse"] at call time; default 0.0; probability roll via random.random() |
| MOCK-02 | Payment mock adapter supports configurable global failure injection: `failed_to_charge_{method}` and `failed_to_refund_{method}` probabilities | payment_mock.py reads FAILURE_CONFIG["payment"] at call time; keys derived dynamically from method argument |

</phase_requirements>

---

## Summary

Phase 3 wires already-complete business logic (auth_service, cart_service, order_service) to HTTP via FastAPI routers, delivers all Jinja2 templates using Bootstrap 5 from CDN, builds the catalog service (search + detail), and creates warehouse/payment mock adapters with configurable failure injection. All service-layer logic is already implemented and tested; this phase is entirely in the routing, templating, and adapter wiring layers.

The two novel pieces of work are: (1) the auth dependency layer — two variants of `get_current_user` that read a JWT from an httpOnly cookie (`get_current_user_web` redirects to login, `get_current_user_api` raises HTTP 401), and (2) the checkout orchestration endpoint that calls payment_mock.charge() then order_service.place_order() and handles mock failures by re-rendering the cart with an error. All other routes are thin wrappers delegating to Phase 2 service functions.

The UI-SPEC (03-UI-SPEC.md) is fully authoritative on template structure, component choices, copy, and color. The CONVENTIONS.md defines the exact mock adapter function signatures and failure injection pattern. No new design decisions are needed — every layout, copy string, and status badge color is already specified.

**Primary recommendation:** Build in four sequential batches — (1) mock adapters + catalog service, (2) auth dependency + router, (3) catalog + cart + checkout routers + templates, (4) orders routers + templates. Each batch is independently testable before the next begins.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Product search + filter | API / Backend (catalog_service) | Frontend Server (template renders results) | Search logic runs server-side; Jinja2 renders the result list |
| Product detail with variants | API / Backend (catalog_service.get_product) | Frontend Server (template) | Domain logic fetches product; template renders variant selectors |
| Cart management (add/update/remove) | API / Backend (cart_service) | Frontend Server (redirect after POST) | asyncio.Lock guards mutations; PRG pattern prevents double-submit |
| Checkout (payment + order) | API / Backend (checkout_router + mock adapters) | — | Payment mock and place_order() both run server-side; no client logic |
| Order lifecycle (view/cancel/return) | API / Backend (order_service) | Frontend Server (template with conditional buttons) | Ownership and eligibility checks enforce server-side; template renders buttons conditionally |
| Auth (JWT cookie issue/read) | API / Backend (auth_router + auth dependency) | Frontend Server (redirect on missing cookie) | Cookie is httpOnly — browser cannot read or manipulate it |
| Failure injection config | API / Backend (config.py FAILURE_CONFIG dict) | — | Global in-process dict; mutation by root token in Phase 5 |
| Flash messages | Frontend Server (Starlette SessionMiddleware) | — | Server-side session stores flash; base.html renders and clears it |

---

## Standard Stack

### Core (all already in pyproject.toml)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastapi | 0.136.0 | HTTP routing, Depends(), APIRouter | Project stack; already installed |
| jinja2 | 3.1.6 | Server-side HTML templating | Project stack; already installed |
| python-multipart | 0.0.26 | Parses HTML form POST bodies (`Form()` dependency) | Required by FastAPI for form data; already installed |
| pyjwt | 2.12.1 | Decodes JWT from cookie in auth dependency | Project stack (not python-jose — CVE); already installed |
| itsdangerous | 2.2.0 | Starlette SessionMiddleware (flash messages) | Already in pyproject.toml; Starlette signs session cookie |
| starlette | (bundled with fastapi) | SessionMiddleware, RedirectResponse, Request | Part of FastAPI's dependency tree |

**No new packages required for Phase 3.** All dependencies are already installed.

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx | 0.28.1 | TestClient for route handler tests | Already in dev deps; use for integration tests |
| pytest-asyncio | 1.3.0 | async test functions | Already in dev deps; needed for async route handlers |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Starlette SessionMiddleware (flash) | Pass flash in query param | Session approach cleaner; query param leaks messages in URL |
| Two auth dependency functions | One with `web: bool` flag | Two functions (get_current_user_web, get_current_user_api) are clearer at call site |
| Form() for checkout POST | JSON body | HTML forms send `application/x-www-form-urlencoded`; Form() is correct; JSON requires JS |

**Installation:** No new packages. All Phase 3 dependencies are present.

---

## Architecture Patterns

### System Architecture Diagram

```
Browser
  │
  ├─ GET /products?q=...&category=...
  │     └─> catalog_router ──> catalog_service.search_products() ──> products_db
  │                                   └─> templates/products/list.html
  │
  ├─ POST /cart/add  (Form: product_id, size, color, qty)
  │     └─> cart_router ──> cart_service.add_item() ──> [asyncio.Lock] ──> carts_db
  │                              └─> RedirectResponse(/cart)
  │
  ├─ POST /checkout  (Form: payment_method)
  │     └─> checkout_router
  │               ├─> warehouse_mock.reserve_inventory()  ─[FAILURE_CONFIG roll]─> success|fail
  │               ├─> payment_mock.charge()               ─[FAILURE_CONFIG roll]─> success|fail
  │               ├─> order_service.place_order()  ──> orders_db
  │               └─> RedirectResponse(/orders/{id}/confirmation)  OR  re-render cart with error
  │
  ├─ POST /orders/{id}/cancel
  │     └─> orders_router
  │               ├─> order_service.cancel_order()
  │               ├─> warehouse_mock.cancel_order()  ─[FAILURE_CONFIG roll]─> success|fail
  │               ├─> payment_mock.refund()           ─[FAILURE_CONFIG roll]─> success|fail
  │               └─> RedirectResponse(/orders/{id})
  │
  └─ Auth flow
        ├─ POST /auth/login  ──> auth_service.login() ──> Set-Cookie(access_token, httpOnly)
        ├─ POST /auth/register ──> auth_service.register()
        └─ All protected routes ──> Depends(get_current_user_web)
                                          └─ Cookie("access_token") ──> verify_token()
                                          └─ Missing/invalid ──> RedirectResponse(/login?next=...)

config.py FAILURE_CONFIG (global dict)
  └─> warehouse_mock reads at call time (never at import)
  └─> payment_mock reads at call time (never at import)
```

### Recommended Project Structure

```
app/
├── api/
│   ├── auth_router.py          # POST /auth/login, /auth/register, /auth/logout
│   │                           # POST /auth/reset-request, /auth/reset-confirm
│   ├── catalog_router.py       # GET /products, GET /products/{id}
│   │                           # POST /cart/add (delegates to cart_service)
│   ├── cart_router.py          # GET /cart, POST /cart/update, POST /cart/remove
│   │                           # POST /checkout
│   └── orders_router.py        # GET /orders, GET /orders/{id}
│                               # GET /orders/{id}/confirmation
│                               # POST /orders/{id}/cancel, POST /orders/{id}/return
├── lib/
│   ├── auth/
│   │   ├── dependencies.py     # get_current_user_web(), get_current_user_api()
│   │   └── (existing files)
│   ├── catalog/
│   │   ├── catalog_service.py  # search_products(), get_product()
│   │   ├── models.py           # (existing)
│   │   └── store.py            # (existing)
│   └── mocks/
│       ├── warehouse_mock.py   # get_available_quantity, reserve_inventory,
│       │                       # ship_order, cancel_order
│       └── payment_mock.py     # charge, refund
└── web/
    └── templates/
        ├── base.html
        ├── products/
        │   ├── list.html
        │   └── detail.html
        ├── cart/
        │   └── cart.html
        ├── orders/
        │   ├── list.html
        │   ├── detail.html
        │   └── confirmation.html
        └── auth/
            ├── login.html
            ├── register.html
            ├── reset_request.html
            └── reset_confirm.html
```

### Pattern 1: Auth Dependency — Two Variants

**What:** Cookie-reading Depends() that returns the current User or fails appropriately for the caller type.
**When to use:** All protected route handlers; choose web vs API variant based on whether the caller is a browser page or REST API consumer.

```python
# app/lib/auth/dependencies.py
from typing import Annotated
from fastapi import Cookie, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from app.lib.auth.auth_service import verify_token
from app.lib.auth.store import users_db
from app.lib.auth.models import User

def _resolve_user(token: str | None) -> User | None:
    """Shared helper: decode token and return User or None."""
    if not token:
        return None
    result = verify_token(token)
    if not result["success"]:
        return None
    user_id = result["data"]["user_id"]
    return users_db.get(user_id)

async def get_current_user_web(
    request: Request,
    access_token: Annotated[str | None, Cookie()] = None,
) -> User:
    """For web page routes: redirect to /login on failure."""
    user = _resolve_user(access_token)
    if not user:
        next_url = str(request.url)
        raise HTTPException(
            status_code=307,
            headers={"Location": f"/login?next={next_url}"},
        )
    return user

async def get_current_user_api(
    access_token: Annotated[str | None, Cookie()] = None,
) -> User:
    """For REST API routes: return 401 on failure."""
    user = _resolve_user(access_token)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
```

**Source:** [VERIFIED: FastAPI docs — fastapi.tiangolo.com/tutorial/cookie-params/, fastapi.tiangolo.com/advanced/response-cookies/]

### Pattern 2: Login — Set httpOnly Cookie, Redirect

**What:** POST handler that calls auth_service.login(), sets JWT in httpOnly cookie, and redirects.
**When to use:** Web login form POST handler.

```python
# app/api/auth_router.py (web login handler)
from fastapi import APIRouter, Form, Request, Response
from fastapi.responses import RedirectResponse
from app.lib.auth.auth_service import login

router = APIRouter(tags=["auth"])

@router.post("/auth/login")
async def login_post(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
):
    result = login(email=email, password=password)
    if not result["success"]:
        # Re-render login page with error
        return templates.TemplateResponse(
            request=request,
            name="auth/login.html",
            context={"error": "Invalid email or password. Please try again."},
        )
    next_url = request.query_params.get("next", "/products")
    # Validate next is a relative path to prevent open redirect
    if not next_url.startswith("/"):
        next_url = "/products"
    redirect = RedirectResponse(url=next_url, status_code=303)
    redirect.set_cookie(
        key="access_token",
        value=result["data"]["token"],
        httponly=True,
        samesite="lax",
        max_age=30 * 60,
    )
    return redirect
```

**Source:** [VERIFIED: FastAPI docs — fastapi.tiangolo.com/advanced/response-cookies/]

### Pattern 3: Jinja2Templates Setup

**What:** One module-level `Jinja2Templates` instance shared across all routers.
**When to use:** Initialize once; import in all router files that render templates.

```python
# app/web/templates_config.py  (or inline in each router)
from fastapi.templating import Jinja2Templates
import os

# Templates directory is relative to project root (where uvicorn runs from)
templates = Jinja2Templates(directory="app/web/templates")
```

```python
# In a route handler:
@router.get("/products", response_class=HTMLResponse)
async def product_list(request: Request, q: str = "", category: str = ""):
    results = catalog_service.search_products(q=q, category=category)
    return templates.TemplateResponse(
        request=request,
        name="products/list.html",
        context={"products": results, "q": q, "active_category": category},
    )
```

**Source:** [VERIFIED: FastAPI docs — fastapi.tiangolo.com/advanced/templates/]

### Pattern 4: Flash Messages via Starlette Session

**What:** Set a flash in `request.session` before redirect; read and clear in `base.html`.
**When to use:** After POST actions that redirect (PRG pattern).

```python
# Setting a flash before redirect
request.session["flash"] = {"category": "success", "message": "Order placed!"}
return RedirectResponse(url=f"/orders/{order_id}/confirmation", status_code=303)
```

```html
<!-- base.html: read and clear flash -->
{% if request.session.get("flash") %}
  {% set flash = request.session.pop("flash") %}
  <div class="alert alert-{{ flash.category }} alert-dismissible fade show" role="alert">
    {{ flash.message }}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  </div>
{% endif %}
```

Middleware registration in main.py:
```python
from starlette.middleware.sessions import SessionMiddleware
app.add_middleware(SessionMiddleware, secret_key="dev-flash-secret")
```

**Source:** [VERIFIED: fastapi.tiangolo.com/tutorial/middleware/ — Starlette SessionMiddleware]

### Pattern 5: Mock Adapter — Failure Injection

**What:** Read `FAILURE_CONFIG` at call time, roll `random.random()`, return structured result.
**When to use:** Every mock adapter function. The pattern is already defined in CONVENTIONS.md.

```python
# app/lib/mocks/payment_mock.py
import random
from config import FAILURE_CONFIG

def charge(order_id: str, payment_method: str, amount: float) -> dict:
    """Simulate payment charge with configurable failure injection.

    Args:
        order_id: The order being charged.
        payment_method: One of credit_card, paypal, apple_pay.
        amount: Charge amount in dollars.

    Returns:
        Success dict with transaction_id, or failure dict with error code.
    """
    failure_key = f"failed_to_charge_{payment_method}"
    failure_prob = FAILURE_CONFIG.get("payment", {}).get(failure_key, 0.0)
    if random.random() < failure_prob:
        return {
            "success": False,
            "code": failure_key.upper(),
            "message": f"Mock payment failure: {failure_key}",
            "retryable": True,
        }
    return {"success": True, "data": {"transaction_id": f"txn_{order_id}"}}
```

**Source:** [VERIFIED: .planning/codebase/CONVENTIONS.md — Error Injection Pattern section]

### Pattern 6: PRG (Post/Redirect/Get) — All Successful POSTs

**What:** Every successful POST returns HTTP 303 redirect, never re-renders on success.
**When to use:** Add to cart, checkout, cancel, return, login, register, logout.

```python
# Correct: status_code=303 (See Other) for POST->GET redirect
return RedirectResponse(url="/cart", status_code=303)

# Wrong: 302 (temporary redirect) — browser may replay POST on redirect
```

**Source:** [ASSUMED — PRG is a universal web pattern; 303 vs 302 choice is standard practice]

### Anti-Patterns to Avoid

- **Reading FAILURE_CONFIG at import time:** Mock adapters must read the config dict at call time so Phase 5 root-token mutations take effect without restart. `failure_prob = FAILURE_CONFIG["payment"][key]` at module top is wrong.
- **Using `Optional[str]` or `List[]` typing:** Project convention requires `str | None` and `list[]` (Python 3.12+ style). See CONVENTIONS.md.
- **Relative imports:** Use `from app.lib.auth.dependencies import get_current_user_web` — not `from ..auth.dependencies`.
- **Storing plain-text token in cookie:** The JWT itself goes in the cookie — never wrap it in a dict or encode separately.
- **Open redirect on `?next=`:** Always validate `next` starts with `/` before redirecting. Never redirect to an external URL.
- **Rendering success response on POST:** Always redirect (PRG). Re-render only on validation failure.
- **Calling `place_order()` before `charge()`:** Charge first — if charge fails, no order is created. If place_order() succeeds and then charge fails, the order exists but payment didn't happen (inconsistent state).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cookie parsing from request | Manual header parse | `Cookie()` FastAPI dependency | FastAPI handles edge cases, encoding, multiple cookies |
| Session/flash storage | Custom dict in memory | Starlette `SessionMiddleware` + `request.session` | Already available via itsdangerous (in pyproject.toml); handles signing |
| HTML escaping in templates | Manual `str.replace()` | Jinja2 auto-escaping | Jinja2 auto-escapes by default in `.html` templates; prevents XSS |
| URL generation in templates | Hardcoded paths | `url_for()` in Jinja2 | Route name changes automatically update all links |
| Form body parsing | Manual body.decode() | FastAPI `Form()` | Handles URL encoding, multipart, content-type negotiation |
| Random failure probability | `random.randint(1, 100) < prob*100` | `random.random() < prob` | `random.random()` gives uniform [0.0, 1.0) — exact match to probability semantics |

**Key insight:** All the complex bits (JWT validation, password hashing, cart locking, order eligibility) are already in Phase 2 services. Phase 3 is wiring + templates — resist adding new logic in route handlers.

---

## Common Pitfalls

### Pitfall 1: Checkout Order of Operations

**What goes wrong:** Calling `place_order()` before `payment_mock.charge()` creates an orphaned order in `orders_db` even when the charge fails. The user sees an order that was never paid.

**Why it happens:** place_order() clears the cart immediately. If charge() then fails, the cart is gone and the order exists with `payment_status="pending"` forever.

**How to avoid:** Sequence is always: (1) `warehouse_mock.reserve_inventory()`, (2) `payment_mock.charge()`, (3) `order_service.place_order()`. Only create the order after both mocks succeed.

**Warning signs:** Order appears in `/orders` with `payment_status=pending` after a payment failure.

### Pitfall 2: `next` Parameter Open Redirect

**What goes wrong:** After login, code does `RedirectResponse(url=request.query_params.get("next"))`. An attacker crafts `/login?next=https://evil.com` and hijacks the redirect.

**Why it happens:** `?next=` is controlled by the unauthenticated user who crafts the URL.

**How to avoid:** Validate: `if not next_url.startswith("/"): next_url = "/products"`. Never allow protocol-relative `//` either.

**Warning signs:** Login redirect goes to an external domain.

### Pitfall 3: `request` Not Passed to TemplateResponse

**What goes wrong:** `templates.TemplateResponse(name="...", context={...})` crashes with a missing argument error in FastAPI 0.100+.

**Why it happens:** New FastAPI versions require `request` as first argument to TemplateResponse (it's used for `url_for()` inside templates).

**How to avoid:** Always pass `request=request` as the first keyword argument to `TemplateResponse`.

**Warning signs:** `TypeError: TemplateResponse.__init__() missing 1 required positional argument`.

### Pitfall 4: Flash Message Not Clearing Between Requests

**What goes wrong:** Flash message persists across multiple page views because the template reads `request.session.get("flash")` without deleting it.

**Why it happens:** `dict.get()` reads but does not remove. `dict.pop()` reads and removes atomically.

**How to avoid:** In base.html use `{% set flash = request.session.pop("flash", None) %}` — not `.get()`.

### Pitfall 5: Form Input Names Must Match FastAPI `Form()` Parameter Names

**What goes wrong:** HTML `<input name="paymentMethod">` does not match `Form(...)` parameter `payment_method`. FastAPI receives `None`.

**Why it happens:** HTML form field names are case-sensitive and must exactly match the Python parameter name (or alias). FastAPI does not auto-camelCase-to-snake_case convert form fields.

**How to avoid:** Use `name="payment_method"` in HTML. Verify every `<input name>` and `<select name>` against the router's `Form()` parameters.

### Pitfall 6: FAILURE_CONFIG Default Keys Must Include All Payment Methods

**What goes wrong:** `FAILURE_CONFIG["payment"]` has `failed_to_charge_credit_card` but not `failed_to_charge_paypal` or `failed_to_charge_apple_pay`. The `.get(failure_key, 0.0)` fallback saves correctness but demo operator cannot set PayPal/Apple Pay failure rates without adding the key.

**Why it happens:** config.py was scaffolded with only a credit_card example key.

**How to avoid:** Ensure FAILURE_CONFIG["payment"] has all six failure keys (3 charge + 3 refund) with default 0.0. Verify config.py has complete key set before implementing mocks.

### Pitfall 7: Variant Selector Sends Only size/color, Not product_id

**What goes wrong:** The Add to Cart form only sends `size` and `color` but not `product_id`. The cart router receives the variant selections but not which product to add.

**Why it happens:** `product_id` lives in the URL path (`/products/{id}`) but form fields must be explicit POST body fields.

**How to avoid:** Include `<input type="hidden" name="product_id" value="{{ product.id }}">` in the product detail form alongside the variant selects.

---

## Code Examples

### Catalog Service — search_products()

```python
# app/lib/catalog/catalog_service.py
from app.lib.catalog.store import products_db
from app.lib.catalog.models import Product

def search_products(q: str = "", category: str = "") -> list[Product]:
    """Search products by keyword and/or category.

    Case-insensitive substring match across name, description, category (D-10).
    Category filter is applied first; keyword narrows within category (D-11).

    Args:
        q: Optional keyword for substring search.
        category: Optional category filter (exact match, case-insensitive).

    Returns:
        List of matching Product instances (may be empty).
    """
    results = list(products_db.values())
    if category:
        results = [p for p in results if p.category.lower() == category.lower()]
    if q:
        q_lower = q.lower()
        results = [
            p for p in results
            if q_lower in p.name.lower()
            or q_lower in p.description.lower()
            or q_lower in p.category.lower()
        ]
    return results

def get_product(product_id: str) -> Product | None:
    """Retrieve a single product by ID.

    Args:
        product_id: UUID string of the product.

    Returns:
        Product dataclass or None if not found.
    """
    return products_db.get(product_id)
```

**Source:** [VERIFIED: .planning/phases/03-web-ui-rest-api/03-CONTEXT.md — D-10, D-11]

### Warehouse Mock — reserve_inventory()

```python
# app/lib/mocks/warehouse_mock.py
import random
from config import FAILURE_CONFIG

def reserve_inventory(order_id: str, items: list[dict]) -> dict:
    """Simulate inventory reservation with failure injection.

    Args:
        order_id: The order reserving inventory.
        items: List of dicts with product_id and quantity keys.

    Returns:
        Success dict or failure dict with retryable=True.
    """
    failure_prob = FAILURE_CONFIG.get("warehouse", {}).get("out_of_stock", 0.0)
    if random.random() < failure_prob:
        return {
            "success": False,
            "code": "OUT_OF_STOCK",
            "message": "Mock warehouse failure: inventory unavailable",
            "retryable": True,
        }
    return {"success": True, "data": {"reservation_id": f"res_{order_id}"}}
```

**Source:** [VERIFIED: .planning/codebase/CONVENTIONS.md — Error Injection Pattern; CONVENTIONS.md function signatures]

### Base Template Structure (Bootstrap 5 CDN)

```html
<!-- app/web/templates/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}ShoeStore{% endblock %}</title>
  <link rel="stylesheet"
        href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
  <link rel="stylesheet"
        href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
</head>
<body>
  <nav class="navbar navbar-expand-lg bg-light navbar-light">
    <div class="container">
      <a class="navbar-brand" href="/products">ShoeStore</a>
      <div class="collapse navbar-collapse">
        <ul class="navbar-nav ms-auto">
          <li class="nav-item"><a class="nav-link" href="/products">Products</a></li>
          <li class="nav-item"><a class="nav-link" href="/cart">
            <i class="bi bi-cart"></i> Cart</a></li>
          <li class="nav-item"><a class="nav-link" href="/orders">Orders</a></li>
          {% if current_user %}
          <li class="nav-item"><a class="nav-link" href="/auth/logout">Logout</a></li>
          {% else %}
          <li class="nav-item"><a class="nav-link" href="/login">Login</a></li>
          {% endif %}
        </ul>
      </div>
    </div>
  </nav>

  <div class="container py-4">
    {% set flash = request.session.pop("flash", None) %}
    {% if flash %}
    <div class="alert alert-{{ flash.category }} alert-dismissible fade show" role="alert">
      {{ flash.message }}
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>
    {% endif %}

    {% block content %}{% endblock %}
  </div>

  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js">
  </script>
</body>
</html>
```

**Source:** [VERIFIED: .planning/phases/03-web-ui-rest-api/03-UI-SPEC.md — base.html section; D-05, D-06]

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `TemplateResponse(name, {"request": request, ...})` | `TemplateResponse(request=request, name=..., context={...})` | FastAPI 0.95+ | Must pass request as keyword arg, not in context dict |
| `Optional[str]` from `typing` | `str \| None` union syntax | Python 3.10+ | Project requires Python 3.12+; use union syntax throughout |
| `from typing import List, Dict` | `list[...]`, `dict[...]` built-ins | Python 3.9+ | Use built-in generics per CONVENTIONS.md |
| `status_code=302` redirect | `status_code=303` (See Other) after POST | Standard practice | 303 guarantees browser switches to GET; 302 may replay POST |

**Deprecated/outdated:**
- `python-jose`: CVE-2024-33664 — project uses PyJWT instead (see CLAUDE.md)
- `Optional[]` from typing: project convention forbids this; use `str | None`
- Storing JWT in localStorage: this project uses httpOnly cookie (XSS-safe)

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | SessionMiddleware flash approach: `request.session.pop("flash", None)` works correctly in Jinja2 template context | Flash Messages pattern | If Starlette session dict doesn't support pop() in template context, flash won't clear; fallback: pass flash through query param or template context variable |
| A2 | FAILURE_CONFIG["payment"] should have all 6 keys (3 charge + 3 refund) with 0.0 defaults for Phase 3; current config.py has only 2 | Pitfall 6 | Mock adapter uses `.get(key, 0.0)` fallback so defaults work; but operator cannot configure missing keys without editing config.py |
| A3 | Checkout endpoint belongs in `cart_router.py` (POST /checkout served by the cart router) rather than a standalone checkout_router.py | Architecture | If planner creates a separate checkout_router, it just needs registering in main.py — low risk either way |

---

## Open Questions

1. **Checkout endpoint — which router file?**
   - What we know: POST /checkout processes the cart and creates an order; it touches cart_service, order_service, warehouse_mock, and payment_mock
   - What's unclear: Whether to put it in cart_router.py, orders_router.py, or a separate checkout_router.py
   - Recommendation: Put in cart_router.py (checkout is the final cart action) — but discretion is Claude's

2. **Jinja2 template base path — relative to project root or to app/web/?**
   - What we know: `Jinja2Templates(directory="app/web/templates")` works when uvicorn is run from project root
   - What's unclear: If run from a different directory, templates won't be found
   - Recommendation: Use `Path(__file__).parent / "templates"` relative to the templates_config.py file for robustness; or document the expected run directory in main.py

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All | ✓ | 3.13.12 | — |
| uv | Package management | ✓ | 0.9.7 | — |
| fastapi | HTTP routing | ✓ | in pyproject.toml | — |
| jinja2 | Templates | ✓ | in pyproject.toml | — |
| python-multipart | Form() parsing | ✓ | in pyproject.toml | — |
| itsdangerous | SessionMiddleware (flash) | ✓ | in pyproject.toml | — |
| pyjwt | JWT decode in auth dep | ✓ | in pyproject.toml | — |
| httpx | TestClient | ✓ | in dev deps | — |
| pytest-asyncio | async tests | ✓ | in dev deps | — |

**Missing dependencies with no fallback:** None — Phase 3 requires no new packages.

**Missing dependencies with fallback:** None.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 + pytest-asyncio 1.3.0 |
| Config file | pyproject.toml `[tool.pytest.ini_options]` (asyncio_mode = "auto") |
| Quick run command | `uv run pytest tests/unit/ -x -q` |
| Full suite command | `uv run pytest tests/ -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CAT-02 | search_products() returns correct results for keyword + category | unit | `uv run pytest tests/unit/test_catalog_service.py -x` | ❌ Wave 0 |
| CAT-03 | get_product() returns product or None | unit | `uv run pytest tests/unit/test_catalog_service.py -x` | ❌ Wave 0 |
| CHK-01 | POST /checkout with credit_card creates order and redirects to confirmation | integration | `uv run pytest tests/integration/test_checkout.py -x` | ❌ Wave 0 |
| CHK-02 | POST /checkout with paypal creates order | integration | `uv run pytest tests/integration/test_checkout.py::test_checkout_paypal -x` | ❌ Wave 0 |
| CHK-03 | POST /checkout with apple_pay creates order | integration | `uv run pytest tests/integration/test_checkout.py::test_checkout_apple_pay -x` | ❌ Wave 0 |
| CHK-04 | Confirmation page shows order ID, items, total, payment method, status | integration | `uv run pytest tests/integration/test_checkout.py::test_confirmation_page -x` | ❌ Wave 0 |
| ORD-01 | GET /orders lists user's orders; GET /orders/{id} shows detail with status badge data | integration | `uv run pytest tests/integration/test_orders_router.py -x` | ❌ Wave 0 |
| ORD-02 | POST /orders/{id}/cancel triggers warehouse cancel + payment refund mocks | integration | `uv run pytest tests/integration/test_orders_router.py::test_cancel_order -x` | ❌ Wave 0 |
| ORD-03 | POST /orders/{id}/return on paid/processing/shipped order succeeds | integration | `uv run pytest tests/integration/test_orders_router.py::test_return_order -x` | ❌ Wave 0 |
| MOCK-01 | warehouse_mock: probability 1.0 always fails; 0.0 always succeeds | unit | `uv run pytest tests/unit/test_warehouse_mock.py -x` | ❌ Wave 0 |
| MOCK-02 | payment_mock: charge and refund failure injection works for all 3 methods | unit | `uv run pytest tests/unit/test_payment_mock.py -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/unit/ -x -q`
- **Per wave merge:** `uv run pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/unit/test_catalog_service.py` — covers CAT-02, CAT-03
- [ ] `tests/unit/test_warehouse_mock.py` — covers MOCK-01
- [ ] `tests/unit/test_payment_mock.py` — covers MOCK-02
- [ ] `tests/integration/test_auth_router.py` — covers login/logout cookie flow
- [ ] `tests/integration/test_checkout.py` — covers CHK-01 through CHK-04
- [ ] `tests/integration/test_orders_router.py` — covers ORD-01 through ORD-03
- [ ] `tests/integration/conftest.py` — shared TestClient fixture, authenticated session helper

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | PyJWT verify_token() from Phase 2; httpOnly cookie; SameSite=Lax |
| V3 Session Management | yes | httpOnly cookie; `max_age=1800`; delete_cookie on logout |
| V4 Access Control | yes | `get_current_user_web/api` dependencies; ownership check in order_service |
| V5 Input Validation | yes | FastAPI Form() + Pydantic type coercion; server-side only (no JS validation) |
| V6 Cryptography | partial | PyJWT (not custom); bcrypt password hashing from Phase 2 — no new crypto in Phase 3 |

### Known Threat Patterns for FastAPI/Jinja2

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Open redirect via `?next=` | Spoofing | Validate `next` starts with `/`; reject protocol-relative or absolute URLs |
| XSS via Jinja2 output | Tampering | Jinja2 auto-escapes HTML in `.html` templates by default — never disable |
| CSRF on state-changing POSTs | Tampering | SameSite=Lax on the auth cookie provides baseline CSRF protection for same-site form POSTs |
| JWT token theft via JS | Information Disclosure | httpOnly cookie prevents JavaScript access to the token |
| Cross-user order access | Elevation of Privilege | order_service.get_order()/cancel_order()/request_return() enforce user_id ownership check (from Phase 2) |
| Double-submit on browser back | Tampering/data integrity | PRG pattern (303 redirect after every successful POST) prevents replay |

---

## Sources

### Primary (HIGH confidence)

- `.planning/phases/03-web-ui-rest-api/03-CONTEXT.md` — all locked decisions (D-01 through D-16)
- `.planning/phases/03-web-ui-rest-api/03-UI-SPEC.md` — authoritative template structure, component choices, copy, colors
- `.planning/codebase/CONVENTIONS.md` — mock adapter signatures, failure injection pattern, route handler pattern
- `app/lib/auth/auth_service.py` — verified service interface (register, login, verify_token, reset_request, reset_confirm)
- `app/lib/cart/cart_service.py` — verified service interface (add_item, update_quantity, remove_item, get_cart, clear_cart)
- `app/lib/orders/order_service.py` — verified service interface (place_order, cancel_order, request_return, get_order, list_orders)
- `config.py` — verified FAILURE_CONFIG structure and key names
- [VERIFIED: fastapi.tiangolo.com/advanced/templates/] — Jinja2Templates setup, TemplateResponse signature
- [VERIFIED: fastapi.tiangolo.com/tutorial/cookie-params/] — Cookie() dependency pattern
- [VERIFIED: fastapi.tiangolo.com/advanced/response-cookies/] — set_cookie parameters (httponly, samesite, max_age)
- [VERIFIED: fastapi.tiangolo.com/tutorial/middleware/] — SessionMiddleware registration

### Secondary (MEDIUM confidence)

- PyJWT 2.12.1 — cookie-based JWT decode pattern; verified against existing Phase 2 auth_service.py usage
- Starlette SessionMiddleware — `request.session` dict for flash messages; itsdangerous already in pyproject.toml

### Tertiary (LOW confidence)

- A1 (Assumptions Log): `request.session.pop()` in Jinja2 template context — standard Python dict method; should work but not explicitly tested against this FastAPI version

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages verified in pyproject.toml; FastAPI docs confirmed for template and cookie patterns
- Architecture: HIGH — all service functions verified by reading Phase 2 source; patterns derived from CONVENTIONS.md and official docs
- Mock adapters: HIGH — function signatures and failure injection pattern explicitly defined in CONVENTIONS.md
- Pitfalls: HIGH — checkout ordering and open redirect are well-known; others derived from reading existing code
- Template structure: HIGH — 03-UI-SPEC.md is fully authoritative

**Research date:** 2026-04-19
**Valid until:** 2026-05-19 (FastAPI 0.136 is stable; Bootstrap 5.3 CDN links are long-lived)
