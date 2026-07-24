"""
TASK-037 — Metrics endpoint integration test.
"""

from __future__ import annotations

import pytest

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


class FakeRAGChain:
    def query(self, question: str) -> AnswerResponse:
        metadata = DocumentMetadata(
            source=DocumentSource.RULEBOOK_PDF,
            document_title="Official Rulebook",
            page_number=15,
            rule_type=RuleType.GENERAL_RULE,
        )
        chunk = Chunk(
            chunk_id="chunk-1",
            doc_id="doc-1",
            text="Rare Candy can only be used when allowed.",
            token_count=9,
            metadata=metadata,
        )
        retrieved = RetrievedChunk(chunk=chunk, score=0.95, retrieval_method="dense")
        return AnswerResponse(
            query=question,
            rewritten_query=question,
            answer="I don't know.",
            citations=[metadata],
            retrieved_chunks=[retrieved],
            model_name="gpt-4o-mini",
            latency_seconds=0.15,
        )


class FakeFeedbackStore:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def submit_feedback(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        return object()


@pytest.mark.integration
def test_metrics_endpoint_exposes_prometheus() -> None:
    feedback_store = FakeFeedbackStore()
    set_dependencies(rag_chain=FakeRAGChain(), feedback_store=feedback_store)
    try:
        query_response = query_rag(QueryRequest(question="Can I use Rare Candy?", top_k=5))
        assert query_response.answer == "I don't know."

        feedback_response = submit_feedback(
            FeedbackRequest(
                query="Can I use Rare Candy?",
                answer="I don't know.",
                rating=1,
                model_name="gpt-4o-mini",
                latency_seconds=0.15,
            )
        )
        assert feedback_response["status"] == "success"

        health = health_check()
        assert health.status == "healthy"
    finally:
        set_dependencies()
