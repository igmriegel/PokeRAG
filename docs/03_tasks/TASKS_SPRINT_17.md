# TASKS_SPRINT_17 — Observability & Product UX

Index: [`TASK_INDEX.md`](./TASK_INDEX.md) · Backlog:
[`CONSOLIDATED_BACKLOG.md`](./CONSOLIDATED_BACKLOG.md).

---

### TASK-081 — Add OpenTelemetry tracing and correlation

| Field | Value |
| :--- | :--- |
| Sprint / REQ | SPRINT_17_OBSERVABILITY_UX · REQ-038 |
| Depends on / unblocks | TASK-049, TASK-057 / TASK-082, TASK-083 |
| Files affected | OTel SDK/exporter, API/RAG spans, logging context, compose/K8s |
| Branch | `feat/task-081-opentelemetry-tracing` |

**Origin.** TECH-23. **Objective.** Correlate API, rewrite, retrieval, reranking, provider and
feedback work without exposing prompts, chunks, answers, tokens or PII.

**Steps.**
1. Define trace/span naming, safe attributes, sampling and propagation standards.
2. Instrument critical boundaries and outbound HTTP/database/vector calls.
3. Correlate structured logs and metrics with trace/request/query IDs.
4. Export locally and in staging with bounded queues and graceful exporter failure.

**Mandatory test:** `TEST-169` — end-to-end span topology, propagation and sensitive-attribute
redaction.

**DoD.** A sampled query/feedback journey is reconstructable across components; exporter failure
does not break requests; forbidden data is absent.

**Commit:** `feat(observability): add end-to-end tracing (TASK-081)`

---

### TASK-082 — Define SLO, token, cost and alert controls

| Field | Value |
| :--- | :--- |
| Sprint / REQ | SPRINT_17_OBSERVABILITY_UX · REQ-038 |
| Depends on / unblocks | TASK-047, TASK-081 / TASK-083, TASK-087 |
| Files affected | metrics, recording/alert rules, SLO/budget config, runbook links |
| Branch | `feat/task-082-slo-cost-alerting` |

**Origin.** TECH-23, TECH-28. **Objective.** Meter reliability and spend for every request and
make actionable SLO/cost breaches visible.

**Steps.**
1. Define availability, latency, error, saturation and quality-adjacent SLIs with labels bounded.
2. Record provider/model tokens, retries, cache and cost using controlled-cardinality labels.
3. Add multi-window burn-rate, dependency, ingestion freshness and budget alerts.
4. Attach owner/severity/runbook and validate alert silence/noise policies.

**Mandatory test:** `TEST-170` — metric completeness/cardinality and synthetic alert-firing suite.

**DoD.** 100% test requests are metered; alert fixtures fire/resolve correctly; each page links to
an actionable runbook and contains no sensitive labels.

**Commit:** `feat(observability): add slo cost metrics and alerts (TASK-082)`

---

### TASK-083 — Populate dashboards and feedback telemetry

| Field | Value |
| :--- | :--- |
| Sprint / REQ | SPRINT_17_OBSERVABILITY_UX · REQ-038, REQ-039 |
| Depends on / unblocks | TASK-065, TASK-081, TASK-082 / TASK-085, TASK-088, TASK-089 |
| Files affected | Grafana dashboards, feedback metrics, evidence capture |
| Branch | `feat/task-083-live-dashboards-feedback` |

**Origin.** TECH-11, TECH-23. **Objective.** Demonstrate dashboards with real query/feedback data,
not panel definitions alone.

**Steps.**
1. Add panels for traffic, errors, latency stages, retrieval quality proxy, tokens/cost and feedback.
2. Link exemplars/traces and annotate deploy/config/corpus versions.
3. Seed a production-like journey and capture time-bounded sanitized evidence.
4. Validate empty/no-data/dependency-down behavior and dashboard provisioning.

**Mandatory test:** `TEST-171` — provisioned dashboard query, live-data and feedback-funnel check.

**DoD.** At least five useful panels render non-synthetic journey data; feedback can be traced to
the owning query aggregate and evidence is retained.

**Commit:** `feat(observability): populate product dashboards (TASK-083)`

---

### TASK-084 — Complete the user workflow UX

| Field | Value |
| :--- | :--- |
| Sprint / REQ | SPRINT_17_OBSERVABILITY_UX · REQ-039 |
| Depends on / unblocks | TASK-044, TASK-050, TASK-065 / TASK-085 |
| Files affected | Streamlit state/components, citation actions, feedback form, UX tests |
| Branch | `feat/task-084-complete-user-workflow` |

**Origin.** TECH-29. **Objective.** Add session history, citation open/copy, comments, accessible
loading and explicit error/degraded states.

**Steps.**
1. Maintain bounded session history without persisting sensitive content unexpectedly.
2. Render citation title/source/section with safe allowlisted open and copy actions.
3. Add bounded feedback comment and clear submitted/update status.
4. Implement accessible keyboard, focus, loading, empty, timeout and dependency-down behavior.

**Mandatory test:** `TEST-172` — browser user-history/citation/feedback/accessibility/degraded suite.

**DoD.** All documented user journeys are understandable and keyboard-usable; SSRF/privacy
controls remain intact and failure states provide recovery guidance.

**Commit:** `feat(ui): complete grounded answer workflow (TASK-084)`

---

### TASK-085 — Publish operational analytics and runbooks

| Field | Value |
| :--- | :--- |
| Sprint / REQ | SPRINT_17_OBSERVABILITY_UX · REQ-038, REQ-039 |
| Depends on / unblocks | TASK-049, TASK-083, TASK-084 / TASK-090 |
| Files affected | operations manual, SLO/incident/dependency/data/troubleshooting runbooks |
| Branch | `docs/task-085-operational-runbooks` |

**Origin.** TECH-30. **Objective.** Turn telemetry into repeatable diagnosis, escalation and safe
recovery procedures.

**Steps.**
1. Document service ownership, severity, escalation, communication and evidence preservation.
2. Add runbooks for SLO/cost burn, provider outage, index parity, ingestion failure and DB capacity.
3. Add troubleshooting decision trees using safe queries and read-only commands.
4. Run a tabletop; time detection/diagnosis and log gaps as owned work.

**Mandatory test:** `TEST-173` — runbook links/commands/owners plus tabletop evidence completeness.

**DoD.** Every actionable alert has a tested runbook, owner and escalation; commands are safe and
current; tabletop findings have disposition.

**Commit:** `docs(operations): add tested runbooks and analytics (TASK-085)`
