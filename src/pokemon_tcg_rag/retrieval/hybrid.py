"""
Hybrid search retriever combining dense and BM25 rankings with Reciprocal Rank Fusion.
"""

from __future__ import annotations

from pokemon_tcg_rag.config.settings import get_settings
from pokemon_tcg_rag.domain.models import RetrievedChunk
from pokemon_tcg_rag.retrieval.bm25 import BM25Retriever
from pokemon_tcg_rag.retrieval.dense import DenseRetriever
from pokemon_tcg_rag.retrieval.policy import (
    apply_mmr,
    matches_metadata_filters,
    normalize_metadata_filters,
)


class HybridRetriever:
    """Combine dense and lexical retrieval using RRF."""

    def __init__(
        self,
        dense_retriever: DenseRetriever,
        bm25_retriever: BM25Retriever,
        rrf_k: int | None = None,
    ) -> None:
        settings = get_settings()
        self.dense_retriever = dense_retriever
        self.bm25_retriever = bm25_retriever
        self.rrf_k = rrf_k if rrf_k is not None else settings.RETRIEVAL_HYBRID_RRF_K

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        filters: dict[str, str] | None = None,
    ) -> list[RetrievedChunk]:
        """Retrieve via both strategies and fuse rankings with RRF."""
        normalized_filters = normalize_metadata_filters(filters)
        dense_results = self._retrieve_dense(query, top_k, normalized_filters)
        bm25_results = self.bm25_retriever.retrieve(query=query, top_k=top_k)

        fused_scores: dict[str, float] = {}
        chunk_map: dict[str, RetrievedChunk] = {}

        for rank, result in enumerate(dense_results, start=1):
            chunk_id = result.chunk.chunk_id
            fused_scores[chunk_id] = fused_scores.get(chunk_id, 0.0) + self._rrf_score(rank)
            chunk_map[chunk_id] = result

        for rank, result in enumerate(bm25_results, start=1):
            chunk_id = result.chunk.chunk_id
            fused_scores[chunk_id] = fused_scores.get(chunk_id, 0.0) + self._rrf_score(rank)
            chunk_map.setdefault(chunk_id, result)

        ordered_ids = sorted(
            fused_scores, key=lambda chunk_id: fused_scores[chunk_id], reverse=True
        )[:top_k]
        fused_results = [
            RetrievedChunk(
                chunk=chunk_map[chunk_id].chunk,
                score=fused_scores[chunk_id],
                retrieval_method="hybrid_rrf",
            )
            for chunk_id in ordered_ids
        ]
        filtered_results = [
            result
            for result in fused_results
            if matches_metadata_filters(result, normalized_filters)
        ]
        return apply_mmr(filtered_results, top_k=top_k, lambda_mult=0.5)

    def _rrf_score(self, rank: int) -> float:
        return 1.0 / (self.rrf_k + rank)

    def _retrieve_dense(
        self,
        query: str,
        top_k: int,
        filters: dict[str, str] | None,
    ) -> list[RetrievedChunk]:
        """Call dense retrieval with compatibility for older fakes."""
        try:
            return self.dense_retriever.retrieve(query=query, top_k=top_k, filters=filters or None)
        except TypeError as exc:
            if "unexpected keyword argument 'filters'" not in str(exc):
                raise
            return self.dense_retriever.retrieve(query=query, top_k=top_k)
