"""
TASK-018 — TEST-058, TEST-059, TEST-060

Unit tests for the BM25 retriever.
"""

from __future__ import annotations

import pytest

from pokemon_tcg_rag.domain.models import Chunk, DocumentMetadata, DocumentSource, RuleType
from pokemon_tcg_rag.retrieval.bm25 import BM25Retriever


def _make_chunk(chunk_id: str, text: str) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        doc_id=f"doc-{chunk_id}",
        text=text,
        token_count=len(text.split()),
        metadata=DocumentMetadata(
            source=DocumentSource.RULEBOOK_PDF,
            document_title="Rulebook",
            rule_type=RuleType.GENERAL_RULE,
        ),
    )


@pytest.mark.unit
def test_index_and_retrieve() -> None:
    """TEST-058: BM25 must index chunks and retrieve scored results."""
    retriever = BM25Retriever()
    retriever.index_chunks(
        [
            _make_chunk("c1", "Rare Candy allows a quick evolution"),
            _make_chunk("c2", "Mega Evolution change"),
        ]
    )

    results = retriever.retrieve("Rare Candy", top_k=2)

    assert len(results) == 2
    assert results[0].chunk.chunk_id == "c1"


@pytest.mark.unit
def test_keyword_match_ranks_first() -> None:
    """TEST-059: exact keyword matches must rank first."""
    retriever = BM25Retriever(
        [
            _make_chunk("c1", "Rare Candy"),
            _make_chunk("c2", "Potion"),
        ]
    )

    results = retriever.retrieve("Rare Candy", top_k=2)

    assert results[0].chunk.chunk_id == "c1"


@pytest.mark.unit
def test_empty_index_returns_empty() -> None:
    """TEST-060: empty queries or empty indexes must return no results."""
    retriever = BM25Retriever()

    assert retriever.retrieve("Rare Candy") == []
    retriever.index_chunks([])
    assert retriever.retrieve("Rare Candy") == []
    assert retriever.retrieve("") == []
