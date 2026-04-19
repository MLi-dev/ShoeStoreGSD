# Phase 1: Domain Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-18
**Phase:** 01-domain-foundation
**Areas discussed:** Packaging setup, Seed data depth, Store initialization pattern, Test structure

---

## Packaging Setup

| Option | Description | Selected |
|--------|-------------|----------|
| pyproject.toml + uv | Modern standard: uv for fast installs, uv.lock for reproducibility | ✓ |
| pyproject.toml + pip | Standard pyproject.toml without uv — no lockfile by default | |
| requirements.txt + requirements-dev.txt | Simple and explicit, no lockfile | |

**User's choice:** pyproject.toml + uv

| Option | Description | Selected |
|--------|-------------|----------|
| Flat layout: app/ at root | app/ alongside main.py and config.py — matches spec structure | ✓ |
| src layout: src/app/ | src/ wrapper prevents accidental imports from root | |

**User's choice:** Flat layout

---

## Seed Data Depth

| Option | Description | Selected |
|--------|-------------|----------|
| Rich & demo-worthy | Real shoe names, compelling descriptions, realistic pricing ($49–$189) | ✓ |
| Functional but minimal | Valid data meeting schema, no marketing copy | |
| You decide | Claude picks the data style | |

**User's choice:** Rich & demo-worthy (confirmed in follow-up)

| Option | Description | Selected |
|--------|-------------|----------|
| 15 products, even spread | 3 per category across all 5 categories | ✓ |
| 10 products, 2 per category | Minimum viable | |
| 20 products, weighted toward shoes | More running/hiking options | |

**User's choice:** 15 products, 3 per category

| Option | Description | Selected |
|--------|-------------|----------|
| alice@example.com / bob@example.com | Memorable conventional test user names | ✓ |
| test1@shoedemo.com / test2@shoedemo.com | Domain-consistent naming | |
| You decide | Claude picks | |

**User's choice:** alice@example.com / bob@example.com

---

## Store Initialization Pattern

| Option | Description | Selected |
|--------|-------------|----------|
| FastAPI lifespan startup event | seed() called in async lifespan — runs once before requests | ✓ |
| Module-level at import | Stores populated when module is first imported | |

**User's choice:** FastAPI lifespan startup event

| Option | Description | Selected |
|--------|-------------|----------|
| Plain module-level dicts | products_db: dict[str, Product] = {} in store.py | ✓ |
| Dataclass wrapper with methods | Store dataclass holding dict + add/get/list methods | |

**User's choice:** Plain module-level dicts (confirmed via "go with recommended")

---

## Test Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Top-level tests/ directory | tests/unit/, tests/integration/, tests/e2e/ | ✓ |
| Adjacent to source | test_*.py next to each module | |

**User's choice:** Top-level tests/ directory

| Option | Description | Selected |
|--------|-------------|----------|
| Models + stores + seed smoke test | Model creation, store CRUD, seed() populates stores | ✓ |
| Models only | Just dataclass instantiation | |
| You decide | Claude determines scope | |

**User's choice:** Models + stores + seed smoke test

---

## Claude's Discretion

- Exact shoe model names, descriptions, and pricing (within rich/demo-worthy constraint)
- Specific password for seeded test users
- Whether seed.py exposes a clear_and_reseed() helper for test isolation

## Deferred Ideas

None.
