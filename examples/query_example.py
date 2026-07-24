"""
Programmatic example for running a RAG query from Python.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from pokemon_tcg_rag.llm.rag_chain import RAGChain
from pokemon_tcg_rag.retrieval.bm25 import BM25Retriever
from pokemon_tcg_rag.retrieval.dense import DenseRetriever
from pokemon_tcg_rag.retrieval.pipeline import RetrievalPipeline
from pokemon_tcg_rag.storage.vector_db import VectorDatabase

DEFAULT_QUESTION = "Posso evoluir um Pokémon no meu primeiro turno usando Rare Candy?"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a sample Pokemon TCG RAG query")
    parser.add_argument("--question", default=DEFAULT_QUESTION)
    return parser


def build_rag_chain() -> RAGChain:
    vector_db = VectorDatabase()
    dense = DenseRetriever(vector_db)
    bm25 = BM25Retriever([])
    retrieval_pipeline = RetrievalPipeline(dense_retriever=dense, bm25_retriever=bm25)
    return RAGChain(retrieval_pipeline=retrieval_pipeline)


def main(
    argv: Sequence[str] | None = None,
    *,
    rag_chain: RAGChain | None = None,
    question: str | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    active_chain = rag_chain or build_rag_chain()
    active_question = question or args.question

    print(f"Pergunta: {active_question}")
    response = active_chain.query(active_question)
    print("\nResposta do Juiz:")
    print(response.answer)
    print(f"\nQuery reformulada: {response.rewritten_query or active_question}")
    print(f"Tempo de resposta: {response.latency_seconds:.3f}s")
    print("Citações:")
    for citation in response.citations:
        page_suffix = f" p. {citation.page_number}" if citation.page_number else ""
        print(f"- {citation.document_title} ({citation.source.value}){page_suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
