# TASKS_SPRINT_10 — API, LLM & Data Security

Granular task specs for **Sprint 10**. Index: [`TASK_INDEX.md`](./TASK_INDEX.md) · Security
baseline: [`SECURITY_REMEDIATION_PLAN.md`](../05_agent_harness/SECURITY_REMEDIATION_PLAN.md).

---

### TASK-046 — API authentication and authorization

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_10_API_LLM_SECURITY |
| **REQ covered** | REQ-022 |
| **Depends on** | TASK-029, TASK-042 |
| **Unblocks** | TASK-047, TASK-050 |
| **Files affected** | API security dependencies, route policies, OpenAPI, auth tests |
| **Branch** | `feat/task-046-api-authz` |

**Description.** Establish a documented identity boundary and default-deny authorization for
query, feedback, metrics and diagnostic operations. Tokens must be verified for issuer,
audience, signature and expiry.

**Definition of Ready.** API contract exists and CI is active.

**Steps.**
1. Define principals, roles/scopes and public versus protected routes.
2. Implement standards-based bearer-token verification with algorithm allowlisting.
3. Apply route-level scope checks and ownership rules.
4. Remove protected operations from anonymous OpenAPI examples and test denial paths.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-134 | Authentication, scope and object-access matrix | security integration |

**Definition of Done.** Anonymous, expired, malformed and under-scoped requests are denied
consistently; OpenAPI declares the effective policy.

**Commit message.** `feat(api): enforce authentication and authorization (TASK-046)`

---

### TASK-047 — API resource, payload and cost controls

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_10_API_LLM_SECURITY |
| **REQ covered** | REQ-023 |
| **Depends on** | TASK-046 |
| **Unblocks** | TASK-049, TASK-057 |
| **Files affected** | API schemas/middleware, provider client timeouts, rate-limit tests |
| **Branch** | `feat/task-047-api-resource-guards` |

**Description.** Bound request size, field length, retrieval depth, concurrency, provider
timeouts and per-principal request/cost rates to resist denial-of-wallet and exhaustion.

**Definition of Ready.** Stable principal identity is available from TASK-046.

**Steps.**
1. Add strict schema bounds and reject unknown/oversized payloads before model calls.
2. Enforce per-principal/IP rate limits and bounded concurrency.
3. Add connect/read/total timeouts, retries with jitter and a circuit breaker.
4. Emit low-cardinality rejection/cost metrics without logging prompts or tokens.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-135 | Payload, rate, timeout and cost-limit suite | security/load |

**Definition of Done.** Limits return deterministic 4xx/429 responses and provider failures do
not create unbounded retries or work.

**Commit message.** `feat(api): enforce resource and cost guards (TASK-047)`

---

### TASK-048 — Prompt-injection resistance and citation integrity

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_10_API_LLM_SECURITY |
| **REQ covered** | REQ-025 |
| **Depends on** | TASK-025, TASK-041 |
| **Unblocks** | TASK-059 |
| **Files affected** | prompts, RAG orchestration, citation validator, adversarial fixtures |
| **Branch** | `fix/task-048-prompt-citation-integrity` |

**Description.** Treat retrieved content as untrusted data, separate instructions from
evidence, constrain model output, and verify every citation against the retrieved set before
returning an answer.

**Definition of Ready.** Generation pipeline exists and dependencies are stable.

**Steps.**
1. Delimit system policy, user input and retrieved text with explicit trust labels.
2. Detect/quarantine instruction-like corpus content and require grounded abstention.
3. Parse structured output and reject citations absent from retrieved chunk IDs.
4. Add indirect-injection, exfiltration, fabricated-citation and poisoned-document tests.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-136 | Prompt-injection and citation-integrity corpus | adversarial |

**Definition of Done.** The adversarial corpus cannot override policy, expose secrets or
produce an accepted citation outside the retrieved evidence.

**Commit message.** `fix(rag): enforce prompt and citation integrity (TASK-048)`

---

### TASK-049 — Safe errors, diagnostics and HTTP headers

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_10_API_LLM_SECURITY |
| **REQ covered** | REQ-026 |
| **Depends on** | TASK-047 |
| **Unblocks** | TASK-059 |
| **Files affected** | API exception handlers, health routes, middleware, logging tests |
| **Branch** | `fix/task-049-safe-api-boundaries` |

**Description.** Replace raw exception disclosure with stable error codes and correlation IDs,
split liveness/readiness diagnostics, redact logs, and apply suitable security headers/CORS.

**Definition of Ready.** Request controls and error semantics from TASK-047 exist.

**Steps.**
1. Centralize exception mapping; keep stack traces and upstream details server-side.
2. Return minimal health information and protect detailed diagnostics.
3. Configure explicit CORS origins and security headers for API/UI responses.
4. Add structured redaction for credentials, tokens, prompts and connection strings.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-137 | Error leakage, CORS, header and diagnostic-access suite | security integration |

**Definition of Done.** Client responses and logs expose no sensitive internals; origins and
diagnostics fail closed.

**Commit message.** `fix(api): harden errors diagnostics and headers (TASK-049)`

---

### TASK-050 — Feedback integrity, privacy and response minimization

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_10_API_LLM_SECURITY |
| **REQ covered** | REQ-026 |
| **Depends on** | TASK-046, TASK-027 |
| **Unblocks** | TASK-057 |
| **Files affected** | feedback schema/repository, query response model, retention migration/tests |
| **Branch** | `fix/task-050-feedback-data-governance` |

**Description.** Bind feedback to an authenticated query event, prevent replay/forgery, limit
free text, define retention/deletion, and stop returning full internal chunks by default.

**Definition of Ready.** Feedback persistence and authenticated principals exist.

**Steps.**
1. Issue opaque query IDs and enforce owner, existence, uniqueness and age on feedback.
2. Bound/sanitize comments and define purpose, retention and deletion behavior.
3. Return minimal source excerpts; make privileged debug context explicit and audited.
4. Test cross-user feedback, replay, enumeration and sensitive-text leakage.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-138 | Feedback authorization/privacy and response-minimization suite | security integration |

**Definition of Done.** Forged/cross-user feedback is rejected; retained fields are documented;
normal responses expose no full internal chunk payload.

**Commit message.** `fix(data): protect feedback and minimize responses (TASK-050)`

---

## Sprint 10 Definition of Done

- [ ] TEST-134..TEST-138 pass.
- [ ] SEC-02, SEC-03, SEC-08, SEC-09, SEC-12 and SEC-15 have closure evidence.
- [ ] SC-027..SC-029 and SC-032 pass.
