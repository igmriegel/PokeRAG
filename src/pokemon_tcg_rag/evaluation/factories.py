"""
Production evaluation factories.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from pokemon_tcg_rag.domain.models import RetrievedChunk
from pokemon_tcg_rag.retrieval.dense import DenseRetriever
from pokemon_tcg_rag.retrieval.hybrid import HybridRetriever
from pokemon_tcg_rag.retrieval.pipeline import RetrievalPipeline


class SupportsRetrieval(Protocol):
    def retrieve(self, query: str, top_k: int = 10) -> list[RetrievedChunk]: ...


RetrievalHandler = Callable[[str, int], list[RetrievedChunk]]


def build_production_retrieval_handlers(
    dense_retriever: DenseRetriever,
    hybrid_retriever: HybridRetriever,
    retrieval_pipeline: RetrievalPipeline,
) -> dict[str, RetrievalHandler]:
    """Return real retrieval handlers derived from the production stack."""

    def dense(query: str, top_k: int) -> list[RetrievedChunk]:
        return dense_retriever.retrieve(query=query, top_k=top_k)

    def bm25(query: str, top_k: int) -> list[RetrievedChunk]:
        return hybrid_retriever.bm25_retriever.retrieve(query=query, top_k=top_k)

    def hybrid(query: str, top_k: int) -> list[RetrievedChunk]:
        return hybrid_retriever.retrieve(query=query, top_k=top_k)

    def hybrid_rerank(query: str, top_k: int) -> list[RetrievedChunk]:
        _, chunks = retrieval_pipeline.execute_retrieval(raw_query=query, top_k=top_k)
        return chunks

    return {
        "dense": dense,
        "bm25": bm25,
        "hybrid": hybrid,
        "hybrid_rerank": hybrid_rerank,
    }
