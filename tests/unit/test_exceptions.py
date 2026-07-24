"""
TASK-004 — TEST-012, TEST-013

Unit tests for the domain exception hierarchy.
"""

import pytest

from pokemon_tcg_rag.domain.exceptions import (
    ConfigurationError,
    IngestionError,
    LLMError,
    ParsingError,
    PokemonRAGError,
    RetrievalError,
    VectorStoreError,
)


# ─────────────────────────────────────────────
# TEST-012  Exception hierarchy
# ─────────────────────────────────────────────

@pytest.mark.unit
def test_exception_hierarchy() -> None:
    """TEST-012: All domain exceptions must subclass PokemonRAGError (and thus Exception)."""
    subclasses = [
        IngestionError,
        ParsingError,
        RetrievalError,
        VectorStoreError,
        LLMError,
        ConfigurationError,
    ]
    for exc_cls in subclasses:
        assert issubclass(exc_cls, PokemonRAGError), (
            f"{exc_cls.__name__} must inherit from PokemonRAGError"
        )
        assert issubclass(exc_cls, Exception), (
            f"{exc_cls.__name__} must ultimately inherit from Exception"
        )


@pytest.mark.unit
def test_base_is_pokemon_rag_error() -> None:
    """PokemonRAGError itself must inherit from Exception."""
    assert issubclass(PokemonRAGError, Exception)


# ─────────────────────────────────────────────
# TEST-013  Exceptions carry message attribute
# ─────────────────────────────────────────────

@pytest.mark.unit
def test_exceptions_carry_message() -> None:
    """TEST-013: Every exception must store and expose the message attribute."""
    exceptions_and_messages = [
        (PokemonRAGError, "base error"),
        (IngestionError, "scraping failed"),
        (ParsingError, "malformed PDF"),
        (RetrievalError, "search failed"),
        (VectorStoreError, "qdrant connection lost"),
        (LLMError, "openai 429"),
        (ConfigurationError, "missing OPENAI_API_KEY"),
    ]
    for exc_cls, msg in exceptions_and_messages:
        exc = exc_cls(msg)
        assert hasattr(exc, "message"), f"{exc_cls.__name__} must have a 'message' attribute"
        assert exc.message == msg
        assert str(exc) == msg


@pytest.mark.unit
def test_exceptions_are_catchable_as_base() -> None:
    """All domain exceptions must be catchable via PokemonRAGError."""
    for exc_cls in (IngestionError, ParsingError, RetrievalError, VectorStoreError, LLMError, ConfigurationError):
        with pytest.raises(PokemonRAGError):
            raise exc_cls("test message")


@pytest.mark.unit
def test_exceptions_are_catchable_as_exception() -> None:
    """All domain exceptions must be catchable via bare Exception."""
    for exc_cls in (IngestionError, ParsingError, RetrievalError, VectorStoreError, LLMError, ConfigurationError):
        with pytest.raises(Exception):  # noqa: B017
            raise exc_cls("test message")
