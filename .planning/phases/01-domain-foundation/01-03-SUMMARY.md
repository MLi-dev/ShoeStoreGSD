---
phase: 01-domain-foundation
plan: 03
subsystem: seed
tags: [python, passlib, bcrypt, fastapi-lifespan, seed-data, pytest]

requires:
  - phase: 01-domain-foundation plan 02
    provides: User/Product/Variant/Order/OrderItem dataclasses and empty in-memory dicts

provides:
  - seed() function that populates users_db (2 users), products_db (15 products), orders_db (3 orders)
  - clear_and_reseed() helper for test isolation
  - FastAPI lifespan in main.py calling seed() before yield
  - 16-test suite covering CAT-01, CAT-04, SEED-01, SEED-02, password hashing, price range, idempotency

affects:
  - Phase 2 auth (login must verify against bcrypt hashes seeded here)
  - Phase 2 catalog API (products_db populated and queryable)
  - Phase 2 orders API (3 prior orders visible immediately on startup)
  - Phase 4 evals (seed data is reference data for chatbot tool tests)
  - Phase 5 observability (agent exercises seeded catalog on first message)

tech-stack:
  added:
    - passlib 1.7.4 (CryptContext bcrypt backend)
    - bcrypt 4.3.0 (downgraded from 5.0.0 — passlib 1.7.4 incompatible with bcrypt 5.x)
  patterns:
    - CryptContext module-level constant, hashing only inside _seed_users() (avoids slow bcrypt at import)
    - clear_and_reseed() pattern for test isolation (clear stores, then call seed())
    - FastAPI asynccontextmanager lifespan: seed() before yield, nothing at shutdown
    - Products seeded as list then bulk-inserted into products_db dict

key-files:
  created:
    - app/lib/seed/seed.py
    - tests/unit/test_seed.py
  modified:
    - main.py
    - pyproject.toml (bcrypt constraint)
    - uv.lock

key-decisions:
  - "Downgraded bcrypt to 4.x: passlib 1.7.4 uses bcrypt.__about__ which was removed in bcrypt 5.x; 4.3.0 is stable"
  - "Password constants (_ALICE_PASSWORD, _BOB_PASSWORD) at module level; hashing deferred to _seed_users() body"
  - "Orders reference seeded product IDs via products_by_name lookup for determinism across UUIDs"
  - "No try/except around seed() in lifespan — loud failure at startup is correct behavior for data errors"

patterns-established:
  - "Seed module: _seed_X() private helpers, seed() orchestrator, clear_and_reseed() for tests"
  - "Bcrypt hashing via passlib CryptContext — never import bcrypt directly"
  - "All IDs: str(uuid.uuid4()); all timestamps: datetime.now(tz=timezone.utc).isoformat()"
  - "autouse fixture clears stores before/after every test for isolation"

requirements-completed: [CAT-01, CAT-04, SEED-01, SEED-02]

duration: 6min
completed: 2026-04-18
---

# Phase 1 Plan 03: Seed Data and Lifespan Wiring Summary

**passlib CryptContext bcrypt hashing for 2 demo users, 15 shoe products across 5 categories with variants and $49-$189 pricing, 3 prior orders covering paid/shipped/canceled, wired into FastAPI asynccontextmanager lifespan**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-04-18T02:01:22Z
- **Completed:** 2026-04-18T02:07:11Z
- **Tasks:** 3 (TDD: RED test file, GREEN implementation, lifespan wiring)
- **Files modified:** 5 (test_seed.py, seed.py, main.py, pyproject.toml, uv.lock)

## Accomplishments

- 16-test TDD suite covering all four Phase 1 requirements (CAT-01, CAT-04, SEED-01, SEED-02) with RED-then-GREEN discipline
- seed.py with 15 demo-quality shoe products (TrailBlaze X9, Summit Pro Hiker, CloudSlide Comfort, etc.) across running/hiking/slides/sandals/socks, each with >=1 Variant
- bcrypt password hashing via passlib CryptContext: alice and bob users stored with `$2b$12$...` hashes, never plaintext
- main.py lifespan calls seed() before yield; `import main` remains side-effect-free

## Task Commits

1. **Task 1: Write tests/unit/test_seed.py (RED)** - `24c6483` (test)
2. **Task 2: Implement app/lib/seed/seed.py (GREEN)** - `fd1308d` (feat)
3. **Task 3: Wire seed() into main.py lifespan** - `eaf2b58` (feat)

## Seeded Data Reference

**Users:**
- alice@example.com / alice-demo-password-2026 (hashed at seed time)
- bob@example.com / bob-demo-password-2026 (hashed at seed time)

**Products (15 total, 3 per category):**

| Category | Products |
|----------|----------|
| running | TrailBlaze X9 ($149), Velocity Pulse ($129), Stride Horizon Light ($99) |
| hiking | Summit Pro Hiker ($189), Ridge Runner GTX ($159), BaseCamp Classic ($119) |
| slides | CloudSlide Comfort ($59), Pool Deck Pro ($49), LoungeLite Slide ($69) |
| sandals | CoastWalker Sport ($89), Sunset Strap ($99), Canyon Trek Sandal ($109) |
| socks | Merino Cushion Crew ($49), PaceSetter No-Show ($55), TrailGuard Hiker Quarter ($65) |

**Orders (3 total):**
- paid: alice / TrailBlaze X9 x1 / credit_card / $149.00
- shipped: bob / CloudSlide Comfort x2 / paypal / $118.00
- canceled: alice / Summit Pro Hiker x1 / apple_pay / $189.00 (payment_status=refunded)

## Files Created/Modified

- `app/lib/seed/seed.py` — seed(), clear_and_reseed(), _seed_users(), _seed_products(), _seed_orders()
- `tests/unit/test_seed.py` — 16 tests covering CAT-01, CAT-04, SEED-01, SEED-02 and security
- `main.py` — FastAPI lifespan now calls seed() before yield
- `pyproject.toml` / `uv.lock` — bcrypt constraint added (bcrypt<5)

## Decisions Made

- **Downgraded bcrypt 5.x to 4.x:** passlib 1.7.4 calls `bcrypt.__about__.__version__` which was removed in bcrypt 5.0.0, causing `ValueError` during backend detection. Pinning `bcrypt<5` restores compatibility. A non-fatal warning `(trapped) error reading bcrypt version` appears at runtime but does not affect correctness.
- **Plaintext password constants with leading underscore:** `_ALICE_PASSWORD` and `_BOB_PASSWORD` are module-private constants used only by `_seed_users()`. They are developer-visible in source but never stored in any User object.
- **No try/except around seed() in lifespan:** per 01-RESEARCH.md Pattern 2, seed failures should be loud startup crashes so bad data is caught immediately.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Downgraded bcrypt from 5.0.0 to 4.3.0**
- **Found during:** Task 2 (GREEN implementation)
- **Issue:** passlib 1.7.4 uses `bcrypt.__about__.__version__` removed in bcrypt 5.0.0. This caused `ValueError: password cannot be longer than 72 bytes` in passlib's internal `detect_wrap_bug()` test during backend initialization.
- **Fix:** `uv add "bcrypt<5"` — installed bcrypt 4.3.0. A non-fatal `(trapped) error reading bcrypt version` warning appears but hashing works correctly.
- **Files modified:** pyproject.toml, uv.lock
- **Verification:** All 16 seed tests pass; `_pwd_context.hash()` returns `$2b$12$...` hashes
- **Committed in:** fd1308d (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 3 — blocking)
**Impact on plan:** Required to unblock passlib bcrypt hashing. No scope creep. All plan requirements delivered.

## Issues Encountered

- passlib 1.7.4 / bcrypt 5.x incompatibility (see deviation above). Non-blocking once bcrypt downgraded.

## Known Stubs

None — all 15 products have real names, descriptions, prices, and variants. All orders reference real user IDs.

## Threat Flags

No new security surface beyond what the plan's threat model covers. The only cryptographic surface (password hashing) is mitigated by T-01-03-01 and verified by `test_passwords_are_hashed`.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- All four Phase 1 requirements delivered: CAT-01, CAT-04, SEED-01, SEED-02
- Full unit suite: 37 tests green (test_models.py + test_stores.py + test_seed.py)
- Phase 2 can use alice@example.com / alice-demo-password-2026 and bob@example.com / bob-demo-password-2026 for auth testing
- Phase 2 catalog API has 15 searchable products immediately available on uvicorn startup

---
## Self-Check: PASSED

- app/lib/seed/seed.py: FOUND
- tests/unit/test_seed.py: FOUND
- main.py: FOUND
- 01-03-SUMMARY.md: FOUND
- Commit 24c6483 (RED): FOUND
- Commit fd1308d (GREEN): FOUND
- Commit eaf2b58 (lifespan): FOUND

---
*Phase: 01-domain-foundation*
*Completed: 2026-04-18*
