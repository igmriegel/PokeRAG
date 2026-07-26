"""
TASK-034 — Retrieval strategy comparison evaluator tests.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from pokemon_tcg_rag.domain.models import (
    Chunk,
    DocumentMetadata,
    DocumentSource,
    RetrievedChunk,
    RuleType,
)
from pokemon_tcg_rag.evaluation.dataset import EvalTestCase, EvaluationDatasetLoader
from pokemon_tcg_rag.evaluation.evaluator import RAGEvaluator


def _case(
    question_id: str, question: str, doc_ids: list[str], source: DocumentSource
) -> EvalTestCase:
    return EvalTestCase(
        question_id=question_id,
        question=question,
        ground_truth_doc_ids=doc_ids,
        expected_source=source,
        reference_answer=f"Reference answer for {question_id}",
    )


def _chunk(
    doc_id: str, source: DocumentSource, page_number: int | None = None
) -> RetrievedChunk:
    chunk = Chunk(
        chunk_id=f"chunk-{doc_id}",
        doc_id=doc_id,
        text=f"content for {doc_id}",
        token_count=3,
        metadata=DocumentMetadata(
            source=source,
            document_title="Official Source",
            page_number=page_number,
            rule_type=RuleType.GENERAL_RULE,
        ),
    )
    return RetrievedChunk(chunk=chunk, score=1.0, retrieval_method="mock")


def _retrieval_handlers() -> (
    tuple[dict[str, Callable[[str, int], list[RetrievedChunk]]], dict[str, int]]
):
    calls = {"dense": 0, "bm25": 0, "hybrid": 0, "hybrid_rerank": 0}

    def dense(_: str, __: int) -> list[RetrievedChunk]:
        calls["dense"] += 1
        return [
            _chunk("doc_noise_1", DocumentSource.RULEBOOK_PDF),
            _chunk("doc_noise_2", DocumentSource.RULEBOOK_PDF),
            _chunk("doc_a", DocumentSource.RULEBOOK_PDF),
            _chunk("doc_b", DocumentSource.POKEGYM),
        ]

    def bm25(_: str, __: int) -> list[RetrievedChunk]:
        calls["bm25"] += 1
        return [
            _chunk("doc_noise_1", DocumentSource.POKEGYM),
            _chunk("doc_b", DocumentSource.POKEGYM),
            _chunk("doc_a", DocumentSource.RULEBOOK_PDF),
        ]

    def hybrid(_: str, __: int) -> list[RetrievedChunk]:
        calls["hybrid"] += 1
        return [
            _chunk("doc_noise_1", DocumentSource.RULEBOOK_PDF),
            _chunk("doc_a", DocumentSource.RULEBOOK_PDF),
            _chunk("doc_noise_2", DocumentSource.POKEGYM),
            _chunk("doc_b", DocumentSource.POKEGYM),
        ]

    def hybrid_rerank(_: str, __: int) -> list[RetrievedChunk]:
        calls["hybrid_rerank"] += 1
        return [
            _chunk("doc_a", DocumentSource.RULEBOOK_PDF),
            _chunk("doc_b", DocumentSource.POKEGYM),
            _chunk("doc_noise_1", DocumentSource.RULEBOOK_PDF),
        ]

    handlers = {
        "dense": dense,
        "bm25": bm25,
        "hybrid": hybrid,
        "hybrid_rerank": hybrid_rerank,
    }
    return handlers, calls


@pytest.mark.evaluation
def test_evaluates_all_four_strategies(monkeypatch: pytest.MonkeyPatch) -> None:
    cases = [
        _case("Q001", "Question 1", ["doc_a"], DocumentSource.RULEBOOK_PDF),
        _case("Q002", "Question 2", ["doc_b"], DocumentSource.POKEGYM),
    ]
    loader = EvaluationDatasetLoader()
    monkeypatch.setattr(loader, "load_dataset", lambda: cases)

    handlers, calls = _retrieval_handlers()
    evaluator = RAGEvaluator(dataset_loader=loader, retrieval_handlers=handlers)

    report = evaluator.evaluate_retrieval_strategies()

    assert set(report.retrieval_results) == {"dense", "bm25", "hybrid", "hybrid_rerank"}
    assert calls == {"dense": 2, "bm25": 2, "hybrid": 2, "hybrid_rerank": 2}


@pytest.mark.evaluation
def test_report_contains_metrics_per_strategy(monkeypatch: pytest.MonkeyPatch) -> None:
    cases = [
        _case("Q001", "Question 1", ["doc_a"], DocumentSource.RULEBOOK_PDF),
        _case("Q002", "Question 2", ["doc_b"], DocumentSource.POKEGYM),
    ]
    loader = EvaluationDatasetLoader()
    monkeypatch.setattr(loader, "load_dataset", lambda: cases)

    handlers, _ = _retrieval_handlers()
    evaluator = RAGEvaluator(dataset_loader=loader, retrieval_handlers=handlers)

    report = evaluator.evaluate_retrieval_strategies()

    assert report.retrieval_results["dense"].total_questions == 2
    assert report.retrieval_results["hybrid"].recall_at_5 == pytest.approx(1.0)
    assert report.retrieval_results["bm25"].hit_rate_at_10 == pytest.approx(1.0)


@pytest.mark.evaluation
def test_best_strategy_selected(monkeypatch: pytest.MonkeyPatch) -> None:
    cases = [
        _case("Q001", "Question 1", ["doc_a"], DocumentSource.RULEBOOK_PDF),
        _case("Q002", "Question 2", ["doc_b"], DocumentSource.POKEGYM),
    ]
    loader = EvaluationDatasetLoader()
    monkeypatch.setattr(loader, "load_dataset", lambda: cases)

    handlers, _ = _retrieval_handlers()
    evaluator = RAGEvaluator(dataset_loader=loader, retrieval_handlers=handlers)

    report = evaluator.evaluate_retrieval_strategies()

    assert report.best_retrieval_strategy == "hybrid_rerank"
