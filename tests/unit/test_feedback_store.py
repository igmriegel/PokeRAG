"""
TASK-027 — TEST-087, TEST-088, TEST-089

Unit tests for the feedback store service.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from pokemon_tcg_rag.domain.models import FeedbackRecord
from pokemon_tcg_rag.monitoring.feedback_store import FeedbackStore


class FakeDB:
    def __init__(self) -> None:
        self.saved = []

    def save_feedback(self, record: FeedbackRecord) -> FeedbackRecord:
        self.saved.append(record)
        return record


@pytest.mark.unit
def test_submit_feedback_persists() -> None:
    """TEST-087: submit_feedback must persist through the database layer."""
    db = FakeDB()
    store = FeedbackStore(db=db)

    record = store.submit_feedback(
        query="q",
        answer="a",
        rating=1,
        comment="ok",
        model_name="gpt-4o-mini",
        latency=0.2,
    )

    assert len(db.saved) == 1
    assert record == db.saved[0]


@pytest.mark.unit
def test_invalid_rating_rejected() -> None:
    """TEST-088: invalid ratings must be rejected by the record model."""
    store = FeedbackStore(db=FakeDB())

    with pytest.raises(ValidationError):
        store.submit_feedback("q", "a", 0, None, "gpt-4o-mini", 0.1)


@pytest.mark.unit
def test_returns_feedback_record() -> None:
    """TEST-089: submit_feedback must return a feedback record."""
    db = FakeDB()
    store = FeedbackStore(db=db)

    record = store.submit_feedback("q", "a", -1, None, "gpt-4o-mini", 0.1)

    assert isinstance(record, FeedbackRecord)
    assert record.rating == -1
