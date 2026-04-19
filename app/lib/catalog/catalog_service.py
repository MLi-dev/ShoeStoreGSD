# app/lib/catalog/catalog_service.py
# Catalog business logic: search and detail retrieval.
# Returns Product instances directly (not wrapped dicts) for template consumption.
# Source: .planning/phases/03-web-ui-rest-api/03-CONTEXT.md D-10, D-11
from app.lib.catalog.models import Product
from app.lib.catalog.store import products_db


def search_products(q: str = "", category: str = "") -> list[Product]:
    """Search products by keyword and/or category.

    Case-insensitive substring match across name, description, category (D-10).
    Category filter is applied first; keyword narrows within category (D-11).

    Args:
        q: Optional keyword for substring search.
        category: Optional category filter (exact match, case-insensitive).

    Returns:
        List of matching Product instances (may be empty).
    """
    results: list[Product] = list(products_db.values())
    if category:
        results = [p for p in results if p.category.lower() == category.lower()]
    if q:
        q_lower = q.lower()
        results = [
            p for p in results
            if q_lower in p.name.lower()
            or q_lower in p.description.lower()
            or q_lower in p.category.lower()
        ]
    return results


def get_product(product_id: str) -> Product | None:
    """Retrieve a single product by ID.

    Args:
        product_id: UUID string of the product.

    Returns:
        Product dataclass or None if not found.
    """
    return products_db.get(product_id)
