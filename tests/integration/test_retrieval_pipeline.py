"""
Integration tests for Hybrid Retrieval Pipeline.
"""

import pytest
from pokemon_tcg_rag.domain.models import Chunk, DocumentMetadata, DocumentSource, RuleType
from pokemon_tcg_rag.retrieval.bm25 import BM25Retriever


@pytest.mark.integration
def test_bm25_retrieval_integration() -> None:
    chunks = [
        Chunk(
            chunk_id="c1",
            doc_id="d1",
            text="Rare Candy allows a player to evolve a Basic Pokemon directly to Stage 2.",
            token_count=14,
            metadata=DocumentMetadata(source=DocumentSource.RULEBOOK_PDF, document_title="Rulebook", rule_type=RuleType.GENERAL_RULE)
        ),
        Chunk(
            chunk_id="c2",
            doc_id="d2",
            text="Mega Evolution rule change: your turn does not end when playing Mega Evolution.",
            token_count=13,
            metadata=DocumentMetadata(source=DocumentSource.MEGA_RULES_HTML, document_title="Mega Rules", rule_type=RuleType.MECHANIC_RULE)
        )
    ]
    bm25 = BM25Retriever(chunks)
    results = bm25.retrieve("Rare Candy evolution", top_k=1)
    assert len(results) == 1
    assert results[0].chunk.chunk_id == "c1"
