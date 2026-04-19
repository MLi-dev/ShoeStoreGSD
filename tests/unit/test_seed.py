# tests/unit/test_seed.py
# CAT-01, CAT-04, SEED-01, SEED-02 coverage.
# Source of patterns: .planning/phases/01-domain-foundation/01-PATTERNS.md test_seed.py section.
import pytest

from app.lib.auth.store import users_db
from app.lib.catalog.store import products_db
from app.lib.orders.store import orders_db
from app.lib.seed.seed import clear_and_reseed, seed


@pytest.fixture(autouse=True)
def reset_stores():
    users_db.clear()
    products_db.clear()
    orders_db.clear()
    yield
    users_db.clear()
    products_db.clear()
    orders_db.clear()


# ---- CAT-01: 15 products across 5 categories ----

def test_seed_product_count():
    clear_and_reseed()
    assert len(products_db) == 15, (
        f"Expected 15 products per D-05; got {len(products_db)}"
    )


def test_products_cover_all_categories():
    clear_and_reseed()
    categories = {p.category for p in products_db.values()}
    assert categories == {"running", "hiking", "slides", "sandals", "socks"}


def test_products_three_per_category():
    clear_and_reseed()
    counts: dict[str, int] = {}
    for p in products_db.values():
        counts[p.category] = counts.get(p.category, 0) + 1
    for cat in ("running", "hiking", "slides", "sandals", "socks"):
        assert counts.get(cat, 0) == 3, (
            f"Expected 3 products in category '{cat}' per D-05; got {counts.get(cat, 0)}"
        )


def test_products_have_required_fields():
    clear_and_reseed()
    for p in products_db.values():
        assert p.name, f"Product {p.id} missing name"
        assert p.description, f"Product {p.id} missing description"
        assert p.unit_price > 0, f"Product {p.id} has non-positive price"
        assert p.inventory >= 0, f"Product {p.id} has negative inventory"
        assert p.category, f"Product {p.id} missing category"
        assert isinstance(p.id, str) and len(p.id) > 0


def test_product_prices_in_demo_range():
    """D-04: realistic demo pricing $49-$189."""
    clear_and_reseed()
    for p in products_db.values():
        assert 49.0 <= p.unit_price <= 189.0, (
            f"Product {p.name} price ${p.unit_price} outside $49-$189 demo range per D-04"
        )


# ---- CAT-04: variants ----

def test_products_have_variants():
    clear_and_reseed()
    for product in products_db.values():
        assert len(product.variants) >= 1, f"{product.name} has no variants (CAT-04)"


def test_variants_have_size_or_color():
    clear_and_reseed()
    for product in products_db.values():
        for v in product.variants:
            assert v.size is not None or v.color is not None, (
                f"Product {product.name} has a variant with neither size nor color"
            )


# ---- SEED-01: 2 test users with hashed passwords ----

def test_seed_user_count():
    clear_and_reseed()
    assert len(users_db) == 2, f"Expected 2 users per D-06; got {len(users_db)}"


def test_alice_and_bob_seeded():
    clear_and_reseed()
    emails = {u.email for u in users_db.values()}
    assert "alice@example.com" in emails, "alice@example.com not seeded (D-06)"
    assert "bob@example.com" in emails, "bob@example.com not seeded (D-06)"


def test_passwords_are_hashed():
    """Threat T-crypto: passwords must be bcrypt hashed, never plaintext."""
    clear_and_reseed()
    for user in users_db.values():
        assert user.password_hash.startswith("$2b$"), (
            f"User {user.email} password_hash {user.password_hash!r} not bcrypt format"
        )
        # No plaintext substrings should appear in the hash
        lowered = user.password_hash.lower()
        assert "password" not in lowered, "Literal 'password' found in hash"
        assert "alice" not in lowered, "Email substring 'alice' found in hash"
        assert "bob" not in lowered, "Email substring 'bob' found in hash"


# ---- SEED-02: 3 prior orders (paid, shipped, canceled) ----

def test_seed_order_count():
    clear_and_reseed()
    assert len(orders_db) == 3, f"Expected 3 seeded orders per D-07; got {len(orders_db)}"


def test_seed_order_statuses():
    clear_and_reseed()
    statuses = {o.order_status for o in orders_db.values()}
    assert "paid" in statuses, "Missing 'paid' order (SEED-02)"
    assert "shipped" in statuses, "Missing 'shipped' order (SEED-02)"
    assert "canceled" in statuses, "Missing 'canceled' order (SEED-02)"


def test_seeded_orders_reference_seeded_users():
    """Cross-store integrity: every order.user_id must exist in users_db."""
    clear_and_reseed()
    user_ids = set(users_db.keys())
    for order in orders_db.values():
        assert order.user_id in user_ids, (
            f"Order {order.id} references missing user {order.user_id}"
        )


def test_seeded_orders_have_items():
    clear_and_reseed()
    for order in orders_db.values():
        assert len(order.items) >= 1, f"Order {order.id} has no items"
        assert order.total_amount > 0, f"Order {order.id} has non-positive total"


# ---- Idempotency ----

def test_clear_and_reseed_is_idempotent():
    clear_and_reseed()
    first_products = len(products_db)
    first_users = len(users_db)
    first_orders = len(orders_db)

    clear_and_reseed()
    assert len(products_db) == first_products == 15
    assert len(users_db) == first_users == 2
    assert len(orders_db) == first_orders == 3


def test_seed_can_be_called_directly():
    """seed() (without clear) also populates stores when stores are empty."""
    seed()
    assert len(products_db) == 15
    assert len(users_db) == 2
    assert len(orders_db) == 3
