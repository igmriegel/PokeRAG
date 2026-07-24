"""
Capacity and cost qualification helpers.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Protocol


class SupportsQuery(Protocol):
    def query(self, question: str, top_k: int | None = None) -> object: ...


@dataclass(frozen=True, slots=True)
class QualificationResult:
    scenario: str
    sample_count: int
    p50: float
    p95: float
    p99: float
    error_count: int
    throughput_qps: float
    estimated_cost_usd: float

    def to_dict(self) -> dict[str, float | int | str]:
        return {
            "scenario": self.scenario,
            "sample_count": self.sample_count,
            "p50": self.p50,
            "p95": self.p95,
            "p99": self.p99,
            "error_count": self.error_count,
            "throughput_qps": self.throughput_qps,
            "estimated_cost_usd": self.estimated_cost_usd,
        }


def run_qualification(
    handler: SupportsQuery,
    questions: list[str],
    *,
    scenario: str,
    concurrency: int = 4,
    warmup_count: int = 0,
    cost_per_call_usd: float = 0.0,
) -> QualificationResult:
    """Run a small load qualification sweep against the provided query handler."""
    latencies: list[float] = []
    error_count = 0

    for question in questions[:warmup_count]:
        try:
            start = time.perf_counter()
            handler.query(question, top_k=5)
            latencies.append(time.perf_counter() - start)
        except Exception:
            error_count += 1

    load_questions = questions[warmup_count:] or questions
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as executor:
        futures = [executor.submit(_timed_query, handler, question) for question in load_questions]
        for future in futures:
            duration, failed = future.result()
            if failed:
                error_count += 1
            else:
                latencies.append(duration)
    elapsed = max(time.perf_counter() - start, 1e-9)
    if not latencies:
        latencies = [0.0]

    latencies.sort()
    return QualificationResult(
        scenario=scenario,
        sample_count=len(latencies),
        p50=_percentile(latencies, 50),
        p95=_percentile(latencies, 95),
        p99=_percentile(latencies, 99),
        error_count=error_count,
        throughput_qps=round(len(load_questions) / elapsed, 4),
        estimated_cost_usd=round(len(load_questions) * cost_per_call_usd, 6),
    )


def _timed_query(handler: SupportsQuery, question: str) -> tuple[float, bool]:
    start = time.perf_counter()
    try:
        handler.query(question, top_k=5)
        return time.perf_counter() - start, False
    except Exception:
        return time.perf_counter() - start, True


def _percentile(samples: list[float], percentile: float) -> float:
    if not samples:
        return 0.0
    if len(samples) == 1:
        return round(samples[0], 4)
    position = (len(samples) - 1) * (percentile / 100.0)
    lower = int(position)
    upper = min(lower + 1, len(samples) - 1)
    fraction = position - lower
    value = samples[lower] * (1 - fraction) + samples[upper] * fraction
    return round(value, 4)
