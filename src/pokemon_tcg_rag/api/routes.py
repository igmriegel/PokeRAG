"""
FastAPI route controllers.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status

from pokemon_tcg_rag.api.schemas import (
    FeedbackRequest,
    HealthResponse,
    QueryRequest,
    QueryResponse,
)
from pokemon_tcg_rag.domain.models import AnswerResponse
from pokemon_tcg_rag.llm.rag_chain import RAGChain
from pokemon_tcg_rag.monitoring.feedback_store import FeedbackStore
from pokemon_tcg_rag.monitoring.metrics_collector import DEFAULT_METRICS_COLLECTOR

router = APIRouter()

_rag_chain: RAGChain | None = None
_feedback_store: FeedbackStore | None = None
_query_sessions: dict[str, AnswerResponse] = {}
_submitted_feedback: set[str] = set()


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


@router.post("/query", response_model=QueryResponse, status_code=status.HTTP_200_OK)
def query_rag(payload: QueryRequest) -> QueryResponse:
    """Execute the RAG pipeline and map the response to the public schema."""
    if _rag_chain is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="RAG chain unavailable"
        )

    try:
        response: AnswerResponse = _rag_chain.query(payload.question, top_k=payload.top_k)
        query_id = response.query_id or f"qr_{uuid.uuid4().hex[:12]}"
        response = response.model_copy(update={"query_id": query_id})
        _query_sessions[query_id] = response
        DEFAULT_METRICS_COLLECTOR.record_query(
            model=response.model_name,
            latency=response.latency_seconds,
            num_docs=len(response.retrieved_chunks),
            status="success",
            sources=[citation.source for citation in response.citations],
        )
        return QueryResponse.from_answer_response(response, query_id=query_id)
    except HTTPException:
        DEFAULT_METRICS_COLLECTOR.record_query(
            model="unknown",
            latency=0.0,
            num_docs=0,
            status="failure",
        )
        raise
    except Exception as exc:  # pragma: no cover - route boundary
        DEFAULT_METRICS_COLLECTOR.record_query(
            model="unknown",
            latency=0.0,
            num_docs=0,
            status="failure",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.post("/feedback", status_code=status.HTTP_201_CREATED)
def submit_feedback(payload: FeedbackRequest) -> dict[str, str]:
    """Persist user feedback through the feedback store service."""
    if _feedback_store is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Feedback store unavailable"
        )
    if payload.query_id in _submitted_feedback:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Feedback already submitted for this query"
        )
    stored_query = _query_sessions.get(payload.query_id)
    if stored_query is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown query_id")
    if stored_query.query != payload.query or stored_query.answer != payload.answer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Feedback payload does not match query"
        )

    try:
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Expose dependency readiness for the service health check."""
    rag_ready, feedback_ready = dependency_status()
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        rag_chain_ready=rag_ready,
        feedback_store_ready=feedback_ready,
    )
