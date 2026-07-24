"""
Evaluation harness for retrieval and LLM quality comparisons.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping, Sequence

from pydantic import BaseModel, ConfigDict, Field

from pokemon_tcg_rag.domain.models import DocumentMetadata, RetrievedChunk
from pokemon_tcg_rag.evaluation.dataset import EvalTestCase, EvaluationDatasetLoader
from pokemon_tcg_rag.evaluation.metrics import (
    calculate_citation_quality,
    calculate_completeness,
    calculate_correctness,
    calculate_faithfulness,
    calculate_hit_rate,
    calculate_mrr,
    calculate_recall_at_k,
)

LOGGER = logging.getLogger(__name__)


class RetrievalStrategyResult(BaseModel):
    """Aggregate metrics for one retrieval strategy."""

    model_config = ConfigDict(frozen=True)

    strategy_name: str
    total_questions: int
    recall_at_5: float
    recall_at_10: float
    mrr: float
    hit_rate_at_5: float
    hit_rate_at_10: float


class LLMConfigurationResult(BaseModel):
    """Aggregate metrics for one prompt/model configuration."""

    model_config = ConfigDict(frozen=True)

    configuration_name: str
    total_questions: int
    faithfulness: float
    correctness: float
    citation_quality: float
    completeness: float


class EvaluationReport(BaseModel):
    """Combined report for retrieval and LLM evaluation."""

    model_config = ConfigDict(frozen=True)

    total_questions: int = 0
    retrieval_results: dict[str, RetrievalStrategyResult] = Field(default_factory=dict)
    llm_results: dict[str, LLMConfigurationResult] = Field(default_factory=dict)
    best_retrieval_strategy: str | None = None
    best_llm_configuration: str | None = None

    def to_markdown(self) -> str:
        """Render a compact Markdown summary."""
        lines = ["# Evaluation Report", ""]

        if self.retrieval_results:
            lines.append("## Retrieval strategies")
            lines.append("")
            lines.append("| Strategy | Recall@5 | Recall@10 | MRR | Hit@5 | Hit@10 |")
            lines.append("| :--- | ---: | ---: | ---: | ---: | ---: |")
            for result in self.retrieval_results.values():
                lines.append(
                    f"| {result.strategy_name} | {result.recall_at_5:.4f} | {result.recall_at_10:.4f} | "
                    f"{result.mrr:.4f} | {result.hit_rate_at_5:.4f} | {result.hit_rate_at_10:.4f} |"
                )
            lines.append("")
            lines.append(f"Best retrieval strategy: {self.best_retrieval_strategy or 'n/a'}")
            lines.append("")

        if self.llm_results:
            lines.append("## LLM configurations")
            lines.append("")
            lines.append("| Configuration | Faithfulness | Correctness | Citation Quality | Completeness |")
            lines.append("| :--- | ---: | ---: | ---: | ---: |")
            for result in self.llm_results.values():
                lines.append(
                    f"| {result.configuration_name} | {result.faithfulness:.4f} | {result.correctness:.4f} | "
                    f"{result.citation_quality:.4f} | {result.completeness:.4f} |"
                )
            lines.append("")
            lines.append(f"Best LLM configuration: {self.best_llm_configuration or 'n/a'}")

        return "\n".join(lines).strip() + "\n"

    def to_json(self) -> str:
        """Render a JSON payload suitable for writing to disk."""
        return self.model_dump_json(indent=2)


RetrievalHandler = Callable[[str, int], Sequence[RetrievedChunk | str]]


class LLMEvaluationSample(BaseModel):
    """Normalized output from a prompt/model benchmark run."""

    model_config = ConfigDict(frozen=True)

    answer: str
    citations: list[DocumentMetadata] = Field(default_factory=list)
    retrieved_chunks: list[RetrievedChunk] = Field(default_factory=list)
    reference_answer: str = ""
    faithfulness: float | None = None
    correctness: float | None = None
    citation_quality: float | None = None
    completeness: float | None = None


LLMHandler = Callable[[EvalTestCase], LLMEvaluationSample | RetrievedChunk | dict[str, object]]


class RAGEvaluator:
    """Evaluate benchmark questions across retrieval strategies and LLM configs."""

    def __init__(
        self,
        rag_chain: object | None = None,
        dataset_loader: EvaluationDatasetLoader | None = None,
        retrieval_handlers: Mapping[str, RetrievalHandler] | None = None,
        llm_handlers: Mapping[str, LLMHandler] | None = None,
    ) -> None:
        self.rag_chain = rag_chain
        self.dataset_loader = dataset_loader or EvaluationDatasetLoader()
        self.retrieval_handlers = dict(retrieval_handlers or {})
        self.llm_handlers = dict(llm_handlers or {})

    def evaluate_retrieval_strategies(
        self,
        strategy_handlers: Mapping[str, RetrievalHandler] | None = None,
    ) -> EvaluationReport:
        """Run all retrieval handlers on the benchmark and compare their metrics."""
        cases = self.dataset_loader.load_dataset()
        handlers = dict(strategy_handlers or self.retrieval_handlers or self._default_retrieval_handlers())
        if not handlers:
            raise ValueError("No retrieval handlers available for evaluation")

        retrieval_results: dict[str, RetrievalStrategyResult] = {}
        for strategy_name, handler in handlers.items():
            retrieval_results[strategy_name] = self._evaluate_single_retrieval_strategy(strategy_name, handler, cases)

        best_strategy = self._select_best_retrieval_strategy(retrieval_results)
        return EvaluationReport(
            total_questions=len(cases),
            retrieval_results=retrieval_results,
            best_retrieval_strategy=best_strategy,
        )

    def evaluate_llm_configurations(
        self,
        llm_handlers: Mapping[str, LLMHandler] | None = None,
    ) -> EvaluationReport:
        """Run prompt/model combinations on the benchmark and compare their metrics."""
        cases = self.dataset_loader.load_dataset()
        handlers = dict(llm_handlers or self.llm_handlers)
        if not handlers:
            raise ValueError("No LLM handlers available for evaluation")

        llm_results: dict[str, LLMConfigurationResult] = {}
        for configuration_name, handler in handlers.items():
            llm_results[configuration_name] = self._evaluate_single_llm_configuration(
                configuration_name,
                handler,
                cases,
            )

        best_configuration = self._select_best_llm_configuration(llm_results)
        return EvaluationReport(
            total_questions=len(cases),
            llm_results=llm_results,
            best_llm_configuration=best_configuration,
        )

    def run_evaluation(self) -> EvaluationReport:
        """Backward-compatible alias that runs retrieval evaluation."""
        return self.evaluate_retrieval_strategies()

    def _evaluate_single_retrieval_strategy(
        self,
        strategy_name: str,
        handler: RetrievalHandler,
        cases: Sequence[EvalTestCase],
    ) -> RetrievalStrategyResult:
        recall_5: list[float] = []
        recall_10: list[float] = []
        mrr_scores: list[float] = []
        hit_5: list[float] = []
        hit_10: list[float] = []

        for case in cases:
            retrieved = handler(case.question, 10)
            recall_5.append(calculate_recall_at_k(retrieved, case.ground_truth_doc_ids, 5))
            recall_10.append(calculate_recall_at_k(retrieved, case.ground_truth_doc_ids, 10))
            mrr_scores.append(calculate_mrr(retrieved, case.ground_truth_doc_ids))
            hit_5.append(calculate_hit_rate(retrieved, case.ground_truth_doc_ids, 5))
            hit_10.append(calculate_hit_rate(retrieved, case.ground_truth_doc_ids, 10))

        return RetrievalStrategyResult(
            strategy_name=strategy_name,
            total_questions=len(cases),
            recall_at_5=self._mean(recall_5),
            recall_at_10=self._mean(recall_10),
            mrr=self._mean(mrr_scores),
            hit_rate_at_5=self._mean(hit_5),
            hit_rate_at_10=self._mean(hit_10),
        )

    def _evaluate_single_llm_configuration(
        self,
        configuration_name: str,
        handler: LLMHandler,
        cases: Sequence[EvalTestCase],
    ) -> LLMConfigurationResult:
        faithfulness_scores: list[float] = []
        correctness_scores: list[float] = []
        citation_scores: list[float] = []
        completeness_scores: list[float] = []

        for case in cases:
            sample = self._normalize_llm_sample(handler(case), case)
            faithfulness_scores.append(self._score_faithfulness(sample))
            correctness_scores.append(self._score_correctness(sample))
            citation_scores.append(self._score_citation_quality(sample))
            completeness_scores.append(self._score_completeness(sample))

        return LLMConfigurationResult(
            configuration_name=configuration_name,
            total_questions=len(cases),
            faithfulness=self._mean(faithfulness_scores),
            correctness=self._mean(correctness_scores),
            citation_quality=self._mean(citation_scores),
            completeness=self._mean(completeness_scores),
        )

    def _normalize_llm_sample(
        self,
        result: LLMEvaluationSample | RetrievedChunk | dict[str, object],
        case: EvalTestCase,
    ) -> LLMEvaluationSample:
        if isinstance(result, LLMEvaluationSample):
            if result.reference_answer:
                return result
            return result.model_copy(update={"reference_answer": case.reference_answer})

        if isinstance(result, RetrievedChunk):
            return LLMEvaluationSample(
                answer="",
                retrieved_chunks=[result],
                reference_answer=case.reference_answer,
            )

        if isinstance(result, dict):
            payload = dict(result)
            payload.setdefault("reference_answer", case.reference_answer)
            return LLMEvaluationSample.model_validate(payload)

        raise TypeError(f"Unsupported LLM evaluation result: {type(result)!r}")

    def _score_faithfulness(self, sample: LLMEvaluationSample) -> float:
        if sample.faithfulness is not None:
            return sample.faithfulness
        return calculate_faithfulness(sample.answer, sample.retrieved_chunks)

    def _score_correctness(self, sample: LLMEvaluationSample) -> float:
        if sample.correctness is not None:
            return sample.correctness
        return calculate_correctness(sample.answer, sample.reference_answer)

    def _score_citation_quality(self, sample: LLMEvaluationSample) -> float:
        if sample.citation_quality is not None:
            return sample.citation_quality
        return calculate_citation_quality(sample.citations, sample.retrieved_chunks)

    def _score_completeness(self, sample: LLMEvaluationSample) -> float:
        if sample.completeness is not None:
            return sample.completeness
        return calculate_completeness(sample.answer, sample.reference_answer)

    def _select_best_retrieval_strategy(self, results: Mapping[str, RetrievalStrategyResult]) -> str:
        best_name = max(
            results,
            key=lambda name: (
                results[name].mrr,
                results[name].recall_at_10,
                results[name].recall_at_5,
                results[name].hit_rate_at_10,
            ),
        )
        LOGGER.info("best_retrieval_strategy_selected", strategy=best_name)
        return best_name

    def _select_best_llm_configuration(self, results: Mapping[str, LLMConfigurationResult]) -> str:
        best_name = max(
            results,
            key=lambda name: (
                self._mean(
                    [
                        results[name].faithfulness,
                        results[name].correctness,
                        results[name].citation_quality,
                        results[name].completeness,
                    ]
                ),
                results[name].faithfulness,
                results[name].correctness,
            ),
        )
        LOGGER.info("best_llm_configuration_selected", configuration=best_name)
        return best_name

    def _default_retrieval_handlers(self) -> dict[str, RetrievalHandler]:
        if self.rag_chain is None:
            return {}

        def baseline_handler(query: str, top_k: int) -> Sequence[RetrievedChunk | str]:
            response = self.rag_chain.query(query)  # type: ignore[call-arg]
            return response.retrieved_chunks[:top_k]

        return {"baseline": baseline_handler}

    def _mean(self, values: Sequence[float]) -> float:
        if not values:
            return 0.0
        return round(sum(values) / len(values), 4)
