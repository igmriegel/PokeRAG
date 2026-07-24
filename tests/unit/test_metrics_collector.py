"""
TASK-037 — Metrics collector unit tests.
"""

from __future__ import annotations

from prometheus_client import CollectorRegistry

from pokemon_tcg_rag.monitoring.metrics_collector import MetricsCollector


def test_record_query_increments() -> None:
    registry = CollectorRegistry()
    collector = MetricsCollector(registry=registry)

    collector.record_query(
        model="gpt-4o-mini",
        latency=0.25,
        num_docs=3,
        status="success",
        sources=["rulebook_pdf", "pokegym_rulings"],
    )

    assert collector.query_counter.labels(model="gpt-4o-mini", status="success")._value.get() == 1.0
    assert collector.retrieved_docs._sum.get() == 3.0
    assert collector.source_counter.labels(source="rulebook_pdf")._value.get() == 1.0
    assert collector.source_counter.labels(source="pokegym_rulings")._value.get() == 1.0


def test_record_feedback_by_rating() -> None:
    registry = CollectorRegistry()
    collector = MetricsCollector(registry=registry)

    collector.record_feedback(1)
    collector.record_feedback(-1)

    assert collector.feedback_counter.labels(rating="positive")._value.get() == 1.0
    assert collector.feedback_counter.labels(rating="negative")._value.get() == 1.0
