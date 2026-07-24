"""
Domain core entities, value objects, data models, and exceptions.
"""

from pokemon_tcg_rag.domain.exceptions import (
    ConfigurationError,
    IngestionError,
    LLMError,
    ParsingError,
    PokemonRAGError,
    RetrievalError,
    VectorStoreError,
)
from pokemon_tcg_rag.domain.models import (
    AnswerResponse,
    Chunk,
    Document,
    DocumentMetadata,
    DocumentSource,
    FeedbackRecord,
    RetrievedChunk,
    RuleType,
)

__all__ = [
    # Enums
    "DocumentSource",
    "RuleType",
    # Models
    "DocumentMetadata",
    "Document",
    "Chunk",
    "RetrievedChunk",
    "AnswerResponse",
    "FeedbackRecord",
    # Exceptions
    "PokemonRAGError",
    "IngestionError",
    "ParsingError",
    "RetrievalError",
    "VectorStoreError",
    "LLMError",
    "ConfigurationError",
]
