"""
TASK-047 — TEST-135

Security/load tests for API payload, rate and body-size controls.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from types import SimpleNamespace

import httpx
import pytest
import pytest_asyncio

from pokemon_tcg_rag.api import main as api_main
from pokemon_tcg_rag.api import routes as api_routes
from pokemon_tcg_rag.api import runtime as api_runtime
from pokemon_tcg_rag.api.auth import create_access_token
from pokemon_tcg_rag.api.guards import APIRequestGuard
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
    def query(
        self,
        question: str,
        top_k: int | None = None,
        metadata_filters: dict[str, str] | None = None,
    ) -> AnswerResponse:
        return _answer_response().model_copy(update={"query": question})


class FakeFeedbackStore:
    def submit_feedback(self, **kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(**kwargs)


class FakeRuntimeContainer:
    def __init__(self) -> None:
        self.rag_chain = FakeRAGChain()
        self.feedback_store = FakeFeedbackStore()

    def close(self) -> None:
        return None


@asynccontextmanager
async def _client_for_app(app: object) -> AsyncIterator[httpx.AsyncClient]:
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client,
    ):
        yield client


@pytest_asyncio.fixture()
async def guarded_client(
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncIterator[httpx.AsyncClient]:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("API_AUTH_SECRET", "unit-test-secret")
    monkeypatch.setenv("API_AUTH_ISSUER", "poketcg-rag")
    monkeypatch.setenv("API_AUTH_AUDIENCE", "poketcg-rag-api")
    monkeypatch.setenv("API_AUTH_ALGORITHM", "HS256")
    monkeypatch.setenv("API_MAX_BODY_BYTES", "4096")
    get_settings.cache_clear()

    monkeypatch.setattr(
        api_routes,
        "DEFAULT_REQUEST_GUARD",
        APIRequestGuard(rate_limit_per_minute=1, max_concurrent_requests=1, max_body_bytes=4096),
    )
    monkeypatch.setattr(api_runtime, "build_runtime_container", lambda: FakeRuntimeContainer())
    set_dependencies(None, None)
    app = api_main.create_app()
    async with _client_for_app(app) as client:
        yield client

    set_dependencies(None, None)
    get_settings.cache_clear()


def _token(scopes: tuple[str, ...]) -> str:
    settings = get_settings()
    return create_access_token(
        subject="user-a",
        secret=settings.API_AUTH_SECRET,
        issuer=settings.API_AUTH_ISSUER,
        audience=settings.API_AUTH_AUDIENCE,
        scopes=scopes,
        lifetime_seconds=60,
        algorithm=settings.API_AUTH_ALGORITHM,
    )


@pytest.mark.asyncio
async def test_payload_schema_limits_reject_unknown_fields(
    guarded_client: httpx.AsyncClient,
) -> None:
    """Unknown request fields must be rejected."""
    response = await guarded_client.post(
        "/api/v1/query",
        json={"question": "Can I use Rare Candy?", "top_k": 5, "unexpected": True},
        headers={"Authorization": f"Bearer {_token(('rag:query',))}"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_payload_schema_limits_reject_oversized_question(
    guarded_client: httpx.AsyncClient,
) -> None:
    """Question text must be bounded."""
    response = await guarded_client.post(
        "/api/v1/query",
        json={"question": "x" * 600, "top_k": 5},
        headers={"Authorization": f"Bearer {_token(('rag:query',))}"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_request_body_size_limit_returns_413(
    guarded_client: httpx.AsyncClient,
) -> None:
    """Large request bodies must be rejected before model execution."""
    response = await guarded_client.post(
        "/api/v1/query",
        json={"question": "x" * 5000, "top_k": 5},
        headers={"Authorization": f"Bearer {_token(('rag:query',))}"},
    )
    assert response.status_code == 413


@pytest.mark.asyncio
async def test_rate_limit_returns_429(guarded_client: httpx.AsyncClient) -> None:
    """Per-principal request limits must be enforced."""
    headers = {"Authorization": f"Bearer {_token(('rag:query',))}"}
    first = await guarded_client.post(
        "/api/v1/query",
        json={"question": "Can I use Rare Candy?", "top_k": 5},
        headers=headers,
    )
    assert first.status_code == 200

    second = await guarded_client.post(
        "/api/v1/query",
        json={"question": "Can I use Rare Candy?", "top_k": 5},
        headers=headers,
    )
    assert second.status_code == 429
