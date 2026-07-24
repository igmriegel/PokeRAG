"""
PostgreSQL Relational DB integration for feedback and audit logs.
"""

import logging
from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from pokemon_tcg_rag.config.settings import get_settings
from pokemon_tcg_rag.domain.models import FeedbackRecord

logger = logging.getLogger(__name__)

Base = declarative_base()


class FeedbackORM(Base):
    """SQLAlchemy model for storing user feedback and RAG metrics."""
    __tablename__ = "user_feedback"

    feedback_id = Column(String, primary_key=True)
    query = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    rating = Column(Integer, nullable=False)  # 1 or -1
    comment = Column(Text, nullable=True)
    model_name = Column(String, nullable=False)
    latency_seconds = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)


class RelationalDatabase:
    """PostgreSQL storage manager for user feedback and query audit trails."""

    def __init__(self) -> None:
        settings = get_settings()
        self.engine = create_engine(settings.postgres_uri, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def init_db(self) -> None:
        """Create database tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables initialized successfully.")
        except Exception as exc:
            logger.warning("Could not initialize relational DB tables: %s", exc)

    def save_feedback(self, record: FeedbackRecord) -> None:
        """Save feedback record to database."""
        session = self.SessionLocal()
        try:
            orm_record = FeedbackORM(
                feedback_id=record.feedback_id,
                query=record.query,
                answer=record.answer,
                rating=record.rating,
                comment=record.comment,
                model_name=record.model_name,
                latency_seconds=str(record.latency_seconds),
                created_at=record.created_at,
            )
            session.add(orm_record)
            session.commit()
        except Exception as exc:
            session.rollback()
            logger.error("Failed to save feedback record: %s", exc)
        finally:
            session.close()
