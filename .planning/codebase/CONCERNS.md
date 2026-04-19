# Codebase Concerns

**Analysis Date:** 2026-04-18

> Greenfield project — concerns are derived from the spec at `/Users/matthew/Downloads/spec_python.md`.
> No source code exists yet. All items below represent risks, open questions, and design decisions
> that need resolution before or during implementation.

---

## Security Considerations

**Root instruction token accessible to end users:**
- Risk: The `[root]:` prompt syntax modifies live `FAILURE_CONFIG` at runtime. If not gated, any user can type `[root]: disable all failures` and override demo behaviour or escalate privileges.
- Files: `app/lib/agent/` (not yet created), `config.py` (not yet created)
- Current mitigation: Spec says root instructions must only work in demo/dev mode and must be stripped before normal prompt processing.
- Recommendations: Parse and strip root instructions in a dedicated pre-processing step that runs before the LLM sees the message. Gate the parser behind an env flag (`DEMO_MODE=true`). Never forward raw user input to `set_failure_mode` without validation. Log every invocation to Langfuse.

**Prompt injection via chatbot input:**
- Risk: A user can craft a message designed to override system/operator instructions, impersonate the operator role, or exfiltrate other users' session data. The spec explicitly lists prompt injection as a required red-team test case.
- Files: `app/lib/agent/` (not yet created), `app/lib/guardrails/` (not yet created)
- Current mitigation: Spec requires a `guardrails` module for scope enforcement and injection detection.
- Recommendations: Enforce a hard separation between the system prompt (operator-controlled), conversation history (user-controlled), and root instructions (env-gated). Do not interpolate raw user strings into the system prompt. Add a guardrail layer that rejects messages matching known injection patterns before forwarding to the LLM.

**Password hashing algorithm:**
- Risk: Using `hashlib` directly or a weak algorithm (MD5, SHA-1) for `User.password_hash` would be a critical vulnerability even in a demo context, since test credentials may be reused across environments.
- Files: `app/lib/auth/` (not yet created)
- Current mitigation: Spec recommends `passlib` for password hashing.
- Recommendations: Use `passlib[bcrypt]` or `passlib[argon2]` exclusively. Never store plaintext passwords or reversible hashes. The `User` dataclass field is named `password_hash` — enforce this by making the auth module the only place that writes to it.

**Cross-user order access:**
- Risk: The agent's `check_order_status`, `cancel_order`, and `return_order` tools accept an `order_id` parameter. Without ownership verification, a user can query or modify another user's order by guessing or enumerating IDs.
- Files: `app/lib/orders/` (not yet created), `app/lib/agent/` (not yet created)
- Current mitigation: Spec's Flow 3 (Cancel Order) explicitly includes "System verifies order ownership" as a step.
- Recommendations: All order-mutating tools must accept a `user_id` derived from the authenticated session — never from user input — and verify `order.user_id == session.user_id` before proceeding. Include a negative eval case for cross-user access.

---

## Concurrency

**In-memory state is not thread-safe:**
- Risk: FastAPI runs async workers. Shared Python dicts (`FAILURE_CONFIG`, order store, cart store, inventory) are not thread-safe. Concurrent requests can produce race conditions: double-charging, inventory going negative, or cart corruption.
- Files: `config.py` (not yet created), `app/lib/orders/` (not yet created), `app/lib/catalog/` (not yet created)
- Current mitigation: None specified in the spec.
- Recommendations: Wrap all mutations to shared in-memory stores in `asyncio.Lock()`. Define one lock per logical store (e.g., `_orders_lock`, `_inventory_lock`, `_cart_lock`, `_config_lock`). Keep critical sections short. For the failure config dict, use a dedicated `ConfigStore` class that owns its lock.

**Inventory decrement race condition:**
- Risk: Two simultaneous checkout requests for the last unit of a product can both pass the stock check before either decrements inventory, resulting in overselling.
- Files: `app/lib/catalog/` (not yet created), `app/lib/mocks/` (not yet created)
- Current mitigation: None.
- Recommendations: Wrap the check-and-decrement of `Product.inventory` in a single locked transaction. Never read inventory in one step and write it in a separate async step without holding the lock across both.

---

## Open Questions

**Web and chat session/auth model:**
- Question: Do the web UI and chat UI share a single backend session and auth model?
- Impact: If sessions are separate, a user authenticated via the web UI would not be recognised by the chatbot, and vice versa. The spec states "User identity available to chatbot context for authenticated actions" but does not specify the mechanism.
- Recommendation: Decide before implementing auth. Simplest approach: a single JWT or signed cookie issued by FastAPI that both the web router and the chat agent endpoint accept and decode. The agent receives `user_id` from the decoded token, not from user text.

**Payment and warehouse failure scope — session-scoped vs. global:**
- Question: When `FAILURE_CONFIG` is modified (via root instruction or config), does the change apply globally to all concurrent users or only to the session that issued it?
- Impact: Global scope is simpler but may interfere with multi-user demos. Session scope requires per-session config storage.
- Recommendation: Default to global (single shared dict) for simplicity. Document this clearly. If per-session scope is needed later, introduce a `session_overrides` dict keyed by session ID that shadows the global config.

**Return eligibility — which order statuses allow returns:**
- Question: Are returns allowed only after the order reaches `shipped` status?
- Impact: The `Order` dataclass includes `returned` as a valid `order_status` value, but the spec does not explicitly state which statuses are eligible for return. Flow 4 (Return Order) says "System verifies eligibility" without defining the rule.
- Recommendation: Define eligibility explicitly before implementing the return flow. Suggested rule: returns allowed only for orders in `shipped` status. Encode this as a constant (e.g., `RETURNABLE_STATUSES = {"shipped"}`) in `app/lib/orders/`.

**Root instruction persistence — current run vs. until reset:**
- Question: Should root instructions persist for the lifetime of the process, or should they reset between requests/sessions?
- Impact: Persistent instructions make demo scenarios predictable ("always fail payments for this demo"). Per-request instructions are safer but harder to sustain across a live demo.
- Recommendation: Persist for the lifetime of the process (in-memory global config). Provide a `[root]: reset` command that restores defaults. Document that a process restart always resets to defaults.

---

## Fragile Areas

**In-memory state reset on process restart:**
- Files: `app/lib/seed/` (not yet created), `main.py` (not yet created)
- Why fragile: Every process restart wipes all users, orders, carts, and products. Any test or demo that does not re-seed will encounter an empty store.
- Safe modification: The `seed.py` module must be idempotent (safe to call multiple times without duplicating data) and fast (no I/O, no network calls). Call it unconditionally at startup via a FastAPI `lifespan` event. Never rely on state persisting across restarts in tests.
- Test coverage: All integration tests must either call the seed loader in their fixture setup or mock the stores directly.

**`random.random()` in mock failure injection:**
- Files: `app/lib/mocks/` (not yet created)
- Why fragile: Using `random.random()` makes test outcomes non-deterministic. Tests that exercise failure paths will be flaky unless the RNG is seeded or replaced in tests.
- Safe modification: Accept an optional `rng` parameter in mock functions (or a mockable `random_func` callable). In tests, inject `lambda: 0.0` (always fail) or `lambda: 1.0` (always succeed). Never use bare `random.random()` in code that tests need to control.

**Agent tool boundary — unauthenticated vs. authenticated actions:**
- Files: `app/lib/agent/` (not yet created)
- Why fragile: Tools like `add_to_cart`, `checkout`, `cancel_order`, and `return_order` require an authenticated user. If the agent calls these tools without a valid session context, they will fail silently or raise unhandled exceptions.
- Safe modification: Each tool function must accept `user_id: str` as a required parameter derived from the session. The agent orchestration layer must resolve and inject `user_id` before invoking any authenticated tool. Document which tools are public vs. authenticated.

---

## Tech Debt (Pre-implementation Risks)

**Eval dataset freshness:**
- Issue: Synthetic eval datasets generated by `deepeval` or `promptfoo` encode expected agent trajectories based on current prompt and tool design. As the agent evolves, datasets become stale and tests produce false negatives.
- Files: `app/lib/evals/` (not yet created)
- Impact: Stale evals give false confidence in agent quality.
- Fix approach: Version eval datasets alongside prompt versions. Add a `generated_at` field to each dataset file. Include a script to regenerate datasets and flag diffs in CI.

**Playwright browser binary dependency:**
- Issue: `playwright-python` requires downloading browser binaries (`playwright install`) before tests run. This step is not part of `pip install` and must be explicitly included in CI setup and local onboarding.
- Files: CI config (not yet created), `README.md` (not yet created)
- Impact: Playwright tests silently fail or error on machines where `playwright install` has not been run.
- Fix approach: Add `playwright install --with-deps chromium` as an explicit CI step. Document it in README. Consider a `Makefile` target (e.g., `make install-playwright`) for local setup.

**Langfuse availability — graceful degradation vs. hard failure:**
- Issue: If the Langfuse service is unreachable (network issue, wrong API key, self-hosted instance down), the app should not crash. The spec does not define whether Langfuse is required for the app to start.
- Files: `app/lib/observability/` (not yet created)
- Impact: A missing Langfuse key or unreachable host would break all agent calls if instrumentation is not wrapped safely.
- Fix approach: Wrap all Langfuse SDK calls in a try/except. Provide a `NoopTracer` fallback that satisfies the same interface but discards events. Log a warning at startup if Langfuse is not configured, but do not block app startup.

---

## Missing Critical Design Decisions

**Store theme not chosen:**
- Problem: The spec offers shoes or pet supplies as options. Seed data, product categories, and copy depend on this choice. Implementation cannot begin on the catalog or seed modules until this is decided.
- Blocks: `app/lib/seed/`, `app/lib/catalog/`, all eval datasets, all Playwright flows
- Recommendation: Choose shoes (more uniform data model — size/color variants map cleanly to the `Variant` dataclass).

**LLM provider not chosen:**
- Problem: The spec lists Anthropic, OpenAI, and Google as options. The agent tool-calling interface differs meaningfully between providers.
- Blocks: `app/lib/agent/`
- Recommendation: Commit to one provider before implementing the agent layer. Abstract behind a thin `LLMClient` interface if multi-provider support is a future requirement.

---

## Test Coverage Gaps (Pre-implementation)

**Concurrent checkout not covered by spec eval cases:**
- What's not tested: Race conditions on inventory during simultaneous checkouts.
- Files: `app/lib/orders/` (not yet created), `app/lib/mocks/` (not yet created)
- Risk: Inventory goes negative in demos with multiple concurrent users.
- Priority: High

**Root instruction injection via chat not in eval dataset:**
- What's not tested: A normal user embedding `[root]:` in a chat message to escalate privileges.
- Files: `app/lib/guardrails/` (not yet created), `app/lib/evals/` (not yet created)
- Risk: The root parser processes the instruction before the guardrail layer sees it.
- Priority: High

**Password reset flow not covered by Playwright spec:**
- What's not tested: The browser automation list in the spec does not include password reset.
- Files: `app/lib/auth/` (not yet created)
- Risk: Password reset regressions go undetected.
- Priority: Medium

---

*Concerns audit: 2026-04-18*
