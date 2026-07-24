# SPRINT_13 — Runtime Stabilization

## Objective

Turn the secured component set into a truthful, executable RAG service from a deterministic
corpus: hydrate both indexes, honor the API contract, compose production dependencies and prove
the authenticated query/feedback journey.

| Item | Outcome | Depends on |
| :--- | :--- | :--- |
| TASK-061 | BM25/Qdrant corpus parity | TASK-057, TASK-063 |
| TASK-062 | Effective `top_k` contract | TASK-057 |
| TASK-063 | Versioned clean-clone corpus/bootstrap | TASK-041, TASK-056 |
| TASK-064 | Real application composition root | TASK-061..063 |
| TASK-065 | Operational query→feedback flow | TASK-050, TASK-051, TASK-064 |

## Delivery sequence and capacity

TASK-062 and TASK-063 may start in parallel; then TASK-061 → TASK-064 → TASK-065. Planned load:
29 SP. Cross-functional team: Backend, Retrieval/Data, QA and Platform.

## Risks and mitigations

- Source redistribution restrictions: commit only legal fixture content and fetch the rest from
  allowlisted sources with checksums.
- Model cold-start/memory: bounded initialization, explicit readiness and test-sized model profile.
- Index drift: one manifest/hash is authoritative and publication is atomic.

## Deliverables

Corpus manifest/bootstrap, hydrated BM25 snapshot, query policy contract, production composition
root, liveness/readiness endpoints and real query/feedback integration evidence.

## Success criteria

SC-035 and SC-036 pass; TEST-149..153 are green; a clean process never reports ready with an
empty/mismatched corpus and completes one authenticated grounded query plus owned feedback.
