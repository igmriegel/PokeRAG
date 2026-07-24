# TASKS_SPRINT_04 — Retrieval: Dense, BM25, Hybrid, Rerank

Granular task specs for **Sprint 4** (`SPRINT_04_RETRIEVAL`). Index:
[`TASK_INDEX.md`](./TASK_INDEX.md) · Graph: [`TASK_DEPENDENCY_GRAPH.md`](./TASK_DEPENDENCY_GRAPH.md).

**Sprint objective:** implement all four retrieval strategies (Dense, BM25, Hybrid RRF,
Hybrid+Rerank) plus the LLM client and query rewriter that feed the RAG pipeline. See
[`RetrievalPipeline.md`](../01_architecture/RetrievalPipeline.md).

---

### TASK-017 — Dense retriever

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_04_RETRIEVAL |
| **REQ covered** | REQ-006 |
| **Depends on** | TASK-014 |
| **Unblocks** | TASK-019 |
| **Files affected** | `src/pokemon_tcg_rag/retrieval/dense.py`, `src/pokemon_tcg_rag/retrieval/__init__.py`, `tests/unit/test_dense.py` |
| **Branch** | `feat/task-017-dense-retriever` |

**Description.** Implement `DenseRetriever(vector_db).retrieve(query, top_k=10)`: lazily load the
`BAAI/bge-large-en-v1.5` embedding model, encode the query to a 1024-d vector, and call
`vector_db.search_dense`, returning ranked `RetrievedChunk`s.

**Definition of Ready.** TASK-014 merged.

**Steps.**
1. Lazy `@property model` (SentenceTransformer, primary embedding from settings).
2. Encode query; call `search_dense(vector, top_k)`.
3. Default `top_k` from `RETRIEVAL_TOP_K_DENSE` (10); raise `RetrievalError` on failure.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-055 | `test_dense_returns_top_k` | unit (mocked model + db) |
| TEST-056 | `test_query_encoded_to_1024` | unit |
| TEST-057 | `test_results_ordered_by_score` | unit |

**Definition of Done.** Dense retrieval returns ≤top_k ranked chunks; ≥90% coverage.

**Acceptance criteria.** For a seeded query the top result's chunk is relevant (validated in eval, TASK-034).

**Commit message.** `feat(retrieval): dense vector retriever (TASK-017)`

---

### TASK-018 — BM25 lexical retriever

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_04_RETRIEVAL |
| **REQ covered** | REQ-007 |
| **Depends on** | TASK-013 |
| **Unblocks** | TASK-019 |
| **Files affected** | `src/pokemon_tcg_rag/retrieval/bm25.py`, `tests/unit/test_bm25.py` |
| **Branch** | `feat/task-018-bm25-retriever` |

**Description.** Implement `BM25Retriever` using `rank-bm25`: `index_chunks(chunks)` tokenizes and
builds the corpus; `retrieve(query, top_k=10)` returns scored `RetrievedChunk`s.

**Definition of Ready.** TASK-013 merged.

**Steps.**
1. Tokenize chunk texts; build `BM25Okapi` index in `index_chunks`.
2. `retrieve`: score query tokens, take top_k, wrap as `RetrievedChunk` with BM25 score.
3. Handle empty index / empty query gracefully.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-058 | `test_index_and_retrieve` | unit |
| TEST-059 | `test_keyword_match_ranks_first` | unit |
| TEST-060 | `test_empty_index_returns_empty` | unit |

**Definition of Done.** BM25 returns ranked chunks; edge cases handled; ≥90% coverage.

**Acceptance criteria.** An exact card-name query ranks the matching chunk first.

**Commit message.** `feat(retrieval): BM25 lexical retriever (TASK-018)`

---

### TASK-019 — Hybrid retriever (RRF k=60)

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_04_RETRIEVAL |
| **REQ covered** | REQ-008 |
| **Depends on** | TASK-017, TASK-018 |
| **Unblocks** | TASK-020, TASK-023 |
| **Files affected** | `src/pokemon_tcg_rag/retrieval/hybrid.py`, `tests/unit/test_hybrid.py` |
| **Branch** | `feat/task-019-hybrid-rrf` |

**Description.** Implement `HybridRetriever(dense, bm25, rrf_k=60).retrieve(query, top_k=10)`
fusing dense and BM25 rankings with **Reciprocal Rank Fusion** (`score = Σ 1/(k + rank)`).

**Definition of Ready.** TASK-017, TASK-018 merged.

**Steps.**
1. Retrieve top_k from both sub-retrievers.
2. Compute RRF score per unique chunk_id (`rrf_k` default 60 from settings).
3. Sort by fused score; return top_k `RetrievedChunk`s with the fused score.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-061 | `test_rrf_fusion_formula` | unit |
| TEST-062 | `test_dedup_across_retrievers` | unit |
| TEST-063 | `test_hybrid_beats_single_on_fixture` | unit |

**Definition of Done.** RRF fusion correct and deduplicated; ≥90% coverage.

**Acceptance criteria.** RRF scores match hand-computed values on a fixed fixture.

**Commit message.** `feat(retrieval): hybrid RRF fusion retriever (TASK-019)`

---

### TASK-020 — Cross-encoder reranker

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_04_RETRIEVAL |
| **REQ covered** | REQ-009 |
| **Depends on** | TASK-019 |
| **Unblocks** | TASK-023 |
| **Files affected** | `src/pokemon_tcg_rag/retrieval/reranker.py`, `tests/unit/test_reranker.py` |
| **Branch** | `feat/task-020-reranker` |

**Description.** Implement `BGEReranker.rerank(query, candidate_chunks, top_k=5)` using the
`BAAI/bge-reranker-large` `CrossEncoder` to re-score candidates and return the final top_k.

**Definition of Ready.** TASK-019 merged.

**Steps.**
1. Lazy `@property model` (CrossEncoder from `RERANKER_MODEL`).
2. Score each `(query, chunk.text)` pair; sort desc; take `RETRIEVAL_FINAL_TOP_K` (5).
3. Preserve chunk metadata; overwrite `score` with rerank score.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-064 | `test_rerank_returns_top_k` | unit (mocked CrossEncoder) |
| TEST-065 | `test_rerank_reorders_by_score` | unit |
| TEST-066 | `test_fewer_candidates_than_k` | unit |

**Definition of Done.** Reranker returns ≤5 reordered chunks; ≥90% coverage.

**Acceptance criteria.** Given shuffled candidates, output is sorted by cross-encoder score.

**Commit message.** `feat(retrieval): bge cross-encoder reranker (TASK-020)`

---

### TASK-021 — LLM client (OpenAI-compatible)

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_04_RETRIEVAL |
| **REQ covered** | REQ-011 |
| **Depends on** | TASK-002 |
| **Unblocks** | TASK-022, TASK-025 |
| **Files affected** | `src/pokemon_tcg_rag/llm/client.py`, `src/pokemon_tcg_rag/llm/__init__.py`, `tests/unit/test_llm_client.py` |
| **Branch** | `feat/task-021-llm-client` |

**Description.** Implement `LLMClient.generate_answer(prompt)` calling an OpenAI-compatible
Chat Completions endpoint with model `gpt-4o-mini`, temperature 0.0 (both from settings), with
retries and typed error handling.

**Definition of Ready.** TASK-002 merged.

**Steps.**
1. Init OpenAI-compatible client from `OPENAI_API_KEY` / model / temperature.
2. `generate_answer(prompt)` → completion text; retry on transient errors.
3. Raise `LLMError` on failure; never leak the API key.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-067 | `test_generate_answer_returns_text` | unit (mocked client) |
| TEST-068 | `test_temperature_and_model_from_settings` | unit |
| TEST-069 | `test_api_error_raises_llm_error` | unit |

**Definition of Done.** Client returns text with mocked API; config-driven; ≥90% coverage.

**Acceptance criteria.** No network call in unit tests; model/temperature sourced from settings.

**Commit message.** `feat(llm): openai-compatible client (TASK-021)`

---

### TASK-022 — LLM query rewriter

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_04_RETRIEVAL |
| **REQ covered** | REQ-010 |
| **Depends on** | TASK-021 |
| **Unblocks** | TASK-023 |
| **Files affected** | `src/pokemon_tcg_rag/retrieval/query_rewriter.py`, `tests/unit/test_query_rewriter.py` |
| **Branch** | `feat/task-022-query-rewriter` |

**Description.** Implement `QueryRewriter.rewrite_query(original_query)` using the LLM to expand a
vague user question into a retrieval-optimized Pokemon TCG query (e.g. "Can I use this card?" →
"Pokemon TCG card legality ruling regarding <card>"), per
[`QUERY_REWRITER`](../05_prompts/QUERY_REWRITER.md).

**Definition of Ready.** TASK-021 merged.

**Steps.**
1. Build a zero-shot rewrite prompt (domain-specific instructions).
2. Call `LLMClient.generate_answer`; sanitize/trim output.
3. Fall back to the original query if the rewrite is empty/degenerate.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-070 | `test_rewrite_expands_vague_query` | unit (mocked LLM) |
| TEST-071 | `test_fallback_to_original_on_empty` | unit |
| TEST-072 | `test_rewrite_prompt_contains_domain_hint` | unit |

**Definition of Done.** Rewriter returns an improved query or safe fallback; ≥90% coverage.

**Acceptance criteria.** A vague query is rewritten to include Pokemon TCG domain terms.

**Commit message.** `feat(retrieval): LLM query rewriter (TASK-022)`

---

## Sprint 4 Definition of Done (roll-up)

- [ ] Dense, BM25, Hybrid (RRF k=60), and Reranker all implemented and unit-tested.
- [ ] LLM client and query rewriter implemented with mocked-network tests.
- [ ] ≥90% coverage per module; Sprint 4 tasks `Done` in [`TASK_INDEX.md`](./TASK_INDEX.md).
