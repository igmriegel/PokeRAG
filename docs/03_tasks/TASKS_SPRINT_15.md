# TASKS_SPRINT_15 — Retrieval Quality

Index: [`TASK_INDEX.md`](./TASK_INDEX.md) · Backlog:
[`CONSOLIDATED_BACKLOG.md`](./CONSOLIDATED_BACKLOG.md).

---

### TASK-071 — Build a reviewed, versioned benchmark

| Field | Value |
| :--- | :--- |
| Sprint / REQ | SPRINT_15_RETRIEVAL_QUALITY · REQ-035 |
| Depends on / unblocks | TASK-063 / TASK-072, TASK-076 |
| Files affected | benchmark dataset/schema, source labels, review guide, dataset card |
| Branch | `feat/task-071-reviewed-benchmark` |

**Origin.** TECH-05, TECH-09. **Objective.** Replace ignored templated questions with at least
100 diverse, source-resolvable questions and reviewed labels.

**Steps.**
1. Define question taxonomy, difficulty, temporal/source scope and train/dev/test separation.
2. Label relevant source/chunk IDs and reference answers against a fixed corpus hash.
3. Run two-person review on a representative sample and adjudicate disagreement.
4. Publish dataset card, license, schema, hash and leakage/version policy.

**Mandatory test:** `TEST-159` — schema, uniqueness, source resolution, split leakage and review
completeness gate.

**DoD.** ≥100 non-templated examples resolve against the versioned corpus; labels and reviewer
evidence meet the dataset policy.

**Commit:** `feat(evaluation): add reviewed versioned benchmark (TASK-071)`

---

### TASK-072 — Use production retrieval implementations in evaluation

| Field | Value |
| :--- | :--- |
| Sprint / REQ | SPRINT_15_RETRIEVAL_QUALITY · REQ-036 |
| Depends on / unblocks | TASK-061, TASK-071 / TASK-073, TASK-075 |
| Files affected | evaluation adapters/CLI, retrieval factory, run manifest |
| Branch | `fix/task-072-real-retrieval-evaluation` |

**Origin.** TECH-06. **Objective.** Evaluate actual Dense, BM25, Hybrid and Rerank outputs,
eliminating fabricated relevant/noise handlers.

**Steps.**
1. Construct strategies through the production retrieval factory against a fixed index.
2. Emit query/result IDs, ranks, timings and configuration into an immutable run manifest.
3. Prevent default synthetic handlers in release evaluation; retain them only for unit tests.
4. Add deterministic seed, resume and failed-query accounting.

**Mandatory test:** `TEST-160` — evaluator-to-production-strategy integration and anti-synthetic
release guard.

**DoD.** Every reported metric can be traced to real ranked outputs, corpus/config hashes and
the production implementation.

**Commit:** `fix(evaluation): run real retrieval strategies (TASK-072)`

---

### TASK-073 — Execute retrieval ablations

| Field | Value |
| :--- | :--- |
| Sprint / REQ | SPRINT_15_RETRIEVAL_QUALITY · REQ-036 |
| Depends on / unblocks | TASK-072 / TASK-075, TASK-086 |
| Files affected | experiment matrix, chunk/embed/rewrite/rerank/filter/MMR configs, reports |
| Branch | `feat/task-073-retrieval-ablations` |

**Origin.** TECH-26, TECH-27. **Objective.** Compare meaningful retrieval alternatives using the
same corpus/split and quality, latency and cost metrics.

**Steps.**
1. Pre-register a bounded matrix for chunk size/overlap, embedding model and top-k/fusion.
2. Ablate rewriting, reranking, metadata filters and MMR diversity independently.
3. Repeat runs with fixed seeds; report confidence intervals and failed/empty-query rates.
4. Store content-addressed configurations and raw ranked outputs.

**Mandatory test:** `TEST-161` — experiment completeness, reproducibility and one-factor ablation
verification.

**DoD.** Each advertised feature has on/off evidence; comparisons share benchmark/corpus hashes
and include quality-latency-cost trade-offs.

**Commit:** `feat(retrieval): run reproducible ablation matrix (TASK-073)`

---

### TASK-074 — Implement incremental manifest-driven ingestion

| Field | Value |
| :--- | :--- |
| Sprint / REQ | SPRINT_15_RETRIEVAL_QUALITY · REQ-032, REQ-036 |
| Depends on / unblocks | TASK-056, TASK-063 / TASK-075 |
| Files affected | ingestion state manifest, diff engine, index/BM25 update, recovery tests |
| Branch | `feat/task-074-incremental-ingestion` |

**Origin.** TECH-24. **Objective.** Process only added/changed/deleted sources while keeping
Qdrant and BM25 atomic and consistent.

**Steps.**
1. Diff source/content/parser/config hashes against the last successful manifest.
2. Stage add/update/delete operations and publish both indexes atomically after validation.
3. Remove stale chunks, support retry/resume and retain the previous recoverable snapshot.
4. Record lineage, counts, duration and failure reason.

**Mandatory test:** `TEST-162` — add/update/delete/idempotency/interrupted-publish lifecycle suite.

**DoD.** Repeated runs converge; deltas touch only expected chunks; failed publication leaves the
previous corpus readable and parity intact.

**Commit:** `feat(ingestion): add incremental corpus lifecycle (TASK-074)`

---

### TASK-075 — Publish retrieval baseline and regression gate

| Field | Value |
| :--- | :--- |
| Sprint / REQ | SPRINT_15_RETRIEVAL_QUALITY · REQ-036 |
| Depends on / unblocks | TASK-072, TASK-073, TASK-074 / TASK-086, TASK-090 |
| Files affected | retrieval report, baseline registry, CI regression policy |
| Branch | `feat/task-075-retrieval-regression-gate` |

**Origin.** TECH-06, TECH-08, TECH-27. **Objective.** Select retrieval configuration based on real
evidence and prevent silent quality regression.

**Steps.**
1. Compare strategies using Recall@K, MRR, context precision/recall, latency and resource cost.
2. Explain selection and rejected alternatives, including confidence and known failure slices.
3. Register baseline only with benchmark/corpus/code/config hashes.
4. Fail matched evaluation on target violation or >2% relative quality regression.

**Mandatory test:** `TEST-163` — report provenance, target threshold and seeded-regression gate.

**DoD.** Selected strategy achieves Recall@10 >0.90 and MRR ≥0.75 or an approved criterion
revision; report and raw evidence are retained and CI gate is effective.

**Commit:** `feat(evaluation): gate retrieval regressions (TASK-075)`
