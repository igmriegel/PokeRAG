"""
Sample script demonstrating RAG query execution via Python SDK.
"""

from pokemon_tcg_rag.llm.rag_chain import RAGChain
from pokemon_tcg_rag.retrieval.bm25 import BM25Retriever
from pokemon_tcg_rag.retrieval.dense import DenseRetriever
from pokemon_tcg_rag.retrieval.pipeline import RetrievalPipeline
from pokemon_tcg_rag.storage.vector_db import VectorDatabase


def main() -> None:
    vdb = VectorDatabase()
    dense = DenseRetriever(vdb)
    bm25 = BM25Retriever([])
    retrieval_pipe = RetrievalPipeline(dense_retriever=dense, bm25_retriever=bm25)
    rag_chain = RAGChain(retrieval_pipeline=retrieval_pipe)

    question = "Posso evoluir um Pokémon no meu primeiro turno jogando a carta Rare Candy?"
    print(f"Pergunta: {question}")
    
    response = rag_chain.query(question)
    print("\nResposta do Juiz:")
    print(response.answer)
    
    print(f"\nTempo de resposta: {response.latency_seconds}s")
    print(f"Citações: {len(response.citations)}")

if __name__ == "__main__":
    main()
