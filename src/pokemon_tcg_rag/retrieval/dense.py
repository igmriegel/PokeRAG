"""
Dense vector retriever.
"""

from __future__ import annotations

from collections.abc import Sequence

from sentence_transformers import SentenceTransformer

from pokemon_tcg_rag.config.settings import get_settings
from pokemon_tcg_rag.domain.exceptions import RetrievalError
from pokemon_tcg_rag.domain.models import RetrievedChunk
from pokemon_tcg_rag.monitoring.tracing import traced_span
from pokemon_tcg_rag.storage.vector_db import VectorDatabase


class DenseRetriever:
    """Dense retriever utilizing sentence-transformers embeddings and Qdrant."""

    def __init__(self, vector_db: VectorDatabase) -> None:
        self.vector_db = vector_db
        settings = get_settings()
        self.model_name = settings.EMBEDDING_MODEL_PRIMARY
        self.default_top_k = settings.RETRIEVAL_TOP_K_DENSE
        self._embedding_model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        if self._embedding_model is None:
            self._embedding_model = SentenceTransformer(self.model_name)
        return self._embedding_model

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        filters: dict[str, str] | None = None,
    ) -> list[RetrievedChunk]:
        """Encode a query into an embedding and search the vector database."""
        limit = top_k or self.default_top_k
        try:
            with traced_span(
                "retrieval.dense",
                attributes={"retrieval.top_k": limit, "query.length": len(query.strip())},
            ):
                query_vector = self._encode_query(query)
                results = self.vector_db.search_dense(
                    query_vector=query_vector,
                    top_k=limit,
                    filters=filters,
                )
        except Exception as exc:  # pragma: no cover - defensive wrapper
            raise RetrievalError(f"Dense retrieval failed: {exc}") from exc
        return sorted(results, key=lambda item: item.score, reverse=True)[:limit]

    def _encode_query(self, query: str) -> list[float]:
        vector = self.model.encode(query, convert_to_numpy=True, normalize_embeddings=True)
        if hasattr(vector, "tolist"):
            query_vector = vector.tolist()
        elif isinstance(vector, Sequence):
            query_vector = list(vector)
        else:  # pragma: no cover - safety for unexpected encoders
            query_vector = [float(value) for value in vector]

        if len(query_vector) != get_settings().EMBEDDING_DIMENSION:
            raise RetrievalError(
                f"Query embedding dimension mismatch: expected {get_settings().EMBEDDING_DIMENSION}, "
                f"got {len(query_vector)}"
            )
        return [float(value) for value in query_vector]
