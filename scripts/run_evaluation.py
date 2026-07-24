#!/usr/bin/env python3
"""
CLI script to run retrieval and LLM evaluation benchmarks.
"""

from pokemon_tcg_rag.evaluation.dataset import EvaluationDatasetLoader
from pokemon_tcg_rag.evaluation.evaluator import RAGEvaluator
from pokemon_tcg_rag.llm.rag_chain import RAGChain
from pokemon_tcg_rag.retrieval.bm25 import BM25Retriever
from pokemon_tcg_rag.retrieval.dense import DenseRetriever
from pokemon_tcg_rag.retrieval.pipeline import RetrievalPipeline
from pokemon_tcg_rag.storage.vector_db import VectorDatabase


def main() -> None:
    print("Starting RAG System Evaluation...")
    vdb = VectorDatabase()
    dense = DenseRetriever(vdb)
    bm25 = BM25Retriever([])
    retrieval_pipe = RetrievalPipeline(dense, bm25)
    rag_chain = RAGChain(retrieval_pipe)
    loader = EvaluationDatasetLoader()
    evaluator = RAGEvaluator(rag_chain, loader)

    report = evaluator.run_evaluation()
    print("=== EVALUATION REPORT ===")
    print(f"Total Test Cases      : {report.total_questions}")
    print(f"Mean Recall@5         : {report.mean_recall_at_5:.4f}")
    print(f"Mean Recall@10        : {report.mean_recall_at_10:.4f}")
    print(f"Mean MRR              : {report.mean_mrr:.4f}")
    print(f"Mean Hit Rate@5       : {report.mean_hit_rate_at_5:.4f}")

if __name__ == "__main__":
    main()
