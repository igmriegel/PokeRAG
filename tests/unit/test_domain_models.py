"""
TASK-003 — TEST-007, TEST-008, TEST-009, TEST-010, TEST-011

Unit tests for domain models and enums.
"""

import json

import pytest
from pydantic import ValidationError

from pokemon_tcg_rag.domain.models import (
    AnswerResponse,
    Chunk,
    DocumentMetadata,
    DocumentSource,
    FeedbackRecord,
    RetrievedChunk,
    RuleType,
)

# ─────────────────────────────────────────────
# TEST-007  DocumentSource enum members
# ─────────────────────────────────────────────


@pytest.mark.unit
def test_document_source_enum_members() -> None:
    """TEST-007: DocumentSource must have exactly 9 members matching the brief §3."""
    expected = {
        "POKEGYM",
        "RULEBOOK_PDF",
        "TOURNAMENT_HANDBOOK_PDF",
        "ALT_PLAY_HANDBOOK_PDF",
        "DECK_LIST_GUIDE_PDF",
        "ERRATA_PDF",
        "BAN_LIST_HTML",
        "PROMO_LEGALITY_HTML",
        "MEGA_RULES_HTML",
    }
    actual = {m.name for m in DocumentSource}
    assert actual == expected, f"DocumentSource members mismatch: {actual}"
    assert len(DocumentSource) == 9


# ─────────────────────────────────────────────
# TEST-008  RuleType enum members
# ─────────────────────────────────────────────


@pytest.mark.unit
def test_rule_type_enum_members() -> None:
    """TEST-008: RuleType must have exactly 7 members matching the brief §3."""
    expected = {
        "RULING",
        "GENERAL_RULE",
        "TOURNAMENT_RULE",
        "ERRATA",
        "BAN_STATUS",
        "PROMO_STATUS",
        "MECHANIC_RULE",
    }
    actual = {m.name for m in RuleType}
    assert actual == expected, f"RuleType members mismatch: {actual}"
    assert len(RuleType) == 7


# ─────────────────────────────────────────────
# TEST-009  Chunk requires metadata
# ─────────────────────────────────────────────


@pytest.mark.unit
def test_chunk_requires_metadata() -> None:
    """TEST-009: Chunk must raise ValidationError when metadata is missing."""
    with pytest.raises(ValidationError):
        Chunk(  # type: ignore[call-arg]
            chunk_id="c1",
            doc_id="d1",
            text="Some text",
        )


@pytest.mark.unit
def test_chunk_rejects_empty_text() -> None:
    """Chunk validator must reject empty/whitespace-only text."""
    meta = DocumentMetadata(
        source=DocumentSource.RULEBOOK_PDF,
        document_title="Test Doc",
    )
    with pytest.raises(ValidationError, match="must not be empty"):
        Chunk(chunk_id="c1", doc_id="d1", text="   ", metadata=meta)


@pytest.mark.unit
def test_document_content_rejects_empty_text() -> None:
    """Document validator must reject empty content."""
    meta = DocumentMetadata(
        source=DocumentSource.RULEBOOK_PDF,
        document_title="Test Doc",
    )
    with pytest.raises(ValidationError, match="must not be empty"):
        from pokemon_tcg_rag.domain.models import Document

        Document(doc_id="d1", content="   ", metadata=meta)


@pytest.mark.unit
def test_chunk_json_serializable(sample_chunk: Chunk) -> None:
    """Chunk must serialize to JSON without error."""
    payload = sample_chunk.model_dump_json()
    parsed = json.loads(payload)
    assert parsed["chunk_id"] == "chunk_test_001"
    assert "embedding" in parsed


# ─────────────────────────────────────────────
# TEST-010  FeedbackRecord rating validation
# ─────────────────────────────────────────────


@pytest.mark.unit
def test_feedback_rating_validation() -> None:
    """TEST-010: FeedbackRecord must reject ratings outside {-1, 1}."""
    base: dict = {
        "feedback_id": "fb_001",
        "query_id": "qid_001",
        "query": "q",
        "answer": "a",
        "model_name": "gpt-4o-mini",
        "latency_seconds": 0.5,
    }

    # Valid ratings
    fb_pos = FeedbackRecord(**base, rating=1)
    assert fb_pos.rating == 1

    fb_neg = FeedbackRecord(**base, rating=-1)
    assert fb_neg.rating == -1

    # Invalid ratings
    for bad_rating in (0, 2, -2, 99):
        with pytest.raises(ValidationError, match="rating must be either"):
            FeedbackRecord(**base, rating=bad_rating)


# ─────────────────────────────────────────────
# TEST-011  RetrievedChunk has score
# ─────────────────────────────────────────────


@pytest.mark.unit
def test_retrieved_chunk_has_score(sample_chunk: Chunk) -> None:
    """TEST-011: RetrievedChunk must carry a numeric score field."""
    rc = RetrievedChunk(chunk=sample_chunk, score=0.87, retrieval_method="dense")
    assert hasattr(rc, "score")
    assert rc.score == pytest.approx(0.87)
    assert rc.retrieval_method == "dense"


@pytest.mark.unit
def test_model_alias_properties() -> None:
    """Backward-compatible alias properties must stay available."""
    meta = DocumentMetadata(
        source=DocumentSource.POKEGYM,
        document_title="Compendium",
    )
    chunk = Chunk(chunk_id="c-alias", doc_id="d-alias", text="ok", metadata=meta)
    response = AnswerResponse(
        query="test?",
        answer="yes",
        citations=[meta],
        retrieved_chunks=[RetrievedChunk(chunk=chunk, score=1.0, retrieval_method="dense")],
        model_name="gpt-4o-mini",
        latency_seconds=0.1,
    )
    assert chunk.document_id == "d-alias"
    assert len(response.chunks) == 1


@pytest.mark.unit
def test_document_metadata_defaults() -> None:
    """DocumentMetadata optional fields default to None."""
    meta = DocumentMetadata(
        source=DocumentSource.POKEGYM,
        document_title="Compendium",
    )
    assert meta.rule_type == RuleType.GENERAL_RULE
    assert meta.page_number is None
    assert meta.card_name is None


@pytest.mark.unit
def test_answer_response_json_serializable() -> None:
    """AnswerResponse must be JSON-serializable."""
    meta = DocumentMetadata(
        source=DocumentSource.RULEBOOK_PDF,
        document_title="Rulebook",
    )
    ar = AnswerResponse(
        query="test?",
        answer="yes",
        citations=[meta],
        retrieved_chunks=[],
        model_name="gpt-4o-mini",
        latency_seconds=0.1,
    )
    payload = json.loads(ar.model_dump_json())
    assert payload["answer"] == "yes"
    assert len(payload["citations"]) == 1
