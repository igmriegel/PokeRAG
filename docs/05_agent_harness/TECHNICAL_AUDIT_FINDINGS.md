# TECHNICAL_AUDIT_FINDINGS — Baseline & Closure Register

> Official planning baseline for the technical assessment performed against application code,
> tests, data, documentation and infrastructure at commit `5015e93`. Security findings
> SEC-01..SEC-17 remain governed by
> [`SECURITY_REMEDIATION_PLAN.md`](./SECURITY_REMEDIATION_PLAN.md).

## Closure Rule

A finding is closed only when every mapped task is `Done`, its mandatory tests pass in the
active CI workflow, and the linked success criterion has retained evidence. Documentation or
an unexecuted manifest alone cannot close a finding.

## Technical Finding Register

| ID | Severity | Finding / evidence | Remediation task(s) | Verification |
| :--- | :--- | :--- | :--- | :--- |
| TECH-01 | Critical | FastAPI has no production composition root; `RAGChain` and `FeedbackStore` remain `None`, so `/query` and `/feedback` return 503. | TASK-057, TASK-064, TASK-065 | TEST-145, TEST-152, TEST-153 |
| TECH-02 | High | Health reports `healthy` when both required dependencies are unavailable; liveness and readiness are conflated. | TASK-057, TASK-064 | TEST-145, TEST-152 |
| TECH-03 | High | BM25 is never hydrated from the persisted corpus; the only executable example constructs `BM25Retriever([])`. | TASK-061, TASK-064 | TEST-149, TEST-152 |
| TECH-04 | Medium | API validates `top_k` but does not propagate it; `RAGChain` always uses the global final top-k. | TASK-062 | TEST-150 |
| TECH-05 | Critical | `data/` is fully ignored; a clean clone has no corpus, benchmark or deterministic seed fixture. Local data has only one sample chunk. | TASK-063, TASK-069, TASK-071 | TEST-151, TEST-157, TEST-159 |
| TECH-06 | High | Retrieval evaluation defaults fabricate relevant/noise chunks instead of invoking Dense, BM25, Hybrid and Rerank implementations. | TASK-072, TASK-075 | TEST-160, TEST-163 |
| TECH-07 | High | LLM evaluation uses hardcoded scores and reference answers; RAGAS/DeepEval dependencies are not used. | TASK-076, TASK-077, TASK-080 | TEST-164, TEST-165, TEST-168 |
| TECH-08 | High | README benchmark values have no versioned report, corpus hash, command output or model evidence. | TASK-070, TASK-075, TASK-080, TASK-090 | TEST-158, TEST-163, TEST-168, TEST-178 |
| TECH-09 | Medium | The 100-question benchmark is templated, locally ignored and lacks demonstrated human/source review. | TASK-071, TASK-078 | TEST-159, TEST-166 |
| TECH-10 | High | Web UI/API exist but are not usable by third parties because runtime wiring is absent. | TASK-057, TASK-064, TASK-069 | TEST-145, TEST-152, TEST-157 |
| TECH-11 | High | Feedback persistence exists in isolation but is unavailable through the running application. | TASK-050, TASK-057, TASK-065, TASK-083 | TEST-138, TEST-145, TEST-153, TEST-171 |
| TECH-12 | High | Test suite passes 146 tests but fails the declared 90% gate at 83.52%. | TASK-067 | TEST-155 |
| TECH-13 | High | Integration/smoke/e2e suites rely predominantly on fakes, SQLite memory or YAML inspection and do not validate the real stack. | TASK-068, TASK-069 | TEST-156, TEST-157 |
| TECH-14 | Medium | Ruff gate has outstanding import/SIM violations. | TASK-066 | TEST-154 |
| TECH-15 | Medium | `mypy --strict` fails on missing stubs and incompatible environment typing. | TASK-066 | TEST-154 |
| TECH-16 | Medium | Black is declared as mandatory but unavailable in the installed development environment. | TASK-066, TASK-067 | TEST-154, TEST-155 |
| TECH-17 | Critical | CI is outside `.github/workflows` and uses Python 3.10 while package metadata requires 3.11+. | TASK-041, TASK-042, TASK-067 | TEST-129, TEST-130, TEST-155 |
| TECH-18 | High | Dependencies are duplicated across files without a hashed lock/profile strategy; clean-install evidence is absent. | TASK-041, TASK-067 | TEST-129, TEST-155 |
| TECH-19 | Medium | README clone URL, Make targets, runtime versions and operational claims diverge from the repository. | TASK-070, TASK-090 | TEST-158, TEST-178 |
| TECH-20 | High | Containers are single-stage/root, include compilers/dev tooling/tests, and lack production image evidence. | TASK-052, TASK-058 | TEST-140, TEST-146 |
| TECH-21 | Medium | Render/Kubernetes IaC exists, but there is no successful remote deployment, reachable URL or remote smoke evidence. | TASK-055, TASK-088 | TEST-143, TEST-176 |
| TECH-22 | High | Prompt is sent entirely as a user message and citations are copied from retrieved metadata without validating that model claims cite/entail them. | TASK-048, TASK-079 | TEST-136, TEST-167 |
| TECH-23 | Medium | Metrics/dashboard definitions exist, but no populated-dashboard evidence, alerting, trace correlation or end-to-end feedback telemetry exists. | TASK-081, TASK-082, TASK-083 | TEST-169, TEST-170, TEST-171 |
| TECH-24 | Medium | Ingestion reprocesses the corpus; no manifest-driven incremental add/update/delete lifecycle is implemented. | TASK-056, TASK-074 | TEST-144, TEST-162 |
| TECH-25 | Medium | No cache strategy exists for embeddings, rewrites, retrieval results or safe generation responses. | TASK-086 | TEST-174 |
| TECH-26 | Low | Metadata filtering exists only in the Qdrant wrapper and is not exposed through retrieval/API; no diversity stage such as MMR is implemented. | TASK-073, TASK-086 | TEST-161, TEST-174 |
| TECH-27 | Medium | No real ablation compares chunk size/overlap, embedding model, query rewrite, reranking or retrieval parameters. | TASK-073, TASK-075 | TEST-161, TEST-163 |
| TECH-28 | Medium | Model lifecycle lacks explicit warm-up, bounded batching and realistic concurrency/latency/cost tests. | TASK-047, TASK-082, TASK-087 | TEST-135, TEST-170, TEST-175 |
| TECH-29 | Low | UI lacks answer history, citation copy/open affordances, comment capture and explicit degraded-state guidance. | TASK-084 | TEST-172 |
| TECH-30 | Medium | Operational runbooks, backup/restore drills, rollback evidence, DORA metrics and final production scorecard are absent. | TASK-085, TASK-088, TASK-089, TASK-090 | TEST-173, TEST-176, TEST-177, TEST-178 |

## Coverage Assertion

- TECH-01..TECH-30: all mapped to at least one implementation task and one mandatory test.
- SEC-01..SEC-17: all mapped in the security remediation plan.
- **Discarded findings: 0. Deferred findings: 0.** Lower-severity opportunities remain planned
  in dependency order rather than being removed; priority affects sequencing, never traceability.
- Tasks may close multiple findings, but no finding may be closed by a task that only changes
  documentation unless the finding itself is a documentation defect.
