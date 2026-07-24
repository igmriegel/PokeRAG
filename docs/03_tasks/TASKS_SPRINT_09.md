# TASKS_SPRINT_09 — Security Containment & Supply Chain

Granular task specs for **Sprint 9**. Index: [`TASK_INDEX.md`](./TASK_INDEX.md) · Security
baseline: [`SECURITY_REMEDIATION_PLAN.md`](../05_agent_harness/SECURITY_REMEDIATION_PLAN.md).

---

### TASK-041 — Reproducible and vulnerability-managed dependency graph

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_09_SECURITY_CONTAINMENT |
| **REQ covered** | REQ-021 |
| **Depends on** | TASK-001 |
| **Unblocks** | TASK-042, TASK-048, TASK-052, TASK-056 |
| **Files affected** | `pyproject.toml`, `requirements*.txt`, lock file, dependency policy |
| **Branch** | `fix/task-041-secure-dependency-lock` |

**Description.** Remove conflicting constraints, separate runtime/dev/evaluation profiles,
upgrade packages with known exploitable CVEs, and commit one deterministic lock with hashes.

**Definition of Ready.** Audit findings SEC-05 and SEC-10 are reproducible.

**Steps.**
1. Inventory direct/transitive dependencies and document accepted risk.
2. Resolve incompatible OpenAI/LangChain constraints and pin supported versions.
3. Generate hashed locks for each supported profile and a dependency-update policy.
4. Produce an SBOM and scan the resolved runtime graph.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-129 | Clean locked install + runtime SCA policy | supply-chain |

**Definition of Done.** Clean installs are deterministic; no unaccepted Critical/High runtime
advisory remains; SBOM and exception evidence are retained.

**Commit message.** `fix(deps): secure and lock dependency graph (TASK-041)`

---

### TASK-042 — Activate CI and baseline security jobs

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_09_SECURITY_CONTAINMENT |
| **REQ covered** | REQ-030 |
| **Depends on** | TASK-041 |
| **Unblocks** | TASK-046, TASK-058 |
| **Files affected** | `.github/workflows/ci.yml`, `ci/`, security tool configuration |
| **Branch** | `ci/task-042-activate-security-pipeline` |

**Description.** Move the workflow to GitHub's discoverable location, use supported runtimes,
least-privilege permissions, pinned actions, and blocking quality/secret/dependency checks.

**Definition of Ready.** TASK-041 merged and lock files available.

**Steps.**
1. Relocate `ci/workflows/ci.yml` to `.github/workflows/ci.yml`.
2. Declare minimal `permissions`, concurrency cancellation, timeouts, and pinned action SHAs.
3. Run lint, typing, tests/coverage, secret scan and dependency scan as blocking jobs.
4. Upload machine-readable evidence without exposing secrets.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-130 | Workflow discovery, syntax and least-privilege policy | CI smoke |

**Definition of Done.** A pull request triggers the workflow and cannot merge when a baseline
quality or security job fails.

**Commit message.** `ci(security): activate least-privilege pipeline (TASK-042)`

---

### TASK-043 — Isolate infrastructure services and remove default credentials

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_09_SECURITY_CONTAINMENT |
| **REQ covered** | REQ-028 |
| **Depends on** | TASK-039 |
| **Unblocks** | TASK-045, TASK-052, TASK-054 |
| **Files affected** | `docker-compose.yml`, `.env.example`, deployment documentation |
| **Branch** | `fix/task-043-isolate-compose-services` |

**Description.** Stop publishing Qdrant, PostgreSQL and Prometheus to host interfaces by
default, remove usable default passwords, and split developer-only exposure into an explicit
profile bound to loopback.

**Definition of Ready.** Full compose topology from TASK-039 exists.

**Steps.**
1. Replace internal `ports` with `expose`; use an opt-in debug profile for local access.
2. Require generated PostgreSQL/Grafana credentials with fail-closed validation.
3. Segment public, application and data networks.
4. Add negative tests for host reachability and default credentials.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-131 | Compose exposure and default-credential policy | security smoke |

**Definition of Done.** Only intended UI/API ports are host-published in the default profile;
startup fails safely when required credentials are absent.

**Commit message.** `fix(deploy): isolate services and remove defaults (TASK-043)`

---

### TASK-044 — Eliminate user-controlled Streamlit SSRF

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_09_SECURITY_CONTAINMENT |
| **REQ covered** | REQ-024 |
| **Depends on** | TASK-030 |
| **Unblocks** | TASK-054 |
| **Files affected** | Streamlit UI client/configuration and SSRF regression tests |
| **Branch** | `fix/task-044-block-streamlit-ssrf` |

**Description.** Remove the backend URL from user input. Resolve it only from trusted
configuration and enforce scheme, destination, redirect and timeout policies as defense in
depth.

**Definition of Ready.** UI/API integration from TASK-030 exists.

**Steps.**
1. Replace the editable URL with an administrator-controlled setting.
2. Permit only expected HTTP(S) origins; reject credentials, unusual schemes and DNS/IP
   destinations in loopback, private, link-local or metadata ranges.
3. Disable cross-origin redirects and set connect/read timeouts.
4. Test encoded addresses, DNS rebinding assumptions and redirect chains.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-132 | SSRF destination and redirect regression suite | security integration |

**Definition of Done.** An untrusted UI user cannot influence the network destination; all
private/metadata probes fail before a request is sent.

**Commit message.** `fix(ui): block backend SSRF paths (TASK-044)`

---

### TASK-045 — Scope configuration and secrets per service

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_09_SECURITY_CONTAINMENT |
| **REQ covered** | REQ-028 |
| **Depends on** | TASK-043 |
| **Unblocks** | TASK-051 |
| **Files affected** | `docker-compose.yml`, K8s secrets/config, settings models, `.env.example` |
| **Branch** | `fix/task-045-scope-service-secrets` |

**Description.** Replace shared environment propagation with explicit, service-specific
configuration and secret sources, validating secret presence without logging values.

**Definition of Ready.** Service exposure and credential policy from TASK-043 are defined.

**Steps.**
1. Inventory which component needs each credential.
2. Remove global `env_file` use and inject the minimum variables per service.
3. Prefer mounted/container-orchestrator secrets and document local rotation.
4. Add config tests proving unrelated services do not receive provider or database secrets.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-133 | Service secret-boundary assertions | configuration security |

**Definition of Done.** Secret distribution follows least privilege; samples contain
placeholders only; logs and rendered manifests contain no secret values.

**Commit message.** `fix(config): scope secrets to consuming services (TASK-045)`

---

## Sprint 9 Definition of Done

- [ ] TEST-129..TEST-133 pass.
- [ ] SEC-01, SEC-04, SEC-05, SEC-07, SEC-10 and SEC-11 have closure evidence.
- [ ] SC-025, SC-026 and applicable SC-030 controls pass.
