# Research: Architecture — Python FastAPI + Claude AI Demo Store

**Date:** 2026-04-18
**Confidence:** HIGH

---

## Summary

Single FastAPI application with two client surfaces (web UI + chat UI), a domain service layer, mock adapters, a Claude tool-use agent, and a Langfuse observability wrapper. Build in 4 waves so each wave is independently runnable and testable.

---

## Component Boundaries

```
┌────────────────────────────────────────────────────────────┐
│                        FastAPI App                         │
│                                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────────────┐ │
│  │  Web Router  │  │  API Router  │  │   Chat Router      │ │
│  │ (Jinja2 UI) │  │ (REST CRUD)  │  │ (SSE stream POST)  │ │
│  └──────┬──────┘  └──────┬───────┘  └────────┬───────────┘ │
│         │                │                   │              │
│         └────────────────┴───────────────────┘              │
│                          │                                  │
│         ┌────────────────▼───────────────────────┐         │
│         │           Domain Services               │         │
│         │  auth | catalog | cart | orders | support│         │
│         └────────────────┬───────────────────────┘         │
│                          │                                  │
│         ┌────────────────┴───────────────────────┐         │
│         │           In-Memory Stores              │         │
│         │  users | products | carts | orders      │         │
│         └────────────────────────────────────────┘         │
│                                                            │
│  ┌─────────────────────┐  ┌─────────────────────────────┐ │
│  │   Mock Adapters      │  │   Agent Layer                │ │
│  │  payment | warehouse │  │  runner | tool_registry      │ │
│  │  + failure injection │  │  + guardrails + root token   │ │
│  └─────────────────────┘  └─────────────────────────────┘ │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │   Observability (lib/observability/tracer.py)       │   │
│  │   Langfuse trace/span/generation wrappers           │   │
│  └────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

---

## Streaming Chat Endpoint

Use `StreamingResponse` with an `async def` generator yielding SSE `data:` lines:

```python
# app/api/chat.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

chat_router = APIRouter()

@chat_router.post("/chat/stream")
async def chat_stream(request: ChatRequest, session: Session = Depends(get_session)):
    async def event_generator():
        async for chunk in agent_runner.run_stream(request.message, session):
            yield f"data: {json.dumps({'text': chunk})}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Also provide a non-streaming endpoint for tests
@chat_router.post("/chat")
async def chat(request: ChatRequest, session: Session = Depends(get_session)):
    result = await agent_runner.run(request.message, session)
    return {"response": result}
```

---

## Claude Agent Loop

Implement a single `for _ in range(MAX_TURNS)` loop driven by `stop_reason`. No framework (LangChain, LlamaIndex) needed or desirable.

```python
# app/lib/agent/runner.py
MAX_AGENT_TURNS = 10

class AgentRunner:
    def __init__(self, client: AsyncAnthropic, tool_registry: ToolRegistry):
        self.client = client
        self.tools = tool_registry

    async def run(self, user_message: str, session: Session) -> str:
        messages = session.history + [{"role": "user", "content": user_message}]

        for _ in range(MAX_AGENT_TURNS):
            response = await self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                tools=self.tools.schemas(),
                messages=messages,
            )

            if response.stop_reason == "end_turn":
                text = next(b.text for b in response.content if b.type == "text")
                session.history.extend([
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": text},
                ])
                return text

            if response.stop_reason == "tool_use":
                tool_results = await self.tools.dispatch(response.content, session)
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})

        return "I'm having trouble completing that request. Please try again."
```

---

## In-Memory Async Safety

Python's GIL makes single `dict[key] = value` assignments safe. Only **multi-step read-modify-write** sequences need `asyncio.Lock`.

| Operation | Needs Lock? | Why |
|-----------|-------------|-----|
| `catalog_store[id]` read | No | Single atomic read |
| `orders_store[id] = order` | No | Single atomic write |
| Reserve inventory (check + decrement) | **Yes** | 2-step read-modify-write |
| Order status transition | **Yes** | Read current state + validate + write |
| Cart concurrent add | **Yes** | Read list + append |
| `FAILURE_CONFIG` update from root token | **Yes** | Read + write under demo concurrency |

Lock placement — lock lives in the same module as the store it protects:

```python
# app/lib/orders/store.py
from asyncio import Lock

orders_store: dict[str, Order] = {}
_orders_lock = Lock()

async def create_order(order: Order) -> Order:
    async with _orders_lock:
        orders_store[order.id] = order
        return order
```

---

## Mock Adapter Pattern

```python
# app/lib/mocks/warehouse.py
import random
from app.config import FAILURE_CONFIG
from app.lib.observability.tracer import get_tracer

def _should_fail(key: str, *, rng=random.random) -> bool:
    prob = FAILURE_CONFIG.get("warehouse", {}).get(key, 0.0)
    return rng() < prob

async def reserve_inventory(order_id: str, items: list, *, rng=random.random) -> dict:
    if _should_fail("out_of_stock", rng=rng):
        return {"success": False, "code": "OUT_OF_STOCK", "message": "Item out of stock", "retryable": False}
    # ... actual reservation logic
    return {"success": True}
```

---

## Langfuse Tracing Layer

All Langfuse SDK imports are isolated in `lib/observability/tracer.py`. Business logic and mock adapters call tracer functions that accept plain dicts. `TraceContext` is a dataclass created per request and passed as a parameter — **never stored in module-level state**.

```python
# app/lib/observability/tracer.py
from dataclasses import dataclass, field
from langfuse import Langfuse

_langfuse: Langfuse | None = None

@dataclass
class TraceContext:
    trace: object = None
    agent_span: object = None

def get_tracer() -> Langfuse:
    global _langfuse
    if _langfuse is None:
        _langfuse = Langfuse()  # reads LANGFUSE_* env vars
    return _langfuse

# Usage in agent runner:
ctx = TraceContext()
ctx.trace = get_tracer().trace(name="chat", user_id=session.user_id)
with ctx.trace.span(name="agent_loop") as ctx.agent_span:
    result = await runner.run(message, session, trace_ctx=ctx)
```

---

## Build Order (Wave Structure)

### Wave 1: Models + Stores + Domain + Seed (no HTTP, no LLM)
- `app/lib/auth/` — User model, password hash, auth service
- `app/lib/catalog/` — Product model, search service
- `app/lib/cart/` — Cart model, cart service
- `app/lib/orders/` — Order model, order service (with asyncio.Lock)
- `app/lib/seed/` — Seed function (populates all stores)
- `config.py` — Settings, FAILURE_CONFIG
- `main.py` — FastAPI app skeleton with lifespan

**Testable:** Pure Python unit tests, no HTTP, no LLM

### Wave 2: Mock Adapters + API Routers + Web UI
- `app/lib/mocks/warehouse.py` + `app/lib/mocks/payment.py`
- `app/api/auth.py`, `app/api/products.py`, `app/api/cart.py`, `app/api/orders.py`
- `app/web/` — Jinja2 templates for all web pages

**Testable:** `TestClient` route tests, Playwright web UI tests

### Wave 3: Agent Tools + Chat Endpoint + Guardrails
- `app/lib/agent/tool_registry.py` — tool definitions + schemas
- `app/lib/agent/runner.py` — Claude agent loop
- `app/lib/guardrails/` — scope enforcement, root token parser
- `app/api/chat.py` — `/chat` and `/chat/stream` endpoints

**Testable:** Agent unit tests with mocked Anthropic client, chat endpoint tests

### Wave 4: Observability + Evals + Playwright
- `app/lib/observability/tracer.py` — Langfuse wiring
- `app/evals/` — Eval datasets (positive, negative, adversarial)
- `tests/e2e/` — Playwright tests for all core flows

**Testable:** Full E2E flows, eval runners

---

## Dependency Graph

```
config.py → (nothing)
models/ → config.py
stores/ → models/
seed/ → stores/ + models/
domain services/ → stores/ + models/
mocks/ → config.py (FAILURE_CONFIG) + observability/
api routers/ → domain services/ + mocks/
agent/ → api routers/ (calls same domain services) + observability/
observability/ → (langfuse only)
main.py → everything
```

---

## Anti-Patterns to Avoid

| Anti-Pattern | Why |
|--------------|-----|
| Storing `TraceContext` in module-level state | Breaks under concurrent requests — always pass as parameter |
| Importing `langfuse` outside `tracer.py` | Scatters SDK dependency, makes `NoopSpan` fallback impossible |
| Using `LangChain` for agent orchestration | Hides the tool-use loop, harder to trace and debug |
| `FAILURE_CONFIG` as a plain module-level dict modified without a lock | Race condition when root token update hits during a request |
| Calling domain services directly from agent tool functions | Bypasses auth/ownership checks — always go through the service layer |
