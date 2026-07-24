# TASKS_SPRINT_11 — Platform Hardening

Granular task specs for **Sprint 11**. Index: [`TASK_INDEX.md`](./TASK_INDEX.md) · Security
baseline: [`SECURITY_REMEDIATION_PLAN.md`](../05_agent_harness/SECURITY_REMEDIATION_PLAN.md).

---

### TASK-051 — PostgreSQL least-privilege roles and migrations

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_11_PLATFORM_HARDENING |
| **REQ covered** | REQ-028 |
| **Depends on** | TASK-045, TASK-026 |
| **Unblocks** | TASK-057 |
| **Files affected** | database migrations/bootstrap, repository settings, compose/K8s secrets |
| **Branch** | `fix/task-051-postgres-least-privilege` |

**Description.** Separate owner/migration/runtime roles, remove application superuser use,
restrict schema privileges and rotate bootstrap credentials.

**Definition of Ready.** Service-specific secret boundaries and schema migrations exist.

**Steps.**
1. Define non-login owner, migration role and restricted runtime role.
2. Revoke public schema privileges and grant only required table/sequence operations.
3. Run migrations separately from the API process and rotate bootstrap secrets.
4. Prove the runtime role cannot create roles/databases, alter schema or read unrelated data.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-139 | Database privilege and migration-role matrix | security integration |

**Definition of Done.** The API operates with a non-superuser role and forbidden DDL/admin
operations fail.

**Commit message.** `fix(db): enforce least-privilege postgres roles (TASK-051)`

---

### TASK-052 — Rootless minimal runtime images

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_11_PLATFORM_HARDENING |
| **REQ covered** | REQ-027 |
| **Depends on** | TASK-041, TASK-043 |
| **Unblocks** | TASK-053 |
| **Files affected** | Dockerfiles, `.dockerignore`, image build/security tests |
| **Branch** | `build/task-052-rootless-runtime-images` |

**Description.** Build minimal multi-stage images with pinned bases, a dedicated non-root user,
read-only-compatible paths and no build tools or credentials in runtime layers.

**Definition of Ready.** Locked dependencies and service topology are stable.

**Steps.**
1. Pin base images by digest and separate build/runtime stages.
2. Create an unprivileged UID/GID and copy only required artifacts.
3. Remove caches/package managers and define writable temp/data locations.
4. Scan image contents, history, CVEs and effective runtime user.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-140 | Image user, contents, history and vulnerability policy | container security |

**Definition of Done.** Runtime containers start non-root from minimal immutable images with no
embedded secrets or unaccepted Critical/High findings.

**Commit message.** `build(container): ship rootless minimal images (TASK-052)`

---

### TASK-053 — Restricted Kubernetes workloads

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_11_PLATFORM_HARDENING |
| **REQ covered** | REQ-027 |
| **Depends on** | TASK-052, TASK-040 |
| **Unblocks** | TASK-054, TASK-055 |
| **Files affected** | `deploy/k8s/`, workload policy tests |
| **Branch** | `fix/task-053-k8s-workload-hardening` |

**Description.** Apply restricted pod/container contexts, dedicated service accounts, bounded
resources and accurate probes to every workload.

**Definition of Ready.** Rootless images and deployment manifests exist.

**Steps.**
1. Set non-root, read-only filesystem, dropped capabilities and seccomp RuntimeDefault.
2. Disable service-account token mounts unless explicitly required.
3. Add CPU/memory requests/limits and bounded ephemeral storage.
4. Define separate liveness/readiness/startup probes and validate against restricted policy.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-141 | Kubernetes restricted-policy and resource validation | IaC security |

**Definition of Done.** All workloads pass policy-as-code checks and function without privileged
execution or unnecessary token mounts.

**Commit message.** `fix(k8s): enforce restricted workload policy (TASK-053)`

---

### TASK-054 — Network segmentation, TLS and protected observability

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_11_PLATFORM_HARDENING |
| **REQ covered** | REQ-024, REQ-028 |
| **Depends on** | TASK-043, TASK-044, TASK-053 |
| **Unblocks** | TASK-055, TASK-057 |
| **Files affected** | ingress/services, NetworkPolicies, TLS and observability configuration |
| **Branch** | `fix/task-054-network-tls-controls` |

**Description.** Default-deny east/west traffic, permit only required service flows, terminate
TLS at ingress and keep metrics/dashboards/diagnostics private or authenticated.

**Definition of Ready.** Compose exposure, SSRF controls and K8s workload identities exist.

**Steps.**
1. Create default-deny ingress/egress policies and explicit DNS/provider/data-service rules.
2. Expose only UI/API ingress over TLS with redirect and secure transport settings.
3. Restrict Prometheus, Grafana, Qdrant, PostgreSQL and detailed diagnostics.
4. Test allowed topology plus denied metadata, private-network and lateral paths.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-142 | NetworkPolicy, TLS and private-observability matrix | infrastructure security |

**Definition of Done.** The deployed network matches the documented allowlist and internal
services have no unintended unauthenticated route.

**Commit message.** `fix(platform): segment network and enforce tls (TASK-054)`

---

### TASK-055 — Consolidated immutable IaC and artifact provenance

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_11_PLATFORM_HARDENING |
| **REQ covered** | REQ-021, REQ-027 |
| **Depends on** | TASK-041, TASK-053, TASK-054 |
| **Unblocks** | TASK-058 |
| **Files affected** | deployment manifests/overlays, image references, provenance policy |
| **Branch** | `refactor/task-055-consolidate-immutable-iac` |

**Description.** Remove duplicate/conflicting manifests, establish one canonical deployment
source with environment overlays, and deploy only digest-pinned, attestable images.

**Definition of Ready.** Hardened workload and network policies are complete.

**Steps.**
1. Inventory and remove duplicate IaC definitions through a documented migration.
2. Create canonical base plus environment-specific overlays with schema validation.
3. Replace mutable tags (including `latest`) with image digests.
4. Generate/verify signatures, provenance attestations and deployment diffs.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-143 | IaC uniqueness, digest and provenance policy | supply-chain/IaC |

**Definition of Done.** A single deterministic manifest set deploys verified immutable
artifacts; no production image uses a mutable tag.

**Commit message.** `refactor(iac): consolidate immutable deployments (TASK-055)`

---

## Sprint 11 Definition of Done

- [ ] TEST-139..TEST-143 pass.
- [ ] SEC-06, SEC-12, SEC-16 and SEC-17 have closure evidence.
- [ ] SC-030 and SC-031 pass.
