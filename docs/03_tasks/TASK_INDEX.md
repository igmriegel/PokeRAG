# TASK_INDEX.md — Master Task Execution Index

## Objective

Single authoritative index of every granular engineering task (`TASK-001` … `TASK-090`)
for the **Pokemon TCG Rules RAG Expert Assistant**. Each task is small, independently
executable by an AI Code Agent, and traceable to a requirement
([`REQUIREMENTS.md`](../00_project/REQUIREMENTS.md)) and a sprint
([`docs/README.md`](../README.md) sitemap).

## Scope

- **In scope:** IDs, titles, sprint, covered `REQ-###`, dependency edges, and live status.
- **Out of scope:** full task bodies — those live in the per-sprint files
  [`TASKS_SPRINT_01.md`](./TASKS_SPRINT_01.md) … [`TASKS_SPRINT_18.md`](./TASKS_SPRINT_18.md);
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
| TASK-017 | Dense retriever (`retrieval/dense.py`) | REQ-006 | TASK-014 | Done |
| TASK-018 | BM25 lexical retriever (`retrieval/bm25.py`) | REQ-007 | TASK-013 | Done |
| TASK-019 | Hybrid retriever — RRF k=60 (`retrieval/hybrid.py`) | REQ-008 | TASK-017, TASK-018 | Done |
| TASK-020 | Cross-encoder reranker (`retrieval/reranker.py`) | REQ-009 | TASK-019 | Done |
| TASK-021 | LLM client — OpenAI-compatible (`llm/client.py`) | REQ-011 | TASK-002 | Done |
| TASK-022 | LLM query rewriter (`retrieval/query_rewriter.py`) | REQ-010 | TASK-021 | Done |

## Sprint 5 — RAG, LLM & Prompting (`SPRINT_05_RAG_LLM`)

| ID | Title | REQ | Depends on | Status |
| :--- | :--- | :--- | :--- | :--- |
| TASK-023 | Retrieval pipeline orchestrator (`retrieval/pipeline.py`) | REQ-008, REQ-009, REQ-010 | TASK-019, TASK-020, TASK-022 | Done |
| TASK-024 | Prompt templates & Judge persona (`llm/prompts.py`) | REQ-011, REQ-012 | TASK-003 | Done |
| TASK-025 | RAG chain — retrieve→prompt→answer (`llm/rag_chain.py`) | REQ-011, REQ-012 | TASK-021, TASK-023, TASK-024 | Done |
| TASK-026 | Relational DB & feedback ORM (`storage/relational_db.py`) | REQ-014 | TASK-002, TASK-003 | Done |
| TASK-027 | Feedback store service (`monitoring/feedback_store.py`) | REQ-014 | TASK-026 | Done |

## Sprint 6 — Interface: API & UI (`SPRINT_06_UI_FEEDBACK`)

| ID | Title | REQ | Depends on | Status |
| :--- | :--- | :--- | :--- | :--- |
| TASK-028 | API request/response schemas (`api/schemas.py`) | REQ-013 | TASK-003 | Done |
| TASK-029 | FastAPI routes & app — `/query` `/feedback` `/health` (`api/routes.py`, `api/main.py`) | REQ-013, REQ-014 | TASK-025, TASK-027, TASK-028 | Done |
| TASK-030 | Streamlit Web UI (`ui/streamlit_app.py`) | REQ-013, REQ-014 | TASK-029 | Done |
| TASK-031 | Example client script (`examples/query_example.py`) | REQ-013 | TASK-025 | Done |

## Sprint 7 — Evaluation (`SPRINT_07_EVALUATION`)

| ID | Title | REQ | Depends on | Status |
| :--- | :--- | :--- | :--- | :--- |
| TASK-032 | Benchmark dataset loader + 100 questions (`evaluation/dataset.py`) | REQ-018 | TASK-003 | Done |
| TASK-033 | Retrieval metrics — Recall@K, MRR, Hit Rate (`evaluation/metrics.py`) | REQ-018 | TASK-003 | Done |
| TASK-034 | Retrieval strategy comparison evaluator (`evaluation/evaluator.py`) | REQ-018 | TASK-023, TASK-032, TASK-033 | Done |
| TASK-035 | LLM answer evaluation — Faithfulness/Correctness (`evaluation/metrics.py`, `evaluation/evaluator.py`) | REQ-019 | TASK-025, TASK-032 | Done |
| TASK-036 | Evaluation CLI & regression gate (`scripts/run_evaluation.py`) | REQ-018, REQ-019 | TASK-034, TASK-035 | Done |

## Sprint 8 — Monitoring & Deployment (`SPRINT_08_MONITORING_DEPLOY`)

| ID | Title | REQ | Depends on | Status |
| :--- | :--- | :--- | :--- | :--- |
| TASK-037 | Prometheus metrics collector (`monitoring/metrics_collector.py`) | REQ-015 | TASK-029 | Done |
| TASK-038 | Prometheus config + Grafana dashboard (≥5 charts) | REQ-015 | TASK-037 | Done |
| TASK-039 | Full Docker Compose integration + smoke tests | REQ-016 | TASK-011, TASK-029, TASK-030, TASK-038 | Done |
| TASK-040 | Cloud deployment IaC (Kubernetes / Render) | REQ-020 | TASK-039 | Done |

## Sprint 9 — Security Containment & Supply Chain (`SPRINT_09_SECURITY_CONTAINMENT`)

| ID | Title | REQ | Depends on | Status |
| :--- | :--- | :--- | :--- | :--- |
| TASK-041 | Reproducible and vulnerability-managed dependency graph | REQ-021 | TASK-001 | Pending |
| TASK-042 | Activate CI and baseline security jobs | REQ-030 | TASK-041 | Pending |
| TASK-043 | Isolate infrastructure services and remove default credentials | REQ-028 | TASK-039 | Pending |
| TASK-044 | Eliminate user-controlled Streamlit SSRF | REQ-024 | TASK-030 | Pending |
| TASK-045 | Scope configuration and secrets per service | REQ-028 | TASK-043 | Pending |

## Sprint 10 — API, LLM & Data Security (`SPRINT_10_API_LLM_SECURITY`)

| ID | Title | REQ | Depends on | Status |
| :--- | :--- | :--- | :--- | :--- |
| TASK-046 | API authentication and authorization | REQ-022 | TASK-029, TASK-042 | Pending |
| TASK-047 | API resource, payload and cost controls | REQ-023 | TASK-046 | Pending |
| TASK-048 | Prompt-injection resistance and citation integrity | REQ-025 | TASK-025, TASK-041 | Pending |
| TASK-049 | Safe errors, diagnostics and HTTP headers | REQ-026 | TASK-047 | Pending |
| TASK-050 | Feedback integrity, privacy and response minimization | REQ-026 | TASK-046, TASK-027 | Pending |

## Sprint 11 — Platform Hardening (`SPRINT_11_PLATFORM_HARDENING`)

| ID | Title | REQ | Depends on | Status |
| :--- | :--- | :--- | :--- | :--- |
| TASK-051 | PostgreSQL least-privilege roles and migrations | REQ-028 | TASK-045, TASK-026 | Pending |
| TASK-052 | Rootless minimal runtime images | REQ-027 | TASK-041, TASK-043 | Pending |
| TASK-053 | Restricted Kubernetes workloads | REQ-027 | TASK-052, TASK-040 | Pending |
| TASK-054 | Network segmentation, TLS and protected observability | REQ-024, REQ-028 | TASK-043, TASK-044, TASK-053 | Pending |
| TASK-055 | Consolidated immutable IaC and artifact provenance | REQ-021, REQ-027 | TASK-041, TASK-053, TASK-054 | Pending |

## Sprint 12 — Security Assurance & Release Gate (`SPRINT_12_SECURITY_ASSURANCE`)

| ID | Title | REQ | Depends on | Status |
| :--- | :--- | :--- | :--- | :--- |
| TASK-056 | Harden the ingestion trust boundary | REQ-029 | TASK-041, TASK-010 | Pending |
| TASK-057 | Production wiring and truthful readiness | REQ-023, REQ-028, REQ-030 | TASK-047, TASK-050, TASK-051, TASK-054 | Pending |
| TASK-058 | Automated security scans, SBOM and policy gates | REQ-021, REQ-030 | TASK-042, TASK-055, TASK-056 | Pending |
| TASK-059 | DAST and adversarial security regression suite | REQ-022, REQ-024, REQ-025, REQ-026, REQ-030 | TASK-048, TASK-049, TASK-057, TASK-058 | Pending |
| TASK-060 | Security closure and release gate | REQ-030 | TASK-041..TASK-059 | Pending |

## Sprint 13 — Runtime Stabilization (`SPRINT_13_RUNTIME_STABILIZATION`)

| ID | Title | REQ | Depends on | Status |
| :--- | :--- | :--- | :--- | :--- |
| TASK-061 | Hydrate BM25 and enforce corpus parity | REQ-031, REQ-032 | TASK-057, TASK-063 | Done |
| TASK-062 | Enforce the query configuration contract | REQ-031 | TASK-057 | Done |
| TASK-063 | Version the corpus and deterministic bootstrap fixture | REQ-032 | TASK-041, TASK-056 | Done |
| TASK-064 | Complete the production composition root | REQ-031, REQ-032 | TASK-061, TASK-062, TASK-063 | Done |
| TASK-065 | Prove the operational query and feedback journey | REQ-031 | TASK-050, TASK-051, TASK-064 | Pending |

## Sprint 14 — Quality & Reproducibility (`SPRINT_14_QUALITY_REPRODUCIBILITY`)

| ID | Title | REQ | Depends on | Status |
| :--- | :--- | :--- | :--- | :--- |
| TASK-066 | Repair static quality gates | REQ-033 | TASK-042 | Pending |
| TASK-067 | Enforce 90% coverage and clean-clone CI | REQ-033, REQ-034 | TASK-041, TASK-042, TASK-066 | Pending |
| TASK-068 | Build a real infrastructure integration layer | REQ-033 | TASK-063, TASK-064, TASK-065, TASK-067 | Pending |
| TASK-069 | Add full compose and browser/API end-to-end test | REQ-033, REQ-034 | TASK-068 | Pending |
| TASK-070 | Reconcile documentation with executable evidence | REQ-034 | TASK-067, TASK-069 | Pending |

## Sprint 15 — Retrieval Quality (`SPRINT_15_RETRIEVAL_QUALITY`)

| ID | Title | REQ | Depends on | Status |
| :--- | :--- | :--- | :--- | :--- |
| TASK-071 | Build a reviewed, versioned benchmark | REQ-035 | TASK-063 | Pending |
| TASK-072 | Use production retrieval implementations in evaluation | REQ-036 | TASK-061, TASK-071 | Pending |
| TASK-073 | Execute retrieval ablations | REQ-036 | TASK-072 | Pending |
| TASK-074 | Implement incremental manifest-driven ingestion | REQ-032, REQ-036 | TASK-056, TASK-063 | Pending |
| TASK-075 | Publish retrieval baseline and regression gate | REQ-036 | TASK-072, TASK-073, TASK-074 | Pending |

## Sprint 16 — LLM Quality & Guardrails (`SPRINT_16_LLM_QUALITY`)

| ID | Title | REQ | Depends on | Status |
| :--- | :--- | :--- | :--- | :--- |
| TASK-076 | Implement a real prompt/model evaluation runner | REQ-037 | TASK-057, TASK-071 | Pending |
| TASK-077 | Add RAGAS/DeepEval automatic scoring | REQ-037 | TASK-076 | Pending |
| TASK-078 | Establish human evaluation and error taxonomy | REQ-037 | TASK-076 | Pending |
| TASK-079 | Validate structured claims and citation entailment | REQ-025, REQ-037 | TASK-048, TASK-076 | Pending |
| TASK-080 | Publish LLM selection report and regression gate | REQ-037 | TASK-077, TASK-078, TASK-079 | Pending |

## Sprint 17 — Observability & Product UX (`SPRINT_17_OBSERVABILITY_UX`)

| ID | Title | REQ | Depends on | Status |
| :--- | :--- | :--- | :--- | :--- |
| TASK-081 | Add OpenTelemetry tracing and correlation | REQ-038 | TASK-049, TASK-057 | Pending |
| TASK-082 | Define SLO, token, cost and alert controls | REQ-038 | TASK-047, TASK-081 | Pending |
| TASK-083 | Populate dashboards and feedback telemetry | REQ-038, REQ-039 | TASK-065, TASK-081, TASK-082 | Pending |
| TASK-084 | Complete the user workflow UX | REQ-039 | TASK-044, TASK-050, TASK-065 | Pending |
| TASK-085 | Publish operational analytics and runbooks | REQ-038, REQ-039 | TASK-049, TASK-083, TASK-084 | Pending |

## Sprint 18 — Scale, Cloud & Production Qualification (`SPRINT_18_PRODUCTION_QUALIFICATION`)

| ID | Title | REQ | Depends on | Status |
| :--- | :--- | :--- | :--- | :--- |
| TASK-086 | Add safe cache, metadata filtering and MMR policy | REQ-040 | TASK-073, TASK-075 | Pending |
| TASK-087 | Qualify warm-up, batching, concurrency and cost | REQ-040 | TASK-047, TASK-080, TASK-082, TASK-086 | Pending |
| TASK-088 | Deploy immutable artifacts to cloud staging | REQ-041 | TASK-055, TASK-058, TASK-069, TASK-083, TASK-087 | Pending |
| TASK-089 | Exercise backup, restore, rollback and DORA metrics | REQ-041 | TASK-051, TASK-055, TASK-083, TASK-088 | Pending |
| TASK-090 | Execute final production scorecard and release gate | REQ-042 | TASK-060, TASK-070, TASK-075, TASK-080, TASK-085, TASK-087..089 | Pending |

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
| REQ-021 | TASK-041, TASK-055, TASK-058 |
| REQ-022 | TASK-046, TASK-059 |
| REQ-023 | TASK-047, TASK-057 |
| REQ-024 | TASK-044, TASK-054, TASK-059 |
| REQ-025 | TASK-048, TASK-059 |
| REQ-026 | TASK-049, TASK-050, TASK-059 |
| REQ-027 | TASK-052, TASK-053, TASK-055 |
| REQ-028 | TASK-043, TASK-045, TASK-051, TASK-054, TASK-057 |
| REQ-029 | TASK-056 |
| REQ-030 | TASK-042, TASK-057, TASK-058, TASK-059, TASK-060 |
| REQ-031 | TASK-061, TASK-062, TASK-064, TASK-065 |
| REQ-032 | TASK-061, TASK-063, TASK-064, TASK-074 |
| REQ-033 | TASK-066, TASK-067, TASK-068, TASK-069 |
| REQ-034 | TASK-067, TASK-069, TASK-070 |
| REQ-035 | TASK-071 |
| REQ-036 | TASK-072, TASK-073, TASK-074, TASK-075 |
| REQ-037 | TASK-076, TASK-077, TASK-078, TASK-079, TASK-080 |
| REQ-038 | TASK-081, TASK-082, TASK-083, TASK-085 |
| REQ-039 | TASK-083, TASK-084, TASK-085 |
| REQ-040 | TASK-086, TASK-087 |
| REQ-041 | TASK-088, TASK-089 |
| REQ-042 | TASK-090 |

## Totals

- **90 tasks** across **18 sprints** (6 / 5 / 5 / 6 / 5 / 4 / 5 / 4, then ten sprints
  with 5 tasks each).
- Security findings and closure evidence: [`SECURITY_REMEDIATION_PLAN.md`](../05_agent_harness/SECURITY_REMEDIATION_PLAN.md).
- Technical findings and closure evidence: [`TECHNICAL_AUDIT_FINDINGS.md`](../05_agent_harness/TECHNICAL_AUDIT_FINDINGS.md).
- Priority, effort and ownership: [`CONSOLIDATED_BACKLOG.md`](./CONSOLIDATED_BACKLOG.md).
- Full parallel-execution strategy: [`TASK_DEPENDENCY_GRAPH.md`](./TASK_DEPENDENCY_GRAPH.md).
