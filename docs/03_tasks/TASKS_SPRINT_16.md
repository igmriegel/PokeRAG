# TASKS_SPRINT_16 — LLM Quality & Guardrails

Index: [`TASK_INDEX.md`](./TASK_INDEX.md) · Backlog:
[`CONSOLIDATED_BACKLOG.md`](./CONSOLIDATED_BACKLOG.md).

---

### TASK-076 — Implement a real prompt/model evaluation runner

| Field | Value |
| :--- | :--- |
| Sprint / REQ | SPRINT_16_LLM_QUALITY · REQ-037 |
| Depends on / unblocks | TASK-057, TASK-071 / TASK-077, TASK-078, TASK-079 |
| Files affected | LLM evaluation runner, prompt/model registry, run artifacts |
| Branch | `feat/task-076-real-llm-evaluation` |

**Origin.** TECH-07. **Objective.** Execute real RAG outputs over a pre-registered zero/few-shot,
model and temperature matrix with bounded spend.

**Steps.**
1. Version prompt/system roles, model/provider, decoding and retrieval configuration.
2. Execute benchmark runs with retry policy, cache key, budget cap and explicit failures.
3. Record sanitized output, citations, token counts, latency and estimated/actual cost.
4. Prevent hardcoded scores/reference outputs in release mode.

**Mandatory test:** `TEST-164` — real-provider-contract execution, provenance and anti-hardcode
release guard.

**DoD.** Re-running the same registered configuration produces a complete auditable result set;
all provider calls are bounded and metered.

**Commit:** `feat(evaluation): run real llm configuration matrix (TASK-076)`

---

### TASK-077 — Add RAGAS/DeepEval automatic scoring

| Field | Value |
| :--- | :--- |
| Sprint / REQ | SPRINT_16_LLM_QUALITY · REQ-037 |
| Depends on / unblocks | TASK-076 / TASK-080 |
| Files affected | evaluator adapters, judge configuration, calibration set, score artifacts |
| Branch | `feat/task-077-real-llm-metrics` |

**Origin.** TECH-07. **Objective.** Replace fixed scores with real faithfulness, answer
correctness/relevance and context precision/recall evaluation.

**Steps.**
1. Integrate one primary framework and a portable evaluator protocol.
2. Pin judge prompt/model and record judge tokens, failures and rate-limit behavior.
3. Calibrate automated scores against reviewed examples and define uncertainty handling.
4. Separate unavailable/error from score zero; never silently impute successful values.

**Mandatory test:** `TEST-165` — framework invocation, calibration and scorer-failure semantics.

**DoD.** Scores derive from recorded real outputs; evaluator provenance and calibration are
retained; no hardcoded metric path can enter a release report.

**Commit:** `feat(evaluation): add calibrated rag quality scoring (TASK-077)`

---

### TASK-078 — Establish human evaluation and error taxonomy

| Field | Value |
| :--- | :--- |
| Sprint / REQ | SPRINT_16_LLM_QUALITY · REQ-037 |
| Depends on / unblocks | TASK-076 / TASK-080 |
| Files affected | review rubric/sample, blinded review tool/export, error taxonomy |
| Branch | `feat/task-078-human-evaluation` |

**Origin.** TECH-09. **Objective.** Measure domain correctness/usefulness and classify failures
that automated judges do not reliably detect.

**Steps.**
1. Define blinded rubric for correctness, completeness, grounding, citation and helpfulness.
2. Stratify a review sample by difficulty/source/failure slice and collect two ratings.
3. Calculate agreement, adjudicate disagreements and protect reviewer/user data.
4. Map error categories to owners and follow-up backlog entries.

**Mandatory test:** `TEST-166` — review schema, blinding, sample coverage and agreement calculation.

**DoD.** A completed versioned review includes agreement and adjudication; each material failure
class has an owner and disposition.

**Commit:** `feat(evaluation): add human review and error taxonomy (TASK-078)`

---

### TASK-079 — Validate structured claims and citation entailment

| Field | Value |
| :--- | :--- |
| Sprint / REQ | SPRINT_16_LLM_QUALITY · REQ-025, REQ-037 |
| Depends on / unblocks | TASK-048, TASK-076 / TASK-080 |
| Files affected | prompt roles, structured response schema, citation validator, adversarial tests |
| Branch | `feat/task-079-citation-entailment-guard` |

**Origin.** TECH-22. **Objective.** Stop copying retrieved metadata as proof; require each material
claim to reference existing retrieved evidence that supports it.

**Steps.**
1. Send immutable policy as system/developer instructions and context as delimited untrusted data.
2. Require structured answer claims and stable citation IDs restricted to retrieved chunks.
3. Validate existence and lexical/semantic entailment; abstain or remove unsupported claims.
4. Test forged IDs, conflicting sources, poisoned instructions and no-answer cases.

**Mandatory test:** `TEST-167` — claim/citation existence, entailment and adversarial abstention.

**DoD.** Citation validity is ≥0.95 on the release set and every unsupported material claim is
blocked or explicitly qualified; security corpus remains green.

**Commit:** `feat(llm): validate claims and citation support (TASK-079)`

---

### TASK-080 — Publish LLM selection report and regression gate

| Field | Value |
| :--- | :--- |
| Sprint / REQ | SPRINT_16_LLM_QUALITY · REQ-037 |
| Depends on / unblocks | TASK-077, TASK-078, TASK-079 / TASK-087, TASK-090 |
| Files affected | LLM report, baseline registry, release evaluation policy |
| Branch | `feat/task-080-llm-regression-gate` |

**Origin.** TECH-07, TECH-08. **Objective.** Select a prompt/model configuration from real
automatic/human quality, safety, latency and cost evidence.

**Steps.**
1. Compare configurations and failure slices; disclose judge/human disagreement.
2. Require faithfulness >0.85, citation validity ≥0.95 and documented correctness target.
3. Register baseline with benchmark/corpus/retrieval/prompt/model/code hashes.
4. Fail regression or budget breach; require approval for model/provider changes.

**Mandatory test:** `TEST-168` — report provenance, score/cost thresholds and seeded-regression
gate.

**DoD.** One defensible configuration is selected with reproducible evidence; unsupported README
values are removed; the matched-baseline gate blocks quality/cost regressions.

**Commit:** `feat(evaluation): gate llm quality and cost regressions (TASK-080)`
