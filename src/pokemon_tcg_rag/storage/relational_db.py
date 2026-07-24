"""
Relational database persistence for feedback records.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from pokemon_tcg_rag.config.settings import get_settings
from pokemon_tcg_rag.domain.exceptions import PokemonRAGError
from pokemon_tcg_rag.domain.models import FeedbackRecord
from pokemon_tcg_rag.monitoring.tracing import traced_span


class Base(DeclarativeBase):
    """SQLAlchemy base class."""


class FeedbackORM(Base):
    """Feedback persistence model."""

    __tablename__ = "user_feedback"
    __table_args__ = (CheckConstraint("rating IN (-1, 1)", name="ck_user_feedback_rating_binary"),)

    feedback_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    query_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    latency_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RelationalDatabase:
    """PostgreSQL persistence manager for feedback records."""

    def __init__(self, engine: Any | None = None) -> None:
        settings = get_settings()
        self.engine = engine or create_engine(settings.postgres_runtime_uri, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)

    def init_db(self) -> None:
        """Create tables if they do not already exist."""
        Base.metadata.create_all(bind=self.engine)

    def save_feedback(self, record: FeedbackRecord) -> FeedbackRecord:
        """Persist a feedback record and return it."""
        with traced_span(
            "db.feedback.save",
            attributes={
                "db.system": "postgresql",
                "feedback.rating": record.rating,
                "feedback.has_comment": bool(record.comment),
            },
        ):
            session: Session = self.SessionLocal()
            try:
                row = FeedbackORM(
                    feedback_id=record.feedback_id,
                    query_id=record.query_id,
                    query=record.query,
                    answer=record.answer,
                    rating=record.rating,
                    comment=record.comment,
                    model_name=record.model_name,
                    latency_seconds=record.latency_seconds,
                    created_at=record.created_at,
                )
                session.add(row)
                session.commit()
                return record
            except Exception as exc:  # pragma: no cover - persistence boundary
                session.rollback()
                raise PokemonRAGError(f"Failed to save feedback: {exc}") from exc
            finally:
                session.close()
