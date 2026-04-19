---
phase: 03-web-ui-rest-api
plan: 04
subsystem: catalog-router, product-templates
tags: [catalog, web-ui, jinja2, bootstrap, search, product-detail, prg-pattern]

# Dependency graph
requires:
  - phase: 03-03
    provides: "stub catalog_router.py, base.html, auth/dependencies.py"
  - phase: 03-02
    provides: "catalog_service.search_products, catalog_service.get_product, cart_service.add_item"
provides:
  - "catalog_router: GET /products (public, search + category filter)"
  - "catalog_router: GET /products/{product_id} (public, 404 on unknown ID)"
  - "catalog_router: POST /cart/add (auth-gated, PRG 303 redirect)"
  - "products/list.html: search form, nav-tabs, product card grid"
  - "products/detail.html: variant selects, quantity, hidden product_id, Add to Cart form"
affects: [03-05, 03-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Public browsing: GET /products and GET /products/{id} have no auth dependency"
    - "POST /cart/add lives in catalog_router (form action on product detail page)"
    - "PRG pattern: POST /cart/add returns 303 redirect on both success and failure"
    - "Flash via request.session on add_item failure before redirect (Pattern 4)"
    - "Jinja2 unique filter on variants for size/color deduplication"
    - "Hidden product_id input on detail form (RESEARCH.md Pitfall 7)"

key-files:
  created:
    - app/web/templates/products/list.html
    - app/web/templates/products/detail.html
  modified:
    - app/api/catalog_router.py

key-decisions:
  - "POST /cart/add lives in catalog_router.py, not cart_router.py — it is the form action on the product detail page; cart_router.py (Plan 05) handles GET /cart, POST /cart/update, POST /cart/remove, POST /checkout"
  - "Public browsing: GET /products and GET /products/{id} require no authentication per plan (D-10, D-11, D-12)"
  - "CATEGORIES constant matches seeded data: [running, hiking, slides, sandals, socks]"

# Metrics
duration: 2min
completed: 2026-04-19
---

# Phase 03 Plan 04: Catalog Router + Product Templates Summary

**Catalog router (GET /products search+filter, GET /products/{id} detail, POST /cart/add) and both product templates (list with nav-tabs + card grid, detail with variant selects + hidden product_id + Add to Cart form posting to /cart/add)**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-04-19T20:14:56Z
- **Completed:** 2026-04-19T20:16:49Z
- **Tasks:** 2
- **Files created:** 2
- **Files modified:** 1

## Accomplishments

- Replaced catalog_router.py stub with full implementation (3 routes)
  - GET /products: public, delegates to `catalog_service.search_products(q=q, category=category)`
  - GET /products/{product_id}: public, 404 on unknown ID
  - POST /cart/add: auth-gated via `Depends(get_current_user_web)`; PRG 303 redirect
- Created products/list.html:
  - Search form with `name="q"` input and hidden `name="category"` (preserves filter on search, D-11)
  - `nav nav-tabs` category tabs: All + 5 seeded categories; active class on matching tab
  - `row row-cols-1 row-cols-md-3 g-4` product card grid
  - Each card: bg-secondary placeholder, card-title, card-text small, price fw-semibold, "View Details" btn-primary btn-sm stretched-link
  - Empty state with "Clear filters" link
- Created products/detail.html:
  - Two-column layout: col-md-6 image placeholder + col-md-6 info + form
  - h2 name, text-muted category, fs-3 fw-semibold price, small text-muted inventory
  - Hidden input `name="product_id"` (RESEARCH.md Pitfall 7 — critical)
  - Size select and Color select populated from `product.variants` via Jinja2 `unique` filter
  - Fallback "One Size" / "Default" options when variants list is empty
  - Quantity input: min=1, max=product.inventory, value=1
  - "Add to Cart" btn-primary btn-lg w-100; disabled when inventory == 0
  - Back to Products link

## Task Commits

1. **Task 1: Build catalog_router.py** — `059d59d` (feat)
2. **Task 2: Build products/list.html and products/detail.html** — `da887e9` (feat)

## Files Created/Modified

- `app/api/catalog_router.py` — stub replaced with GET /products, GET /products/{id}, POST /cart/add
- `app/web/templates/products/list.html` — search form, nav-tabs, product card grid
- `app/web/templates/products/detail.html` — variant selects, Add to Cart form, hidden product_id

## Test Results

```
uv run pytest tests/unit/ -x -q
131 passed, 26 xpassed, 10 warnings
```

No prior tests broken. App imports cleanly from main.py.

## Decisions Made

- POST /cart/add belongs in `catalog_router.py` because it is the form action on the product detail page. The `cart_router.py` (Plan 05) will own GET /cart, POST /cart/update, POST /cart/remove, and POST /checkout.
- Public browsing: GET /products and GET /products/{id} have no `Depends(get_current_user_web)` — browsing the catalog does not require login.
- `CATEGORIES = ["running", "hiking", "slides", "sandals", "socks"]` constant in the router matches the seeded data categories exactly.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — both templates are fully wired to live router context.

## Threat Flags

None — all threat mitigations applied as specified:
- T-03-02 (XSS via {{ q }}): Jinja2 auto-escaping on .html templates; no `| safe` filter used
- T-03-05 (cross-user cart pollution): `user_id` resolved from JWT cookie via `Depends(get_current_user_web)`, never from form body
- T-03-06 (double-submit): POST /cart/add returns 303 on both success and failure (PRG)
- T-03-03 (CSRF): SameSite=Lax on auth cookie; accepted per threat register

## Self-Check: PASSED

Files verified:
- app/api/catalog_router.py: FOUND (contains product_list, product_detail, add_to_cart, CATEGORIES, catalog_service.search_products)
- app/web/templates/products/list.html: FOUND (contains nav-tabs, row-cols-md-3, View Details, hidden category input)
- app/web/templates/products/detail.html: FOUND (contains type="hidden" name="product_id", name="size", name="color", name="quantity", action="/cart/add")

Commits verified:
- 059d59d: FOUND (feat(03-04): implement catalog_router)
- da887e9: FOUND (feat(03-04): add products/list.html and products/detail.html)

---
*Phase: 03-web-ui-rest-api*
*Completed: 2026-04-19*
