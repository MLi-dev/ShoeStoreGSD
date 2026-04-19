# app/lib/agent/tools.py
# Agent tool functions — 10 async functions wrapping existing services.
# Each function accepts user_id as its first parameter (D-15 ownership enforcement).
# All functions return serializable dicts; no dataclass instances are returned.
# Ownership of orders is enforced by the service layer (T-04-02 mitigation).
from app.lib.auth.auth_service import reset_confirm, reset_request
from app.lib.auth.store import users_db
from app.lib.cart import cart_service
from app.lib.catalog import catalog_service
from app.lib.orders import order_service


async def search_products(user_id: str, q: str = "", category: str = "") -> dict:
    """Search the shoe catalog by keyword and/or category.

    Args:
        user_id: Authenticated user's ID (passed by agent dispatcher; not used
            for filtering — catalog is public — but required for consistency).
        q: Optional keyword for case-insensitive substring search.
        category: Optional category filter (e.g. "running", "hiking").

    Returns:
        Success dict:
            {"success": True, "data": {"products": [...], "count": int}}
        Always succeeds; empty results mean no match (count=0).
    """
    results = catalog_service.search_products(q=q, category=category)
    products = [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "unit_price": p.unit_price,
            "inventory": p.inventory,
            "category": p.category,
        }
        for p in results
    ]
    return {"success": True, "data": {"products": products, "count": len(products)}}


async def get_product_details(user_id: str, product_id: str) -> dict:
    """Retrieve full details for a single product, including size/color variants.

    Args:
        user_id: Authenticated user's ID (required for dispatcher consistency).
        product_id: UUID string of the product to retrieve.

    Returns:
        Success dict with full product data:
            {"success": True, "data": {"product": {..., "variants": [...]}}}
        Failure dict if product not found:
            {"success": False, "code": "PRODUCT_NOT_FOUND", ...}
    """
    product = catalog_service.get_product(product_id)
    if product is None:
        return {
            "success": False,
            "code": "PRODUCT_NOT_FOUND",
            "message": "Product not found",
            "retryable": False,
        }
    return {
        "success": True,
        "data": {
            "product": {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "unit_price": product.unit_price,
                "inventory": product.inventory,
                "category": product.category,
                "variants": [
                    {"size": v.size, "color": v.color}
                    for v in product.variants
                ],
            }
        },
    }


async def add_to_cart(user_id: str, product_id: str, quantity: int) -> dict:
    """Add a product to the authenticated user's cart.

    Delegates to cart_service.add_item which checks inventory and uses
    asyncio.Lock to prevent oversell races (D-09 pitfall).

    Args:
        user_id: Authenticated user's ID.
        product_id: UUID string of the product to add.
        quantity: Number of units to add (must be positive).

    Returns:
        Service result directly (success or failure dict from cart_service).
    """
    return await cart_service.add_item(
        user_id=user_id,
        product_id=product_id,
        quantity=quantity,
    )


async def view_cart(user_id: str) -> dict:
    """Retrieve the authenticated user's current cart contents and total.

    Args:
        user_id: Authenticated user's ID.

    Returns:
        Success dict with items list and computed total:
            {"success": True, "data": {"items": [...], "total": float}}
        Returns empty items and 0.0 total if cart is empty or does not exist.
    """
    cart_result = cart_service.get_cart(user_id)
    if not cart_result["success"]:
        return {"success": True, "data": {"items": [], "total": 0.0}}

    cart_data = cart_result["data"]["cart"]
    return {
        "success": True,
        "data": {
            "items": cart_data.get("items", []),
            "total": cart_data.get("total", 0.0),
        },
    }


async def checkout(user_id: str, payment_method: str) -> dict:
    """Place an order using the user's current cart and specified payment method.

    Validates payment_method before delegating to order_service.place_order.
    Accepted methods: credit_card, paypal, apple_pay.

    Args:
        user_id: Authenticated user's ID.
        payment_method: One of "credit_card", "paypal", "apple_pay".

    Returns:
        Service result directly on valid payment method.
        Failure dict with INVALID_PAYMENT_METHOD if method is not recognized.
    """
    valid_methods = {"credit_card", "paypal", "apple_pay"}
    if payment_method not in valid_methods:
        return {
            "success": False,
            "code": "INVALID_PAYMENT_METHOD",
            "message": "Payment method must be credit_card, paypal, or apple_pay",
            "retryable": False,
        }
    return order_service.place_order(
        user_id=user_id,
        payment_method=payment_method,  # type: ignore[arg-type]
    )


async def place_order(user_id: str, payment_method: str) -> dict:
    """Alias for checkout() — both tool names are valid in natural language.

    Args:
        user_id: Authenticated user's ID.
        payment_method: One of "credit_card", "paypal", "apple_pay".

    Returns:
        Same result as checkout().
    """
    return await checkout(user_id=user_id, payment_method=payment_method)


async def check_order_status(user_id: str, order_id: str) -> dict:
    """Retrieve the status and details of a single order.

    Ownership is enforced by order_service.get_order (T-04-02 mitigation).

    Args:
        user_id: Authenticated user's ID (from JWT session, never from message).
        order_id: UUID string of the order to retrieve.

    Returns:
        Service result directly (success with order data, or failure dict).
    """
    return order_service.get_order(order_id=order_id, user_id=user_id)


async def cancel_order(user_id: str, order_id: str) -> dict:
    """Cancel an order owned by the authenticated user.

    Security: user_id comes exclusively from the authenticated session (JWT),
    never from the user's message content (T-04-02, D-15). The service layer
    enforces ownership and returns UNAUTHORIZED if the order belongs to another
    user.

    Args:
        user_id: Authenticated user's ID (from JWT session, never from message).
        order_id: UUID string of the order to cancel.

    Returns:
        Service result directly (success or failure dict from order_service).
    """
    return order_service.cancel_order(order_id=order_id, user_id=user_id)


async def return_order(user_id: str, order_id: str) -> dict:
    """Request a return for an order owned by the authenticated user.

    Same ownership pattern as cancel_order (T-04-02, D-15). The service layer
    enforces ownership and eligibility (paid, processing, shipped statuses only).

    Args:
        user_id: Authenticated user's ID (from JWT session, never from message).
        order_id: UUID string of the order to return.

    Returns:
        Service result directly (success or failure dict from order_service).
    """
    return order_service.request_return(order_id=order_id, user_id=user_id)


async def reset_password(user_id: str, new_password: str) -> dict:
    """Reset the authenticated user's password.

    Resolves the user's email from users_db using user_id (from JWT session),
    then calls reset_request() to obtain a token and reset_confirm() to apply
    the new password. The user never needs to provide their email (T-04-05).

    Args:
        user_id: Authenticated user's ID (from JWT session).
        new_password: The new plain-text password to set.

    Returns:
        Success dict on password update:
            {"success": True, "data": {"message": "Password reset successfully"}}
        Failure dict with INVALID_PASSWORD if new_password is blank.
        Failure dict with USER_NOT_FOUND if user_id is not in users_db.
    """
    if not new_password or not new_password.strip():
        return {
            "success": False,
            "code": "INVALID_PASSWORD",
            "message": "Password cannot be empty",
            "retryable": False,
        }

    # Resolve user from JWT session — email is never taken from message content.
    user = users_db.get(user_id)
    if user is None:
        return {
            "success": False,
            "code": "USER_NOT_FOUND",
            "message": "User not found",
            "retryable": False,
        }

    # Issue a reset token using the user's email, then immediately confirm it.
    request_result = reset_request(user.email)
    token = request_result["data"].get("token")
    if token is None:
        # Should not happen since we verified the user exists, but guard anyway.
        return {
            "success": False,
            "code": "RESET_FAILED",
            "message": "Failed to initiate password reset",
            "retryable": True,
        }

    confirm_result = reset_confirm(token=token, new_password=new_password)
    if not confirm_result["success"]:
        return confirm_result

    return {"success": True, "data": {"message": "Password reset successfully"}}
