---
status: partial
phase: 04-claude-agent
source: [04-VERIFICATION.md]
started: 2026-04-19T22:41:37Z
updated: 2026-04-19T22:41:37Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. CHAT-03: Clarifying Questions — Agent asks for missing info
expected: Send "Cancel my order" (no order ID) to the chat UI. Agent should ask which order to cancel rather than failing or guessing. Tool schema requires order_id, so Claude must request it from the user.
result: [pending]

### 2. CHAT-05: Graceful Mock Failure Recovery
expected: Set out_of_stock_probability=1.0 via failure config, attempt checkout via chat. Agent should surface a human-readable failure message with a concrete next step (retry, try different payment method) — no raw error codes or stack traces exposed to the user.
result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
