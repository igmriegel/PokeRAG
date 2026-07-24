"""
Structured Logging Configuration using Structlog.

Provides setup_logging() configuring structlog for JSON output at the level
from Settings.LOG_LEVEL, so all services emit machine-parseable logs for
observability (REQ-015).
"""

import logging
import sys
from typing import Any

import structlog

from pokemon_tcg_rag.config.settings import get_settings
from pokemon_tcg_rag.monitoring.tracing import current_trace_context


def _inject_trace_context(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    context = current_trace_context()
    if context.trace_id:
        event_dict.setdefault("trace_id", context.trace_id)
    if context.span_id:
        event_dict.setdefault("span_id", context.span_id)
    return event_dict


def setup_logging() -> None:
    """Initialize structured JSON logging for production observability.

    Reads LOG_LEVEL from Settings and configures structlog with a processor
    chain that emits ISO-timestamped JSON lines to stdout.
    """
    settings = get_settings()
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Configure standard library logging as the backend
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            _inject_trace_context,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> Any:
    """Return a structlog bound logger for the given module name.

    Usage::

        logger = get_logger(__name__)
        logger.info("event", key="value")

    Args:
        name: Typically ``__name__`` of the calling module.

    Returns:
        A structlog BoundLogger that emits JSON-structured log events.
    """
    return structlog.get_logger(name)
