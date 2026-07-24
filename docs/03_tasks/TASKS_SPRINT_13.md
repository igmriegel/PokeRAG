# TASKS_SPRINT_13 — Runtime Stabilization

Index: [`TASK_INDEX.md`](./TASK_INDEX.md) · Backlog:
[`CONSOLIDATED_BACKLOG.md`](./CONSOLIDATED_BACKLOG.md).

---

### TASK-061 — Hydrate BM25 and enforce corpus parity

| Field | Value |
| :--- | :--- |
| Sprint / REQ | SPRINT_13_RUNTIME_STABILIZATION · REQ-031, REQ-032 |
| Depends on / unblocks | TASK-057, TASK-063 / TASK-064, TASK-072 |
| Files affected | composition root, BM25 loader, corpus manifest, parity tests |
| Branch | `fix/task-061-bm25-corpus-parity` |

**Description and origin.** Replace the empty lexical index path with hydration from the same
versioned corpus manifest used by Qdrant. Origin: TECH-03.

**Definition of Ready.** TASK-057 and TASK-063 expose a validated manifest and initialized
vector collection.

**Steps.**
1. Load normalized chunks by manifest version/hash and build a deterministic BM25 snapshot.
2. Compare source/chunk IDs, count and corpus hash with the Qdrant collection metadata.
3. Refuse readiness on empty or mismatched indexes; support atomic snapshot replacement.
4. Record index version, build duration and document/chunk counts without content leakage.

**Mandatory test:** `TEST-149` — cold/warm BM25 hydration, lexical hit and Qdrant/BM25 parity
integration test.

**DoD.** A non-empty clean corpus yields lexical results; both indexes expose the same manifest,
and any mismatch makes readiness false. `TEST-149` passes in active CI.

**Commit:** `fix(retrieval): hydrate bm25 from versioned corpus (TASK-061)`

---

### TASK-062 — Enforce the query configuration contract

| Field | Value |
| :--- | :--- |
| Sprint / REQ | SPRINT_13_RUNTIME_STABILIZATION · REQ-031 |
| Depends on / unblocks | TASK-057 / TASK-064 |
| Files affected | API schemas/routes, RAG chain, retrieval pipeline, policy settings |
| Branch | `fix/task-062-propagate-query-contract` |

**Description and origin.** Propagate validated request `top_k` through candidate retrieval,
fusion and final reranking, subject to server-side caps. Origin: TECH-04.

**Definition of Ready.** Authenticated query schema and resource policy are stable.

**Steps.**
1. Define typed request overrides and immutable server policy bounds.
2. Pass effective values explicitly instead of rereading global settings downstream.
3. Record requested/effective values in sanitized telemetry and response metadata where safe.
4. Reject invalid values and cap valid-but-expensive values deterministically.

**Mandatory test:** `TEST-150` — API-to-retriever propagation, invalid boundary and server-cap
contract matrix.

**DoD.** Each accepted request uses its documented effective `top_k`; no path bypasses resource
caps; OpenAPI and implementation agree. `TEST-150` passes.

**Commit:** `fix(api): enforce retrieval request contract (TASK-062)`

---

### TASK-063 — Version the corpus and deterministic bootstrap fixture

| Field | Value |
| :--- | :--- |
| Sprint / REQ | SPRINT_13_RUNTIME_STABILIZATION · REQ-032 |
| Depends on / unblocks | TASK-041, TASK-056 / TASK-061, TASK-064, TASK-068, TASK-071, TASK-074 |
| Files affected | data manifest/fixtures, bootstrap CLI, checksums, licenses, CI |
| Branch | `feat/task-063-versioned-corpus-bootstrap` |

**Description and origin.** Make a clean clone capable of obtaining a legal, deterministic,
non-empty corpus without relying on ignored local state. Origin: TECH-05.

**Definition of Ready.** Source allowlist, provenance format and locked runtime are defined.

**Steps.**
1. Commit a minimal redistributable fixture and source manifest with licenses and checksums.
2. Add an idempotent bootstrap command that fetches approved non-redistributable sources.
3. Validate hash, schema, provenance, expected sources and minimum chunk count before publish.
4. Cache only content-addressed artifacts; fail with actionable diagnostics on drift.

**Mandatory test:** `TEST-151` — clean-worktree offline fixture and approved online bootstrap
reproducibility test.

**DoD.** A clean clone produces the documented corpus hash and non-empty chunks, or fails
closed with source-specific guidance. Hidden local data is never required. `TEST-151` passes.

**Commit:** `feat(data): add versioned deterministic corpus bootstrap (TASK-063)`

---

### TASK-064 — Complete the production composition root

| Field | Value |
| :--- | :--- |
| Sprint / REQ | SPRINT_13_RUNTIME_STABILIZATION · REQ-031, REQ-032 |
| Depends on / unblocks | TASK-061, TASK-062, TASK-063 / TASK-065, TASK-068 |
| Files affected | FastAPI factory/lifespan, dependency container, model/store lifecycle, health |
| Branch | `fix/task-064-production-composition-root` |

**Description and origin.** Compose real settings, clients, stores, retrievers, reranker, LLM,
RAG chain and feedback service during application lifespan. Origin: TECH-01..03, TECH-10.

**Definition of Ready.** Corpus parity and query contracts pass independently.

**Steps.**
1. Introduce a typed application container with explicit construction and reverse-order close.
2. Bound startup, warm required clients/models and verify migrations/collections/index parity.
3. Separate `/live` process health from authenticated or protected dependency-aware `/ready`.
4. Make degraded provider behavior explicit; never install placeholder production dependencies.

**Mandatory test:** `TEST-152` — fresh-process composition, lifecycle cleanup and degraded
readiness matrix against real ephemeral stores.

**DoD.** A fresh process serves only after its required dependency graph is usable; each injected
component is real and closed exactly once; degraded states are truthful. `TEST-152` passes.

**Commit:** `fix(runtime): complete production composition root (TASK-064)`

---

### TASK-065 — Prove the operational query and feedback journey

| Field | Value |
| :--- | :--- |
| Sprint / REQ | SPRINT_13_RUNTIME_STABILIZATION · REQ-031 |
| Depends on / unblocks | TASK-050, TASK-051, TASK-064 / TASK-068, TASK-083, TASK-084 |
| Files affected | API/UI query-feedback flow, persistence, correlation IDs, integration tests |
| Branch | `test/task-065-query-feedback-journey` |

**Description and origin.** Complete the real authenticated answer-to-feedback path, including
query ownership and exactly-once persistence. Origin: TECH-01, TECH-11.

**Definition of Ready.** Production composition and feedback privacy controls are complete.

**Steps.**
1. Return an opaque query ID with a grounded answer and authorized citation metadata.
2. Accept one owned feedback decision plus bounded optional comment; define update semantics.
3. Correlate request, query and feedback without logging prompt, answer or PII by default.
4. Verify unauthorized, duplicate, stale and missing-query behavior.

**Mandatory test:** `TEST-153` — authenticated real API query→feedback persistence and ownership
journey.

**DoD.** The running stack answers a seeded question and persists exactly the documented owned
feedback record; negative cases fail safely. `TEST-153` passes.

**Commit:** `test(runtime): prove query feedback journey (TASK-065)`
