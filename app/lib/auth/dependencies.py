# app/lib/auth/dependencies.py
# FastAPI dependency functions for authenticated routes.
# Two variants:
#   get_current_user_web  — for web page routes: 307 redirect to /login on failure
#   get_current_user_api  — for REST API routes: HTTP 401 on failure
# Source: .planning/phases/03-web-ui-rest-api/03-RESEARCH.md Pattern 1
from typing import Annotated

from fastapi import Cookie, HTTPException, Request

from app.lib.auth.auth_service import verify_token
from app.lib.auth.models import User
from app.lib.auth.store import users_db


def _resolve_user(token: str | None) -> User | None:
    """Decode JWT and return the corresponding User, or None on any failure.

    Args:
        token: JWT string from the httpOnly cookie, or None if cookie absent.

    Returns:
        User dataclass if token is valid and user exists; None otherwise.
    """
    if not token:
        return None
    result = verify_token(token)
    if not result["success"]:
        return None
    user_id = result["data"]["user_id"]
    return users_db.get(user_id)


async def get_current_user_web(
    request: Request,
    access_token: Annotated[str | None, Cookie()] = None,
) -> User:
    """FastAPI dependency for web page routes.

    On failure (missing/invalid cookie): raise HTTPException(307) redirecting
    to /login?next=<current_path>. The `next` URL is the path only (no host),
    validated to be a relative path (no open redirect — T-03-01).

    Args:
        request: Current Starlette Request (provides URL for `next` param).
        access_token: JWT from httpOnly cookie, injected by FastAPI Cookie().

    Returns:
        Authenticated User dataclass.

    Raises:
        HTTPException(307): When no valid auth cookie is present.
    """
    user = _resolve_user(access_token)
    if not user:
        # Build the next URL from the request path only (path + query, no host)
        # to prevent open redirect (T-03-01).
        next_url = request.url.path
        if request.url.query:
            next_url = f"{next_url}?{request.url.query}"
        raise HTTPException(
            status_code=307,
            headers={"Location": f"/login?next={next_url}"},
        )
    return user


async def get_current_user_api(
    access_token: Annotated[str | None, Cookie()] = None,
) -> User:
    """FastAPI dependency for REST API routes.

    On failure (missing/invalid cookie): raise HTTP 401.

    Args:
        access_token: JWT from httpOnly cookie, injected by FastAPI Cookie().

    Returns:
        Authenticated User dataclass.

    Raises:
        HTTPException(401): When no valid auth cookie is present.
    """
    user = _resolve_user(access_token)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
