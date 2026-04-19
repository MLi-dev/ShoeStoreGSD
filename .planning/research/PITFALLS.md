# Research: Pitfalls — Python FastAPI + Claude AI Demo Store

**Date:** 2026-04-18
**Scope:** Greenfield Python demo e-commerce app with FastAPI, Anthropic Claude tool-use, Langfuse, in-memory state

---

## Summary

13 specific pitfalls across 6 domains. 4 are critical (data corruption or security) and should be addressed in early phases. The rest are moderate or minor — manageable if caught before the relevant phase ships.

---

## Domain 1: Async State & Concurrency

### Pitfall 1 — Inventory oversell via async race condition
**Severity:** Critical

**What goes wrong:** Two concurrent checkout requests both read `product.inventory = 1`, both pass the "in stock" check, both decrement — inventory goes to -1.

**Why it happens:** FastAPI is async. Without locking, `check → decrement` is not atomic across concurrent requests.

**Prevention:**
```python
# In app/lib/orders/service.py
from asyncio import Lock

_inventory_lock = Lock()

async def reserve_inventory(product_id: str, qty: int) -> bool:
    async with _inventory_lock:
        product = catalog_store[product_id]
        if product.inventory < qty:
            return False
        product.inventory -= qty
        return True
```

**Warning signs:** Tests occasionally fail with negative inventory under load.

**Phase to address:** Phase 2 (Core Domain Actions)

---

### Pitfall 2 — Shared dict mutation during iteration
**Severity:** Moderate

**What goes wrong:** Iterating `orders_store.values()` while another coroutine adds an order raises `RuntimeError: dictionary changed size during iteration`.

**Prevention:** Snapshot before iterating: `list(orders_store.values())`. Never iterate raw store dicts in async context.

**Warning signs:** Intermittent `RuntimeError` only under concurrent requests.

**Phase to address:** Phase 2

---

## Domain 2: Claude Tool-Use Agent Loop

### Pitfall 3 — Agent loop with no hard stop
**Severity:** Critical

**What goes wrong:** Agent keeps calling tools indefinitely — either stuck in a clarification loop or tool errors return ambiguous results the model tries to resolve with more tools. Request hangs, burns tokens.

**Prevention:**
```python
MAX_AGENT_ITERATIONS = 10

async def run_agent(messages, tools):
    for _ in range(MAX_AGENT_ITERATIONS):
        response = await client.messages.create(...)
        if response.stop_reason == "end_turn":
            break
        if response.stop_reason == "tool_use":
            tool_results = await dispatch_tools(response)
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
    else:
        return error_response("Agent iteration limit reached")
```

**Warning signs:** Requests that never return; runaway token usage in Langfuse.

**Phase to address:** Phase 4 (Chatbot Tool Layer)

---

### Pitfall 4 — Malformed tool results break the messages array
**Severity:** Critical

**What goes wrong:** When a tool raises an exception, the code skips appending the `tool_result` block. The Anthropic API receives a `tool_use` with no matching `tool_result` on the next turn → 400 error.

**Prevention:** Always emit a `tool_result` block, even on exception:
```python
async def dispatch_tools(response) -> list:
    results = []
    for block in response.content:
        if block.type == "tool_use":
            try:
                output = await call_tool(block.name, block.input)
            except Exception as e:
                output = {"success": False, "error": str(e)}
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(output)
            })
    return results
```

**Warning signs:** 400 errors from Anthropic API mid-conversation.

**Phase to address:** Phase 4

---

### Pitfall 5 — Tool input validation failures are swallowed
**Severity:** Moderate

**What goes wrong:** Model passes `product_id: null` to `get_product_details`. Code crashes or returns a confusing error. Model hallucinates a recovery.

**Prevention:** Validate all tool inputs at the tool boundary, return structured `{"success": false, "code": "INVALID_INPUT", "message": "..."}` — never let exceptions bubble up to the agent messages array.

**Phase to address:** Phase 4

---

## Domain 3: Security & Prompt Injection

### Pitfall 6 — Root token reaches the LLM before parsing
**Severity:** Critical

**What goes wrong:** `[root]: disable all failures` is passed directly into the messages array sent to Claude. The model may parse it as a user preference rather than a system command, or leak it in a response.

**Prevention:** Strip and parse root instructions in the route handler before building the messages array. Gate on `DEMO_MODE` env var:
```python
def extract_root_instruction(user_input: str) -> tuple[str, str | None]:
    if not settings.DEMO_MODE:
        return user_input, None
    match = re.match(r"^\[root\]:\s*(.+)", user_input.strip(), re.IGNORECASE)
    if match:
        return "", match.group(1)
    return user_input, None
```

**Warning signs:** Root instructions appear in Claude's response text; model acknowledges `[root]` syntax.

**Phase to address:** Phase 5 (Mock Failure Injection)

---

### Pitfall 7 — Cross-user order access via agent tool
**Severity:** Critical

**What goes wrong:** Agent calls `check_order_status(order_id="ORD-999")`. If the tool looks up by `order_id` alone without verifying `user_id`, any authenticated user can see any order.

**Prevention:** Always resolve `user_id` from the authenticated session (injected into the tool context), never from the user's message:
```python
async def check_order_status(order_id: str, *, session_user_id: str) -> dict:
    order = orders_store.get(order_id)
    if not order or order.user_id != session_user_id:
        return {"success": False, "code": "NOT_FOUND"}
    return {"success": True, "order": order}
```

**Warning signs:** Any tool that takes `order_id` or `user_id` as a user-supplied parameter.

**Phase to address:** Phase 4

---

## Domain 4: Langfuse Observability

### Pitfall 8 — Broken parent/child span relationships
**Severity:** Moderate

**What goes wrong:** Spans appear flat in Langfuse instead of nested. Agent span doesn't contain tool spans. Makes traces useless for debugging.

**Why it happens:** Using `@observe` decorator in one function and `langfuse.span()` context manager in another without threading the parent explicitly.

**Prevention:** Pass the parent trace/span explicitly through the call stack rather than relying on decorator magic:
```python
trace = langfuse.trace(name="chat_request", user_id=user_id)
with trace.span(name="agent_loop") as agent_span:
    for tool_call in tool_calls:
        with agent_span.span(name=f"tool:{tool_call.name}") as tool_span:
            result = await call_tool(tool_call, span=tool_span)
```

**Warning signs:** All spans appear at the same depth in Langfuse UI.

**Phase to address:** Phase 6 (Observability)

---

### Pitfall 9 — PII leaks into Langfuse trace inputs
**Severity:** Moderate

**What goes wrong:** Full message history including `email`, `password_hash` references, or order details gets logged as trace input/output.

**Prevention:** Scrub messages before passing to Langfuse:
```python
SCRUB_KEYS = {"password", "password_hash", "token", "credit_card"}

def scrub_for_trace(obj):
    if isinstance(obj, dict):
        return {k: "***" if k in SCRUB_KEYS else scrub_for_trace(v) for k, v in obj.items()}
    return obj
```

**Phase to address:** Phase 6

---

### Pitfall 10 — Langfuse client failure crashes the app
**Severity:** Moderate

**What goes wrong:** Langfuse is unreachable (network issue, bad API key). Every request throws an exception.

**Prevention:** Wrap all Langfuse calls in try/except. Use a `NoopSpan` fallback:
```python
class NoopSpan:
    def span(self, **kwargs): return self
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def update(self, **kwargs): pass

def get_trace(name, **kwargs):
    try:
        return langfuse.trace(name=name, **kwargs)
    except Exception:
        return NoopSpan()
```

**Phase to address:** Phase 6

---

## Domain 5: In-Memory State & Seeding

### Pitfall 11 — Cold start with empty stores
**Severity:** Moderate

**What goes wrong:** App starts with no products, no test users. First request fails or returns empty catalog. Demo is broken on every fresh start.

**Prevention:** Call `seed()` unconditionally in FastAPI `lifespan` startup:
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    seed()  # always runs, idempotent
    assert len(catalog_store) >= 10, "Seed failed — catalog empty"
    yield
```

**Warning signs:** Empty product list on first page load; test failures on fresh runs.

**Phase to address:** Phase 1 (Scaffold + Seed)

---

### Pitfall 12 — Failure injection tests are flaky due to `random.random()`
**Severity:** Moderate

**What goes wrong:** Tests that exercise mock failure paths pass sometimes and fail sometimes because probability rolls are non-deterministic.

**Prevention:** Make the RNG injectable:
```python
def charge(order_id, method, amount, *, rng=random.random):
    if rng() < FAILURE_CONFIG["payment"]["failed_to_charge_credit_card"]:
        return {"success": False, "code": "FAILED_TO_CHARGE_CREDIT_CARD", ...}
    return {"success": True}

# In tests:
result = charge("ORD-1", "credit_card", 99.99, rng=lambda: 0.0)  # always fails
result = charge("ORD-1", "credit_card", 99.99, rng=lambda: 1.0)  # always succeeds
```

**Phase to address:** Phase 5 (Mock Failure Injection)

---

## Domain 6: Playwright Testing

### Pitfall 13 — Port conflict and shared state between test runs
**Severity:** Moderate

**What goes wrong:** Two Playwright test runs start simultaneously (or a previous run left the server running) → port 8000 already in use. Tests intermittently fail with connection errors.

Also: test A places an order; test B looks up orders and sees test A's data.

**Prevention:**
```python
# conftest.py
import pytest
from app.seed import seed
from app.state import reset_stores

@pytest.fixture(autouse=True)
def clean_state():
    reset_stores()
    seed()
    yield
    reset_stores()

# Use pytest-anyio + find-free-port for server fixture:
@pytest.fixture(scope="session")
def server_port():
    import socket
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]
```

**Warning signs:** Tests pass in isolation but fail in suite; `Address already in use` errors.

**Phase to address:** Phase 7 (Evals + Automated Tests)

---

## Quick Reference — Phase Assignment

| Phase | Pitfalls to address |
|-------|---------------------|
| Phase 1: Scaffold + Seed | #11 (cold start) |
| Phase 2: Core Domain | #1 (inventory lock), #2 (dict iteration) |
| Phase 4: Chatbot Tools | #3 (iteration limit), #4 (tool_result), #5 (input validation), #7 (cross-user) |
| Phase 5: Failure Injection | #6 (root token), #12 (injectable RNG) |
| Phase 6: Observability | #8 (span nesting), #9 (PII), #10 (Langfuse crash) |
| Phase 7: Testing | #13 (port/state isolation) |
