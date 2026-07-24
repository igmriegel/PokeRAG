# TASK_INDEX.md — Master Task Execution Index

## Objective

Single authoritative index of every granular engineering task (`TASK-001` … `TASK-040`)
for the **Pokemon TCG Rules RAG Expert Assistant**. Each task is small, independently
executable by an AI Code Agent, and traceable to a requirement
([`REQUIREMENTS.md`](../00_project/REQUIREMENTS.md)) and a sprint
([`docs/README.md`](../README.md) sitemap).

## Scope

- **In scope:** IDs, titles, sprint, covered `REQ-###`, dependency edges, and live status.
- **Out of scope:** full task bodies — those live in the per-sprint files
  [`TASKS_SPRINT_01.md`](./TASKS_SPRINT_01.md) … [`TASKS_SPRINT_08.md`](./TASKS_SPRINT_08.md);
  the visual dependency graph and parallel waves live in
  [`TASK_DEPENDENCY_GRAPH.md`](./TASK_DEPENDENCY_GRAPH.md).

## How to use (agents)

1. Pick the lowest-numbered task whose **Status = Pending** and whose **Depends on** tasks are all **Done**.
2. Open its full spec in the matching `TASKS_SPRINT_0X.md` file.
3. Follow the task's **Definition of Ready → Steps → Mandatory tests → Definition of Done**.
4. Flip the **Status** cell here to `In Progress`, then `Done` on merge.

> Status legend: `Pending` · `In Progress` · `Blocked` · `Done`. All tasks start `Pending`.

---

## Sprint 1 — Foundation & Infrastructure (`SPRINT_01_FOUNDATION`)

| ID | Title | REQ | Depends on | Status |
| :--- | :--- | :--- | :--- | :--- |
| TASK-001 | Project scaffold, dependency pinning & tooling | REQ-016, REQ-017 | — | Done |
| TASK-002 | Application settings module (`config/settings.py`) | REQ-016 | TASK-001 | Done |
| TASK-003 | Domain models & enums (`domain/models.py`) | REQ-004, REQ-012 | TASK-001 | Done |
| TASK-004 | Domain exceptions (`domain/exceptions.py`) | REQ-017 | TASK-001 | Done |
| TASK-005 | Structured JSON logging (`monitoring/logger.py`) | REQ-015 | TASK-002 | Done |
| TASK-006 | Docker Compose & service Dockerfiles skeleton | REQ-016 | TASK-001, TASK-002 | Done |

## Sprint 2 — Ingestion: Scraping & PDF Parsing (`SPRINT_02_INGESTION`)

| ID | Title | REQ | Depends on | Status |
| :--- | :--- | :--- | :--- | :--- |
| TASK-007 | Pokegym rulings crawler (`ingestion/crawler_pokegym.py`) | REQ-001 | TASK-003, TASK-005 | Done |
| TASK-008 | HTML pages scraper — Ban/Promo/Mega (`ingestion/html_scraper.py`) | REQ-003 | TASK-003, TASK-005 | Done |
| TASK-009 | PDF & Rulebook parser (`ingestion/pdf_parser.py`) | REQ-002 | TASK-003, TASK-005 | Done |
| TASK-010 | Ingestion orchestrator: download & raw persistence (`ingestion/pipeline.py`) | REQ-001, REQ-002, REQ-003 | TASK-007, TASK-008, TASK-009 | Done |
| TASK-011 | Ingestion CLI & Docker ingestion service (`scripts/run_ingestion.py`) | REQ-016 | TASK-010, TASK-006 | Done |

## Sprint 3 — Normalization, Chunking & Indexing (`SPRINT_03_CHUNKING_INDEXING`)

| ID | Title | REQ | Depends on | Status |
| :--- | :--- | :--- | :--- | :--- |
| TASK-012 | Document normalizer (`ingestion/normalizer.py`) | REQ-004 | TASK-003, TASK-010 | Done |
| TASK-013 | Document chunker (`ingestion/chunker.py`) | REQ-004 | TASK-012 | Done |
| TASK-014 | Qdrant vector store client (`storage/vector_db.py`) | REQ-005 | TASK-002, TASK-003 | Done |
| TASK-015 | Embedding & indexing job (`scripts/seed_db.py`) | REQ-005 | TASK-013, TASK-014 | Done |
| TASK-016 | Ingestion→index integration + chunks Parquet (`ingestion/pipeline.py`) | REQ-004, REQ-005 | TASK-013, TASK-015 | Done |

## Sprint 4 — Retrieval: Dense, BM25, Hybrid, Rerank (`SPRINT_04_RETRIEVAL`)

| ID | Title | REQ | Depends on | Status |
| :--- | :--- | :--- | :--- | :--- |
| TASK-017 | Dense retriever (`retrieval/dense.py`) | REQ-006 | TASK-014 | Pending |
| TASK-018 | BM25 lexical retriever (`retrieval/bm25.py`) | REQ-007 | TASK-013 | Pending |
| TASK-019 | Hybrid retriever — RRF k=60 (`retrieval/hybrid.py`) | REQ-008 | TASK-017, TASK-018 | Pending |
| TASK-020 | Cross-encoder reranker (`retrieval/reranker.py`) | REQ-009 | TASK-019 | Pending |
| TASK-021 | LLM client — OpenAI-compatible (`llm/client.py`) | REQ-011 | TASK-002 | Pending |
| TASK-022 | LLM query rewriter (`retrieval/query_rewriter.py`) | REQ-010 | TASK-021 | Pending |

## Sprint 5 — RAG, LLM & Prompting (`SPRINT_05_RAG_LLM`)

| ID | Title | REQ | Depends on | Status |
| :--- | :--- | :--- | :--- | :--- |
| TASK-023 | Retrieval pipeline orchestrator (`retrieval/pipeline.py`) | REQ-008, REQ-009, REQ-010 | TASK-019, TASK-020, TASK-022 | Pending |
| TASK-024 | Prompt templates & Judge persona (`llm/prompts.py`) | REQ-011, REQ-012 | TASK-003 | Pending |
| TASK-025 | RAG chain — retrieve→prompt→answer (`llm/rag_chain.py`) | REQ-011, REQ-012 | TASK-021, TASK-023, TASK-024 | Pending |
| TASK-026 | Relational DB & feedback ORM (`storage/relational_db.py`) | REQ-014 | TASK-002, TASK-003 | Pending |
| TASK-027 | Feedback store service (`monitoring/feedback_store.py`) | REQ-014 | TASK-026 | Pending |

## Sprint 6 — Interface: API & UI (`SPRINT_06_UI_FEEDBACK`)

| ID | Title | REQ | Depends on | Status |
| :--- | :--- | :--- | :--- | :--- |
| TASK-028 | API request/response schemas (`api/schemas.py`) | REQ-013 | TASK-003 | Pending |
| TASK-029 | FastAPI routes & app — `/query` `/feedback` `/health` (`api/routes.py`, `api/main.py`) | REQ-013, REQ-014 | TASK-025, TASK-027, TASK-028 | Pending |
| TASK-030 | Streamlit Web UI (`ui/streamlit_app.py`) | REQ-013, REQ-014 | TASK-029 | Pending |
| TASK-031 | Example client script (`examples/query_example.py`) | REQ-013 | TASK-025 | Pending |

## Sprint 7 — Evaluation (`SPRINT_07_EVALUATION`)

| ID | Title | REQ | Depends on | Status |
| :--- | :--- | :--- | :--- | :--- |
| TASK-032 | Benchmark dataset loader + 100 questions (`evaluation/dataset.py`) | REQ-018 | TASK-003 | Pending |
| TASK-033 | Retrieval metrics — Recall@K, MRR, Hit Rate (`evaluation/metrics.py`) | REQ-018 | TASK-003 | Pending |
| TASK-034 | Retrieval strategy comparison evaluator (`evaluation/evaluator.py`) | REQ-018 | TASK-023, TASK-032, TASK-033 | Pending |
| TASK-035 | LLM answer evaluation — Faithfulness/Correctness (`evaluation/metrics.py`, `evaluation/evaluator.py`) | REQ-019 | TASK-025, TASK-032 | Pending |
| TASK-036 | Evaluation CLI & regression gate (`scripts/run_evaluation.py`) | REQ-018, REQ-019 | TASK-034, TASK-035 | Pending |

## Sprint 8 — Monitoring & Deployment (`SPRINT_08_MONITORING_DEPLOY`)

| ID | Title | REQ | Depends on | Status |
| :--- | :--- | :--- | :--- | :--- |
| TASK-037 | Prometheus metrics collector (`monitoring/metrics_collector.py`) | REQ-015 | TASK-029 | Pending |
| TASK-038 | Prometheus config + Grafana dashboard (≥5 charts) | REQ-015 | TASK-037 | Pending |
| TASK-039 | Full Docker Compose integration + smoke tests | REQ-016 | TASK-011, TASK-029, TASK-030, TASK-038 | Pending |
| TASK-040 | Cloud deployment IaC (Kubernetes / Render) | REQ-020 | TASK-039 | Pending |

---

## Requirement → Task coverage (traceability roll-up)

| REQ | Covered by tasks |
| :--- | :--- |
| REQ-001 | TASK-007, TASK-010 |
| REQ-002 | TASK-009, TASK-010 |
| REQ-003 | TASK-008, TASK-010 |
| REQ-004 | TASK-012, TASK-013, TASK-016 |
| REQ-005 | TASK-014, TASK-015, TASK-016 |
| REQ-006 | TASK-017 |
| REQ-007 | TASK-018 |
| REQ-008 | TASK-019, TASK-023 |
| REQ-009 | TASK-020, TASK-023 |
| REQ-010 | TASK-022, TASK-023 |
| REQ-011 | TASK-021, TASK-024, TASK-025 |
| REQ-012 | TASK-003, TASK-024, TASK-025 |
| REQ-013 | TASK-028, TASK-029, TASK-030, TASK-031 |
| REQ-014 | TASK-026, TASK-027, TASK-029, TASK-030 |
| REQ-015 | TASK-005, TASK-037, TASK-038 |
| REQ-016 | TASK-001, TASK-002, TASK-006, TASK-011, TASK-039 |
| REQ-017 | TASK-001, TASK-004 (+ every task via 90% coverage gate) |
| REQ-018 | TASK-032, TASK-033, TASK-034, TASK-036 |
| REQ-019 | TASK-035, TASK-036 |
| REQ-020 | TASK-040 |

## Totals

- **40 tasks** across **8 sprints** (6 / 5 / 5 / 6 / 5 / 4 / 5 / 4).
- Full parallel-execution strategy: [`TASK_DEPENDENCY_GRAPH.md`](./TASK_DEPENDENCY_GRAPH.md).
