# Feature Landscape

**Domain:** AI-powered demo e-commerce store (shoe store) with agentic chatbot
**Researched:** 2026-04-18
**Confidence:** HIGH — spec is authoritative; findings derived from spec analysis plus established LLM chatbot design patterns

---

## Table Stakes

Features the chatbot must have or the demo feels broken. Each one represents a gap that a live observer will immediately notice.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Natural language product search | Core reason to have a chatbot at all; "find me running shoes under $100" must work | Medium | Calls `search_products`; agent must map vague intent to catalog query |
| Add to cart via conversation | If the chatbot can find a product but can't add it, the flow dead-ends | Low | `add_to_cart` tool; agent must resolve product ID from prior search context |
| Cart visibility in conversation | Users ask "what's in my cart?" constantly during shopping flows | Low | `view_cart` tool; simple but omitting it breaks conversational continuity |
| Checkout confirmation loop | Agent must collect payment method, confirm total, then execute — not skip straight to charge | Medium | Two-step: confirm intent → call `checkout` + `place_order`; skipping feels reckless |
| Order status lookup | "Where is my order?" is the #1 support query in any e-commerce context | Low | `check_order_status` by order ID; agent must handle missing order ID gracefully |
| Clarification questions for missing info | Without this the chatbot either fails silently or hallucinates intent | Medium | e.g. "Cancel my order" → agent asks which order; spec explicitly requires this |
| Graceful error recovery | Mock failures are intentionally injected; agent must communicate failure clearly and suggest next step | Medium | "Payment failed — would you like to try a different method?" not a raw stack trace |
| Scope enforcement (stay on topic) | If the chatbot helps with cookie recipes, the demo looks unprofessional and the LLM safety story collapses | Medium | Reject off-topic requests politely; spec explicitly lists cookie recipes, math problems |
| Authenticated vs unauthenticated awareness | Cart and order actions must fail gracefully when user is not logged in, not silently produce wrong data | Low | Agent must check auth state before calling protected tools |
| Order cancellation flow | Support flow; must verify ownership and cancellation eligibility before attempting | Medium | Spec requires ownership check + status check before warehouse cancel mock |
| Return order flow | Paired with cancellation; missing it makes the support story half-complete | Medium | Eligibility: paid/processing status and above per PROJECT.md |
| Password reset via chat | Listed in spec user stories; omitting creates asymmetry vs web UI support features | Low | `reset_password` tool; simple but completes the support surface area |
| Typo and broken grammar tolerance | Spec explicitly calls out "Cansel odrer", abbreviations, implicit intent | Medium | Claude handles this naturally but system prompt must not overconstrain phrasing |
| Session-scoped conversation memory | Agent must remember what was searched and selected within a session | Medium | Maintained via Anthropic SDK message history; required for multi-turn shopping flows |

---

## Differentiators

Features that elevate the demo from functional to impressive. Not expected by default, but create a memorable experience.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Multi-turn product refinement | "Show me something cheaper" after a search result — agent remembers prior context and narrows | Medium | Requires referencing prior tool results in follow-up; showcases genuine agent reasoning |
| Proactive upsell / cross-sell suggestion | "You added trail runners — want to see wool hiking socks?" — demonstrates agent initiative | Medium | Triggered after `add_to_cart`; must feel helpful not pushy; good demo moment |
| Failure recovery with alternatives | After payment failure, agent proactively offers "Try PayPal instead?" — not just "it failed" | Medium | Requires agent to reason about retryable failures and available payment methods |
| Emotional tone matching | Calm response to angry/caps-lock user; spec calls out profanity, all-caps, sarcasm | Medium | System prompt instruction; Claude does this well with explicit guidance |
| Root instruction acknowledgment | When `[root]: make payment fail 100%` is applied, agent should confirm the config change clearly | Low | `set_failure_mode` tool; good demo operator affordance |
| Structured cart/order confirmation display | Rich-ish text output: itemized cart with prices, order summary before checkout — not just "done" | Low | No frontend rendering needed; well-formatted markdown in the chat transcript is enough |
| Disambiguation for variant selection | "I want the trail runners" → "We have those in sizes 8–13, which size?" — collects missing variant | Medium | Requires agent to identify incomplete product spec before adding to cart |
| Graceful degradation explanation | When the warehouse mock rejects, explain why (out of stock, reservation failed) and what the user can do | Low | Already covered by error recovery but distinguishing the *reason* is the differentiator |
| Langfuse trace visibility during demo | Demo operator can show traces in Langfuse mid-demo — tool calls, latencies, failures — as a live teaching moment | High | Requires Langfuse integration to be instrumented correctly; very high demo value for the target audience (AI engineers) |
| Replay of failed conversation for debugging | Transcript export or Langfuse session link for post-demo analysis | High | Nice-to-have in spec; valuable for the AI engineer persona |

---

## Anti-Features

Things that look valuable for a demo but actively make it worse. Deliberately not building these.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Streaming token output | Looks impressive technically but breaks the tool-call agentic loop; intermediate streaming before tool results is confusing UX | Return complete responses after tool execution completes |
| Persistent memory across sessions | In-memory design is intentional; adding cross-session memory creates state debugging hell and demo unpredictability | Let each restart be a clean slate; seed data handles this |
| Fuzzy order ownership (access any order) | Spec red-team case explicitly: agent must reject cross-user order access; "helpful" access would be a security demo failure | Strictly scope order lookups to `current_user.id` |
| Auto-checkout without confirmation | Agent that places an order without explicit user confirmation feels alarming and untrustworthy | Always require explicit user confirmation step before calling `place_order` |
| Free-form failure config via chat for end users | Root token mechanism is demo-operator-only; exposing failure config to normal chat users breaks the safety story | Gate `set_failure_mode` behind `[root]:` prefix parsed before normal execution |
| LLM-generated product descriptions on the fly | Hallucinated product specs undermine trust; the catalog has real seed data | Use catalog data verbatim; agent can paraphrase but not invent specs |
| Markdown-heavy chat output | Overly formatted responses (headers, tables) look awkward in a chat bubble and signal "I'm outputting a document" | Prefer conversational prose; use light formatting (bold, bullet lists) only where it aids clarity |
| Retry loops without user input | Agent autonomously retrying a failed payment 3 times without asking feels robotic and opaque | One attempt, report failure, ask user what to do next |
| Broad tool exposure (all tools, always) | Giving the agent access to `set_failure_mode` in unauthenticated or end-user sessions is a prompt injection risk | Scope tool availability by auth state and demo mode flag |
| Verbose internal reasoning in responses | Chain-of-thought exposed in the chat transcript ("First I will call search_products...") erodes trust and reads as junk | Keep internal reasoning internal; surface only the result and the next question |

---

## Feature Dependencies

```
auth (login/signup)
  └── view_cart            (cart is user-scoped)
  └── add_to_cart          (cart is user-scoped)
  └── checkout             (requires authenticated cart)
      └── place_order      (requires completed checkout)
          └── check_order_status  (requires an order to exist)
          └── cancel_order        (requires an order in cancelable state)
          └── return_order        (requires an order in returnable state)

search_products            (unauthenticated OK)
  └── get_product_details  (unauthenticated OK)
      └── add_to_cart      (requires auth)

[root]: token parsing
  └── set_failure_mode     (demo mode only, pre-execution)

Langfuse instrumentation
  └── all tool calls       (wraps all agent actions; not in critical path but must not break them)
```

---

## Conversational Patterns by Flow

### Product Search

**Pattern:** Query → Results → Selection → Detail → Add to cart

- Agent calls `search_products` with extracted query terms
- Presents top 3–5 results conversationally, not as a data dump
- Asks "Want details on any of these?" or "Which would you like to add?"
- If query returns zero results: says so clearly, asks if they want to try different terms
- If product has variants (size/color): before adding to cart, collects the missing variant

**What breaks this flow:** Silent empty results, dumping all 20 products, adding to cart before confirming size

### Checkout

**Pattern:** Cart review → Payment method → Confirmation → Execute → Report outcome

- Agent surfaces cart contents and total before asking for payment method
- Collects payment method if not stated ("Would you like to pay by credit card, PayPal, or Apple Pay?")
- Confirms: "Ready to place your order for $X via PayPal?" before calling `checkout` + `place_order`
- On success: order ID, status, brief confirmation
- On failure: specific failure type, retryable suggestion if applicable

**What breaks this flow:** Skipping confirmation, opaque error messages, not offering alternatives after failure

### Order Support

**Pattern:** Intent detection → Order ID collection → Eligibility check → Action → Outcome

- Agent asks for order ID if not provided
- Calls `check_order_status` first to verify state and ownership
- For cancel: checks status is not already shipped/canceled before proceeding
- For return: checks status is paid/processing or above
- Reports outcome clearly: "Your order #12345 has been canceled and a refund initiated"

**What breaks this flow:** Acting on ambiguous order references, not checking eligibility, hiding the actual status

---

## Guardrail / Safety Features (Table Stakes for LLM Chatbot)

| Guardrail | Why Table Stakes | Implementation |
|-----------|-----------------|----------------|
| Scope rejection | Off-topic requests (cookie recipes, math) erode trust and expose the LLM's general capabilities in an uncontrolled way | System prompt: explicit scope definition + rejection instruction |
| Prompt injection detection | Spec red-team dataset explicitly includes injection attempts; a demo that can be jailbroken is embarrassing | Pre-execution parsing of input; `[root]:` token only valid in demo mode; system prompt hardening |
| Cross-user data isolation | Agent must never return another user's orders, cart, or personal data | All data store lookups scoped to `current_user.id`; never pass user ID from user input |
| Tool availability scoping | `set_failure_mode` must not be callable in normal user context | Tool list is dynamic based on auth state + demo mode flag; not exposed in production mode |
| Ownership verification before destructive actions | Cancel and return must verify the order belongs to the requesting user | `check_order_status` includes user_id match before cancel/return tools proceed |
| Graceful auth-gate messaging | Attempting cart/order actions when unauthenticated should produce a clear, helpful message — not a 401 JSON error | Agent handles tool errors and translates to conversational responses |

---

## MVP Feature Set Recommendation

Build in this order — each layer unblocks the next:

**Layer 1 — Core shopping loop (must ship first)**
1. `search_products` + `get_product_details` (unauthenticated OK)
2. Auth gate (login required for cart/order)
3. `add_to_cart` + `view_cart`
4. `checkout` + `place_order` with confirmation step
5. Basic scope enforcement in system prompt

**Layer 2 — Support loop (completes the demo story)**
6. `check_order_status`
7. `cancel_order` with eligibility check
8. `return_order` with eligibility check
9. `reset_password`

**Layer 3 — Demo quality (makes it impressive)**
10. Graceful failure recovery messaging
11. `set_failure_mode` via `[root]:` token
12. Langfuse instrumentation on all tool calls
13. Variant/size disambiguation before add-to-cart
14. Emotional tone handling in system prompt

**Defer to nice-to-have:**
- Cross-sell suggestions (add after Layer 3 stabilizes)
- Transcript replay viewer
- Admin debug panel for failure config

---

## Sources

- Spec derived from: `/Users/matthew/Downloads/spec_python.md` (canonical)
- Project context: `/Users/matthew/Dev/ShoeStoreGSD/.planning/PROJECT.md`
- Confidence: HIGH for all table stakes and anti-features (spec-grounded); MEDIUM for differentiators (pattern-based, not externally verified due to web search unavailability)
