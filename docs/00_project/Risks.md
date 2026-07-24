# Risks.md - Project Risk Register

## Objective

Maintain the **risk register** for the Pokemon TCG Rules RAG Expert Assistant: identified
threats to delivery, quality, and compliance, each with a likelihood/impact assessment, a
concrete mitigation, an owner, and traceability to the requirements
([`REQUIREMENTS.md`](./REQUIREMENTS.md)) and decisions (`docs/04_decisions/`) they touch.

## Scope

- **In scope:** technical, operational, domain, and legal risks that could prevent meeting
  [`SUCCESS_CRITERIA.md`](./SUCCESS_CRITERIA.md).
- **Out of scope:** granular per-task risks (handled inline in `docs/03_tasks/`).

**Likelihood / Impact scale:** Low / Medium / High.
**Owner roles:** Data Eng (ingestion), ML Eng (retrieval/LLM/eval), Platform (infra/deploy),
Lead (governance). Roles, not individuals.

---

## 1. Risk Heat Overview

```mermaid
quadrantChart
    title Likelihood vs Impact
    x-axis Low Likelihood --> High Likelihood
    y-axis Low Impact --> High Impact
    quadrant-1 Mitigate now
    quadrant-2 Monitor closely
    quadrant-3 Accept / watch
    quadrant-4 Contingency plan
    RISK-001 Scraping fragility: [0.75, 0.7]
    RISK-002 PDF extraction: [0.6, 0.75]
    RISK-003 Embedding cost: [0.45, 0.5]
    RISK-004 LLM hallucination: [0.5, 0.9]
    RISK-005 Qdrant/reranker memory: [0.5, 0.6]
    RISK-006 Source license/ToS: [0.4, 0.85]
    RISK-007 Ground-truth effort: [0.7, 0.6]
    RISK-008 Reproducibility drift: [0.55, 0.7]
```

---

## 2. Risk Register

| ID | Category | Description | Likelihood | Impact | Mitigation | Owner | Linked REQ / ADR |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RISK-001** | Technical / Operational | **Scraping fragility.** Pokegym and pokemon.com HTML markup or URLs change, breaking the crawler and the Ban/Promo/Mega scrapers. | High | High | Isolate selectors in one module; snapshot raw HTML to `data/raw_data/html`; `tenacity` retry/backoff; schema-validate parsed fields; alert on 0-record extraction; regression test parsers against saved fixtures. | Data Eng | REQ-001, REQ-003 |
| **RISK-002** | Technical / Domain | **PDF extraction quality.** Errata/handbook PDFs use dense/tabular layouts; PyMuPDF may mis-order text or lose section/page structure, corrupting citations. | Medium | High | Use pymupdf4llm for structure; QA spot-checks vs source pages; keep `page_number`/`section_title` in `DocumentMetadata`; add layout-specific parsing/OCR fallback only where QA fails. See [ASSUMPTION-010](./Assumptions.md). | Data Eng | REQ-002, REQ-004, [ADR_003](../04_decisions/ADR_003_CHUNKING.md) |
| **RISK-003** | Operational / Cost | **Embedding & LLM cost/time.** Full-corpus embedding and the embedding/model A/B experiments consume compute (local GPU/CPU time) or paid API tokens. | Medium | Medium | Default to local BGE embeddings (no per-call cost); batch embeddings; cache by content checksum; cap OpenAI usage to the comparison subset; log token spend. See [ASSUMPTION-003](./Assumptions.md). | ML Eng | REQ-005, REQ-006, REQ-019, [ADR_002](../04_decisions/ADR_002_EMBEDDINGS.md) |
| **RISK-004** | Technical / Domain | **LLM hallucination.** Model invents card interactions or rules not in context, or fails to cite, undermining trust. | Medium | High | Certified-Judge system prompt (answer only from context, always cite, say "I don't know"); temperature 0.0; Faithfulness gate > 0.85 ([SC-006](./SUCCESS_CRITERIA.md)); citation-resolvability check ([SC-008](./SUCCESS_CRITERIA.md)); adversarial no-answer probe ([SC-011](./SUCCESS_CRITERIA.md)). | ML Eng | REQ-011, REQ-012, REQ-019 |
| **RISK-005** | Technical / Operational | **Memory footprint.** Qdrant vectors plus torch + BGE embedder + cross-encoder reranker exceed container/host memory, causing OOM or slow rerank. | Medium | Medium | Pin container memory limits; lazy-load models; use CPU-friendly batch sizes; cap reranker input to fused top-N; measure in `docs/04_tests/PERFORMANCE.md`; enforce P95 latency ([SC-013](./SUCCESS_CRITERIA.md)). | Platform | REQ-005, REQ-009, REQ-015 |
| **RISK-006** | Legal / Domain | **Source license / ToS.** Pokegym and pokemon.com content is copyrighted; scraping/redistribution or public cloud hosting may violate ToS. | Low | High | Non-commercial educational use; cite sources + dates; honor robots.txt and rate limits; do not redistribute raw corpus; keep raw data out of public repo/deploy if required. See [ASSUMPTION-006](./Assumptions.md), [ASSUMPTION-011](./Assumptions.md). | Lead | REQ-001, REQ-020 |
| **RISK-007** | Operational | **Evaluation ground-truth effort.** Authoring and labeling 100 questions with expected source docs is labor-intensive and subjective. | High | Medium | Bootstrap from actual sources; template question/expected-source pairs; peer-review a sample; version the dataset; reuse across regression runs. See [ASSUMPTION-012](./Assumptions.md). | ML Eng | REQ-018, REQ-019 |
| **RISK-008** | Technical / Operational | **Reproducibility drift.** Unpinned images/model revisions or `latest` tags cause different results across machines, failing the reproducibility criterion. | Medium | High | Pin all deps ([SC-019](./SUCCESS_CRITERIA.md)); pin Docker image tags (no `latest`); pin HF model revisions; clean-clone validation ([SC-024](./SUCCESS_CRITERIA.md)); CI enforces `ruff`/`mypy`/coverage. See [ASSUMPTION-001](./Assumptions.md). | Platform | REQ-016, REQ-017 |
| **RISK-009** | Operational | **Cloud deploy overrun (bonus).** Managed hosting resource limits (memory for models, cold starts) make the public deploy unstable or costly. | Medium | Low | Treat as bonus, not blocking ([SC-023](./SUCCESS_CRITERIA.md)); prefer a slimmed profile (smaller/remote embeddings) for cloud; document limits. See [ASSUMPTION-009](./Assumptions.md). | Platform | REQ-020 |
| **RISK-010** | Technical | **Retrieval quality below target.** Best strategy fails Recall@10 > 0.90 due to chunking/embedding choices. | Medium | High | Run 4-strategy comparison + chunk-size/embedding ablations; select best; regression gate blocks merges that lower Recall. | ML Eng | REQ-018, [ADR_003](../04_decisions/ADR_003_CHUNKING.md) |

---

## 3. Monitoring & Review

| Trigger | Risks reviewed |
| :--- | :--- |
| Ingestion run produces 0/low records | RISK-001, RISK-002 |
| Retrieval regression run | RISK-010, RISK-003 |
| LLM regression run | RISK-004, RISK-003 |
| Container OOM / latency breach | RISK-005, RISK-008 |
| Before public/cloud deploy | RISK-006, RISK-009 |

Risks are re-scored at each sprint boundary (see [`ROADMAP.md`](./ROADMAP.md)). Any risk that
materializes into a defect gets a regression test per the plan's TDD rule.

---

## Cross-References

- [`REQUIREMENTS.md`](./REQUIREMENTS.md) · [`SUCCESS_CRITERIA.md`](./SUCCESS_CRITERIA.md) · [`Assumptions.md`](./Assumptions.md)
- [`ROADMAP.md`](./ROADMAP.md) — phase-level risk callouts.
- ADRs `docs/04_decisions/` — decisions that mitigate these risks.
