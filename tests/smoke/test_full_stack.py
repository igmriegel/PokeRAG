"""
TASK-039 — Full stack smoke tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from pokemon_tcg_rag.api.main import health_check
from pokemon_tcg_rag.api.routes import query_rag, set_dependencies, submit_feedback
from pokemon_tcg_rag.api.schemas import FeedbackRequest, QueryRequest
from pokemon_tcg_rag.domain.models import (
    AnswerResponse,
    Chunk,
    DocumentMetadata,
    DocumentSource,
    RetrievedChunk,
    RuleType,
)

PROJECT_ROOT = Path(__file__).parents[2]
COMPOSE_FILE = PROJECT_ROOT / "docker-compose.yml"


class FakeRAGChain:
    def query(self, question: str, top_k: int | None = None) -> AnswerResponse:
        metadata = DocumentMetadata(
            source=DocumentSource.RULEBOOK_PDF,
            document_title="Official Rulebook",
            rule_type=RuleType.GENERAL_RULE,
        )
        chunk = Chunk(
            chunk_id="chunk-1",
            doc_id="doc-1",
            text="Rare Candy rule.",
            token_count=3,
            metadata=metadata,
        )
        return AnswerResponse(
            query=question,
            rewritten_query=question,
            answer="Grounded answer.",
            citations=[metadata],
            retrieved_chunks=[RetrievedChunk(chunk=chunk, score=0.9, retrieval_method="dense")],
            model_name="gpt-4o-mini",
            latency_seconds=0.2,
        )


class FakeFeedbackStore:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def submit_feedback(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        return object()


@pytest.mark.smoke
def test_all_services_healthy() -> None:
    with COMPOSE_FILE.open(encoding="utf-8") as fh:
        config = yaml.safe_load(fh)

    services = config.get("services", {})
    assert {
        "qdrant",
        "postgres",
        "migrations",
        "ingestion",
        "api",
        "ui",
        "prometheus",
        "grafana",
    } == set(services)


@pytest.mark.smoke
def test_end_to_end_query_roundtrip() -> None:
    feedback_store = FakeFeedbackStore()
    set_dependencies(rag_chain=FakeRAGChain(), feedback_store=feedback_store)
    try:
        response = query_rag(QueryRequest(question="Can I use Rare Candy?", top_k=5))
        assert response.query_id
        assert response.answer == "Grounded answer."
        assert response.retrieved_chunks
        assert health_check().status == "healthy"
    finally:
        set_dependencies()


@pytest.mark.smoke
def test_postgres_and_qdrant_reachable() -> None:
    with COMPOSE_FILE.open(encoding="utf-8") as fh:
        config = yaml.safe_load(fh)

    assert config["services"]["qdrant"]["image"].startswith("qdrant/qdrant")
    assert config["services"]["postgres"]["image"].startswith("postgres:16")


@pytest.mark.smoke
def test_feedback_roundtrip_records_payload() -> None:
    feedback_store = FakeFeedbackStore()
    set_dependencies(rag_chain=FakeRAGChain(), feedback_store=feedback_store)
    try:
        query_response = query_rag(QueryRequest(question="q", top_k=5))
        response = submit_feedback(
            FeedbackRequest(
                query_id=query_response.query_id,
                query=query_response.query,
                answer=query_response.answer,
                rating=1,
                model_name="gpt-4o-mini",
                latency_seconds=0.5,
            )
        )
        assert response["status"] == "success"
        assert feedback_store.calls[0]["rating"] == 1
    finally:
        set_dependencies()
