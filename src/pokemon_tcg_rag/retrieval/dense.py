"""
Dense Vector Search Retriever.
"""

import logging
from sentence_transformers import SentenceTransformer

from pokemon_tcg_rag.config.settings import get_settings
from pokemon_tcg_rag.domain.models import RetrievedChunk
from pokemon_tcg_rag.storage.vector_db import VectorDatabase

logger = logging.getLogger(__name__)


class DenseRetriever:
    """Dense retriever utilizing sentence-transformers embedding model and Qdrant."""

    def __init__(self, vector_db: VectorDatabase) -> None:
        self.vector_db = vector_db
        settings = get_settings()
        self.model_name = settings.EMBEDDING_MODEL_PRIMARY
        # Lazy loading embedding model
        self._embedding_model = None

    @property
    def model(self) -> SentenceTransformer:
        if self._embedding_model is None:
            logger.info("Loading embedding model: %s", self.model_name)
            self._embedding_model = SentenceTransformer(self.model_name)
        return self._embedding_model

    def retrieve(self, query: str, top_k: int = 10) -> list[RetrievedChunk]:
        """Encode query into vector embedding and search vector database."""
        query_vector = self.model.encode(query).tolist()
        return self.vector_db.search_dense(query_vector=query_vector, top_k=top_k)
