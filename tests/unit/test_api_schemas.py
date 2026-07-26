"""
TASK-028 — TEST-090, TEST-091, TEST-092

Unit tests for API schemas.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from pokemon_tcg_rag.api.schemas import (
    ChunkSnippetSchema,
    CitationSchema,
    FeedbackRequest,
    QueryRequest,
    QueryResponse,
)
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
        section_title="Setup",
        card_name="Rare Candy",
        rule_type=RuleType.GENERAL_RULE,
        publication_date="2026-07-24",
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


@pytest.mark.unit
def test_query_request_validation() -> None:
    """TEST-090: query request must reject empty questions."""
    with pytest.raises(ValidationError):
        QueryRequest(question="   ")

    request = QueryRequest(question="Can I use Rare Candy?")
    assert request.top_k == 5


@pytest.mark.unit
def test_query_request_metadata_filters_normalization() -> None:
    """Query metadata filters must drop unsupported keys and blanks."""
    request = QueryRequest(
        question="Can I use Rare Candy?",
        metadata_filters={
            "source": "  rulebook_pdf  ",
            "ignored": "value",
            "card_name": "  ",
        },
    )
    assert request.metadata_filters == {"source": "rulebook_pdf"}
    assert (
        QueryRequest(
            question="Can I use Rare Candy?", metadata_filters=None
        ).metadata_filters
        is None
    )


@pytest.mark.unit
def test_answer_response_maps_to_schema() -> None:
    """TEST-091: AnswerResponse must map cleanly into QueryResponse."""
    response = QueryResponse.from_answer_response(_answer_response())

    assert response.query_id == ""
    assert response.query == "Can I use Rare Candy?"
    assert response.rewritten_query == "Pokemon TCG Rare Candy legality"
    assert response.citations[0].document_title == "Official Rulebook"
    assert response.retrieved_chunks[0].chunk_id == "chunk-1"
    assert response.retrieved_chunks[0].source == DocumentSource.RULEBOOK_PDF.value


@pytest.mark.unit
def test_schema_helpers_normalize_and_truncate() -> None:
    """Schema helpers must preserve citation metadata and truncate long snippets."""
    metadata = DocumentMetadata(
        source=DocumentSource.RULEBOOK_PDF,
        document_title="Official Rulebook",
        page_number=12,
        section_title="Setup",
        card_name="Rare Candy",
        rule_type=RuleType.GENERAL_RULE,
        publication_date="2026-07-24",
        source_url="https://example.com/rulebook.pdf",
    )
    citation = CitationSchema.from_metadata(metadata)
    assert citation.page_number == 12
    assert citation.card_name == "Rare Candy"
    assert citation.source_url == "https://example.com/rulebook.pdf"

    chunk = Chunk(
        chunk_id="chunk-long",
        doc_id="doc-long",
        text="x" * 400,
        token_count=100,
        metadata=metadata,
    )
    retrieved = RetrievedChunk(chunk=chunk, score=0.5, retrieval_method="dense")
    snippet = ChunkSnippetSchema.from_retrieved_chunk(retrieved)
    assert len(snippet.text) == 323
    assert snippet.text.endswith("...")

    short_chunk = Chunk(
        chunk_id="chunk-short",
        doc_id="doc-short",
        text="Rare Candy text",
        token_count=3,
        metadata=metadata,
    )
    short_snippet = ChunkSnippetSchema.from_retrieved_chunk(
        RetrievedChunk(chunk=short_chunk, score=0.75, retrieval_method="bm25")
    )
    assert short_snippet.text == "Rare Candy text"
    assert short_snippet.retrieval_method == "bm25"


@pytest.mark.unit
def test_feedback_request_rating_bounds() -> None:
    """TEST-092: feedback rating must be limited to +/- 1."""
    with pytest.raises(ValidationError):
        FeedbackRequest(
            query_id="qid-1",
            query="q",
            answer="a",
            rating=0,
            model_name="gpt-4o-mini",
            latency_seconds=0.1,
        )

    valid = FeedbackRequest(
        query_id="qid-1",
        query="q",
        answer="a",
        rating=1,
        model_name="gpt-4o-mini",
        latency_seconds=0.1,
    )
    assert valid.rating == 1
