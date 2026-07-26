"""
TASK-091 — Evaluation stack coverage tests.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pokemon_tcg_rag.domain.models import (
    Chunk,
    DocumentMetadata,
    DocumentSource,
    RetrievedChunk,
    RuleType,
)
from pokemon_tcg_rag.evaluation.dataset import (
    EXPECTED_CASE_COUNT,
    EvalTestCase,
    EvaluationDatasetLoader,
)
from pokemon_tcg_rag.evaluation.evaluator import (
    EvaluationReport,
    LLMConfigurationResult,
    LLMEvaluationSample,
    RAGEvaluator,
    RetrievalStrategyResult,
)
from pokemon_tcg_rag.evaluation.factories import build_production_retrieval_handlers
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


def _retrieved(
    doc_id: str,
    *,
    source: DocumentSource = DocumentSource.RULEBOOK_PDF,
    page_number: int | None = 12,
    text: str = "Rare Candy allows evolution.",
) -> RetrievedChunk:
    chunk = Chunk(
        chunk_id=f"chunk-{doc_id}",
        doc_id=doc_id,
        text=text,
        token_count=len(text.split()),
        metadata=DocumentMetadata(
            source=source,
            document_title="Official Rulebook",
            page_number=page_number,
            rule_type=RuleType.GENERAL_RULE,
            source_url="https://example.com/rulebook.pdf",
        ),
    )
    return RetrievedChunk(chunk=chunk, score=0.9, retrieval_method="mock")


def _cases() -> list[EvalTestCase]:
    return [
        EvalTestCase(
            question_id="Q001",
            question="Question 1",
            ground_truth_doc_ids=["doc-a"],
            expected_source=DocumentSource.RULEBOOK_PDF,
            reference_answer="Reference answer 1",
        ),
        EvalTestCase(
            question_id="Q002",
            question="Question 2",
            ground_truth_doc_ids=["doc-b"],
            expected_source=DocumentSource.POKEGYM,
            reference_answer="Reference answer 2",
        ),
    ]


@pytest.mark.unit
def test_eval_case_validation_and_metric_helpers() -> None:
    case = EvalTestCase(
        question_id="Q001",
        question="  Can Rare Candy evolve?  ",
        ground_truth_doc_ids=[" doc-a ", "doc-b"],
        expected_source=DocumentSource.RULEBOOK_PDF,
        reference_answer="Rare Candy can evolve.",
    )

    retrieved = [_retrieved("doc-a"), _retrieved("doc-z", page_number=13)]
    citations = [retrieved[0].chunk.metadata]

    assert case.question == "Can Rare Candy evolve?"
    assert case.expected_doc_ids == ["doc-a", "doc-b"]
    assert calculate_recall_at_k(retrieved, case.ground_truth_doc_ids, k=1) == 0.5
    assert calculate_mrr(retrieved, case.ground_truth_doc_ids) == 1.0
    assert calculate_hit_rate(retrieved, case.ground_truth_doc_ids, k=2) == 1.0
    assert calculate_faithfulness("Rare Candy can evolve", retrieved) > 0.0
    assert calculate_correctness("Rare Candy can evolve", case.reference_answer) > 0.0
    assert calculate_citation_quality(citations, retrieved) == 1.0
    assert calculate_completeness("Rare Candy can evolve", case.reference_answer) > 0.0
    assert combine_scores([0.25, 0.5, float("nan"), 1.4]) == pytest.approx(0.5833)


@pytest.mark.unit
def test_dataset_loader_supports_legacy_payloads(tmp_path: Path) -> None:
    cases: list[dict[str, object]] = []
    for index in range(1, EXPECTED_CASE_COUNT + 1):
        cases.append(
            {
                "question_id": f"Q{index:03d}",
                "question": f"Question {index}",
                "expected_doc_ids": [f"doc-{index}"],
                "expected_source": "rulebook_pdf",
                "expected_answer_keywords": ["Rare Candy", "evolve"],
            }
        )

    dataset_path = tmp_path / "benchmark.json"
    dataset_path.write_text(json.dumps({"cases": cases}), encoding="utf-8")

    loader = EvaluationDatasetLoader(dataset_path)
    loaded = loader.load_dataset()

    assert len(loaded) == EXPECTED_CASE_COUNT
    assert loaded[0].ground_truth_doc_ids == ["doc-1"]
    assert loaded[0].reference_answer == "Rare Candy; evolve"


@pytest.mark.unit
def test_dataset_loader_rejects_invalid_payloads(tmp_path: Path) -> None:
    loader = EvaluationDatasetLoader(tmp_path / "missing.json")

    with pytest.raises(FileNotFoundError):
        loader.load_dataset()

    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text(json.dumps({"cases": [1, 2, 3]}), encoding="utf-8")
    with pytest.raises(ValueError, match="must be an object"):
        EvaluationDatasetLoader(invalid_path).load_dataset()

    short_path = tmp_path / "short.json"
    short_path.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "question_id": "Q001",
                        "question": "Q1",
                        "ground_truth_doc_ids": ["doc-a"],
                        "expected_source": "rulebook_pdf",
                        "reference_answer": "Answer 1",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="exactly"):
        EvaluationDatasetLoader(short_path).load_dataset()


@pytest.mark.unit
def test_evaluator_runs_retrieval_and_llm_comparisons(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cases = _cases()
    loader = EvaluationDatasetLoader()
    monkeypatch.setattr(loader, "load_dataset", lambda: cases)

    retrieval_calls: dict[str, int] = {"dense": 0, "bm25": 0}
    llm_calls: dict[str, int] = {"prompt_a": 0, "prompt_b": 0}

    def dense(_: str, __: int) -> list[RetrievedChunk]:
        retrieval_calls["dense"] += 1
        return [_retrieved("doc-a"), _retrieved("doc-noise")]

    def bm25(_: str, __: int) -> list[RetrievedChunk]:
        retrieval_calls["bm25"] += 1
        return [_retrieved("doc-b"), _retrieved("doc-noise")]

    def prompt_a(case: EvalTestCase) -> LLMEvaluationSample:
        llm_calls["prompt_a"] += 1
        chunk = _retrieved(case.ground_truth_doc_ids[0])
        return LLMEvaluationSample(
            answer="Grounded answer.",
            citations=[chunk.chunk.metadata],
            retrieved_chunks=[chunk],
            reference_answer=case.reference_answer,
            faithfulness=0.96,
            correctness=0.94,
            citation_quality=1.0,
            completeness=0.93,
        )

    def prompt_b(case: EvalTestCase) -> LLMEvaluationSample:
        llm_calls["prompt_b"] += 1
        return LLMEvaluationSample(
            answer="Weak answer.",
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
        retrieval_handlers={"dense": dense, "bm25": bm25},
        llm_handlers={"prompt_a": prompt_a, "prompt_b": prompt_b},
    )

    retrieval_report = evaluator.evaluate_retrieval_strategies()
    llm_report = evaluator.evaluate_llm_configurations()
    combined = EvaluationReport(
        total_questions=max(
            retrieval_report.total_questions, llm_report.total_questions
        ),
        retrieval_results=retrieval_report.retrieval_results,
        llm_results=llm_report.llm_results,
        best_retrieval_strategy=retrieval_report.best_retrieval_strategy,
        best_llm_configuration=llm_report.best_llm_configuration,
    )

    assert retrieval_calls == {"dense": 2, "bm25": 2}
    assert llm_calls == {"prompt_a": 2, "prompt_b": 2}
    assert retrieval_report.best_retrieval_strategy in {"dense", "bm25"}
    assert llm_report.best_llm_configuration == "prompt_a"
    assert "## Retrieval strategies" in combined.to_markdown()
    assert "## LLM configurations" in combined.to_markdown()
    assert json.loads(combined.to_json())["total_questions"] == 2


@pytest.mark.unit
def test_factory_handlers_delegate_to_dependencies() -> None:
    class FakeDense:
        def __init__(self) -> None:
            self.calls: list[tuple[str, int]] = []

        def retrieve(self, query: str, top_k: int = 10) -> list[RetrievedChunk]:
            self.calls.append((query, top_k))
            return [_retrieved("doc-a")]

    class FakeBM25:
        def __init__(self) -> None:
            self.calls: list[tuple[str, int]] = []

        def retrieve(self, query: str, top_k: int = 10) -> list[RetrievedChunk]:
            self.calls.append((query, top_k))
            return [_retrieved("doc-b")]

    class FakePipeline:
        def __init__(self) -> None:
            self.calls: list[tuple[str, int]] = []

        def execute_retrieval(
            self, raw_query: str, top_k: int = 10
        ) -> tuple[str, list[RetrievedChunk]]:
            self.calls.append((raw_query, top_k))
            return "rewritten", [_retrieved("doc-a"), _retrieved("doc-b")]

    class FakeHybridRetriever:
        def __init__(self, bm25_retriever: FakeBM25) -> None:
            self.bm25_retriever = bm25_retriever
            self.calls: list[tuple[str, int]] = []

        def retrieve(self, query: str, top_k: int = 10) -> list[RetrievedChunk]:
            self.calls.append((query, top_k))
            return [_retrieved("doc-a"), _retrieved("doc-b")]

    dense = FakeDense()
    bm25 = FakeBM25()
    pipeline = FakePipeline()
    hybrid = FakeHybridRetriever(bm25)
    handlers = build_production_retrieval_handlers(dense, hybrid, pipeline)

    assert set(handlers) == {"dense", "bm25", "hybrid", "hybrid_rerank"}
    assert handlers["dense"]("Rare Candy", 3)[0].chunk.doc_id == "doc-a"
    assert handlers["bm25"]("Rare Candy", 4)[0].chunk.doc_id == "doc-b"
    assert handlers["hybrid"]("Rare Candy", 5)[0].chunk.doc_id == "doc-a"
    assert handlers["hybrid_rerank"]("Rare Candy", 6)[1].chunk.doc_id == "doc-b"
    assert dense.calls == [("Rare Candy", 3)]
    assert bm25.calls == [("Rare Candy", 4)]
    assert hybrid.calls == [("Rare Candy", 5)]
    assert pipeline.calls == [("Rare Candy", 6)]
