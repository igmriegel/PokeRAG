# TASKS_SPRINT_06 — Interface: API & UI

Granular task specs for **Sprint 6** (`SPRINT_06_UI_FEEDBACK`). Index:
[`TASK_INDEX.md`](./TASK_INDEX.md) · Graph: [`TASK_DEPENDENCY_GRAPH.md`](./TASK_DEPENDENCY_GRAPH.md).

**Sprint objective:** expose the RAG system through a FastAPI service (`/query`, `/feedback`,
`/health`) and a Streamlit UI showing answer, sources, chunks, timing, model, and feedback
buttons. See [`APIContracts.md`](../01_architecture/APIContracts.md).

---

### TASK-028 — API request/response schemas

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_06_UI_FEEDBACK |
| **REQ covered** | REQ-013 |
| **Depends on** | TASK-003 |
| **Unblocks** | TASK-029 |
| **Files affected** | `src/pokemon_tcg_rag/api/schemas.py`, `src/pokemon_tcg_rag/api/__init__.py`, `tests/unit/test_api_schemas.py` |
| **Branch** | `feat/task-028-api-schemas` |

**Description.** Define the Pydantic wire schemas: `QueryRequest`, `QueryResponse` (with
`CitationSchema`, `ChunkSnippetSchema`), `FeedbackRequest`, `HealthResponse` — the stable API
contract mapping to/from domain models.

**Definition of Ready.** TASK-003 merged.

**Steps.**
1. Define request/response models with validation (non-empty query; rating ∈ {-1,1}).
2. Add `CitationSchema`, `ChunkSnippetSchema`, `HealthResponse`.
3. Provide mappers from `AnswerResponse`/`RetrievedChunk` to the response schemas.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-090 | `test_query_request_validation` | unit |
| TEST-091 | `test_answer_response_maps_to_schema` | unit |
| TEST-092 | `test_feedback_request_rating_bounds` | unit |

**Definition of Done.** Schemas validate and map cleanly from domain models; ≥90% coverage.

**Acceptance criteria.** `QueryResponse` round-trips an `AnswerResponse` with citations + chunks.

**Commit message.** `feat(api): request/response schemas (TASK-028)`

---

### TASK-029 — FastAPI routes & app

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_06_UI_FEEDBACK |
| **REQ covered** | REQ-013, REQ-014 |
| **Depends on** | TASK-025, TASK-027, TASK-028 |
| **Unblocks** | TASK-030, TASK-037, TASK-039 |
| **Files affected** | `src/pokemon_tcg_rag/api/routes.py`, `src/pokemon_tcg_rag/api/main.py`, `tests/integration/test_api_routes.py` |
| **Branch** | `feat/task-029-fastapi-routes` |

**Description.** Implement the FastAPI app: `POST /query` (RAG chain → `QueryResponse`),
`POST /feedback` (→ feedback store), `GET /health`, with dependency injection of `RAGChain` and
`FeedbackStore` via `set_dependencies`.

**Definition of Ready.** TASK-025, TASK-027, TASK-028 merged.

**Steps.**
1. `set_dependencies(rag_chain, feedback_store)`; wire router into `main.py` app.
2. `/query`: validate, call `rag_chain.query`, map to `QueryResponse`; handle errors → HTTP 4xx/5xx.
3. `/feedback`: persist via `FeedbackStore`; return 201.
4. `/health`: return service + dependency status.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-093 | `test_query_endpoint_returns_answer` | integration (TestClient, mocked chain) |
| TEST-094 | `test_feedback_endpoint_persists` | integration |
| TEST-095 | `test_health_endpoint_ok` | integration |
| TEST-096 | `test_query_error_maps_to_http_500` | integration |

**Definition of Done.** All three endpoints work via TestClient; DI wired; ≥90% coverage.

**Acceptance criteria.** `POST /query` returns a cited answer; `POST /feedback` returns 201; `GET /health` returns 200.

**Commit message.** `feat(api): query, feedback and health endpoints (TASK-029)`

---

### TASK-030 — Streamlit Web UI

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_06_UI_FEEDBACK |
| **REQ covered** | REQ-013, REQ-014 |
| **Depends on** | TASK-029 |
| **Unblocks** | TASK-039 |
| **Files affected** | `src/pokemon_tcg_rag/ui/streamlit_app.py`, `src/pokemon_tcg_rag/ui/__init__.py`, `tests/unit/test_streamlit_app.py` |
| **Branch** | `feat/task-030-streamlit-ui` |

**Description.** Build the Streamlit UI: question input → answer, cited sources, expandable used
chunks, plus latency, model name, and number of retrieved docs; 👍/👎 + optional comment posting
to `/feedback`.

**Definition of Ready.** TASK-029 merged.

**Steps.**
1. Question box → call API `/query`; render answer + citations.
2. Expanders for used chunks; show latency, model, doc count.
3. 👍/👎 buttons + comment → `POST /feedback`.
4. Factor API calls into testable functions (mock `requests`).

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-097 | `test_render_answer_helper` | unit (logic extracted) |
| TEST-098 | `test_feedback_payload_built` | unit |
| TEST-099 | `test_sources_and_metrics_displayed` | unit |

**Definition of Done.** UI renders answer/sources/metrics and posts feedback; helpers unit-tested; ≥90%.

**Acceptance criteria.** Asking a question shows answer + sources + timing + model, and feedback submits.

**Commit message.** `feat(ui): streamlit interface with sources and feedback (TASK-030)`

---

### TASK-031 — Example client script

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_06_UI_FEEDBACK |
| **REQ covered** | REQ-013 |
| **Depends on** | TASK-025 |
| **Unblocks** | — |
| **Files affected** | `examples/query_example.py`, `tests/unit/test_query_example.py` |
| **Branch** | `feat/task-031-example-client` |

**Description.** Provide a runnable example (`examples/query_example.py`) demonstrating a
programmatic RAG query and printing the cited answer — a lightweight scripted interface and doc aid.

**Definition of Ready.** TASK-025 merged.

**Steps.**
1. Construct the `RAGChain` (or call the API) for a sample question.
2. Print answer + citations + timing in a readable format.
3. Guard with `if __name__ == "__main__"`; keep import-safe for tests.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-100 | `test_example_runs_with_mocked_chain` | unit |
| TEST-101 | `test_example_prints_citations` | unit (capsys) |

**Definition of Done.** Example runs against a mocked chain and prints a cited answer; ≥90%.

**Acceptance criteria.** `python examples/query_example.py` prints a cited answer for a sample question.

**Commit message.** `docs(examples): programmatic RAG query example (TASK-031)`

---

## Sprint 6 Definition of Done (roll-up)

- [ ] FastAPI `/query`, `/feedback`, `/health` live and tested.
- [ ] Streamlit UI shows answer, sources, chunks, metrics, and feedback controls.
- [ ] Example client runs; ≥90% coverage per module.
- [ ] Sprint 6 tasks `Done` in [`TASK_INDEX.md`](./TASK_INDEX.md).
