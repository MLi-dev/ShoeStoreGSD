# Phase 4: Claude Agent - Pattern Map

**Mapped:** 2026-04-19
**Files analyzed:** 7 new/modified files
**Analogs found:** 6 / 7

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `app/api/chat_router.py` | router | request-response | `app/api/orders_router.py` | exact |
| `app/web/templates/chat/chat.html` | template | request-response | `app/web/templates/cart/cart.html` | role-match |
| `app/lib/agent/agent.py` | service | event-driven (tool loop) | `app/lib/cart/cart_service.py` | partial (async + lock pattern) |
| `app/lib/agent/tools.py` | service | request-response | `app/lib/orders/order_service.py` | role-match |
| `app/lib/guardrails/guardrails.py` | utility | transform | `app/lib/mocks/payment_mock.py` | partial (config-read-at-call-time pattern) |
| `app/lib/agent/history.py` | utility | CRUD | `app/lib/cart/store.py` | exact (in-memory dict store + lock) |
| `main.py` | config | - | `main.py` (self — modify) | exact |

---

## Pattern Assignments

### `app/api/chat_router.py` (router, request-response)

**Analog:** `app/api/orders_router.py`

**Imports pattern** (lines 1-15):
```python
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.lib.auth.dependencies import get_current_user_web
from app.lib.auth.models import User
from app.lib.agent import agent
```

**Auth dependency pattern** (orders_router.py lines 40-43):
```python
@router.get("/chat", response_class=HTMLResponse)
async def chat_page(
    request: Request,
    current_user: User = Depends(get_current_user_web),
):
```

**GET page route pattern** — renders Jinja2 template, passes `current_user` to context (orders_router.py lines 40-55):
```python
    return templates.TemplateResponse(
        request=request,
        name="chat/chat.html",
        context={"current_user": current_user},
    )
```

**POST AJAX endpoint pattern** — thin handler: call service, check `success`, return JSON. The chat POST differs from other routers in that it returns `JSONResponse` (not a redirect) because the frontend submits via fetch():
```python
@router.post("/chat/message")
async def chat_message(
    request: Request,
    current_user: User = Depends(get_current_user_web),
) -> JSONResponse:
    body = await request.json()
    user_message: str = body.get("message", "").strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Message required")
    # [root]: strip happens here (D-14) before passing to agent
    result = await agent.run(user_id=current_user.id, user=current_user, message=user_message)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return JSONResponse({"reply": result["data"]["reply"]})
```

**Router setup** (no prefix — consistent with orders_router.py line 14):
```python
router = APIRouter(tags=["chat"])
templates = Jinja2Templates(directory="app/web/templates")
```

**Error shape** — translate `success: False` to HTTP error (orders_router.py lines 65-69):
```python
    if not result["success"]:
        if result.get("code") == "UNAUTHORIZED":
            raise HTTPException(status_code=403, detail="Access denied")
        raise HTTPException(status_code=404, detail="Order not found")
```

---

### `app/web/templates/chat/chat.html` (template, request-response)

**Analog:** `app/web/templates/cart/cart.html` and `app/web/templates/base.html`

**Extends base.html** (cart.html line 1):
```jinja2
{% extends "base.html" %}
{% block title %}Chat — ShoeStore{% endblock %}
{% block content %}
```

**Bootstrap 5 from CDN — no build step** (base.html lines 7-10):
```html
<link rel="stylesheet"
      href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
```
Chat template loads `marked.js` the same way — CDN `<script>` tag, no npm:
```html
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
```

**current_user available in context** (base.html lines 34-43):
```jinja2
{% if current_user %}
<li class="nav-item">
  <form method="post" action="/auth/logout" class="d-inline">
    <button type="submit" class="btn btn-link nav-link p-0">Logout</button>
  </form>
</li>
{% endif %}
```
Chat template passes `current_user` so navbar renders correctly; no other template data needed (transcript is AJAX-driven).

**JS fetch pattern for AJAX POST** — no analog exists in codebase (all other forms are standard HTML form POSTs). This is the only AJAX pattern:
```javascript
async function sendMessage() {
    const input = document.getElementById("user-input");
    const message = input.value.trim();
    if (!message) return;
    appendMessage("user", message);
    input.value = "";
    const response = await fetch("/chat/message", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message}),
    });
    const data = await response.json();
    appendMessage("agent", data.reply);
}

function appendMessage(role, text) {
    const div = document.createElement("div");
    div.className = role === "agent" ? "mb-3 text-start" : "mb-3 text-end";
    // Agent messages: render markdown via marked.js
    div.innerHTML = role === "agent"
        ? `<div class="d-inline-block bg-light border rounded p-2">${marked.parse(text)}</div>`
        : `<div class="d-inline-block bg-primary text-white rounded p-2">${text}</div>`;
    document.getElementById("transcript").appendChild(div);
    div.scrollIntoView({behavior: "smooth"});
}
```

---

### `app/lib/agent/agent.py` (service, event-driven tool loop)

**Analog:** `app/lib/cart/cart_service.py` (for `asyncio.Lock` pattern) and CONVENTIONS.md agent loop spec

**asyncio.Lock pattern** (cart_service.py lines 5-11):
```python
import asyncio

_cart_lock = asyncio.Lock()

# Usage:
async with _cart_lock:
    # mutate shared state
```
History dict uses same pattern:
```python
_history_lock = asyncio.Lock()
```

**Async service function signature** — all public agent functions are `async def` (cart_service.py line 36):
```python
async def add_item(user_id: str, product_id: str, quantity: int) -> dict:
```

**Structured result dict returned** — success/failure shape (order_service.py lines 72-78):
```python
return {
    "success": False,
    "code": "CART_EMPTY",
    "message": "Cart is empty",
    "retryable": False,
}
```

**Agent loop pattern** — from CONVENTIONS.md and D-11 through D-13; no existing analog in codebase:
```python
import asyncio
from anthropic import AsyncAnthropic

_client = AsyncAnthropic()
MAX_TURNS = 10

async def run(user_id: str, user: User, message: str) -> dict:
    """Run the agent loop for one user turn.

    Args:
        user_id: Authenticated user's ID (from JWT, never from message content).
        user: Full User dataclass for system prompt injection.
        message: Sanitized user message (root token already stripped by router).

    Returns:
        Success dict with reply text, or failure dict on loop error.
    """
    # Append user message to history (under lock)
    async with _history_lock:
        history.append_message(user_id, {"role": "user", "content": message})
        messages = history.get_messages(user_id)

    for _ in range(MAX_TURNS):
        response = await _client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            system=_build_system_prompt(user),
            messages=messages,
            tools=TOOL_SCHEMAS,
        )
        if response.stop_reason == "end_turn":
            reply = _extract_text(response)
            async with _history_lock:
                history.append_message(user_id, {"role": "assistant", "content": reply})
            return {"success": True, "data": {"reply": reply}}

        # Tool use block — D-13: always append tool_result even on exception
        tool_uses = [b for b in response.content if b.type == "tool_use"]
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for tool_use in tool_uses:
            try:
                result = await _dispatch_tool(user_id=user_id, tool_use=tool_use)
            except Exception as exc:
                result = {"error": str(exc)}
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": str(result),
            })
        messages.append({"role": "user", "content": tool_results})

    # Hard cap reached — return last partial response
    return {"success": True, "data": {"reply": _extract_text(response)}}
```

**Import from config at call time** (payment_mock.py lines 8-9 and config.py lines 7-24):
```python
from config import DEMO_MODE, FAILURE_CONFIG
# Read inside the function body, not at module level
```

---

### `app/lib/agent/tools.py` (service, request-response)

**Analog:** `app/lib/orders/order_service.py`

**Docstring pattern — Google style** (order_service.py lines 26-35):
```python
def _order_to_dict(order: Order) -> dict:
    """Serialize an Order to a plain dict.

    Args:
        order: The Order dataclass instance.

    Returns:
        Dict with all Order fields; items rendered as dicts.
    """
```

**Ownership from user_id only — never from message content** (order_service.py lines 144-150):
```python
    # D-13: ownership check first
    if order.user_id != user_id:
        return {
            "success": False,
            "code": "UNAUTHORIZED",
            "message": "Access denied",
            "retryable": False,
        }
```

**Structured result dict** (order_service.py lines 172-174):
```python
    return {
        "success": True,
        "data": {"order_id": order.id, "order_status": "canceled"},
    }
```

**Tool function signatures** — wrap existing services (from CONVENTIONS.md):
```python
async def search_products(user_id: str, q: str = "", category: str = "") -> dict:
async def get_product_details(user_id: str, product_id: str) -> dict:
async def add_to_cart(user_id: str, product_id: str, quantity: int) -> dict:
async def view_cart(user_id: str) -> dict:
async def checkout(user_id: str, payment_method: str) -> dict:
async def place_order(user_id: str, payment_method: str) -> dict:
async def check_order_status(user_id: str, order_id: str) -> dict:
async def cancel_order(user_id: str, order_id: str) -> dict:
async def return_order(user_id: str, order_id: str) -> dict:
async def reset_password(user_id: str, new_password: str) -> dict:
```

**Wrapping call pattern** (catalog_router.py lines 27-30):
```python
    products = catalog_service.search_products(q=q, category=category)
    # tool returns serializable dict, not dataclass instances
```

**Async call to cart service** (catalog_router.py lines 69-73):
```python
    result = await cart_service.add_item(
        user_id=current_user.id,
        product_id=product_id,
        quantity=quantity,
    )
```

---

### `app/lib/guardrails/guardrails.py` (utility, transform)

**Analog:** `app/lib/mocks/payment_mock.py` (config-read-at-call-time, structured return)

**No direct analog** — no other pre-flight filter exists in codebase. Pattern derived from CONVENTIONS.md guardrails section.

**Config read at call time** (payment_mock.py lines 23-25):
```python
    failure_prob = FAILURE_CONFIG.get("payment", {}).get(failure_key, 0.0)
    if random.random() < failure_prob:
```
Guardrails reads `DEMO_MODE` at call time:
```python
from config import DEMO_MODE  # imported at module level is fine since DEMO_MODE is static
```

**Structured return shape** (order_service.py lines 73-77):
```python
return {
    "success": False,
    "code": "INJECTION_DETECTED",
    "message": "I can only help with ShoeStore shopping and orders. Is there something I can help you find or order?",
    "retryable": False,
}
```

**Pattern to implement:**
```python
import re

# Compile once at module load — patterns are static
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(previous|prior|all)\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+your\s+system\s+prompt", re.IGNORECASE),
    re.compile(r"pretend\s+you\s+are", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+a", re.IGNORECASE),
    re.compile(r"forget\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
]

_SCOPE_REFUSAL = (
    "I can only help with ShoeStore shopping and orders. "
    "Is there something I can help you find or order?"
)

def check_message(message: str) -> dict:
    """Check a user message for prompt injection patterns.

    Args:
        message: Raw user message text (after [root]: stripping).

    Returns:
        Success dict if message is clean, or failure dict with SCOPE_VIOLATION code.
    """
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(message):
            return {
                "success": False,
                "code": "INJECTION_DETECTED",
                "message": _SCOPE_REFUSAL,
                "retryable": False,
            }
    return {"success": True, "data": {"message": message}}
```

---

### `app/lib/agent/history.py` (utility, CRUD)

**Analog:** `app/lib/cart/store.py` (in-memory dict, keyed by user_id)

**Store pattern** (cart/store.py lines 1-6):
```python
# app/lib/cart/store.py
# In-memory Cart store. Keyed by user_id (one cart per user).
from app.lib.cart.models import Cart

carts_db: dict[str, Cart] = {}
```
History uses same pattern with `asyncio.Lock`:
```python
import asyncio
from typing import Any

# Keyed by user_id. Each value is a list of Anthropic message dicts.
_history: dict[str, list[dict[str, Any]]] = {}
_history_lock = asyncio.Lock()
```

**Lock usage pattern** (cart_service.py lines 59-67):
```python
async with _cart_lock:
    if product.inventory == 0:
        return { ... }
    cart = carts_db.get(user_id)
    if cart is None:
        cart = Cart(user_id=user_id)
        carts_db[user_id] = cart
```
History functions follow the same `async with _history_lock:` guard on all mutations.

**Public interface functions:**
```python
async def append_message(user_id: str, message: dict[str, Any]) -> None:
async def get_messages(user_id: str) -> list[dict[str, Any]]:
async def clear_history(user_id: str) -> None:
```

---

### `main.py` (modify — router registration)

**Analog:** `main.py` itself (lines 34-42)

**Router import + include_router pattern** (main.py lines 34-42):
```python
from app.api.auth_router import router as auth_router       # noqa: E402
from app.api.catalog_router import router as catalog_router  # noqa: E402
from app.api.cart_router import router as cart_router        # noqa: E402
from app.api.orders_router import router as orders_router    # noqa: E402

app.include_router(auth_router)
app.include_router(catalog_router)
app.include_router(cart_router)
app.include_router(orders_router)
```

**Addition — append after existing routers:**
```python
from app.api.chat_router import router as chat_router        # noqa: E402
app.include_router(chat_router)
```

---

## Shared Patterns

### Authentication Dependency
**Source:** `app/lib/auth/dependencies.py` lines 34-65
**Apply to:** `app/api/chat_router.py` (both GET page and POST AJAX endpoint)

Use `get_current_user_web` for both routes — page GET redirects to /login if unauthenticated (consistent with D-01 from Phase 3). The POST endpoint also uses `get_current_user_web` so the 307 redirect is consistent; client-side JS can detect a non-JSON redirect response and reload the page.

```python
from app.lib.auth.dependencies import get_current_user_web
from app.lib.auth.models import User

async def get_current_user_web(
    request: Request,
    access_token: Annotated[str | None, Cookie()] = None,
) -> User:
    user = _resolve_user(access_token)
    if not user:
        next_url = request.url.path
        raise HTTPException(
            status_code=307,
            headers={"Location": f"/login?next={next_url}"},
        )
    return user
```

### Structured Error Response Shape
**Source:** `app/lib/orders/order_service.py` lines 73-78 and CONVENTIONS.md
**Apply to:** `agent.py`, `tools.py`, `guardrails.py`

```python
# Success
{"success": True, "data": {...}}

# Failure
{
    "success": False,
    "code": "SCREAMING_SNAKE_CASE_CODE",
    "message": "Human-readable message",
    "retryable": bool,
}
```

### asyncio.Lock on Mutable In-Memory State
**Source:** `app/lib/cart/cart_service.py` lines 5-11, 59-67
**Apply to:** `app/lib/agent/history.py`, `app/lib/agent/agent.py`

```python
import asyncio
_some_lock = asyncio.Lock()

async def mutate_state(...):
    async with _some_lock:
        # check + mutate — atomic under the lock
```

### Google-Style Docstrings on All Public Functions
**Source:** `app/lib/orders/order_service.py` lines 54-70
**Apply to:** All functions in `agent.py`, `tools.py`, `guardrails.py`, `history.py`

```python
def function_name(arg1: str, arg2: int) -> dict:
    """One-line summary of what the function does.

    Args:
        arg1: Description of arg1.
        arg2: Description of arg2.

    Returns:
        Description of return value shape.
    """
```

### Config Read at Call Time (not import time)
**Source:** `app/lib/mocks/payment_mock.py` lines 23-25 and CONVENTIONS.md
**Apply to:** Any agent or guardrail code that checks `DEMO_MODE` or `FAILURE_CONFIG`

```python
# In the function body, not at module top:
from config import FAILURE_CONFIG  # OK at module level only if used inside functions
failure_prob = FAILURE_CONFIG.get("payment", {}).get(failure_key, 0.0)
```
For `DEMO_MODE` (static bool): reading at import time is safe since it does not mutate.
For `FAILURE_CONFIG` (mutated by Phase 5 root instructions): always read the dict value inside the function body.

### Import Organization
**Source:** `app/api/orders_router.py` lines 5-13 and CONVENTIONS.md
**Apply to:** All new files

```python
# 1. Standard library
import asyncio
import re
from typing import Any

# 2. Third-party
from anthropic import AsyncAnthropic
from fastapi import APIRouter, Depends, HTTPException, Request

# 3. Internal — absolute imports
from app.lib.auth.dependencies import get_current_user_web
from app.lib.auth.models import User
from app.lib.agent import history
from config import DEMO_MODE
```

### Jinja2 Template Setup (per router)
**Source:** `app/api/orders_router.py` lines 14-15 and `app/api/catalog_router.py` lines 14-15
**Apply to:** `app/api/chat_router.py`

```python
router = APIRouter(tags=["chat"])
templates = Jinja2Templates(directory="app/web/templates")
```

### Base Template Extension
**Source:** `app/web/templates/cart/cart.html` line 1, `app/web/templates/orders/list.html` line 1
**Apply to:** `app/web/templates/chat/chat.html`

```jinja2
{% extends "base.html" %}
{% block title %}Chat — ShoeStore{% endblock %}
{% block content %}
...
{% endblock %}
```
Pass `current_user` in template context so navbar logout link renders (base.html lines 34-43 conditional on `current_user`).

---

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `app/lib/agent/agent.py` (core loop) | service | event-driven (LLM tool loop) | No LLM agent loop exists in codebase; loop pattern comes from CONVENTIONS.md D-11 through D-14 and Anthropic SDK docs |

---

## Metadata

**Analog search scope:** `app/api/`, `app/lib/`, `app/web/templates/`, `main.py`, `config.py`
**Files scanned:** 14 Python source files, 11 HTML templates
**Pattern extraction date:** 2026-04-19
