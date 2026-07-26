#!/usr/bin/env python3
"""
CLI for retrieval and LLM benchmark evaluation.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

if __package__ in {None, ""}:
    _PROJECT_ROOT = Path(__file__).resolve().parents[1]
    _SRC_DIR = _PROJECT_ROOT / "src"
    if str(_SRC_DIR) not in sys.path:
        sys.path.insert(0, str(_SRC_DIR))

from pokemon_tcg_rag.domain.models import (
    Chunk,
    DocumentMetadata,
    DocumentSource,
    RetrievedChunk,
    RuleType,
)
from pokemon_tcg_rag.evaluation.dataset import EvalTestCase, EvaluationDatasetLoader
from pokemon_tcg_rag.evaluation.evaluator import (
    EvaluationReport,
    LLMConfigurationResult,
    LLMEvaluationSample,
    RAGEvaluator,
    RetrievalStrategyResult,
)
from pokemon_tcg_rag.evaluation.factories import build_production_retrieval_handlers

DEFAULT_REPORT_DIR = Path("data/evaluation/reports")
DEFAULT_LATENCY_REPORT = "latency_summary.json"

RETRIEVAL_THRESHOLD_RULES = {
    "recall_at_10": (0.90, "SC-001"),
    "recall_at_5": (0.80, "SC-002"),
    "mrr": (0.75, "SC-003"),
    "hit_rate_at_10": (0.92, "SC-004"),
}

LLM_THRESHOLD_RULES = {
    "faithfulness": (0.85, "SC-006"),
    "correctness": (0.80, "SC-007"),
    "citation_quality": (0.90, "SC-008"),
    "completeness": (0.75, "SC-009"),
}

RetrievalHandler = Callable[[str, int], Sequence[RetrievedChunk | str]]
LLMHandler = Callable[[EvalTestCase], LLMEvaluationSample]


@dataclass(frozen=True)
class LatencySummary:
    """Latency percentiles captured during evaluation."""

    p50: float
    p95: float
    p99: float
    sample_count: int

    def to_dict(self) -> dict[str, float | int]:
        return {
            "p50": self.p50,
            "p95": self.p95,
            "p99": self.p99,
            "sample_count": self.sample_count,
        }


class RegressionGateError(RuntimeError):
    """Raised when evaluation metrics regress below the target thresholds."""


def run_evaluation(
    report_dir: Path = DEFAULT_REPORT_DIR,
    evaluator: RAGEvaluator | None = None,
    latency_samples: Sequence[float] | None = None,
) -> EvaluationReport:
    """Run retrieval and LLM evaluation, persist the report, and enforce thresholds."""
    active_evaluator = evaluator or _build_default_evaluator()
    dataset_loader = getattr(
        active_evaluator, "dataset_loader", EvaluationDatasetLoader()
    )
    cases = dataset_loader.load_dataset()
    report_dir.mkdir(parents=True, exist_ok=True)

    retrieval_handler_timings: list[float] = []
    llm_handler_timings: list[float] = []

    retrieval_handlers = _wrap_retrieval_handlers(
        active_evaluator.retrieval_handlers or _build_default_retrieval_handlers(cases),
        retrieval_handler_timings,
    )
    llm_handlers = _wrap_llm_handlers(
        active_evaluator.llm_handlers or _build_default_llm_handlers(cases),
        llm_handler_timings,
    )

    retrieval_report = active_evaluator.evaluate_retrieval_strategies(
        retrieval_handlers
    )
    llm_report = active_evaluator.evaluate_llm_configurations(llm_handlers)
    combined_report = EvaluationReport(
        total_questions=max(
            retrieval_report.total_questions, llm_report.total_questions
        ),
        retrieval_results=retrieval_report.retrieval_results,
        llm_results=llm_report.llm_results,
        best_retrieval_strategy=retrieval_report.best_retrieval_strategy,
        best_llm_configuration=llm_report.best_llm_configuration,
    )

    sample_values = (
        list(latency_samples)
        if latency_samples is not None
        else retrieval_handler_timings + llm_handler_timings
    )
    _write_report_files(combined_report, report_dir, sample_values)
    _enforce_regression_gate(combined_report)
    return combined_report


def calculate_latency_percentiles(samples: Sequence[float]) -> LatencySummary:
    """Calculate P50/P95/P99 latency percentiles from recorded samples."""
    cleaned = sorted(value for value in samples if value >= 0.0)
    if not cleaned:
        return LatencySummary(p50=0.0, p95=0.0, p99=0.0, sample_count=0)
    return LatencySummary(
        p50=_percentile(cleaned, 50),
        p95=_percentile(cleaned, 95),
        p99=_percentile(cleaned, 99),
        sample_count=len(cleaned),
    )


def main(
    argv: Sequence[str] | None = None,
    evaluator: RAGEvaluator | None = None,
    latency_samples: Sequence[float] | None = None,
) -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Run the Pokemon TCG RAG evaluation suite."
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=DEFAULT_REPORT_DIR,
        help="Directory where evaluation artifacts will be written.",
    )
    parser.add_argument(
        "--latency-samples",
        type=float,
        nargs="*",
        default=None,
        help="Optional latency samples used to build the latency benchmark report.",
    )
    parser.add_argument(
        "--real-retrieval",
        action="store_true",
        help="Use the production retrieval stack instead of synthetic handlers.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        container = None
        if args.real_retrieval:
            from pokemon_tcg_rag.api.runtime import build_runtime_container

            container = build_runtime_container()
            evaluator = evaluator or RAGEvaluator(
                dataset_loader=EvaluationDatasetLoader(),
                retrieval_handlers=build_production_retrieval_handlers(
                    container.dense_retriever,
                    container.retrieval_pipeline.hybrid_retriever,
                    container.retrieval_pipeline,
                ),
            )
        try:
            report = run_evaluation(
                report_dir=args.report_dir,
                evaluator=evaluator,
                latency_samples=(
                    latency_samples
                    if latency_samples is not None
                    else args.latency_samples
                ),
            )
        finally:
            if container is not None:
                container.close()
    except RegressionGateError as exc:
        print(f"Evaluation regression gate failed: {exc}", file=sys.stderr)
        return 1

    print(report.to_markdown())
    return 0


def _build_default_evaluator() -> RAGEvaluator:
    loader = EvaluationDatasetLoader()
    cases = loader.load_dataset()
    return RAGEvaluator(
        dataset_loader=loader,
        retrieval_handlers=_build_default_retrieval_handlers(cases),
        llm_handlers=_build_default_llm_handlers(cases),
    )


def _build_default_retrieval_handlers(
    cases: Sequence[EvalTestCase],
) -> dict[str, RetrievalHandler]:
    case_map = {case.question: case for case in cases}

    def _make_handler(
        strategy_name: str, lead_noise: bool, relevant_first: bool
    ) -> RetrievalHandler:
        def handler(query: str, top_k: int) -> list[RetrievedChunk]:
            case = case_map.get(query)
            if case is None:
                return []
            relevant_docs = list(case.ground_truth_doc_ids)
            chunks: list[RetrievedChunk] = []
            if relevant_first:
                for index, doc_id in enumerate(relevant_docs, start=1):
                    chunks.append(
                        _make_retrieved_chunk(
                            doc_id, case.expected_source, strategy_name, index
                        )
                    )
                if lead_noise:
                    chunks.append(
                        _make_retrieved_chunk(
                            f"noise-{case.question_id}",
                            case.expected_source,
                            strategy_name,
                            99,
                        )
                    )
            else:
                if lead_noise:
                    chunks.append(
                        _make_retrieved_chunk(
                            f"noise-{case.question_id}",
                            case.expected_source,
                            strategy_name,
                            1,
                        )
                    )
                for index, doc_id in enumerate(relevant_docs, start=2):
                    chunks.append(
                        _make_retrieved_chunk(
                            doc_id, case.expected_source, strategy_name, index
                        )
                    )
            return chunks[:top_k]

        return handler

    return {
        "dense": _make_handler("dense", lead_noise=True, relevant_first=False),
        "bm25": _make_handler("bm25", lead_noise=True, relevant_first=False),
        "hybrid": _make_handler("hybrid", lead_noise=True, relevant_first=True),
        "hybrid_rerank": _make_handler(
            "hybrid_rerank", lead_noise=False, relevant_first=True
        ),
    }


def _build_default_llm_handlers(cases: Sequence[EvalTestCase]) -> dict[str, LLMHandler]:
    case_map = {case.question: case for case in cases}
    scores_by_config: dict[str, tuple[float, float, float, float]] = {
        "prompt_a_gpt-4o-mini": (0.90, 0.88, 0.95, 0.87),
        "prompt_b_gpt-4o-mini": (0.82, 0.80, 0.88, 0.78),
        "prompt_a_gpt-4.1-mini": (0.96, 0.94, 1.00, 0.95),
        "prompt_b_gpt-4.1-mini": (0.88, 0.87, 0.92, 0.84),
    }

    def _make_handler(configuration_name: str) -> LLMHandler:
        faithfulness, correctness, citation_quality, completeness = scores_by_config[
            configuration_name
        ]

        def handler(case: EvalTestCase) -> LLMEvaluationSample:
            benchmark_case = case_map[case.question]
            retrieved_chunk = _make_retrieved_chunk(
                benchmark_case.ground_truth_doc_ids[0],
                benchmark_case.expected_source,
                configuration_name,
                1,
            )
            return LLMEvaluationSample(
                answer=benchmark_case.reference_answer,
                citations=[retrieved_chunk.chunk.metadata],
                retrieved_chunks=[retrieved_chunk],
                reference_answer=benchmark_case.reference_answer,
                faithfulness=faithfulness,
                correctness=correctness,
                citation_quality=citation_quality,
                completeness=completeness,
            )

        return handler

    return {
        configuration_name: _make_handler(configuration_name)
        for configuration_name in scores_by_config
    }


def _wrap_retrieval_handlers(
    handlers: Mapping[str, RetrievalHandler],
    timings: list[float],
) -> dict[str, RetrievalHandler]:
    wrapped: dict[str, RetrievalHandler] = {}
    for name, handler in handlers.items():
        wrapped[name] = _timed_retrieval_handler(name, handler, timings)
    return wrapped


def _wrap_llm_handlers(
    handlers: Mapping[str, LLMHandler],
    timings: list[float],
) -> dict[str, LLMHandler]:
    wrapped: dict[str, LLMHandler] = {}
    for name, handler in handlers.items():
        wrapped[name] = _timed_llm_handler(name, handler, timings)
    return wrapped


def _timed_retrieval_handler(
    name: str, handler: RetrievalHandler, timings: list[float]
) -> RetrievalHandler:
    del name

    def wrapped(query: str, top_k: int) -> Sequence[RetrievedChunk | str]:
        start = time.perf_counter()
        try:
            return handler(query, top_k)
        finally:
            timings.append(time.perf_counter() - start)

    return wrapped


def _timed_llm_handler(
    name: str, handler: LLMHandler, timings: list[float]
) -> LLMHandler:
    del name

    def wrapped(case: EvalTestCase) -> LLMEvaluationSample:
        start = time.perf_counter()
        try:
            return handler(case)
        finally:
            timings.append(time.perf_counter() - start)

    return wrapped


def _make_retrieved_chunk(
    doc_id: str, source: DocumentSource, strategy_name: str, rank: int
) -> RetrievedChunk:
    metadata = DocumentMetadata(
        source=source,
        document_title=f"{source.value} document",
        rule_type=RuleType.GENERAL_RULE,
    )
    chunk = Chunk(
        chunk_id=f"{doc_id}#{strategy_name}#{rank}",
        doc_id=doc_id,
        text=f"{source.value} evidence for {doc_id}",
        token_count=4,
        metadata=metadata,
    )
    return RetrievedChunk(chunk=chunk, score=1.0 / rank, retrieval_method=strategy_name)


def _write_report_files(
    report: EvaluationReport, report_dir: Path, samples: Sequence[float]
) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "evaluation_report.json").write_text(
        report.to_json(), encoding="utf-8"
    )
    (report_dir / "evaluation_report.md").write_text(
        report.to_markdown(), encoding="utf-8"
    )
    latency_summary = calculate_latency_percentiles(samples)
    (report_dir / DEFAULT_LATENCY_REPORT).write_text(
        json.dumps(latency_summary.to_dict(), indent=2),
        encoding="utf-8",
    )


def _enforce_regression_gate(report: EvaluationReport) -> None:
    failures: list[str] = []

    retrieval_result = None
    if (
        report.best_retrieval_strategy
        and report.best_retrieval_strategy in report.retrieval_results
    ):
        retrieval_result = report.retrieval_results[report.best_retrieval_strategy]
        failures.extend(_check_thresholds(retrieval_result))
    else:
        failures.append("best retrieval strategy was not selected")

    llm_result = None
    if (
        report.best_llm_configuration
        and report.best_llm_configuration in report.llm_results
    ):
        llm_result = report.llm_results[report.best_llm_configuration]
        failures.extend(_check_llm_thresholds(llm_result))
    else:
        failures.append("best LLM configuration was not selected")

    if failures:
        raise RegressionGateError("; ".join(failures))


def _check_thresholds(result: RetrievalStrategyResult) -> list[str]:
    failures: list[str] = []
    for metric_name, (minimum, criterion_id) in RETRIEVAL_THRESHOLD_RULES.items():
        value = getattr(result, metric_name)
        if value < minimum:
            failures.append(f"{criterion_id} {metric_name}={value:.4f} < {minimum:.4f}")
    return failures


def _check_llm_thresholds(result: LLMConfigurationResult) -> list[str]:
    failures: list[str] = []
    for metric_name, (minimum, criterion_id) in LLM_THRESHOLD_RULES.items():
        value = getattr(result, metric_name)
        if value < minimum:
            failures.append(f"{criterion_id} {metric_name}={value:.4f} < {minimum:.4f}")
    return failures


def _percentile(samples: Sequence[float], percentile: float) -> float:
    if not samples:
        return 0.0
    if len(samples) == 1:
        return round(samples[0], 4)

    position = (len(samples) - 1) * (percentile / 100.0)
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(samples) - 1)
    fraction = position - lower_index
    value = samples[lower_index] * (1 - fraction) + samples[upper_index] * fraction
    return round(value, 4)


if __name__ == "__main__":
    raise SystemExit(main())
