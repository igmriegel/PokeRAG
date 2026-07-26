"""
Retrieval policy helpers for safe metadata filters and MMR diversity.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from pokemon_tcg_rag.domain.models import RetrievedChunk

ALLOWED_FILTER_KEYS = {
    "source",
    "rule_type",
    "document_title",
    "card_name",
    "page_number",
}


def normalize_metadata_filters(filters: dict[str, str] | None) -> dict[str, str]:
    """Allow only bounded, typed metadata filters."""
    if not filters:
        return {}
    normalized: dict[str, str] = {}
    for key, value in filters.items():
        cleaned_key = str(key).strip()
        cleaned_value = str(value).strip()
        if cleaned_key in ALLOWED_FILTER_KEYS and cleaned_value:
            normalized[cleaned_key] = cleaned_value
    return normalized


def matches_metadata_filters(chunk: RetrievedChunk, filters: dict[str, str] | None) -> bool:
    """Return True when a chunk satisfies the allowlisted filters."""
    normalized = normalize_metadata_filters(filters)
    if not normalized:
        return True

    metadata = chunk.chunk.metadata
    for key, value in normalized.items():
        if key == "source" and metadata.source.value != value:
            return False
        if key == "rule_type" and metadata.rule_type.value != value:
            return False
        if key == "document_title" and metadata.document_title != value:
            return False
        if key == "card_name" and metadata.card_name != value:
            return False
        if key == "page_number" and str(metadata.page_number or "") != value:
            return False
    return True


def apply_mmr(
    candidates: Sequence[RetrievedChunk],
    top_k: int,
    lambda_mult: float = 0.5,
) -> list[RetrievedChunk]:
    """Apply a lexical MMR-like diversity pass to the fused candidates."""
    if top_k <= 0 or not candidates:
        return []

    normalized_lambda = min(1.0, max(0.0, lambda_mult))
    remaining = list(candidates)
    selected: list[RetrievedChunk] = []

    while remaining and len(selected) < top_k:
        if not selected:
            chosen = max(remaining, key=lambda item: item.score)
            selected.append(chosen)
            remaining.remove(chosen)
            continue

        scored = [
            (
                item.score * normalized_lambda
                - _max_similarity(item.chunk.text, [picked.chunk.text for picked in selected])
                * (1.0 - normalized_lambda),
                item,
            )
            for item in remaining
        ]
        _, chosen = max(scored, key=lambda pair: pair[0])
        selected.append(chosen)
        remaining.remove(chosen)

    return selected


def _max_similarity(candidate: str, selected_texts: Sequence[str]) -> float:
    candidate_tokens = set(re.findall(r"[A-Za-z0-9]+", candidate.lower()))
    if not candidate_tokens:
        return 0.0
    best = 0.0
    for text in selected_texts:
        selected_tokens = set(re.findall(r"[A-Za-z0-9]+", text.lower()))
        if not selected_tokens:
            continue
        overlap = len(candidate_tokens & selected_tokens)
        union = len(candidate_tokens | selected_tokens)
        if union:
            best = max(best, overlap / union)
    return best
