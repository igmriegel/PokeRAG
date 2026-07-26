"""
Unit tests for retrieval policy helpers.
"""

from __future__ import annotations

from pokemon_tcg_rag.domain.models import (
    Chunk,
    DocumentMetadata,
    DocumentSource,
    RetrievedChunk,
    RuleType,
)
from pokemon_tcg_rag.retrieval.policy import (
    apply_mmr,
    matches_metadata_filters,
    normalize_metadata_filters,
)


def _chunk(
    doc_id: str, text: str, source: DocumentSource = DocumentSource.RULEBOOK_PDF
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk=Chunk(
            chunk_id=f"{doc_id}#1",
            doc_id=doc_id,
            text=text,
            token_count=len(text.split()),
            metadata=DocumentMetadata(
                source=source,
                document_title="Rulebook",
                rule_type=RuleType.GENERAL_RULE,
                card_name="Rare Candy",
                page_number=12,
            ),
        ),
        score=1.0,
        retrieval_method="hybrid_rrf",
    )


def test_normalize_metadata_filters_keeps_allowlisted_keys() -> None:
    filters = normalize_metadata_filters(
        {"source": "rulebook_pdf", "prompt": "secret", "page_number": "12", "junk": "x"}
    )

    assert filters == {"source": "rulebook_pdf", "page_number": "12"}


def test_matches_metadata_filters_uses_allowlist() -> None:
    chunk = _chunk("doc-1", "Rare Candy lets you evolve faster.")

    assert matches_metadata_filters(
        chunk, {"source": "rulebook_pdf", "page_number": "12"}
    )
    assert not matches_metadata_filters(chunk, {"source": "pokegym_rulings"})


def test_apply_mmr_prefers_diverse_results() -> None:
    first = _chunk("doc-1", "Rare Candy lets you evolve faster.")
    second = _chunk("doc-2", "Rare Candy lets you evolve faster again.")
    third = _chunk("doc-3", "A different ruling about stadium cards.")
    first.score = 0.9
    second.score = 0.99
    third.score = 0.95

    selected = apply_mmr([second, first, third], top_k=2, lambda_mult=0.3)

    assert len(selected) == 2
    assert selected[0].chunk.doc_id == "doc-2"
    assert selected[1].chunk.doc_id in {"doc-1", "doc-3"}
