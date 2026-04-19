# Phase 4: Claude Agent - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-19
**Phase:** 04-claude-agent
**Areas discussed:** Chat UI, System prompt & context, Guardrail enforcement, Conversation history

---

## Chat UI

| Option | Description | Selected |
|--------|-------------|----------|
| Dedicated /chat page | Full-page chat at /chat, linked from navbar | ✓ |
| Floating widget on all pages | Chat button visible site-wide, slide-in panel | |
| Embedded on sidebar | Chat sidebar on product/order pages | |

**User's choice:** Dedicated /chat page

---

| Option | Description | Selected |
|--------|-------------|----------|
| Plain text only | Simple, no formatting risk | |
| Markdown rendered | Agent can use bold, lists, code. marked.js from CDN | ✓ |
| Structured cards per message type | Custom HTML cards for products, orders, etc. | |

**User's choice:** Markdown rendered (marked.js from CDN)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Transcript only | Clean chat window, navbar links elsewhere | ✓ |
| Transcript + current cart summary | Small cart widget alongside chat | |
| Transcript + links to web pages | Quick links to /products, /cart, /orders | |

**User's choice:** Transcript only

---

## System Prompt & Context

| Option | Description | Selected |
|--------|-------------|----------|
| User identity only | Name/email in system prompt; cart/orders via tools | ✓ |
| Full context injection — user + cart + orders | Pre-load current state into system prompt | |
| No user context — tools only | Generic persona; all info via tool calls | |

**User's choice:** User identity only (name/email injected; cart/orders discovered on demand)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Shoe store assistant, strict scope | "You are a helpful ShoeStore shopping assistant…" | ✓ |
| Friendly assistant, soft scope | Warm persona; scope mentioned but not enforced via prompt | |
| Tool-only agent, minimal persona | Minimal system prompt; Claude figures out persona | |

**User's choice:** Shoe store assistant, strict scope

---

## Guardrail Enforcement

| Option | Description | Selected |
|--------|-------------|----------|
| Instruction-based — system prompt enforces | Claude's judgment + regex for injection heuristics | ✓ |
| Pre-flight LLM check before tool dispatch | Classifier call before agent loop — extra LLM call | |
| Keyword blocklist in guardrails.py | Python-side blocklist — fast but brittle | |

**User's choice:** Instruction-based (system prompt) + regex injection detection in guardrails.py

---

| Option | Description | Selected |
|--------|-------------|----------|
| Polite refusal with redirect | "I can only help with ShoeStore…" — no error code | ✓ |
| Hard stop — generic error message | Fixed refusal string, less helpful | |
| Refusal + log the attempt | Same refusal but logs at WARNING with user_id | |

**User's choice:** Polite refusal with redirect

---

| Option | Description | Selected |
|--------|-------------|----------|
| Regex pattern matching in guardrails.py | Known patterns caught pre-agent. Fast, covers common attacks | ✓ |
| Rely on system prompt alone | Trust Claude's instruction-following | |
| Dedicated injection detection module | Comprehensive pattern library — overkill for demo | |

**User's choice:** Regex pattern matching in guardrails.py

---

## Conversation History

| Option | Description | Selected |
|--------|-------------|----------|
| In-memory per session key | Server-side dict keyed by user_id. Lost on restart | ✓ |
| Client-side in the browser | History sent with each POST. Stateless server | |
| FastAPI session (itsdangerous) | History in signed cookie. Size-limited | |

**User's choice:** In-memory per session key (user_id)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Full history up to MAX_TURNS limit | All messages from session, bounded by 10-turn cap | ✓ |
| Last N messages (sliding window) | Last 6–10 messages to control context size | |
| No history — each message is independent | Stateless; breaks multi-turn flows | |

**User's choice:** Full history up to MAX_TURNS limit

---

| Option | Description | Selected |
|--------|-------------|----------|
| History lost — fresh start | Page reload clears chat. Consistent with in-memory design | ✓ |
| History preserved in session | Serialize history to cookie or client store | |

**User's choice:** History lost on page refresh

---

## Claude's Discretion

- Exact system prompt wording beyond persona and scope declaration
- Whether chat route uses `get_current_user_web` or a hybrid for AJAX
- `asyncio.Lock` on history dict (recommended yes)
- Tool response verbosity
- Whether `set_failure_mode` tool is in Phase 4 (deferred to Phase 5)
- CSS styling details for chat UI

## Deferred Ideas

- `set_failure_mode` agent tool — belongs in Phase 5 root token flow
- Langfuse tracing — deferred to v2
- Typing indicator / streaming — conflicts with tool-use loop, deferred to v2
