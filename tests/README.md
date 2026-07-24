# Test Suite Directory (`tests/`)

This directory contains test suites enforcing 90%+ code coverage across unit, integration, smoke, e2e, evaluation, and benchmark performance tests.

## Test Directory Structure

- `unit/`: Unit tests for chunker, parsers, prompts, embeddings, and domain entities.
- `integration/`: Integration tests validating end-to-end ingestion, retrieval pipeline, and RAG chain.
- `smoke/`: Quick smoke tests verifying backend API health and vector DB connectivity.
- `e2e/`: End-to-end user scenario testing (e.g. Rare Candy evolution, Mew VMAX legality, Mega Evolution rules).
- `evaluation/`: Retrieval Recall@K/MRR evaluation and LLM faithfulness test suite.
- `performance/`: Benchmarks measuring search latency and memory usage under load.
