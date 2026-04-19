# app/lib/cart/cart_service.py
# Cart business logic: add, update, remove, get, total, clear.
# All mutations to cart state go through these functions.
# add_item and update_quantity are async to allow asyncio.Lock acquisition.
import asyncio

from app.lib.cart.models import Cart, CartItem
from app.lib.cart.store import carts_db
from app.lib.catalog.store import products_db

_cart_lock = asyncio.Lock()


def _cart_to_dict(cart: Cart) -> dict:
    """Serialize a Cart to a plain dict (without total).

    Args:
        cart: The Cart dataclass instance.

    Returns:
        Dict with user_id and items list.
    """
    return {
        "user_id": cart.user_id,
        "items": [
            {
                "product_id": i.product_id,
                "quantity": i.quantity,
                "unit_price": i.unit_price,
            }
            for i in cart.items
        ],
    }


async def add_item(user_id: str, product_id: str, quantity: int) -> dict:
    """Add a product to the user's cart, merging if already present.

    Checks that the product exists and has inventory before adding.
    Uses asyncio.Lock to prevent concurrent inventory race (D-09).

    Args:
        user_id: The authenticated user's ID.
        product_id: ID of the product to add.
        quantity: Number of units to add.

    Returns:
        Success dict with cart data, or failure dict with error code.
    """
    product = products_db.get(product_id)
    if not product:
        return {
            "success": False,
            "code": "PRODUCT_NOT_FOUND",
            "message": "Product not found",
            "retryable": False,
        }

    async with _cart_lock:
        if product.inventory == 0:
            return {
                "success": False,
                "code": "OUT_OF_STOCK",
                "message": "Product is out of stock",
                "retryable": False,
            }

        cart = carts_db.get(user_id)
        if cart is None:
            cart = Cart(user_id=user_id)
            carts_db[user_id] = cart

        # D-08: merge if same product already in cart
        existing = next((i for i in cart.items if i.product_id == product_id), None)
        if existing:
            existing.quantity += quantity
        else:
            cart.items.append(
                CartItem(
                    product_id=product_id,
                    quantity=quantity,
                    unit_price=product.unit_price,
                )
            )

    return {"success": True, "data": {"cart": _cart_to_dict(cart)}}


async def update_quantity(user_id: str, product_id: str, quantity: int) -> dict:
    """Update the quantity of an item already in the cart.

    If quantity <= 0, delegates to remove_item.

    Args:
        user_id: The authenticated user's ID.
        product_id: ID of the product whose quantity to update.
        quantity: New quantity; <= 0 triggers removal.

    Returns:
        Success dict with updated cart, or failure dict with error code.
    """
    cart = carts_db.get(user_id)
    if not cart:
        return {
            "success": False,
            "code": "CART_NOT_FOUND",
            "message": "Cart not found",
            "retryable": False,
        }

    item = next((i for i in cart.items if i.product_id == product_id), None)
    if not item:
        return {
            "success": False,
            "code": "ITEM_NOT_IN_CART",
            "message": "Item not in cart",
            "retryable": False,
        }

    if quantity <= 0:
        return remove_item(user_id, product_id)

    async with _cart_lock:
        item.quantity = quantity

    return {"success": True, "data": {"cart": _cart_to_dict(cart)}}


def remove_item(user_id: str, product_id: str) -> dict:
    """Remove an item from the user's cart entirely.

    Args:
        user_id: The authenticated user's ID.
        product_id: ID of the product to remove.

    Returns:
        Success dict with updated cart, or failure dict with error code.
    """
    cart = carts_db.get(user_id)
    if not cart:
        return {
            "success": False,
            "code": "CART_NOT_FOUND",
            "message": "Cart not found",
            "retryable": False,
        }

    original_len = len(cart.items)
    cart.items = [i for i in cart.items if i.product_id != product_id]
    if len(cart.items) == original_len:
        return {
            "success": False,
            "code": "ITEM_NOT_IN_CART",
            "message": "Item not in cart",
            "retryable": False,
        }

    return {"success": True, "data": {"cart": _cart_to_dict(cart)}}


def get_cart(user_id: str) -> dict:
    """Get the user's cart with computed total.

    Args:
        user_id: The authenticated user's ID.

    Returns:
        Success dict with cart data including computed total (D-09).
    """
    cart = carts_db.get(user_id)
    if cart is None:
        return {
            "success": True,
            "data": {"cart": {"user_id": user_id, "items": [], "total": 0.0}},
        }

    total = get_cart_total(user_id)["data"]["total"]
    return {
        "success": True,
        "data": {"cart": {**_cart_to_dict(cart), "total": total}},
    }


def get_cart_total(user_id: str) -> dict:
    """Compute the total price of all items in the user's cart.

    Computed on-the-fly as sum(item.quantity * item.unit_price) per D-09.

    Args:
        user_id: The authenticated user's ID.

    Returns:
        Success dict with total float.
    """
    cart = carts_db.get(user_id)
    if not cart:
        return {"success": True, "data": {"total": 0.0}}

    total = sum(i.quantity * i.unit_price for i in cart.items)
    return {"success": True, "data": {"total": total}}


def clear_cart(user_id: str) -> dict:
    """Remove all items from the user's cart. Idempotent.

    Args:
        user_id: The authenticated user's ID.

    Returns:
        Success dict with confirmation message.
    """
    if user_id in carts_db:
        del carts_db[user_id]
    return {"success": True, "data": {"message": "Cart cleared"}}
