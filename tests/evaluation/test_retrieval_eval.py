"""
Evaluation test suite for IR metrics.
"""

import pytest
from pokemon_tcg_rag.domain.models import Chunk, DocumentMetadata, DocumentSource, RetrievedChunk, RuleType
from pokemon_tcg_rag.evaluation.metrics import calculate_hit_rate, calculate_mrr, calculate_recall_at_k


@pytest.mark.evaluation
def test_recall_at_k_calculation() -> None:
    chunk1 = Chunk(chunk_id="c1", doc_id="doc_A", text="", token_count=0, metadata=DocumentMetadata(source=DocumentSource.RULEBOOK_PDF, document_title="Rulebook", rule_type=RuleType.GENERAL_RULE))
    chunk2 = Chunk(chunk_id="c2", doc_id="doc_B", text="", token_count=0, metadata=DocumentMetadata(source=DocumentSource.POKEGYM, document_title="Pokegym", rule_type=RuleType.RULING))
    retrieved = [
        RetrievedChunk(chunk=chunk1, score=0.9, retrieval_method="dense"),
        RetrievedChunk(chunk=chunk2, score=0.8, retrieval_method="dense"),
    ]
    recall = calculate_recall_at_k(retrieved, ground_truth_doc_ids=["doc_A"], k=5)
    assert recall == 1.0
    
    mrr = calculate_mrr(retrieved, ground_truth_doc_ids=["doc_A"])
    assert mrr == 1.0

    hit = calculate_hit_rate(retrieved, ground_truth_doc_ids=["doc_B"], k=5)
    assert hit == 1.0
