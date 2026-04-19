# External Integrations

**Analysis Date:** 2026-04-18
**Status:** Planned/Intended — no source code implemented yet. This document reflects the spec-prescribed integrations from `spec_python.md`.

## APIs & External Services

**LLM:**
- Anthropic API — Claude model calls for all chatbot agent functionality
  - SDK/Client: `anthropic` Python SDK
  - Auth: `ANTHROPIC_API_KEY` environment variable
  - Usage: agent intent interpretation, tool selection, clarification questions, response summarization
  - Instrumented with Langfuse traces at generation level

**Observability:**
- Langfuse — LLM trace collection for agent, tool, and generation steps
  - SDK/Client: `langfuse` Python SDK
  - Auth: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` environment variables
  - Captures: request ID, session ID, user ID, agent input/output, tool calls, tool latency, tool success/failure, mock failure reason, model metadata, total request outcome
  - Used for: debugging failed checkouts, prompt injection attempts, slow tool calls, root instruction events

## Data Storage

**Databases:**
- None. No database is used.
- All data held in in-memory Python dicts and lists at module scope.
- In-memory stores: `users`, `products`, `carts`, `orders` — reset on every restart.

**File Storage:**
- Local filesystem only, for static assets (CSS, images) served by FastAPI.
- No cloud file storage.

**Caching:**
- None.

## Authentication & Identity

**Auth Provider:**
- Custom (no third-party auth service)
- Password hashing: `passlib[bcrypt]`
- Session tokens: `python-jose[cryptography]` (JWT) or `itsdangerous` (signed cookies)
- User records stored in in-memory `users` dict

## Mock Adapters (Internal — No Real External Integration)

**Payment Mock (`app/lib/mocks/payment.py`):**
- Simulates: Credit Card charge/refund, PayPal charge/refund, Apple Pay charge/refund
- No real payment processor (no Stripe, no PayPal SDK, no Apple Pay API)
- Interface:
  - `charge(order_id, payment_method, amount) -> dict`
  - `refund(order_id, payment_method, amount) -> dict`
- Failure injection: reads `FAILURE_CONFIG["payment"]` and rolls `random.random()` per call
- Failure response shape: `{"success": False, "code": "...", "message": "...", "retryable": True/False}`
- Emits Langfuse observability event on every call (success and failure)

**Warehouse Mock (`app/lib/mocks/warehouse.py`):**
- Simulates: inventory check, inventory reservation, order shipping, order cancellation
- No real warehouse or shipping provider integration
- Interface:
  - `get_available_quantity(product_id) -> int`
  - `reserve_inventory(order_id, items) -> dict`
  - `ship_order(order_id) -> dict`
  - `cancel_order(order_id) -> dict`
- Failure injection: reads `FAILURE_CONFIG["warehouse"]` and rolls `random.random()` per call
- Emits Langfuse observability event on every call (success and failure)

## Configurable Failure Injection

**Config location:** `config.py` — `FAILURE_CONFIG` dict (mutable at runtime)

**Default example config:**
```python
FAILURE_CONFIG = {
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

**Runtime updates:** Root instruction token (`[root]: ...` prefix) updates `FAILURE_CONFIG` live during demo/dev mode (`APP_MODE=dev` only). Every root instruction is logged to Langfuse.

## Monitoring & Observability

**LLM Tracing:**
- Langfuse Python SDK — all agent/tool/generation steps instrumented
- Trace fields: request ID, session ID, user ID, agent I/O, tool calls, tool latency, mock failure reason

**Error Tracking:**
- None (no Sentry or equivalent). Errors surface via Langfuse traces and Python logging.

**Logs:**
- Python standard `logging` module; structured where possible for Langfuse correlation.

## CI/CD & Deployment

**Hosting:**
- Local development (primary use case)
- Compatible with: Fly.io, Railway, Render (single-process ASGI only — in-memory state not safe for multi-worker)

**CI Pipeline:**
- Not specified. `pytest` and `playwright` run locally or in any CI runner.

## Webhooks & Callbacks

**Incoming:**
- None. No real external service sends webhooks.

**Outgoing:**
- None. All external calls are outbound API calls (Anthropic, Langfuse), not webhook-based.

## Environment Configuration

**Required environment variables (names only):**
- `ANTHROPIC_API_KEY` — Anthropic API access
- `LANGFUSE_PUBLIC_KEY` — Langfuse project public key
- `LANGFUSE_SECRET_KEY` — Langfuse project secret key
- `LANGFUSE_HOST` — Langfuse host URL (e.g. `https://cloud.langfuse.com`)
- `SECRET_KEY` — signing key for session cookies or JWTs
- `APP_MODE` — `dev` or `prod`; controls root instruction availability

**Secrets location:**
- `.env` file (local development); never committed to version control

---

*Integration audit: 2026-04-18*
