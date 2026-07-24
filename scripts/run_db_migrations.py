#!/usr/bin/env python3
"""Apply the relational schema using the dedicated migration role."""

from __future__ import annotations

from pokemon_tcg_rag.config.settings import get_settings
from pokemon_tcg_rag.storage.relational_db import Base
from sqlalchemy import create_engine


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.postgres_migration_uri, pool_pre_ping=True)
    try:
        Base.metadata.create_all(bind=engine)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
