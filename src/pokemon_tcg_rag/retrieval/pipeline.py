"""
Unified retrieval pipeline.
"""

from __future__ import annotations

from pokemon_tcg_rag.config.settings import get_settings
from pokemon_tcg_rag.domain.models import RetrievedChunk
from pokemon_tcg_rag.retrieval.bm25 import BM25Retriever
from pokemon_tcg_rag.retrieval.dense import DenseRetriever
from pokemon_tcg_rag.retrieval.hybrid import HybridRetriever
from pokemon_tcg_rag.retrieval.query_rewriter import QueryRewriter
from pokemon_tcg_rag.retrieval.reranker import BGEReranker


class RetrievalPipeline:
    """Orchestrate query rewriting, hybrid retrieval, and reranking."""

    def __init__(
        self,
        dense_retriever: DenseRetriever,
        bm25_retriever: BM25Retriever,
        query_rewriter: QueryRewriter | None = None,
        hybrid_retriever: HybridRetriever | None = None,
        reranker: BGEReranker | None = None,
        enable_query_rewrite: bool = True,
        enable_reranking: bool = True,
    ) -> None:
        settings = get_settings()
        self.settings = settings
        self.query_rewriter = query_rewriter or QueryRewriter()
        self.hybrid_retriever = hybrid_retriever or HybridRetriever(
            dense_retriever=dense_retriever,
            bm25_retriever=bm25_retriever,
            rrf_k=settings.RETRIEVAL_HYBRID_RRF_K,
        )
        self.reranker = reranker or BGEReranker()
        self.enable_query_rewrite = enable_query_rewrite
        self.enable_reranking = enable_reranking

    def execute_retrieval(self, raw_query: str, top_k: int = 5) -> tuple[str, list[RetrievedChunk]]:
        """Run query rewriting, hybrid retrieval, and reranking."""
        rewritten_query = (
            self.query_rewriter.rewrite_query(raw_query) if self.enable_query_rewrite else raw_query
        )
        candidates = self.hybrid_retriever.retrieve(
            query=rewritten_query,
            top_k=max(top_k, self.settings.RETRIEVAL_TOP_K_DENSE),
        )

        if self.enable_reranking and candidates:
            final_chunks = self.reranker.rerank(
                query=rewritten_query, candidate_chunks=candidates, top_k=top_k
            )
        else:
            final_chunks = candidates[:top_k]

        return rewritten_query, final_chunks
