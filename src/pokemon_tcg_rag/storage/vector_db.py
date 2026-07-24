"""
Qdrant Vector Database Integration Client.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from pokemon_tcg_rag.config.settings import get_settings
from pokemon_tcg_rag.domain.exceptions import VectorStoreError
from pokemon_tcg_rag.domain.models import (
    Chunk,
    DocumentMetadata,
    DocumentSource,
    RetrievedChunk,
    RuleType,
)


class VectorDatabase:
    """Qdrant vector-store wrapper for dense retrieval."""

    def __init__(self, client: QdrantClient | None = None) -> None:
        settings = get_settings()
        self.client = client or QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            grpc_port=settings.QDRANT_GRPC_PORT,
            api_key=settings.QDRANT_API_KEY or None,
        )
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.vector_dim = settings.EMBEDDING_DIMENSION

    def init_collection(self) -> None:
        """Create the target collection if it does not already exist."""
        try:
            if self.client.collection_exists(self.collection_name):
                return

            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=qmodels.VectorParams(
                    size=self.vector_dim,
                    distance=qmodels.Distance.COSINE,
                ),
            )
        except Exception as exc:  # pragma: no cover - defensive wrapper
            raise VectorStoreError(f"Failed to initialize Qdrant collection: {exc}") from exc

    def upsert_chunks(self, chunks: Sequence[Chunk]) -> None:
        """Upsert embedded chunks into Qdrant."""
        try:
            points: list[qmodels.PointStruct] = []
            for chunk in chunks:
                if not chunk.embedding:
                    continue
                points.append(
                    qmodels.PointStruct(
                        id=self._point_id(chunk.chunk_id),
                        vector=chunk.embedding,
                        payload=self._chunk_payload(chunk),
                    )
                )

            if points:
                self.client.upsert(collection_name=self.collection_name, points=points)
        except Exception as exc:  # pragma: no cover - defensive wrapper
            raise VectorStoreError(f"Failed to upsert Qdrant points: {exc}") from exc

    def search_dense(
        self,
        query_vector: Sequence[float],
        top_k: int = 10,
        filters: dict[str, str] | None = None,
    ) -> list[RetrievedChunk]:
        """Search dense vectors and map Qdrant hits back into domain chunks."""
        try:
            query_filter = self._build_filter(filters)
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=list(query_vector),
                query_filter=query_filter,
                limit=top_k,
                with_payload=True,
            )
            points = response.points if hasattr(response, "points") else []
            return [self._point_to_retrieved_chunk(point) for point in points]
        except Exception as exc:  # pragma: no cover - defensive wrapper
            raise VectorStoreError(f"Failed to search Qdrant: {exc}") from exc

    def _chunk_payload(self, chunk: Chunk) -> dict[str, Any]:
        return {
            "chunk_id": chunk.chunk_id,
            "text": chunk.text,
            "doc_id": chunk.doc_id,
            "source": chunk.metadata.source.value,
            "document_title": chunk.metadata.document_title,
            "page_number": chunk.metadata.page_number,
            "section_title": chunk.metadata.section_title,
            "card_name": chunk.metadata.card_name,
            "rule_type": chunk.metadata.rule_type.value,
            "publication_date": chunk.metadata.publication_date,
            "source_url": chunk.metadata.source_url,
            "checksum": chunk.metadata.checksum,
        }

    def _build_filter(self, filters: dict[str, str] | None) -> qmodels.Filter | None:
        if not filters:
            return None
        return qmodels.Filter(
            must=[
                qmodels.FieldCondition(
                    key=key,
                    match=qmodels.MatchValue(value=value),
                )
                for key, value in filters.items()
            ]
        )

    def _point_to_retrieved_chunk(self, point: Any) -> RetrievedChunk:
        payload = point.payload or {}
        metadata = DocumentMetadata(
            source=DocumentSource(payload["source"]),
            document_title=payload["document_title"],
            page_number=payload.get("page_number"),
            section_title=payload.get("section_title"),
            card_name=payload.get("card_name"),
            rule_type=RuleType(payload["rule_type"]),
            publication_date=payload.get("publication_date"),
            source_url=payload.get("source_url"),
            checksum=payload.get("checksum"),
        )
        chunk = Chunk(
            chunk_id=str(payload.get("chunk_id", point.id)),
            doc_id=payload.get("doc_id", str(point.id)),
            text=payload.get("text", ""),
            token_count=len(payload.get("text", "").split()),
            metadata=metadata,
        )
        return RetrievedChunk(chunk=chunk, score=float(point.score), retrieval_method="dense")

    def _point_id(self, chunk_id: str) -> str:
        return str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))
