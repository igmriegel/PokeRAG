"""
Unit tests for tracing helpers.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from opentelemetry import trace

from pokemon_tcg_rag.monitoring.tracing import (
    current_trace_context,
    sanitize_attributes,
    traced_span,
)


def test_sanitize_attributes_drops_sensitive_keys() -> None:
    attributes = {
        "query.length": 42,
        "llm.model_name": "gpt-4o-mini",
        "prompt": "secret prompt",
        "answer": "secret answer",
        "feedback.rating": 1,
    }

    sanitized = sanitize_attributes(attributes)

    assert "query.length" in sanitized
    assert "llm.model_name" in sanitized
    assert "feedback.rating" in sanitized
    assert "prompt" not in sanitized
    assert "answer" not in sanitized


def test_traced_span_provides_trace_context() -> None:
    with traced_span("outer"):
        outer = current_trace_context()
        with traced_span("inner"):
            inner = current_trace_context()

    assert outer.trace_id is not None
    assert outer.span_id is not None
    assert inner.trace_id == outer.trace_id
    assert inner.span_id is not None
    assert inner.span_id != outer.span_id


def test_current_trace_context_handles_invalid_span_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        trace,
        "get_current_span",
        lambda: SimpleNamespace(get_span_context=lambda: SimpleNamespace(is_valid=False)),
    )

    context = current_trace_context()

    assert context.trace_id is None
    assert context.span_id is None


def test_traced_span_records_exceptions(monkeypatch: pytest.MonkeyPatch) -> None:
    recorded: dict[str, object] = {}

    class FakeSpan:
        def set_attribute(self, *_args: object, **_kwargs: object) -> None:
            pass

        def record_exception(self, exc: Exception) -> None:
            recorded["exception"] = exc

        def set_status(self, status: object) -> None:
            recorded["status"] = status

    class FakeSpanContext:
        def __enter__(self) -> FakeSpan:
            return FakeSpan()

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            tb: object | None,
        ) -> bool:
            return False

    class FakeTracer:
        def start_as_current_span(self, _name: str) -> FakeSpanContext:
            return FakeSpanContext()

    monkeypatch.setattr(
        "pokemon_tcg_rag.monitoring.tracing.get_tracer",
        lambda: FakeTracer(),
    )

    with pytest.raises(RuntimeError, match="boom"), traced_span("test-span"):
        raise RuntimeError("boom")

    assert isinstance(recorded["exception"], RuntimeError)
    assert recorded["status"] is not None
