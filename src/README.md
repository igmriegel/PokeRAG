# Source Code Directory (`src/`)

This directory contains the complete source code for the **Pokemon TCG RAG Expert System**, organized strictly under the `pokemon_tcg_rag` package following Clean Architecture and Domain-Driven Design (DDD) principles.

## Package Architecture

```
src/pokemon_tcg_rag/
├── config/       # Environment variables, Pydantic settings & application constants
├── domain/       # Core domain entities, value objects, and domain exceptions
├── ingestion/    # Web crawler, PDF parsers, normalizer, chunker, ingestion pipeline
├── storage/      # Qdrant Vector DB client & Postgres Relational DB persistence
├── retrieval/    # Dense, BM25, Hybrid search, Reranking, and Query Rewriting
├── llm/          # LLM client abstractions, prompt templates, RAG chain
├── evaluation/   # Retrieval (Recall@K, MRR) & LLM evaluation (Faithfulness, Correctness)
├── monitoring/   # Metrics collection, structlog setup, feedback database store
├── api/          # FastAPI REST endpoints, OpenAPI schemas, dependency injection
└── ui/           # Streamlit web application with source citation & feedback collection
```
