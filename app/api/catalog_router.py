# app/api/catalog_router.py
# Catalog router: product list (search + filter) and product detail.
# Also handles POST /cart/add (Add to Cart form on product detail page).
# Routes: GET /products, GET /products/{product_id}, POST /cart/add
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.lib.auth.dependencies import get_current_user_web
from app.lib.auth.models import User
from app.lib.cart import cart_service
from app.lib.catalog import catalog_service

router = APIRouter(tags=["catalog"])
templates = Jinja2Templates(directory="app/web/templates")

CATEGORIES = ["running", "hiking", "slides", "sandals", "socks"]


@router.get("/products", response_class=HTMLResponse)
async def product_list(request: Request, q: str = "", category: str = ""):
    """Product list page with keyword search and category filter tabs (CAT-02, D-10, D-11).

    Does not require authentication — browsing is public.
    """
    products = catalog_service.search_products(q=q, category=category)
    return templates.TemplateResponse(
        request=request,
        name="products/list.html",
        context={
            "products": products,
            "q": q,
            "active_category": category,
            "categories": CATEGORIES,
        },
    )


@router.get("/products/{product_id}", response_class=HTMLResponse)
async def product_detail(request: Request, product_id: str):
    """Product detail page with variant selector and Add to Cart form (CAT-03, D-12).

    Does not require authentication — viewing product details is public.
    """
    product = catalog_service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return templates.TemplateResponse(
        request=request,
        name="products/detail.html",
        context={"product": product},
    )


@router.post("/cart/add")
async def add_to_cart(
    request: Request,
    product_id: str = Form(...),
    size: str = Form(...),
    color: str = Form(...),
    quantity: int = Form(1),
    current_user: User = Depends(get_current_user_web),
):
    """Add a product variant to the authenticated user's cart (D-12, PRG pattern).

    On success: redirect to /cart (303).
    On failure (out of stock, product not found): flash error + redirect to product page.
    """
    result = await cart_service.add_item(
        user_id=current_user.id,
        product_id=product_id,
        quantity=quantity,
    )
    if not result["success"]:
        request.session["flash"] = {"category": "danger", "message": result["message"]}
        return RedirectResponse(url=f"/products/{product_id}", status_code=303)
    return RedirectResponse(url="/cart", status_code=303)
