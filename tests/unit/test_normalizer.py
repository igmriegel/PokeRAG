"""
TASK-012 — TEST-034, TEST-035, TEST-036, TEST-037

Unit tests for the document normalizer.
"""

from __future__ import annotations

import hashlib

import pytest

from pokemon_tcg_rag.domain.models import Document, DocumentMetadata, DocumentSource, RuleType
from pokemon_tcg_rag.ingestion.normalizer import DocumentNormalizer


def _make_document(content: str) -> Document:
    return Document(
        doc_id="doc-001",
        content=content,
        metadata=DocumentMetadata(
            source=DocumentSource.RULEBOOK_PDF,
            document_title="Rulebook",
            page_number=7,
            section_title="Setup",
            card_name="Rare Candy",
            rule_type=RuleType.GENERAL_RULE,
            publication_date="2026-07-24",
            source_url="https://example.com/rulebook.pdf",
            checksum="old-checksum",
        ),
    )


@pytest.mark.unit
def test_whitespace_collapsed() -> None:
    """TEST-034: repeated whitespace and newlines must be collapsed."""
    document = _make_document("Rare Candy\n\n\n   can be used\t\t on your turn.")

    normalized = DocumentNormalizer().normalize(document)

    assert normalized.content == "Rare Candy\ncan be used on your turn."
    assert normalized.metadata.checksum == hashlib.sha256(normalized.content.encode("utf-8")).hexdigest()


@pytest.mark.unit
def test_dehyphenation() -> None:
    """TEST-035: line-broken hyphenated words must be merged."""
    document = _make_document("This is a long-\nterm rule explanation.")

    normalized = DocumentNormalizer().normalize(document)

    assert normalized.content == "This is a longterm rule explanation."


@pytest.mark.unit
def test_unicode_normalized() -> None:
    """TEST-036: compatibility unicode forms must be normalized with NFKC."""
    document = _make_document("Pokémon ﬁeld ＡＢＣ")

    normalized = DocumentNormalizer().normalize(document)

    assert normalized.content == "Pokémon field ABC"


@pytest.mark.unit
def test_metadata_preserved() -> None:
    """TEST-037: metadata must remain unchanged except checksum."""
    document = _make_document("Simple text.")

    normalized = DocumentNormalizer().normalize(document)

    assert normalized.doc_id == document.doc_id
    assert normalized.metadata.source == document.metadata.source
    assert normalized.metadata.document_title == document.metadata.document_title
    assert normalized.metadata.page_number == document.metadata.page_number
    assert normalized.metadata.section_title == document.metadata.section_title
    assert normalized.metadata.card_name == document.metadata.card_name
    assert normalized.metadata.rule_type == document.metadata.rule_type
    assert normalized.metadata.publication_date == document.metadata.publication_date
    assert normalized.metadata.source_url == document.metadata.source_url
    assert normalized.metadata.checksum != document.metadata.checksum
