"""
OpenTelemetry helpers for correlated tracing.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import IO, Any, cast

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Status, StatusCode

_TRACER_PROVIDER_INITIALIZED = False
_TRACER_NAME = "pokemon_tcg_rag"
_SAFE_ATTRIBUTE_PREFIXES = (
    "query.",
    "retrieval.",
    "llm.",
    "feedback.",
    "api.",
    "db.",
)


@dataclass(frozen=True, slots=True)
class TraceContext:
    """Lightweight trace identifiers used for log correlation."""

    trace_id: str | None
    span_id: str | None


def initialize_tracing(service_name: str = "pokemon-tcg-rag") -> None:
    """Install a safe tracer provider once per process.

    The default exporter is the console exporter so local development and tests do not
    require an external collector. If an OTLP exporter is available and configured by
    environment, it can be added without making startup brittle.
    """
    global _TRACER_PROVIDER_INITIALIZED
    if _TRACER_PROVIDER_INITIALIZED:
        return

    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    stdout = cast(IO[Any], sys.__stdout__ or sys.stdout)
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter(out=stdout)))
    trace.set_tracer_provider(provider)
    _TRACER_PROVIDER_INITIALIZED = True


def get_tracer() -> trace.Tracer:
    """Return the shared application tracer."""
    initialize_tracing()
    return trace.get_tracer(_TRACER_NAME)


@contextmanager
def traced_span(name: str, *, attributes: dict[str, object] | None = None) -> Iterator[None]:
    """Create a child span with sanitized, low-cardinality attributes."""
    tracer = get_tracer()
    with tracer.start_as_current_span(name) as span:
        safe_attributes = sanitize_attributes(attributes)
        if safe_attributes:
            for key, value in safe_attributes.items():
                if key and value is not None:
                    span.set_attribute(
                        str(key),
                        cast(
                            str
                            | bool
                            | int
                            | float
                            | list[str]
                            | list[bool]
                            | list[int]
                            | list[float],
                            value,
                        ),
                    )
        try:
            yield
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            raise


def current_trace_context() -> TraceContext:
    """Expose the active trace/span identifiers for structured log correlation."""
    span = trace.get_current_span()
    context = span.get_span_context()
    if context is None or not context.is_valid:
        return TraceContext(trace_id=None, span_id=None)
    return TraceContext(trace_id=f"{context.trace_id:032x}", span_id=f"{context.span_id:016x}")


def sanitize_attributes(attributes: dict[str, object] | None) -> dict[str, object]:
    """Drop any attribute that may carry sensitive or high-cardinality data."""
    if not attributes:
        return {}
    sanitized: dict[str, object] = {}
    for key, value in attributes.items():
        if any(str(key).startswith(prefix) for prefix in _SAFE_ATTRIBUTE_PREFIXES):
            sanitized[str(key)] = value
    return sanitized
