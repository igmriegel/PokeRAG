"""
TASK-013 — TEST-038, TEST-039, TEST-040, TEST-041, TEST-042, TEST-043

Unit tests for the document chunker.
"""

from __future__ import annotations

import pytest

from pokemon_tcg_rag.domain.models import Document, DocumentMetadata, DocumentSource, RuleType
from pokemon_tcg_rag.ingestion.chunker import DocumentChunker


def _make_document(
    content: str,
    source: DocumentSource = DocumentSource.RULEBOOK_PDF,
) -> Document:
    return Document(
        doc_id="doc-001",
        content=content,
        metadata=DocumentMetadata(
            source=source,
            document_title="Rulebook",
            section_title="Setup",
            rule_type=RuleType.GENERAL_RULE,
        ),
    )


@pytest.mark.unit
def test_chunk_size_respected() -> None:
    """TEST-038: chunks must not exceed the configured token size."""
    document = _make_document(" ".join(f"token{i}" for i in range(20)))

    chunks = DocumentChunker(chunk_size=5, chunk_overlap=1).chunk_document(document)

    assert chunks
    assert all(chunk.token_count <= 5 for chunk in chunks)


@pytest.mark.unit
def test_overlap_applied() -> None:
    """TEST-039: consecutive chunks must overlap by the configured amount."""
    document = _make_document(" ".join(f"token{i}" for i in range(12)))

    chunks = DocumentChunker(chunk_size=5, chunk_overlap=2).chunk_document(document)

    assert len(chunks) == 4
    assert chunks[0].text.split()[-2:] == chunks[1].text.split()[:2]


@pytest.mark.unit
def test_metadata_propagated() -> None:
    """TEST-040: chunk metadata must be copied from the source document."""
    document = _make_document("one two three")

    chunk = DocumentChunker(chunk_size=5, chunk_overlap=1).chunk_document(document)[0]

    assert chunk.metadata == document.metadata
    assert chunk.doc_id == document.doc_id
    assert chunk.chunk_id == "doc-001#0"


@pytest.mark.unit
def test_empty_document() -> None:
    """TEST-041: empty documents should yield no chunks."""
    document = _make_document("placeholder")
    document.content = ""

    chunks = DocumentChunker().chunk_document(document)

    assert chunks == []


@pytest.mark.unit
def test_pokegym_single_chunk() -> None:
    """TEST-042: Pokegym rulings must stay as a single chunk."""
    document = _make_document(
        "Question: Can I use Rare Candy? Answer: Yes, on your turn.",
        source=DocumentSource.POKEGYM,
    )

    chunks = DocumentChunker(chunk_size=3, chunk_overlap=1).chunk_document(document)

    assert len(chunks) == 1
    assert chunks[0].token_count == len(document.content.split())


@pytest.mark.unit
def test_unicode_and_long_paragraph() -> None:
    """TEST-043: unicode text and long paragraphs should split deterministically."""
    document = _make_document("Pokémon " + " ".join(["ﬁeld"] * 25))

    chunks = DocumentChunker(chunk_size=8, chunk_overlap=2).chunk_document(document)

    assert len(chunks) >= 3
    assert chunks[0].text.startswith("Pokémon")
    assert all(chunk.token_count <= 8 for chunk in chunks)
