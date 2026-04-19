# app/lib/cart/models.py
# Cart domain models: Cart and CartItem.
# Source of shape: .planning/codebase/CONVENTIONS.md lines 79-89.
# CartItem.unit_price captures price at add-to-cart time (avoids price drift).
from dataclasses import dataclass, field


@dataclass
class CartItem:
    product_id: str
    quantity: int
    unit_price: float


@dataclass
class Cart:
    user_id: str
    items: list[CartItem] = field(default_factory=list)
