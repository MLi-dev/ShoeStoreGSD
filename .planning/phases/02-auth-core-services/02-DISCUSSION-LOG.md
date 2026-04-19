# Phase 2: Auth & Core Services - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.

**Date:** 2026-04-19
**Phase:** 02-auth-core-services
**Areas discussed:** JWT token design, Password reset flow, Cart service rules, Order service scope

---

## JWT Token Design

| Option | Selected |
|--------|----------|
| user_id only | ✓ |
| user_id + email | |
| user_id + email + role | |

**Expiry:** 30-min access token, no refresh

---

## Password Reset Flow

| Option | Selected |
|--------|----------|
| In-memory token store | ✓ |
| Direct reset endpoint | |
| Stub that logs the token | |

**Notes:** Token returned in response body — no email server, demo only. User confirmed this is intentional for demo purposes.

---

## Cart Service Rules

| Decision | Choice |
|----------|--------|
| Zero-inventory add | Reject with error |
| Duplicate variant | Merge into existing line item |

---

## Order Service Scope

| Decision | Choice |
|----------|--------|
| Cancel eligibility | placed + paid only |
| Ownership enforcement | Service layer |
