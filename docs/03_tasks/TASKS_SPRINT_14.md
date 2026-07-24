# TASKS_SPRINT_14 — Quality & Reproducibility

Index: [`TASK_INDEX.md`](./TASK_INDEX.md) · Backlog:
[`CONSOLIDATED_BACKLOG.md`](./CONSOLIDATED_BACKLOG.md).

---

### TASK-066 — Repair static quality gates

| Field | Value |
| :--- | :--- |
| Sprint / REQ | SPRINT_14_QUALITY_REPRODUCIBILITY · REQ-033 |
| Depends on / unblocks | TASK-042 / TASK-067 |
| Files affected | Python source/tests, pyproject, type stubs, CI quality job |
| Branch | `fix/task-066-green-static-quality` |

**Origin.** TECH-14..16. **Objective.** Make Ruff, Black and strict mypy executable and green on
the declared Python versions.

**Steps.**
1. Install/pin all declared quality tools in the canonical development lock.
2. Fix violations without blanket ignores; scope unavoidable exceptions with rationale.
3. Add missing third-party stubs or typed adapter boundaries.
4. Run identical commands locally and in the active workflow.

**Mandatory test:** `TEST-154` — zero-error Ruff, Black check and strict mypy gate.

**DoD.** All three tools run from a clean development install and report zero actionable errors;
exceptions are narrow, owned and documented.

**Commit:** `fix(quality): make static gates green (TASK-066)`

---

### TASK-067 — Enforce 90% coverage and clean-clone CI

| Field | Value |
| :--- | :--- |
| Sprint / REQ | SPRINT_14_QUALITY_REPRODUCIBILITY · REQ-033, REQ-034 |
| Depends on / unblocks | TASK-041, TASK-042, TASK-066 / TASK-068, TASK-070 |
| Files affected | tests, coverage config, lock profiles, CI runtime matrix |
| Branch | `test/task-067-coverage-clean-clone-ci` |

**Origin.** TECH-12, TECH-16..18. **Objective.** Test meaningful behavior to reach the declared
coverage threshold and prove installation on every supported runtime.

**Steps.**
1. Publish a line/branch/module coverage baseline and target uncovered risk paths first.
2. Add deterministic negative, lifecycle and boundary tests; exclude only generated/vendor code.
3. Build clean environments from locks for supported Python versions.
4. Fail CI below 90% application line coverage or on dependency/profile drift.

**Mandatory test:** `TEST-155` — clean-clone lock install, runtime matrix and ≥90% coverage gate.

**DoD.** Canonical CI reports ≥90% on `src/pokemon_tcg_rag`; no unsupported Python job exists;
clean install and full unit suite pass.

**Commit:** `test(quality): enforce clean clone and coverage gate (TASK-067)`

---

### TASK-068 — Build a real infrastructure integration layer

| Field | Value |
| :--- | :--- |
| Sprint / REQ | SPRINT_14_QUALITY_REPRODUCIBILITY · REQ-033 |
| Depends on / unblocks | TASK-063, TASK-064, TASK-065, TASK-067 / TASK-069 |
| Files affected | integration fixtures, Postgres/Qdrant/provider contract tests, CI services |
| Branch | `test/task-068-real-integration-stack` |

**Origin.** TECH-13. **Objective.** Exercise critical adapters across actual process/network/data
boundaries instead of mocks, SQLite substitutions or YAML-only assertions.

**Steps.**
1. Start isolated version-pinned Postgres and Qdrant per test session with unique namespaces.
2. Verify migrations, vector writes/search, BM25 parity and feedback transactions.
3. Add an LLM HTTP contract stub as a real network service, including timeout/error cases.
4. Retain logs on failure and guarantee cleanup/parallel-test isolation.

**Mandatory test:** `TEST-156` — ephemeral Postgres/Qdrant/network-provider integration suite.

**DoD.** Critical persistence/retrieval/provider contracts cross real boundaries in CI; fakes
remain only in unit tests and are clearly labelled.

**Commit:** `test(integration): exercise real infrastructure adapters (TASK-068)`

---

### TASK-069 — Add full compose and browser/API end-to-end test

| Field | Value |
| :--- | :--- |
| Sprint / REQ | SPRINT_14_QUALITY_REPRODUCIBILITY · REQ-033, REQ-034 |
| Depends on / unblocks | TASK-068 / TASK-070, TASK-088 |
| Files affected | compose test profile, seed job, Playwright/API tests, evidence artifacts |
| Branch | `test/task-069-clean-stack-e2e` |

**Origin.** TECH-05, TECH-10, TECH-13. **Objective.** Prove a third party can run the product
from clean state and complete the primary user journey.

**Steps.**
1. Build immutable local images and start an isolated compose project with deterministic seed.
2. Wait on truthful readiness and authenticate through the documented mechanism.
3. Exercise UI and API query, citations, feedback, metrics and restart persistence.
4. Capture sanitized screenshots, traces and service logs; tear down volumes reliably.

**Mandatory test:** `TEST-157` — one-command clean-seed browser/API/feedback E2E.

**DoD.** No monkeypatch or pre-existing volume is used; the seeded real stack completes all
critical journeys and retained evidence is reproducible.

**Commit:** `test(e2e): add clean stack user journey (TASK-069)`

---

### TASK-070 — Reconcile documentation with executable evidence

| Field | Value |
| :--- | :--- |
| Sprint / REQ | SPRINT_14_QUALITY_REPRODUCIBILITY · REQ-034 |
| Depends on / unblocks | TASK-067, TASK-069 / TASK-090 |
| Files affected | README, Makefile/help, API/deploy/evaluation docs, doc checks |
| Branch | `docs/task-070-evidence-backed-documentation` |

**Origin.** TECH-08, TECH-19. **Objective.** Remove claims that cannot be reproduced and make
clone, install, run, evaluate and deploy instructions executable.

**Steps.**
1. Correct repository URL, versions, targets, environment examples and supported profiles.
2. Link benchmark/deployment claims only to versioned reports or mark them explicitly planned.
3. Generate OpenAPI reference and validate commands/links in CI.
4. Add clean-clone quickstart, limitations, data-license and troubleshooting sections.

**Mandatory test:** `TEST-158` — documentation link, command, OpenAPI and evidence-reference check.

**DoD.** A reviewer can execute every quickstart command; all quantitative claims resolve to
matching retained evidence; no stale endpoint/version remains.

**Commit:** `docs(project): align claims with executable evidence (TASK-070)`
