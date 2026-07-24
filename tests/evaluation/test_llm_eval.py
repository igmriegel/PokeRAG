"""
TASK-035 — LLM output evaluation tests.
"""

from __future__ import annotations

import pytest

from pokemon_tcg_rag.domain.models import (
    Chunk,
    DocumentMetadata,
    DocumentSource,
    RetrievedChunk,
    RuleType,
)
from pokemon_tcg_rag.evaluation.dataset import EvalTestCase, EvaluationDatasetLoader
from pokemon_tcg_rag.evaluation.evaluator import LLMEvaluationSample, RAGEvaluator
from pokemon_tcg_rag.evaluation.metrics import calculate_faithfulness


def _case(question_id: str, question: str) -> EvalTestCase:
    return EvalTestCase(
        question_id=question_id,
        question=question,
        ground_truth_doc_ids=[f"doc-{question_id.lower()}"],
        expected_source=DocumentSource.RULEBOOK_PDF,
        reference_answer=f"Reference answer for {question_id}",
    )


def _chunk(doc_id: str, source: DocumentSource = DocumentSource.RULEBOOK_PDF) -> RetrievedChunk:
    metadata = DocumentMetadata(
        source=source,
        document_title="Official Rulebook",
        rule_type=RuleType.GENERAL_RULE,
    )
    chunk = Chunk(
        chunk_id=f"chunk-{doc_id}",
        doc_id=doc_id,
        text="Rare Candy can only be used when the rules permit it.",
        token_count=11,
        metadata=metadata,
    )
    return RetrievedChunk(chunk=chunk, score=0.9, retrieval_method="mock")


@pytest.mark.evaluation
def test_faithfulness_score_range() -> None:
    score = calculate_faithfulness(
        "Rare Candy can be used when rules permit it.", [_chunk("doc-q001")]
    )

    assert 0.0 <= score <= 1.0


@pytest.mark.evaluation
def test_prompt_ab_comparison(monkeypatch: pytest.MonkeyPatch) -> None:
    cases = [_case("Q001", "Question 1"), _case("Q002", "Question 2")]
    loader = EvaluationDatasetLoader()
    monkeypatch.setattr(loader, "load_dataset", lambda: cases)

    def prompt_a(case: EvalTestCase) -> LLMEvaluationSample:
        return LLMEvaluationSample(
            answer="Grounded answer.",
            citations=[_chunk(case.ground_truth_doc_ids[0]).chunk.metadata],
            retrieved_chunks=[_chunk(case.ground_truth_doc_ids[0])],
            reference_answer=case.reference_answer,
            faithfulness=0.96,
            correctness=0.95,
            citation_quality=1.0,
            completeness=0.94,
        )

    def prompt_b(case: EvalTestCase) -> LLMEvaluationSample:
        return LLMEvaluationSample(
            answer="Less grounded answer.",
            citations=[],
            retrieved_chunks=[],
            reference_answer=case.reference_answer,
            faithfulness=0.4,
            correctness=0.35,
            citation_quality=0.0,
            completeness=0.3,
        )

    evaluator = RAGEvaluator(
        dataset_loader=loader,
        llm_handlers={
            "prompt_a_gpt-4o-mini": prompt_a,
            "prompt_b_gpt-4o-mini": prompt_b,
        },
    )

    report = evaluator.evaluate_llm_configurations()

    assert set(report.llm_results) == {"prompt_a_gpt-4o-mini", "prompt_b_gpt-4o-mini"}
    assert report.best_llm_configuration == "prompt_a_gpt-4o-mini"
    assert (
        report.llm_results["prompt_a_gpt-4o-mini"].faithfulness
        > report.llm_results["prompt_b_gpt-4o-mini"].faithfulness
    )


@pytest.mark.evaluation
def test_model_comparison_records_best(monkeypatch: pytest.MonkeyPatch) -> None:
    cases = [_case("Q001", "Question 1"), _case("Q002", "Question 2")]
    loader = EvaluationDatasetLoader()
    monkeypatch.setattr(loader, "load_dataset", lambda: cases)

    def gpt_4o(case: EvalTestCase) -> LLMEvaluationSample:
        return LLMEvaluationSample(
            answer="Adequate answer.",
            citations=[_chunk(case.ground_truth_doc_ids[0]).chunk.metadata],
            retrieved_chunks=[_chunk(case.ground_truth_doc_ids[0])],
            reference_answer=case.reference_answer,
            faithfulness=0.8,
            correctness=0.78,
            citation_quality=0.95,
            completeness=0.79,
        )

    def gpt_41(case: EvalTestCase) -> LLMEvaluationSample:
        return LLMEvaluationSample(
            answer="Better answer.",
            citations=[_chunk(case.ground_truth_doc_ids[0]).chunk.metadata],
            retrieved_chunks=[_chunk(case.ground_truth_doc_ids[0])],
            reference_answer=case.reference_answer,
            faithfulness=0.92,
            correctness=0.9,
            citation_quality=1.0,
            completeness=0.91,
        )

    evaluator = RAGEvaluator(
        dataset_loader=loader,
        llm_handlers={
            "prompt_a_gpt-4o-mini": gpt_4o,
            "prompt_a_gpt-4.1-mini": gpt_41,
        },
    )

    report = evaluator.evaluate_llm_configurations()

    assert report.best_llm_configuration == "prompt_a_gpt-4.1-mini"
    assert (
        report.llm_results["prompt_a_gpt-4.1-mini"].correctness
        > report.llm_results["prompt_a_gpt-4o-mini"].correctness
    )
