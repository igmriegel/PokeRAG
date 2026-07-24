"""
Application-facing feedback store service.
"""

from __future__ import annotations

import uuid

from pokemon_tcg_rag.domain.models import FeedbackRecord
from pokemon_tcg_rag.storage.relational_db import RelationalDatabase


class FeedbackStore:
    """Validate, persist, and return feedback records."""

    def __init__(self, db: RelationalDatabase) -> None:
        self.db = db

    def submit_feedback(
        self,
        query: str,
        answer: str,
        rating: int,
        comment: str | None,
        model_name: str,
        latency: float,
    ) -> FeedbackRecord:
        """Build and persist a feedback record."""
        record = FeedbackRecord(
            feedback_id=f"fb_{uuid.uuid4().hex[:10]}",
            query=query,
            answer=answer,
            rating=rating,
            comment=comment,
            model_name=model_name,
            latency_seconds=latency,
        )
        stored = self.db.save_feedback(record)
        return stored
