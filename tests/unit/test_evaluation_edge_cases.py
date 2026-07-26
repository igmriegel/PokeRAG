"""
Unit tests for evaluation helper edge cases and normalization branches.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from pokemon_tcg_rag.domain.models import (
    AnswerResponse,
    Chunk,
    DocumentMetadata,
    DocumentSource,
    RetrievedChunk,
    RuleType,
)
from pokemon_tcg_rag.evaluation.dataset import EvalTestCase, EvaluationDatasetLoader
from pokemon_tcg_rag.evaluation.evaluator import (
    LLMConfigurationResult,
    LLMEvaluationSample,
    RAGEvaluator,
    RetrievalStrategyResult,
)
from pokemon_tcg_rag.evaluation.metrics import (
    calculate_citation_quality,
    calculate_completeness,
    calculate_correctness,
    calculate_faithfulness,
    calculate_hit_rate,
    calculate_mrr,
    calculate_recall_at_k,
    combine_scores,
)


def _metadata(
    *,
    source: DocumentSource = DocumentSource.RULEBOOK_PDF,
    page_number: int | None = 12,
) -> DocumentMetadata:
    return DocumentMetadata(
        source=source,
        document_title="Rulebook",
        page_number=page_number,
        card_name="Rare Candy",
        rule_type=RuleType.GENERAL_RULE,
    )


def _retrieved(
    text: str = "Rare Candy lets you evolve faster.",
    *,
    doc_id: str = "doc-1",
    source: DocumentSource = DocumentSource.RULEBOOK_PDF,
) -> RetrievedChunk:
    chunk = Chunk(
        chunk_id=f"{doc_id}#1",
        doc_id=doc_id,
        text=text,
        token_count=len(text.split()),
        metadata=_metadata(source=source),
    )
    return RetrievedChunk(chunk=chunk, score=0.9, retrieval_method="dense")


def _case(question_id: str = "Q001") -> EvalTestCase:
    return EvalTestCase(
        question_id=question_id,
        question="Can I use Rare Candy?",
        ground_truth_doc_ids=["doc-1"],
        expected_source=DocumentSource.RULEBOOK_PDF,
        reference_answer="Yes.",
    )


def test_metric_helpers_cover_boundary_conditions() -> None:
    retrieved = [_retrieved(), "doc-2", " "]

    assert calculate_recall_at_k(retrieved, [], 5) == 0.0
    assert calculate_recall_at_k(retrieved, ["doc-1"], 0) == 0.0
    assert calculate_recall_at_k(retrieved, ["doc-1", "doc-2"], 2) == 1.0
    assert calculate_mrr(retrieved, []) == 0.0
    assert calculate_mrr(retrieved, ["doc-2"]) == 0.5
    assert calculate_hit_rate(retrieved, [], 5) == 0.0
    assert calculate_hit_rate(retrieved, ["doc-1"], 1) == 1.0

    assert calculate_faithfulness("", [_retrieved()]) == 0.0
    assert calculate_faithfulness("Rare Candy", []) == 0.0
    assert (
        calculate_faithfulness(
            "Rare Candy evolves a Pokemon.",
            [_retrieved("Rare Candy evolves a Pokemon.")],
        )
        > 0.0
    )

    assert calculate_correctness("", "Yes.") == 0.0
    assert calculate_correctness("Yes.", "") == 0.0
    assert calculate_completeness("", "Yes.") == 0.0
    assert calculate_completeness("Yes.", "") == 0.0

    citation = _metadata()
    assert calculate_citation_quality([], [_retrieved()]) == 0.0
    assert calculate_citation_quality([citation], []) == 0.0
    assert calculate_citation_quality([citation], [_retrieved()]) == 1.0

    assert combine_scores([1.2, -0.5, float("nan")]) == 0.5


def test_metric_helpers_cover_zero_return_branches() -> None:
    assert calculate_recall_at_k(["doc-1"], [" ", ""], 5) == 0.0
    assert calculate_hit_rate(["doc-1"], [" ", ""], 5) == 0.0
    assert calculate_faithfulness("abc", [_retrieved("def")]) == 0.0
    assert calculate_correctness("!!!", "???") == 0.0
    assert calculate_completeness("!!!", "???") == 0.0
    assert combine_scores([]) == 0.0


def test_dataset_loader_normalization_and_validation_edges(
    tmp_path: pytest.TempPathFactory,
) -> None:
    loader = EvaluationDatasetLoader(tmp_path / "missing.json")
    with pytest.raises(FileNotFoundError):
        loader.load_dataset()

    normalized = loader._normalize_case(
        {
            "question": "  Can I use Rare Candy?  ",
            "expected_doc_ids": ["doc-1", " doc-2 "],
            "expected_source": DocumentSource.RULEBOOK_PDF.value,
            "expected_answer_keywords": [" yes ", "", "allowed"],
        },
        1,
    )
    assert normalized["question"] == "  Can I use Rare Candy?  "
    assert normalized["reference_answer"] == "yes; allowed"

    with pytest.raises(ValueError):
        loader._normalize_case(
            {
                "question_id": "Q002",
                "question": "Can I use Rare Candy?",
                "expected_doc_ids": ["doc-1"],
            },
            2,
        )

    with pytest.raises(ValidationError):
        EvalTestCase(
            question_id="Q003",
            question="Can I use Rare Candy?",
            ground_truth_doc_ids=["doc-1", "doc-1"],
            expected_source=DocumentSource.RULEBOOK_PDF,
            reference_answer="Yes.",
        )


def test_evaluator_handles_default_handlers_and_normalization_edges() -> None:
    cases = [_case(), _case("Q002")]

    class Loader:
        def load_dataset(self) -> list[EvalTestCase]:
            return cases

    class FakeChain:
        def query(self, raw_query: str, top_k: int | None = None) -> AnswerResponse:
            metadata = _metadata()
            chunk = _retrieved()
            return AnswerResponse(
                query_id="qr-1",
                query=raw_query,
                rewritten_query=raw_query,
                answer="Yes.",
                citations=[metadata],
                retrieved_chunks=[chunk],
                model_name="gpt-4o-mini",
                latency_seconds=0.1,
            )

    evaluator = RAGEvaluator(rag_chain=FakeChain(), dataset_loader=Loader())

    default_handlers = evaluator._default_retrieval_handlers()
    assert "baseline" in default_handlers
    assert default_handlers["baseline"]("Can I use Rare Candy?", 1)

    retrieval_report = evaluator.evaluate_retrieval_strategies()
    assert retrieval_report.best_retrieval_strategy == "baseline"
    assert retrieval_report.total_questions == 2
    assert evaluator.run_evaluation().best_retrieval_strategy == "baseline"

    llm_sample = evaluator._normalize_llm_sample(
        {
            "answer": "Yes.",
            "citations": [_metadata().model_dump()],
            "retrieved_chunks": [
                {
                    "chunk": _retrieved().chunk,
                    "score": 0.9,
                    "retrieval_method": "dense",
                }
            ],
        },
        _case(),
    )
    assert isinstance(llm_sample, LLMEvaluationSample)
    assert llm_sample.reference_answer == "Yes."

    retrieved_sample = evaluator._normalize_llm_sample(_retrieved(), _case())
    assert retrieved_sample.retrieved_chunks

    score_sample = LLMEvaluationSample(
        answer="Yes.",
        citations=[_metadata()],
        retrieved_chunks=[_retrieved()],
        reference_answer="Yes.",
        faithfulness=0.1,
        correctness=0.2,
        citation_quality=0.3,
        completeness=0.4,
    )
    assert evaluator._score_faithfulness(score_sample) == 0.1
    assert evaluator._score_correctness(score_sample) == 0.2
    assert evaluator._score_citation_quality(score_sample) == 0.3
    assert evaluator._score_completeness(score_sample) == 0.4
    assert evaluator._mean([]) == 0.0

    retrieval_result = RetrievalStrategyResult(
        strategy_name="a",
        total_questions=1,
        recall_at_5=0.9,
        recall_at_10=0.8,
        mrr=0.7,
        hit_rate_at_5=0.6,
        hit_rate_at_10=0.5,
    )
    other_result = RetrievalStrategyResult(
        strategy_name="b",
        total_questions=1,
        recall_at_5=0.5,
        recall_at_10=0.4,
        mrr=0.3,
        hit_rate_at_5=0.2,
        hit_rate_at_10=0.1,
    )
    assert (
        evaluator._select_best_retrieval_strategy({"a": retrieval_result, "b": other_result}) == "a"
    )

    llm_result = LLMConfigurationResult(
        configuration_name="a",
        total_questions=1,
        faithfulness=0.9,
        correctness=0.8,
        citation_quality=0.7,
        completeness=0.6,
    )
    other_llm_result = LLMConfigurationResult(
        configuration_name="b",
        total_questions=1,
        faithfulness=0.5,
        correctness=0.4,
        citation_quality=0.3,
        completeness=0.2,
    )
    assert evaluator._select_best_llm_configuration({"a": llm_result, "b": other_llm_result}) == "a"

    empty_evaluator = RAGEvaluator(dataset_loader=Loader())
    with pytest.raises(ValueError):
        empty_evaluator.evaluate_retrieval_strategies({})
    with pytest.raises(ValueError):
        evaluator.evaluate_llm_configurations({})
