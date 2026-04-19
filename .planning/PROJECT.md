# ShoeStore AI Demo

## What This Is

A Python/FastAPI demo e-commerce application for a shoe store that showcases agentic product development. It supports both a traditional web UI and a Claude-powered chatbot UI, letting users browse shoes, manage carts, place orders, and handle support workflows. The system is intentionally mock-heavy, in-memory, and observable — built as a vehicle for learning end-to-end agentic development workflows.

## Core Value

A working end-to-end loop where a user can discover a shoe, buy it, and resolve an issue — through either the web UI or the chatbot — with every step traced and testable.

## Requirements

### Validated

- [x] App seeds 10–20 shoe products on startup with name, description, price, inventory, and size/color variants — Validated in Phase 1: Domain Foundation
- [x] App seeds at least 2 test users and 3 prior orders (paid, shipped, canceled) — Validated in Phase 1: Domain Foundation
- [x] Domain models (User, Product, Variant, Cart, CartItem, Order, OrderItem) can be created, stored, and retrieved without an HTTP server — Validated in Phase 1: Domain Foundation

### Active

- [ ] User can sign up, log in, and reset their password via shared FastAPI auth (web + chat)
- [ ] User can browse, search, and view details for seeded shoe products
- [ ] User can add items to cart, update quantities, and remove items
- [ ] User can check out and place an order (Credit Card, PayPal, Apple Pay)
- [ ] User can check order status, cancel, or return an order via web UI
- [ ] Chatbot (Claude via Anthropic SDK) can handle all shopping and support flows conversationally
- [ ] Warehouse and payment mock adapters have configurable global failure injection
- [ ] `[root]:` instruction token updates live failure config for current run only
- [ ] Langfuse traces capture agent/tool/generation activity
- [ ] Eval datasets exist for positive, negative, and adversarial cases
- [ ] Playwright E2E tests cover core flows

### Out of Scope

- Production-grade database — in-memory state only, resets on restart
- Real payment processor or warehouse integration — mocked only
- Multi-tenant or admin portal — not needed for personal learning demo
- OAuth / social login — email/password only
- Per-session failure config — global failure rates only

## Context

- **Spec**: The full project spec lives at `/Users/matthew/Downloads/spec_python.md` — canonical reference for all requirements
- **Codebase map**: `.planning/codebase/` contains STACK, ARCHITECTURE, STRUCTURE, CONVENTIONS, TESTING, INTEGRATIONS, and CONCERNS docs
- **Purpose**: Personal learning — working through an agentic dev workflow by building a realistic but non-trivial app
- **Stack**: Python 3.12+, FastAPI, Pydantic dataclasses, Anthropic Python SDK (Claude), Langfuse, pytest, playwright-python
- **State**: Pure in-memory Python dicts/lists — every restart is a clean slate with seeded data
- **Store theme**: Shoes (running, hiking, slides, sandals, socks)

## Constraints

- **Tech stack**: Python + FastAPI — no Node.js/TypeScript
- **Persistence**: In-memory only — no database, no disk state
- **Auth**: Single shared FastAPI session/auth layer used by both web UI and chatbot
- **LLM**: Anthropic Python SDK (Claude) — not swappable at this stage
- **Failure config**: Global scope — one failure config affects all sessions; resets on process restart
- **Returns**: Allowed on any completed order (paid or processing status and above), not restricted to shipped-only
- **Root token**: `[root]:` instructions are in-memory only, reset each run
- **Demo mode**: Root instructions only active in dev/demo mode, never exposed to end users

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python + FastAPI over Node.js | User's preferred stack per spec | — Pending |
| Anthropic SDK (Claude) for LLM | Best tool-use support, matches spec recommendation | — Pending |
| Shared auth for web + chat | Simpler — one login state, less code | — Pending |
| Global failure config | Easier to demo and reason about | — Pending |
| Returns allowed on paid/processing+ | More realistic support flow for learning | — Pending |
| Root token resets each run | Predictable demo behavior, no stale state | — Pending |
| In-memory state | Spec requirement — simplifies repeated testing | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-19 — Phase 1 complete*
