"""
TASK-019 — TEST-061, TEST-062, TEST-063

Unit tests for the hybrid RRF retriever.
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
from pokemon_tcg_rag.retrieval.hybrid import HybridRetriever


def _make_retrieved(chunk_id: str, score: float, retrieval_method: str) -> RetrievedChunk:
    chunk = Chunk(
        chunk_id=chunk_id,
        doc_id=f"doc-{chunk_id}",
        text=f"text-{chunk_id}",
        token_count=1,
        metadata=DocumentMetadata(
            source=DocumentSource.RULEBOOK_PDF,
            document_title="Rulebook",
            rule_type=RuleType.GENERAL_RULE,
        ),
    )
    return RetrievedChunk(chunk=chunk, score=score, retrieval_method=retrieval_method)


class FakeDense:
    def __init__(self, results: list[RetrievedChunk]) -> None:
        self.results = results

    def retrieve(self, query: str, top_k: int = 10) -> list[RetrievedChunk]:
        return self.results[:top_k]


class FakeBM25:
    def __init__(self, results: list[RetrievedChunk]) -> None:
        self.results = results

    def retrieve(self, query: str, top_k: int = 10) -> list[RetrievedChunk]:
        return self.results[:top_k]


@pytest.mark.unit
def test_rrf_fusion_formula() -> None:
    """TEST-061: RRF score must follow 1 / (k + rank)."""
    dense = FakeDense([_make_retrieved("c1", 0.8, "dense"), _make_retrieved("c2", 0.7, "dense")])
    bm25 = FakeBM25([_make_retrieved("c2", 2.0, "bm25"), _make_retrieved("c1", 1.0, "bm25")])
    retriever = HybridRetriever(dense, bm25, rrf_k=60)

    results = retriever.retrieve("Rare Candy", top_k=2)

    expected_c1 = 1 / 61 + 1 / 62
    expected_c2 = 1 / 62 + 1 / 61
    assert results[0].score == pytest.approx(max(expected_c1, expected_c2))
    assert {item.chunk.chunk_id for item in results} == {"c1", "c2"}


@pytest.mark.unit
def test_dedup_across_retrievers() -> None:
    """TEST-062: duplicate chunk ids must be deduplicated in the fused output."""
    dense = FakeDense([_make_retrieved("c1", 0.8, "dense")])
    bm25 = FakeBM25([_make_retrieved("c1", 2.0, "bm25")])
    retriever = HybridRetriever(dense, bm25, rrf_k=60)

    results = retriever.retrieve("Rare Candy", top_k=10)

    assert len(results) == 1
    assert results[0].chunk.chunk_id == "c1"
    assert results[0].score == pytest.approx((1 / 61) + (1 / 61))


@pytest.mark.unit
def test_hybrid_beats_single_on_fixture() -> None:
    """TEST-063: hybrid retrieval should keep the strongest merged candidate first."""
    dense = FakeDense([_make_retrieved("dense_best", 0.9, "dense"), _make_retrieved("shared", 0.8, "dense")])
    bm25 = FakeBM25([_make_retrieved("shared", 2.0, "bm25"), _make_retrieved("lexical_best", 1.0, "bm25")])
    retriever = HybridRetriever(dense, bm25, rrf_k=60)

    results = retriever.retrieve("Rare Candy", top_k=3)

    assert results[0].chunk.chunk_id == "shared"
