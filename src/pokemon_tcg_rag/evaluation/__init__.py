"""
Evaluation package for benchmark dataset loading, retrieval metrics, and LLM output evaluation.
"""

from pokemon_tcg_rag.evaluation.dataset import EvaluationDatasetLoader
from pokemon_tcg_rag.evaluation.evaluator import RAGEvaluator
from pokemon_tcg_rag.evaluation.metrics import (
    calculate_faithfulness,
    calculate_hit_rate,
    calculate_mrr,
    calculate_recall_at_k,
)

__all__ = [
    "calculate_recall_at_k",
    "calculate_mrr",
    "calculate_hit_rate",
    "calculate_faithfulness",
    "EvaluationDatasetLoader",
    "RAGEvaluator",
]
