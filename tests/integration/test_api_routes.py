"""
TASK-029 — TEST-093, TEST-094, TEST-095, TEST-096

Integration tests for the FastAPI application.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from pokemon_tcg_rag.api.main import app
from pokemon_tcg_rag.api.routes import set_dependencies
from pokemon_tcg_rag.domain.models import (
    AnswerResponse,
    Chunk,
    DocumentMetadata,
    DocumentSource,
    RetrievedChunk,
    RuleType,
)


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
    retrieved = RetrievedChunk(chunk=chunk, score=0.9, retrieval_method="dense")
    return AnswerResponse(
        query="Can I use Rare Candy?",
        rewritten_query="Pokemon TCG Rare Candy legality",
        answer="Yes.",
        citations=[metadata],
        retrieved_chunks=[retrieved],
        model_name="gpt-4o-mini",
        latency_seconds=0.42,
    )


class FakeRAGChain:
    def __init__(self, response: AnswerResponse | None = None, error: Exception | None = None) -> None:
        self.response = response or _answer_response()
        self.error = error
        self.calls: list[str] = []

    def query(self, question: str) -> AnswerResponse:
        self.calls.append(question)
        if self.error is not None:
            raise self.error
        return self.response


class FakeFeedbackStore:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def submit_feedback(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(**kwargs)


@pytest.fixture(autouse=True)
def _reset_dependencies() -> None:
    set_dependencies(None, None)
    yield
    set_dependencies(None, None)


@pytest.mark.integration
def test_query_endpoint_returns_answer() -> None:
    """TEST-093: query endpoint must return a cited answer."""
    fake_chain = FakeRAGChain()
    fake_feedback = FakeFeedbackStore()
    set_dependencies(fake_chain, fake_feedback)
    client = TestClient(app)

    response = client.post("/api/v1/query", json={"question": "Can I use Rare Candy?", "top_k": 5})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Yes."
    assert body["citations"][0]["document_title"] == "Official Rulebook"
    assert fake_chain.calls == ["Can I use Rare Candy?"]


@pytest.mark.integration
def test_feedback_endpoint_persists() -> None:
    """TEST-094: feedback endpoint must persist the payload."""
    fake_chain = FakeRAGChain()
    fake_feedback = FakeFeedbackStore()
    set_dependencies(fake_chain, fake_feedback)
    client = TestClient(app)

    response = client.post(
        "/api/v1/feedback",
        json={
            "query": "q",
            "answer": "a",
            "rating": 1,
            "comment": "ok",
            "model_name": "gpt-4o-mini",
            "latency_seconds": 0.5,
        },
    )

    assert response.status_code == 201
    assert fake_feedback.calls[0]["rating"] == 1


@pytest.mark.integration
def test_health_endpoint_ok() -> None:
    """TEST-095: health endpoint must report dependency readiness."""
    set_dependencies(FakeRAGChain(), FakeFeedbackStore())
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["rag_chain_ready"] is True
    assert body["feedback_store_ready"] is True


@pytest.mark.integration
def test_query_error_maps_to_http_500() -> None:
    """TEST-096: query endpoint must map retrieval errors to HTTP 500."""
    set_dependencies(FakeRAGChain(error=RuntimeError("boom")), FakeFeedbackStore())
    client = TestClient(app)

    response = client.post("/api/v1/query", json={"question": "Can I use Rare Candy?", "top_k": 5})

    assert response.status_code == 500
    assert "boom" in response.json()["detail"]
