"""
Feedback persistence store wrapper.
"""

import uuid
from pokemon_tcg_rag.domain.models import FeedbackRecord
from pokemon_tcg_rag.monitoring.metrics_collector import MetricsCollector
from pokemon_tcg_rag.storage.relational_db import RelationalDatabase


class FeedbackStore:
    """Saves user feedback ratings (+1 / -1) to PostgreSQL and updates Prometheus counters."""

    def __init__(self, db: RelationalDatabase) -> None:
        self.db = db

    def submit_feedback(self, query: str, answer: str, rating: int, comment: str | None, model_name: str, latency: float) -> FeedbackRecord:
        """Create and store user feedback record."""
        record = FeedbackRecord(
            feedback_id=f"fb_{uuid.uuid4().hex[:10]}",
            query=query,
            answer=answer,
            rating=rating,
            comment=comment,
            model_name=model_name,
            latency_seconds=latency,
        )
        self.db.save_feedback(record)
        MetricsCollector.record_feedback(rating)
        return record
