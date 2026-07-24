# ROADMAP.md - Macro Multi-Phase Implementation Roadmap

## Objective

Provide the **macro, phase-level plan** that sequences the entire build of the Pokemon TCG
Rules RAG Expert Assistant, mapping each phase to the sprint files under `docs/02_sprints/`
(SPRINT_01..08) and to the requirements in [`REQUIREMENTS.md`](./REQUIREMENTS.md). Each
phase carries an objective, its dependencies, the artifacts it produces, completion
criteria (linked to [`SUCCESS_CRITERIA.md`](./SUCCESS_CRITERIA.md)), and key risks (linked
to [`Risks.md`](./Risks.md)). This is the "what/when/in-what-order"; sprint files carry the
task-level detail.

## Scope

- **In scope:** ordering, dependencies, and gating between the eleven named phases.
- **Out of scope:** granular tasks (see `docs/03_tasks/`) and per-sprint checklists (see
  `docs/02_sprints/`).

The phase ordering follows the "Roadmap de implementação" in the source plan
(`PlanejamentoRAG_Pokemon`, lines 514–526).

---

## 1. Phase → Sprint → Requirement Map

| Phase | Sprint(s) | Primary REQ IDs | Rubric contribution |
| :--- | :--- | :--- | :--- |
| **P1 Foundation** | [SPRINT_01](../02_sprints/SPRINT_01_FOUNDATION.md) | REQ-016, REQ-017 | Containerization, Reproducibility |
| **P2 Infrastructure** | [SPRINT_01](../02_sprints/SPRINT_01_FOUNDATION.md) | REQ-005, REQ-014, REQ-015, REQ-016 | Containerization, Monitoring base |
| **P3 Domain** | [SPRINT_01](../02_sprints/SPRINT_01_FOUNDATION.md) | REQ-004, REQ-012 | Problem/flow foundation |
| **P4 Data Pipeline (Ingestion)** | [SPRINT_02](../02_sprints/SPRINT_02_INGESTION.md) | REQ-001, REQ-002, REQ-003 | Ingestion pipeline |
| **P5 Chunking & Knowledge Base** | [SPRINT_03](../02_sprints/SPRINT_03_CHUNKING_INDEXING.md) | REQ-004, REQ-005 | Ingestion pipeline |
| **P6 RAG Pipeline** | [SPRINT_05](../02_sprints/SPRINT_05_RAG_LLM.md) | REQ-010, REQ-011, REQ-012 | Retrieval flow, Best practices |
| **P7 Retrieval** | [SPRINT_04](../02_sprints/SPRINT_04_RETRIEVAL.md) | REQ-006, REQ-007, REQ-008, REQ-009 | Retrieval eval, Best practices |
| **P8 APIs** | [SPRINT_05](../02_sprints/SPRINT_05_RAG_LLM.md), [SPRINT_06](../02_sprints/SPRINT_06_UI_FEEDBACK.md) | REQ-013, REQ-014 | Interface |
| **P9 Frontend / UI** | [SPRINT_06](../02_sprints/SPRINT_06_UI_FEEDBACK.md) | REQ-013, REQ-014 | Interface, Monitoring (feedback) |
| **P10 Testing & Evaluation** | [SPRINT_07](../02_sprints/SPRINT_07_EVALUATION.md) | REQ-017, REQ-018, REQ-019 | Retrieval & LLM evaluation |
| **P11 Deploy & Hardening** | [SPRINT_08](../02_sprints/SPRINT_08_MONITORING_DEPLOY.md) | REQ-015, REQ-016, REQ-020 | Monitoring, Containerization, Bonus |

> Note: P6 (RAG Pipeline) and P7 (Retrieval) are logically distinct phases but are built in
> overlapping sprints — a minimal Dense→LLM pipeline (P6) is stood up first, then the full
> multi-strategy retrieval (P7) is layered under it, matching the plan's order
> "basic RAG → BM25/Hybrid → query rewriting → rerank".

---

## 2. Phase Ordering Diagram

```mermaid
graph TD
    P1[P1 Foundation] --> P2[P2 Infrastructure]
    P2 --> P3[P3 Domain]
    P3 --> P4[P4 Data Pipeline / Ingestion]
    P4 --> P5[P5 Chunking and Knowledge Base]
    P5 --> P6[P6 RAG Pipeline - Dense to LLM]
    P6 --> P7[P7 Retrieval - BM25/Hybrid/Rerank/Rewrite]
    P7 --> P8[P8 APIs]
    P8 --> P9[P9 Frontend / UI + Feedback]
    P9 --> P10[P10 Testing and Evaluation]
    P10 --> P11[P11 Deploy and Hardening]
    P10 -.regression feedback.-> P7
    P10 -.regression feedback.-> P6
```

```mermaid
gantt
    title Sprint Timeline (relative)
    dateFormat  X
    axisFormat  S%L
    section Setup
    SPRINT_01 Foundation/Infra/Domain      :s1, 0, 1
    section Data
    SPRINT_02 Ingestion                    :s2, after s1, 1
    SPRINT_03 Chunking and Indexing        :s3, after s2, 1
    section RAG
    SPRINT_04 Retrieval                    :s4, after s3, 1
    SPRINT_05 RAG/LLM/Rewrite              :s5, after s4, 1
    section Product
    SPRINT_06 UI and Feedback              :s6, after s5, 1
    SPRINT_07 Evaluation                   :s7, after s6, 1
    SPRINT_08 Monitoring and Deploy        :s8, after s7, 1
```

---

## 3. Phase Details

### P1 — Foundation
- **Objective:** Establish the repository skeleton, Clean Architecture package layout
  (`domain/ingestion/retrieval/llm/evaluation/monitoring/storage/api/ui/config`), Pydantic
  `Settings`, tooling (ruff/mypy/pytest), and the Docker Compose shell.
- **Dependencies:** none (entry phase).
- **Artifacts:** `pyproject.toml`, `requirements.txt`, `docker-compose.yml`, `.env.example`,
  `src/pokemon_tcg_rag/config/settings.py`, CI under `ci/`.
- **Completion criteria:** `ruff` + `mypy --strict` clean; `docker compose config` valid;
  empty test suite green. Links [SC-016](./SUCCESS_CRITERIA.md), [SC-020](./SUCCESS_CRITERIA.md).
- **Risks:** [RISK-008](./Risks.md) reproducibility drift.

### P2 — Infrastructure
- **Objective:** Bring up Qdrant, PostgreSQL, Prometheus, and Grafana as healthy compose
  services with provisioning and healthchecks; wire connection settings.
- **Dependencies:** P1.
- **Artifacts:** compose services + volumes, Prometheus/Grafana provisioning under `config/`
  and `infra/`, Alembic baseline migration for the feedback schema.
- **Completion criteria:** all services healthy < 60 s ([SC-014](./SUCCESS_CRITERIA.md));
  Qdrant collection `pokemon_tcg_rules` (dim 1024) creatable.
- **Risks:** [RISK-005](./Risks.md) Qdrant memory.

### P3 — Domain
- **Objective:** Finalize domain models and enums (`DocumentSource`, `RuleType`,
  `DocumentMetadata`, `Document`, `Chunk`, `RetrievedChunk`, `AnswerResponse`,
  `FeedbackRecord`) as the shared contract across layers.
- **Dependencies:** P1.
- **Artifacts:** `src/pokemon_tcg_rag/domain/models.py`, unit tests for validation.
- **Completion criteria:** models typed, validated, 100% covered; referenced by
  `docs/01_architecture/DomainModel.md`.
- **Risks:** metadata schema instability if source layouts differ ([RISK-002](./Risks.md)).

### P4 — Data Pipeline (Ingestion)
- **Objective:** Automated download + scrape of all 9 sources: Pokegym crawler, 5 PDFs,
  and 3 HTML legality pages; persist raw HTML/PDF/JSON.
- **Dependencies:** P3.
- **Artifacts:** downloader + scrapers, `data/raw_data/{pdfs,html,json}`, source manifest.
- **Completion criteria:** 100% sources fetched with 0 hard failures
  ([SC-015](./SUCCESS_CRITERIA.md)). REQ-001/002/003.
- **Risks:** [RISK-001](./Risks.md) scraping fragility; [RISK-006](./Risks.md) source ToS/license.

### P5 — Chunking & Knowledge Base
- **Objective:** Normalize/parse raw docs (PyMuPDF/pymupdf4llm + BeautifulSoup), chunk with
  metadata enrichment and stable IDs, embed with `BAAI/bge-large-en-v1.5`, index into Qdrant.
- **Dependencies:** P4, P2 (Qdrant up).
- **Artifacts:** `data/processed`, `data/chunks` (JSONL/Parquet), populated Qdrant collection.
- **Completion criteria:** 100% docs indexed, chunk counts > 0 per source ([SC-015](./SUCCESS_CRITERIA.md)). REQ-004/005.
- **Risks:** [RISK-002](./Risks.md) PDF extraction quality; [RISK-003](./Risks.md) embedding cost/time.

### P6 — RAG Pipeline (Dense → LLM)
- **Objective:** Stand up the minimal grounded pipeline: Dense retrieval → prompt builder
  (Certified Judge persona) → LLM (`gpt-4o-mini`, temp 0.0) → cited `AnswerResponse`; add
  LLM query rewriting before retrieval.
- **Dependencies:** P5.
- **Artifacts:** retrieval/llm modules, prompt templates (`docs/05_prompts/`), query rewriter.
- **Completion criteria:** end-to-end answer with citations; abstains when unsupported
  ([SC-011](./SUCCESS_CRITERIA.md)). REQ-010/011/012.
- **Risks:** [RISK-004](./Risks.md) LLM hallucination.

### P7 — Retrieval (BM25 / Hybrid / Rerank)
- **Objective:** Implement all four strategies — Dense, BM25 (`rank-bm25`), Hybrid via RRF
  (k=60), Hybrid+Rerank (`bge-reranker-large`) — behind a common interface.
- **Dependencies:** P6.
- **Artifacts:** four retriever implementations, RRF fusion, reranker stage.
- **Completion criteria:** all 4 selectable and benchmarkable ([SC-005](./SUCCESS_CRITERIA.md),
  [SC-022](./SUCCESS_CRITERIA.md)). REQ-006/007/008/009.
- **Risks:** [RISK-005](./Risks.md) reranker memory/latency.

### P8 — APIs
- **Objective:** Expose FastAPI `/query`, `/feedback`, `/health` returning typed
  `AnswerResponse`/`FeedbackRecord`; persist feedback to Postgres.
- **Dependencies:** P6 (query), P2 (Postgres).
- **Artifacts:** FastAPI app, API contracts (`docs/01_architecture/APIContracts.md`), tests.
- **Completion criteria:** endpoints conform to schema ([SC-021](./SUCCESS_CRITERIA.md)). REQ-013/014.
- **Risks:** [RISK-007](./Risks.md) input handling / injection.

### P9 — Frontend / UI + Feedback
- **Objective:** Streamlit UI: question → answer → sources → chunks, with latency/model/
  #docs, plus 👍/👎 + optional comment persisted via the API to Postgres.
- **Dependencies:** P8.
- **Artifacts:** Streamlit app, feedback wiring.
- **Completion criteria:** UI answers a query and records feedback ([SC-018](./SUCCESS_CRITERIA.md),
  [SC-021](./SUCCESS_CRITERIA.md)). REQ-013/014.
- **Risks:** UX gaps hiding citations ([RISK-004](./Risks.md)).

### P10 — Testing & Evaluation
- **Objective:** Build the 100-question benchmark and evaluation harness; compare 4
  retrieval strategies (Recall@5/@10, MRR, Hit Rate) and LLM configs (2 prompts × 2 models)
  on Faithfulness/Correctness/Citation/Completeness; enforce ≥90% coverage and regression
  gates.
- **Dependencies:** P7, P9.
- **Artifacts:** benchmark dataset, eval reports, regression baselines, full test suite.
- **Completion criteria:** [SC-001](./SUCCESS_CRITERIA.md)–SC-011, SC-016 met; best configs
  selected & documented. REQ-017/018/019.
- **Risks:** [RISK-009](./Risks.md) ground-truth labeling effort.

### P11 — Deploy & Hardening
- **Objective:** Finalize `docker compose up` for the full stack (streamlit, api, qdrant,
  postgres, prometheus, grafana, ingestion), Grafana dashboard (≥5 charts), docs, and
  optional cloud deploy (Render/Railway/AWS).
- **Dependencies:** P10.
- **Artifacts:** finalized compose + dashboards, README/setup/architecture/evaluation docs,
  optional IaC (REQ-020), demo video.
- **Completion criteria:** [SC-014](./SUCCESS_CRITERIA.md), [SC-017](./SUCCESS_CRITERIA.md),
  [SC-024](./SUCCESS_CRITERIA.md); optionally [SC-023](./SUCCESS_CRITERIA.md). REQ-015/016/020.
- **Risks:** [RISK-006](./Risks.md) legal/ToS for public deploy; [RISK-008](./Risks.md) drift.

---

## 4. Critical Path & Parallelism

- **Critical path:** P1 → P2 → P4 → P5 → P6 → P7 → P10 → P11 (data must exist before
  retrieval can be evaluated).
- **Parallelizable:** P3 (Domain) alongside P2; P8/P9 (API/UI shell) can start against a
  stubbed pipeline once P6 exists; prompt authoring (`docs/05_prompts/`) can precede P6.
- Regression loop: P10 feeds fixes back into P6/P7 until [SUCCESS_CRITERIA.md](./SUCCESS_CRITERIA.md)
  targets hold.

---

## Cross-References

- [`REQUIREMENTS.md`](./REQUIREMENTS.md) · [`SUCCESS_CRITERIA.md`](./SUCCESS_CRITERIA.md) · [`TECH_STACK.md`](./TECH_STACK.md)
- [`Risks.md`](./Risks.md) · [`Assumptions.md`](./Assumptions.md) · [`Backlog.md`](./Backlog.md)
- Sprint specs: `docs/02_sprints/SPRINT_01..08`; tasks: `docs/03_tasks/`.
