"""
Domain Exceptions for Pokemon TCG RAG.

Defines a typed exception hierarchy so failures across layers are
catchable and testable rather than bare exceptions.

Raise each exception at the appropriate layer:
- PokemonRAGError      : Base; never raised directly.
- IngestionError       : Document fetching, downloading, or storage failures.
- ParsingError         : PDF/HTML extraction and text-parsing failures.
- RetrievalError       : Dense, BM25, or hybrid search processing failures.
- VectorStoreError     : Qdrant connection or operation failures.
- LLMError             : LLM provider errors, timeout, or invalid responses.
- ConfigurationError   : Missing or invalid application configuration.
"""


class PokemonRAGError(Exception):
    """Base exception for the Pokemon TCG RAG system.

    All domain exceptions inherit from this class, enabling callers to
    catch every application-level error with a single ``except PokemonRAGError``.

    Attributes:
        message: Human-readable description of the failure.
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        return self.message


class IngestionError(PokemonRAGError):
    """Raised when document fetching, downloading, or raw storage fails.

    Examples: network timeout while scraping PokéGym, file system write
    error, or duplicate document detection.
    """


class ParsingError(PokemonRAGError):
    """Raised during PDF/HTML extraction and text-parsing failures.

    Examples: corrupted PDF bytes, unsupported document format, or
    failed HTML structure parsing that prevents content extraction.
    """


class RetrievalError(PokemonRAGError):
    """Raised during dense, BM25, or hybrid search processing.

    Examples: empty query after preprocessing, scorer initialization
    failure, or unexpected result schema from the vector store.
    """


class VectorStoreError(PokemonRAGError):
    """Raised on Qdrant connection or operation failures.

    Examples: gRPC timeout, collection not found, upsert failure, or
    incompatible vector dimension mismatch.
    """


class LLMError(PokemonRAGError):
    """Raised when the LLM provider returns an error or fails.

    Examples: OpenAI rate-limit (429), context-window overflow,
    malformed JSON in a structured-output response, or API key invalid.
    """


class LLMQuotaError(LLMError):
    """Raised when the configured LLM provider has no available billing quota."""


class ConfigurationError(PokemonRAGError):
    """Raised when required application configuration is missing or invalid.

    Examples: OPENAI_API_KEY not set, QDRANT_PORT out of range, or an
    unsupported ENVIRONMENT value passed at startup.
    """
