# Phase 3: Web UI & REST API - Pattern Map

**Mapped:** 2026-04-19
**Files analyzed:** 17 new/modified files
**Analogs found:** 14 / 17

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `app/lib/auth/dependencies.py` | middleware | request-response | `app/lib/auth/auth_service.py` (verify_token) | role-match |
| `app/api/auth_router.py` | route | request-response | `app/lib/auth/auth_service.py` (return shape) | role-match (no router analog yet) |
| `app/api/catalog_router.py` | route | request-response | `app/lib/orders/order_service.py` (thin wrapper pattern) | role-match |
| `app/api/cart_router.py` | route | request-response | `app/lib/cart/cart_service.py` (async pattern) | role-match |
| `app/api/orders_router.py` | route | request-response | `app/lib/orders/order_service.py` | role-match |
| `app/lib/catalog/catalog_service.py` | service | CRUD | `app/lib/cart/cart_service.py` | exact |
| `app/lib/mocks/warehouse_mock.py` | utility | request-response | `config.py` FAILURE_CONFIG + RESEARCH.md Pattern 5 | partial |
| `app/lib/mocks/payment_mock.py` | utility | request-response | `config.py` FAILURE_CONFIG + RESEARCH.md Pattern 5 | partial |
| `app/web/templates/base.html` | template | request-response | RESEARCH.md Pattern 3 / Pattern 4 | no codebase analog |
| `app/web/templates/products/list.html` | template | request-response | no analog | no analog |
| `app/web/templates/products/detail.html` | template | request-response | no analog | no analog |
| `app/web/templates/cart/cart.html` | template | request-response | no analog | no analog |
| `app/web/templates/orders/list.html` | template | request-response | no analog | no analog |
| `app/web/templates/orders/detail.html` | template | request-response | no analog | no analog |
| `app/web/templates/orders/confirmation.html` | template | request-response | no analog | no analog |
| `app/web/templates/auth/login.html` | template | request-response | no analog | no analog |
| `app/web/templates/auth/register.html` | template | request-response | no analog | no analog |
| `app/web/templates/auth/reset_request.html` | template | request-response | no analog | no analog |
| `app/web/templates/auth/reset_confirm.html` | template | request-response | no analog | no analog |
| `main.py` (modify) | config | request-response | `main.py` itself | exact (extend) |
| `config.py` (modify) | config | — | `config.py` itself | exact (extend) |
| `tests/unit/test_catalog_service.py` | test | CRUD | `tests/unit/test_cart_service.py` | exact |
| `tests/unit/test_warehouse_mock.py` | test | request-response | `tests/unit/test_auth_service.py` | role-match |
| `tests/unit/test_payment_mock.py` | test | request-response | `tests/unit/test_auth_service.py` | role-match |
| `tests/integration/conftest.py` | test | request-response | no analog | no analog |
| `tests/integration/test_auth_router.py` | test | request-response | no analog | no analog |
| `tests/integration/test_checkout.py` | test | request-response | no analog | no analog |
| `tests/integration/test_orders_router.py` | test | request-response | no analog | no analog |

---

## Pattern Assignments

### `app/lib/auth/dependencies.py` (middleware, request-response)

**Analog:** `app/lib/auth/auth_service.py` — specifically `verify_token()` (lines 94–123)

**Imports pattern** (from auth_service.py lines 5–14):
```python
from app.lib.auth.models import User
from app.lib.auth.store import users_db
from config import JWT_ALGORITHM, JWT_SECRET
```

**Core auth dependency pattern** — copy from RESEARCH.md Pattern 1 (no codebase analog exists yet, use research pattern verbatim):
```python
# app/lib/auth/dependencies.py
from typing import Annotated
from fastapi import Cookie, HTTPException, Request
from app.lib.auth.auth_service import verify_token
from app.lib.auth.store import users_db
from app.lib.auth.models import User

def _resolve_user(token: str | None) -> User | None:
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
    user = _resolve_user(access_token)
    if not user:
        next_url = str(request.url)
        if not next_url.startswith("/"):
            next_url = "/products"
        raise HTTPException(
            status_code=307,
            headers={"Location": f"/login?next={next_url}"},
        )
    return user

async def get_current_user_api(
    access_token: Annotated[str | None, Cookie()] = None,
) -> User:
    user = _resolve_user(access_token)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
```

**verify_token error-handling pattern** (auth_service.py lines 107–123):
```python
try:
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    return {"success": True, "data": {"user_id": payload["user_id"]}}
except jwt.ExpiredSignatureError:
    return {"success": False, "code": "TOKEN_EXPIRED", "message": "Token has expired", "retryable": False}
except jwt.InvalidTokenError:
    return {"success": False, "code": "INVALID_TOKEN", "message": "Token is invalid", "retryable": False}
```

---

### `app/api/auth_router.py` (route, request-response)

**Analog:** No existing router in codebase. Use RESEARCH.md Patterns 2 and 6 as the template, plus the service return shape from `app/lib/auth/auth_service.py`.

**Service return shapes to wire** (auth_service.py):
- `register()` → `{"success": True, "data": {"user_id": str, "email": str}}`
- `login()` → `{"success": True, "data": {"token": str, "user_id": str}}`
- `reset_request()` → `{"success": True, "data": {"token": str | None, "message": str}}`
- `reset_confirm()` → `{"success": True, "data": {"message": str}}`

**Thin route handler pattern** — check result["success"], raise or redirect (order_service.py lines 116–162 for the ownership-check-then-action structure, applied to HTTP):
```python
# Route handler shape — thin wrapper
result = service_fn(...)
if not result["success"]:
    # Re-render form with error (on GET-producing routes) or raise HTTPException (API routes)
    return templates.TemplateResponse(request=request, name="...", context={"error": result["message"]})
# On success: PRG — always 303
return RedirectResponse(url="/...", status_code=303)
```

**Set httpOnly cookie + PRG redirect** (RESEARCH.md Pattern 2):
```python
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

**Delete cookie on logout**:
```python
response = RedirectResponse(url="/products", status_code=303)
response.delete_cookie("access_token")
return response
```

**Open redirect guard** (always apply when using `?next=`):
```python
next_url = request.query_params.get("next", "/products")
if not next_url.startswith("/") or next_url.startswith("//"):
    next_url = "/products"
```

---

### `app/api/catalog_router.py` (route, request-response)

**Analog:** `app/lib/orders/order_service.py` for the service-delegate pattern; `app/lib/catalog/store.py` for the store access pattern.

**Imports pattern** (mirrors order_service.py lines 1–11 style):
```python
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.lib.catalog import catalog_service
from app.lib.auth.dependencies import get_current_user_web
from app.lib.auth.models import User
```

**TemplateResponse pattern** (RESEARCH.md Pattern 3 — required keyword-arg form for FastAPI 0.95+):
```python
return templates.TemplateResponse(
    request=request,
    name="products/list.html",
    context={"products": results, "q": q, "active_category": category},
)
```

**404 pattern** (mirrors order_service.py lines 129–136 for not-found handling):
```python
product = catalog_service.get_product(product_id)
if not product:
    raise HTTPException(status_code=404, detail="Product not found")
```

---

### `app/api/cart_router.py` (route, request-response)

**Analog:** `app/lib/cart/cart_service.py` — async service calls with Lock; also RESEARCH.md Pattern 6 (PRG).

**Async route with await** (cart_service.py lines 36–86 — add_item is async):
```python
# Cart mutations are async — must await
result = await cart_service.add_item(user_id=current_user.id, product_id=product_id, quantity=qty)
if not result["success"]:
    request.session["flash"] = {"category": "danger", "message": result["message"]}
return RedirectResponse(url="/cart", status_code=303)
```

**Checkout sequencing** (RESEARCH.md Pitfall 1 — order of operations is critical):
```python
# Correct order: reserve → charge → place_order
reserve_result = warehouse_mock.reserve_inventory(...)
if not reserve_result["success"]: ...  # re-render cart with error

charge_result = payment_mock.charge(...)
if not charge_result["success"]: ...  # re-render cart with error

order_result = order_service.place_order(user_id, payment_method)
# Only here do we redirect to confirmation
return RedirectResponse(url=f"/orders/{order_result['data']['order_id']}/confirmation", status_code=303)
```

**Form() parameter** (must match HTML input name exactly — RESEARCH.md Pitfall 5):
```python
from fastapi import Form
async def checkout_post(
    request: Request,
    payment_method: str = Form(...),
    current_user: User = Depends(get_current_user_web),
):
```

---

### `app/api/orders_router.py` (route, request-response)

**Analog:** `app/lib/orders/order_service.py` — ownership check, eligibility check, structured return.

**Service delegation + ownership pattern** (order_service.py lines 214–241):
```python
# user_id always from session (JWT), never from request body
result = order_service.get_order(order_id=order_id, user_id=current_user.id)
if not result["success"]:
    if result["code"] == "UNAUTHORIZED":
        raise HTTPException(status_code=403, detail="Access denied")
    raise HTTPException(status_code=404, detail="Order not found")
```

**Conditional redirect with flash** (RESEARCH.md Pattern 4):
```python
if not result["success"]:
    request.session["flash"] = {"category": "danger", "message": result["message"]}
    return RedirectResponse(url=f"/orders/{order_id}", status_code=303)
request.session["flash"] = {"category": "success", "message": "Order canceled."}
return RedirectResponse(url=f"/orders/{order_id}", status_code=303)
```

---

### `app/lib/catalog/catalog_service.py` (service, CRUD)

**Analog:** `app/lib/cart/cart_service.py` — same service pattern (plain functions, structured dict returns, store access, no HTTP dependency).

**Imports pattern** (mirrors cart_service.py lines 1–10):
```python
# app/lib/catalog/catalog_service.py
from app.lib.catalog.store import products_db
from app.lib.catalog.models import Product
```

**Service function return shape** (cart_service.py lines 86, 158, 175–181):
```python
# Success: {"success": True, "data": {...}}
# Not-found: {"success": False, "code": "...", "message": "...", "retryable": False}
```

**Search function** (from RESEARCH.md Code Examples, matches D-10, D-11):
```python
def search_products(q: str = "", category: str = "") -> list[Product]:
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
    return products_db.get(product_id)
```

**Note:** catalog_service returns `Product` objects directly (not wrapped dicts) for search_products, because the router passes them directly to the template. get_product returns `Product | None` — router handles the None → 404 conversion.

---

### `app/lib/mocks/warehouse_mock.py` (utility, request-response)

**Analog:** `config.py` (lines 7–16) for FAILURE_CONFIG structure; RESEARCH.md Pattern 5 for failure injection.

**Imports pattern**:
```python
# app/lib/mocks/warehouse_mock.py
import random
from config import FAILURE_CONFIG
```

**Failure injection pattern** (RESEARCH.md Pattern 5 — read config at call time, never import time):
```python
def reserve_inventory(order_id: str, items: list[dict]) -> dict:
    failure_prob = FAILURE_CONFIG.get("warehouse", {}).get("out_of_stock", 0.0)
    if random.random() < failure_prob:
        return {
            "success": False,
            "code": "OUT_OF_STOCK",
            "message": "Mock warehouse failure: inventory unavailable",
            "retryable": True,
        }
    return {"success": True, "data": {"reservation_id": f"res_{order_id}"}}

def cancel_order(order_id: str) -> dict:
    failure_prob = FAILURE_CONFIG.get("warehouse", {}).get("failed_to_cancel_order", 0.0)
    if random.random() < failure_prob:
        return {
            "success": False,
            "code": "FAILED_TO_CANCEL_ORDER",
            "message": "Mock warehouse failure: cancel failed",
            "retryable": True,
        }
    return {"success": True, "data": {"order_id": order_id}}
```

**Structured return shape** (mirrors auth_service.py and order_service.py success/failure shape — all services in this project):
```python
# Success: {"success": True, "data": {…}}
# Failure: {"success": False, "code": str, "message": str, "retryable": bool}
```

---

### `app/lib/mocks/payment_mock.py` (utility, request-response)

**Analog:** Same as warehouse_mock.py — `config.py` FAILURE_CONFIG + RESEARCH.md Pattern 5.

**Dynamic key pattern** (RESEARCH.md Pattern 5, D-14):
```python
# app/lib/mocks/payment_mock.py
import random
from config import FAILURE_CONFIG

def charge(order_id: str, payment_method: str, amount: float) -> dict:
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

def refund(order_id: str, payment_method: str, amount: float) -> dict:
    failure_key = f"failed_to_refund_{payment_method}"
    failure_prob = FAILURE_CONFIG.get("payment", {}).get(failure_key, 0.0)
    if random.random() < failure_prob:
        return {
            "success": False,
            "code": failure_key.upper(),
            "message": f"Mock payment failure: {failure_key}",
            "retryable": True,
        }
    return {"success": True, "data": {"refund_id": f"ref_{order_id}"}}
```

---

### `main.py` (modify — add routers + middleware)

**Analog:** `main.py` itself (lines 1–27) — extend the existing lifespan pattern.

**Router registration pattern** (extend lines 26–27):
```python
from starlette.middleware.sessions import SessionMiddleware
from app.api.auth_router import router as auth_router
from app.api.catalog_router import router as catalog_router
from app.api.cart_router import router as cart_router
from app.api.orders_router import router as orders_router

app.add_middleware(SessionMiddleware, secret_key="dev-flash-secret")
app.include_router(auth_router)
app.include_router(catalog_router)
app.include_router(cart_router)
app.include_router(orders_router)
```

---

### `config.py` (modify — complete FAILURE_CONFIG keys)

**Analog:** `config.py` lines 7–16 — extend existing dict.

**Current state** (lines 7–16) — missing 4 of 6 payment keys and FAILURE_CONFIG defaults:
```python
FAILURE_CONFIG: dict[str, dict[str, float]] = {
    "warehouse": {
        "out_of_stock": 0.10,
        "failed_to_cancel_order": 0.20,
    },
    "payment": {
        "failed_to_charge_credit_card": 0.03,
        "failed_to_refund_paypal": 0.08,
    },
}
```

**Target state** — all 6 payment keys must exist (RESEARCH.md Pitfall 6):
```python
FAILURE_CONFIG: dict[str, dict[str, float]] = {
    "warehouse": {
        "out_of_stock": 0.10,
        "failed_to_cancel_order": 0.20,
    },
    "payment": {
        "failed_to_charge_credit_card": 0.03,
        "failed_to_charge_paypal": 0.0,
        "failed_to_charge_apple_pay": 0.0,
        "failed_to_refund_credit_card": 0.0,
        "failed_to_refund_paypal": 0.08,
        "failed_to_refund_apple_pay": 0.0,
    },
}
```

---

### Unit test files (test_catalog_service.py, test_warehouse_mock.py, test_payment_mock.py)

**Analog:** `tests/unit/test_cart_service.py` (lines 1–60) for structure; `tests/unit/test_auth_service.py` (lines 19–31) for the store-clearing autouse fixture; `tests/unit/test_order_service.py` (lines 22–37) for the factory helper pattern.

**File header + autouse fixture** (test_cart_service.py lines 1–19, test_auth_service.py lines 19–31):
```python
# tests/unit/test_catalog_service.py
import pytest
from app.lib.catalog.store import products_db
from app.lib.catalog.models import Product

@pytest.fixture(autouse=True)
def clear_stores():
    products_db.clear()
    yield
    products_db.clear()
```

**Factory helper pattern** (test_order_service.py lines 22–37):
```python
def make_product(
    product_id: str = "prod-1",
    name: str = "Test Shoe",
    description: str = "A test shoe",
    unit_price: float = 99.99,
    inventory: int = 10,
    category: str = "running",
) -> Product:
    return Product(id=product_id, name=name, description=description,
                   unit_price=unit_price, inventory=inventory, category=category)
```

**async test marker** (test_cart_service.py lines 39–44 — used when testing async functions):
```python
@pytest.mark.asyncio
async def test_add_item_product_not_found():
    ...
```

**Mock adapter test pattern** — set FAILURE_CONFIG probability to 1.0 to force failure, 0.0 to force success:
```python
# tests/unit/test_warehouse_mock.py
from config import FAILURE_CONFIG

def test_reserve_inventory_always_fails_at_prob_1():
    FAILURE_CONFIG["warehouse"]["out_of_stock"] = 1.0
    result = warehouse_mock.reserve_inventory("ord-1", [])
    assert result["success"] is False
    assert result["code"] == "OUT_OF_STOCK"
    FAILURE_CONFIG["warehouse"]["out_of_stock"] = 0.0  # reset

def test_reserve_inventory_always_succeeds_at_prob_0():
    FAILURE_CONFIG["warehouse"]["out_of_stock"] = 0.0
    result = warehouse_mock.reserve_inventory("ord-1", [])
    assert result["success"] is True
```

---

### Integration test files

**Analog:** No existing integration tests. Use RESEARCH.md Validation Architecture section + the unit test patterns above.

**conftest.py pattern** (standard FastAPI TestClient + authenticated session):
```python
# tests/integration/conftest.py
import pytest
from fastapi.testclient import TestClient
from main import app
from app.lib.auth.store import users_db, reset_tokens_db
from app.lib.cart.store import carts_db
from app.lib.orders.store import orders_db
from app.lib.catalog.store import products_db
from app.lib.seed.seed import seed

@pytest.fixture(autouse=True)
def reset_stores():
    users_db.clear(); reset_tokens_db.clear()
    carts_db.clear(); orders_db.clear(); products_db.clear()
    seed()
    yield
    users_db.clear(); reset_tokens_db.clear()
    carts_db.clear(); orders_db.clear(); products_db.clear()

@pytest.fixture
def client():
    return TestClient(app, follow_redirects=False)

@pytest.fixture
def auth_client(client):
    """TestClient with alice@example.com already logged in (cookie set)."""
    resp = client.post("/auth/login", data={"email": "alice@example.com", "password": "password123"})
    # Cookie is set automatically on the client session
    return client
```

---

## Shared Patterns

### Structured Return Shape
**Source:** `app/lib/auth/auth_service.py` lines 30–38, 66–71; `app/lib/orders/order_service.py` lines 131–136
**Apply to:** All service functions, all mock adapter functions
```python
# Success
{"success": True, "data": {…}}
# Failure
{"success": False, "code": "SCREAMING_SNAKE", "message": "Human-readable.", "retryable": bool}
```

### Route Handler Thin-Wrapper Pattern
**Source:** RESEARCH.md — "Key insight" (Phase 2 services have all logic; Phase 3 is wiring)
**Apply to:** All four router files
```python
result = service_fn(...)
if not result["success"]:
    # For web routes: flash + redirect, or re-render with error in context
    # For API routes: raise HTTPException with appropriate status
    ...
# On success: PRG (303 redirect) for web; JSON response for API
```

### Flash Message Pattern
**Source:** RESEARCH.md Pattern 4
**Apply to:** `auth_router.py`, `cart_router.py`, `orders_router.py` (all POST handlers that redirect)
```python
# Setting flash before redirect
request.session["flash"] = {"category": "success"|"danger"|"warning", "message": "..."}
return RedirectResponse(url="...", status_code=303)

# Reading in base.html (use pop, not get — clears after one display)
{% set flash = request.session.pop("flash", None) %}
```

### PRG (Post/Redirect/Get) — All Successful POSTs
**Source:** RESEARCH.md Pattern 6
**Apply to:** Every POST handler in every router
```python
return RedirectResponse(url="...", status_code=303)  # Always 303, never 302
```

### Python 3.12+ Type Syntax
**Source:** `app/lib/auth/auth_service.py` line 74; `app/lib/catalog/models.py` lines 22–23; `config.py` line 7
**Apply to:** All new files
```python
# Correct (project convention)
str | None          # not Optional[str]
list[Product]       # not List[Product]
dict[str, float]    # not Dict[str, float]
```

### Absolute Imports Only
**Source:** `app/lib/cart/cart_service.py` lines 6–9; `app/lib/orders/order_service.py` lines 6–11
**Apply to:** All new files
```python
from app.lib.auth.dependencies import get_current_user_web  # correct
# NOT: from ..auth.dependencies import ...                   # wrong
```

### FAILURE_CONFIG Read at Call Time
**Source:** `config.py` lines 1–5 (comment), RESEARCH.md Anti-Patterns section
**Apply to:** `warehouse_mock.py`, `payment_mock.py`
```python
# Correct — read inside function body
def charge(...):
    failure_prob = FAILURE_CONFIG.get("payment", {}).get(failure_key, 0.0)

# Wrong — read at module level (config mutation won't take effect)
# failure_prob = FAILURE_CONFIG["payment"]["failed_to_charge_credit_card"]  # at top of file
```

### TemplateResponse Keyword-Arg Signature
**Source:** RESEARCH.md Pattern 3 + Pitfall 3 (FastAPI 0.95+ requirement)
**Apply to:** All route handlers that render templates
```python
# Correct (FastAPI 0.95+)
return templates.TemplateResponse(
    request=request,
    name="products/list.html",
    context={"key": value},
)
# Wrong — request in context dict (old pattern, causes TypeError)
# return templates.TemplateResponse("products/list.html", {"request": request, ...})
```

---

## No Analog Found

Files with no close match in the codebase (planner should use RESEARCH.md patterns instead):

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `app/web/templates/base.html` | template | request-response | No Jinja2 templates exist yet in the codebase; use RESEARCH.md Code Example (Base Template Structure) |
| `app/web/templates/products/list.html` | template | request-response | No HTML templates in codebase; use 03-UI-SPEC.md as primary reference |
| `app/web/templates/products/detail.html` | template | request-response | Same — use 03-UI-SPEC.md |
| `app/web/templates/cart/cart.html` | template | request-response | Same — use 03-UI-SPEC.md |
| `app/web/templates/orders/list.html` | template | request-response | Same — use 03-UI-SPEC.md |
| `app/web/templates/orders/detail.html` | template | request-response | Same — use 03-UI-SPEC.md |
| `app/web/templates/orders/confirmation.html` | template | request-response | Same — use 03-UI-SPEC.md |
| `app/web/templates/auth/login.html` | template | request-response | Same — use 03-UI-SPEC.md; note demo hint for alice@example.com / bob@example.com (CONTEXT.md Specifics) |
| `app/web/templates/auth/register.html` | template | request-response | Same — use 03-UI-SPEC.md |
| `app/web/templates/auth/reset_request.html` | template | request-response | Same — use 03-UI-SPEC.md |
| `app/web/templates/auth/reset_confirm.html` | template | request-response | Same — use 03-UI-SPEC.md |
| `tests/integration/conftest.py` | test | request-response | No integration tests exist yet; use FastAPI TestClient pattern from RESEARCH.md |
| `tests/integration/test_auth_router.py` | test | request-response | Same |
| `tests/integration/test_checkout.py` | test | request-response | Same |
| `tests/integration/test_orders_router.py` | test | request-response | Same |

---

## Critical Implementation Notes for Planner

1. **Checkout order of operations is non-negotiable:** reserve_inventory → charge → place_order. See RESEARCH.md Pitfall 1. Reversing any step creates orphaned orders.

2. **`config.py` must be patched first** (add missing payment keys) before any mock adapter tests will be meaningful. See RESEARCH.md Pitfall 6.

3. **`request.session.pop("flash", None)` in Jinja2 template** — use `pop`, not `get`. See RESEARCH.md Pitfall 4.

4. **Form field names must exactly match FastAPI `Form()` parameter names** — `name="payment_method"` in HTML, `payment_method: str = Form(...)` in Python. See RESEARCH.md Pitfall 5.

5. **Hidden product_id input required in Add to Cart form** — `<input type="hidden" name="product_id" value="{{ product.id }}">`. See RESEARCH.md Pitfall 7.

6. **`Jinja2Templates` instance** — instantiate once, import everywhere. Recommended location: `app/web/templates_config.py` or inline in each router. Path should be resolved relative to project root or use `Path(__file__)`.

---

## Metadata

**Analog search scope:** `app/lib/`, `app/api/`, `tests/unit/`, `main.py`, `config.py`
**Files scanned:** 14 source files read in full
**Pattern extraction date:** 2026-04-19
