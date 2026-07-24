"""
Pytest global test fixtures and configuration.
"""

import sys
from pathlib import Path

import pytest

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pokemon_tcg_rag.domain.models import Chunk, Document, DocumentMetadata, DocumentSource, RuleType


@pytest.fixture
def sample_document() -> Document:
    """Fixture providing a sample Document domain object."""
    return Document(
        doc_id="doc_test_001",
        content="Rare Candy can only be played to evolve a Basic Pokemon in play. A player cannot play Rare Candy on their first turn.",
        metadata=DocumentMetadata(
            source=DocumentSource.RULEBOOK_PDF,
            document_title="Official Rulebook",
            page_number=15,
            rule_type=RuleType.GENERAL_RULE,
            card_name="Rare Candy",
        )
    )


@pytest.fixture
def sample_chunk(sample_document: Document) -> Chunk:
    """Fixture providing a sample Chunk domain object."""
    return Chunk(
        chunk_id="chunk_test_001",
        document_id=sample_document.doc_id,
        text=sample_document.content,
        token_count=24,
        metadata=sample_document.metadata,
        embedding=[0.1] * 1024
    )
