"""
Unit tests for DocumentNormalizer and Parsers.

NOTE: DocumentNormalizer is implemented in Sprint 2 (TASK-008).
These tests are placeholders that will be activated once the ingestion
package is fully implemented.
"""

import pytest

pytest.importorskip(
    "pokemon_tcg_rag.ingestion.normalizer",
    reason="DocumentNormalizer not yet implemented (Sprint 2 / TASK-008)",
)

from pokemon_tcg_rag.domain.models import Document, DocumentMetadata, DocumentSource  # noqa: E402
from pokemon_tcg_rag.ingestion.normalizer import DocumentNormalizer  # noqa: E402


@pytest.mark.unit
def test_normalizer_replaces_pokemon_accent() -> None:
    doc = Document(
        doc_id="test_norm",
        content="Pokémon rules and Pokémon TCG errata\n\n\n\nSection 1",
        metadata=DocumentMetadata(source=DocumentSource.RULEBOOK_PDF, document_title="Test")
    )
    normalizer = DocumentNormalizer()
    normalized = normalizer.normalize(doc)
    assert "Pokémon" not in normalized.content
    assert "Pokemon" in normalized.content
    assert "\n\n\n" not in normalized.content
