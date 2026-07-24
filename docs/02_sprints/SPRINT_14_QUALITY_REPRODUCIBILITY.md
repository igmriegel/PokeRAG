# SPRINT_14 — Quality & Reproducibility

## Objective

Make the repository reproducible from a clean clone with green static analysis, ≥90% application
coverage and tests that exercise real infrastructure and the complete user journey.

| Item | Outcome | Depends on |
| :--- | :--- | :--- |
| TASK-066 | Ruff/Black/mypy green | TASK-042 |
| TASK-067 | Coverage and runtime-matrix gate | TASK-041, TASK-042, TASK-066 |
| TASK-068 | Real infrastructure integration suite | TASK-063..065, TASK-067 |
| TASK-069 | Clean compose/browser/API E2E | TASK-068 |
| TASK-070 | Evidence-backed documentation | TASK-067, TASK-069 |

## Delivery sequence and capacity

TASK-066 → 067 → 068 → 069 → 070. Planned load: 34 SP. Test fixes may proceed by module in
parallel once quality commands and fixtures are stable.

## Risks and mitigations

- Flaky integration tests: unique namespaces, pinned images, health waits and retained failure logs.
- Inflated coverage: prioritize risk behavior and forbid broad exclusions.
- Documentation drift: generate API reference and execute docs checks in the same CI.

## Deliverables

Canonical development lock, active quality/coverage gates, ephemeral Postgres/Qdrant/provider
tests, one-command E2E evidence, corrected README/API/deployment instructions.

## Success criteria

SC-037 and SC-038 pass; TEST-154..158 are green; no critical path is validated only by a fake,
SQLite substitution or static YAML assertion.
