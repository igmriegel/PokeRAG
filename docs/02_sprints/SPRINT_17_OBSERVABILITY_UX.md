# SPRINT_17 — Observability & Product UX

## Objective

Make the product diagnosable and usable: end-to-end traces, metered SLO/cost controls, live
dashboards, complete user workflow and tested operational runbooks.

| Item | Outcome | Depends on |
| :--- | :--- | :--- |
| TASK-081 | OpenTelemetry/correlation | TASK-049, TASK-057 |
| TASK-082 | SLO, token, cost and alerts | TASK-047, TASK-081 |
| TASK-083 | Live dashboards/feedback funnel | TASK-065, TASK-081, TASK-082 |
| TASK-084 | History/citation/comment/degraded UX | TASK-044, TASK-050, TASK-065 |
| TASK-085 | Operational analytics/runbooks | TASK-049, TASK-083, TASK-084 |

## Delivery sequence and capacity

TASK-081 and TASK-084 can proceed in parallel; 081 → 082 → 083, then both branches converge at
TASK-085. Planned load: 31 SP.

## Risks and mitigations

- Telemetry leaks/cardinality: attribute allowlist, redaction tests and label budgets.
- Noisy alerts: synthetic firing tests, burn-rate design and named owners.
- UI security regression: reuse trusted backend/citation policies and run SSRF/privacy tests.

## Deliverables

Trace topology, correlation standard, SLI/SLO and cost rules, alerts, populated Grafana evidence,
accessible UX journeys and incident/troubleshooting runbooks.

## Success criteria

SC-043 and SC-044 pass; TEST-169..173 are green; one query/feedback journey is traceable without
sensitive data, alerts are actionable and the browser workflow passes accessibility/degraded tests.
