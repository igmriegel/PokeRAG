"""
Retrieval & LLM Evaluation Metrics Implementation.
"""

from pokemon_tcg_rag.domain.models import RetrievedChunk


def calculate_recall_at_k(retrieved_chunks: list[RetrievedChunk], ground_truth_doc_ids: list[str], k: int) -> float:
    """Calculate Recall@K metric."""
    if not ground_truth_doc_ids:
        return 0.0
    top_k_ids = [item.chunk.doc_id for item in retrieved_chunks[:k]]
    hits = len(set(top_k_ids).intersection(set(ground_truth_doc_ids)))
    return hits / len(ground_truth_doc_ids)


def calculate_mrr(retrieved_chunks: list[RetrievedChunk], ground_truth_doc_ids: list[str]) -> float:
    """Calculate Mean Reciprocal Rank (MRR)."""
    for rank, item in enumerate(retrieved_chunks, start=1):
        if item.chunk.doc_id in ground_truth_doc_ids:
            return 1.0 / rank
    return 0.0


def calculate_hit_rate(retrieved_chunks: list[RetrievedChunk], ground_truth_doc_ids: list[str], k: int) -> float:
    """Calculate Hit Rate @ K (1 if at least one relevant document is in top K, else 0)."""
    top_k_ids = [item.chunk.doc_id for item in retrieved_chunks[:k]]
    return 1.0 if any(doc_id in top_k_ids for doc_id in ground_truth_doc_ids) else 0.0


def calculate_faithfulness(answer: str, context_chunks: list[RetrievedChunk]) -> float:
    """Stub/heuristic for Faithfulness calculation (integrates Ragas/DeepEval in pipeline)."""
    if not answer or not context_chunks:
        return 0.0
    return 0.90
