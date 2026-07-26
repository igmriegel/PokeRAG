"""
TASK-002 — TEST-003, TEST-004, TEST-005, TEST-006

Unit tests for the application Settings module.
"""

import pytest

from pokemon_tcg_rag.config.settings import Settings, get_settings


@pytest.mark.unit
def test_settings_defaults() -> None:
    """TEST-003: Settings must expose correct default values matching the brief."""
    s = Settings()

    # Environment
    assert s.ENVIRONMENT == "development"
    assert s.LOG_LEVEL == "INFO"

    # Embedding
    assert s.EMBEDDING_DIMENSION == 1024
    assert s.EMBEDDING_MODEL_PRIMARY == "BAAI/bge-large-en-v1.5"

    # Qdrant
    assert s.QDRANT_COLLECTION_NAME == "pokemon_tcg_rules"
    assert s.QDRANT_PORT == 6333

    # Retrieval
    assert s.RETRIEVAL_HYBRID_RRF_K == 60
    assert s.RETRIEVAL_TOP_K_DENSE == 10
    assert s.RETRIEVAL_TOP_K_BM25 == 10
    assert s.RETRIEVAL_FINAL_TOP_K == 5


@pytest.mark.unit
def test_postgres_uri_composition() -> None:
    """TEST-004: postgres_uri property must return a well-formed postgresql:// URI."""
    s = Settings(
        POSTGRES_USER="testuser",
        POSTGRES_PASSWORD="testpass",
        POSTGRES_HOST="db.example.com",
        POSTGRES_PORT=5433,
        POSTGRES_DB="testdb",
    )
    uri = s.postgres_uri
    assert uri == "postgresql://testuser:testpass@db.example.com:5433/testdb"
    assert uri.startswith("postgresql://")
    assert "testuser" in uri
    assert "testpass" in uri
    assert "db.example.com:5433" in uri
    assert uri.endswith("/testdb")


@pytest.mark.unit
def test_postgres_owner_uri_composition() -> None:
    """postgres_owner_uri must use the dedicated owner credentials."""
    s = Settings(
        POSTGRES_OWNER_USER="owner",
        POSTGRES_OWNER_PASSWORD="owner-pass",
        POSTGRES_HOST="db.example.com",
        POSTGRES_PORT=5433,
        POSTGRES_DB="testdb",
    )
    assert s.postgres_owner_uri == "postgresql://owner:owner-pass@db.example.com:5433/testdb"


@pytest.mark.unit
def test_postgres_runtime_and_migration_uri_composition() -> None:
    """Dedicated runtime and migration URIs must use their own credential sets."""
    s = Settings(
        POSTGRES_HOST="db.example.com",
        POSTGRES_PORT=5433,
        POSTGRES_DB="testdb",
        POSTGRES_RUNTIME_USER="runtime_user",
        POSTGRES_RUNTIME_PASSWORD="runtime_pass",
        POSTGRES_MIGRATION_USER="migrator_user",
        POSTGRES_MIGRATION_PASSWORD="migrator_pass",
    )
    assert (
        s.postgres_runtime_uri
        == "postgresql://runtime_user:runtime_pass@db.example.com:5433/testdb"
    )
    assert s.postgres_migration_uri == (
        "postgresql://migrator_user:migrator_pass@db.example.com:5433/testdb"
    )


@pytest.mark.unit
def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """TEST-005: Environment variables must override defaults."""
    monkeypatch.setenv("OPENAI_MODEL_NAME", "gpt-4o")
    monkeypatch.setenv("RETRIEVAL_FINAL_TOP_K", "8")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("ENVIRONMENT", "test")

    get_settings.cache_clear()
    s = get_settings()
    assert s.OPENAI_MODEL_NAME == "gpt-4o"
    assert s.RETRIEVAL_FINAL_TOP_K == 8
    assert s.LOG_LEVEL == "DEBUG"
    assert s.ENVIRONMENT == "test"
    get_settings.cache_clear()


@pytest.mark.unit
def test_get_settings_cached() -> None:
    """TEST-006: get_settings() must return the same instance on repeated calls (lru_cache)."""
    get_settings.cache_clear()
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2, "get_settings() must be a cached singleton (same object identity)"
    get_settings.cache_clear()


@pytest.mark.unit
def test_settings_environment_literal_includes_test(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ENVIRONMENT Literal must accept 'test' as a valid value."""
    monkeypatch.setenv("ENVIRONMENT", "test")
    s = Settings()
    assert s.ENVIRONMENT == "test"


@pytest.mark.unit
def test_settings_extra_env_vars_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings with extra='ignore' must not raise on unknown env vars."""
    monkeypatch.setenv("UNKNOWN_VAR_XYZ", "irrelevant")
    s = Settings()  # Should not raise
    assert s is not None
