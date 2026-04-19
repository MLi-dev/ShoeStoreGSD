# app/lib/orders/models.py
# Orders domain models: Order and OrderItem.
# Source of shape: .planning/codebase/CONVENTIONS.md lines 91-111.
# Per CLAUDE.md: returns allowed on paid/processing/shipped — the "returned" state is in order_status Literal.
from dataclasses import dataclass
from typing import Literal


@dataclass
class OrderItem:
    product_id: str
    quantity: int
    unit_price: float


@dataclass
class Order:
    id: str
    user_id: str
    items: list[OrderItem]
    total_amount: float
    payment_method: Literal["credit_card", "paypal", "apple_pay"]
    payment_status: Literal["pending", "paid", "failed", "refunded"]
    order_status: Literal["placed", "paid", "processing", "shipped", "canceled", "returned"]
    created_at: str
    updated_at: str
