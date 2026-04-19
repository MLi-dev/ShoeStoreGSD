---
phase: 04-claude-agent
plan: "03"
subsystem: chat-endpoint
tags: [fastapi, jinja2, marked-js, guardrails, agent, chat-ui]

# Dependency graph
requires:
  - phase: 04-claude-agent
    plan: "01"
    provides: guardrails.check_message(), history.append_message/get_messages
  - phase: 04-claude-agent
    plan: "02"
    provides: agent.run(user_id, user, message)
  - phase: 03-web-ui-rest-api
    provides: get_current_user_web dependency, base.html navbar structure

provides:
  - GET /chat — authenticated chat page (redirects to /login when unauthenticated)
  - POST /chat/message — AJAX endpoint returning JSON {reply: str}
  - chat/chat.html — Bootstrap chat UI with marked.js transcript rendering
  - Chat navbar link in base.html (visible to authenticated users only)

affects:
  - 04-04 (tracer — wraps agent.run() calls with Langfuse; same chat_router uses agent.run())

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "AJAX chat pattern: fetch() POST → JSON {reply: str} → marked.parse() render in DOM"
    - "[root]: prefix stripped in route handler before guardrail check, gated on DEMO_MODE"
    - "307 redirect detection in JS: response.status === 307 || response.redirected → /login"
    - "user_id always from JWT session (current_user.id), never from request body"

key-files:
  created:
    - app/api/chat_router.py
    - app/web/templates/chat/chat.html
  modified:
    - main.py
    - app/web/templates/base.html

key-decisions:
  - "GET /chat and POST /chat/message share get_current_user_web — consistent 307 redirect behavior on session expiry"
  - "guardrails.check_message() returns {reply: guard[message]} directly to user without 4xx — avoids leaking injection detection to attacker"
  - "HTTPException(500) raised only on agent loop failures — guard rejections return 200 with a refusal message"
  - "Chat navbar link inside {% if current_user %} block — hidden from unauthenticated users who are redirected anyway"

patterns-established:
  - "Chat endpoint: strip [root]: → check_message() → agent.run() → JSONResponse({reply})"
  - "JS loading state: btn.disabled + input.disabled during fetch, restored in finally block"
  - "marked.parse() for agent replies, HTML-escaped plain text for user messages"

requirements-completed:
  - CHAT-01
  - CHAT-02
  - CHAT-03
  - CHAT-04
  - CHAT-05

# Metrics
duration: 4min
completed: "2026-04-19"
---

# Phase 4 Plan 03: Chat Endpoint and UI Summary

**FastAPI chat router with guardrail-gated agent dispatch, Bootstrap transcript UI with marked.js rendering, and navbar integration — the complete user-visible conversational interface wiring all agent capabilities**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-19T22:14:06Z
- **Completed:** 2026-04-19T22:18:13Z
- **Tasks:** 2
- **Files modified:** 2 created, 2 modified

## Accomplishments

- GET /chat renders chat page for authenticated users; unauthenticated users get 307 → /login (verified with TestClient)
- POST /chat/message applies the full security pipeline: [root]: stripping → guardrails → agent.run() → JSON reply
- chat.html delivers Bootstrap transcript UI with marked.js markdown rendering for agent replies and HTML escaping for user messages
- Loading state (spinner + disabled input/button) prevents double-submit during agent processing
- Chat navbar link added inside {% if current_user %} block — only visible to logged-in users
- All 18 integration tests pass (xpassed), 1 skipped — no regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: chat_router.py — GET /chat + POST /chat/message** - `520cd03` (feat)
2. **Task 2: chat.html + main.py + base.html wiring** - `9edde90` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `app/api/chat_router.py` — GET /chat page route + POST /chat/message AJAX endpoint; [root]: stripping, guardrail check, agent.run() dispatch, structured error responses
- `app/web/templates/chat/chat.html` — Bootstrap chat UI: transcript div, marked.js CDN, fetch() AJAX, loading spinner, Enter key handler, session expiry redirect
- `main.py` — Added chat_router import and app.include_router(chat_router)
- `app/web/templates/base.html` — Chat navbar link inside {% if current_user %} block

## Decisions Made

- Guard rejections return HTTP 200 with `{"reply": guard["message"]}` rather than 4xx — avoids leaking injection detection details to attackers while still informing the user
- HTTPException(500) is raised only on genuine agent loop failures — this surfaces a human-readable message (not a stack trace) per T-04-15
- Chat link is inside `{% if current_user %}` (same block as Logout) — consistent with existing auth-gated nav pattern; unauthenticated users are redirected before they can use the endpoint anyway

## Deviations from Plan

None - plan executed exactly as written.

## Threat Surface Scan

No new trust boundaries beyond those documented in the plan threat model. All T-04-11 through T-04-15 mitigations implemented as specified:
- T-04-11: empty/missing message returns 400; guardrails run before agent.run(); [root]: stripped before guardrail check
- T-04-12: user messages HTML-escaped; agent replies via marked.parse() (accepted XSS risk for demo)
- T-04-13: [root]: stripping logged at WARNING level; content not acted on in Phase 4
- T-04-14: JS detects 307 redirect and navigates to /login
- T-04-15: HTTPException detail uses result["message"] not stack trace

## Known Stubs

None — the chat endpoint fully wires to agent.run(). The agent requires ANTHROPIC_API_KEY at runtime, but the import and routing are complete. Chat UI displays a personalized greeting using current_user.email.

## User Setup Required

`ANTHROPIC_API_KEY` environment variable must be set at server runtime for agent.run() to make API calls. The route handler, guardrails, and UI are all functional without it — only live chat turns require the key.

## Next Phase Readiness

- Phase 4 Plan 04 (Langfuse tracer) can wrap agent.run() in chat_router.py without modifying the chat endpoint — tracer hooks into agent.py
- All routes registered; /chat and /chat/message verified via TestClient and route introspection
- No blockers. Plan 04-04 can proceed immediately.

---
*Phase: 04-claude-agent*
*Completed: 2026-04-19*
