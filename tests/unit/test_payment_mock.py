# tests/unit/test_payment_mock.py
import pytest
from config import FAILURE_CONFIG

@pytest.fixture(autouse=True)
def reset_failure_config():
    original_payment = dict(FAILURE_CONFIG.get("payment", {}))
    yield
    FAILURE_CONFIG["payment"] = original_payment

# MOCK-02: charge failure injection for all 3 methods
@pytest.mark.xfail(strict=False, reason="implementation pending")
@pytest.mark.parametrize("method", ["credit_card", "paypal", "apple_pay"])
def test_charge_always_fails_at_prob_1(method):
    from app.lib.mocks import payment_mock
    FAILURE_CONFIG["payment"][f"failed_to_charge_{method}"] = 1.0
    result = payment_mock.charge("ord-1", method, 99.99)
    assert result["success"] is False
    assert result["code"] == f"FAILED_TO_CHARGE_{method.upper()}"

@pytest.mark.xfail(strict=False, reason="implementation pending")
@pytest.mark.parametrize("method", ["credit_card", "paypal", "apple_pay"])
def test_charge_always_succeeds_at_prob_0(method):
    from app.lib.mocks import payment_mock
    FAILURE_CONFIG["payment"][f"failed_to_charge_{method}"] = 0.0
    result = payment_mock.charge("ord-1", method, 99.99)
    assert result["success"] is True

@pytest.mark.xfail(strict=False, reason="implementation pending")
@pytest.mark.parametrize("method", ["credit_card", "paypal", "apple_pay"])
def test_refund_always_fails_at_prob_1(method):
    from app.lib.mocks import payment_mock
    FAILURE_CONFIG["payment"][f"failed_to_refund_{method}"] = 1.0
    result = payment_mock.refund("ord-1", method, 99.99)
    assert result["success"] is False
    assert result["code"] == f"FAILED_TO_REFUND_{method.upper()}"

@pytest.mark.xfail(strict=False, reason="implementation pending")
@pytest.mark.parametrize("method", ["credit_card", "paypal", "apple_pay"])
def test_refund_always_succeeds_at_prob_0(method):
    from app.lib.mocks import payment_mock
    FAILURE_CONFIG["payment"][f"failed_to_refund_{method}"] = 0.0
    result = payment_mock.refund("ord-1", method, 99.99)
    assert result["success"] is True
