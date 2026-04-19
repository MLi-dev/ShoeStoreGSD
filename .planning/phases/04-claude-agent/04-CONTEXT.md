# Phase 4: Claude Agent - Context

**Gathered:** 2026-04-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire the LLM agent layer — tool registry, agentic loop, guardrails, and chat endpoint — so every shopping and support action available via the web UI is also available conversationally through a Claude-powered `/chat` page. Phase is complete when a logged-in user can complete the full purchase lifecycle and all support flows through chat, with guardrails enforcing scope and graceful mock failure handling.

</domain>

<decisions>
## Implementation Decisions

### Chat UI
- **D-01:** Dedicated `/chat` page — full-page chat accessible from the navbar. No widget, no overlay, no sidebar embedding. Clean, focused conversation experience.
- **D-02:** Markdown rendering via `marked.js` loaded from CDN — no build step. Agent responses may use **bold**, bullet lists, and code spans for readability (product lists, order details). User messages rendered as plain text.
- **D-03:** Transcript only — chat page shows user/agent message history only. No cart widget, no quick-links sidebar. Navbar provides navigation back to /products, /cart, /orders.

### System Prompt & Context
- **D-04:** User identity only injected into system prompt — Claude receives the authenticated user's name and email at conversation start. Cart contents and order list are discovered on demand via tool calls (never pre-loaded). Avoids stale context mid-conversation.
- **D-05:** Strict persona — system prompt declares: "You are a helpful ShoeStore shopping assistant. You help users search for shoes, manage their cart, check out, and manage their orders. Politely decline anything outside this scope." Scope enforcement is in-prompt, not a separate call.

### Guardrail Enforcement
- **D-06:** Two-layer guardrails: (1) instruction-based — system prompt scope declaration handles off-topic refusals via Claude's own judgment; (2) regex pattern matching in `app/lib/guardrails/guardrails.py` — catches known prompt injection patterns (e.g., "ignore previous instructions", "disregard your system prompt", "pretend you are") before the message reaches the agent loop.
- **D-07:** Scope violation response — polite refusal with redirect: "I can only help with ShoeStore shopping and orders. Is there something I can help you find or order?" No stack trace, no error code exposed to user. Injection attempts that are caught pre-flight return the same message shape.

### Conversation History
- **D-08:** In-memory per session — conversation history stored in a server-side dict keyed by `user_id`. Consistent with the project's in-memory-only design. Lost on server restart. No serialization.
- **D-09:** Full history per request — all messages from the session are passed to the Anthropic API on each call. The `MAX_TURNS=10` hard cap in the agent loop keeps context bounded. No sliding window truncation.
- **D-10:** Page refresh clears history — consistent with in-memory design. Chat page reloads empty. This is expected and acceptable for a demo.

### Agent Loop (from prior phases — locked)
- **D-11:** `AsyncAnthropic` client only — sync client blocks the event loop. No streaming (conflicts with tool-use loop). Return complete responses.
- **D-12:** `for _ in range(MAX_TURNS)` hard cap — agent loop terminates after 10 iterations. Final iteration returns whatever partial response exists.
- **D-13:** Tool dispatcher always appends `tool_result` to messages even on exception — prevents Anthropic API crash from malformed message arrays.
- **D-14:** `[root]:` prefix parsed and stripped in the chat route handler before the messages array is built — never reaches the LLM. Gated on `DEMO_MODE`.
- **D-15:** Cross-user access prevention — `user_id` resolved exclusively from the authenticated session (JWT cookie), never from the user's message content.

### Claude's Discretion
- Exact system prompt wording beyond the persona and scope declaration
- Whether the chat route uses `get_current_user_web` (redirects on 401) or a hybrid that returns JSON for AJAX
- Whether to use `asyncio.Lock` on the in-memory history dict (recommended yes — consistent with rest of codebase)
- Tool response verbosity (how much detail each tool returns to Claude)
- Whether `set_failure_mode` tool is exposed in Phase 4 (may belong to Phase 5 root token flow instead)
- CSS styling details for the chat UI (Bootstrap bubbles, color contrast, input field placement)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Spec & Requirements
- `/Users/matthew/Downloads/spec_python.md` — canonical requirements source; Phase 4 covers CHAT-01 through CHAT-05
- `.planning/REQUIREMENTS.md` — CHAT-01: shopping flows, CHAT-02: support flows, CHAT-03: clarifying questions, CHAT-04: scope enforcement, CHAT-05: mock failure recovery

### Planning & Architecture
- `.planning/ROADMAP.md` — Phase 4 success criteria (5 items), goal statement
- `.planning/codebase/CONVENTIONS.md` — agent tool function signatures, guardrail patterns, root instruction token rules, error response shape, asyncio.Lock patterns
- `.planning/codebase/STRUCTURE.md` — where agent files go (`app/lib/agent/`), guardrails (`app/lib/guardrails/`), chat route (`app/api/chat_router.py`), chat template (`app/web/templates/chat/`)

### Prior Phase Artifacts (patterns to follow)
- `.planning/phases/03-web-ui-rest-api/03-CONTEXT.md` — auth dependency pattern (D-01: JWT httpOnly cookie, `get_current_user_web`/`get_current_user_api`), Bootstrap/CDN approach, thin route handler pattern
- `app/lib/auth/dependencies.py` — `get_current_user_web` and `get_current_user_api` — reuse for chat route auth
- `app/lib/cart/cart_service.py` — cart operations called by agent tools
- `app/lib/orders/order_service.py` — order operations (status, cancel, return) called by agent tools
- `app/lib/catalog/catalog_service.py` — product search and detail called by agent tools
- `app/lib/mocks/payment_mock.py` — failure behavior the agent must handle gracefully
- `app/lib/mocks/warehouse_mock.py` — failure behavior the agent must handle gracefully
- `config.py` — `FAILURE_CONFIG`, `DEMO_MODE` flag

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/lib/auth/dependencies.py` — `get_current_user_web` (redirects) and `get_current_user_api` (401) — use for chat route, likely `get_current_user_web` since it's a page
- `app/lib/cart/cart_service.py` — all cart operations already implemented; tools wrap these
- `app/lib/orders/order_service.py` — place, cancel, return, get, list with ownership enforcement; tools wrap these
- `app/lib/catalog/catalog_service.py` — search and get_product; tools wrap these
- `app/lib/auth/auth_service.py` — reset_password for the password reset tool
- `app/web/templates/base.html` — Bootstrap 5 base template; chat.html extends this
- `app/lib/mocks/` — warehouse and payment mocks already wired; agent surfaces their error responses

### Established Patterns
- Route handlers are thin: call service function → check `success` → return or raise `HTTPException`
- Error shape: `{"success": bool, "code": str, "message": str, "retryable": bool}`
- `asyncio.Lock` on all mutable in-memory state
- Bootstrap 5 from CDN — no build step, consistent with Phase 3 templates
- `from config import FAILURE_CONFIG, DEMO_MODE` read at call time

### Integration Points
- `main.py` — add `app.include_router(chat_router)` for the new chat router
- `app/api/chat_router.py` — new file: POST /chat/message endpoint, GET /chat page route
- `app/web/templates/chat/chat.html` — new Jinja2 template extending base.html
- `app/lib/agent/agent.py` — new file: async agent runner with tool dispatch loop
- `app/lib/agent/tools.py` — new file: all tool functions wrapping existing services
- `app/lib/guardrails/guardrails.py` — new file: injection detection regex patterns
- `app/lib/agent/history.py` — new file (or dict in agent.py): in-memory conversation history store

</code_context>

<specifics>
## Specific Ideas

- The chat route POST endpoint should return JSON (agent response text) so the frontend JS can append messages without a full page reload — AJAX pattern, not a form POST redirect.
- The history store should be keyed by `user_id` (from JWT), not session ID — consistent with the rest of the codebase which uses user_id as the primary key.
- marked.js should be loaded from a CDN `<script>` tag in base.html or in the chat template only, and called after each agent message is appended to the DOM.
- The tool set from CONVENTIONS.md is the definitive list: `search_products`, `get_product_details`, `add_to_cart`, `view_cart`, `checkout`, `place_order`, `check_order_status`, `cancel_order`, `return_order`, `reset_password`. The `set_failure_mode` tool belongs in Phase 5 (root token flow).

</specifics>

<deferred>
## Deferred Ideas

- `set_failure_mode` tool — belongs in Phase 5 with the `[root]:` token flow and live failure config control.
- Langfuse tracing (agent/tool/generation traces) — deferred to v2 per REQUIREMENTS.md.
- Typing indicator / streaming display — conflicts with tool-use loop; deferred to v2.
- Chat history persistence across server restarts — in-memory only by design.

</deferred>

---

*Phase: 04-claude-agent*
*Context gathered: 2026-04-19*
