# Phase 3: Web UI & REST API - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-19
**Phase:** 03-web-ui-rest-api
**Areas discussed:** Auth web session, UI styling, Checkout flow, Catalog search

---

## Auth Web Session

| Option | Description | Selected |
|--------|-------------|----------|
| JWT in httpOnly cookie | Login sets JWT via Set-Cookie (httpOnly, SameSite=Lax). FastAPI Depends() reads it. No JS needed. | ✓ |
| itsdangerous session cookie | Server-side signed session using existing itsdangerous dep. Dual-auth path complexity. | |
| JWT in localStorage + fetch | SPA-style, JS-dependent, conflicts with Jinja2 SSR simplicity. | |

**User's choice:** JWT in httpOnly cookie

---

| Option | Description | Selected |
|--------|-------------|----------|
| Login page | POST form → validate → set JWT cookie → redirect | ✓ |
| Register page | POST form → create user → set JWT cookie → redirect | ✓ |
| Password reset | Two pages: request-reset and reset-confirm. Token in response body. | ✓ |
| Logout endpoint | Clears JWT cookie, redirects to login | ✓ |

**User's choice:** All four selected

---

| Option | Description | Selected |
|--------|-------------|----------|
| Redirect to login | 302 redirect to /login?next=<url>. After login, redirect back. | ✓ |
| 401 JSON error | HTTP 401 — only appropriate for API routes, not web pages. | |

**User's choice:** Redirect to login

---

## UI Styling

| Option | Description | Selected |
|--------|-------------|----------|
| Bootstrap 5 CDN | Load from CDN via link tag. No build step. Grid, cards, forms, buttons. | ✓ |
| Tailwind CDN play | Utility-first, modern, but verbose HTML and CDN limitations. | |
| Minimal custom CSS | Single style block in base.html. Plain but functional. | |

**User's choice:** Bootstrap 5 CDN

---

| Option | Description | Selected |
|--------|-------------|----------|
| Functional + clean | Bootstrap defaults, minimal customization. Navbar, cards, forms. | ✓ |
| Store-branded | Custom brand colors, logo placeholder. More effort. | |
| Bare/utilitarian | Raw Bootstrap, no visual extras. | |

**User's choice:** Functional + clean

---

## Checkout Flow

| Option | Description | Selected |
|--------|-------------|----------|
| Single-page checkout | Cart page has payment selector + Checkout button. One POST places order. | ✓ |
| Multi-step | Cart → Payment selection → Review & confirm → Confirmation. | |

**User's choice:** Single-page checkout

---

| Option | Description | Selected |
|--------|-------------|----------|
| Order ID + summary | Order ID, items, total, payment method, status, link to orders. | ✓ |
| Minimal confirmation | Just "Order placed! ID is X" with a link. | |
| Full receipt view | All details, same as order detail page. | |
| You decide | Claude picks detail level | |

**User's choice:** Order ID + summary

---

| Option | Description | Selected |
|--------|-------------|----------|
| Buttons on order detail page | Cancel/Return shown conditionally on /orders/{id} based on status. | ✓ |
| Buttons on orders list | Inline per-row buttons. Less room for detail. | |
| You decide | Claude picks placement | |

**User's choice:** Buttons on order detail page

---

## Catalog Search

| Option | Description | Selected |
|--------|-------------|----------|
| Case-insensitive substring match | Match against name, description, category. Returns all matching products. | ✓ |
| Name + category only | Faster but ignores description. | |
| You decide | Claude picks matching logic | |

**User's choice:** Case-insensitive substring match (name + description + category)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Category filter tabs/links | All / Running / Hiking / Slides / Sandals / Socks. Combines with search. | ✓ |
| Search-only, no filter | Just a search box. | |
| You decide | Claude decides | |

**User's choice:** Category filter tabs/links

---

| Option | Description | Selected |
|--------|-------------|----------|
| Full detail + variant selector | Name, description, price, inventory, variant dropdowns, Add to Cart POST form. | ✓ |
| Detail page, no variant selector | Uses default/first variant. Ignores variant model. | |
| You decide | Claude picks detail page design | |

**User's choice:** Full detail + variant selector form

---

## Claude's Discretion

- Bootstrap component choices (card vs. list-group)
- Navbar layout and links
- Flash/alert approach for errors
- Catalog service file naming
- Quantity selector behavior on product detail page

## Deferred Ideas

None.
