# Assumptions.md - Documented Ambiguities & Working Decisions

## Objective

Record every **genuine ambiguity** in the source plan (`PlanejamentoRAG_Pokemon`) and the
existing specs, together with the **working decision** the harness adopts until the
ambiguity is resolved. Ambiguities are documented
here rather than silently resolved elsewhere; other docs reference these `ASSUMPTION-###`
IDs instead of inventing answers. The source of truth for scope and requirements is
[`PROJECT.md`](./PROJECT.md) and [`REQUIREMENTS.md`](./REQUIREMENTS.md).

## Scope

- **In scope:** decisions taken under uncertainty that could change if new information
  arrives (default chunk size, LLM availability, embedding provider default, cloud target,
  scraped-data licensing, source stability, latency/startup measurement boundaries).
- **Out of scope:** settled facts already encoded in `src/pokemon_tcg_rag/config/settings.py`
  or `docs/00_project/*` (those are decisions, not assumptions).

Each entry: **statement**, **rationale**, **impact if wrong**, **how to validate**.

---

## Assumptions Register

### ASSUMPTION-001 — Python runtime floor
- **Statement:** The project targets **Python 3.11** even though `pyproject.toml` declares
  `requires-python >=3.10` and `[tool.ruff]`/`[tool.mypy]` say `py310`/`3.10`.
- **Rationale:** The Agent Brief and plan say "Python 3.11+", while the packaging metadata
  allows 3.10 for broader install compatibility.
- **Impact if wrong:** 3.10-only environments could hit 3.11 syntax; or 3.11-only features
  (e.g. `tomllib`, finer typing) may be unavailable if 3.10 is enforced.
- **How to validate:** confirm CI matrix and the Docker base image tag; align the ruff/mypy
  `target-version` if 3.11 is mandatory. Tracked against [`TECH_STACK.md`](./TECH_STACK.md) §2.

### ASSUMPTION-002 — Default LLM provider & availability
- **Statement:** The default generation model is **`gpt-4o-mini`** via an OpenAI-compatible
  endpoint (`OPENAI_MODEL_NAME` in `settings.py`), with `gpt-4.1-mini` as the comparison
  model; a valid `OPENAI_API_KEY` is available at runtime.
- **Rationale:** `settings.py` and the Agent Brief name these models; the plan allows "or
  another available model".
- **Impact if wrong:** if no OpenAI access, generation and the `text-embedding-3-small`
  comparison break; the LLM-evaluation A/B ([SC-010](./SUCCESS_CRITERIA.md)) cannot run as
  specified.
- **How to validate:** smoke-test a `/query` call with the configured key; if unavailable,
  fall back to a local/OpenAI-compatible server and document the substitution.

### ASSUMPTION-003 — Default embedding backend
- **Statement:** The **default** embedding path is the **local** `BAAI/bge-large-en-v1.5`
  (1024-d) via sentence-transformers; `text-embedding-3-small` is used only for the
  comparison experiment, not as the production default.
- **Rationale:** 1024-d matches `EMBEDDING_DIMENSION` and the Qdrant collection; local
  embeddings avoid per-embedding API cost during full-corpus indexing.
- **Impact if wrong:** if OpenAI embeddings were intended as default, dimension config and
  cost/latency assumptions ([RISK-003](./Risks.md)) change.
- **How to validate:** confirm which model populates `pokemon_tcg_rules`; assert vector dim
  == 1024 at index time.

### ASSUMPTION-004 — Default chunk size & overlap
- **Statement:** Fixed-size chunking defaults to **512 tokens with ~64-token overlap** for
  PDF/HTML prose; Pokegym Q&A is kept as **one chunk per ruling**.
- **Rationale:** The plan lists a chunk-size experiment (256 × 512 × 1024) but names no
  default; 512 is the balanced midpoint and Pokegym entries are naturally atomic.
- **Impact if wrong:** retrieval recall and latency shift; the chunk-size experiment may
  select a different winner ([ADR_003](../04_decisions/ADR_003_CHUNKING.md)).
- **How to validate:** run the chunk-size ablation from `docs/01_architecture/EvaluationPlan.md`
  and adopt the best-Recall@10 value; record it in the ADR.

### ASSUMPTION-005 — Chunking strategy default (fixed vs semantic)
- **Statement:** The **default** strategy is **fixed-size overlapping** chunking; semantic
  chunking is a stretch experiment ([Backlog BL-015](./Backlog.md)).
- **Rationale:** Plan lists "Fixo × Semântico" as an experiment; fixed is simpler and
  deterministic for the baseline.
- **Impact if wrong:** if semantic is required for baseline, more implementation effort and
  different chunk boundaries.
- **How to validate:** eval comparison; promote semantic only if it beats the baseline.

### ASSUMPTION-006 — Pokegym & pokemon.com content usage/licensing
- **Statement:** Scraped Pokegym rulings and pokemon.com pages/PDFs are used **only** for a
  non-commercial educational RAG demo, with source URLs and dates cited; content is not
  redistributed as a standalone dataset.
- **Rationale:** The plan names these public sources but states no explicit license; citing
  and non-redistribution is the conservative posture.
- **Impact if wrong:** potential ToS/copyright issue, especially for public cloud deploy
  ([RISK-006](./Risks.md)).
- **How to validate:** review each site's Terms of Service / robots.txt; restrict caching
  and honor `robots.txt`; keep raw data out of the public repo if required.

### ASSUMPTION-007 — Latency measurement boundary
- **Statement:** "Mean latency < 2 s" ([SC-012](./SUCCESS_CRITERIA.md)) is measured on a
  **warm** system (models loaded, caches primed) and **excludes** one-time model
  warm-up/download; it covers rewrite → retrieve → rerank → generate.
- **Rationale:** Cross-encoder rerank and LLM calls dominate; cold model load is a startup
  cost, not steady-state query cost.
- **Impact if wrong:** if cold-start is counted, the target is effectively unachievable on
  first query; SLA interpretation changes.
- **How to validate:** report P50/P95 from `AnswerResponse.latency_seconds` after warm-up;
  note warm-up time separately in `docs/04_tests/PERFORMANCE.md`.

### ASSUMPTION-008 — `docker compose up` startup boundary
- **Statement:** "Startup < 60 s" ([SC-014](./SUCCESS_CRITERIA.md)) assumes **images are
  pre-built/pre-pulled and model weights cached**; image build and first-time HF model
  download are excluded.
- **Rationale:** Plan says "Docker compose sobe em menos de 60 segundos"; building images
  and downloading multi-GB models clearly cannot fit in 60 s.
- **Impact if wrong:** if build+download must fit in 60 s, the target is infeasible.
- **How to validate:** measure time from `up` to all healthchecks green on a warm cache; log
  cold-build time separately.

### ASSUMPTION-009 — Cloud deployment target
- **Statement:** The optional cloud deploy ([SC-023](./SUCCESS_CRITERIA.md), REQ-020) targets
  **Render or Railway** first (managed compose-like hosting); AWS is a secondary option.
- **Rationale:** Plan lists "AWS, Render ou Railway" without choosing; Render/Railway are the
  lowest-effort path to a public URL for the bonus.
- **Impact if wrong:** IaC manifests (REQ-020) may need to be provider-specific (e.g. ECS/K8s
  for AWS), changing deployment artifacts.
- **How to validate:** confirm target with stakeholder; produce provider-matching manifests
  and a reachable `/health`.

### ASSUMPTION-010 — Errata / official PDF layout stability
- **Statement:** The official PDFs (rulebook, tournament, alternative-play, errata, deck
  list) have a **stable enough layout** for PyMuPDF/pymupdf4llm to extract structured text
  without per-document custom OCR.
- **Rationale:** These are text-based PDFs; the plan assumes structured extraction. Errata
  in particular may use dense tabular layouts.
- **Impact if wrong:** garbled sections, wrong page numbers in citations, lower faithfulness
  ([RISK-002](./Risks.md)).
- **How to validate:** spot-check extracted text vs source pages; add layout-specific parsing
  or OCR fallback only for documents that fail QA.

### ASSUMPTION-011 — pokemon.com rate limiting / access
- **Statement:** pokemon.com static assets and HTML pages are fetchable without
  authentication and tolerate polite, low-rate requests (single-pass ingestion with backoff
  via `tenacity`).
- **Rationale:** These are public URLs; ingestion is a one-shot/batch, not high-frequency.
- **Impact if wrong:** blocked/429 responses could break ingestion ([RISK-001](./Risks.md)).
- **How to validate:** run ingestion with rate limiting + retry/backoff; cache raw responses
  to avoid re-fetching.

### ASSUMPTION-012 — Benchmark ground-truth authorship
- **Statement:** The 100-question evaluation benchmark ([SC-001](./SUCCESS_CRITERIA.md)) is
  authored in-project (questions + expected source documents), not provided externally.
- **Rationale:** Plan says "Criar um dataset — 100 perguntas"; no dataset ships with the
  sources.
- **Impact if wrong:** if an official benchmark exists, effort estimate and labels change
  ([RISK-009](./Risks.md)).
- **How to validate:** confirm no external benchmark; label questions against indexed
  sources and peer-review a sample.

### ASSUMPTION-013 — API path prefix & unversioned operational routes
- **Statement:** Application routes are mounted under **`/api/v1`** (so `/api/v1/query`,
  `/api/v1/feedback`), while `/health` and `/metrics` sit at the **root** (unversioned).
- **Rationale:** `api/main.py`/`api/routes.py` wire the router under a version prefix; probes
  and the Prometheus scrape target are conventionally unversioned.
- **Impact if wrong:** clients ([`APIContracts.md`](../01_architecture/APIContracts.md),
  `examples/query_example.py`, the Streamlit UI) call the wrong path and 404.
- **How to validate:** assert against the live OpenAPI schema at `/docs`; smoke-test each path.

### ASSUMPTION-014 — Single `app` container hosts both interfaces
- **Statement:** The committed `docker-compose.yml` runs **FastAPI (`:8000`) and Streamlit
  (`:8501`) inside one `app` service**, not two separate `streamlit` + `api` services as the
  plan's service list implies.
- **Rationale:** Simplicity and shared process/config; the plan lists interfaces logically,
  not as a binding container topology.
- **Impact if wrong:** if independent scaling is required, the compose file and
  [`Deployment.md`](../01_architecture/Deployment.md) must split the services.
- **How to validate:** confirm both ports respond from the single container; split later only
  if scaling needs diverge.

### ASSUMPTION-015 — Qdrant payload persists a metadata subset & latency typing
- **Statement:** The Qdrant payload persists **7 of the 9 `DocumentMetadata` fields** (the
  full model remains the domain contract), and `user_feedback.latency_seconds` is stored as
  **VARCHAR** in PostgreSQL rather than a numeric type.
- **Rationale:** Current `storage/vector_db.py`/`storage/relational_db.py` implementations;
  full-fidelity payload and numeric typing are refinements, not blockers.
- **Impact if wrong:** metadata filtering on the two omitted fields is unavailable, and
  numeric aggregation over latency requires a cast ([`DataModel.md`](../01_architecture/DataModel.md),
  [`Observability.md`](../01_architecture/Observability.md)).
- **How to validate:** inspect a stored point payload and the `user_feedback` DDL; widen the
  payload / retype the column if filtering or aggregation needs it.

### ASSUMPTION-016 — Query-log table is a planned extension
- **Statement:** No `query_log` table exists in code today; query telemetry flows through
  Prometheus and (for rated turns) the `user_feedback` table. `query_log` is documented as a
  **planned extension**, not an existing schema.
- **Rationale:** Avoids inventing a schema absent from the source; monitoring needs are met by
  metrics + feedback.
- **Impact if wrong:** per-query historical analytics (beyond rated turns) require adding the
  table before the corresponding Grafana/SQL panels can populate.
- **How to validate:** if analytics require it, add the table under a dedicated task and update
  [`DataModel.md`](../01_architecture/DataModel.md).

### ASSUMPTION-SRCLOG — Source-distribution logging extension *(alias of ASSUMPTION-016 scope)*
- **Statement:** The Grafana "source distribution" and "top questions" panels rely on a small
  **source-usage logging extension** (persisting which sources/queries were used per turn) that
  is **not yet emitted** by the current metrics/feedback path.
- **Rationale:** No existing Prometheus metric carries per-source usage; the panels are spec'd
  against a Postgres/SQL source pending that extension.
- **Impact if wrong:** those two dashboard panels stay empty until the logging is added.
- **How to validate:** implement `sources_used` logging in the RAG turn and confirm the panels
  populate. Referenced by [`Observability.md`](../01_architecture/Observability.md).

### ASSUMPTION-PRECOMMIT — Pre-commit hook framework *(alias of CodingStandards Appendix A)*
- **Statement:** Local quality enforcement assumes the **`pre-commit`** framework runs ruff +
  mypy before commit, mirroring the CI gates.
- **Rationale:** The plan mandates lint/type/coverage gates; `pre-commit` is the conventional
  local mechanism and is referenced by
  [`CodingStandards.md`](../01_architecture/CodingStandards.md) Appendix A.
- **Impact if wrong:** if `pre-commit` is not adopted, gates run only in CI and local feedback
  is slower; no functional impact.
- **How to validate:** confirm a `.pre-commit-config.yaml` exists or document CI-only enforcement.

### ASSUMPTION-LANG — Python runtime floor *(alias of [ASSUMPTION-001](#assumption-001--python-runtime-floor))*
- **Statement:** Same ambiguity as ASSUMPTION-001 (plan says "Python 3.11+"; `pyproject.toml`/
  ruff/mypy/CI pin 3.10). Referenced under the `ASSUMPTION-LANG` label by
  [`CodingStandards.md`](../01_architecture/CodingStandards.md) Appendix A. Canonical entry:
  **ASSUMPTION-001**.

---

## Cross-References

- [`SUCCESS_CRITERIA.md`](./SUCCESS_CRITERIA.md) — SC-012/014/023 qualified here.
- [`Risks.md`](./Risks.md) — risks arising from these assumptions.
- [`TECH_STACK.md`](./TECH_STACK.md) · [`ROADMAP.md`](./ROADMAP.md) · [`Backlog.md`](./Backlog.md)
- ADRs `docs/04_decisions/` — where an assumption becomes a ratified decision.
