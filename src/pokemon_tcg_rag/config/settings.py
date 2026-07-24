"""
Application Pydantic Settings management.

Centralizes all configuration in a pydantic-settings Settings class loaded
from .env, exposing OpenAI, embeddings, Qdrant, Postgres, retrieval, and path
settings plus a postgres_uri property and a cached get_settings() accessor.
No hardcoded config should exist anywhere else in the codebase.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global settings for Pokemon TCG RAG application."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Environment
    ENVIRONMENT: Literal["development", "staging", "production", "test"] = "development"
    LOG_LEVEL: str = "INFO"

    # API Authentication
    API_AUTH_ENABLED: bool = True
    API_AUTH_SECRET: str = ""
    API_AUTH_ISSUER: str = "poketcg-rag"
    API_AUTH_AUDIENCE: str = "poketcg-rag-api"
    API_AUTH_ALGORITHM: str = "HS256"
    API_AUTH_TOKEN_LIFETIME_SECONDS: int = 3600
    API_MAX_BODY_BYTES: int = 16384
    API_RATE_LIMIT_PER_MINUTE: int = 120
    API_MAX_CONCURRENT_REQUESTS: int = 20
    API_PROVIDER_TIMEOUT_SECONDS: float = 30.0
    API_PROVIDER_MAX_RETRIES: int = 2
    API_PROVIDER_CIRCUIT_BREAKER_THRESHOLD: int = 3
    API_PROVIDER_CIRCUIT_BREAKER_RESET_SECONDS: int = 60
    API_CORS_ALLOWED_ORIGINS: str = "http://localhost:8501,http://127.0.0.1:8501"
    API_FEEDBACK_MAX_AGE_SECONDS: int = 86400

    # OpenAI API Configuration
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL_NAME: str = "gpt-4o-mini"
    OPENAI_TEMPERATURE: float = 0.0

    # Embedding Models
    EMBEDDING_MODEL_PRIMARY: str = "BAAI/bge-large-en-v1.5"
    EMBEDDING_MODEL_SECONDARY: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1024

    # Vector DB (Qdrant)
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_GRPC_PORT: int = 6334
    QDRANT_COLLECTION_NAME: str = "pokemon_tcg_rules"
    QDRANT_API_KEY: str = ""

    # Relational Database (PostgreSQL)
    POSTGRES_USER: str = "pokemon_user"
    POSTGRES_PASSWORD: str = "pokemon_password"
    POSTGRES_DB: str = "pokemon_tcg_rag_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # Retrieval & Reranking Settings
    RETRIEVAL_TOP_K_DENSE: int = 10
    RETRIEVAL_TOP_K_BM25: int = 10
    RETRIEVAL_HYBRID_RRF_K: int = 60
    RERANKER_MODEL: str = "BAAI/bge-reranker-large"
    RETRIEVAL_FINAL_TOP_K: int = 5

    # Storage Paths
    DATA_RAW_DIR: str = "data/raw_data"
    DATA_PROCESSED_DIR: str = "data/processed"
    DATA_CHUNKS_DIR: str = "data/chunks"

    # Streamlit Interface
    STREAMLIT_SERVER_PORT: int = 8501
    STREAMLIT_SERVER_ADDRESS: str = "0.0.0.0"
    POKERAG_API_TOKEN: str = ""

    # Prometheus Monitoring
    PROMETHEUS_METRICS_PORT: int = 9090

    @property
    def postgres_uri(self) -> str:
        """Construct PostgreSQL connection URI."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings singleton loader.

    Uses lru_cache so all callers share the same Settings instance.
    Clear the cache in tests with get_settings.cache_clear() when
    monkeypatching environment variables.
    """
    return Settings()
