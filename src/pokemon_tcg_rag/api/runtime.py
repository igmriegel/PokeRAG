"""
Runtime composition helpers for the FastAPI application.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastapi import FastAPI

from pokemon_tcg_rag.api.routes import set_dependencies
from pokemon_tcg_rag.config.settings import Settings, get_settings
from pokemon_tcg_rag.domain.models import Chunk
from pokemon_tcg_rag.llm.rag_chain import RAGChain
from pokemon_tcg_rag.monitoring.feedback_store import FeedbackStore
from pokemon_tcg_rag.retrieval.bm25 import BM25Retriever
from pokemon_tcg_rag.retrieval.dense import DenseRetriever
from pokemon_tcg_rag.retrieval.pipeline import RetrievalPipeline
from pokemon_tcg_rag.storage.indexing import load_chunks
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


def build_runtime_container(settings: Settings | None = None) -> RuntimeContainer:
    """Build the real dependency graph used by the API and UI."""
    active_settings = settings or get_settings()
    vector_db = VectorDatabase()
    relational_db = RelationalDatabase()

    chunks: list[Chunk] = load_chunks(active_settings.DATA_CHUNKS_DIR)
    bm25_retriever = BM25Retriever(chunks)
    dense_retriever = DenseRetriever(vector_db)
    retrieval_pipeline = RetrievalPipeline(
        dense_retriever=dense_retriever,
        bm25_retriever=bm25_retriever,
    )
    feedback_store = FeedbackStore(relational_db)
    rag_chain = RAGChain(retrieval_pipeline=retrieval_pipeline)

    vector_db.init_collection()
    relational_db.init_db()

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
