# tests/unit/test_root_instruction.py
# Unit tests for parse_root_instruction() — TDD RED phase.
# 8 behavior cases from 05-01-PLAN.md Task 1.
import pytest

from app.lib.guardrails.root_instruction import parse_root_instruction


def test_warehouse_out_of_stock():
    result = parse_root_instruction("warehouse out_of_stock 50%")
    assert result["success"] is True
    assert result["mutations"] == {"warehouse": {"out_of_stock": 0.5}}


def test_payment_fail_all_methods():
    result = parse_root_instruction("payment fail 100%")
    assert result["success"] is True
    assert result["mutations"] == {
        "payment": {
            "failed_to_charge_credit_card": 1.0,
            "failed_to_charge_paypal": 1.0,
            "failed_to_charge_apple_pay": 1.0,
        }
    }


def test_payment_fail_specific_method():
    result = parse_root_instruction("payment fail 30% credit card")
    assert result["success"] is True
    assert result["mutations"] == {"payment": {"failed_to_charge_credit_card": 0.3}}


def test_refund_fail_specific_method():
    result = parse_root_instruction("refund fail 75% apple pay")
    assert result["success"] is True
    assert result["mutations"] == {"payment": {"failed_to_refund_apple_pay": 0.75}}


def test_warehouse_cancel_fail():
    result = parse_root_instruction("warehouse cancel fail 20%")
    assert result["success"] is True
    assert result["mutations"] == {"warehouse": {"failed_to_cancel_order": 0.2}}


def test_disable_all_failures():
    result = parse_root_instruction("disable all failures")
    assert result["success"] is True
    mutations = result["mutations"]
    assert mutations["warehouse"]["out_of_stock"] == 0.0
    assert mutations["warehouse"]["failed_to_cancel_order"] == 0.0
    assert mutations["payment"]["failed_to_charge_credit_card"] == 0.0
    assert mutations["payment"]["failed_to_charge_paypal"] == 0.0
    assert mutations["payment"]["failed_to_charge_apple_pay"] == 0.0
    assert mutations["payment"]["failed_to_refund_credit_card"] == 0.0
    assert mutations["payment"]["failed_to_refund_paypal"] == 0.0
    assert mutations["payment"]["failed_to_refund_apple_pay"] == 0.0


def test_disable_all_resets_all_eight_keys():
    result = parse_root_instruction("disable all failures")
    warehouse_keys = set(result["mutations"]["warehouse"].keys())
    payment_keys = set(result["mutations"]["payment"].keys())
    assert warehouse_keys == {"out_of_stock", "failed_to_cancel_order"}
    assert payment_keys == {
        "failed_to_charge_credit_card",
        "failed_to_charge_paypal",
        "failed_to_charge_apple_pay",
        "failed_to_refund_credit_card",
        "failed_to_refund_paypal",
        "failed_to_refund_apple_pay",
    }


def test_unknown_instruction():
    result = parse_root_instruction("set everything to chaos")
    assert result["success"] is False
    assert result["mutations"] == {}
    assert "Unknown root instruction" in result["message"]
    assert "set everything to chaos" in result["message"]
