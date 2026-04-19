# tests/evals/test_smoke.py
# Smoke runner: one real Anthropic API call per eval dataset (3 total).
# Skips all tests when ANTHROPIC_API_KEY is absent — safe for CI with no key.
# Source: CONTEXT.md D-12, D-13
import logging
import os

import pytest

from app.lib.agent import agent
from app.lib.agent import history as agent_history
from app.lib.auth.store import reset_tokens_db, users_db
from app.lib.cart.store import carts_db
from app.lib.catalog.store import products_db
from app.lib.evals.datasets.adversarial import CASES as ADVERSARIAL_CASES
from app.lib.evals.datasets.negative import CASES as NEGATIVE_CASES
from app.lib.evals.datasets.positive import CASES as POSITIVE_CASES
from app.lib.orders.store import orders_db
from app.lib.seed.seed import seed

logger = logging.getLogger(__name__)

# Skip entire module when API key is absent — not a failure, just not runnable.
pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live eval smoke run",
)


@pytest.fixture(autouse=True)
def reset_stores():
    """Reset all in-memory stores and re-seed before each smoke test."""
    users_db.clear()
    reset_tokens_db.clear()
    carts_db.clear()
    orders_db.clear()
    products_db.clear()
    agent_history._history.clear()
    seed()
    yield
    users_db.clear()
    reset_tokens_db.clear()
    carts_db.clear()
    orders_db.clear()
    products_db.clear()
    agent_history._history.clear()


@pytest.fixture
def smoke_user():
    """Return the seeded alice User object for agent.run() calls."""
    return next(u for u in users_db.values() if u.email == "alice@example.com")


@pytest.mark.asyncio
async def test_smoke_positive(smoke_user):
    """Smoke: one positive case — happy-path agent call must not raise."""
    case = POSITIVE_CASES[0]
    logger.info("Smoke positive: tags=%r input=%r", case["tags"], case["input"])
    result = await agent.run(
        user_id=smoke_user.id,
        user=smoke_user,
        message=case["input"],
    )
    assert "success" in result, f"agent.run returned no 'success' key: {result!r}"


@pytest.mark.asyncio
async def test_smoke_negative(smoke_user):
    """Smoke: one negative case — error-scenario agent call must not raise."""
    case = NEGATIVE_CASES[0]
    logger.info("Smoke negative: tags=%r input=%r", case["tags"], case["input"])
    result = await agent.run(
        user_id=smoke_user.id,
        user=smoke_user,
        message=case["input"],
    )
    assert "success" in result, f"agent.run returned no 'success' key: {result!r}"


@pytest.mark.asyncio
async def test_smoke_adversarial(smoke_user):
    """Smoke: one adversarial case — hostile-input agent call must not raise."""
    case = ADVERSARIAL_CASES[0]
    logger.info("Smoke adversarial: tags=%r input=%r", case["tags"], case["input"])
    result = await agent.run(
        user_id=smoke_user.id,
        user=smoke_user,
        message=case["input"],
    )
    assert "success" in result, f"agent.run returned no 'success' key: {result!r}"
