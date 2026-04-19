# tests/unit/test_agent_tools.py
# Unit tests for app/lib/agent/tools.py
# Verifies all 10 tool function signatures, return shapes, and basic behavior.
# Does NOT call the Anthropic API.
import inspect

import pytest

from app.lib.seed.seed import seed
from app.lib.catalog.store import products_db
from app.lib.orders.store import orders_db
from app.lib.cart.store import carts_db
from app.lib.auth.store import users_db


@pytest.fixture(autouse=True)
def seed_stores():
    """Seed all in-memory stores before each test."""
    products_db.clear()
    orders_db.clear()
    carts_db.clear()
    users_db.clear()
    seed()
    yield
    products_db.clear()
    orders_db.clear()
    carts_db.clear()
    users_db.clear()


EXPECTED_TOOLS = [
    "search_products",
    "get_product_details",
    "add_to_cart",
    "view_cart",
    "checkout",
    "place_order",
    "check_order_status",
    "cancel_order",
    "return_order",
    "reset_password",
]


class TestToolSignatures:
    """All 10 tool functions exist, are async, and accept user_id as first param."""

    @pytest.mark.parametrize("tool_name", EXPECTED_TOOLS)
    def test_tool_exists_and_is_async(self, tool_name: str) -> None:
        from app.lib.agent import tools
        fn = getattr(tools, tool_name, None)
        assert fn is not None, f"Tool missing: {tool_name}"
        assert inspect.iscoroutinefunction(fn), f"{tool_name} must be async"

    @pytest.mark.parametrize("tool_name", EXPECTED_TOOLS)
    def test_tool_has_user_id_param(self, tool_name: str) -> None:
        from app.lib.agent import tools
        fn = getattr(tools, tool_name)
        sig = inspect.signature(fn)
        assert "user_id" in sig.parameters, f"{tool_name} missing user_id param"
        # user_id must be first positional parameter
        params = list(sig.parameters.keys())
        assert params[0] == "user_id", f"{tool_name}: user_id must be first param, got {params[0]}"


class TestSearchProducts:
    async def test_search_returns_success_dict(self) -> None:
        from app.lib.agent.tools import search_products
        result = await search_products("test-user", q="running")
        assert result["success"] is True
        assert "products" in result["data"]
        assert isinstance(result["data"]["products"], list)
        assert "count" in result["data"]

    async def test_search_empty_query_returns_all(self) -> None:
        from app.lib.agent.tools import search_products
        result = await search_products("test-user")
        assert result["success"] is True
        assert result["data"]["count"] > 0

    async def test_search_no_results_still_succeeds(self) -> None:
        from app.lib.agent.tools import search_products
        result = await search_products("test-user", q="xyznonexistentshoe99999")
        assert result["success"] is True
        assert result["data"]["count"] == 0


class TestGetProductDetails:
    async def test_valid_product_returns_details(self) -> None:
        from app.lib.agent.tools import get_product_details
        product_id = list(products_db.keys())[0]
        result = await get_product_details("test-user", product_id)
        assert result["success"] is True
        assert "product" in result["data"]
        assert result["data"]["product"]["id"] == product_id

    async def test_invalid_product_id_returns_not_found(self) -> None:
        from app.lib.agent.tools import get_product_details
        result = await get_product_details("test-user", "nonexistent-uuid-00000")
        assert result["success"] is False
        assert result["code"] == "PRODUCT_NOT_FOUND"
        assert result["retryable"] is False


class TestCheckOrderStatus:
    async def test_wrong_user_cannot_access_order(self) -> None:
        """Cross-user order access returns UNAUTHORIZED — D-15 enforcement."""
        from app.lib.agent.tools import check_order_status
        # Get a seeded order that belongs to alice or bob
        order_id = list(orders_db.keys())[0]
        # Use a different user_id — should be denied
        result = await check_order_status("attacker-user-id", order_id)
        # Service returns UNAUTHORIZED or ORDER_NOT_FOUND — either is acceptable
        assert result["success"] is False
        assert result["code"] in ("UNAUTHORIZED", "ORDER_NOT_FOUND")

    async def test_nonexistent_order_returns_failure(self) -> None:
        from app.lib.agent.tools import check_order_status
        result = await check_order_status("test-user", "nonexistent-order-id")
        assert result["success"] is False


class TestCheckoutValidation:
    async def test_invalid_payment_method_returns_failure(self) -> None:
        from app.lib.agent.tools import checkout
        result = await checkout("test-user", payment_method="bitcoin")
        assert result["success"] is False
        assert result["code"] == "INVALID_PAYMENT_METHOD"
        assert result["retryable"] is False
