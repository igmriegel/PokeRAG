"""
Unified retrieval pipeline.
"""

from __future__ import annotations

from pokemon_tcg_rag.config.settings import get_settings
from pokemon_tcg_rag.domain.models import RetrievedChunk
from pokemon_tcg_rag.monitoring.tracing import traced_span
from pokemon_tcg_rag.retrieval.bm25 import BM25Retriever
from pokemon_tcg_rag.retrieval.cache import RetrievalCache
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
        self.cache = RetrievalCache(
            max_items=settings.RETRIEVAL_CACHE_MAX_ITEMS,
            ttl_seconds=settings.RETRIEVAL_CACHE_TTL_SECONDS,
        )
        self.enable_query_rewrite = enable_query_rewrite
        self.enable_reranking = enable_reranking

    def execute_retrieval(
        self,
        raw_query: str,
        top_k: int = 5,
        metadata_filters: dict[str, str] | None = None,
    ) -> tuple[str, list[RetrievedChunk]]:
        """Run query rewriting, hybrid retrieval, and reranking."""
        with traced_span(
            "retrieval.execute",
            attributes={
                "retrieval.enable_query_rewrite": self.enable_query_rewrite,
                "retrieval.enable_reranking": self.enable_reranking,
                "retrieval.top_k": top_k,
            },
        ):
            cache_key = self.cache.make_key(
                corpus_version=self.settings.CORPUS_VERSION,
                embedding_model=self.settings.EMBEDDING_MODEL_PRIMARY,
                reranker_model=self.settings.RERANKER_MODEL,
                rewrite_enabled=self.enable_query_rewrite,
                rerank_enabled=self.enable_reranking,
                top_k=top_k,
                raw_query=raw_query.strip().lower(),
                filters=metadata_filters or {},
            )
            cached = self.cache.get(cache_key)
            if cached is not None:
                return raw_query, cached
            rewritten_query = (
                self.query_rewriter.rewrite_query(raw_query)
                if self.enable_query_rewrite
                else raw_query
            )
            candidates = self._retrieve_candidates(
                rewritten_query,
                max(top_k, self.settings.RETRIEVAL_TOP_K_DENSE),
                metadata_filters,
            )

            if self.enable_reranking and candidates:
                final_chunks = self.reranker.rerank(
                    query=rewritten_query, candidate_chunks=candidates, top_k=top_k
                )
            else:
                final_chunks = candidates[:top_k]

            self.cache.set(cache_key, final_chunks)
            return rewritten_query, final_chunks

    def _retrieve_candidates(
        self,
        query: str,
        top_k: int,
        metadata_filters: dict[str, str] | None,
    ) -> list[RetrievedChunk]:
        """Call the hybrid retriever with compatibility for older fakes."""
        try:
            return self.hybrid_retriever.retrieve(
                query=query,
                top_k=top_k,
                filters=metadata_filters,
            )
        except TypeError as exc:
            if "unexpected keyword argument 'filters'" not in str(exc):
                raise
            return self.hybrid_retriever.retrieve(query=query, top_k=top_k)
