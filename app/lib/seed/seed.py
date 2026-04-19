# app/lib/seed/seed.py
# Populate in-memory stores with demo-quality reference data.
# Called once from FastAPI lifespan (main.py) before any request is served.
# Requirements: CAT-01, CAT-04, SEED-01, SEED-02. Decisions: D-04 through D-09.
# Source of structure: .planning/phases/01-domain-foundation/01-PATTERNS.md seed.py section.
import uuid
from datetime import datetime, timezone

from passlib.context import CryptContext

from app.lib.auth.models import User
from app.lib.auth.store import users_db
from app.lib.catalog.models import Product, Variant
from app.lib.catalog.store import products_db
from app.lib.orders.models import Order, OrderItem
from app.lib.orders.store import orders_db

# Module-level CryptContext is cheap to create; bcrypt hashing happens only inside
# _seed_users() to avoid slow bcrypt runs at import time (01-RESEARCH.md Pitfall 6).
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Passwords for seeded users. Claude's Discretion per CONTEXT.md; never stored plaintext.
_ALICE_PASSWORD = "alice-demo-password-2026"
_BOB_PASSWORD = "bob-demo-password-2026"


def seed() -> None:
    """Populate all in-memory stores with demo data.

    Called once from FastAPI lifespan before serving requests.
    Idempotent only if stores are cleared first (use clear_and_reseed).
    """
    _seed_users()
    _seed_products()
    _seed_orders()


def clear_and_reseed() -> None:
    """Clear all stores and re-run seed. Useful for test isolation.

    Added per Claude's Discretion in 01-CONTEXT.md (aids test isolation).
    """
    users_db.clear()
    products_db.clear()
    orders_db.clear()
    seed()


def _now() -> str:
    """UTC-aware ISO 8601 timestamp (01-RESEARCH.md Don't-hand-roll table)."""
    return datetime.now(tz=timezone.utc).isoformat()


def _seed_users() -> None:
    now = _now()
    alice = User(
        id=str(uuid.uuid4()),
        email="alice@example.com",
        password_hash=_pwd_context.hash(_ALICE_PASSWORD),
        created_at=now,
    )
    bob = User(
        id=str(uuid.uuid4()),
        email="bob@example.com",
        password_hash=_pwd_context.hash(_BOB_PASSWORD),
        created_at=now,
    )
    users_db[alice.id] = alice
    users_db[bob.id] = bob


def _seed_products() -> None:
    # 15 products, 3 per category, $49-$189, demo-worthy names.
    # Claude's Discretion per D-04 — invent names like "TrailBlaze X9", not "Product 1".
    # Each product gets ≥1 Variant with size and/or color (CAT-04).
    products: list[Product] = []

    # --- running (3) ---
    products.append(Product(
        id=str(uuid.uuid4()),
        name="TrailBlaze X9",
        description="Responsive road runner with a carbon-infused plate and airy mesh upper. Built for sub-20 5K splits.",
        unit_price=149.00,
        inventory=42,
        category="running",
        variants=[
            Variant(size="9", color="midnight black"),
            Variant(size="10", color="midnight black"),
            Variant(size="11", color="solar orange"),
        ],
    ))
    products.append(Product(
        id=str(uuid.uuid4()),
        name="Velocity Pulse",
        description="Daily trainer with plush EVA foam and a reinforced heel cup. Goes from easy miles to tempo without complaint.",
        unit_price=129.00,
        inventory=55,
        category="running",
        variants=[
            Variant(size="8", color="storm gray"),
            Variant(size="9", color="storm gray"),
            Variant(size="10", color="electric teal"),
        ],
    ))
    products.append(Product(
        id=str(uuid.uuid4()),
        name="Stride Horizon Light",
        description="Featherweight racer at under 6 oz. Minimal overlays, maximum ground feel for speed work and races.",
        unit_price=99.00,
        inventory=30,
        category="running",
        variants=[
            Variant(size="9", color="white lightning"),
            Variant(size="10", color="white lightning"),
        ],
    ))

    # --- hiking (3) ---
    products.append(Product(
        id=str(uuid.uuid4()),
        name="Summit Pro Hiker",
        description="Full-grain leather mid-cut with a Vibram-style lug sole. Waterproof membrane keeps feet dry on wet descents.",
        unit_price=189.00,
        inventory=25,
        category="hiking",
        variants=[
            Variant(size="9", color="cedar brown"),
            Variant(size="10", color="cedar brown"),
            Variant(size="11", color="granite"),
        ],
    ))
    products.append(Product(
        id=str(uuid.uuid4()),
        name="Ridge Runner GTX",
        description="Technical trail shoe with an aggressive tread pattern and a precision-fit lacing system. Quick-drying mesh panels.",
        unit_price=159.00,
        inventory=38,
        category="hiking",
        variants=[
            Variant(size="9", color="moss green"),
            Variant(size="10", color="moss green"),
            Variant(size="11", color="volcanic red"),
        ],
    ))
    products.append(Product(
        id=str(uuid.uuid4()),
        name="BaseCamp Classic",
        description="Old-school leather day hiker with a soft EVA midsole and padded ankle collar. Broken-in comfort out of the box.",
        unit_price=119.00,
        inventory=44,
        category="hiking",
        variants=[
            Variant(size="8", color="walnut"),
            Variant(size="9", color="walnut"),
            Variant(size="10", color="espresso"),
        ],
    ))

    # --- slides (3) ---
    products.append(Product(
        id=str(uuid.uuid4()),
        name="CloudSlide Comfort",
        description="Contoured foam bed with a wide footbed and textured top for all-day indoor wear. Recovery shoe favorite.",
        unit_price=59.00,
        inventory=80,
        category="slides",
        variants=[
            Variant(size="M", color="fog white"),
            Variant(size="L", color="fog white"),
            Variant(size="L", color="jet black"),
        ],
    ))
    products.append(Product(
        id=str(uuid.uuid4()),
        name="Pool Deck Pro",
        description="Water-ready EVA slide with deep drainage channels. Non-slip sole for locker rooms and poolside lounging.",
        unit_price=49.00,
        inventory=100,
        category="slides",
        variants=[
            Variant(size="S", color="ocean blue"),
            Variant(size="M", color="ocean blue"),
            Variant(size="L", color="sunset coral"),
        ],
    ))
    products.append(Product(
        id=str(uuid.uuid4()),
        name="LoungeLite Slide",
        description="Memory-foam lined slide with an embroidered logo strap. Your house-to-porch-to-mailbox workhorse.",
        unit_price=69.00,
        inventory=65,
        category="slides",
        variants=[
            Variant(size="M", color="heather gray"),
            Variant(size="L", color="heather gray"),
        ],
    ))

    # --- sandals (3) ---
    products.append(Product(
        id=str(uuid.uuid4()),
        name="CoastWalker Sport",
        description="Adjustable three-strap sandal with a contoured footbed. Quick-drying webbing handles beach-to-trail.",
        unit_price=89.00,
        inventory=50,
        category="sandals",
        variants=[
            Variant(size="9", color="driftwood"),
            Variant(size="10", color="driftwood"),
            Variant(size="11", color="slate"),
        ],
    ))
    products.append(Product(
        id=str(uuid.uuid4()),
        name="Sunset Strap",
        description="Everyday flat sandal with a padded leather footbed and buckle closure. Goes with shorts or a linen dress.",
        unit_price=99.00,
        inventory=40,
        category="sandals",
        variants=[
            Variant(size="7", color="tan"),
            Variant(size="8", color="tan"),
            Variant(size="9", color="black"),
        ],
    ))
    products.append(Product(
        id=str(uuid.uuid4()),
        name="Canyon Trek Sandal",
        description="Rugged closed-toe sandal with a lugged rubber outsole. Built for water crossings and rocky trails.",
        unit_price=109.00,
        inventory=32,
        category="sandals",
        variants=[
            Variant(size="9", color="canyon rust"),
            Variant(size="10", color="canyon rust"),
            Variant(size="11", color="bedrock black"),
        ],
    ))

    # --- socks (3) ---
    products.append(Product(
        id=str(uuid.uuid4()),
        name="Merino Cushion Crew",
        description="Fine-gauge merino wool crew socks with targeted cushioning at heel and forefoot. Pack of 3 pairs.",
        unit_price=49.00,
        inventory=120,
        category="socks",
        variants=[
            Variant(size="M", color="charcoal"),
            Variant(size="L", color="charcoal"),
            Variant(size="L", color="natural"),
        ],
    ))
    products.append(Product(
        id=str(uuid.uuid4()),
        name="PaceSetter No-Show",
        description="Low-profile running socks with silicone heel tabs and a compressive arch band. Pack of 6 pairs.",
        unit_price=55.00,
        inventory=95,
        category="socks",
        variants=[
            Variant(size="S", color="white"),
            Variant(size="M", color="white"),
            Variant(size="L", color="black"),
        ],
    ))
    products.append(Product(
        id=str(uuid.uuid4()),
        name="TrailGuard Hiker Quarter",
        description="Reinforced quarter-length hiking sock with merino-nylon blend. Padded shin and Achilles zones.",
        unit_price=65.00,
        inventory=70,
        category="socks",
        variants=[
            Variant(size="M", color="forest"),
            Variant(size="L", color="forest"),
            Variant(size="L", color="stone"),
        ],
    ))

    for p in products:
        products_db[p.id] = p


def _seed_orders() -> None:
    # Per D-07: 1 paid, 1 shipped, 1 canceled. Split across alice and bob.
    # Orders reference product IDs from products_db — look them up by (name, category) for determinism.
    now = _now()

    # Look up seeded users by email to get their stable UUIDs.
    alice = next(u for u in users_db.values() if u.email == "alice@example.com")
    bob = next(u for u in users_db.values() if u.email == "bob@example.com")

    # Pick 3 distinct seeded products by name — any products will do; use first-found.
    products_by_name = {p.name: p for p in products_db.values()}
    trailblaze = products_by_name["TrailBlaze X9"]
    cloudslide = products_by_name["CloudSlide Comfort"]
    summit = products_by_name["Summit Pro Hiker"]

    # --- Order 1: paid (alice, credit_card, TrailBlaze X9) ---
    paid_items = [OrderItem(product_id=trailblaze.id, quantity=1, unit_price=trailblaze.unit_price)]
    paid_order = Order(
        id=str(uuid.uuid4()),
        user_id=alice.id,
        items=paid_items,
        total_amount=trailblaze.unit_price,
        payment_method="credit_card",
        payment_status="paid",
        order_status="paid",
        created_at=now,
        updated_at=now,
    )
    orders_db[paid_order.id] = paid_order

    # --- Order 2: shipped (bob, paypal, CloudSlide Comfort x2) ---
    shipped_items = [OrderItem(product_id=cloudslide.id, quantity=2, unit_price=cloudslide.unit_price)]
    shipped_total = cloudslide.unit_price * 2
    shipped_order = Order(
        id=str(uuid.uuid4()),
        user_id=bob.id,
        items=shipped_items,
        total_amount=shipped_total,
        payment_method="paypal",
        payment_status="paid",
        order_status="shipped",
        created_at=now,
        updated_at=now,
    )
    orders_db[shipped_order.id] = shipped_order

    # --- Order 3: canceled (alice, apple_pay, Summit Pro Hiker — refunded) ---
    canceled_items = [OrderItem(product_id=summit.id, quantity=1, unit_price=summit.unit_price)]
    canceled_order = Order(
        id=str(uuid.uuid4()),
        user_id=alice.id,
        items=canceled_items,
        total_amount=summit.unit_price,
        payment_method="apple_pay",
        payment_status="refunded",
        order_status="canceled",
        created_at=now,
        updated_at=now,
    )
    orders_db[canceled_order.id] = canceled_order
