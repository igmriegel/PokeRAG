"""
TASK-030 — TEST-097, TEST-098, TEST-099

Unit tests for the Streamlit application helpers.
"""

from __future__ import annotations

import pytest
import requests

from pokemon_tcg_rag.ui.streamlit_app import (
    BackendAPIError,
    build_feedback_payload,
    build_history_entry,
    fetch_answer,
    get_backend_api_url,
    render_answer,
    send_feedback,
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


def test_history_entry_is_bounded_and_sanitized() -> None:
    """TEST-172: UI history entries should be session-bound and concise."""
    summary = render_answer(
        {
            "query_id": "qid-2",
            "answer": "Yes.",
            "citations": [{"document_title": "Official Rulebook"}],
            "retrieved_chunks": [],
            "latency_seconds": 1.0,
            "model_name": "gpt-4o-mini",
        }
    )

    entry = build_history_entry("  question  ", summary)

    assert entry["question"] == "question"
    assert entry["answer"] == "Yes."
    assert entry["model_name"] == "gpt-4o-mini"
    assert entry["citations"] == ["Official Rulebook"]


def test_backend_api_url_comes_from_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    """TEST-132: the backend URL must be sourced from trusted configuration."""
    monkeypatch.setenv("POKERAG_API_URL", "http://api:8000/api/v1")

    assert get_backend_api_url() == "http://api:8000/api/v1"


@pytest.mark.parametrize("url", ["ftp://localhost:8000", "http://user:pass@localhost:8000"])
def test_backend_api_url_rejects_unsupported_values(
    monkeypatch: pytest.MonkeyPatch, url: str
) -> None:
    """Unsafe URL schemes or embedded credentials must be rejected."""
    monkeypatch.setenv("POKERAG_API_URL", url)

    with pytest.raises(ValueError):
        get_backend_api_url()


def test_fetch_answer_blocks_redirects() -> None:
    """Query traffic must not follow redirects."""
    captured: dict[str, object] = {}

    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, str]:
            return {"answer": "ok"}

    def fake_post(url: str, **kwargs: object) -> Response:
        captured["url"] = url
        captured["kwargs"] = kwargs
        return Response()

    response = fetch_answer("http://example.com/api/v1", "question", 3, post=fake_post)

    assert response["answer"] == "ok"
    assert captured["url"] == "http://example.com/api/v1/query"
    assert captured["kwargs"]["allow_redirects"] is False


def test_fetch_answer_exposes_safe_backend_detail() -> None:
    """The UI should explain actionable backend failures instead of reporting connectivity."""

    class Response:
        status_code = 503

        def raise_for_status(self) -> None:
            raise requests.HTTPError("503 Server Error")

        def json(self) -> dict[str, str]:
            return {"detail": "OpenAI API quota is unavailable."}

    with pytest.raises(BackendAPIError) as exc_info:
        fetch_answer(
            "http://example.com/api/v1",
            "question",
            3,
            post=lambda *args, **kwargs: Response(),
        )

    assert exc_info.value.status_code == 503
    assert str(exc_info.value) == "OpenAI API quota is unavailable."


def test_send_feedback_blocks_redirects() -> None:
    """Feedback submission must not follow redirects."""
    captured: dict[str, object] = {}

    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, str]:
            return {"status": "ok"}

    def fake_post(url: str, **kwargs: object) -> Response:
        captured["url"] = url
        captured["kwargs"] = kwargs
        return Response()

    response = send_feedback(
        "http://example.com/api/v1",
        "qid-1",
        "question",
        "answer",
        1,
        "gpt-4o-mini",
        0.2,
        post=fake_post,
    )

    assert response["status"] == "ok"
    assert captured["url"] == "http://example.com/api/v1/feedback"
    assert captured["kwargs"]["allow_redirects"] is False
