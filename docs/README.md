# Engineering Harness & Project Documentation (`docs/`)

This directory contains the full Engineering Harness documentation suite for the **Pokemon TCG Rules Specialist RAG System**. It is designed to act as an unambiguous, self-contained specification for human developers and autonomous AI Code Agents (AGY, Claude Code, Codex, Cursor).

## Documentation Sitemap

```
docs/
├── README.md                           # Documentation Index & Sitemap
├── 00_project/                         # Core Project Governance & Specifications
│   ├── PROJECT.md                      # High-level vision, scope, and DataTalks requirements
│   ├── REQUIREMENTS.md                 # Traceable requirements matrix (REQ-001 to REQ-042)
│   ├── SUCCESS_CRITERIA.md             # Quantifiable performance and quality benchmarks
│   ├── TECH_STACK.md                   # Technology stack choices, framework specs & versions
│   ├── ROADMAP.md                      # Multi-phase macro implementation roadmap
│   ├── Assumptions.md                  # System assumptions and scope boundary definitions
│   ├── Risks.md                        # Technical, operational, and domain risk register
│   └── Backlog.md                      # Prioritized feature backlog items
├── 01_architecture/                    # System & Component Architectural Designs
│   ├── Architecture.md                 # System Architecture & Component Interaction Diagrams
│   ├── DomainModel.md                  # DDD Domain Model, Entities, Value Objects & Bounded Contexts
│   ├── FunctionalRequirements.md       # Functional specs for Ingestion, Retrieval, LLM, UI
│   ├── NonFunctionalRequirements.md    # SLA, Latency, Security, Scalability, Quality specs
│   ├── CodingStandards.md              # Coding conventions, type safety, linting & TDD rules
│   ├── APIContracts.md                 # OpenAPI REST endpoints specs (/query, /feedback, /health)
│   ├── DataModel.md                    # Database schemas (Qdrant payload, Postgres tables, Parquet)
│   ├── RAGArchitecture.md              # End-to-End RAG architecture & pipeline flow
│   ├── RetrievalPipeline.md            # Multi-stage retrieval: Dense, BM25, Hybrid RRF, Reranker
│   ├── IndexingPipeline.md             # Data ingestion, PDF parsing, text cleaning, chunking
│   ├── EmbeddingStrategy.md            # Embedding models comparative strategy (BGE vs OpenAI)
│   ├── PromptEngineering.md            # System prompts, Judge persona, context & citation rules
│   ├── EvaluationPlan.md               # RAG evaluation plan: Recall@K, MRR, RAGAS, DeepEval
│   ├── TestingStrategy.md              # Testing matrix: Unit, Integration, Smoke, E2E, Performance
│   ├── Security.md                     # Security policy, secrets management, input sanitization
│   ├── Deployment.md                   # Docker Compose, Kubernetes IaC & Cloud Deployment
│   └── Observability.md                # Prometheus metrics, Grafana dashboards, structlog JSON
├── 02_sprints/                         # Objective Sprint Specs (Sprints 1-18)
│   ├── SPRINT_01_FOUNDATION.md         # Sprint 1: Project Scaffold & Infrastructure Setup
│   ├── SPRINT_02_INGESTION.md          # Sprint 2: Web Scraping & PDF Parsing Pipeline
│   ├── SPRINT_03_CHUNKING_INDEXING.md  # Sprint 3: Normalization, Chunking & Qdrant Indexing
│   ├── SPRINT_04_RETRIEVAL.md          # Sprint 4: Hybrid Search & Cross-Encoder Reranking
│   ├── SPRINT_05_RAG_LLM.md            # Sprint 5: Query Rewriting, Prompt Builder & LLM Chain
│   ├── SPRINT_06_UI_FEEDBACK.md        # Sprint 6: Streamlit Web UI & Feedback Store
│   ├── SPRINT_07_EVALUATION.md         # Sprint 7: Benchmark Dataset & RAG Evaluation Suite
│   ├── SPRINT_08_MONITORING_DEPLOY.md  # Sprint 8: Prometheus/Grafana & Cloud Deployment
│   ├── SPRINT_09_SECURITY_CONTAINMENT.md # Sprint 9: Critical Containment & Supply Chain
│   ├── SPRINT_10_API_LLM_SECURITY.md    # Sprint 10: API, LLM & Data Security
│   ├── SPRINT_11_PLATFORM_HARDENING.md  # Sprint 11: Container/K8s/Network Hardening
│   ├── SPRINT_12_SECURITY_ASSURANCE.md  # Sprint 12: DevSecOps & Security Release Gate
│   ├── SPRINT_13_RUNTIME_STABILIZATION.md # Sprint 13: Corpus, Composition & Runtime
│   ├── SPRINT_14_QUALITY_REPRODUCIBILITY.md # Sprint 14: Real Tests & Clean Clone
│   ├── SPRINT_15_RETRIEVAL_QUALITY.md   # Sprint 15: Benchmark, Ablations & Retrieval Gate
│   ├── SPRINT_16_LLM_QUALITY.md         # Sprint 16: Real LLM Evaluation & Grounding
│   ├── SPRINT_17_OBSERVABILITY_UX.md    # Sprint 17: Tracing, SLO, Dashboards & UX
│   ├── SPRINT_18_PRODUCTION_QUALIFICATION.md # Sprint 18: Scale, Cloud, Recovery & Go/No-Go
│   └── DONE_CHECKLIST.md               # Definition of Done validation checklist
├── 03_tasks/                           # Task Execution Harness for AI Code Agents
│   ├── TASK_INDEX.md                   # Master index of granular tasks (TASK-001 to TASK-090)
│   ├── CONSOLIDATED_BACKLOG.md         # Jira-ready audit/evolution backlog with estimates/DoD
│   ├── TASK_DEPENDENCY_GRAPH.md        # Visual task dependency graph for parallel agent runs
│   ├── TASKS_SPRINT_01.md              # Granular task specs for Sprint 1
│   ├── TASKS_SPRINT_02.md              # Granular task specs for Sprint 2
│   ├── TASKS_SPRINT_03.md              # Granular task specs for Sprint 3
│   ├── TASKS_SPRINT_04.md              # Granular task specs for Sprint 4
│   ├── TASKS_SPRINT_05.md              # Granular task specs for Sprint 5
│   ├── TASKS_SPRINT_06.md              # Granular task specs for Sprint 6
│   ├── TASKS_SPRINT_07.md              # Granular task specs for Sprint 7
│   ├── TASKS_SPRINT_08.md              # Granular task specs for Sprint 8
│   ├── TASKS_SPRINT_09.md              # Security containment tasks (TASK-041..045)
│   ├── TASKS_SPRINT_10.md              # API/LLM security tasks (TASK-046..050)
│   ├── TASKS_SPRINT_11.md              # Platform hardening tasks (TASK-051..055)
│   ├── TASKS_SPRINT_12.md              # Assurance/release tasks (TASK-056..060)
│   ├── TASKS_SPRINT_13.md              # Runtime stabilization tasks (TASK-061..065)
│   ├── TASKS_SPRINT_14.md              # Quality/reproducibility tasks (TASK-066..070)
│   ├── TASKS_SPRINT_15.md              # Retrieval quality tasks (TASK-071..075)
│   ├── TASKS_SPRINT_16.md              # LLM quality tasks (TASK-076..080)
│   ├── TASKS_SPRINT_17.md              # Observability/UX tasks (TASK-081..085)
│   └── TASKS_SPRINT_18.md              # Production qualification tasks (TASK-086..090)
├── 04_decisions/                       # Architecture Decision Records (ADRs)
│   ├── ADR_001_VECTOR_DB.md            # Decision: Qdrant vs Chroma vs pgvector
│   ├── ADR_002_EMBEDDINGS.md           # Decision: BAAI/bge-large-en-v1.5 vs text-embedding-3-small
│   ├── ADR_003_CHUNKING.md             # Decision: Fixed overlapping vs Semantic section chunking
│   ├── ADR_004_RERANKING.md            # Decision: BGE Reranker vs Cohere Rerank
│   ├── ADR_005_QUERY_REWRITING.md      # Decision: Zero-shot LLM query expansion
│   └── ADR_006_INGESTION_ORCHESTRATOR.md # Decision: Modular Python Pipeline vs Prefect/Airflow
└── 05_agent_harness/                   # Governance & Operating Instructions for AI Agents
    ├── PROJECT_CONSTITUTION.md         # Core architectural & design principles
    ├── AGENT_PLAYBOOK.md               # Step-by-step agent workflow instructions
    ├── IMPLEMENTATION_GUIDE.md         # TDD guidelines, commit strategy, branch management
    ├── QUALITY_GATE_SPECIFICATION.md   # PR merge criteria (linter, mypy, 90% coverage)
    ├── SECURITY_REMEDIATION_PLAN.md     # Audit SEC-01..17 -> sprint/task/test closure map
    ├── TECHNICAL_AUDIT_FINDINGS.md      # TECH-01..30 -> task/test closure register
    ├── EVOLUTION_PROGRAM.md             # Official target architecture, roadmap, KPIs & governance
    └── TRACEABILITY_MATRIX.md          # Traceability mapping: Requirements <-> Tasks <-> Tests
```
