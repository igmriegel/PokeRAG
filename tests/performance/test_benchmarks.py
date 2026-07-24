"""
Performance and latency benchmarks.
"""

import time
import pytest
from pokemon_tcg_rag.domain.models import Chunk, DocumentMetadata, DocumentSource, RuleType
from pokemon_tcg_rag.retrieval.bm25 import BM25Retriever


@pytest.mark.performance
def test_bm25_retrieval_speed_benchmark() -> None:
    # Benchmark indexing speed over 1,000 synthetic chunks
    chunks = [
        Chunk(
            chunk_id=f"c_{i}",
            doc_id=f"d_{i}",
            text=f"Sample Pokemon TCG rule document number {i} regarding evolution and energy attachment.",
            token_count=12,
            metadata=DocumentMetadata(source=DocumentSource.RULEBOOK_PDF, document_title="Rulebook", rule_type=RuleType.GENERAL_RULE)
        ) for i in range(1000)
    ]
    start = time.time()
    bm25 = BM25Retriever(chunks)
    index_time = time.time() - start
    assert index_time < 2.0  # Index 1000 chunks under 2 seconds

    start = time.time()
    results = bm25.retrieve("energy attachment rules", top_k=10)
    search_time = time.time() - start
    assert search_time < 0.1  # Search under 100ms
    assert len(results) == 10
