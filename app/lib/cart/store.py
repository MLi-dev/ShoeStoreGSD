# app/lib/cart/store.py
# In-memory Cart store. Keyed by user_id (one cart per user).
# Not populated by seed() in Phase 1 — empty until Phase 2+ API adds to it.
from app.lib.cart.models import Cart

carts_db: dict[str, Cart] = {}
