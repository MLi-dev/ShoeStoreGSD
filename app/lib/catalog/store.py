# app/lib/catalog/store.py
# In-memory Product store. Keyed by Product.id (UUID string).
# Empty at import time; populated by app.lib.seed.seed.seed() at startup.
from app.lib.catalog.models import Product

products_db: dict[str, Product] = {}
