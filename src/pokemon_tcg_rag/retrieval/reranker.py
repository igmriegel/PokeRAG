"""
Document Re-ranking Module using BGE Cross-Encoder Reranker.
"""

import logging
from sentence_transformers import CrossEncoder

from pokemon_tcg_rag.config.settings import get_settings
from pokemon_tcg_rag.domain.models import RetrievedChunk

logger = logging.getLogger(__name__)


class BGEReranker:
    """Re-ranks retrieved candidate chunks using BGE Cross-Encoder for high semantic precision."""

    def __init__(self) -> None:
        settings = get_settings()
        self.model_name = settings.RERANKER_MODEL
        self._reranker_model = None

    @property
    def model(self) -> CrossEncoder:
        if self._reranker_model is None:
            logger.info("Loading Cross-Encoder reranker model: %s", self.model_name)
            self._reranker_model = CrossEncoder(self.model_name)
        return self._reranker_model

    def rerank(self, query: str, candidate_chunks: list[RetrievedChunk], top_k: int = 5) -> list[RetrievedChunk]:
        """Re-rank candidate chunks using query-document pairs."""
        if not candidate_chunks:
            return []

        pairs = [[query, item.chunk.text] for item in candidate_chunks]
        scores = self.model.predict(pairs)

        reranked: list[RetrievedChunk] = []
        for idx, score in enumerate(scores):
            original = candidate_chunks[idx]
            reranked.append(
                RetrievedChunk(
                    chunk=original.chunk,
                    score=float(score),
                    retrieval_method="bge_reranked"
                )
            )

        # Sort descending by cross-encoder relevance score
        reranked.sort(key=lambda x: x.score, reverse=True)
        return reranked[:top_k]
