"""
FastAPI route controllers.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

from fastapi import APIRouter, Depends, HTTPException, Security, status

from pokemon_tcg_rag.api.auth import (
    Principal,
    authorize_request,
    bearer_scheme,
    get_current_principal,
)
from pokemon_tcg_rag.api.guards import DEFAULT_REQUEST_GUARD
from pokemon_tcg_rag.api.schemas import (
    FeedbackRequest,
    HealthResponse,
    QueryRequest,
    QueryResponse,
)
from pokemon_tcg_rag.config.settings import get_settings
from pokemon_tcg_rag.domain.exceptions import LLMQuotaError
from pokemon_tcg_rag.domain.models import AnswerResponse
from pokemon_tcg_rag.llm.rag_chain import RAGChain
from pokemon_tcg_rag.monitoring.feedback_store import FeedbackStore
from pokemon_tcg_rag.monitoring.logger import get_logger
from pokemon_tcg_rag.monitoring.metrics_collector import DEFAULT_METRICS_COLLECTOR
from pokemon_tcg_rag.monitoring.tracing import traced_span

router = APIRouter()
LOGGER = get_logger(__name__)

_rag_chain: RAGChain | None = None
_feedback_store: FeedbackStore | None = None
_query_sessions: dict[str, QuerySession] = {}
_submitted_feedback: set[str] = set()


@dataclass(frozen=True, slots=True)
class QuerySession:
    """Stored query context used to validate later feedback."""

    response: AnswerResponse
    owner_subject: str
    issued_at: float


def set_dependencies(
    rag_chain: RAGChain | None = None,
    feedback_store: FeedbackStore | None = None,
) -> None:
    """Register application dependencies for request handlers."""
    global _rag_chain, _feedback_store
    _rag_chain = rag_chain
    _feedback_store = feedback_store
    if rag_chain is None and feedback_store is None:
        _query_sessions.clear()
        _submitted_feedback.clear()


def dependency_status() -> tuple[bool, bool]:
    """Return availability flags for dependency health checks."""
    return _rag_chain is not None, _feedback_store is not None


@router.post(
    "/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Security(bearer_scheme()), Depends(authorize_request("rag:query"))],
)
def query_rag_route(payload: QueryRequest) -> QueryResponse:
    """HTTP wrapper that enforces auth then delegates to the core query flow."""
    return query_rag(payload, principal=get_current_principal())


def query_rag(payload: QueryRequest, principal: Principal | None = None) -> QueryResponse:
    """Execute the RAG pipeline and map the response to the public schema."""
    if _rag_chain is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG chain unavailable",
        )

    try:
        effective_principal = principal or _resolve_principal()
        with (
            traced_span(
                "api.query",
                attributes={
                    "query.length": len(payload.question.strip()),
                    "query.top_k": payload.top_k,
                },
            ),
            DEFAULT_REQUEST_GUARD.admit(effective_principal, None, "query"),
        ):
            response: AnswerResponse = _call_rag_chain_query(
                payload.question,
                top_k=payload.top_k,
                metadata_filters=payload.metadata_filters,
            )
            query_id = response.query_id or f"qr_{uuid.uuid4().hex[:12]}"
            response = response.model_copy(update={"query_id": query_id})
            _query_sessions[query_id] = QuerySession(
                response=response,
                owner_subject=effective_principal.subject,
                issued_at=time.time(),
            )
            DEFAULT_METRICS_COLLECTOR.record_query(
                model=response.model_name,
                latency=response.latency_seconds,
                num_docs=len(response.retrieved_chunks),
                status="success",
                sources=[citation.source for citation in response.citations],
            )
            return QueryResponse.from_answer_response(response, query_id=query_id)
    except LLMQuotaError as exc:
        LOGGER.warning("llm_quota_unavailable")
        DEFAULT_METRICS_COLLECTOR.record_query(
            model="unknown",
            latency=0.0,
            num_docs=0,
            status="failure",
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "OpenAI API quota is unavailable. Add API credits or review "
                "the organization's billing limits."
            ),
        ) from exc
    except HTTPException:
        DEFAULT_METRICS_COLLECTOR.record_query(
            model="unknown",
            latency=0.0,
            num_docs=0,
            status="failure",
        )
        raise
    except Exception as exc:  # pragma: no cover - route boundary
        error_id = uuid.uuid4().hex[:8]
        LOGGER.exception("query_failed", extra={"error_id": error_id})
        DEFAULT_METRICS_COLLECTOR.record_query(
            model="unknown",
            latency=0.0,
            num_docs=0,
            status="failure",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Request failed (ref: {error_id})",
        ) from exc


@router.post(
    "/feedback",
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Security(bearer_scheme()),
        Depends(authorize_request("rag:feedback")),
    ],
)
def submit_feedback_route(payload: FeedbackRequest) -> dict[str, str]:
    """HTTP wrapper that enforces auth then delegates to the core feedback flow."""
    return submit_feedback(payload, principal=get_current_principal())


def submit_feedback(payload: FeedbackRequest, principal: Principal | None = None) -> dict[str, str]:
    """Persist user feedback through the feedback store service."""
    if _feedback_store is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Feedback store unavailable",
        )
    if payload.query_id in _submitted_feedback:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Feedback already submitted for this query",
        )
    effective_principal = principal or _resolve_principal()
    stored_query = _query_sessions.get(payload.query_id)
    if stored_query is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown query_id")
    if stored_query.owner_subject != effective_principal.subject:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Feedback owner mismatch")
    if time.time() - stored_query.issued_at > get_settings().API_FEEDBACK_MAX_AGE_SECONDS:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Feedback window expired")
    if (
        stored_query.response.query != payload.query
        or stored_query.response.answer != payload.answer
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feedback payload does not match query",
        )

    try:
        with (
            traced_span(
                "api.feedback",
                attributes={
                    "feedback.rating": payload.rating,
                    "feedback.comment_length": len(payload.comment or ""),
                },
            ),
            DEFAULT_REQUEST_GUARD.admit(effective_principal, None, "feedback"),
        ):
            _feedback_store.submit_feedback(
                query_id=payload.query_id,
                query=payload.query,
                answer=payload.answer,
                rating=payload.rating,
                comment=payload.comment,
                model_name=payload.model_name,
                latency=payload.latency_seconds,
            )
            _submitted_feedback.add(payload.query_id)
            DEFAULT_METRICS_COLLECTOR.record_feedback(payload.rating)
            return {"status": "success", "message": "Feedback recorded successfully."}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - route boundary
        error_id = uuid.uuid4().hex[:8]
        LOGGER.exception("feedback_failed", extra={"error_id": error_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Request failed (ref: {error_id})",
        ) from exc


@router.get(
    "/health",
    response_model=HealthResponse,
    dependencies=[Depends(authorize_request("rag:diagnostics"))],
)
def health() -> HealthResponse:
    """Expose dependency readiness for the service health check."""
    rag_ready, feedback_ready = dependency_status()
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        rag_chain_ready=rag_ready,
        feedback_store_ready=feedback_ready,
    )


def _resolve_principal() -> Principal:
    return Principal(
        subject="anonymous",
        issuer="poketcg-rag",
        audience="poketcg-rag-api",
        scopes=frozenset({"rag:query", "rag:feedback", "rag:metrics", "rag:diagnostics"}),
    )


def _call_rag_chain_query(
    question: str,
    top_k: int,
    metadata_filters: dict[str, str] | None,
) -> AnswerResponse:
    """Invoke the configured chain with compatibility for older fakes."""
    assert _rag_chain is not None
    try:
        return _rag_chain.query(
            question,
            top_k=top_k,
            metadata_filters=metadata_filters,
        )
    except TypeError as exc:
        if "unexpected keyword argument 'metadata_filters'" not in str(exc):
            raise
        return _rag_chain.query(question, top_k=top_k)
