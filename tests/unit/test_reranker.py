"""
TASK-020 — TEST-064, TEST-065, TEST-066

Unit tests for the BGE reranker.
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
from pokemon_tcg_rag.retrieval.reranker import BGEReranker


class FakeCrossEncoder:
    def __init__(self, *args, **kwargs) -> None:
        self.calls = []

    def predict(self, inputs, **kwargs):
        self.calls.append((inputs, kwargs))
        return [0.2, 0.9, 0.5]


def _make_candidate(chunk_id: str, text: str) -> RetrievedChunk:
    chunk = Chunk(
        chunk_id=chunk_id,
        doc_id=f"doc-{chunk_id}",
        text=text,
        token_count=len(text.split()),
        metadata=DocumentMetadata(
            source=DocumentSource.RULEBOOK_PDF,
            document_title="Rulebook",
            rule_type=RuleType.GENERAL_RULE,
        ),
    )
    return RetrievedChunk(chunk=chunk, score=0.1, retrieval_method="hybrid_rrf")


@pytest.mark.unit
def test_rerank_returns_top_k(monkeypatch: pytest.MonkeyPatch) -> None:
    """TEST-064: reranker must return the requested number of candidates."""
    monkeypatch.setattr("pokemon_tcg_rag.retrieval.reranker.CrossEncoder", lambda *args, **kwargs: FakeCrossEncoder())
    reranker = BGEReranker()

    output = reranker.rerank("Rare Candy", [_make_candidate("c1", "a"), _make_candidate("c2", "b"), _make_candidate("c3", "c")], top_k=2)

    assert len(output) == 2


@pytest.mark.unit
def test_rerank_reorders_by_score(monkeypatch: pytest.MonkeyPatch) -> None:
    """TEST-065: reranker must sort candidates by cross-encoder score."""
    monkeypatch.setattr("pokemon_tcg_rag.retrieval.reranker.CrossEncoder", lambda *args, **kwargs: FakeCrossEncoder())
    reranker = BGEReranker()

    output = reranker.rerank("Rare Candy", [_make_candidate("c1", "a"), _make_candidate("c2", "b"), _make_candidate("c3", "c")], top_k=3)

    assert [item.chunk.chunk_id for item in output] == ["c2", "c3", "c1"]


@pytest.mark.unit
def test_fewer_candidates_than_k(monkeypatch: pytest.MonkeyPatch) -> None:
    """TEST-066: fewer candidates than requested should return all of them."""
    monkeypatch.setattr("pokemon_tcg_rag.retrieval.reranker.CrossEncoder", lambda *args, **kwargs: FakeCrossEncoder())
    reranker = BGEReranker()

    output = reranker.rerank("Rare Candy", [_make_candidate("c1", "a")], top_k=5)

    assert len(output) == 1
