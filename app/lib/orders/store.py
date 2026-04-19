# app/lib/orders/store.py
# In-memory Order store. Keyed by Order.id (UUID string).
# Empty at import time; populated by app.lib.seed.seed.seed() at startup with 3 prior orders (paid, shipped, canceled) per D-07.
from app.lib.orders.models import Order

orders_db: dict[str, Order] = {}
