# app/api/cart_router.py
# Cart router: view cart, update/remove items, checkout with mock adapters.
# CRITICAL: Checkout sequence is reserve_inventory → charge → place_order.
# Never call place_order before both mocks succeed (RESEARCH.md Pitfall 1).
from uuid import uuid4

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.lib.auth.dependencies import get_current_user_web
from app.lib.auth.models import User
from app.lib.cart import cart_service
from app.lib.catalog.store import products_db
from app.lib.mocks import payment_mock, warehouse_mock
from app.lib.orders import order_service

router = APIRouter(tags=["cart"])
templates = Jinja2Templates(directory="app/web/templates")


def _enrich_cart_items(cart_data: dict) -> list[dict]:
    """Enrich cart items with product name for template display.

    cart_service stores only product_id, quantity, unit_price.
    Template needs name for the Product column.

    Args:
        cart_data: The cart dict from cart_service.get_cart()["data"]["cart"].

    Returns:
        List of enriched item dicts with added 'name' key.
    """
    enriched = []
    for item in cart_data.get("items", []):
        product = products_db.get(item["product_id"])
        enriched.append({
            **item,
            "name": product.name if product else item["product_id"],
        })
    return enriched


@router.get("/cart", response_class=HTMLResponse)
async def cart_page(
    request: Request,
    current_user: User = Depends(get_current_user_web),
):
    """Render cart page with items, totals, and checkout form (D-07)."""
    cart_result = cart_service.get_cart(user_id=current_user.id)
    cart_data = cart_result["data"]["cart"]
    enriched_items = _enrich_cart_items(cart_data)
    return templates.TemplateResponse(
        request=request,
        name="cart/cart.html",
        context={
            "items": enriched_items,
            "total": cart_data.get("total", 0.0),
            "current_user": current_user,
        },
    )


@router.post("/cart/update")
async def cart_update(
    request: Request,
    product_id: str = Form(...),
    quantity: int = Form(...),
    current_user: User = Depends(get_current_user_web),
):
    """Update quantity for a cart item. PRG: redirect to /cart on completion."""
    result = await cart_service.update_quantity(
        user_id=current_user.id,
        product_id=product_id,
        quantity=quantity,
    )
    if not result["success"]:
        request.session["flash"] = {"category": "danger", "message": result["message"]}
    return RedirectResponse(url="/cart", status_code=303)


@router.post("/cart/remove")
async def cart_remove(
    request: Request,
    product_id: str = Form(...),
    current_user: User = Depends(get_current_user_web),
):
    """Remove an item from the cart. PRG: redirect to /cart on completion."""
    result = cart_service.remove_item(user_id=current_user.id, product_id=product_id)
    if not result["success"]:
        request.session["flash"] = {"category": "danger", "message": result["message"]}
    return RedirectResponse(url="/cart", status_code=303)


@router.post("/checkout")
async def checkout_post(
    request: Request,
    payment_method: str = Form(...),
    current_user: User = Depends(get_current_user_web),
):
    """Process checkout: reserve → charge → place_order.

    CRITICAL SEQUENCE (RESEARCH.md Pitfall 1):
    1. Reserve inventory (warehouse mock)
    2. Charge payment (payment mock)
    3. Place order (order service) — only after both mocks succeed

    On any mock failure: re-render cart page with error. Do NOT create the order.
    On success: redirect to /orders/{id}/confirmation (PRG, 303).
    """
    # Get current cart state
    cart_result = cart_service.get_cart(user_id=current_user.id)
    cart_data = cart_result["data"]["cart"]
    enriched_items = _enrich_cart_items(cart_data)
    total = cart_data.get("total", 0.0)

    if not cart_data.get("items"):
        request.session["flash"] = {"category": "warning", "message": "Your cart is empty."}
        return RedirectResponse(url="/cart", status_code=303)

    # Use a temporary ID for mock calls (real order ID created by place_order)
    temp_id = str(uuid4())
    mock_items = [
        {"product_id": item["product_id"], "quantity": item["quantity"]}
        for item in cart_data["items"]
    ]

    # Step 1: Reserve inventory (warehouse mock)
    reserve_result = warehouse_mock.reserve_inventory(order_id=temp_id, items=mock_items)
    if not reserve_result["success"]:
        return templates.TemplateResponse(
            request=request,
            name="cart/cart.html",
            context={
                "items": enriched_items,
                "total": total,
                "current_user": current_user,
                "error": "One or more items in your cart are out of stock. Please update your cart and try again.",
            },
            status_code=200,
        )

    # Step 2: Charge payment (payment mock)
    charge_result = payment_mock.charge(
        order_id=temp_id,
        payment_method=payment_method,
        amount=total,
    )
    if not charge_result["success"]:
        return templates.TemplateResponse(
            request=request,
            name="cart/cart.html",
            context={
                "items": enriched_items,
                "total": total,
                "current_user": current_user,
                "error": "Payment failed. Please try a different payment method or contact support.",
            },
            status_code=200,
        )

    # Step 3: Place order (only after both mocks succeed)
    order_result = order_service.place_order(
        user_id=current_user.id,
        payment_method=payment_method,
    )
    if not order_result["success"]:
        request.session["flash"] = {"category": "danger", "message": order_result["message"]}
        return RedirectResponse(url="/cart", status_code=303)

    order_id = order_result["data"]["order_id"]
    return RedirectResponse(url=f"/orders/{order_id}/confirmation", status_code=303)
