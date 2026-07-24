"""
Integration tests for FastAPI runtime bootstrap.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from pokemon_tcg_rag.api import main as api_main
from pokemon_tcg_rag.api import runtime as api_runtime
from pokemon_tcg_rag.api.routes import dependency_status, query_rag, set_dependencies
from pokemon_tcg_rag.api.schemas import QueryRequest
from pokemon_tcg_rag.config.settings import Settings
from pokemon_tcg_rag.domain.exceptions import ConfigurationError
from pokemon_tcg_rag.domain.models import (
    AnswerResponse,
    Chunk,
    DocumentMetadata,
    DocumentSource,
    FeedbackRecord,
    RetrievedChunk,
    RuleType,
)
from pokemon_tcg_rag.storage.indexing import load_chunks


def _answer_response() -> AnswerResponse:
    metadata = DocumentMetadata(
        source=DocumentSource.RULEBOOK_PDF,
        document_title="Official Rulebook",
        page_number=12,
        rule_type=RuleType.GENERAL_RULE,
        source_url="https://example.com/rulebook.pdf",
    )
    chunk = Chunk(
        chunk_id="chunk-1",
        doc_id="doc-1",
        text="Rare Candy text",
        token_count=3,
        metadata=metadata,
    )
    return AnswerResponse(
        query="Can I use Rare Candy?",
        rewritten_query="Pokemon TCG Rare Candy legality",
        answer="Yes.",
        citations=[metadata],
        retrieved_chunks=[RetrievedChunk(chunk=chunk, score=0.9, retrieval_method="dense")],
        model_name="gpt-4o-mini",
        latency_seconds=0.42,
    )


class FakeRAGChain:
    def query(self, question: str, top_k: int | None = None) -> AnswerResponse:
        response = _answer_response()
        return response.model_copy(update={"query": question})


class FakeFeedbackStore:
    def submit_feedback(self, **kwargs: object) -> FeedbackRecord:
        return FeedbackRecord(
            feedback_id="fb_123",
            query_id=str(kwargs["query_id"]),
            query=str(kwargs["query"]),
            answer=str(kwargs["answer"]),
            rating=int(kwargs["rating"]),
            comment=None if kwargs.get("comment") is None else str(kwargs["comment"]),
            model_name=str(kwargs["model_name"]),
            latency_seconds=float(kwargs["latency"]),
        )


class FakeRuntimeContainer:
    def __init__(self) -> None:
        self.rag_chain = FakeRAGChain()
        self.feedback_store = FakeFeedbackStore()
        self.closed = False

    def close(self) -> None:
        self.closed = True


def test_lifespan_bootstraps_real_dependencies(monkeypatch) -> None:
    """The app must register runtime dependencies during startup."""
    container = FakeRuntimeContainer()
    monkeypatch.setattr(api_runtime, "build_runtime_container", lambda: container)
    set_dependencies(None, None)
    api_main.create_app()

    async def run_lifespan() -> None:
        state = SimpleNamespace()
        app_stub = SimpleNamespace(state=state)
        async with api_runtime.app_lifespan(app_stub):
            assert dependency_status() == (True, True)
            health_response = api_main.health_check()
            assert health_response.rag_chain_ready is True
            assert health_response.feedback_store_ready is True

            query_response = query_rag(QueryRequest(question="Can I use Rare Candy?", top_k=5))
            assert query_response.answer == "Yes."

            ready_response = api_main.ready_check()
            assert ready_response.status == "healthy"

        assert container.closed is True
        assert dependency_status() == (False, False)

    asyncio.run(run_lifespan())


def test_build_runtime_container_uses_offline_fallback_without_openai(monkeypatch) -> None:
    """Development startup must degrade when OpenAI, Qdrant and Postgres are unavailable."""

    def fail_qdrant(self) -> None:
        raise RuntimeError("qdrant down")

    def fail_postgres(self) -> None:
        raise RuntimeError("postgres down")

    monkeypatch.setattr(api_runtime.VectorDatabase, "init_collection", fail_qdrant)
    monkeypatch.setattr(api_runtime.RelationalDatabase, "init_db", fail_postgres)
    monkeypatch.setattr(api_runtime, "load_chunks", lambda *_args, **_kwargs: [])

    container = api_runtime.build_runtime_container(
        Settings(ENVIRONMENT="development", OPENAI_API_KEY="")
    )
    try:
        assert container.rag_chain.llm_client.model_name == "offline-llm"
        assert (
            container.retrieval_pipeline.query_rewriter.client.model_name
            == "offline-query-rewriter"
        )
        assert isinstance(container.vector_db, api_runtime.OfflineVectorDatabase)
        assert isinstance(container.feedback_store, api_runtime.OfflineFeedbackStore)
        feedback = container.feedback_store.submit_feedback(
            query_id="qid-1",
            query="q",
            answer="a",
            rating=1,
            comment=None,
            model_name="offline-llm",
            latency=0.1,
        )
        assert feedback.feedback_id.startswith("fb_")
        assert len(container.feedback_store.records) == 1
    finally:
        container.close()


def test_build_runtime_container_requires_openai_in_production(monkeypatch) -> None:
    """Production startup must fail closed if OpenAI credentials are absent."""
    monkeypatch.setattr(api_runtime.VectorDatabase, "init_collection", lambda self: None)
    monkeypatch.setattr(api_runtime.RelationalDatabase, "init_db", lambda self: None)
    monkeypatch.setattr(api_runtime, "load_chunks", lambda *_args, **_kwargs: [])

    with pytest.raises(ConfigurationError):
        api_runtime.build_runtime_container(Settings(ENVIRONMENT="production", OPENAI_API_KEY=""))


def test_bootstrap_corpus_is_loadable() -> None:
    """The bundled local corpus must be discoverable by the loader."""
    chunks = load_chunks("data/chunks")

    assert chunks
    assert any(chunk.metadata.card_name == "Rare Candy" for chunk in chunks)


def test_offline_answer_client_uses_context() -> None:
    """The offline answer path should summarize retrieved context instead of abstaining."""
    client = api_runtime.OfflineAnswerClient()
    prompt = (
        "Você é um Juiz Certificado Oficial do Pokémon Trading Card Game (TCG).\n"
        "Contexto:\n"
        "[1] Demo Rulebook Reference — p. 12\n"
        "Rare Candy lets you evolve a Basic Pokémon directly into a Stage 2 Pokémon.\n\n"
        "Pergunta:\n"
        "Posso usar Rare Candy?"
    )

    answer = client.generate_answer(prompt)

    assert answer != "I don't know."
    assert "Rare Candy" in answer


def test_ready_check_fails_closed_without_dependencies() -> None:
    """Readiness must return 503 when the runtime graph is not attached."""
    set_dependencies(None, None)
    with pytest.raises(HTTPException) as exc_info:
        api_main.ready_check()
    assert exc_info.value.status_code == 503
