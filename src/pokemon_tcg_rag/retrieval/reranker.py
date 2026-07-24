"""
Cross-encoder reranker.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, cast

from sentence_transformers import CrossEncoder

from pokemon_tcg_rag.config.settings import get_settings
from pokemon_tcg_rag.domain.models import RetrievedChunk
from pokemon_tcg_rag.monitoring.logger import get_logger
from pokemon_tcg_rag.monitoring.tracing import traced_span

LOGGER = get_logger(__name__)


class BGEReranker:
    """Re-rank candidate chunks using the BGE cross-encoder."""

    def __init__(self) -> None:
        settings = get_settings()
        self.model_name = settings.RERANKER_MODEL
        self.default_top_k = settings.RETRIEVAL_FINAL_TOP_K
        self._reranker_model: CrossEncoder | None = None
        self._disabled_reason: str | None = None

    @property
    def model(self) -> CrossEncoder:
        if self._reranker_model is None:
            try:
                self._reranker_model = CrossEncoder(self.model_name)
            except Exception as exc:  # pragma: no cover - defensive fallback
                self._disabled_reason = str(exc)
                LOGGER.warning(
                    "reranker_disabled", model=self.model_name, reason=self._disabled_reason
                )
                raise
        return self._reranker_model

    def rerank(
        self,
        query: str,
        candidate_chunks: Sequence[RetrievedChunk],
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        """Score candidate chunks with a cross-encoder and return the top results."""
        if not candidate_chunks:
            return []

        limit = top_k or self.default_top_k
        with traced_span(
            "retrieval.rerank",
            attributes={"retrieval.top_k": limit, "candidate_count": len(candidate_chunks)},
        ):
            if self._disabled_reason is not None:
                ordered = sorted(candidate_chunks, key=lambda item: item.score, reverse=True)
                return list(ordered[:limit])

            pairs = [(query, item.chunk.text) for item in candidate_chunks]
            try:
                scores = list(cast(Any, self.model.predict)(pairs, convert_to_numpy=True))
            except Exception:
                ordered = sorted(candidate_chunks, key=lambda item: item.score, reverse=True)
                return list(ordered[:limit])

            reranked = [
                RetrievedChunk(
                    chunk=item.chunk,
                    score=float(score),
                    retrieval_method="bge_reranked",
                )
                for item, score in zip(candidate_chunks, scores, strict=False)
            ]
            reranked.sort(key=lambda item: item.score, reverse=True)
            return reranked[:limit]
