# tests/unit/test_stores.py
# D-11: store CRUD tests for users_db, products_db, carts_db, orders_db.
# Per 01-RESEARCH.md Pitfall 2 + Pattern 7: autouse fixture clears stores before and after each test
# to prevent module-level dict state bleed between tests.
import pytest

from app.lib.auth.models import User
from app.lib.auth.store import users_db
from app.lib.cart.models import Cart, CartItem
from app.lib.cart.store import carts_db
from app.lib.catalog.models import Product
from app.lib.catalog.store import products_db
from app.lib.orders.models import Order, OrderItem
from app.lib.orders.store import orders_db


@pytest.fixture(autouse=True)
def clear_all_stores():
    users_db.clear()
    products_db.clear()
    carts_db.clear()
    orders_db.clear()
    yield
    users_db.clear()
    products_db.clear()
    carts_db.clear()
    orders_db.clear()


# ---- products_db ----

def test_add_and_get_product():
    p = Product(
        id="p1", name="X", description="", unit_price=1.0, inventory=1, category="running"
    )
    products_db["p1"] = p
    assert products_db.get("p1") is p


def test_list_products():
    for i in range(3):
        products_db[str(i)] = Product(
            id=str(i),
            name=f"P{i}",
            description="",
            unit_price=1.0,
            inventory=1,
            category="running",
        )
    assert len(products_db) == 3
    assert {p.name for p in products_db.values()} == {"P0", "P1", "P2"}


def test_missing_product_returns_none():
    assert products_db.get("nonexistent") is None


# ---- users_db ----

def test_add_and_get_user():
    u = User(id="u1", email="a@b.com", password_hash="$2b$12$x", created_at="t")
    users_db["u1"] = u
    assert users_db.get("u1") is u


def test_list_users():
    for i in range(2):
        users_db[str(i)] = User(
            id=str(i), email=f"{i}@x.com", password_hash="$2b$12$x", created_at="t"
        )
    assert len(users_db) == 2


# ---- carts_db ----

def test_add_and_get_cart():
    c = Cart(user_id="u1", items=[CartItem(product_id="p1", quantity=1, unit_price=1.0)])
    carts_db["u1"] = c
    assert carts_db.get("u1") is c
    assert carts_db["u1"].items[0].product_id == "p1"


# ---- orders_db ----

def test_add_and_get_order():
    o = Order(
        id="o1",
        user_id="u1",
        items=[OrderItem(product_id="p1", quantity=1, unit_price=1.0)],
        total_amount=1.0,
        payment_method="credit_card",
        payment_status="paid",
        order_status="paid",
        created_at="t",
        updated_at="t",
    )
    orders_db["o1"] = o
    assert orders_db.get("o1") is o


def test_list_orders():
    for i in range(3):
        orders_db[str(i)] = Order(
            id=str(i),
            user_id="u1",
            items=[],
            total_amount=0.0,
            payment_method="credit_card",
            payment_status="paid",
            order_status="placed",
            created_at="t",
            updated_at="t",
        )
    assert len(orders_db) == 3


def test_store_isolation_between_tests_pass_1():
    """This test adds data; test_store_isolation_between_tests_pass_2 verifies the fixture cleared it."""
    products_db["isolation-marker"] = Product(
        id="isolation-marker",
        name="I",
        description="",
        unit_price=1.0,
        inventory=1,
        category="running",
    )
    assert "isolation-marker" in products_db


def test_store_isolation_between_tests_pass_2():
    """The autouse fixture must have cleared products_db before this test runs."""
    assert "isolation-marker" not in products_db
