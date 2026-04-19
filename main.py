# main.py
# FastAPI application entry point.
# Lifespan populates all in-memory stores via seed() before the first request (D-09).
# Source of pattern: .planning/phases/01-domain-foundation/01-PATTERNS.md main.py section.
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.lib.seed.seed import seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager.

    On startup, populate in-memory stores with demo data (15 products, 2 users,
    3 orders) via seed(). If seed() raises, the app fails to start — fix the
    seed data before deployment.
    """
    # Startup: populate all in-memory stores.
    seed()
    yield
    # Shutdown: nothing to clean up for in-memory stores.


app = FastAPI(title="ShoeStore AI Demo", lifespan=lifespan)
# No routers registered in Phase 1 — Phase 2+ adds auth, catalog, cart, orders, chat routers.
