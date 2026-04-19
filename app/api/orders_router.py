# app/api/orders_router.py
# Orders router: list, detail, confirmation, cancel, return.
# All routes require authentication (get_current_user_web).
# Ownership check delegated to order_service — router raises 403 on UNAUTHORIZED.
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.lib.auth.dependencies import get_current_user_web
from app.lib.auth.models import User
from app.lib.mocks import payment_mock, warehouse_mock
from app.lib.orders import order_service

router = APIRouter(tags=["orders"])
templates = Jinja2Templates(directory="app/web/templates")

# Statuses where a refund should run on cancel
_REFUND_ON_CANCEL_STATUSES = ("paid", "captured")


def _status_badge(status: str) -> str:
    """Return Bootstrap badge classes for a given order status.

    Args:
        status: Order status string (placed, paid, processing, shipped, canceled, returned).

    Returns:
        Bootstrap badge CSS classes.
    """
    return {
        "placed": "bg-secondary",
        "paid": "bg-info text-dark",
        "processing": "bg-warning text-dark",
        "shipped": "bg-primary",
        "canceled": "bg-danger",
        "returned": "bg-secondary",
    }.get(status, "bg-secondary")


@router.get("/orders", response_class=HTMLResponse)
async def orders_list(
    request: Request,
    current_user: User = Depends(get_current_user_web),
):
    """Render the authenticated user's order list (ORD-01)."""
    result = order_service.list_orders(user_id=current_user.id)
    orders = result["data"]["orders"]
    # Attach badge class to each order for template use
    for o in orders:
        o["badge_class"] = _status_badge(o["order_status"])
    return templates.TemplateResponse(
        request=request,
        name="orders/list.html",
        context={"orders": orders, "current_user": current_user},
    )


@router.get("/orders/{order_id}/confirmation", response_class=HTMLResponse)
async def order_confirmation(
    request: Request,
    order_id: str,
    current_user: User = Depends(get_current_user_web),
):
    """Render order confirmation page after checkout (CHK-04, D-08)."""
    result = order_service.get_order(order_id=order_id, user_id=current_user.id)
    if not result["success"]:
        if result.get("code") == "UNAUTHORIZED":
            raise HTTPException(status_code=403, detail="Access denied")
        raise HTTPException(status_code=404, detail="Order not found")
    return templates.TemplateResponse(
        request=request,
        name="orders/confirmation.html",
        context={
            "order": result["data"]["order"],
            "badge_class": _status_badge(result["data"]["order"]["order_status"]),
            "current_user": current_user,
        },
    )


@router.get("/orders/{order_id}", response_class=HTMLResponse)
async def order_detail(
    request: Request,
    order_id: str,
    current_user: User = Depends(get_current_user_web),
):
    """Render order detail page with conditional cancel/return buttons (ORD-01, D-09)."""
    result = order_service.get_order(order_id=order_id, user_id=current_user.id)
    if not result["success"]:
        if result.get("code") == "UNAUTHORIZED":
            raise HTTPException(status_code=403, detail="Access denied")
        raise HTTPException(status_code=404, detail="Order not found")
    order = result["data"]["order"]
    return templates.TemplateResponse(
        request=request,
        name="orders/detail.html",
        context={
            "order": order,
            "badge_class": _status_badge(order["order_status"]),
            "can_cancel": order["order_status"] in ("placed", "paid"),
            "can_return": order["order_status"] in ("paid", "processing", "shipped"),
            "current_user": current_user,
        },
    )


@router.post("/orders/{order_id}/cancel")
async def cancel_order(
    request: Request,
    order_id: str,
    current_user: User = Depends(get_current_user_web),
):
    """Cancel an order (ORD-02): order_service.cancel_order -> warehouse mock -> optional refund.

    Reads order BEFORE canceling to determine payment_method and payment_status for refund.
    Mock failures surface as warning flash messages, not hard errors.
    """
    # Read order first to capture payment info before state changes
    pre_result = order_service.get_order(order_id=order_id, user_id=current_user.id)
    if not pre_result["success"]:
        if pre_result.get("code") == "UNAUTHORIZED":
            raise HTTPException(status_code=403, detail="Access denied")
        raise HTTPException(status_code=404, detail="Order not found")
    pre_order = pre_result["data"]["order"]

    # Cancel via service layer (ownership + eligibility check)
    cancel_result = order_service.cancel_order(order_id=order_id, user_id=current_user.id)
    if not cancel_result["success"]:
        if cancel_result.get("code") == "UNAUTHORIZED":
            raise HTTPException(status_code=403, detail="Access denied")
        request.session["flash"] = {"category": "danger", "message": cancel_result["message"]}
        return RedirectResponse(url=f"/orders/{order_id}", status_code=303)

    # Warehouse cancel mock (always run on successful cancel)
    wh_result = warehouse_mock.cancel_order(order_id=order_id)
    if not wh_result["success"]:
        request.session["flash"] = {
            "category": "warning",
            "message": f"Order canceled, but warehouse notification failed: {wh_result['message']}",
        }
        return RedirectResponse(url=f"/orders/{order_id}", status_code=303)

    # Payment refund mock (only if payment was captured)
    if pre_order.get("payment_status") in _REFUND_ON_CANCEL_STATUSES:
        refund_result = payment_mock.refund(
            order_id=order_id,
            payment_method=pre_order["payment_method"],
            amount=pre_order["total_amount"],
        )
        if not refund_result["success"]:
            request.session["flash"] = {
                "category": "warning",
                "message": f"Order canceled, but refund failed: {refund_result['message']}",
            }
            return RedirectResponse(url=f"/orders/{order_id}", status_code=303)

    request.session["flash"] = {"category": "success", "message": "Order canceled."}
    return RedirectResponse(url=f"/orders/{order_id}", status_code=303)


@router.post("/orders/{order_id}/return")
async def return_order(
    request: Request,
    order_id: str,
    current_user: User = Depends(get_current_user_web),
):
    """Request a return for an order (ORD-03).

    Delegates to order_service.request_return() which enforces ownership + eligibility.
    """
    result = order_service.request_return(order_id=order_id, user_id=current_user.id)
    if not result["success"]:
        if result.get("code") == "UNAUTHORIZED":
            raise HTTPException(status_code=403, detail="Access denied")
        request.session["flash"] = {"category": "danger", "message": result["message"]}
    else:
        request.session["flash"] = {"category": "success", "message": "Return request submitted."}
    return RedirectResponse(url=f"/orders/{order_id}", status_code=303)
