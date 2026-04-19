# main.py
# FastAPI application entry point.
# Source of pattern: .planning/phases/01-domain-foundation/01-PATTERNS.md (main.py section)
# Source of pattern: .planning/phases/01-domain-foundation/01-RESEARCH.md Pattern 2 (lifespan)
from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager.

    Plan 03 wires `seed()` here to populate in-memory stores before the
    first request is served. This no-op stub keeps `uvicorn main:app`
    runnable while domain models are being built in Plan 02.
    """
    # Startup: Plan 03 adds `from app.lib.seed.seed import seed; seed()`
    yield
    # Shutdown: nothing to clean up for in-memory stores


app = FastAPI(title="ShoeStore AI Demo", lifespan=lifespan)
# No routers registered in Phase 1 — Phase 2+ adds auth, catalog, cart, orders, chat routers.
