# Backlog.md - Prioritized Product & Engineering Backlog

## Objective

Maintain the original product-level backlog for the Pokemon TCG Rules RAG Expert Assistant:
every deliverable from the source plan plus stretch items, each with a MoSCoW priority, a
link to the requirement it satisfies ([`REQUIREMENTS.md`](./REQUIREMENTS.md)), a target
sprint (`docs/02_sprints/`), and a status. The backlog is the flat, sortable view; the
  [`ROADMAP.md`](./ROADMAP.md) provides the phased ordering. The authoritative audit-remediation
  and production-evolution backlog—including origin, criticality, story points, effort,
  dependencies, owner and DoD—is
  [`CONSOLIDATED_BACKLOG.md`](../03_tasks/CONSOLIDATED_BACKLOG.md).

## Scope

- **In scope:** original functional/non-functional work items and stretch experiments through
  Sprint 12. Sprints 13–18 are represented by TASK-061..090 in the consolidated backlog.
- **Out of scope:** task-level breakdown (see `docs/03_tasks/`).

**MoSCoW:** Must / Should / Could / Won't (this iteration).
**Status:** Todo / In-Progress / Done / Deferred.

---

## 1. Priority Distribution

```mermaid
pie title Backlog by MoSCoW
    "Must" : 36
    "Should" : 4
    "Could" : 5
```

---

## 2. Backlog Table

| ID | Title | Description | Priority | Linked REQ | Target Sprint | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BL-001** | Repo scaffold & config | Clean Architecture package layout, `Settings`, tooling (ruff/mypy/pytest), compose shell. | Must | REQ-016, REQ-017 | SPRINT_01 | Done |
| **BL-002** | Infra services up | Qdrant, Postgres, Prometheus, Grafana healthy in compose with provisioning. | Must | REQ-005, REQ-015, REQ-016 | SPRINT_01 | Done |
| **BL-003** | Domain models | Finalize enums + models in `domain/models.py` as shared contract. | Must | REQ-004, REQ-012 | SPRINT_01 | Done |
| **BL-004** | Pokegym crawler | Scrape all rulings; extract date/set/card/question/answer/url; save raw HTML + JSONL/Parquet. | Must | REQ-001 | SPRINT_02 | Done |
| **BL-005** | PDF downloader + extractor | Auto-download 5 official PDFs; extract with PyMuPDF/pymupdf4llm preserving structure. | Must | REQ-002 | SPRINT_02 | Done |
| **BL-006** | HTML legality scrapers | Scrape Ban List, Promo Legality, Mega Rules pages. | Must | REQ-003 | SPRINT_02 | Done |
| **BL-007** | Normalization & chunking | Normalize docs; fixed-size chunking (Pokegym = 1 chunk/ruling); metadata enrichment + stable IDs. | Must | REQ-004 | SPRINT_03 | Done |
| **BL-008** | Embed & index into Qdrant | Embed chunks with `bge-large-en-v1.5` (1024-d); index into `pokemon_tcg_rules`. | Must | REQ-005 | SPRINT_03 | Done |
| **BL-009** | Dense retrieval | Dense vector search, top-10. | Must | REQ-006 | SPRINT_04 | Done |
| **BL-010** | BM25 retrieval | Lexical retrieval via `rank-bm25`, top-10. | Must | REQ-007 | SPRINT_04 | Done |
| **BL-011** | Hybrid search (RRF) | Fuse Dense + BM25 via Reciprocal Rank Fusion (k=60). | Must | REQ-008 | SPRINT_04 | Done |
| **BL-012** | Cross-encoder rerank | Re-rank fused candidates with `bge-reranker-large`; final top-5. | Must | REQ-009 | SPRINT_04 | Done |
| **BL-013** | Query rewriting | LLM rewrite of user query before retrieval. | Must | REQ-010 | SPRINT_05 | Done |
| **BL-014** | Prompt builder + LLM chain | Certified-Judge prompt, context assembly, citations, "I don't know" guardrail. | Must | REQ-011, REQ-012 | SPRINT_05 | Done |
| **BL-015** | FastAPI endpoints | `/query`, `/feedback`, `/health` with typed request/response. | Must | REQ-013, REQ-014 | SPRINT_05 | Done |
| **BL-016** | Streamlit UI + feedback | Answer/sources/chunks view, latency/model/#docs, 👍/👎 + comment → Postgres. | Must | REQ-013, REQ-014 | SPRINT_06 | Done |
| **BL-017** | Evaluation benchmark (100 Q) | Author/label 100 questions with expected sources. | Should | REQ-018, REQ-019 | SPRINT_07 | Done |
| **BL-018** | Retrieval evaluation | Recall@5/@10, MRR, Hit Rate across 4 strategies; pick best. | Should | REQ-018 | SPRINT_07 | Done |
| **BL-019** | LLM evaluation (RAGAS/DeepEval) | Faithfulness/Correctness/Citation/Completeness; Prompt A/B × model A/B. | Should | REQ-019 | SPRINT_07 | Done |
| **BL-020** | Grafana dashboard (≥5 charts) | Questions/day, mean latency, #docs retrieved, 👍/👎, source distribution, top questions. | Must | REQ-015 | SPRINT_08 | Done |
| **BL-021** | Full compose deploy | Always-on services up with `docker compose up`; ingestion runs only with the `ingestion` profile; startup < 60 s (warm). | Must | REQ-016 | SPRINT_08 | Done |
| **BL-022** | Prometheus metrics exporter | Instrument query count, latency, retrieval size, feedback counters. | Must | REQ-015 | SPRINT_08 | Done |
| **BL-023** | ≥90% test coverage + CI gates | Unit/integration/smoke/e2e/regression; ruff + mypy + coverage in CI. | Must | REQ-017 | SPRINT_07 | Done |
| **BL-024** | Final docs + demo video | README/setup/architecture/evaluation; reproducibility validation; demo video. | Should | REQ-016 | SPRINT_08 | Done |
| **BL-025** | Cloud deploy (bonus) | Deploy to Render/Railway/AWS; public reachable URL + `/health`. | Could | REQ-020 | SPRINT_08 | Deferred |
| **BL-026** | Second embedding model comparison | Benchmark `text-embedding-3-small` vs `bge-large-en-v1.5`; document winner. | Could | REQ-018 | SPRINT_07 | Deferred |
| **BL-027** | Semantic chunking experiment | Compare semantic vs fixed-size chunking on Recall@10. | Could | REQ-004, REQ-018 | SPRINT_07 | Deferred |
| **BL-028** | Chunk-size ablation | 256 × 512 × 1024 token comparison to fix the default. | Could | REQ-004, REQ-018 | SPRINT_07 | Deferred |
| **BL-029** | Cohere Rerank alternative | Evaluate Cohere Rerank vs `bge-reranker-large`. | Could | REQ-009, REQ-018 | SPRINT_07 | Deferred |
| **BL-030** | IaC / K8s manifests | Deployment manifests for cloud hosting. | Won't (this iter) | REQ-020 | SPRINT_08 | Deferred |
| **BL-031** | Secure dependency graph | Resolve conflicts/CVEs; commit hashed locks and SBOM. | Must | REQ-021 | SPRINT_09 | Done |
| **BL-032** | Activate security CI | Discoverable least-privilege workflow with baseline blocking checks. | Must | REQ-030 | SPRINT_09 | Done |
| **BL-033** | Isolate compose services | Remove public data ports and default credentials. | Must | REQ-028 | SPRINT_09 | Done |
| **BL-034** | Block UI SSRF | Trusted backend destination plus redirect/IP/timeout defense. | Must | REQ-024 | SPRINT_09 | Done |
| **BL-035** | Scope service secrets | Explicit minimum configuration and secret injection per component. | Must | REQ-028 | SPRINT_09 | Done |
| **BL-036** | API identity and authorization | Token verification, scopes, route/object access matrix. | Must | REQ-022 | SPRINT_10 | Done |
| **BL-037** | API abuse/cost controls | Payload, rate, concurrency, timeout, retry and LLM-budget limits. | Must | REQ-023 | SPRINT_10 | Done |
| **BL-038** | Prompt/citation integrity | Untrusted-context isolation and verified retrieved citations. | Must | REQ-025 | SPRINT_10 | Done |
| **BL-039** | Safe API disclosure | Stable errors, redacted logs, protected diagnostics, CORS/headers. | Must | REQ-026 | SPRINT_10 | Done |
| **BL-040** | Feedback and data governance | Owner-bound feedback, replay protection, retention and response minimization. | Must | REQ-026 | SPRINT_10 | Done |
| **BL-041** | PostgreSQL least privilege | Separate migration/runtime roles and revoke administrative access. | Must | REQ-028 | SPRINT_11 | Done |
| **BL-042** | Rootless minimal images | Multi-stage digest-pinned non-root runtime images. | Must | REQ-027 | SPRINT_11 | Done |
| **BL-043** | Restricted K8s workloads | Security contexts, resource bounds, probes and service accounts. | Must | REQ-027 | SPRINT_11 | Done |
| **BL-044** | Network/TLS hardening | Default-deny policy, required flows only, private observability. | Must | REQ-024, REQ-028 | SPRINT_11 | Done |
| **BL-045** | Immutable canonical IaC | Remove duplicate manifests; digest/signature/provenance enforcement. | Must | REQ-021, REQ-027 | SPRINT_11 | Done |
| **BL-046** | Secure ingestion boundary | Source allowlist, parser limits, provenance and quarantine. | Must | REQ-029 | SPRINT_12 | Done |
| **BL-047** | Truthful runtime readiness | Real dependency wiring and fail-closed readiness lifecycle. | Must | REQ-023, REQ-028, REQ-030 | SPRINT_12 | Done |
| **BL-048** | Automated security gates | Secret/SAST/SCA/IaC/container scans, SBOM and policy. | Must | REQ-021, REQ-030 | SPRINT_12 | Done |
| **BL-049** | DAST and adversarial regression | Authenticated API DAST plus SSRF and LLM attack corpus. | Must | REQ-022, REQ-024, REQ-025, REQ-026, REQ-030 | SPRINT_12 | Done |
| **BL-050** | Security release closure | Re-test SEC-01..17, runbooks, residual-risk approval and go/no-go. | Must | REQ-030 | SPRINT_12 | Done |

---

## 3. Prioritization Rationale

- **Must** items are the direct path to rubric points (retrieval flow, evaluation,
  interface, ingestion, monitoring, containerization, reproducibility, and the three
  best-practice points: Hybrid, Rerank, Query rewriting).
- **Should** items (evaluation depth, docs, coverage) protect quality gates in
  [`SUCCESS_CRITERIA.md`](./SUCCESS_CRITERIA.md) and provide the comparison evidence the
  rubric's "multiple approaches, best selected" lines require.
- **Could** items are bonus/stretch experiments that raise the score ceiling but do not
  block acceptance; several are the ablations that resolve open
  [`Assumptions.md`](./Assumptions.md) (ASSUMPTION-004/005 via BL-027/BL-028).
- **Won't (this iteration)**: full IaC/K8s (BL-030) is beyond the compose-first delivery;
  revisit if cloud deploy (BL-025) is pursued seriously.
- **Security Must items (BL-031..BL-050)** implement the audit remediation plan. Critical
  containment precedes access/data controls, then platform hardening, with assurance and
  evidence last; an unaccepted Critical/High finding blocks release.

---

## Cross-References

- [`REQUIREMENTS.md`](./REQUIREMENTS.md) · [`SUCCESS_CRITERIA.md`](./SUCCESS_CRITERIA.md) · [`ROADMAP.md`](./ROADMAP.md)
- [`Assumptions.md`](./Assumptions.md) — BL-026/027/028/029 resolve open assumptions.
- [`Risks.md`](./Risks.md) — RISK-007/009/010 relate to evaluation & deploy items.
- Sprint specs `docs/02_sprints/`; tasks `docs/03_tasks/`.
