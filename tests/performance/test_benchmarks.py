"""
Performance and latency benchmarks.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from pokemon_tcg_rag.domain.models import (
    Chunk,
    DocumentMetadata,
    DocumentSource,
    RuleType,
)
from pokemon_tcg_rag.evaluation.evaluator import (
    EvaluationReport,
    LLMConfigurationResult,
    RetrievalStrategyResult,
)
from pokemon_tcg_rag.retrieval.bm25 import BM25Retriever
from scripts.run_evaluation import calculate_latency_percentiles, main


@pytest.mark.performance
def test_bm25_retrieval_speed_benchmark() -> None:
    # Benchmark indexing speed over 1,000 synthetic chunks
    chunks = [
        Chunk(
            chunk_id=f"c_{i}",
            doc_id=f"d_{i}",
            text=f"Sample Pokemon TCG rule document number {i} regarding evolution and energy attachment.",
            token_count=12,
            metadata=DocumentMetadata(
                source=DocumentSource.RULEBOOK_PDF,
                document_title="Rulebook",
                rule_type=RuleType.GENERAL_RULE,
            ),
        )
        for i in range(1000)
    ]
    start = time.time()
    bm25 = BM25Retriever(chunks)
    index_time = time.time() - start
    assert index_time < 2.0  # Index 1000 chunks under 2 seconds

    start = time.time()
    results = bm25.retrieve("energy attachment rules", top_k=10)
    search_time = time.time() - start
    assert search_time < 0.1  # Search under 100ms
    assert len(results) == 10


class _FakeEvaluator:
    def __init__(self, retrieval_report: EvaluationReport, llm_report: EvaluationReport) -> None:
        self.retrieval_handlers = {"dense": lambda query, top_k: []}
        self.llm_handlers = {"prompt_a_gpt-4o-mini": lambda case: None}
        self._retrieval_report = retrieval_report
        self._llm_report = llm_report

    def evaluate_retrieval_strategies(self, strategy_handlers=None) -> EvaluationReport:
        return self._retrieval_report

    def evaluate_llm_configurations(self, llm_handlers=None) -> EvaluationReport:
        return self._llm_report


@pytest.mark.performance
def test_cli_runs_and_writes_report(tmp_path: Path) -> None:
    retrieval_report = EvaluationReport(
        total_questions=2,
        retrieval_results={
            "hybrid_rerank": RetrievalStrategyResult(
                strategy_name="hybrid_rerank",
                total_questions=2,
                recall_at_5=0.91,
                recall_at_10=0.95,
                mrr=0.88,
                hit_rate_at_5=0.95,
                hit_rate_at_10=0.98,
            )
        },
        best_retrieval_strategy="hybrid_rerank",
    )
    llm_report = EvaluationReport(
        total_questions=2,
        llm_results={
            "prompt_a_gpt-4.1-mini": LLMConfigurationResult(
                configuration_name="prompt_a_gpt-4.1-mini",
                total_questions=2,
                faithfulness=0.96,
                correctness=0.94,
                citation_quality=0.98,
                completeness=0.92,
            )
        },
        best_llm_configuration="prompt_a_gpt-4.1-mini",
    )
    fake_evaluator = _FakeEvaluator(retrieval_report, llm_report)

    exit_code = main(
        ["--report-dir", str(tmp_path)],
        evaluator=fake_evaluator,  # type: ignore[arg-type]
        latency_samples=[0.1, 0.2, 0.3, 0.4],
    )

    assert exit_code == 0
    assert (tmp_path / "evaluation_report.json").exists()
    assert (tmp_path / "evaluation_report.md").exists()
    assert (tmp_path / "latency_summary.json").exists()

    payload = json.loads((tmp_path / "latency_summary.json").read_text(encoding="utf-8"))
    assert payload["p50"] == pytest.approx(0.25)
    assert payload["p95"] == pytest.approx(0.385)
    assert payload["p99"] == pytest.approx(0.397)


@pytest.mark.performance
def test_regression_gate_fails_below_threshold(tmp_path: Path) -> None:
    retrieval_report = EvaluationReport(
        total_questions=2,
        retrieval_results={
            "bm25": RetrievalStrategyResult(
                strategy_name="bm25",
                total_questions=2,
                recall_at_5=0.5,
                recall_at_10=0.6,
                mrr=0.5,
                hit_rate_at_5=0.5,
                hit_rate_at_10=0.6,
            )
        },
        best_retrieval_strategy="bm25",
    )
    llm_report = EvaluationReport(
        total_questions=2,
        llm_results={
            "prompt_b_gpt-4o-mini": LLMConfigurationResult(
                configuration_name="prompt_b_gpt-4o-mini",
                total_questions=2,
                faithfulness=0.5,
                correctness=0.5,
                citation_quality=0.5,
                completeness=0.5,
            )
        },
        best_llm_configuration="prompt_b_gpt-4o-mini",
    )
    fake_evaluator = _FakeEvaluator(retrieval_report, llm_report)

    exit_code = main(
        ["--report-dir", str(tmp_path)],
        evaluator=fake_evaluator,
        latency_samples=[0.1, 0.2],
    )  # type: ignore[arg-type]

    assert exit_code == 1


@pytest.mark.performance
def test_latency_percentiles_recorded() -> None:
    summary = calculate_latency_percentiles([0.1, 0.2, 0.3, 0.4])

    assert summary.sample_count == 4
    assert summary.p50 == pytest.approx(0.25)
    assert summary.p95 == pytest.approx(0.385)
    assert summary.p99 == pytest.approx(0.397)
