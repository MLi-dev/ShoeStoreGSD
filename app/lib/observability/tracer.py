# app/lib/observability/tracer.py
# Langfuse 4.x client lifecycle for the ShoeStore agent.
#
# Langfuse 4.x is OpenTelemetry-native: spans created via @observe and
# start_as_current_span are exported through the OTel pipeline. When
# LANGFUSE_PUBLIC_KEY is unset the SDK logs a warning and turns into a no-op,
# so this module is safe to import in tests and local dev without credentials.
#
# Why a singleton: Langfuse() reads env vars on construction and registers an OTel
# tracer provider — calling it more than once produces duplicate exporters.
import logging

import config

logger = logging.getLogger(__name__)

_initialized: bool = False


def init_tracer() -> None:
    """Initialize the Langfuse client once per process.

    Idempotent: subsequent calls are no-ops. Reads credentials from `config` (which
    pulls them from the environment). When credentials are missing this still calls
    Langfuse() — the SDK degrades to a tracing no-op and emits a single warning.
    """
    global _initialized
    if _initialized:
        return

    from langfuse import Langfuse

    Langfuse(
        public_key=config.LANGFUSE_PUBLIC_KEY,
        secret_key=config.LANGFUSE_SECRET_KEY,
        host=config.LANGFUSE_HOST,
    )
    _initialized = True

    if config.LANGFUSE_PUBLIC_KEY:
        logger.info("Langfuse tracer initialized (host=%s)", config.LANGFUSE_HOST)
    else:
        logger.info("Langfuse credentials absent — tracer running in no-op mode")


def flush_tracer() -> None:
    """Flush any buffered spans. Call from the FastAPI shutdown path."""
    if not _initialized:
        return
    from langfuse import get_client

    try:
        get_client().flush()
    except Exception:
        logger.exception("Langfuse flush failed")
