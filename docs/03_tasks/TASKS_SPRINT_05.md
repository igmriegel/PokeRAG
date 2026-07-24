# TASKS_SPRINT_05 — RAG, LLM & Prompting

Granular task specs for **Sprint 5** (`SPRINT_05_RAG_LLM`). Index:
[`TASK_INDEX.md`](./TASK_INDEX.md) · Graph: [`TASK_DEPENDENCY_GRAPH.md`](./TASK_DEPENDENCY_GRAPH.md).

**Sprint objective:** assemble the end-to-end RAG chain (rewrite → hybrid → rerank → prompt →
LLM → cited answer) and the feedback persistence layer. See
[`RAGArchitecture.md`](../01_architecture/RAGArchitecture.md) and
[`PromptEngineering.md`](../01_architecture/PromptEngineering.md).

---

### TASK-023 — Retrieval pipeline orchestrator

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_05_RAG_LLM |
| **REQ covered** | REQ-008, REQ-009, REQ-010 |
| **Depends on** | TASK-019, TASK-020, TASK-022 |
| **Unblocks** | TASK-025, TASK-034 |
| **Files affected** | `src/pokemon_tcg_rag/retrieval/pipeline.py`, `tests/integration/test_retrieval_pipeline.py` |
| **Branch** | `feat/task-023-retrieval-pipeline` |

**Description.** Implement `RetrievalPipeline.execute_retrieval(raw_query, top_k=5)` chaining
query rewriting → hybrid retrieval → reranking, returning `(rewritten_query, final_chunks)`.

**Definition of Ready.** TASK-019, TASK-020, TASK-022 merged.

**Steps.**
1. Inject `QueryRewriter`, `HybridRetriever`, `BGEReranker` via constructor.
2. Rewrite query → hybrid retrieve top 10 → rerank to final top_k (5).
3. Return the rewritten query plus final ranked `RetrievedChunk`s; support toggling rewrite/rerank for experiments.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-073 | `test_pipeline_chains_stages` | integration (mocked components) |
| TEST-074 | `test_returns_rewritten_query` | integration |
| TEST-075 | `test_final_top_k_respected` | integration |

**Definition of Done.** Pipeline chains all stages and returns ≤5 chunks + rewritten query; ≥90%.

**Acceptance criteria.** Stage toggles let the evaluator compare strategies (TASK-034).

**Commit message.** `feat(retrieval): end-to-end retrieval pipeline (TASK-023)`

---

### TASK-024 — Prompt templates & Judge persona

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_05_RAG_LLM |
| **REQ covered** | REQ-011, REQ-012 |
| **Depends on** | TASK-003 |
| **Unblocks** | TASK-025 |
| **Files affected** | `src/pokemon_tcg_rag/llm/prompts.py`, `tests/unit/test_prompts.py` |
| **Branch** | `feat/task-024-prompt-templates` |

**Description.** Implement `PromptTemplateManager` with the Certified-Judge system persona,
`format_context(chunks)` (numbered, citable sources), and `build_prompt(query, chunks)` enforcing
"answer only from context; always cite; say 'I don't know' if unsupported". Provides Prompt A/B
variants for LLM evaluation. See [`SYSTEM_PROMPT`](../05_prompts/SYSTEM_PROMPT.md).

**Definition of Ready.** TASK-003 merged.

**Steps.**
1. Author the Judge system prompt (no hallucination, cite sources, refuse if unsupported).
2. `format_context`: number chunks with source/page/date for citation.
3. `build_prompt`: assemble system + context + question; bound context length.
4. Expose an alternate prompt variant (Prompt B) for experiments.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-076 | `test_context_ordering_and_numbering` | unit |
| TEST-077 | `test_prompt_contains_citation_instruction` | unit |
| TEST-078 | `test_idk_instruction_present` | unit |
| TEST-079 | `test_context_length_bounded` | unit |

**Definition of Done.** Prompts enforce grounding + citations; A/B variants available; ≥90%.

**Acceptance criteria.** Built prompt contains persona, numbered sources, and citation/refusal instructions.

**Commit message.** `feat(llm): certified-judge prompt templates (TASK-024)`

---

### TASK-025 — RAG chain

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_05_RAG_LLM |
| **REQ covered** | REQ-011, REQ-012 |
| **Depends on** | TASK-021, TASK-023, TASK-024 |
| **Unblocks** | TASK-029, TASK-031, TASK-035 |
| **Files affected** | `src/pokemon_tcg_rag/llm/rag_chain.py`, `tests/integration/test_rag_chain.py` |
| **Branch** | `feat/task-025-rag-chain` |

**Description.** Implement `RAGChain(retrieval_pipeline).query(raw_query)` → `AnswerResponse`:
retrieve context, build prompt, call the LLM, and assemble the answer with citations, source
chunks, latency, and model name.

**Definition of Ready.** TASK-021, TASK-023, TASK-024 merged.

**Steps.**
1. Call `execute_retrieval` → chunks; `build_prompt`; `LLMClient.generate_answer`.
2. Parse/attach citations from the used chunks; measure latency; record model name.
3. Return a validated `AnswerResponse`; on no context, return grounded "I don't know".

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-080 | `test_query_returns_answer_response` | integration (mocked LLM + retrieval) |
| TEST-081 | `test_answer_includes_citations` | integration |
| TEST-082 | `test_latency_and_model_recorded` | integration |
| TEST-083 | `test_no_context_returns_idk` | integration |

**Definition of Done.** `query()` returns cited `AnswerResponse` with latency/model; ≥90% coverage.

**Acceptance criteria.** Every non-empty answer carries ≥1 citation traceable to a source chunk.

**Commit message.** `feat(llm): RAG chain producing cited answers (TASK-025)`

---

### TASK-026 — Relational DB & feedback ORM

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_05_RAG_LLM |
| **REQ covered** | REQ-014 |
| **Depends on** | TASK-002, TASK-003 |
| **Unblocks** | TASK-027 |
| **Files affected** | `src/pokemon_tcg_rag/storage/relational_db.py`, `tests/unit/test_relational_db.py` |
| **Branch** | `feat/task-026-relational-db` |

**Description.** Implement `RelationalDatabase` with SQLAlchemy: `FeedbackORM` table, `init_db()`
(create tables), and `save_feedback(record)` persisting `FeedbackRecord`s to PostgreSQL
(URI from settings).

**Definition of Ready.** TASK-002, TASK-003 merged.

**Steps.**
1. Define `FeedbackORM` (id, query, answer, rating, comment, model_name, latency, created_at).
2. Engine/session from `settings.postgres_uri`; `init_db()` idempotent.
3. `save_feedback(FeedbackRecord)` → row insert; raise on error.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-084 | `test_init_db_creates_table` | unit (SQLite in-memory) |
| TEST-085 | `test_save_feedback_persists_row` | unit |
| TEST-086 | `test_rating_column_constraint` | unit |

**Definition of Done.** Feedback persists; schema created idempotently; ≥90% coverage.

**Acceptance criteria.** A saved `FeedbackRecord` is retrievable with all fields intact.

**Commit message.** `feat(storage): postgres feedback ORM and persistence (TASK-026)`

---

### TASK-027 — Feedback store service

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_05_RAG_LLM |
| **REQ covered** | REQ-014 |
| **Depends on** | TASK-026 |
| **Unblocks** | TASK-029 |
| **Files affected** | `src/pokemon_tcg_rag/monitoring/feedback_store.py`, `tests/unit/test_feedback_store.py` |
| **Branch** | `feat/task-027-feedback-store` |

**Description.** Implement `FeedbackStore(db).submit_feedback(query, answer, rating, comment,
model_name, latency)` building and persisting a `FeedbackRecord` and returning it — the
application-facing façade over the relational DB.

**Definition of Ready.** TASK-026 merged.

**Steps.**
1. Validate `rating ∈ {-1, 1}`; assemble `FeedbackRecord`.
2. Delegate persistence to `RelationalDatabase.save_feedback`.
3. Return the stored record.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-087 | `test_submit_feedback_persists` | unit (mocked db) |
| TEST-088 | `test_invalid_rating_rejected` | unit |
| TEST-089 | `test_returns_feedback_record` | unit |

**Definition of Done.** Service validates and persists feedback; ≥90% coverage.

**Acceptance criteria.** `submit_feedback` calls `save_feedback` exactly once with a valid record.

**Commit message.** `feat(monitoring): feedback store service (TASK-027)`

---

## Sprint 5 Definition of Done (roll-up)

- [ ] End-to-end RAG chain returns cited `AnswerResponse`s.
- [ ] Prompt templates enforce the Judge persona, citations, and refusal behavior.
- [ ] Feedback persists to PostgreSQL via the store service.
- [ ] ≥90% coverage per module; Sprint 5 tasks `Done` in [`TASK_INDEX.md`](./TASK_INDEX.md).
