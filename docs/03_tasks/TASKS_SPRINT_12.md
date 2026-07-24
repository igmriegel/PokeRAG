# TASKS_SPRINT_12 — Security Assurance & Release Gate

Granular task specs for **Sprint 12**. Index: [`TASK_INDEX.md`](./TASK_INDEX.md) · Security
baseline: [`SECURITY_REMEDIATION_PLAN.md`](../05_agent_harness/SECURITY_REMEDIATION_PLAN.md).

---

### TASK-056 — Harden the ingestion trust boundary

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_12_SECURITY_ASSURANCE |
| **REQ covered** | REQ-029 |
| **Depends on** | TASK-041, TASK-010 |
| **Unblocks** | TASK-058 |
| **Files affected** | ingestion fetchers/parsers, source manifest, quarantine and security tests |
| **Branch** | `fix/task-056-harden-ingestion-boundary` |

**Description.** Permit only approved source origins and formats, bound downloads/parsing, verify
content integrity, and quarantine malformed or instruction-poisoned documents.

**Definition of Ready.** Ingestion pipeline and stable parser dependencies exist.

**Steps.**
1. Enforce source allowlists, HTTPS, redirect limits, timeouts and maximum bytes/pages.
2. Validate MIME/signatures before parsing and isolate temporary files safely.
3. Record source URL, hash, retrieval time and parser version in a provenance manifest.
4. Quarantine parser bombs, malformed documents and suspicious embedded instructions.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-144 | Ingestion origin, size, parser and quarantine suite | security integration |

**Definition of Done.** Unapproved, oversized, malformed or suspicious inputs cannot enter the
index; accepted chunks retain verifiable provenance.

**Commit message.** `fix(ingestion): harden untrusted content boundary (TASK-056)`

---

### TASK-057 — Production wiring and truthful readiness

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_12_SECURITY_ASSURANCE |
| **REQ covered** | REQ-023, REQ-028, REQ-030 |
| **Depends on** | TASK-047, TASK-050, TASK-051, TASK-054 |
| **Unblocks** | TASK-059 |
| **Files affected** | application factory/lifespan, dependency wiring, health/readiness and stack tests |
| **Branch** | `fix/task-057-wire-readiness-lifecycle` |

**Description.** Replace placeholder runtime wiring with explicit initialized dependencies and
make readiness fail until required stores, models and migrations are truly usable.

**Definition of Ready.** API limits, data policy, DB roles and network controls are stable.

**Steps.**
1. Initialize clients through lifespan with typed settings and bounded startup.
2. Separate liveness from dependency-aware readiness.
3. Fail closed on missing migrations, indexes, credentials or model/provider readiness.
4. Exercise a hardened end-to-end query and feedback flow in compose/K8s.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-145 | Dependency wiring, degraded readiness and secure E2E stack | integration/smoke |

**Definition of Done.** Readiness never reports success for a non-functional or insecure
dependency graph; the real stack completes authenticated query/feedback flows.

**Commit message.** `fix(runtime): wire dependencies and truthful readiness (TASK-057)`

---

### TASK-058 — Automated security scans, SBOM and policy gates

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_12_SECURITY_ASSURANCE |
| **REQ covered** | REQ-021, REQ-030 |
| **Depends on** | TASK-042, TASK-055, TASK-056 |
| **Unblocks** | TASK-059 |
| **Files affected** | `.github/workflows/ci.yml`, SAST/SCA/secret/IaC/container configs, artifact policy |
| **Branch** | `ci/task-058-security-scans-sbom` |

**Description.** Make secret/history scanning, SAST, SCA, IaC/container scanning, SBOM generation
and provenance verification repeatable blocking CI controls.

**Definition of Ready.** Active CI, canonical IaC and hardened ingestion are complete.

**Steps.**
1. Configure low-noise rulesets and repository-wide secret-history scanning.
2. Scan source, lock graph, images and rendered infrastructure.
3. Generate CycloneDX/SPDX SBOMs and sign/attest release artifacts.
4. Define severity thresholds, expiry-bound exceptions and evidence retention.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-146 | Seeded-finding detection and security-gate policy | CI security |

**Definition of Done.** CI detects seeded vulnerabilities/secrets/misconfiguration and blocks
unaccepted Critical/High findings while retaining actionable reports.

**Commit message.** `ci(security): enforce scans sbom and provenance (TASK-058)`

---

### TASK-059 — DAST and adversarial security regression suite

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_12_SECURITY_ASSURANCE |
| **REQ covered** | REQ-022, REQ-024, REQ-025, REQ-026, REQ-030 |
| **Depends on** | TASK-048, TASK-049, TASK-057, TASK-058 |
| **Unblocks** | TASK-060 |
| **Files affected** | security test harness, DAST config, adversarial corpus, CI workflow |
| **Branch** | `test/task-059-dast-adversarial-suite` |

**Description.** Test the running application for API authorization, injection, SSRF, leakage,
abuse controls and LLM-specific indirect prompt/citation attacks.

**Definition of Ready.** Hardened application stack and automated security jobs are available.

**Steps.**
1. Build an ephemeral seeded test stack with non-production credentials.
2. Run authenticated DAST for OWASP API classes and negative authorization cases.
3. Run deterministic SSRF, prompt-injection, poisoned-document and citation-forgery probes.
4. Publish sanitized reports and fail on regressions or unaccepted Critical/High findings.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-147 | Authenticated DAST and LLM adversarial regression | DAST/adversarial |

**Definition of Done.** Repeatable scans cover the documented threat model without touching
production; exploitable Critical/High results block release.

**Commit message.** `test(security): add dast and adversarial regression (TASK-059)`

---

### TASK-060 — Security closure and release gate

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_12_SECURITY_ASSURANCE |
| **REQ covered** | REQ-030 |
| **Depends on** | TASK-041..TASK-059 |
| **Unblocks** | Security-approved release |
| **Files affected** | threat model, runbooks, risk register, release checklist, audit evidence |
| **Branch** | `chore/task-060-security-release-gate` |

**Description.** Re-test all SEC-01..SEC-17 findings, update threat model/runbooks, record
time-bound residual-risk decisions and enforce the final go/no-go security gate.

**Definition of Ready.** TASK-041..TASK-059 are Done with machine-readable evidence.

**Steps.**
1. Map every audit finding to fix commit, test and retained evidence.
2. Re-run quality, SAST/SCA/secret/IaC/container, DAST and adversarial suites from clean state.
3. Update incident response, secret rotation, backup/restore and dependency-response runbooks.
4. Require accountable approval for any residual risk with owner and expiry.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-148 | Full security acceptance and evidence-completeness gate | release |

**Definition of Done.** SEC-01..SEC-17 are verified closed or explicitly accepted with owner and
expiry; SC-025..SC-034 pass; no unaccepted Critical/High risk remains.

**Commit message.** `chore(security): enforce final release gate (TASK-060)`

---

## Sprint 12 Definition of Done

- [ ] TEST-144..TEST-148 pass.
- [ ] SEC-01..SEC-17 are closed or formally accepted with owner and expiry.
- [ ] SC-025..SC-034 pass and the release evidence bundle is retained.
