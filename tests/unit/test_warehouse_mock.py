# tests/unit/test_warehouse_mock.py
import pytest
from config import FAILURE_CONFIG

@pytest.fixture(autouse=True)
def reset_failure_config():
    original_warehouse = dict(FAILURE_CONFIG.get("warehouse", {}))
    yield
    FAILURE_CONFIG["warehouse"] = original_warehouse

# MOCK-01: reserve_inventory failure injection
@pytest.mark.xfail(strict=False, reason="implementation pending")
def test_reserve_inventory_always_fails_at_prob_1():
    from app.lib.mocks import warehouse_mock
    FAILURE_CONFIG["warehouse"]["out_of_stock"] = 1.0
    result = warehouse_mock.reserve_inventory("ord-1", [])
    assert result["success"] is False
    assert result["code"] == "OUT_OF_STOCK"

@pytest.mark.xfail(strict=False, reason="implementation pending")
def test_reserve_inventory_always_succeeds_at_prob_0():
    from app.lib.mocks import warehouse_mock
    FAILURE_CONFIG["warehouse"]["out_of_stock"] = 0.0
    result = warehouse_mock.reserve_inventory("ord-1", [])
    assert result["success"] is True

@pytest.mark.xfail(strict=False, reason="implementation pending")
def test_cancel_order_always_fails_at_prob_1():
    from app.lib.mocks import warehouse_mock
    FAILURE_CONFIG["warehouse"]["failed_to_cancel_order"] = 1.0
    result = warehouse_mock.cancel_order("ord-1")
    assert result["success"] is False
    assert result["code"] == "FAILED_TO_CANCEL_ORDER"

@pytest.mark.xfail(strict=False, reason="implementation pending")
def test_cancel_order_always_succeeds_at_prob_0():
    from app.lib.mocks import warehouse_mock
    FAILURE_CONFIG["warehouse"]["failed_to_cancel_order"] = 0.0
    result = warehouse_mock.cancel_order("ord-1")
    assert result["success"] is True

@pytest.mark.xfail(strict=False, reason="implementation pending")
def test_get_available_quantity_returns_success():
    from app.lib.mocks import warehouse_mock
    result = warehouse_mock.get_available_quantity("prod-1")
    assert result["success"] is True

@pytest.mark.xfail(strict=False, reason="implementation pending")
def test_ship_order_returns_success():
    from app.lib.mocks import warehouse_mock
    result = warehouse_mock.ship_order("ord-1")
    assert result["success"] is True
