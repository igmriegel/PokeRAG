# SPRINT_10 — API, LLM & Data Security

> Security remediation program · Tasks:
> [`TASKS_SPRINT_10.md`](../03_tasks/TASKS_SPRINT_10.md) · Baseline:
> [`SECURITY_REMEDIATION_PLAN.md`](../05_agent_harness/SECURITY_REMEDIATION_PLAN.md).

## Sprint Goal

Establish explicit trust boundaries for callers, resource consumption, LLM instructions,
errors, diagnostics and persisted feedback. The public API must fail safely and remain
economically bounded under hostile input.

## Position

| Attribute | Value |
| :--- | :--- |
| Position | Sprint 10 of 12 |
| Depends on | Sprint 9 |
| Tasks | TASK-046..TASK-050 |
| Requirements | REQ-022, REQ-023, REQ-025, REQ-026 |

## Task List

| Task | Deliverable | Audit findings |
| :--- | :--- | :--- |
| TASK-046 | Authentication/authorization policy and protected FastAPI routes | SEC-02 |
| TASK-047 | Payload limits, rate limits, timeouts, quotas and LLM cost controls | SEC-02 |
| TASK-048 | System-role prompt boundary, injection defenses and citation validation | SEC-03 |
| TASK-049 | Safe error envelope, security headers and protected diagnostics | SEC-08, SEC-12 |
| TASK-050 | Server-correlated feedback, privacy/retention and response minimization | SEC-09, SEC-15 |

## Acceptance Criteria

- OpenAPI declares the chosen security scheme and every route has an explicit access policy.
- Oversized bodies fail before expensive work; abusive clients receive deterministic 429s.
- Provider calls have connect/read/total timeout, bounded output tokens and retry policy.
- Prompt instructions use the system role; context is marked untrusted and citations resolve.
- 5xx responses contain an opaque request ID, never raw exception text.
- `/metrics` and production API docs are not anonymously exposed.
- Feedback references a server-issued query ID and cannot forge model/answer/latency.
- Public responses return citations and bounded snippets, not unrestricted full chunks.

## Exit Gate

SC-027, SC-028, SC-029 and SC-032 must pass, including adversarial unit/integration tests.
