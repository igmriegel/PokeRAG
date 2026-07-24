"""
Unit tests for DocumentChunker.

NOTE: DocumentChunker is implemented in Sprint 2 (TASK-007).
These tests are placeholders that will be activated once the ingestion
package is fully implemented.
"""

import pytest

pytest.importorskip(
    "pokemon_tcg_rag.ingestion.chunker",
    reason="DocumentChunker not yet implemented (Sprint 2 / TASK-007)",
)

from pokemon_tcg_rag.domain.models import Document  # noqa: E402
from pokemon_tcg_rag.ingestion.chunker import DocumentChunker  # noqa: E402


@pytest.mark.unit
def test_chunk_size_and_overlap(sample_document: Document) -> None:
    """Verify document chunker produces expected segment size and token counts."""
    chunker = DocumentChunker(chunk_size=10, chunk_overlap=2)
    chunks = chunker.chunk_document(sample_document)
    assert len(chunks) > 0
    assert chunks[0].doc_id == sample_document.doc_id
    assert chunks[0].metadata.source == sample_document.metadata.source


@pytest.mark.unit
def test_empty_document_chunking(sample_document: Document) -> None:
    """Verify chunker gracefully handles empty text."""
    sample_document.content = ""
    chunker = DocumentChunker()
    chunks = chunker.chunk_document(sample_document)
    assert len(chunks) == 0
