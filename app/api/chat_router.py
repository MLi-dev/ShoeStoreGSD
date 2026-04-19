# app/api/chat_router.py
# Chat router: GET /chat page and POST /chat/message AJAX endpoint.
# All routes require authentication (get_current_user_web redirects to /login).
# Message flow: strip [root]: prefix → guardrails check → agent.run() → JSON reply.
import logging

import config
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.lib.agent import agent
from app.lib.auth.dependencies import get_current_user_web
from app.lib.auth.models import User
from app.lib.guardrails.guardrails import check_message
from app.lib.guardrails.root_instruction import parse_root_instruction
from config import DEMO_MODE

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])
templates = Jinja2Templates(directory="app/web/templates")


@router.get("/chat", response_class=HTMLResponse)
async def chat_page(
    request: Request,
    current_user: User = Depends(get_current_user_web),
) -> HTMLResponse:
    """Render the chat UI page.

    Requires authentication (get_current_user_web redirects to /login on failure).
    Passes current_user for navbar rendering only; transcript starts empty (D-10).

    Args:
        request: Current Starlette Request.
        current_user: Authenticated User from JWT cookie.

    Returns:
        HTMLResponse rendering chat/chat.html.
    """
    return templates.TemplateResponse(
        request=request,
        name="chat/chat.html",
        context={"current_user": current_user},
    )


@router.post("/chat/message")
async def chat_message(
    request: Request,
    current_user: User = Depends(get_current_user_web),
) -> JSONResponse:
    """Handle a single chat turn — run guardrails then agent loop.

    Parses JSON body {message: str}. Strips [root]: prefix when DEMO_MODE is
    True (D-14) before any further processing. Runs injection guardrail check
    (D-06). Calls agent.run() with authenticated user_id from JWT — never from
    message content (D-15). Returns JSON {reply: str}.

    Args:
        request: Current Starlette Request (JSON body).
        current_user: Authenticated User from JWT cookie.

    Returns:
        JSONResponse with {reply: str} on success.

    Raises:
        HTTPException(400): If message body is missing or empty.
        HTTPException(500): If agent loop returns a non-retryable error.
    """
    body = await request.json()
    user_message: str = body.get("message", "").strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Message required")

    # D-14: parse [root]: instructions in route handler before messages array is built.
    # Gated on DEMO_MODE so production behavior is unchanged.
    if DEMO_MODE and user_message.startswith("[root]:"):
        raw_instruction = user_message[len("[root]:"):].strip()
        logger.warning(
            "Root instruction received from user_id=%s: %r",
            current_user.id,
            raw_instruction,
        )
        if not raw_instruction:
            return JSONResponse({"reply": "Root instruction received but was empty."})

        result = parse_root_instruction(raw_instruction)
        if result["success"]:
            for section, keys in result["mutations"].items():
                for key, value in keys.items():
                    config.FAILURE_CONFIG[section][key] = value
            logger.warning(
                "FAILURE_CONFIG mutated by user_id=%s: %r",
                current_user.id,
                result["mutations"],
            )
        else:
            logger.warning(
                "Unrecognized root instruction from user_id=%s: %r",
                current_user.id,
                raw_instruction,
            )
        return JSONResponse({"reply": result["message"]})

    # D-06: Layer 1 guardrail — injection pattern check before agent sees the message.
    guard = check_message(user_message)
    if not guard["success"]:
        logger.info(
            "Injection pattern detected for user_id=%s, code=%s",
            current_user.id,
            guard.get("code"),
        )
        return JSONResponse({"reply": guard["message"]})

    # D-15: user_id comes exclusively from JWT session, never from message content.
    result = await agent.run(
        user_id=current_user.id,
        user=current_user,
        message=user_message,
    )

    if not result["success"]:
        logger.error(
            "Agent error for user_id=%s: %s",
            current_user.id,
            result.get("code"),
        )
        raise HTTPException(status_code=500, detail=result.get("message", "Agent error"))

    return JSONResponse({"reply": result["data"]["reply"]})
