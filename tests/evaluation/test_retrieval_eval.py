"""
TASK-033 — Retrieval metrics tests.
"""

from __future__ import annotations

import pytest

from pokemon_tcg_rag.domain.models import (
    Chunk,
    DocumentMetadata,
    DocumentSource,
    RetrievedChunk,
    RuleType,
)
from pokemon_tcg_rag.evaluation.metrics import (
    calculate_hit_rate,
    calculate_mrr,
    calculate_recall_at_k,
)


def _retrieved(doc_id: str, score: float) -> RetrievedChunk:
    chunk = Chunk(
        chunk_id=f"chunk-{doc_id}",
        doc_id=doc_id,
        text=f"content for {doc_id}",
        token_count=3,
        metadata=DocumentMetadata(
            source=DocumentSource.RULEBOOK_PDF,
            document_title="Rulebook",
            rule_type=RuleType.GENERAL_RULE,
        ),
    )
    return RetrievedChunk(chunk=chunk, score=score, retrieval_method="hybrid")


@pytest.mark.evaluation
def test_recall_at_k_value() -> None:
    retrieved = [_retrieved("doc_a", 0.95), _retrieved("doc_b", 0.9), _retrieved("doc_c", 0.8)]

    score = calculate_recall_at_k(retrieved, ["doc_a", "doc_c"], k=2)

    assert score == pytest.approx(0.5)


@pytest.mark.evaluation
def test_mrr_value() -> None:
    retrieved = [_retrieved("doc_x", 0.95), _retrieved("doc_b", 0.9), _retrieved("doc_c", 0.8)]

    score = calculate_mrr(retrieved, ["doc_c", "doc_z"])

    assert score == pytest.approx(1 / 3)


@pytest.mark.evaluation
def test_hit_rate_value() -> None:
    retrieved = [_retrieved("doc_x", 0.95), _retrieved("doc_b", 0.9), _retrieved("doc_c", 0.8)]

    score = calculate_hit_rate(retrieved, ["doc_c"], k=3)

    assert score == pytest.approx(1.0)


@pytest.mark.evaluation
def test_metrics_handle_empty() -> None:
    assert calculate_recall_at_k([], [], k=5) == 0.0
    assert calculate_mrr([], []) == 0.0
    assert calculate_hit_rate([], [], k=5) == 0.0
