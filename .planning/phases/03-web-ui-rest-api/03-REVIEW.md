---
phase: 03-web-ui-rest-api
reviewed: 2026-04-19T00:00:00Z
depth: standard
files_reviewed: 27
files_reviewed_list:
  - app/api/auth_router.py
  - app/api/cart_router.py
  - app/api/catalog_router.py
  - app/api/orders_router.py
  - app/lib/auth/dependencies.py
  - app/lib/catalog/catalog_service.py
  - app/lib/mocks/payment_mock.py
  - app/lib/mocks/warehouse_mock.py
  - app/web/templates/auth/login.html
  - app/web/templates/auth/register.html
  - app/web/templates/auth/reset_confirm.html
  - app/web/templates/auth/reset_request.html
  - app/web/templates/base.html
  - app/web/templates/cart/cart.html
  - app/web/templates/orders/confirmation.html
  - app/web/templates/orders/detail.html
  - app/web/templates/orders/list.html
  - app/web/templates/products/detail.html
  - app/web/templates/products/list.html
  - config.py
  - main.py
  - pyproject.toml
  - tests/integration/conftest.py
  - tests/integration/test_auth_router.py
  - tests/integration/test_checkout.py
  - tests/integration/test_orders_router.py
  - tests/unit/test_catalog_service.py
  - tests/unit/test_payment_mock.py
  - tests/unit/test_warehouse_mock.py
findings:
  critical: 2
  warning: 4
  info: 4
  total: 10
status: issues_found
---

# Phase 03: Code Review Report

**Reviewed:** 2026-04-19
**Depth:** standard
**Files Reviewed:** 27
**Status:** issues_found

## Summary

The Phase 03 web UI and REST API implementation is solid overall. The PRG pattern is consistently applied, the open-redirect guard in `_safe_next` is correct, the httpOnly SameSite=Lax cookie is set properly, and the checkout sequence (reserve → charge → place_order) follows the documented critical path. Auth dependency split (web vs API) is well-structured.

Two critical issues require fixes before the phase can be signed off: a silent inventory leak when payment fails at checkout (reserved inventory is never released), and a dead status string `"captured"` in the cancel-order refund guard that will silently skip refunds for orders that reach that payment state. Four warnings cover the unencoded `next` parameter in the redirect URL built by `get_current_user_web`, a silent drop of `size`/`color` variant data in `add_to_cart`, hardcoded secrets, and a missing CSRF-token mechanism. Four info items cover minor quality improvements.

---

## Critical Issues

### CR-01: Inventory reservation not released on payment failure

**File:** `app/api/cart_router.py:144-160`

**Issue:** When `reserve_inventory` succeeds (Step 1) but `payment_mock.charge` fails (Step 2), the handler immediately returns the error template without calling `warehouse_mock.cancel_order`. This leaves a dangling warehouse reservation for the temporary order ID (`temp_id`). In a real system this would permanently hold stock. Even in the mock, if failure-injection tests run in sequence, the reservation count is never decremented.

**Fix:**
```python
# Step 2: Charge payment (payment mock)
charge_result = payment_mock.charge(
    order_id=temp_id,
    payment_method=payment_method,
    amount=total,
)
if not charge_result["success"]:
    # Release the reservation before surfacing the error
    warehouse_mock.cancel_order(order_id=temp_id)
    return templates.TemplateResponse(
        request=request,
        name="cart/cart.html",
        context={
            "items": enriched_items,
            "total": total,
            "current_user": current_user,
            "error": "Payment failed. Please try a different payment method or contact support.",
        },
        status_code=200,
    )
```

---

### CR-02: Dead status string `"captured"` in `_REFUND_ON_CANCEL_STATUSES`

**File:** `app/api/orders_router.py:18`

**Issue:** `_REFUND_ON_CANCEL_STATUSES = ("paid", "captured")`. The order status enum used throughout the codebase is `placed`, `paid`, `processing`, `shipped`, `canceled`, `returned`. There is no `"captured"` status. Including it is dead code — no order will ever have `payment_status == "captured"` — but it signals a mismatch between the intended design and the implementation. More importantly, if the intent was to also refund orders in `"processing"` or `"shipped"` state, those cases are currently silently skipped when canceling (which the spec says is not allowed for those statuses anyway, so the cancel path may never be reached — but the tuple is still wrong and confusing).

**Fix:** Remove the dead entry and add a comment explaining which statuses trigger a refund:
```python
# Statuses where a payment was captured and a refund must be issued on cancel.
# Only "paid" orders can be canceled per order_service eligibility check.
_REFUND_ON_CANCEL_STATUSES = ("paid",)
```

---

## Warnings

### WR-01: `next` redirect URL not URL-encoded in `get_current_user_web`

**File:** `app/lib/auth/dependencies.py:58-63`

**Issue:** The `next_url` built from `request.url.path` and `request.url.query` is spliced directly into the `Location` header as `?next={next_url}`. If the original request URL contains characters that are significant in a query string (`&`, `=`, `+`, `#`), the `next` parameter boundary will be broken, causing the login handler to receive a truncated or malformed `next` value. For example, a request to `/orders?status=paid` would produce `Location: /login?next=/orders?status=paid`, making `status=paid` a separate query parameter on the login URL rather than part of the `next` value.

**Fix:** URL-encode the next value before embedding it:
```python
from urllib.parse import quote

next_url = request.url.path
if request.url.query:
    next_url = f"{next_url}?{request.url.query}"
raise HTTPException(
    status_code=307,
    headers={"Location": f"/login?next={quote(next_url, safe='/')}"},
)
```

The `login.html` template must then also decode it when submitting the form — but since `_safe_next` in the auth router receives the decoded value from FastAPI's query-param parsing, encoding here is sufficient.

---

### WR-02: `add_to_cart` silently drops `size` and `color` variant fields

**File:** `app/api/catalog_router.py:69-73`

**Issue:** The form on `products/detail.html` collects `size` and `color` inputs and posts them to `/cart/add`. The route handler receives them (`size: str = Form(...)`, `color: str = Form(...)`) but passes only `product_id` and `quantity` to `cart_service.add_item`. The variant selection is silently discarded:

```python
result = await cart_service.add_item(
    user_id=current_user.id,
    product_id=product_id,
    quantity=quantity,
    # size and color are NOT forwarded
)
```

If `cart_service.add_item` is meant to validate that the selected size/color combination is a real variant (and reserve the correct variant's stock), this drop means all adds succeed regardless of variant availability, and the stored cart item carries no variant information. This is a correctness issue — the cart stores product-level items, not variant-level items, which will cause problems if variant stock needs to be tracked.

If the current design intentionally ignores variants at the cart level (tracking only product-level stock), the `size` and `color` form fields and the route parameters are misleading dead code. Either forward the fields to `add_item` or remove them from the route signature.

**Fix (if variants are intentionally ignored for now):**
```python
@router.post("/cart/add")
async def add_to_cart(
    request: Request,
    product_id: str = Form(...),
    quantity: int = Form(1),
    current_user: User = Depends(get_current_user_web),
):
```
If variants must be tracked, extend `cart_service.add_item` to accept and store `size` and `color`.

---

### WR-03: Hardcoded secrets in `config.py` and `main.py`

**File:** `config.py:27` and `main.py:31`

**Issue:** Two secrets are hardcoded as string literals:
- `JWT_SECRET: str = "dev-secret-change-in-prod"` (`config.py:27`)
- `secret_key="dev-flash-secret"` (`main.py:31`)

These will be committed to version control. For a personal demo this is low risk, but if this repo is ever pushed to a public host (GitHub, etc.) the secrets are permanently exposed in git history. The JWT secret signs auth tokens; if leaked, it allows forging tokens for any user including admin.

**Fix:** Load from environment variables with a fallback only for local dev:
```python
import os
JWT_SECRET: str = os.environ.get("JWT_SECRET", "dev-secret-change-in-prod")
```
```python
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SESSION_SECRET", "dev-flash-secret"))
```

---

### WR-04: No CSRF token on state-changing forms

**File:** `app/web/templates/cart/cart.html:29,39,56`, `app/web/templates/orders/detail.html:49,60`, `app/web/templates/auth/login.html:10`

**Issue:** All HTML forms that trigger state mutations (add/update/remove cart items, checkout, cancel order, return order, login, logout) contain no CSRF token. SameSite=Lax cookies provide partial protection — cross-site navigations via `<a>` or `window.location` will not send the cookie. However, same-site iframes, form POSTs from the same registrable domain, and subdomain attacks are not mitigated by SameSite=Lax alone.

For the current single-origin demo this is acceptable, but it is a gap worth tracking.

**Fix (minimal):** Add a CSRF token to the session middleware and inject it into a hidden form field, or enable the `itsdangerous`-backed CSRF middleware that is already a transitive dependency (via `itsdangerous` in `pyproject.toml`).

---

## Info

### IN-01: `"captured"` absent from `_status_badge` map

**File:** `app/api/orders_router.py:30-37`

**Issue:** `_status_badge` has no entry for `"captured"` (which is referenced by `_REFUND_ON_CANCEL_STATUSES` — see CR-02). This is a consistency signal pointing to the same root problem identified in CR-02.

**Fix:** Resolved by fixing CR-02 (removing `"captured"` from `_REFUND_ON_CANCEL_STATUSES`).

---

### IN-02: Demo passwords hardcoded in login template

**File:** `app/web/templates/auth/login.html:29`

**Issue:** `Demo accounts: alice@example.com or bob@example.com — password: password123` — the displayed password (`password123`) does not match the actual seeded password used in tests (`alice-demo-password-2026`, `bob-demo-password-2026`). A user following the UI hint will fail to log in.

**Fix:** Update the template hint to match the actual demo passwords, or make the hint dynamic from a template variable:
```html
<p class="small text-muted text-center">
  Demo: alice@example.com / alice-demo-password-2026 &nbsp;|&nbsp; bob@example.com / bob-demo-password-2026
</p>
```

---

### IN-03: All integration and unit tests marked `xfail` — implementation is complete

**File:** `tests/integration/test_auth_router.py:7`, `tests/integration/test_checkout.py:25`, `tests/integration/test_orders_router.py:28`, `tests/unit/test_catalog_service.py:30`, `tests/unit/test_payment_mock.py:12`, `tests/unit/test_warehouse_mock.py:12`

**Issue:** Every test is decorated with `@pytest.mark.xfail(strict=False, reason="... not yet implemented")`. The implementation appears complete (routers are registered, services are in place). Tests that pass will be silently reported as `xpass` (unexpected pass) rather than as green tests. With `strict=False`, an `xpass` does not fail the suite, so the test suite always "passes" even when all tests succeed — providing no meaningful CI signal.

**Fix:** Remove the `xfail` markers now that Phase 03 implementation is complete. Run `pytest` to confirm all tests pass, then strip the decorators.

---

### IN-04: `bcrypt<4` pin in `pyproject.toml` — version floor missing

**File:** `pyproject.toml:11`

**Issue:** `"bcrypt<4"` sets an upper bound only, meaning `bcrypt==1.0` would satisfy the constraint. The pin was added to avoid a known passlib compatibility break with bcrypt 4.x, but without a lower bound (e.g., `"bcrypt>=3.2,<4"`) the dependency resolver could theoretically select a much older version.

**Fix:**
```toml
"bcrypt>=3.2,<4",
```

---

_Reviewed: 2026-04-19_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
