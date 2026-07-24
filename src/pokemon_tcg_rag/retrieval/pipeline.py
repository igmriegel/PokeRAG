"""
Unified Retrieval Pipeline executing Query Rewriting -> Hybrid Search -> Cross-Encoder Re-ranking.
"""

import logging
from pokemon_tcg_rag.config.settings import get_settings
from pokemon_tcg_rag.domain.models import RetrievedChunk
from pokemon_tcg_rag.retrieval.bm25 import BM25Retriever
from pokemon_tcg_rag.retrieval.dense import DenseRetriever
from pokemon_tcg_rag.retrieval.hybrid import HybridRetriever
from pokemon_tcg_rag.retrieval.query_rewriter import QueryRewriter
from pokemon_tcg_rag.retrieval.reranker import BGEReranker

logger = logging.getLogger(__name__)


class RetrievalPipeline:
    """Orchestrates end-to-end retrieval strategy: Query Rewrite -> Hybrid (Dense + BM25) -> Reranker."""

    def __init__(
        self,
        dense_retriever: DenseRetriever,
        bm25_retriever: BM25Retriever,
        enable_query_rewrite: bool = True,
        enable_reranking: bool = True,
    ) -> None:
        self.settings = get_settings()
        self.query_rewriter = QueryRewriter()
        self.hybrid_retriever = HybridRetriever(
            dense_retriever=dense_retriever,
            bm25_retriever=bm25_retriever,
            rrf_k=self.settings.RETRIEVAL_HYBRID_RRF_K
        )
        self.reranker = BGEReranker()
        self.enable_query_rewrite = enable_query_rewrite
        self.enable_reranking = enable_reranking

    def execute_retrieval(self, raw_query: str, top_k: int = 5) -> tuple[str, list[RetrievedChunk]]:
        """Run full multi-stage retrieval pipeline."""
        # Step 1: Query Rewriting
        if self.enable_query_rewrite:
            query = self.query_rewriter.rewrite_query(raw_query)
        else:
            query = raw_query

        # Step 2: Hybrid Search (Dense + BM25)
        candidates = self.hybrid_retriever.retrieve(query=query, top_k=self.settings.RETRIEVAL_TOP_K_DENSE)

        # Step 3: Cross-Encoder Re-ranking
        if self.enable_reranking and candidates:
            final_chunks = self.reranker.rerank(query=query, candidate_chunks=candidates, top_k=top_k)
        else:
            final_chunks = candidates[:top_k]

        return query, final_chunks
