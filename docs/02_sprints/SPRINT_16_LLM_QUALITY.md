# SPRINT_16 — LLM Quality & Guardrails

## Objective

Select a prompt/model configuration using real outputs, calibrated automatic and human evaluation,
and claim-level citation validation instead of hardcoded scores.

| Item | Outcome | Depends on |
| :--- | :--- | :--- |
| TASK-076 | Real model/prompt evaluation runner | TASK-057, TASK-071 |
| TASK-077 | RAGAS/DeepEval scoring | TASK-076 |
| TASK-078 | Human review/error taxonomy | TASK-076 |
| TASK-079 | Claim/citation entailment guard | TASK-048, TASK-076 |
| TASK-080 | LLM selection/regression gate | TASK-077..079 |

## Delivery sequence and capacity

TASK-076 first; TASK-077, TASK-078 and TASK-079 proceed in parallel; TASK-080 consolidates.
Planned load: 37 SP.

## Risks and mitigations

- Judge bias/non-determinism: pin judge configuration, calibrate with humans and report uncertainty.
- Provider cost/rate limit: hard run budgets, resume, bounded retries and full metering.
- False citation support: adversarial cases plus explicit claim-to-chunk validation and abstention.

## Deliverables

Versioned prompt/model registry, raw run artifacts, calibrated RAG metrics, blinded review report,
structured citation validator and LLM baseline registry.

## Success criteria

SC-041 and SC-042 pass; TEST-164..168 are green; faithfulness >0.85 and citation validity ≥0.95
on the release benchmark with documented latency/cost trade-offs.
