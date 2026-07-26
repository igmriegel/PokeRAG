"""
TASK-023 — TEST-073, TEST-074, TEST-075

Integration tests for the retrieval pipeline orchestration.
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
from pokemon_tcg_rag.retrieval.pipeline import RetrievalPipeline


def _make_retrieved(
    chunk_id: str, score: float, retrieval_method: str
) -> RetrievedChunk:
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


class FakeQueryRewriter:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def rewrite_query(self, original_query: str) -> str:
        self.calls.append(original_query)
        return "rewritten query"


class FakeHybridRetriever:
    def __init__(self, candidates: list[RetrievedChunk]) -> None:
        self.calls: list[tuple[str, int]] = []
        self.candidates = candidates

    def retrieve(self, query: str, top_k: int = 10) -> list[RetrievedChunk]:
        self.calls.append((query, top_k))
        return self.candidates[:top_k]


class FakeReranker:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    def rerank(
        self, query: str, candidate_chunks: list[RetrievedChunk], top_k: int = 5
    ) -> list[RetrievedChunk]:
        self.calls.append((query, top_k))
        return sorted(candidate_chunks, key=lambda item: item.score, reverse=True)[
            :top_k
        ]


@pytest.mark.integration
def test_pipeline_chains_stages() -> None:
    """TEST-073: retrieval pipeline must chain rewrite -> hybrid -> rerank."""
    candidates = [
        _make_retrieved("c1", 0.1, "hybrid_rrf"),
        _make_retrieved("c2", 0.9, "hybrid_rrf"),
    ]
    query_rewriter = FakeQueryRewriter()
    hybrid = FakeHybridRetriever(candidates)
    reranker = FakeReranker()

    pipeline = RetrievalPipeline(
        dense_retriever=object(),  # type: ignore[arg-type]
        bm25_retriever=object(),  # type: ignore[arg-type]
        query_rewriter=query_rewriter,
        hybrid_retriever=hybrid,
        reranker=reranker,
    )

    rewritten, final_chunks = pipeline.execute_retrieval(
        "Can I use Rare Candy?", top_k=1
    )

    assert rewritten == "rewritten query"
    assert query_rewriter.calls == ["Can I use Rare Candy?"]
    assert hybrid.calls[0][0] == "rewritten query"
    assert reranker.calls[0][0] == "rewritten query"
    assert len(final_chunks) == 1


@pytest.mark.integration
def test_returns_rewritten_query() -> None:
    """TEST-074: pipeline must return the rewritten query string."""
    pipeline = RetrievalPipeline(
        dense_retriever=object(),  # type: ignore[arg-type]
        bm25_retriever=object(),  # type: ignore[arg-type]
        query_rewriter=FakeQueryRewriter(),
        hybrid_retriever=FakeHybridRetriever(
            [_make_retrieved("c1", 0.9, "hybrid_rrf")]
        ),
        reranker=FakeReranker(),
    )

    rewritten, _ = pipeline.execute_retrieval("Can I use Rare Candy?", top_k=1)

    assert rewritten == "rewritten query"


@pytest.mark.integration
def test_final_top_k_respected() -> None:
    """TEST-075: final returned chunk count must not exceed top_k."""
    pipeline = RetrievalPipeline(
        dense_retriever=object(),  # type: ignore[arg-type]
        bm25_retriever=object(),  # type: ignore[arg-type]
        query_rewriter=FakeQueryRewriter(),
        hybrid_retriever=FakeHybridRetriever(
            [
                _make_retrieved("c1", 0.1, "hybrid_rrf"),
                _make_retrieved("c2", 0.9, "hybrid_rrf"),
                _make_retrieved("c3", 0.5, "hybrid_rrf"),
            ]
        ),
        reranker=FakeReranker(),
    )

    _, final_chunks = pipeline.execute_retrieval("Can I use Rare Candy?", top_k=2)

    assert len(final_chunks) == 2
    assert [item.chunk.chunk_id for item in final_chunks] == ["c2", "c3"]
