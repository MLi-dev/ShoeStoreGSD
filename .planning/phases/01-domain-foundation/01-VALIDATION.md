---
phase: 1
slug: domain-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-18
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 + pytest-asyncio 1.3.0 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` — created in Wave 0 |
| **Quick run command** | `uv run pytest tests/unit/ -x -q` |
| **Full suite command** | `uv run pytest tests/ -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/unit/ -x -q`
- **After every plan wave:** Run `uv run pytest tests/ -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | — | — | N/A | smoke | `uv run pytest tests/unit/ -x -q` | ❌ W0 | ⬜ pending |
| 1-seed-01 | seed | 1 | CAT-01 | — | N/A | unit | `uv run pytest tests/unit/test_seed.py::test_seed_product_count -x` | ❌ W0 | ⬜ pending |
| 1-seed-02 | seed | 1 | CAT-01 | — | N/A | unit | `uv run pytest tests/unit/test_seed.py::test_products_have_required_fields -x` | ❌ W0 | ⬜ pending |
| 1-seed-03 | seed | 1 | CAT-04 | — | N/A | unit | `uv run pytest tests/unit/test_seed.py::test_products_have_variants -x` | ❌ W0 | ⬜ pending |
| 1-seed-04 | seed | 1 | SEED-01 | — | Passwords hashed | unit | `uv run pytest tests/unit/test_seed.py::test_seed_user_count -x` | ❌ W0 | ⬜ pending |
| 1-seed-05 | seed | 1 | SEED-01 | T-crypto | Bcrypt hash, not plaintext | unit | `uv run pytest tests/unit/test_seed.py::test_passwords_are_hashed -x` | ❌ W0 | ⬜ pending |
| 1-seed-06 | seed | 1 | SEED-02 | — | N/A | unit | `uv run pytest tests/unit/test_seed.py::test_seed_order_statuses -x` | ❌ W0 | ⬜ pending |
| 1-model-01 | models | 1 | — | — | N/A | unit | `uv run pytest tests/unit/test_models.py -x` | ❌ W0 | ⬜ pending |
| 1-store-01 | stores | 1 | — | — | N/A | unit | `uv run pytest tests/unit/test_stores.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/__init__.py` — package marker
- [ ] `tests/unit/__init__.py` — package marker
- [ ] `tests/unit/test_models.py` — stubs for model instantiation (D-11)
- [ ] `tests/unit/test_stores.py` — stubs for store CRUD (D-11)
- [ ] `tests/unit/test_seed.py` — stubs for CAT-01, CAT-04, SEED-01, SEED-02

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `uvicorn main:app` starts without errors | Phase goal | Requires running uvicorn process | Run `uv run uvicorn main:app --reload` and confirm no startup error |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
