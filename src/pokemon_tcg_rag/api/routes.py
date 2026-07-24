"""
FastAPI route controllers.
"""

from __future__ import annotations

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

router = APIRouter()

_rag_chain: RAGChain | None = None
_feedback_store: FeedbackStore | None = None


def set_dependencies(
    rag_chain: RAGChain | None = None,
    feedback_store: FeedbackStore | None = None,
) -> None:
    """Register application dependencies for request handlers."""
    global _rag_chain, _feedback_store
    _rag_chain = rag_chain
    _feedback_store = feedback_store


def dependency_status() -> tuple[bool, bool]:
    """Return availability flags for dependency health checks."""
    return _rag_chain is not None, _feedback_store is not None


@router.post("/query", response_model=QueryResponse, status_code=status.HTTP_200_OK)
def query_rag(payload: QueryRequest) -> QueryResponse:
    """Execute the RAG pipeline and map the response to the public schema."""
    if _rag_chain is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="RAG chain unavailable")

    try:
        response: AnswerResponse = _rag_chain.query(payload.question)
        return QueryResponse.from_answer_response(response)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - route boundary
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("/feedback", status_code=status.HTTP_201_CREATED)
def submit_feedback(payload: FeedbackRequest) -> dict[str, str]:
    """Persist user feedback through the feedback store service."""
    if _feedback_store is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Feedback store unavailable")

    try:
        _feedback_store.submit_feedback(
            query=payload.query,
            answer=payload.answer,
            rating=payload.rating,
            comment=payload.comment,
            model_name=payload.model_name,
            latency=payload.latency_seconds,
        )
        return {"status": "success", "message": "Feedback recorded successfully."}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - route boundary
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


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
