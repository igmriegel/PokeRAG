"""
Unit tests for API, retrieval, schema and LLM helper branches.
"""

from __future__ import annotations

import time
from types import SimpleNamespace

import pytest
from fastapi import HTTPException, Request
from pydantic import ValidationError

from pokemon_tcg_rag.api import auth as api_auth
from pokemon_tcg_rag.api import routes as api_routes
from pokemon_tcg_rag.api.auth import (
    Principal,
    _extract_bearer_token,
    authorize_request,
    create_access_token,
    decode_access_token,
    get_current_principal,
)
from pokemon_tcg_rag.api.guards import APIRequestGuard
from pokemon_tcg_rag.api.schemas import (
    ChunkSnippetSchema,
    CitationSchema,
    FeedbackRequest,
    QueryRequest,
)
from pokemon_tcg_rag.config.settings import Settings, get_settings
from pokemon_tcg_rag.domain.exceptions import LLMError
from pokemon_tcg_rag.domain.models import (
    AnswerResponse,
    Chunk,
    DocumentMetadata,
    DocumentSource,
    RetrievedChunk,
    RuleType,
)
from pokemon_tcg_rag.llm.client import LLMClient, _is_insufficient_quota
from pokemon_tcg_rag.retrieval.cache import RetrievalCache
from pokemon_tcg_rag.retrieval.policy import (
    apply_mmr,
    matches_metadata_filters,
    normalize_metadata_filters,
)


def _metadata(
    *,
    source: DocumentSource = DocumentSource.RULEBOOK_PDF,
    document_title: str = "Rulebook",
    page_number: int | None = 12,
    card_name: str | None = "Rare Candy",
    rule_type: RuleType = RuleType.GENERAL_RULE,
) -> DocumentMetadata:
    return DocumentMetadata(
        source=source,
        document_title=document_title,
        page_number=page_number,
        card_name=card_name,
        rule_type=rule_type,
        source_url="https://example.com/rulebook.pdf",
    )


def _retrieved(text: str, *, score: float = 0.9) -> RetrievedChunk:
    chunk = Chunk(
        chunk_id="chunk-1",
        doc_id="doc-1",
        text=text,
        token_count=len(text.split()),
        metadata=_metadata(),
    )
    return RetrievedChunk(chunk=chunk, score=score, retrieval_method="dense")


def _answer_response(query_id: str | None = None) -> AnswerResponse:
    chunk = _retrieved("Rare Candy lets you evolve a Basic Pokemon.")
    metadata = _metadata()
    return AnswerResponse(
        query_id=query_id,
        query="Can I use Rare Candy?",
        rewritten_query="Pokemon TCG Rare Candy legality",
        answer="Yes.",
        citations=[metadata],
        retrieved_chunks=[chunk],
        model_name="gpt-4o-mini",
        latency_seconds=0.42,
    )


def _request(
    method: str = "POST",
    *,
    headers: dict[str, str] | None = None,
    client_host: str | None = "127.0.0.1",
) -> Request:
    encoded_headers = [
        (key.lower().encode("utf-8"), value.encode("utf-8"))
        for key, value in (headers or {}).items()
    ]
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": encoded_headers,
        "server": ("testserver", 80),
        "client": (client_host, 12345) if client_host else None,
        "root_path": "",
    }
    return Request(scope)


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch: pytest.MonkeyPatch) -> None:
    api_auth._CURRENT_PRINCIPAL = None
    api_routes.set_dependencies(None, None)
    get_settings.cache_clear()
    yield
    api_auth._CURRENT_PRINCIPAL = None
    api_routes.set_dependencies(None, None)
    get_settings.cache_clear()


def test_decode_access_token_and_principal_scopes() -> None:
    settings = Settings(
        ENVIRONMENT="production",
        API_AUTH_SECRET="unit-test-secret",
        API_AUTH_ISSUER="poketcg-rag",
        API_AUTH_AUDIENCE="poketcg-rag-api",
        API_AUTH_ALGORITHM="HS256",
    )
    token = create_access_token(
        "user-a",
        secret=settings.API_AUTH_SECRET,
        issuer=settings.API_AUTH_ISSUER,
        audience=settings.API_AUTH_AUDIENCE,
        scopes=("rag:query", "rag:feedback"),
        lifetime_seconds=60,
        algorithm=settings.API_AUTH_ALGORITHM,
    )

    principal = decode_access_token(
        token,
        settings=settings,
        required_algorithms={"HS256"},
    )

    assert principal.subject == "user-a"
    assert principal.has_scopes(("rag:query",))
    assert principal.has_scopes(("rag:query", "rag:feedback"))
    assert not principal.has_scopes(("rag:metrics",))


@pytest.mark.parametrize(
    "token,settings,required_algorithms,expected_status",
    [
        (
            "abc",
            Settings(ENVIRONMENT="production", API_AUTH_SECRET="secret"),
            None,
            401,
        ),
        (
            create_access_token(
                "user-a",
                secret="secret",
                issuer="poketcg-rag",
                audience="poketcg-rag-api",
                scopes=("rag:query",),
                lifetime_seconds=-1,
            ),
            Settings(
                ENVIRONMENT="production",
                API_AUTH_SECRET="secret",
                API_AUTH_ISSUER="poketcg-rag",
                API_AUTH_AUDIENCE="poketcg-rag-api",
            ),
            {"HS256"},
            401,
        ),
        (
            create_access_token(
                "user-a",
                secret="secret",
                issuer="poketcg-rag",
                audience="poketcg-rag-api",
                scopes=("rag:query",),
                lifetime_seconds=60,
            ),
            Settings(
                ENVIRONMENT="production",
                API_AUTH_SECRET="secret",
                API_AUTH_ISSUER="wrong-issuer",
                API_AUTH_AUDIENCE="poketcg-rag-api",
            ),
            {"HS256"},
            403,
        ),
        (
            create_access_token(
                "user-a",
                secret="secret",
                issuer="poketcg-rag",
                audience="poketcg-rag-api",
                scopes=("rag:query",),
                lifetime_seconds=60,
            ),
            Settings(
                ENVIRONMENT="production",
                API_AUTH_SECRET="secret",
                API_AUTH_ISSUER="poketcg-rag",
                API_AUTH_AUDIENCE="poketcg-rag-api",
            ),
            {"RS256"},
            401,
        ),
    ],
)
def test_decode_access_token_rejects_invalid_tokens(
    token: str,
    settings: Settings,
    required_algorithms: set[str] | None,
    expected_status: int,
) -> None:
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(
            token,
            settings=settings,
            required_algorithms=required_algorithms,
        )

    assert exc_info.value.status_code == expected_status


def test_authorize_request_uses_development_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("API_AUTH_SECRET", "")
    get_settings.cache_clear()

    request = _request("GET")
    principal = authorize_request("rag:query")(request)

    assert principal.subject == "anonymous"
    assert request.state.principal == principal
    assert get_current_principal() == principal


def test_extract_bearer_token_handles_variants() -> None:
    assert _extract_bearer_token("Bearer abc123") == "abc123"
    assert _extract_bearer_token("Basic abc123") is None
    assert _extract_bearer_token("Bearer   ") is None
    assert _extract_bearer_token(None) is None


def test_request_guard_enforces_body_size_and_concurrency() -> None:
    guard = APIRequestGuard(
        rate_limit_per_minute=2,
        max_concurrent_requests=1,
        max_body_bytes=10,
    )

    guard.enforce_request_size(_request("GET"))

    with pytest.raises(HTTPException) as size_error:
        guard.enforce_request_size(_request("POST", headers={"content-length": "25"}))
    assert size_error.value.status_code == 413

    with pytest.raises(HTTPException) as header_error:
        guard.enforce_request_size(_request("POST", headers={"content-length": "bad"}))
    assert header_error.value.status_code == 400

    principal = Principal(
        subject="user-a",
        issuer="poketcg-rag",
        audience="poketcg-rag-api",
        scopes=frozenset({"rag:query"}),
    )
    with guard.admit(principal, _request("POST"), "query"):
        assert guard._principal_key(principal, _request("POST"), "query").startswith(
            "user-a:127.0.0.1:query"
        )

    guard._inflight.acquire(blocking=False)
    try:
        with (
            pytest.raises(HTTPException) as concurrency_error,
            guard.admit(principal, _request("POST"), "query"),
        ):
            pass
        assert concurrency_error.value.status_code == 429
    finally:
        guard._inflight.release()


def test_request_guard_rate_limit_rejects_repeated_requests() -> None:
    guard = APIRequestGuard(
        rate_limit_per_minute=1,
        max_concurrent_requests=1,
        max_body_bytes=1024,
    )
    principal = Principal(
        subject="user-a",
        issuer="poketcg-rag",
        audience="poketcg-rag-api",
        scopes=frozenset({"rag:query"}),
    )
    request = _request("POST")

    with guard.admit(principal, request, "query"):
        pass

    with (
        pytest.raises(HTTPException) as rate_error,
        guard.admit(principal, request, "query"),
    ):
        pass
    assert rate_error.value.status_code == 429


def test_cache_set_get_expire_and_evict(monkeypatch: pytest.MonkeyPatch) -> None:
    cache = RetrievalCache(max_items=1, ttl_seconds=60)
    key = cache.make_key(query="Rare Candy", top_k=5)
    assert key == cache.make_key(top_k=5, query="Rare Candy")

    monkeypatch.setattr("pokemon_tcg_rag.retrieval.cache.time.time", lambda: 100.0)
    chunk = _retrieved("Rare Candy lets you evolve faster.")
    cache.set(key, [chunk])
    cached = cache.get(key)
    assert cached is not None
    assert cached[0] is not chunk
    assert cached[0].chunk.chunk_id == "chunk-1"

    monkeypatch.setattr("pokemon_tcg_rag.retrieval.cache.time.time", lambda: 200.0)
    assert cache.get(key) is None

    fresh_key = cache.make_key(query="other")
    monkeypatch.setattr("pokemon_tcg_rag.retrieval.cache.time.time", lambda: 210.0)
    cache.set(key, [chunk])
    cache.set(fresh_key, [chunk])
    assert cache.get(key) is None
    assert cache.get(fresh_key) is not None


def test_retrieval_policy_filters_and_mmr_edges() -> None:
    chunk = _retrieved("Rare Candy lets you evolve faster.")
    assert normalize_metadata_filters(None) == {}
    assert matches_metadata_filters(chunk, {"source": "rulebook_pdf"})
    assert not matches_metadata_filters(chunk, {"source": "pokegym_rulings"})
    assert apply_mmr([], top_k=2) == []
    assert apply_mmr([chunk], top_k=0) == []


def test_schema_helpers_normalize_and_truncate() -> None:
    request = QueryRequest(
        question="  Can I use Rare Candy?  ",
        metadata_filters={" source ": " rulebook_pdf ", "junk": "x"},
    )
    assert request.question == "Can I use Rare Candy?"
    assert request.metadata_filters == {"source": "rulebook_pdf"}

    metadata = _metadata()
    citation = CitationSchema.from_metadata(metadata)
    assert citation.source == DocumentSource.RULEBOOK_PDF.value

    snippet = ChunkSnippetSchema.from_retrieved_chunk(
        RetrievedChunk(
            chunk=Chunk(
                chunk_id="chunk-2",
                doc_id="doc-2",
                text="x" * 400,
                token_count=1,
                metadata=metadata,
            ),
            score=0.5,
            retrieval_method="dense",
        )
    )
    assert snippet.text.endswith("...")
    assert len(snippet.text) == 323

    with pytest.raises(ValidationError):
        FeedbackRequest(
            query_id="qid-1",
            query=" ",
            answer="a",
            rating=1,
            model_name="gpt-4o-mini",
            latency_seconds=0.1,
        )


def test_route_helper_supports_legacy_chain_signature() -> None:
    class LegacyChain:
        def __init__(self) -> None:
            self.calls: list[tuple[str, int | None]] = []

        def query(self, question: str, top_k: int | None = None) -> AnswerResponse:
            self.calls.append((question, top_k))
            return _answer_response("qr_legacy")

    chain = LegacyChain()
    api_routes.set_dependencies(chain, SimpleNamespace())

    response = api_routes._call_rag_chain_query(
        "Can I use Rare Candy?",
        top_k=5,
        metadata_filters={"source": "rulebook_pdf"},
    )

    assert response.query_id == "qr_legacy"
    assert chain.calls == [("Can I use Rare Candy?", 5)]


def test_submit_feedback_rejects_duplicate_and_owner_mismatch() -> None:
    store = SimpleNamespace(submit_feedback=lambda **kwargs: SimpleNamespace(**kwargs))
    api_routes.set_dependencies(SimpleNamespace(), store)

    session = api_routes.QuerySession(
        response=_answer_response("qr-1"),
        owner_subject="owner-a",
        issued_at=time.time(),
    )
    api_routes._query_sessions["qr-1"] = session
    principal = Principal(
        subject="owner-a",
        issuer="poketcg-rag",
        audience="poketcg-rag-api",
        scopes=frozenset({"rag:feedback"}),
    )
    payload = FeedbackRequest(
        query_id="qr-1",
        query="Can I use Rare Candy?",
        answer="Yes.",
        rating=1,
        model_name="gpt-4o-mini",
        latency_seconds=0.1,
    )

    assert (
        api_routes.submit_feedback(payload, principal=principal)["status"] == "success"
    )

    with pytest.raises(HTTPException) as duplicate_error:
        api_routes.submit_feedback(payload, principal=principal)
    assert duplicate_error.value.status_code == 409

    api_routes._submitted_feedback.clear()
    api_routes._query_sessions["qr-2"] = api_routes.QuerySession(
        response=_answer_response("qr-2"),
        owner_subject="owner-a",
        issued_at=time.time(),
    )
    with pytest.raises(HTTPException) as owner_error:
        api_routes.submit_feedback(
            FeedbackRequest(
                query_id="qr-2",
                query="Can I use Rare Candy?",
                answer="Yes.",
                rating=1,
                model_name="gpt-4o-mini",
                latency_seconds=0.1,
            ),
            principal=Principal(
                subject="owner-b",
                issuer="poketcg-rag",
                audience="poketcg-rag-api",
                scopes=frozenset({"rag:feedback"}),
            ),
        )
    assert owner_error.value.status_code == 403


def test_llm_client_circuit_breaker_and_quota_helper() -> None:
    class FakeCompletions:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def create(self, **kwargs: object) -> object:
            self.calls.append(kwargs)
            raise RuntimeError("boom")

    class FakeClient:
        def __init__(self) -> None:
            self.chat = SimpleNamespace(completions=FakeCompletions())

    client = LLMClient(client=FakeClient(), retries=1, retry_delay=0.0)
    client.circuit_breaker_threshold = 1
    client.circuit_breaker_reset_seconds = 60

    with pytest.raises(LLMError):
        client.generate_answer("prompt")

    with pytest.raises(LLMError, match="circuit breaker is open"):
        client.generate_answer("prompt")

    assert _is_insufficient_quota(SimpleNamespace(code="insufficient_quota"))
    assert _is_insufficient_quota(
        SimpleNamespace(body={"error": {"code": "insufficient_quota"}})
    )
    assert _is_insufficient_quota(RuntimeError("insufficient_quota"))
