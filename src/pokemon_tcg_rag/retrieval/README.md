# Retrieval Module (`retrieval/`)

This directory contains retrieval strategies and candidate ranking components:
- `dense.py`: Dense vector search using sentence-transformers and Qdrant.
- `bm25.py`: Lexical keyword search using BM25Okapi.
- `hybrid.py`: Hybrid search using Reciprocal Rank Fusion (RRF).
- `reranker.py`: Deep learning cross-encoder re-ranker (`BAAI/bge-reranker-large`).
- `query_rewriter.py`: LLM-based user query expansion and normalization.
- `pipeline.py`: Unified orchestrator for multi-stage retrieval.
