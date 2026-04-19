# tests/unit/test_cart_service.py
# TDD RED phase: failing tests for cart_service.py
import pytest

from app.lib.cart.models import Cart, CartItem
from app.lib.cart.store import carts_db
from app.lib.catalog.models import Product
from app.lib.catalog.store import products_db


@pytest.fixture(autouse=True)
def clear_stores():
    """Reset in-memory stores before each test."""
    carts_db.clear()
    products_db.clear()
    yield
    carts_db.clear()
    products_db.clear()


def make_product(
    product_id: str = "prod-1",
    unit_price: float = 99.99,
    inventory: int = 10,
) -> Product:
    return Product(
        id=product_id,
        name="Test Shoe",
        description="A test shoe",
        unit_price=unit_price,
        inventory=inventory,
        category="sneaker",
    )


# --- add_item ---


@pytest.mark.asyncio
async def test_add_item_product_not_found():
    from app.lib.cart.cart_service import add_item

    result = await add_item("user-1", "nonexistent", 1)
    assert result["success"] is False
    assert result["code"] == "PRODUCT_NOT_FOUND"
    assert result["retryable"] is False


@pytest.mark.asyncio
async def test_add_item_out_of_stock():
    from app.lib.cart.cart_service import add_item

    products_db["prod-1"] = make_product(inventory=0)
    result = await add_item("user-1", "prod-1", 1)
    assert result["success"] is False
    assert result["code"] == "OUT_OF_STOCK"
    assert result["retryable"] is False


@pytest.mark.asyncio
async def test_add_item_creates_cart_and_item():
    from app.lib.cart.cart_service import add_item

    products_db["prod-1"] = make_product()
    result = await add_item("user-1", "prod-1", 2)
    assert result["success"] is True
    cart = result["data"]["cart"]
    assert cart["user_id"] == "user-1"
    assert len(cart["items"]) == 1
    assert cart["items"][0]["product_id"] == "prod-1"
    assert cart["items"][0]["quantity"] == 2
    assert cart["items"][0]["unit_price"] == 99.99


@pytest.mark.asyncio
async def test_add_item_merges_duplicate_product():
    """Adding the same product twice increments quantity (D-08)."""
    from app.lib.cart.cart_service import add_item

    products_db["prod-1"] = make_product()
    await add_item("user-1", "prod-1", 2)
    result = await add_item("user-1", "prod-1", 3)
    assert result["success"] is True
    cart = result["data"]["cart"]
    assert len(cart["items"]) == 1
    assert cart["items"][0]["quantity"] == 5


@pytest.mark.asyncio
async def test_add_item_multiple_distinct_products():
    from app.lib.cart.cart_service import add_item

    products_db["prod-1"] = make_product("prod-1")
    products_db["prod-2"] = make_product("prod-2", unit_price=49.99)
    await add_item("user-1", "prod-1", 1)
    result = await add_item("user-1", "prod-2", 1)
    assert result["success"] is True
    cart = result["data"]["cart"]
    assert len(cart["items"]) == 2


# --- update_quantity ---


@pytest.mark.asyncio
async def test_update_quantity_cart_not_found():
    from app.lib.cart.cart_service import update_quantity

    result = await update_quantity("user-1", "prod-1", 5)
    assert result["success"] is False
    assert result["code"] == "CART_NOT_FOUND"


@pytest.mark.asyncio
async def test_update_quantity_item_not_in_cart():
    from app.lib.cart.cart_service import update_quantity

    carts_db["user-1"] = Cart(user_id="user-1")
    result = await update_quantity("user-1", "prod-99", 5)
    assert result["success"] is False
    assert result["code"] == "ITEM_NOT_IN_CART"


@pytest.mark.asyncio
async def test_update_quantity_success():
    from app.lib.cart.cart_service import add_item, update_quantity

    products_db["prod-1"] = make_product()
    await add_item("user-1", "prod-1", 2)
    result = await update_quantity("user-1", "prod-1", 7)
    assert result["success"] is True
    cart = result["data"]["cart"]
    assert cart["items"][0]["quantity"] == 7


@pytest.mark.asyncio
async def test_update_quantity_zero_removes_item():
    from app.lib.cart.cart_service import add_item, update_quantity

    products_db["prod-1"] = make_product()
    await add_item("user-1", "prod-1", 2)
    result = await update_quantity("user-1", "prod-1", 0)
    assert result["success"] is True
    assert result["data"]["cart"]["items"] == []


# --- remove_item ---


def test_remove_item_cart_not_found():
    from app.lib.cart.cart_service import remove_item

    result = remove_item("user-1", "prod-1")
    assert result["success"] is False
    assert result["code"] == "CART_NOT_FOUND"


def test_remove_item_item_not_in_cart():
    from app.lib.cart.cart_service import remove_item

    carts_db["user-1"] = Cart(user_id="user-1")
    result = remove_item("user-1", "prod-99")
    assert result["success"] is False
    assert result["code"] == "ITEM_NOT_IN_CART"


def test_remove_item_success():
    from app.lib.cart.cart_service import remove_item

    cart = Cart(user_id="user-1", items=[CartItem("prod-1", 2, 99.99)])
    carts_db["user-1"] = cart
    result = remove_item("user-1", "prod-1")
    assert result["success"] is True
    assert result["data"]["cart"]["items"] == []


# --- get_cart ---


def test_get_cart_no_cart_returns_empty():
    from app.lib.cart.cart_service import get_cart

    result = get_cart("user-1")
    assert result["success"] is True
    cart = result["data"]["cart"]
    assert cart["user_id"] == "user-1"
    assert cart["items"] == []
    assert cart["total"] == 0.0


def test_get_cart_with_items_includes_total():
    from app.lib.cart.cart_service import get_cart

    cart = Cart(
        user_id="user-1",
        items=[CartItem("prod-1", 2, 99.99), CartItem("prod-2", 1, 49.99)],
    )
    carts_db["user-1"] = cart
    result = get_cart("user-1")
    assert result["success"] is True
    data = result["data"]["cart"]
    assert len(data["items"]) == 2
    assert abs(data["total"] - (2 * 99.99 + 49.99)) < 0.001


# --- get_cart_total ---


def test_get_cart_total_empty_cart():
    from app.lib.cart.cart_service import get_cart_total

    result = get_cart_total("user-1")
    assert result["success"] is True
    assert result["data"]["total"] == 0.0


def test_get_cart_total_with_items():
    from app.lib.cart.cart_service import get_cart_total

    cart = Cart(
        user_id="user-1",
        items=[CartItem("prod-1", 3, 10.0), CartItem("prod-2", 2, 25.0)],
    )
    carts_db["user-1"] = cart
    result = get_cart_total("user-1")
    assert result["success"] is True
    assert result["data"]["total"] == 80.0  # 3*10 + 2*25


# --- clear_cart ---


def test_clear_cart_idempotent_when_no_cart():
    from app.lib.cart.cart_service import clear_cart

    result = clear_cart("user-1")
    assert result["success"] is True
    assert "cleared" in result["data"]["message"].lower()


def test_clear_cart_removes_items():
    from app.lib.cart.cart_service import clear_cart

    cart = Cart(user_id="user-1", items=[CartItem("prod-1", 2, 99.99)])
    carts_db["user-1"] = cart
    result = clear_cart("user-1")
    assert result["success"] is True
    assert "user-1" not in carts_db or carts_db["user-1"].items == []


# ---------------------------------------------------------------------------
# Required named aliases (plan 02-03 acceptance criteria)
# ---------------------------------------------------------------------------


def _seed_product(product_id: str = "p1", inventory: int = 5, price: float = 99.0):
    p = Product(
        id=product_id,
        name="Test Shoe",
        description="",
        unit_price=price,
        inventory=inventory,
        category="running",
    )
    products_db[product_id] = p
    return p


@pytest.mark.asyncio
async def test_add_item_success():
    from app.lib.cart.cart_service import add_item

    _seed_product("p1", inventory=5, price=99.0)
    result = await add_item("u1", "p1", 2)
    assert result["success"] is True
    assert result["data"]["cart"]["items"][0]["product_id"] == "p1"
    assert result["data"]["cart"]["items"][0]["quantity"] == 2


@pytest.mark.asyncio
async def test_add_item_zero_inventory_rejected():
    from app.lib.cart.cart_service import add_item

    _seed_product("p1", inventory=0)
    result = await add_item("u1", "p1", 1)
    assert result["success"] is False
    assert result["code"] == "OUT_OF_STOCK"


@pytest.mark.asyncio
async def test_add_item_merge_same_product():
    from app.lib.cart.cart_service import add_item

    _seed_product("p1", inventory=10)
    await add_item("u1", "p1", 2)
    result = await add_item("u1", "p1", 3)
    cart_data = result["data"]["cart"]
    assert len(cart_data["items"]) == 1
    assert cart_data["items"][0]["quantity"] == 5


@pytest.mark.asyncio
async def test_cart_total():
    from app.lib.cart.cart_service import add_item, get_cart_total

    _seed_product("p1", inventory=10, price=50.0)
    _seed_product("p2", inventory=10, price=30.0)
    await add_item("u1", "p1", 2)
    await add_item("u1", "p2", 3)
    result = get_cart_total("u1")
    assert result["success"] is True
    assert result["data"]["total"] == 190.0  # 2*50 + 3*30


@pytest.mark.asyncio
async def test_update_quantity():
    from app.lib.cart.cart_service import add_item, update_quantity

    _seed_product("p1", inventory=10)
    await add_item("u1", "p1", 2)
    result = await update_quantity("u1", "p1", 5)
    assert result["success"] is True
    item = result["data"]["cart"]["items"][0]
    assert item["quantity"] == 5


@pytest.mark.asyncio
async def test_remove_item():
    from app.lib.cart.cart_service import add_item, remove_item

    _seed_product("p1", inventory=5)
    await add_item("u1", "p1", 1)
    result = remove_item("u1", "p1")
    assert result["success"] is True
    assert result["data"]["cart"]["items"] == []


def test_get_cart_empty():
    from app.lib.cart.cart_service import get_cart

    result = get_cart("u1")
    assert result["success"] is True
    assert result["data"]["cart"]["items"] == []
    assert result["data"]["cart"]["total"] == 0.0
