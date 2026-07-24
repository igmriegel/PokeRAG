"""
TASK-030 — TEST-097, TEST-098, TEST-099

Unit tests for the Streamlit application helpers.
"""

from __future__ import annotations

from pokemon_tcg_rag.ui.streamlit_app import (
    build_feedback_payload,
    render_answer,
)


def test_render_answer_helper() -> None:
    """TEST-097: render helper must summarize the response."""
    summary = render_answer(
        {
            "query_id": "qid-1",
            "answer": "Yes.",
            "rewritten_query": "Pokemon TCG Rare Candy legality",
            "citations": [{"document_title": "Official Rulebook"}],
            "retrieved_chunks": [{"text": "chunk text"}],
            "latency_seconds": 0.42,
            "model_name": "gpt-4o-mini",
        }
    )

    assert summary["answer"] == "Yes."
    assert summary["metrics"]["retrieved_count"] == 1
    assert summary["citations"][0]["document_title"] == "Official Rulebook"


def test_feedback_payload_built() -> None:
    """TEST-098: feedback payload must include the key API fields."""
    payload = build_feedback_payload("qid-1", "q", "a", 1, "gpt-4o-mini", 0.5, "comment")

    assert payload["rating"] == 1
    assert payload["query_id"] == "qid-1"
    assert payload["comment"] == "comment"
    assert payload["latency_seconds"] == 0.5


def test_sources_and_metrics_displayed() -> None:
    """TEST-099: response summary must include sources and metrics."""
    summary = render_answer(
        {
            "answer": "Yes.",
            "citations": [{"document_title": "Official Rulebook", "source": "rulebook_pdf"}],
            "retrieved_chunks": [{"text": "chunk text", "score": 0.9, "retrieval_method": "dense"}],
            "latency_seconds": 1.0,
            "model_name": "gpt-4o-mini",
        }
    )

    assert summary["metrics"]["model_name"] == "gpt-4o-mini"
    assert summary["metrics"]["latency_seconds"] == 1.0
    assert summary["chunks"][0]["retrieval_method"] == "dense"
