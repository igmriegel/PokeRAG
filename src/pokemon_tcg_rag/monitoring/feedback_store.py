"""
Application-facing feedback store service.
"""

from __future__ import annotations

import uuid

from pokemon_tcg_rag.domain.models import FeedbackRecord
from pokemon_tcg_rag.monitoring.tracing import traced_span
from pokemon_tcg_rag.storage.relational_db import RelationalDatabase


class FeedbackStore:
    """Validate, persist, and return feedback records."""

    def __init__(self, db: RelationalDatabase) -> None:
        self.db = db

    def submit_feedback(
        self,
        query_id: str,
        query: str,
        answer: str,
        rating: int,
        comment: str | None,
        model_name: str,
        latency: float,
    ) -> FeedbackRecord:
        """Build and persist a feedback record."""
        with traced_span(
            "feedback.persist",
            attributes={
                "feedback.rating": rating,
                "feedback.has_comment": bool(comment and comment.strip()),
                "feedback.comment_length": len(comment.strip())
                if comment and comment.strip()
                else 0,
            },
        ):
            normalized_comment = comment.strip() if comment else None
            if normalized_comment:
                normalized_comment = normalized_comment[:1000]
            record = FeedbackRecord(
                feedback_id=f"fb_{uuid.uuid4().hex[:10]}",
                query_id=query_id,
                query=query,
                answer=answer,
                rating=rating,
                comment=normalized_comment,
                model_name=model_name,
                latency_seconds=latency,
            )
            stored = self.db.save_feedback(record)
            return stored
