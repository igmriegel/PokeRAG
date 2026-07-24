"""
Comprehensive RAG System Evaluator.
"""

import logging
from pydantic import BaseModel

from pokemon_tcg_rag.evaluation.dataset import EvaluationDatasetLoader
from pokemon_tcg_rag.evaluation.metrics import calculate_hit_rate, calculate_mrr, calculate_recall_at_k
from pokemon_tcg_rag.llm.rag_chain import RAGChain

logger = logging.getLogger(__name__)


class EvaluationReport(BaseModel):
    """Aggregate evaluation report results."""
    total_questions: int
    mean_recall_at_5: float
    mean_recall_at_10: float
    mean_mrr: float
    mean_hit_rate_at_5: float


class RAGEvaluator:
    """Evaluates RAG pipeline across retrieval strategies and LLM generation quality."""

    def __init__(self, rag_chain: RAGChain, dataset_loader: EvaluationDatasetLoader) -> None:
        self.rag_chain = rag_chain
        self.dataset_loader = dataset_loader

    def run_evaluation(self) -> EvaluationReport:
        """Execute evaluation loop over all test cases."""
        test_cases = self.dataset_loader.load_dataset()
        logger.info("Executing evaluation on %d test cases...", len(test_cases))

        recalls_5, recalls_10, mrrs, hits_5 = [], [], [], []

        for case in test_cases:
            response = self.rag_chain.query(case.question)
            r5 = calculate_recall_at_k(response.retrieved_chunks, case.expected_doc_ids, k=5)
            r10 = calculate_recall_at_k(response.retrieved_chunks, case.expected_doc_ids, k=10)
            mrr = calculate_mrr(response.retrieved_chunks, case.expected_doc_ids)
            hit5 = calculate_hit_rate(response.retrieved_chunks, case.expected_doc_ids, k=5)

            recalls_5.append(r5)
            recalls_10.append(r10)
            mrrs.append(mrr)
            hits_5.append(hit5)

        total = len(test_cases)
        return EvaluationReport(
            total_questions=total,
            mean_recall_at_5=sum(recalls_5) / total if total > 0 else 0.0,
            mean_recall_at_10=sum(recalls_10) / total if total > 0 else 0.0,
            mean_mrr=sum(mrrs) / total if total > 0 else 0.0,
            mean_hit_rate_at_5=sum(hits_5) / total if total > 0 else 0.0,
        )
