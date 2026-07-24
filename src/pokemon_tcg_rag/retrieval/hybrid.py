"""
Hybrid Search Retriever combining Dense Vector and BM25 Lexical search via Reciprocal Rank Fusion (RRF).
"""

import logging
from pokemon_tcg_rag.domain.models import RetrievedChunk
from pokemon_tcg_rag.retrieval.bm25 import BM25Retriever
from pokemon_tcg_rag.retrieval.dense import DenseRetriever

logger = logging.getLogger(__name__)


class HybridRetriever:
    """Hybrid Search Coordinator combining Dense vector search and BM25 lexical search with RRF."""

    def __init__(self, dense_retriever: DenseRetriever, bm25_retriever: BM25Retriever, rrf_k: int = 60) -> None:
        self.dense_retriever = dense_retriever
        self.bm25_retriever = bm25_retriever
        self.rrf_k = rrf_k

    def retrieve(self, query: str, top_k: int = 10) -> list[RetrievedChunk]:
        """Execute hybrid search using Reciprocal Rank Fusion (RRF)."""
        dense_results = self.dense_retriever.retrieve(query=query, top_k=top_k * 2)
        bm25_results = self.bm25_retriever.retrieve(query=query, top_k=top_k * 2)

        # RRF Fusion Score Calculation: RRF_score = sum(1 / (k + rank))
        rrf_scores: dict[str, float] = {}
        chunk_map: dict[str, RetrievedChunk] = {}

        # 1. Rank dense results
        for rank, res in enumerate(dense_results, start=1):
            cid = res.chunk.chunk_id
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank))
            chunk_map[cid] = res

        # 2. Rank BM25 results
        for rank, res in enumerate(bm25_results, start=1):
            cid = res.chunk.chunk_id
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank))
            if cid not in chunk_map:
                chunk_map[cid] = res

        # Sort combined results by RRF score
        sorted_chunk_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)[:top_k]

        hybrid_results: list[RetrievedChunk] = []
        for cid in sorted_chunk_ids:
            base_item = chunk_map[cid]
            hybrid_results.append(
                RetrievedChunk(
                    chunk=base_item.chunk,
                    score=rrf_scores[cid],
                    retrieval_method="hybrid_rrf"
                )
            )

        return hybrid_results
