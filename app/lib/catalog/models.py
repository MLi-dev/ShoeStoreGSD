# app/lib/catalog/models.py
# Catalog domain models: Variant and Product.
# Source of shape: .planning/codebase/CONVENTIONS.md lines 60-77.
# CAT-04: Product.variants supports size/color variants.
from dataclasses import dataclass, field


@dataclass
class Variant:
    size: str | None = None
    color: str | None = None


@dataclass
class Product:
    id: str
    name: str
    description: str
    unit_price: float
    inventory: int
    category: str
    image_url: str | None = None
    variants: list[Variant] = field(default_factory=list)
