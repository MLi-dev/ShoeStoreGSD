# app/api/auth_router.py
# Auth router: login, register, logout, password reset (request + confirm).
# All protected routes use get_current_user_web / get_current_user_api (D-01).
# PRG pattern (303 redirect) on every successful POST (T-03-06).
# httpOnly SameSite=Lax cookie (T-03-04).
# Open redirect guard on ?next= (T-03-01).
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.lib.auth.auth_service import login, register, reset_confirm, reset_request

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="app/web/templates")


def _safe_next(next_url: str | None) -> str:
    """Validate and return a safe relative redirect URL.

    Rejects absolute URLs and protocol-relative URLs to prevent open redirect (T-03-01).

    Args:
        next_url: URL from ?next= query param, or None.

    Returns:
        Validated relative URL starting with /, or /products as fallback.
    """
    if not next_url:
        return "/products"
    if not next_url.startswith("/") or next_url.startswith("//"):
        return "/products"
    return next_url


# ── GET endpoints (render forms) ──────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def index():
    """Redirect root to product list."""
    return RedirectResponse(url="/products", status_code=303)


@router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request, next: str | None = None):
    return templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context={"next": next},
    )


@router.get("/register", response_class=HTMLResponse)
async def register_get(request: Request):
    return templates.TemplateResponse(request=request, name="auth/register.html", context={})


@router.get("/auth/reset-request", response_class=HTMLResponse)
async def reset_request_get(request: Request):
    return templates.TemplateResponse(request=request, name="auth/reset_request.html", context={})


@router.get("/auth/reset-confirm", response_class=HTMLResponse)
async def reset_confirm_get(request: Request, token: str | None = None):
    return templates.TemplateResponse(
        request=request,
        name="auth/reset_confirm.html",
        context={"prefill_token": token},
    )


# ── POST endpoints (process forms) ────────────────────────────────────────────

@router.post("/auth/login")
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: str | None = None,
):
    """Process login form. Sets httpOnly JWT cookie on success (D-01, T-03-04)."""
    result = login(email=email, password=password)
    if not result["success"]:
        return templates.TemplateResponse(
            request=request,
            name="auth/login.html",
            context={"error": "Invalid email or password. Please try again.", "next": next},
            status_code=200,
        )
    redirect_to = _safe_next(next)
    response = RedirectResponse(url=redirect_to, status_code=303)
    response.set_cookie(
        key="access_token",
        value=result["data"]["token"],
        httponly=True,
        samesite="lax",
        max_age=30 * 60,
    )
    return response


@router.post("/auth/register")
async def register_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    """Process registration form. Redirects to /login on success."""
    result = register(email=email, password=password)
    if not result["success"]:
        error_msg = (
            "An account with this email already exists. Sign in instead?"
            if result.get("code") == "EMAIL_ALREADY_EXISTS"
            else result.get("message", "Registration failed.")
        )
        return templates.TemplateResponse(
            request=request,
            name="auth/register.html",
            context={"error": error_msg},
            status_code=200,
        )
    request.session["flash"] = {"category": "success", "message": "Account created. Please sign in."}
    return RedirectResponse(url="/login", status_code=303)


@router.post("/auth/logout")
async def logout_post():
    """Clear the access_token cookie and redirect to /login."""
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response


@router.post("/auth/reset-request")
async def reset_request_post(
    request: Request,
    email: str = Form(...),
):
    """Process password reset request. Returns token in page for demo (D-04)."""
    result = reset_request(email=email)
    # Always shows success response (prevents user enumeration).
    token = result["data"].get("token")  # None when email not found
    return templates.TemplateResponse(
        request=request,
        name="auth/reset_request.html",
        context={
            "reset_token": token,
            "message": "Check the API response for your reset token. Use it to set a new password.",
        },
        status_code=200,
    )


@router.post("/auth/reset-confirm")
async def reset_confirm_post(
    request: Request,
    token: str = Form(...),
    new_password: str = Form(...),
):
    """Process password reset confirmation. Redirects to /login on success."""
    result = reset_confirm(token=token, new_password=new_password)
    if not result["success"]:
        return templates.TemplateResponse(
            request=request,
            name="auth/reset_confirm.html",
            context={"error": "This reset link is invalid or has expired. Request a new one."},
            status_code=200,
        )
    request.session["flash"] = {"category": "success", "message": "Password updated. Please sign in."}
    return RedirectResponse(url="/login", status_code=303)
