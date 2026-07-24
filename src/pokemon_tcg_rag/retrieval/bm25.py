"""
BM25 keyword retriever.
"""

from __future__ import annotations

import re

from rank_bm25 import BM25Okapi

from pokemon_tcg_rag.domain.models import Chunk, RetrievedChunk
from pokemon_tcg_rag.monitoring.tracing import traced_span


class BM25Retriever:
    """Keyword-based lexical retriever powered by BM25Okapi."""

    def __init__(self, chunks: list[Chunk] | None = None) -> None:
        self.chunks: list[Chunk] = []
        self.bm25: BM25Okapi | None = None
        if chunks:
            self.index_chunks(chunks)

    def index_chunks(self, chunks: list[Chunk]) -> None:
        """Tokenize chunks and build a BM25 index."""
        self.chunks = list(chunks)
        if not chunks:
            self.bm25 = None
            return
        tokenized_corpus = [self._tokenize(chunk.text) for chunk in chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def retrieve(self, query: str, top_k: int = 10) -> list[RetrievedChunk]:
        """Return BM25-ranked chunks for the query."""
        if not query.strip() or not self.bm25 or not self.chunks:
            return []

        with traced_span(
            "retrieval.bm25",
            attributes={"retrieval.top_k": top_k, "query.length": len(query.strip())},
        ):
            scores = self.bm25.get_scores(self._tokenize(query))
            ranked_indices = sorted(
                range(len(scores)), key=lambda index: scores[index], reverse=True
            )
            results: list[RetrievedChunk] = []
            for index in ranked_indices[:top_k]:
                results.append(
                    RetrievedChunk(
                        chunk=self.chunks[index],
                        score=float(scores[index]),
                        retrieval_method="bm25",
                    )
                )
            return results

    def _tokenize(self, text: str) -> list[str]:
        tokens = re.findall(r"[A-Za-z0-9]+", text.lower())
        return tokens
