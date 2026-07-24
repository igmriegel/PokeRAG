# SUCCESS_CRITERIA.md - Quantifiable Acceptance Thresholds

## Objective

Define the **measurable, verifiable pass/fail thresholds** that determine whether the
Pokemon TCG Rules RAG Expert Assistant is considered "done" and rubric-complete. Every
criterion carries a stable ID (`SC-###`), a single metric, an explicit numeric target, a
documented measurement procedure, and a cross-link to the requirement (`REQ-###`) it
validates. These criteria are the executable interpretation of
[`REQUIREMENTS.md`](./REQUIREMENTS.md) and the DataTalks / LLM Zoomcamp scoring rubric
captured in [`PROJECT.md`](./PROJECT.md).

## Scope

- **In scope:** functional quality gates (retrieval, generation), performance SLAs,
  reproducibility, coverage, monitoring completeness, and rubric-derived thresholds.
- **Out of scope:** the *how-to-measure* implementation details of the evaluation harness
  itself — those live in `docs/01_architecture/EvaluationPlan.md`. This document states the
  **numbers**; the evaluation plan states the **code**.

Genuine ambiguities (e.g. whether latency includes cold model load) are recorded in
[`Assumptions.md`](./Assumptions.md) and referenced here rather than silently resolved.

---

## 1. Success Criteria Matrix

Each criterion maps to a rubric line and one or more `REQ-###`. "How measured" names the
artifact or command that produces the evidence.

| ID | Metric | Target | How Measured | Linked REQ | Rubric Line |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SC-001** | Retrieval **Recall@10** (best strategy) | **> 0.90** | `EvaluationPlan.md` harness over the 100-question benchmark; best of {Dense, BM25, Hybrid RRF, Hybrid+Rerank}. | [REQ-018](./REQUIREMENTS.md) | Retrieval evaluation |
| **SC-002** | Retrieval **Recall@5** (best strategy) | **≥ 0.80** | Same harness, cut-off at final `RETRIEVAL_FINAL_TOP_K=5`. | [REQ-018](./REQUIREMENTS.md) | Retrieval evaluation |
| **SC-003** | Retrieval **MRR** (best strategy) | **≥ 0.75** | Mean Reciprocal Rank of first relevant chunk across 100 questions. | [REQ-018](./REQUIREMENTS.md) | Retrieval evaluation |
| **SC-004** | Retrieval **Hit Rate@10** | **≥ 0.92** | Fraction of questions with ≥1 relevant chunk in top 10. | [REQ-018](./REQUIREMENTS.md) | Retrieval evaluation |
| **SC-005** | **Multiple** retrieval strategies compared | **≥ 4** strategies benchmarked, best selected & documented | Comparison table in eval report (Dense vs BM25 vs Hybrid vs Hybrid+Rerank). | [REQ-006](./REQUIREMENTS.md)–[REQ-009](./REQUIREMENTS.md), [REQ-018](./REQUIREMENTS.md) | Retrieval evaluation (2 pts) |
| **SC-006** | LLM **Faithfulness** (RAGAS) | **> 0.85** | RAGAS `faithfulness` over benchmark answers with retrieved context. | [REQ-019](./REQUIREMENTS.md), [REQ-011](./REQUIREMENTS.md) | LLM evaluation |
| **SC-007** | LLM **Answer Correctness** | **≥ 0.80** | RAGAS/DeepEval correctness vs reference answers. | [REQ-019](./REQUIREMENTS.md) | LLM evaluation |
| **SC-008** | LLM **Citation Quality** | **≥ 0.90** answers with ≥1 valid, resolvable citation | Automated check that each `AnswerResponse.citations[*]` resolves to an indexed source. | [REQ-012](./REQUIREMENTS.md) | LLM evaluation |
| **SC-009** | LLM **Completeness** | **≥ 0.75** | DeepEval/RAGAS completeness metric vs reference. | [REQ-019](./REQUIREMENTS.md) | LLM evaluation |
| **SC-010** | **Multiple** LLM approaches compared | ≥ 2 prompts **and** ≥ 2 models, best selected | Prompt A vs Prompt B; `gpt-4o-mini` vs `gpt-4.1-mini` comparison table. | [REQ-019](./REQUIREMENTS.md) | LLM evaluation (2 pts) |
| **SC-011** | **Grounding / abstention** | 100% of unsupported queries return "I don't know" (no fabricated rule) on a 10-item adversarial set | Adversarial no-answer probe set; manual + automated review. | [REQ-011](./REQUIREMENTS.md) | LLM evaluation |
| **SC-012** | **Mean end-to-end query latency** | **< 2.0 s** (excludes one-time model warm-up) | P50 of `AnswerResponse.latency_seconds` over benchmark, warm cache. See [ASSUMPTION-007](./Assumptions.md). | [REQ-015](./REQUIREMENTS.md) | Reproducibility / NFR |
| **SC-013** | **P95 query latency** | **< 4.0 s** | 95th percentile of `latency_seconds` over benchmark. | [REQ-015](./REQUIREMENTS.md) | NFR |
| **SC-014** | **`docker compose up` startup** | Stack **healthy < 60 s** (image build & model download excluded) | Time from `up` to all healthchecks green, images pre-pulled. See [ASSUMPTION-008](./Assumptions.md). | [REQ-016](./REQUIREMENTS.md) | Containerization / Reproducibility |
| **SC-015** | **Documents fully indexed** | **100%** of 9 official sources ingested; 0 hard failures | Ingestion report: `sources_expected == sources_indexed`; chunk count > 0 per source. | [REQ-001](./REQUIREMENTS.md)–[REQ-005](./REQUIREMENTS.md) | Ingestion pipeline |
| **SC-016** | **Test coverage** | **≥ 90%** line coverage on `src/pokemon_tcg_rag` | `pytest --cov` gate (see [`pyproject.toml`](../../pyproject.toml) `addopts`). | [REQ-017](./REQUIREMENTS.md) | Reproducibility |
| **SC-017** | **Grafana dashboard** | **≥ 5 charts** live with real data | Dashboard JSON panel count + screenshot; feedback also collected. | [REQ-015](./REQUIREMENTS.md), [REQ-014](./REQUIREMENTS.md) | Monitoring (2 pts) |
| **SC-018** | **Feedback persistence** | 100% of 👍/👎 events written to Postgres | Query `feedback` table row count vs UI events in a scripted run. | [REQ-014](./REQUIREMENTS.md) | Monitoring |
| **SC-019** | **Dependency pinning** | 100% of runtime deps version-constrained | Lint of [`requirements.txt`](../../requirements.txt) / [`pyproject.toml`](../../pyproject.toml): every entry has a version specifier. | [REQ-016](./REQUIREMENTS.md), [REQ-017](./REQUIREMENTS.md) | Reproducibility (2 pts) |
| **SC-020** | **Static quality gate** | `ruff` 0 errors, `mypy --strict` 0 errors | CI job under `ci/`; see `pyproject.toml` `[tool.ruff]` / `[tool.mypy]`. | [REQ-017](./REQUIREMENTS.md) | Reproducibility |
| **SC-021** | **API contract** | `/query`, `/feedback`, `/health` respond per OpenAPI schema | Integration test hitting FastAPI (`AnswerResponse` / `FeedbackRecord` shape). | [REQ-013](./REQUIREMENTS.md), [REQ-014](./REQUIREMENTS.md) | Interface (2 pts) |
| **SC-022** | **Best-practice features present** | Hybrid search + Reranking + Query rewriting all implemented **and** ablated | Eval report shows on/off comparison for each of the 3. | [REQ-008](./REQUIREMENTS.md), [REQ-009](./REQUIREMENTS.md), [REQ-010](./REQUIREMENTS.md) | Best practices (3 pts) |
| **SC-023** | **Cloud deploy (bonus)** | Public reachable URL on Render/Railway/AWS | Live URL + `/health` 200 from public internet. See [ASSUMPTION-009](./Assumptions.md). | [REQ-020](./REQUIREMENTS.md) | Bonus (2 pts) |
| **SC-024** | **Reproducible from clean clone** | Fresh clone → `.env` → `docker compose up` → answered query, no manual patching | Documented in README; validated on a clean machine/CI. | [REQ-016](./REQUIREMENTS.md) | Reproducibility (2 pts) |

---

## 2. Rubric-to-Criteria Coverage

```mermaid
graph LR
    subgraph Rubric[DataTalks Rubric Lines]
        R1[Problem description]
        R2[Retrieval flow]
        R3[Retrieval evaluation]
        R4[LLM evaluation]
        R5[Interface]
        R6[Ingestion pipeline]
        R7[Monitoring]
        R8[Containerization]
        R9[Reproducibility]
        R10[Best practices x3]
        R11[Bonus: cloud]
    end
    R3 --> SC001[SC-001..005]
    R4 --> SC006[SC-006..011]
    R5 --> SC021[SC-021]
    R6 --> SC015[SC-015]
    R7 --> SC017[SC-017,018]
    R8 --> SC014[SC-014]
    R9 --> SC016[SC-016,019,020,024]
    R10 --> SC022[SC-022]
    R11 --> SC023[SC-023]
    R2 --> SC001
    R2 --> SC021
```

`R1` (Problem description) is satisfied narratively by [`PROJECT.md`](./PROJECT.md) §2 and
has no numeric threshold. `R2` (Retrieval flow: KB + LLM both used) is proven by SC-001
(retrieval works) combined with SC-021 (the `/query` flow returns a grounded answer).

---

## 3. Measurement Cadence & Gates

| Gate | When | Criteria enforced | Blocking? |
| :--- | :--- | :--- | :--- |
| **Per-PR quality gate** | Every pull request | SC-016, SC-019, SC-020 | Yes |
| **Smoke gate** | Every PR / nightly | SC-014, SC-021 (basic) | Yes |
| **Retrieval regression** | After any retrieval/chunking change | SC-001–SC-005 | Yes — must not regress vs baseline |
| **LLM regression** | After any prompt/model change | SC-006–SC-011 | Yes — must not regress vs baseline |
| **Release / demo gate** | Before final submission | All SC-### | Yes |
| **Bonus gate** | Optional | SC-023 | No |

Regression rule (from the plan's TDD section): if a change lowers Recall, Faithfulness, or
raises latency past its target, the pipeline **fails**. Baselines are stored alongside the
evaluation report described in `docs/01_architecture/EvaluationPlan.md`.

---

## 4. Acceptance Definition

The project is **accepted** when:

1. Every `SC-###` with a "Yes" blocking gate passes at its stated target.
2. The best retrieval strategy (SC-005) and best LLM configuration (SC-010) are explicitly
   documented with the comparison evidence.
3. A clean-clone reproducibility run (SC-024) succeeds end-to-end.

Bonus criteria (SC-023) are additive and do not block acceptance.

---

## Cross-References

- [`REQUIREMENTS.md`](./REQUIREMENTS.md) — requirement definitions (REQ-###).
- [`PROJECT.md`](./PROJECT.md) — problem statement and rubric.
- [`ROADMAP.md`](./ROADMAP.md) — the phases/sprints that deliver each criterion.
- [`Risks.md`](./Risks.md) — risks threatening these targets.
- [`Assumptions.md`](./Assumptions.md) — ASSUMPTION-007/008/009 qualify SC-012/014/023.
- `docs/01_architecture/EvaluationPlan.md` — measurement implementation.
