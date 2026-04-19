# tests/unit/test_models.py
# D-11: model instantiation tests for User, Product, Variant, Cart, CartItem, Order, OrderItem.
# Source of pattern: .planning/phases/01-domain-foundation/01-PATTERNS.md test_models.py section.
from app.lib.auth.models import User
from app.lib.cart.models import Cart, CartItem
from app.lib.catalog.models import Product, Variant
from app.lib.orders.models import Order, OrderItem


def test_user_instantiation():
    user = User(
        id="u1",
        email="test@example.com",
        password_hash="$2b$12$dummy-hash-value",
        created_at="2026-01-01T00:00:00+00:00",
    )
    assert user.id == "u1"
    assert user.email == "test@example.com"
    assert user.password_hash.startswith("$2b$")
    assert user.created_at == "2026-01-01T00:00:00+00:00"


def test_variant_all_optional():
    v = Variant()
    assert v.size is None
    assert v.color is None

    v2 = Variant(size="10", color="black")
    assert v2.size == "10"
    assert v2.color == "black"


def test_product_instantiation():
    product = Product(
        id="p1",
        name="Test Shoe",
        description="A test shoe",
        unit_price=99.99,
        inventory=10,
        category="running",
    )
    assert product.id == "p1"
    assert product.name == "Test Shoe"
    assert product.unit_price == 99.99
    assert product.inventory == 10
    assert product.category == "running"
    assert product.image_url is None
    assert product.variants == []


def test_product_variants_default_empty():
    product = Product(
        id="p1", name="n", description="d", unit_price=1.0, inventory=1, category="running"
    )
    assert product.variants == []


def test_two_products_do_not_share_variants():
    """Regression test for shared-mutable-default bug (01-RESEARCH.md Pitfall 1)."""
    p1 = Product(
        id="p1", name="A", description="", unit_price=1.0, inventory=1, category="running"
    )
    p2 = Product(
        id="p2", name="B", description="", unit_price=1.0, inventory=1, category="running"
    )
    p1.variants.append(Variant(size="10"))
    assert len(p1.variants) == 1
    assert len(p2.variants) == 0, "Two Product instances share the same variants list (shared-mutable-default bug)"


def test_cart_item_instantiation():
    item = CartItem(product_id="p1", quantity=2, unit_price=49.99)
    assert item.product_id == "p1"
    assert item.quantity == 2
    assert item.unit_price == 49.99


def test_cart_instantiation():
    cart = Cart(user_id="u1")
    assert cart.user_id == "u1"
    assert cart.items == []


def test_two_carts_do_not_share_items():
    """Regression test for shared-mutable-default bug on Cart.items."""
    c1 = Cart(user_id="u1")
    c2 = Cart(user_id="u2")
    c1.items.append(CartItem(product_id="p1", quantity=1, unit_price=1.0))
    assert len(c1.items) == 1
    assert len(c2.items) == 0


def test_order_item_instantiation():
    item = OrderItem(product_id="p1", quantity=1, unit_price=89.99)
    assert item.product_id == "p1"
    assert item.quantity == 1
    assert item.unit_price == 89.99


def test_order_instantiation():
    order = Order(
        id="o1",
        user_id="u1",
        items=[OrderItem(product_id="p1", quantity=1, unit_price=89.99)],
        total_amount=89.99,
        payment_method="credit_card",
        payment_status="paid",
        order_status="paid",
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )
    assert order.id == "o1"
    assert order.user_id == "u1"
    assert len(order.items) == 1
    assert order.items[0].product_id == "p1"
    assert order.total_amount == 89.99
    assert order.payment_method == "credit_card"
    assert order.payment_status == "paid"
    assert order.order_status == "paid"


def test_order_accepts_all_status_literals():
    """Runtime does not enforce Literal, but instances constructed with each valid value must work."""
    for status in ("placed", "paid", "processing", "shipped", "canceled", "returned"):
        order = Order(
            id=f"o-{status}",
            user_id="u1",
            items=[],
            total_amount=0.0,
            payment_method="credit_card",
            payment_status="paid",
            order_status=status,  # type: ignore[arg-type]
            created_at="t",
            updated_at="t",
        )
        assert order.order_status == status
