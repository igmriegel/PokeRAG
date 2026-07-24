# ADR-006: Ingestion Orchestration

- **Status:** Accepted
- **Date:** 2026-07-23
- **Deciders:** Architecture team (Pokemon TCG RAG)

## Context

Ingestion fetches nine official sources (Pokegym compendium scrape, five+ PDFs, three HTML pages — see [PROJECT.md](../00_project/PROJECT.md) section 3), then normalizes → chunks → embeds → indexes into Qdrant. The pipeline is coordinated by [`ingestion/pipeline.py`](../../src/pokemon_tcg_rag/ingestion/pipeline.py) (`IngestionPipeline` composing `PokegymCrawler`, `PDFParser`, `HTMLPageScraper`, `DocumentNormalizer`, `DocumentChunker`) and invoked via [`scripts/run_ingestion.py`](../../scripts/run_ingestion.py).

The rubric distinguishes **semi-automated** ingestion (a script/notebook, 1 pt) from **automated ingestion with a special tool** such as Kestra, dlt, Airflow, or Prefect (2 pts). This ADR decides how ingestion is orchestrated while still targeting the automated tier. It satisfies **REQ-001**–**REQ-005** and **REQ-016**.

## Decision Drivers

- **DD-1 — Reproducibility:** anyone can reproduce the knowledge base deterministically (**REQ-017** / reproducibility rubric).
- **DD-2 — Simplicity & footprint:** minimize new services/dependencies in an already multi-service stack.
- **DD-3 — Automated-ingestion rubric:** ingestion must run as an automated, containerized step, not a manual notebook, to credibly reach the 2-pt tier.
- **DD-4 — Clean Architecture fit:** orchestration must not leak into domain/retrieval layers; ingestion stays a modular Python component.
- **DD-5 — Runs in `docker compose`:** the whole stack, ingestion included, comes up with `docker compose up` (**REQ-016**).
- **DD-6 — Future scalability:** leave room for scheduling/retries/backfills as sources change over time (ban/promo/mega pages evolve).

## Considered Options

### Option A — Modular Python pipeline + dockerized ingestion service (chosen)

| Pros | Cons |
| :--- | :--- |
| Deterministic, no external orchestrator to reproduce (DD-1) | No built-in scheduler/retry/backfill UI (DD-6) |
| Smallest footprint; reuses existing code (DD-2) | Cross-source retry/observability is hand-rolled |
| Runs as a dedicated `ingestion` compose service (DD-3, DD-5) | |
| Pure Python component; clean layering (DD-4) | |

### Option B — Prefect

| Pros | Cons |
| :--- | :--- |
| Native retries, scheduling, observability UI (DD-6) | Adds a server/agent + dependency to the stack (DD-2) |
| Python-native flow definitions (DD-4) | Overkill for a fixed, small source list (DD-1 risk: more to reproduce) |

### Option C — Airflow

| Pros | Cons |
| :--- | :--- |
| Industry-standard DAG scheduling; mature (DD-6) | Heavyweight (scheduler + webserver + metadata DB) (DD-2) |
| Rich operator ecosystem | Significant compose/ops overhead for a periodic batch job (DD-5) |

### Option D — Kestra

| Pros | Cons |
| :--- | :--- |
| Declarative YAML workflows; UI + scheduling (DD-6) | New runtime + its own storage to operate (DD-2) |
| Language-agnostic | Team must learn Kestra DSL; pulls logic out of Python layers (DD-4) |

### Option E — dlt (data load tool)

| Pros | Cons |
| :--- | :--- |
| Lightweight Python; strong extract-load ergonomics | Optimized for structured EL to warehouses, not PDF/HTML → embeddings → Qdrant (DD-4) |
| Schema/state handling | Bespoke chunk/embed/index steps still custom; marginal gain here |

## Decision Outcome

**Chosen: A — the modular Python pipeline packaged as a dockerized ingestion service.**

For a fixed, small set of nine official sources, a full orchestrator (Prefect/Airflow/Kestra/dlt) adds services, dependencies, and its own state to operate and reproduce — cost that outweighs its scheduling/retry benefits at this scale (DD-1, DD-2). `IngestionPipeline` + `run_ingestion.py` already provide a deterministic, testable, Clean-Architecture-respecting flow (DD-4). Crucially, the rubric's **automated ingestion** tier is met not by a heavyweight tool but by running this pipeline as a dedicated **containerized `ingestion` service** in `docker compose` — it executes automatically as part of `docker compose up` rather than as a hand-run notebook (DD-3, DD-5).

A workflow orchestrator is explicitly recorded as a **future option**: should sources grow or require scheduled backfills/retries with an observability UI (DD-6), Prefect (Python-native, lowest migration cost from the current flow) is the preferred upgrade path. This deferral is noted in [Backlog.md](../00_project/Backlog.md).

## Consequences

**Positive**
- Minimal footprint and maximal reproducibility; the KB rebuilds deterministically from one entrypoint.
- Containerized ingestion service satisfies **REQ-016** and the automated-ingestion rubric within `docker compose up`.
- Orchestration logic stays out of domain/retrieval layers, preserving Clean Architecture.

**Negative**
- No out-of-the-box scheduling, retries, backfills, or run-history UI; these are manual or cron-driven until an orchestrator is adopted.
- Cross-source failure handling and observability are hand-rolled (structured logging via `monitoring/logger.py`).
- Because ban/promo/mega pages change over time, refreshes must be triggered manually or via an external scheduler until the future-option orchestrator lands.

## Links

- Requirements: **REQ-001**, **REQ-002**, **REQ-003**, **REQ-004**, **REQ-005**, **REQ-016**, **REQ-017** — [REQUIREMENTS.md](../00_project/REQUIREMENTS.md)
- Related ADRs: [ADR-003 Chunking](./ADR_003_CHUNKING.md), [ADR-001 Vector DB](./ADR_001_VECTOR_DB.md)
- Sibling docs: [IndexingPipeline.md](../01_architecture/IndexingPipeline.md), [Deployment.md](../01_architecture/Deployment.md), [Backlog.md](../00_project/Backlog.md)
- Code: [`ingestion/pipeline.py`](../../src/pokemon_tcg_rag/ingestion/pipeline.py), [`scripts/run_ingestion.py`](../../scripts/run_ingestion.py)
