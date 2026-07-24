"""
TASK-046 — TEST-134

Security integration tests for API authentication and authorization.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from pokemon_tcg_rag.api import main as api_main
from pokemon_tcg_rag.api import runtime as api_runtime
from pokemon_tcg_rag.api.auth import create_access_token
from pokemon_tcg_rag.api.routes import set_dependencies
from pokemon_tcg_rag.config.settings import get_settings
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
        return _answer_response().model_copy(update={"query": question})


class FakeFeedbackStore:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def submit_feedback(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        return SimpleNamespace(**kwargs)


class FakeRuntimeContainer:
    def __init__(self) -> None:
        self.rag_chain = FakeRAGChain()
        self.feedback_store = FakeFeedbackStore()
        self.closed = False

    def close(self) -> None:
        self.closed = True


@pytest.fixture()
def security_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("API_AUTH_SECRET", "unit-test-secret")
    monkeypatch.setenv("API_AUTH_ISSUER", "poketcg-rag")
    monkeypatch.setenv("API_AUTH_AUDIENCE", "poketcg-rag-api")
    monkeypatch.setenv("API_AUTH_ALGORITHM", "HS256")
    get_settings.cache_clear()

    container = FakeRuntimeContainer()
    monkeypatch.setattr(api_runtime, "build_runtime_container", lambda: container)
    set_dependencies(None, None)
    app = api_main.app

    with TestClient(app) as client:
        yield client

    set_dependencies(None, None)
    get_settings.cache_clear()


def _token(subject: str, scopes: tuple[str, ...]) -> str:
    settings = get_settings()
    return create_access_token(
        subject=subject,
        secret=settings.API_AUTH_SECRET,
        issuer=settings.API_AUTH_ISSUER,
        audience=settings.API_AUTH_AUDIENCE,
        scopes=scopes,
        lifetime_seconds=60,
        algorithm=settings.API_AUTH_ALGORITHM,
    )


def test_openapi_declares_bearer_security(security_client: TestClient) -> None:
    """Protected endpoints must advertise bearer auth in OpenAPI."""
    schema = security_client.get("/openapi.json").json()
    query_security = schema["paths"]["/api/v1/query"]["post"]["security"]
    feedback_security = schema["paths"]["/api/v1/feedback"]["post"]["security"]
    assert query_security
    assert feedback_security


@pytest.mark.parametrize(
    "path,method",
    [
        ("/api/v1/query", "post"),
        ("/api/v1/feedback", "post"),
        ("/api/v1/health", "get"),
        ("/metrics", "get"),
        ("/ready", "get"),
    ],
)
def test_protected_routes_reject_missing_token(
    security_client: TestClient, path: str, method: str
) -> None:
    """Anonymous access must be rejected for protected API operations."""
    if method == "post":
        response = security_client.post(
            path,
            json={"question": "Can I use Rare Candy?"},
        )
    else:
        response = security_client.get(path)
    assert response.status_code == 401


def test_scope_matrix_and_ownership_enforced(security_client: TestClient) -> None:
    """Scope checks and object ownership must be enforced consistently."""
    query_token = _token("user-a", ("rag:query",))
    feedback_token = _token("user-b", ("rag:feedback",))
    full_token = _token("user-a", ("rag:query", "rag:feedback", "rag:metrics", "rag:diagnostics"))

    query_response = security_client.post(
        "/api/v1/query",
        json={"question": "Can I use Rare Candy?", "top_k": 5},
        headers={"Authorization": f"Bearer {query_token}"},
    )
    assert query_response.status_code == 200
    payload = query_response.json()

    denied_feedback = security_client.post(
        "/api/v1/feedback",
        json={
            "query_id": payload["query_id"],
            "query": payload["query"],
            "answer": payload["answer"],
            "rating": 1,
            "model_name": "gpt-4o-mini",
            "latency_seconds": 0.5,
        },
        headers={"Authorization": f"Bearer {feedback_token}"},
    )
    assert denied_feedback.status_code == 403

    allowed_feedback = security_client.post(
        "/api/v1/feedback",
        json={
            "query_id": payload["query_id"],
            "query": payload["query"],
            "answer": payload["answer"],
            "rating": 1,
            "model_name": "gpt-4o-mini",
            "latency_seconds": 0.5,
        },
        headers={"Authorization": f"Bearer {full_token}"},
    )
    assert allowed_feedback.status_code == 201

    metrics_response = security_client.get(
        "/metrics",
        headers={"Authorization": f"Bearer {full_token}"},
    )
    assert metrics_response.status_code == 200

    diagnostics_response = security_client.get(
        "/ready",
        headers={"Authorization": f"Bearer {full_token}"},
    )
    assert diagnostics_response.status_code == 200
