# TASKS_SPRINT_18 — Scale, Cloud & Production Qualification

Index: [`TASK_INDEX.md`](./TASK_INDEX.md) · Backlog:
[`CONSOLIDATED_BACKLOG.md`](./CONSOLIDATED_BACKLOG.md).

---

### TASK-086 — Add safe cache, metadata filtering and MMR policy

| Field | Value |
| :--- | :--- |
| Sprint / REQ | SPRINT_18_PRODUCTION_QUALIFICATION · REQ-040 |
| Depends on / unblocks | TASK-073, TASK-075 / TASK-087 |
| Files affected | cache adapters/keys, retrieval filters, MMR stage, policy tests |
| Branch | `feat/task-086-cache-filter-mmr` |

**Origin.** TECH-25, TECH-26. **Objective.** Reduce repeated work and improve result diversity
without crossing principals/corpus versions or hiding stale results.

**Steps.**
1. Define cacheable stages, content-addressed keys, TTL/size, stampede and failure behavior.
2. Include tenant/policy/corpus/model/prompt/config versions; never cache sensitive feedback.
3. Expose allowlisted typed metadata filters and bounded MMR configuration.
4. Measure hit rate, latency/cost saving and relevance/diversity delta before enabling defaults.

**Mandatory test:** `TEST-174` — cache isolation/invalidation/stampede plus filter/MMR quality
policy suite.

**DoD.** No cross-principal/version leakage occurs; updates invalidate safely; enabled policy
meets the approved quality delta and records cache metrics.

**Commit:** `feat(performance): add safe cache filters and mmr (TASK-086)`

---

### TASK-087 — Qualify warm-up, batching, concurrency and cost

| Field | Value |
| :--- | :--- |
| Sprint / REQ | SPRINT_18_PRODUCTION_QUALIFICATION · REQ-040 |
| Depends on / unblocks | TASK-047, TASK-080, TASK-082, TASK-086 / TASK-088, TASK-090 |
| Files affected | model lifecycle, batch/queue controls, k6/Locust suite, performance report |
| Branch | `perf/task-087-runtime-qualification` |

**Origin.** TECH-28. **Objective.** Establish realistic capacity, latency and cost limits for cold,
warm, burst and dependency-degraded workloads.

**Steps.**
1. Preload selected models/indexes with readiness gating and bounded memory/startup.
2. Implement bounded queues/batches/concurrency with backpressure and cancellation.
3. Run reproducible load shapes using representative queries and controlled provider behavior.
4. Report P50/P95/P99, throughput, errors, saturation, tokens/cost and recommended capacity.

**Mandatory test:** `TEST-175` — cold/warm/burst/soak/degraded performance and budget gate.

**DoD.** Warm query P50 <2s and P95 <4s or an approved SLO revision; no overload collapse; cost
budget and capacity assumptions are documented with raw results.

**Commit:** `perf(runtime): qualify latency capacity and cost (TASK-087)`

---

### TASK-088 — Deploy immutable artifacts to cloud staging

| Field | Value |
| :--- | :--- |
| Sprint / REQ | SPRINT_18_PRODUCTION_QUALIFICATION · REQ-041 |
| Depends on / unblocks | TASK-055, TASK-058, TASK-069, TASK-083, TASK-087 / TASK-089, TASK-090 |
| Files affected | deployment pipeline, environment config, DNS/TLS, remote smoke/evidence |
| Branch | `ci/task-088-cloud-staging-deploy` |

**Origin.** TECH-21, TECH-30. **Objective.** Prove IaC by deploying the signed digest to an
isolated staging environment and testing it remotely.

**Steps.**
1. Select/document target and provision least-privilege secret, network, data and telemetry resources.
2. Promote an approved signed image digest through an approval-protected deployment job.
3. Run migrations/seed safely, wait for readiness and execute authenticated remote smoke/E2E.
4. Retain sanitized URL, digest, IaC plan/apply, test and teardown/cost evidence.

**Mandatory test:** `TEST-176` — automated staging deployment, TLS/readiness and remote smoke gate.

**DoD.** A reachable TLS staging URL serves the approved digest and real query/feedback flow;
deployment is repeatable and no credential is stored in artifacts.

**Commit:** `ci(deploy): prove cloud staging deployment (TASK-088)`

---

### TASK-089 — Exercise backup, restore, rollback and DORA metrics

| Field | Value |
| :--- | :--- |
| Sprint / REQ | SPRINT_18_PRODUCTION_QUALIFICATION · REQ-041 |
| Depends on / unblocks | TASK-051, TASK-055, TASK-083, TASK-088 / TASK-090 |
| Files affected | backup/restore/rollback automation, drill runbooks, DORA collector |
| Branch | `test/task-089-recovery-rollback-drill` |

**Origin.** TECH-30. **Objective.** Demonstrate data recovery and safe release rollback while
measuring delivery/incident performance.

**Steps.**
1. Define RPO/RTO and encrypted retention for Postgres, Qdrant and corpus manifests.
2. Restore into an isolated environment and verify counts, hashes, ownership and query behavior.
3. Roll back a deliberately failing release without database corruption or unsupported downgrade.
4. Calculate deployment frequency, lead time, change failure rate and MTTR from auditable events.

**Mandatory test:** `TEST-177` — timed isolated restore, failed-release rollback and DORA evidence.

**DoD.** Drill meets approved RPO/RTO, restored data is consistent, rollback returns service to
SLO and DORA metrics are generated without manual fabrication.

**Commit:** `test(operations): exercise recovery and rollback (TASK-089)`

---

### TASK-090 — Execute final production scorecard and release gate

| Field | Value |
| :--- | :--- |
| Sprint / REQ | SPRINT_18_PRODUCTION_QUALIFICATION · REQ-042 |
| Depends on / unblocks | TASK-060, TASK-070, TASK-075, TASK-080, TASK-085, TASK-087..089 / production decision |
| Files affected | scorecard, finding registers, release checklist, evidence index, ADRs |
| Branch | `chore/task-090-production-scorecard` |

**Origin.** TECH-08, TECH-19, TECH-30 and program closure. **Objective.** Produce an accountable,
evidence-backed go/no-go decision covering every security and technical audit finding.

**Steps.**
1. Re-run clean-clone quality/security, real E2E, retrieval/LLM, SLO/load and remote smoke gates.
2. Map SEC-01..17 and TECH-01..30 to implementation commit, test, artifact and criterion.
3. Re-score architecture/RAG maturity using only retained current evidence.
4. Record owner/expiry/compensating control for residual risk and collect required approvals.

**Mandatory test:** `TEST-178` — evidence freshness/completeness and all-blocking-gates release
test.

**DoD.** All 47 findings are closed or explicitly accepted; every blocking SC is green; artifacts
match released hashes; Security, Tech Lead and Product record a go/no-go decision.

**Commit:** `chore(release): publish production qualification (TASK-090)`
