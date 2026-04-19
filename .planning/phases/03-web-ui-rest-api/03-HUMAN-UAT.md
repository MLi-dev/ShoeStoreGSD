---
status: partial
phase: 03-web-ui-rest-api
source: [03-VERIFICATION.md]
started: 2026-04-19T00:00:00Z
updated: 2026-04-19T00:00:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Full browser purchase flow
expected: Add item to cart from /products/{id}, checkout with any payment method → redirected to /orders/{id}/confirmation showing order ID, items, total, payment method, status badge
result: [pending]

### 2. Category filter + search combination
expected: GET /products?q=trail&category=hiking returns only matching items with the Hiking tab shown as active
result: [pending]

### 3. Checkout failure display
expected: Set FAILURE_CONFIG payment failure prob to 1.0, attempt checkout → cart re-renders with "Payment failed..." error text; no order created in /orders list
result: [pending]

### 4. Order detail conditional buttons
expected: paid order shows Cancel + Return; shipped order shows Return only; canceled order shows neither button
result: [pending]

## Summary

total: 4
passed: 0
issues: 0
pending: 4
skipped: 0
blocked: 0

## Gaps
