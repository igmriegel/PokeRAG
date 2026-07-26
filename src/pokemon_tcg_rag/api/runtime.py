"""
Runtime composition helpers for the FastAPI application.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastapi import FastAPI

from pokemon_tcg_rag.api.routes import set_dependencies
from pokemon_tcg_rag.config.settings import Settings, get_settings
from pokemon_tcg_rag.domain.exceptions import ConfigurationError
from pokemon_tcg_rag.domain.models import Chunk, FeedbackRecord, RetrievedChunk
from pokemon_tcg_rag.llm.client import LLMClient, SupportsGeneration
from pokemon_tcg_rag.llm.rag_chain import RAGChain
from pokemon_tcg_rag.monitoring.feedback_store import FeedbackStore
from pokemon_tcg_rag.retrieval.bm25 import BM25Retriever
from pokemon_tcg_rag.retrieval.dense import DenseRetriever
from pokemon_tcg_rag.retrieval.pipeline import RetrievalPipeline
from pokemon_tcg_rag.retrieval.query_rewriter import QueryRewriter
from pokemon_tcg_rag.storage.indexing import load_chunks, load_corpus_manifest
from pokemon_tcg_rag.storage.relational_db import RelationalDatabase
from pokemon_tcg_rag.storage.vector_db import VectorDatabase


@dataclass(slots=True)
class RuntimeContainer:
    """Application runtime graph built during FastAPI startup."""

    settings: Settings
    vector_db: VectorDatabase
    relational_db: RelationalDatabase
    dense_retriever: DenseRetriever
    bm25_retriever: BM25Retriever
    retrieval_pipeline: RetrievalPipeline
    feedback_store: FeedbackStore
    rag_chain: RAGChain

    def close(self) -> None:
        """Release resources created for the runtime graph."""
        self.relational_db.engine.dispose()


class OfflineQueryRewriterClient:
    """Local fallback that preserves the original query during startup without OpenAI."""

    model_name = "offline-query-rewriter"

    def generate_answer(self, prompt: str) -> str:
        """Return the original question from the rewrite prompt."""
        marker = "Original question:"
        if marker not in prompt:
            return prompt.strip()
        original = prompt.split(marker, 1)[1].splitlines()[0].strip()
        return original or prompt.strip()


class OfflineAnswerClient:
    """Local fallback that summarizes retrieved context when OpenAI is unavailable."""

    model_name = "offline-llm"

    def generate_answer(self, prompt: str) -> str:
        """Return a short grounded answer derived from the retrieved context."""
        context = self._extract_context(prompt)
        if not context:
            return "I don't know."

        first_block = context.split("\n\n", 1)[0].strip()
        lines = [line.strip() for line in first_block.splitlines() if line.strip()]
        if len(lines) < 2:
            fallback = lines[0] if lines else "I don't know."
            return f"Com base no contexto recuperado: {fallback}"

        source_line = lines[0]
        text = " ".join(lines[1:]).strip()
        if "." in text:
            text = text.split(".", 1)[0].strip() + "."
        return f"Com base em {source_line}, {text}"

    def _extract_context(self, prompt: str) -> str:
        start_marker = "Contexto:"
        end_marker = "\n\nPergunta:"
        if start_marker not in prompt:
            return ""
        remainder = prompt.split(start_marker, 1)[1]
        if end_marker not in remainder:
            return remainder.strip()
        return remainder.split(end_marker, 1)[0].strip()


class OfflineVectorDatabase(VectorDatabase):
    """Local fallback vector store used when Qdrant is unavailable in development."""

    def __init__(self, collection_name: str) -> None:
        self.collection_name = collection_name

    def init_collection(self, metadata: dict[str, object] | None = None) -> None:
        """No-op for local degraded startup."""

    def search_dense(
        self,
        query_vector: Sequence[float],
        top_k: int = 10,
        filters: dict[str, str] | None = None,
    ) -> list[RetrievedChunk]:
        """Return no dense matches when the vector store is unavailable."""
        return []

    def upsert_chunks(self, chunks: Sequence[Chunk], batch_size: int = 64) -> None:
        """Ignore writes in degraded mode."""


class OfflineDenseRetriever(DenseRetriever):
    """Local fallback dense retriever that avoids model loading and returns no hits."""

    def __init__(self, vector_db: VectorDatabase) -> None:
        self.vector_db = vector_db
        self.model_name = "offline-dense-retriever"
        self.default_top_k = 10
        self._embedding_model = None

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        filters: dict[str, str] | None = None,
    ) -> list[RetrievedChunk]:
        """Return no dense matches when embeddings are unavailable locally."""
        return []


class OfflineFeedbackStore(FeedbackStore):
    """Local fallback feedback store that keeps submissions in memory."""

    def __init__(self) -> None:
        self.records: list[FeedbackRecord] = []

    def submit_feedback(
        self,
        query_id: str,
        query: str,
        answer: str,
        rating: int,
        comment: str | None,
        model_name: str,
        latency: float,
    ) -> FeedbackRecord:
        record = FeedbackRecord(
            feedback_id=f"fb_{uuid.uuid4().hex[:10]}",
            query_id=query_id,
            query=query,
            answer=answer,
            rating=rating,
            comment=comment,
            model_name=model_name,
            latency_seconds=latency,
        )
        self.records.append(record)
        return record

    def close(self) -> None:
        """No-op for in-memory storage."""
        return None


def build_runtime_container(settings: Settings | None = None) -> RuntimeContainer:
    """Build the real dependency graph used by the API and UI."""
    active_settings = settings or get_settings()
    relational_db = RelationalDatabase()

    manifest = load_corpus_manifest(active_settings.DATA_CHUNKS_DIR)
    chunks: list[Chunk] = load_chunks(active_settings.DATA_CHUNKS_DIR)
    if active_settings.ENVIRONMENT == "production" and manifest is None:
        raise ConfigurationError("Corpus manifest is required in production runtime startup")
    if active_settings.ENVIRONMENT == "production" and not chunks:
        raise ConfigurationError("Corpus chunks are required in production runtime startup")
    bm25_retriever = BM25Retriever(chunks)
    vector_db: VectorDatabase | OfflineVectorDatabase = VectorDatabase()
    dense_retriever: DenseRetriever | OfflineDenseRetriever = DenseRetriever(vector_db)

    query_rewriter_client: SupportsGeneration
    llm_client: SupportsGeneration
    openai_key = active_settings.OPENAI_API_KEY.strip()
    if openai_key:
        llm_client = LLMClient()
        query_rewriter_client = llm_client
    else:
        if active_settings.ENVIRONMENT == "production":
            raise ConfigurationError("OPENAI_API_KEY is required in production runtime startup")
        llm_client = OfflineAnswerClient()
        query_rewriter_client = OfflineQueryRewriterClient()

    try:
        vector_db.init_collection(metadata=manifest.to_collection_metadata() if manifest else None)
    except Exception as exc:
        if active_settings.ENVIRONMENT == "production":
            raise ConfigurationError(f"Qdrant initialization failed: {exc}") from exc
        vector_db = OfflineVectorDatabase(active_settings.QDRANT_COLLECTION_NAME)
        dense_retriever = OfflineDenseRetriever(vector_db)

    relational_db = RelationalDatabase()
    try:
        relational_db.init_db()
        feedback_store: FeedbackStore | OfflineFeedbackStore = FeedbackStore(relational_db)
    except Exception as exc:
        if active_settings.ENVIRONMENT == "production":
            raise ConfigurationError(f"PostgreSQL initialization failed: {exc}") from exc
        feedback_store = OfflineFeedbackStore()

    retrieval_pipeline = RetrievalPipeline(
        dense_retriever=dense_retriever,
        bm25_retriever=bm25_retriever,
        query_rewriter=QueryRewriter(client=query_rewriter_client),
    )
    rag_chain = RAGChain(retrieval_pipeline=retrieval_pipeline, llm_client=llm_client)

    return RuntimeContainer(
        settings=active_settings,
        vector_db=vector_db,
        relational_db=relational_db,
        dense_retriever=dense_retriever,
        bm25_retriever=bm25_retriever,
        retrieval_pipeline=retrieval_pipeline,
        feedback_store=feedback_store,
        rag_chain=rag_chain,
    )


@asynccontextmanager
async def app_lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize and tear down the runtime graph around the app lifespan."""
    container = build_runtime_container()
    app.state.runtime = container
    set_dependencies(container.rag_chain, container.feedback_store)
    try:
        yield
    finally:
        set_dependencies(None, None)
        container.close()
