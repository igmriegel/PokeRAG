# SECURITY_REMEDIATION_PLAN — Audit Finding Closure

> Part of the [Engineering Harness](../README.md). This plan converts the security audit
> baseline into requirements, sprints, tasks, tests, and blocking release evidence.
> The combined security + technical roadmap is
> [`EVOLUTION_PROGRAM.md`](./EVOLUTION_PROGRAM.md).

## Objective

Close every finding from the repository security audit performed against commit `5015e93`
without losing traceability. A finding is closed only when its implementation task is `Done`,
its mandatory security tests pass, and the corresponding security success criterion is green.

## Audit Baseline

| Audit ID | Severity | Finding | Remediation task(s) | Verification |
| :--- | :--- | :--- | :--- | :--- |
| SEC-01 | High | User-controlled Streamlit backend enables SSRF | TASK-044, TASK-054, TASK-059 | TEST-132, TEST-142, TEST-147 |
| SEC-02 | High | API has no auth, rate limit, request-size or cost controls | TASK-046, TASK-047 | TEST-134, TEST-135 |
| SEC-03 | High | Direct/indirect prompt injection and citation trust gap | TASK-048, TASK-059 | TEST-136, TEST-147 |
| SEC-04 | High | Data/observability services exposed with weak defaults | TASK-043, TASK-054 | TEST-131, TEST-142 |
| SEC-05 | Critical | Known vulnerable runtime dependencies | TASK-041, TASK-058 | TEST-129, TEST-146 |
| SEC-06 | High | Root containers and Kubernetes workloads lack hardening | TASK-052, TASK-053 | TEST-140, TEST-141 |
| SEC-07 | Medium | Secrets are propagated to services that do not need them | TASK-045 | TEST-133 |
| SEC-08 | Medium | Internal exception details are returned to callers | TASK-049 | TEST-137 |
| SEC-09 | Medium | Feedback can be forged and has no privacy/retention controls | TASK-050 | TEST-138 |
| SEC-10 | Medium | Dependency graph is unsatisfiable and supply chain is not reproducible | TASK-041, TASK-055, TASK-058 | TEST-129, TEST-143, TEST-146 |
| SEC-11 | Medium | CI workflow is undiscoverable and lacks security gates | TASK-042, TASK-058 | TEST-130, TEST-146 |
| SEC-12 | Medium | TLS, security headers and diagnostics access are not enforced | TASK-049, TASK-054 | TEST-137, TEST-142 |
| SEC-13 | Medium | Readiness reports healthy while dependencies are absent | TASK-057 | TEST-145 |
| SEC-14 | Medium | External ingestion has no size, redirect or content validation | TASK-056 | TEST-144 |
| SEC-15 | Low | Public API returns complete retrieved chunks | TASK-050 | TEST-138 |
| SEC-16 | Medium | Duplicate IaC and mutable image tags create deployment drift | TASK-055 | TEST-143 |
| SEC-17 | High | Runtime application uses PostgreSQL bootstrap superuser | TASK-051 | TEST-139 |

## Remediation Sprints

| Sprint | Theme | Tasks | Exit condition |
| :--- | :--- | :--- | :--- |
| [SPRINT_09](../02_sprints/SPRINT_09_SECURITY_CONTAINMENT.md) | Immediate containment and supply chain | TASK-041..045 | Critical CVE/build, public-service, SSRF and secret-blast-radius risks contained |
| [SPRINT_10](../02_sprints/SPRINT_10_API_LLM_SECURITY.md) | API, LLM and data protection | TASK-046..050 | Auth, quotas, prompt boundaries, safe errors and feedback integrity enforced |
| [SPRINT_11](../02_sprints/SPRINT_11_PLATFORM_HARDENING.md) | Containers, Kubernetes and database | TASK-051..055 | Least privilege, workload isolation, network controls and immutable IaC enforced |
| [SPRINT_12](../02_sprints/SPRINT_12_SECURITY_ASSURANCE.md) | Security assurance and release gate | TASK-056..060 | Automated SAST/SCA/IaC/DAST evidence closes all SEC findings |

## Closure Rules

1. No finding may be marked closed from documentation alone.
2. Every fix starts with a failing regression/security test.
3. A risk may be accepted only by a human-approved ADR containing owner, expiration date,
   compensating controls, and explicit `SEC-##` reference.
4. `SEC-05` blocks every production image while a reachable Critical/High runtime advisory
   remains without an approved exception.
5. `TASK-060` is the release gate and cannot start until TASK-041..059 are `Done`.
6. Evidence is retained as CI artifacts: test reports, SBOM, SCA/SAST/IaC/secret-scan output,
   DAST report, image digest/signature and final closure matrix.

## Security Definition of Done

- All mandatory tests TEST-129..TEST-148 in TASK-041..060 pass.
- Security criteria SC-025..SC-034 are green.
- No real secret exists in the current tree or reachable Git history.
- No unauthenticated route can trigger paid/unbounded work.
- No user-controlled URL can reach private, loopback, link-local or metadata destinations.
- Runtime containers are non-root and Kubernetes workloads meet the Restricted posture.
- Internal data services have no public host port and are protected by network policy.
- Runtime database credentials are least-privilege and cannot perform DDL.
- CI runs from `.github/workflows/`, generates an SBOM, and blocks defined severity thresholds.
- The final DAST/adversarial report contains no open Critical or High finding.
