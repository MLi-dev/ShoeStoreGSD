---
phase: 3
slug: web-ui-rest-api
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-19
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 + pytest-asyncio 1.3.0 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` (asyncio_mode = "auto") |
| **Quick run command** | `uv run pytest tests/unit/ -x -q` |
| **Full suite command** | `uv run pytest tests/ -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/unit/ -x -q`
- **After every plan wave:** Run `uv run pytest tests/ -x -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 3-??-catalog | TBD | 1 | CAT-02 | — | N/A | unit | `uv run pytest tests/unit/test_catalog_service.py -x` | ❌ W0 | ⬜ pending |
| 3-??-catalog | TBD | 1 | CAT-03 | — | N/A | unit | `uv run pytest tests/unit/test_catalog_service.py -x` | ❌ W0 | ⬜ pending |
| 3-??-checkout | TBD | 2 | CHK-01 | open-redirect | `next` param validated to relative path | integration | `uv run pytest tests/integration/test_checkout.py -x` | ❌ W0 | ⬜ pending |
| 3-??-checkout | TBD | 2 | CHK-02 | — | N/A | integration | `uv run pytest tests/integration/test_checkout.py::test_checkout_paypal -x` | ❌ W0 | ⬜ pending |
| 3-??-checkout | TBD | 2 | CHK-03 | — | N/A | integration | `uv run pytest tests/integration/test_checkout.py::test_checkout_apple_pay -x` | ❌ W0 | ⬜ pending |
| 3-??-checkout | TBD | 2 | CHK-04 | — | N/A | integration | `uv run pytest tests/integration/test_checkout.py::test_confirmation_page -x` | ❌ W0 | ⬜ pending |
| 3-??-orders | TBD | 2 | ORD-01 | cross-user | ownership check enforced in order_service | integration | `uv run pytest tests/integration/test_orders_router.py -x` | ❌ W0 | ⬜ pending |
| 3-??-orders | TBD | 2 | ORD-02 | cross-user | ownership check before cancel | integration | `uv run pytest tests/integration/test_orders_router.py::test_cancel_order -x` | ❌ W0 | ⬜ pending |
| 3-??-orders | TBD | 2 | ORD-03 | cross-user | ownership check before return | integration | `uv run pytest tests/integration/test_orders_router.py::test_return_order -x` | ❌ W0 | ⬜ pending |
| 3-??-warehouse | TBD | 1 | MOCK-01 | — | N/A | unit | `uv run pytest tests/unit/test_warehouse_mock.py -x` | ❌ W0 | ⬜ pending |
| 3-??-payment | TBD | 1 | MOCK-02 | — | N/A | unit | `uv run pytest tests/unit/test_payment_mock.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_catalog_service.py` — stubs for CAT-02, CAT-03
- [ ] `tests/unit/test_warehouse_mock.py` — stubs for MOCK-01
- [ ] `tests/unit/test_payment_mock.py` — stubs for MOCK-02
- [ ] `tests/integration/conftest.py` — shared TestClient fixture, authenticated session helper
- [ ] `tests/integration/test_auth_router.py` — stubs for login/logout cookie flow
- [ ] `tests/integration/test_checkout.py` — stubs for CHK-01 through CHK-04
- [ ] `tests/integration/test_orders_router.py` — stubs for ORD-01 through ORD-03

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Browser renders product list with correct Bootstrap card grid | CAT-02 | Visual layout cannot be asserted in unit tests | Open `/products` in browser; verify 3-column card grid, category tabs, search box |
| Bootstrap status badges render correct color per order status | ORD-01 | CSS class rendering is visual | Open `/orders/{id}` for each status; verify badge color matches UI-SPEC color map |
| Checkout button disabled/enabled state | CHK-01 | Dynamic state is client-side | Add item to cart, select payment method, verify "Place Order" button is clickable |
| Demo credential hint visible on login page | AUTH | Copy contract | Open `/login`; verify demo hint text matches copywriting contract |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
