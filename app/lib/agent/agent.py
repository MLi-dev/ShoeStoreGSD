# app/lib/agent/agent.py
# AsyncAnthropic tool-use agent loop.
# Orchestrates conversation history + tool dispatch in a single async function.
# The route handler calls run() once per user turn.
#
# Key invariants (from CLAUDE.md Critical Pitfalls):
#   - MAX_TURNS = 10 hard cap — loop never runs forever (D-12)
#   - tool_result always appended even on exception — prevents API crash (D-13)
#   - user_id comes from JWT session parameter, never parsed from message text (D-15)
#   - Intermediate tool-use turns are NOT stored in history — only user message
#     and final assistant reply are persisted (history.get_messages returns a copy)
import logging
import os
from typing import Any

from anthropic import AsyncAnthropic
from anthropic.types import Message

from app.lib.agent import history, tools
from app.lib.auth.models import User

logger = logging.getLogger(__name__)

MAX_TURNS: int = 10
_client: AsyncAnthropic | None = None


def _get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client

# ---------------------------------------------------------------------------
# Tool schemas (Anthropic tool definitions — passed as tools= parameter)
# ---------------------------------------------------------------------------

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "search_products",
        "description": "Search the ShoeStore catalog for shoes by keyword and/or category.",
        "input_schema": {
            "type": "object",
            "properties": {
                "q": {"type": "string", "description": "Search keyword (optional)"},
                "category": {
                    "type": "string",
                    "description": "Category filter: running, hiking, slides, sandals, socks (optional)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_product_details",
        "description": "Get full details for a specific product including variants.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Product UUID"},
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "add_to_cart",
        "description": "Add a product to the user's shopping cart.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Product UUID"},
                "quantity": {
                    "type": "integer",
                    "description": "Number of units to add",
                    "minimum": 1,
                },
            },
            "required": ["product_id", "quantity"],
        },
    },
    {
        "name": "view_cart",
        "description": "View the current contents and total of the user's cart.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "checkout",
        "description": "Check out the cart and place an order with the specified payment method.",
        "input_schema": {
            "type": "object",
            "properties": {
                "payment_method": {
                    "type": "string",
                    "description": "Payment method: credit_card, paypal, or apple_pay",
                    "enum": ["credit_card", "paypal", "apple_pay"],
                },
            },
            "required": ["payment_method"],
        },
    },
    {
        "name": "place_order",
        "description": "Alias for checkout — place an order with the specified payment method.",
        "input_schema": {
            "type": "object",
            "properties": {
                "payment_method": {
                    "type": "string",
                    "description": "Payment method: credit_card, paypal, or apple_pay",
                    "enum": ["credit_card", "paypal", "apple_pay"],
                },
            },
            "required": ["payment_method"],
        },
    },
    {
        "name": "check_order_status",
        "description": "Get the current status and details of a specific order.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order UUID"},
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "cancel_order",
        "description": "Cancel an order. Only placed or paid orders can be canceled.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order UUID to cancel"},
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "return_order",
        "description": "Request a return on a paid, processing, or shipped order.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order UUID to return"},
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "reset_password",
        "description": "Reset the authenticated user's password.",
        "input_schema": {
            "type": "object",
            "properties": {
                "new_password": {"type": "string", "description": "The new password to set"},
            },
            "required": ["new_password"],
        },
    },
]

# ---------------------------------------------------------------------------
# Tool registry — maps tool name to async tool function
# ---------------------------------------------------------------------------

_TOOL_REGISTRY: dict[str, Any] = {
    "search_products": tools.search_products,
    "get_product_details": tools.get_product_details,
    "add_to_cart": tools.add_to_cart,
    "view_cart": tools.view_cart,
    "checkout": tools.checkout,
    "place_order": tools.place_order,
    "check_order_status": tools.check_order_status,
    "cancel_order": tools.cancel_order,
    "return_order": tools.return_order,
    "reset_password": tools.reset_password,
}

# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _build_system_prompt(user: User) -> str:
    """Build the system prompt for the agent, injecting the authenticated user's identity.

    Injects user.email to bind the assistant to a specific user session (D-04, D-05).
    Includes an explicit scope declaration to prevent out-of-scope requests (D-05).
    """
    return (
        f"You are a helpful ShoeStore shopping assistant. "
        f"You help users search for shoes, manage their cart, check out, and manage their orders. "
        f"Politely decline anything outside this scope.\n\n"
        f"The authenticated user is {user.email}. "
        f"Always act on behalf of this user only."
    )


def _extract_text(response: Message) -> str:
    """Extract the first text block from an Anthropic response.

    Args:
        response: Anthropic Message object.

    Returns:
        Text of the first TextBlock found, or empty string if none present.
    """
    for block in response.content:
        if block.type == "text":
            return block.text
    return ""


async def _dispatch_tool(user_id: str, tool_use: Any) -> dict:
    """Dispatch a tool call from the LLM to the appropriate async tool function.

    Looks up the tool name in _TOOL_REGISTRY. Returns a failure dict for unknown
    tool names without executing anything (T-04-07 mitigation). Never raises —
    exceptions are caught and returned as failure dicts so the caller can always
    append a tool_result block (D-13).

    Args:
        user_id: Authenticated user's ID (from JWT session, never from message).
        tool_use: Anthropic ToolUseBlock with .name, .id, and .input attributes.

    Returns:
        Tool function result dict on success.
        Failure dict with UNKNOWN_TOOL code if name not in registry.
        Failure dict with error details on unexpected exception.
    """
    logger.debug("Dispatching tool %r for user_id=%r", tool_use.name, user_id)

    tool_fn = _TOOL_REGISTRY.get(tool_use.name)
    if tool_fn is None:
        return {
            "success": False,
            "code": "UNKNOWN_TOOL",
            "message": f"Unknown tool: {tool_use.name}",
            "retryable": False,
        }

    try:
        return await tool_fn(user_id=user_id, **tool_use.input)
    except Exception as exc:
        logger.exception("Tool %r raised an unexpected exception", tool_use.name)
        return {
            "success": False,
            "code": "TOOL_ERROR",
            "message": str(exc),
            "retryable": True,
        }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def run(user_id: str, user: User, message: str) -> dict:
    """Run one user turn of the agent loop.

    Appends the user message to history, then iterates up to MAX_TURNS calling
    the Anthropic API. On end_turn: extracts reply text, appends to history,
    returns success dict. On tool_use: dispatches tool, always appends tool_result
    even on exception (D-13). Caps at MAX_TURNS=10 (D-12).

    IMPORTANT: The `messages` list is a copy from history.get_messages(). Mutations
    during the tool-use loop (intermediate assistant + tool_result turns) are NOT
    persisted to history. Only the initial user message and the final assistant reply
    are stored via append_message.

    Args:
        user_id: Authenticated user ID from JWT session (never from message content, D-15).
        user: Full User dataclass for system prompt injection (D-04).
        message: Sanitized user message ([root]: already stripped by router, D-14).

    Returns:
        {"success": True, "data": {"reply": str}} on success.
        {"success": False, "code": str, "message": str, "retryable": bool} on error.
    """
    await history.append_message(user_id, {"role": "user", "content": message})
    messages = await history.get_messages(user_id)

    response: Message | None = None
    for _ in range(MAX_TURNS):
        try:
            response = await _get_client().messages.create(
                model="claude-opus-4-5",
                max_tokens=1024,
                system=_build_system_prompt(user),
                messages=messages,
                tools=TOOL_SCHEMAS,
            )
        except Exception:
            logger.exception("Anthropic API error in agent loop")
            return {
                "success": False,
                "code": "AGENT_ERROR",
                "message": "The assistant encountered an error. Please try again.",
                "retryable": True,
            }

        if response.stop_reason == "end_turn":
            reply = _extract_text(response)
            await history.append_message(user_id, {"role": "assistant", "content": reply})
            return {"success": True, "data": {"reply": reply}}

        # stop_reason == "tool_use" — dispatch all tool calls in this response
        tool_uses = [b for b in response.content if b.type == "tool_use"]
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for tool_use in tool_uses:
            try:
                result = await _dispatch_tool(user_id=user_id, tool_use=tool_use)
            except Exception as exc:
                # _dispatch_tool should never raise, but guard here too (D-13)
                logger.exception("Tool dispatch error for %s", tool_use.name)
                result = {"error": str(exc)}
            # D-13: ALWAYS append tool_result even on exception
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": str(result),
            })
        messages.append({"role": "user", "content": tool_results})

    # MAX_TURNS hard cap reached — return last partial text response
    last_reply = (
        _extract_text(response)
        if response
        else "I reached the limit of my reasoning steps. Please try rephrasing."
    )
    return {"success": True, "data": {"reply": last_reply}}
