"""
Qdrant Vector Database Integration Client.
"""

import logging
from typing import Any
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from pokemon_tcg_rag.config.settings import get_settings
from pokemon_tcg_rag.domain.models import Chunk, RetrievedChunk

logger = logging.getLogger(__name__)


class VectorDatabase:
    """Qdrant Vector Store wrapper supporting dense vector search and payload filtering."""

    def __init__(self) -> None:
        settings = get_settings()
        self.client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            api_key=settings.QDRANT_API_KEY or None,
        )
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.vector_dim = settings.EMBEDDING_DIMENSION

    def init_collection(self) -> None:
        """Create collection if not exists with Cosine distance metric."""
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        if not exists:
            logger.info("Creating Qdrant collection: %s", self.collection_name)
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=qmodels.VectorParams(
                    size=self.vector_dim,
                    distance=qmodels.Distance.COSINE
                ),
            )

    def upsert_chunks(self, chunks: list[Chunk]) -> None:
        """Upsert embedded text chunks into Qdrant index."""
        points: list[qmodels.PointStruct] = []
        for chunk in chunks:
            if not chunk.embedding:
                continue
            point = qmodels.PointStruct(
                id=chunk.chunk_id,
                vector=chunk.embedding,
                payload={
                    "text": chunk.text,
                    "doc_id": chunk.doc_id,
                    "source": chunk.metadata.source.value,
                    "document_title": chunk.metadata.document_title,
                    "page_number": chunk.metadata.page_number,
                    "rule_type": chunk.metadata.rule_type.value,
                    "card_name": chunk.metadata.card_name,
                }
            )
            points.append(point)

        if points:
            self.client.upsert(collection_name=self.collection_name, points=points)
            logger.info("Upserted %d vector points to Qdrant", len(points))

    def search_dense(self, query_vector: list[float], top_k: int = 10) -> list[RetrievedChunk]:
        """Perform dense vector search in Qdrant."""
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
            )
            retrieved: list[RetrievedChunk] = []
            for res in results:
                # Reconstruct chunk domain model from payload
                payload = res.payload or {}
                chunk = Chunk(
                    chunk_id=str(res.id),
                    doc_id=payload.get("doc_id", ""),
                    text=payload.get("text", ""),
                    token_count=len(payload.get("text", "").split()),
                    metadata={
                        "source": payload.get("source"),
                        "document_title": payload.get("document_title"),
                        "page_number": payload.get("page_number"),
                        "rule_type": payload.get("rule_type"),
                        "card_name": payload.get("card_name"),
                    }
                )
                retrieved.append(RetrievedChunk(chunk=chunk, score=res.score, retrieval_method="dense"))
            return retrieved
        except Exception as exc:
            logger.error("Qdrant vector search error: %s", exc)
            return []
