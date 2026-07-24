# SPRINT_11 — Platform & Infrastructure Hardening

> Security remediation program · Tasks:
> [`TASKS_SPRINT_11.md`](../03_tasks/TASKS_SPRINT_11.md) · Baseline:
> [`SECURITY_REMEDIATION_PLAN.md`](../05_agent_harness/SECURITY_REMEDIATION_PLAN.md).

## Sprint Goal

Reduce blast radius after an application or dependency compromise through least-privilege
database roles, rootless/minimal containers, Restricted Kubernetes settings, network
segmentation, TLS and immutable deployment artifacts.

## Position

| Attribute | Value |
| :--- | :--- |
| Position | Sprint 11 of 12 |
| Depends on | Sprint 9; may begin after its platform tasks are complete |
| Tasks | TASK-051..TASK-055 |
| Requirements | REQ-021, REQ-024, REQ-027, REQ-028 |

## Task List

| Task | Deliverable | Audit findings |
| :--- | :--- | :--- |
| TASK-051 | Separate migration and runtime PostgreSQL roles | SEC-17 |
| TASK-052 | Rootless, minimal, multi-stage runtime images | SEC-06 |
| TASK-053 | Kubernetes security contexts, probes, quotas and service accounts | SEC-06 |
| TASK-054 | Default-deny network policy, TLS and observability access controls | SEC-01, SEC-04, SEC-12 |
| TASK-055 | Consolidated IaC, immutable digests and signed artifact policy | SEC-10, SEC-16 |

## Acceptance Criteria

- Runtime DB role cannot create/drop schema, role or database.
- App images run as a numeric non-root UID with dropped capabilities.
- Kubernetes workloads set seccomp, no privilege escalation, resource limits and probes.
- Service account token automount is disabled unless justified.
- Default-deny ingress/egress permits only documented service flows and blocks metadata APIs.
- External traffic is TLS-only; Grafana/Prometheus require operator access.
- One canonical deployment stack remains; production images use immutable digests.

## Exit Gate

SC-030 and SC-031 pass; Checkov/Trivy results contain no unaccepted Critical/High finding.
