"""
TASK-017 — TEST-055, TEST-056, TEST-057

Unit tests for the dense retriever.
"""

from __future__ import annotations

import numpy as np
import pytest

from pokemon_tcg_rag.domain.models import (
    Chunk,
    DocumentMetadata,
    DocumentSource,
    RetrievedChunk,
    RuleType,
)
from pokemon_tcg_rag.retrieval.dense import DenseRetriever


class FakeModel:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def encode(self, inputs, **kwargs):
        self.calls.append((inputs, kwargs))
        return np.array([0.1] * 1024, dtype=float)


class FakeVectorDB:
    def __init__(self, results: list[RetrievedChunk]) -> None:
        self.results = results
        self.calls: list[tuple] = []

    def search_dense(self, query_vector, top_k):
        self.calls.append((query_vector, top_k))
        return self.results


def _make_retrieved(chunk_id: str, score: float) -> RetrievedChunk:
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
    return RetrievedChunk(chunk=chunk, score=score, retrieval_method="dense")


@pytest.mark.unit
def test_dense_returns_top_k(monkeypatch: pytest.MonkeyPatch) -> None:
    """TEST-055: dense retriever must return only the requested top_k results."""
    fake_model = FakeModel()
    monkeypatch.setattr(
        "pokemon_tcg_rag.retrieval.dense.SentenceTransformer", lambda *args, **kwargs: fake_model
    )

    results = [_make_retrieved("c1", 0.1), _make_retrieved("c2", 0.9)]
    db = FakeVectorDB(results)
    retriever = DenseRetriever(db)

    output = retriever.retrieve("Rare Candy", top_k=1)

    assert len(output) == 1
    assert output[0].chunk.chunk_id == "c2"
    assert db.calls[0][1] == 1


@pytest.mark.unit
def test_query_encoded_to_1024(monkeypatch: pytest.MonkeyPatch) -> None:
    """TEST-056: the query embedding must be 1024-dimensional."""
    fake_model = FakeModel()
    monkeypatch.setattr(
        "pokemon_tcg_rag.retrieval.dense.SentenceTransformer", lambda *args, **kwargs: fake_model
    )

    db = FakeVectorDB([_make_retrieved("c1", 0.5)])
    retriever = DenseRetriever(db)

    retriever.retrieve("Rare Candy", top_k=1)

    query_vector = db.calls[0][0]
    assert len(query_vector) == 1024


@pytest.mark.unit
def test_results_ordered_by_score(monkeypatch: pytest.MonkeyPatch) -> None:
    """TEST-057: results must be sorted by descending score."""
    fake_model = FakeModel()
    monkeypatch.setattr(
        "pokemon_tcg_rag.retrieval.dense.SentenceTransformer", lambda *args, **kwargs: fake_model
    )

    results = [_make_retrieved("c1", 0.1), _make_retrieved("c2", 0.9), _make_retrieved("c3", 0.5)]
    db = FakeVectorDB(results)
    retriever = DenseRetriever(db)

    output = retriever.retrieve("query", top_k=3)

    assert [item.chunk.chunk_id for item in output] == ["c2", "c3", "c1"]
