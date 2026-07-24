"""
TASK-026 — TEST-084, TEST-085, TEST-086

Unit tests for the relational feedback database.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError

from pokemon_tcg_rag.domain.models import FeedbackRecord
from pokemon_tcg_rag.storage.relational_db import FeedbackORM, RelationalDatabase


@pytest.fixture
def sqlite_db() -> RelationalDatabase:
    engine = create_engine("sqlite:///:memory:")
    db = RelationalDatabase(engine=engine)
    return db


def _record(rating: int = 1) -> FeedbackRecord:
    return FeedbackRecord(
        feedback_id="fb_001",
        query="Can I use Rare Candy?",
        answer="Yes",
        rating=rating,
        comment="good",
        model_name="gpt-4o-mini",
        latency_seconds=0.5,
        created_at=datetime.now(UTC),
    )


@pytest.mark.unit
def test_init_db_creates_table(sqlite_db: RelationalDatabase) -> None:
    """TEST-084: init_db must create the feedback table idempotently."""
    sqlite_db.init_db()
    inspector = inspect(sqlite_db.engine)
    assert "user_feedback" in inspector.get_table_names()
    sqlite_db.init_db()


@pytest.mark.unit
def test_save_feedback_persists_row(sqlite_db: RelationalDatabase) -> None:
    """TEST-085: save_feedback must persist a row with all fields."""
    sqlite_db.init_db()
    sqlite_db.save_feedback(_record())

    session = sqlite_db.SessionLocal()
    try:
        row = session.get(FeedbackORM, "fb_001")
        assert row is not None
        assert row.query == "Can I use Rare Candy?"
        assert row.rating == 1
        assert row.latency_seconds == pytest.approx(0.5)
    finally:
        session.close()


@pytest.mark.unit
def test_rating_column_constraint(sqlite_db: RelationalDatabase) -> None:
    """TEST-086: database must reject ratings outside {-1, 1}."""
    sqlite_db.init_db()
    session = sqlite_db.SessionLocal()
    try:
        session.add(
            FeedbackORM(
                feedback_id="fb_bad",
                query="q",
                answer="a",
                rating=2,
                comment=None,
                model_name="gpt-4o-mini",
                latency_seconds=0.1,
                created_at=datetime.now(UTC),
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
    finally:
        session.rollback()
        session.close()
