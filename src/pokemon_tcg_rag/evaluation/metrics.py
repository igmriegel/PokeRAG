"""
Retrieval and LLM evaluation metrics.
"""

from __future__ import annotations

import math
import re
from collections.abc import Sequence
from difflib import SequenceMatcher

from pokemon_tcg_rag.domain.models import DocumentMetadata, RetrievedChunk

_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")


def calculate_recall_at_k(
    retrieved_chunks: Sequence[RetrievedChunk | str],
    ground_truth_doc_ids: Sequence[str],
    k: int,
) -> float:
    """Calculate Recall@K over retrieved chunks and known relevant document IDs."""
    if k <= 0 or not ground_truth_doc_ids:
        return 0.0
    relevant = set(_clean_strings(ground_truth_doc_ids))
    if not relevant:
        return 0.0
    top_k = _top_k_doc_ids(retrieved_chunks, k)
    hits = len(relevant.intersection(top_k))
    return hits / len(relevant)


def calculate_mrr(
    retrieved_chunks: Sequence[RetrievedChunk | str],
    ground_truth_doc_ids: Sequence[str],
) -> float:
    """Calculate Mean Reciprocal Rank for the first relevant retrieved chunk."""
    relevant = set(_clean_strings(ground_truth_doc_ids))
    if not relevant:
        return 0.0

    for rank, doc_id in enumerate(_top_k_doc_id_list(retrieved_chunks), start=1):
        if doc_id in relevant:
            return 1.0 / rank
    return 0.0


def calculate_hit_rate(
    retrieved_chunks: Sequence[RetrievedChunk | str],
    ground_truth_doc_ids: Sequence[str],
    k: int,
) -> float:
    """Return 1.0 if at least one relevant document appears in the top-k results."""
    if k <= 0 or not ground_truth_doc_ids:
        return 0.0
    relevant = set(_clean_strings(ground_truth_doc_ids))
    if not relevant:
        return 0.0
    top_k = _top_k_doc_ids(retrieved_chunks, k)
    return 1.0 if top_k.intersection(relevant) else 0.0


def calculate_faithfulness(answer: str, context_chunks: Sequence[RetrievedChunk]) -> float:
    """Score how strongly the answer is supported by the provided context."""
    answer_tokens = _token_set(answer)
    context_tokens = _token_set(" ".join(item.chunk.text for item in context_chunks))
    if not answer_tokens or not context_tokens:
        return 0.0

    overlap = answer_tokens.intersection(context_tokens)
    if not overlap:
        return 0.0

    answer_coverage = len(overlap) / len(answer_tokens)
    context_support = len(overlap) / len(context_tokens)
    return round(min(1.0, 0.5 * answer_coverage + 0.5 * context_support), 4)


def calculate_correctness(answer: str, reference_answer: str) -> float:
    """Score answer similarity against a reference answer."""
    if not answer.strip() or not reference_answer.strip():
        return 0.0
    answer_tokens = _token_set(answer)
    reference_tokens = _token_set(reference_answer)
    if not answer_tokens or not reference_tokens:
        return 0.0

    overlap = answer_tokens.intersection(reference_tokens)
    token_score = len(overlap) / len(reference_tokens)
    sequence_score = SequenceMatcher(
        None, answer.lower().strip(), reference_answer.lower().strip()
    ).ratio()
    return round(min(1.0, 0.6 * token_score + 0.4 * sequence_score), 4)


def calculate_citation_quality(
    citations: Sequence[DocumentMetadata],
    context_chunks: Sequence[RetrievedChunk],
) -> float:
    """Score whether citations map to the same sources and pages as the retrieved context."""
    if not citations:
        return 0.0
    if not context_chunks:
        return 0.0

    context_keys = {_citation_key(item.chunk.metadata) for item in context_chunks}
    matches = sum(1 for citation in citations if _citation_key(citation) in context_keys)
    return round(matches / len(citations), 4)


def calculate_completeness(answer: str, reference_answer: str) -> float:
    """Score how much of the reference answer is covered by the model answer."""
    if not answer.strip() or not reference_answer.strip():
        return 0.0
    answer_tokens = _token_set(answer)
    reference_tokens = _token_set(reference_answer)
    if not reference_tokens:
        return 0.0
    overlap = answer_tokens.intersection(reference_tokens)
    return round(len(overlap) / len(reference_tokens), 4)


def _top_k_doc_ids(retrieved_chunks: Sequence[RetrievedChunk | str], k: int) -> set[str]:
    doc_ids: set[str] = set()
    for item in retrieved_chunks[:k]:
        doc_id = _extract_doc_id(item)
        if doc_id:
            doc_ids.add(doc_id)
    return doc_ids


def _top_k_doc_id_list(retrieved_chunks: Sequence[RetrievedChunk | str]) -> list[str]:
    doc_ids: list[str] = []
    for item in retrieved_chunks:
        doc_id = _extract_doc_id(item)
        if doc_id:
            doc_ids.append(doc_id)
    return doc_ids


def _extract_doc_id(item: RetrievedChunk | str) -> str | None:
    if isinstance(item, str):
        cleaned = item.strip()
        return cleaned or None
    doc_id = item.chunk.doc_id.strip()
    return doc_id or None


def _clean_strings(values: Sequence[str]) -> list[str]:
    return [value.strip() for value in values if value and value.strip()]


def _token_set(text: str) -> set[str]:
    return {match.group(0).lower() for match in _TOKEN_PATTERN.finditer(text)}


def _citation_key(metadata: DocumentMetadata) -> tuple[str, int | None]:
    return (metadata.source.value, metadata.page_number)


def _safe_mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)


def combine_scores(scores: Sequence[float]) -> float:
    """Combine scores while preserving a bounded 0-1 scale."""
    bounded = [min(1.0, max(0.0, value)) for value in scores if not math.isnan(value)]
    return _safe_mean(bounded)
