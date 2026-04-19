# app/lib/agent/history.py
# Per-user conversation history store for the Claude agent.
# In-memory only — consistent with the project's in-memory-only design (D-08).
# History is keyed by user_id and lost on server restart (D-10).
# asyncio.Lock guards all reads and writes (T-04-01 mitigation).
import asyncio
from typing import Any

# Keyed by user_id. Value is a list of Anthropic message dicts.
# Message dict shape: {"role": "user"|"assistant", "content": str|list}
_history: dict[str, list[dict[str, Any]]] = {}
_history_lock = asyncio.Lock()


async def append_message(user_id: str, message: dict[str, Any]) -> None:
    """Append a message to the user's conversation history.

    Initializes the history list for a new user if it does not exist.
    Thread-safe: acquires _history_lock before any read or write.

    Args:
        user_id: The authenticated user's ID (from JWT session).
        message: Anthropic message dict with "role" and "content" keys.
    """
    async with _history_lock:
        if user_id not in _history:
            _history[user_id] = []
        _history[user_id].append(message)


async def get_messages(user_id: str) -> list[dict[str, Any]]:
    """Return a copy of the user's conversation history.

    Returns a shallow copy to prevent the caller from mutating the stored
    list outside the lock (T-04-01 mitigation).

    Args:
        user_id: The authenticated user's ID (from JWT session).

    Returns:
        List of Anthropic message dicts (may be empty). Callers receive
        a copy — mutations do not affect the stored history.
    """
    async with _history_lock:
        return list(_history.get(user_id, []))


async def clear_history(user_id: str) -> None:
    """Clear the conversation history for a user.

    Sets the history to an empty list rather than deleting the key,
    so subsequent appends work without re-initializing (D-10).

    Args:
        user_id: The authenticated user's ID (from JWT session).
    """
    async with _history_lock:
        _history[user_id] = []
