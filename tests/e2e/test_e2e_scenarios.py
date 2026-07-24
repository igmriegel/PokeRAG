"""
End-to-End User Scenarios Test Suite.
"""

from __future__ import annotations

import pytest

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


class FakeFeedbackStore:
    def submit_feedback(self, **kwargs: object) -> object:
        return kwargs


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
        query="Can Rare Candy evolve a Pokemon on Turn 1?",
        rewritten_query="Pokemon TCG Rare Candy legality",
        answer="Yes.",
        citations=[metadata],
        retrieved_chunks=[retrieved],
        model_name="gpt-4o-mini",
        latency_seconds=0.42,
    )


class FakeRAGChain:
    def query(self, question: str, top_k: int | None = None) -> AnswerResponse:
        response = _answer_response()
        return response.model_copy(update={"query": question})


@pytest.mark.e2e
def test_e2e_rare_candy_query() -> None:
    payload = {"question": "Can Rare Candy evolve a Pokemon on Turn 1?", "top_k": 5}
    set_dependencies(FakeRAGChain(), FakeFeedbackStore())
    try:
        response = query_rag(QueryRequest(**payload))
        assert response.answer == "Yes."
        assert response.citations
        assert response.query == payload["question"]
    finally:
        set_dependencies()


@pytest.mark.e2e
def test_e2e_feedback_submission() -> None:
    fb_payload = {
        "query": "Is Mew VMAX legal?",
        "answer": "Mew VMAX is currently rotated out of Standard format.",
        "rating": 1,
        "comment": "Accurate ban status citation.",
        "model_name": "gpt-4o-mini",
        "latency_seconds": 0.35,
    }
    set_dependencies(FakeRAGChain(), FakeFeedbackStore())
    try:
        response = submit_feedback(FeedbackRequest(**fb_payload))
        assert response["status"] == "success"
    finally:
        set_dependencies()
