# tests/unit/test_catalog_service.py
import pytest
from app.lib.catalog.store import products_db
from app.lib.catalog.models import Product, Variant

@pytest.fixture(autouse=True)
def clear_stores():
    products_db.clear()
    yield
    products_db.clear()

def make_product(
    product_id: str = "prod-1",
    name: str = "Trail Runner",
    description: str = "A running shoe",
    unit_price: float = 89.99,
    inventory: int = 10,
    category: str = "running",
) -> Product:
    return Product(
        id=product_id,
        name=name,
        description=description,
        unit_price=unit_price,
        inventory=inventory,
        category=category,
    )

# CAT-02: keyword search
@pytest.mark.xfail(strict=False, reason="implementation pending")
def test_search_products_by_keyword_in_name():
    products_db["prod-1"] = make_product(name="Trail Runner")
    from app.lib.catalog import catalog_service
    results = catalog_service.search_products(q="trail")
    assert any(p.id == "prod-1" for p in results)

@pytest.mark.xfail(strict=False, reason="implementation pending")
def test_search_products_by_keyword_in_description():
    products_db["prod-1"] = make_product(description="great for hiking trails")
    from app.lib.catalog import catalog_service
    results = catalog_service.search_products(q="hiking")
    assert any(p.id == "prod-1" for p in results)

@pytest.mark.xfail(strict=False, reason="implementation pending")
def test_search_products_by_category():
    products_db["prod-1"] = make_product(category="hiking")
    products_db["prod-2"] = make_product(product_id="prod-2", category="running")
    from app.lib.catalog import catalog_service
    results = catalog_service.search_products(category="hiking")
    assert len(results) == 1 and results[0].id == "prod-1"

@pytest.mark.xfail(strict=False, reason="implementation pending")
def test_search_products_keyword_and_category_combine():
    products_db["prod-1"] = make_product(name="Trail Hiker", category="hiking")
    products_db["prod-2"] = make_product(product_id="prod-2", name="Trail Runner", category="running")
    from app.lib.catalog import catalog_service
    results = catalog_service.search_products(q="trail", category="hiking")
    assert len(results) == 1 and results[0].id == "prod-1"

@pytest.mark.xfail(strict=False, reason="implementation pending")
def test_search_products_case_insensitive():
    products_db["prod-1"] = make_product(name="TRAIL RUNNER")
    from app.lib.catalog import catalog_service
    results = catalog_service.search_products(q="trail runner")
    assert any(p.id == "prod-1" for p in results)

@pytest.mark.xfail(strict=False, reason="implementation pending")
def test_search_products_no_match_returns_empty():
    products_db["prod-1"] = make_product(name="Trail Runner")
    from app.lib.catalog import catalog_service
    results = catalog_service.search_products(q="sandal")
    assert results == []

# CAT-03: get_product
@pytest.mark.xfail(strict=False, reason="implementation pending")
def test_get_product_found():
    products_db["prod-1"] = make_product()
    from app.lib.catalog import catalog_service
    product = catalog_service.get_product("prod-1")
    assert product is not None and product.id == "prod-1"

@pytest.mark.xfail(strict=False, reason="implementation pending")
def test_get_product_not_found():
    from app.lib.catalog import catalog_service
    product = catalog_service.get_product("nonexistent")
    assert product is None
