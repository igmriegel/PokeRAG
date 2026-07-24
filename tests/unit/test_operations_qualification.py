"""
Unit tests for operational qualification helpers.
"""

from __future__ import annotations

from pokemon_tcg_rag.operations.qualification import run_qualification


class _FakeHandler:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def query(self, question: str, top_k: int | None = None) -> object:
        self.calls.append(question)
        return {"question": question, "top_k": top_k}


def test_run_qualification_records_latency_and_throughput() -> None:
    handler = _FakeHandler()
    result = run_qualification(
        handler,
        ["q1", "q2", "q3", "q4"],
        scenario="warm",
        concurrency=2,
        warmup_count=1,
        cost_per_call_usd=0.01,
    )

    assert result.sample_count >= 1
    assert result.throughput_qps > 0
    assert result.estimated_cost_usd == 0.03
    assert handler.calls
