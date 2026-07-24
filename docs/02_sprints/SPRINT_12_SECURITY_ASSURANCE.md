# SPRINT_12 — Security Assurance & Release Gate

> Security remediation program · Tasks:
> [`TASKS_SPRINT_12.md`](../03_tasks/TASKS_SPRINT_12.md) · Baseline:
> [`SECURITY_REMEDIATION_PLAN.md`](../05_agent_harness/SECURITY_REMEDIATION_PLAN.md).

## Sprint Goal

Complete remaining trust-boundary fixes and make security continuously verifiable. The sprint
ends with a repeatable release gate that produces evidence for every SEC-01..SEC-17 finding.

## Position

| Attribute | Value |
| :--- | :--- |
| Position | Sprint 12 of 12; final security release sprint |
| Depends on | Sprints 9–11 |
| Tasks | TASK-056..TASK-060 |
| Requirements | REQ-029, REQ-030 plus closure of REQ-021..REQ-028 |

## Task List

| Task | Deliverable | Audit findings |
| :--- | :--- | :--- |
| TASK-056 | Bounded, allowlisted and sandboxed external ingestion | SEC-14 |
| TASK-057 | Production dependency wiring and truthful liveness/readiness | SEC-13 |
| TASK-058 | SAST/SCA/secrets/IaC/container scanning and SBOM enforcement | SEC-05, SEC-10, SEC-11 |
| TASK-059 | DAST plus API/SSRF/prompt-injection adversarial regression suite | SEC-01, SEC-02, SEC-03, SEC-08, SEC-12 |
| TASK-060 | Final closure matrix, clean-clone security run and release decision | SEC-01..SEC-17 |

## Acceptance Criteria

- Downloads enforce scheme/host/redirect/MIME/size limits and run parsers in constrained jobs.
- `/live` and `/ready` have distinct semantics; readiness returns 503 when dependencies fail.
- CI publishes SBOM and all required security reports on every PR.
- DAST and adversarial suites produce no open Critical/High result.
- Every SEC finding has implementation, test and retained evidence.
- Clean clone can build and run the hardened stack without manual security patches.

## Exit Gate

SC-033 and SC-034 pass. TASK-060 records one explicit result: `APPROVED`, `APPROVED WITH
EXPIRING RISK ACCEPTANCE`, or `REJECTED`. Only the first two allow a production release.
