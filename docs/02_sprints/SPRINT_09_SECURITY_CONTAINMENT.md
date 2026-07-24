# SPRINT_09 — Security Containment & Supply Chain

> Security remediation program · Tasks:
> [`TASKS_SPRINT_09.md`](../03_tasks/TASKS_SPRINT_09.md) · Baseline:
> [`SECURITY_REMEDIATION_PLAN.md`](../05_agent_harness/SECURITY_REMEDIATION_PLAN.md).

## Sprint Goal

Contain the audit's immediately exploitable and release-blocking risks: vulnerable and
unresolvable dependencies, inactive CI, publicly exposed infrastructure, user-controlled SSRF,
and unnecessarily broad secret propagation.

## Position

| Attribute | Value |
| :--- | :--- |
| Position | Sprint 9 of 12; first security remediation sprint |
| Depends on | Sprint 8 complete |
| Tasks | TASK-041..TASK-045 |
| Requirements | REQ-021, REQ-024, REQ-028, REQ-030 |

## Task List

| Task | Deliverable | Audit findings |
| :--- | :--- | :--- |
| TASK-041 | Resolve dependency graph, upgrade vulnerable packages, split profiles, lock and hash | SEC-05, SEC-10 |
| TASK-042 | Activate GitHub Actions and establish baseline security jobs | SEC-11 |
| TASK-043 | Remove public data-service ports and default credentials | SEC-04 |
| TASK-044 | Eliminate user-controlled backend SSRF in Streamlit | SEC-01 |
| TASK-045 | Apply service-specific configuration and secret injection | SEC-07 |

## Acceptance Criteria

- Clean environment installs from one committed lock without resolver conflict.
- Runtime dependency scan has no unaccepted Critical/High advisory.
- GitHub discovers and runs the workflow using a supported Python version.
- Qdrant/Postgres/Prometheus are not published on host interfaces by default.
- Grafana and PostgreSQL have no usable default password.
- UI users cannot choose a backend URL; private/link-local URL regression tests pass.
- Each service receives only the secrets required for its role.

## Exit Gate

SC-025, SC-026 and the Sprint 9 portions of SC-030 must pass. Open Critical findings block
Sprint 10 release even if feature tests are green.
