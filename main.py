# main.py
# FastAPI application entry point.
# Lifespan populates all in-memory stores via seed() before the first request (D-09).
# Source of pattern: .planning/phases/01-domain-foundation/01-PATTERNS.md main.py section.
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

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

# SessionMiddleware enables request.session for flash messages (D-01 itsdangerous).
# secret_key is dev-only; not used for JWT or user auth.
app.add_middleware(SessionMiddleware, secret_key="dev-flash-secret")

# Router registration — routers created in Phase 3 plans 03–06.
from app.api.auth_router import router as auth_router       # noqa: E402
from app.api.catalog_router import router as catalog_router  # noqa: E402
from app.api.cart_router import router as cart_router        # noqa: E402
from app.api.orders_router import router as orders_router    # noqa: E402

app.include_router(auth_router)
app.include_router(catalog_router)
app.include_router(cart_router)
app.include_router(orders_router)
