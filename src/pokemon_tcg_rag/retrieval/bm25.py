"""
BM25 Keyword Search Retriever.
"""

import logging
from rank_bm25 import BM25Okapi

from pokemon_tcg_rag.domain.models import Chunk, RetrievedChunk

logger = logging.getLogger(__name__)


class BM25Retriever:
    """Keyword-based lexical retriever powered by BM25Okapi algorithm."""

    def __init__(self, chunks: list[Chunk] | None = None) -> None:
        self.chunks: list[Chunk] = chunks or []
        self.bm25: BM25Okapi | None = None
        if self.chunks:
            self.index_chunks(self.chunks)

    def index_chunks(self, chunks: list[Chunk]) -> None:
        """Tokenize document chunks and build BM25 index."""
        self.chunks = chunks
        tokenized_corpus = [chunk.text.lower().split() for chunk in chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)
        logger.info("Indexed %d chunks in BM25 search engine", len(chunks))

    def retrieve(self, query: str, top_k: int = 10) -> list[RetrievedChunk]:
        """Perform lexical keyword search over indexed corpus."""
        if not self.bm25 or not self.chunks:
            logger.warning("BM25 index is empty. Returning 0 results.")
            return []

        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        
        # Sort indices by score descending
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        retrieved: list[RetrievedChunk] = []
        for idx in top_indices:
            if scores[idx] > 0:
                retrieved.append(
                    RetrievedChunk(
                        chunk=self.chunks[idx],
                        score=float(scores[idx]),
                        retrieval_method="bm25"
                    )
                )
        return retrieved
