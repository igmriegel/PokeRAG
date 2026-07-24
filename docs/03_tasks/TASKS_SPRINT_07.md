# TASKS_SPRINT_07 — Evaluation

Granular task specs for **Sprint 7** (`SPRINT_07_EVALUATION`). Index:
[`TASK_INDEX.md`](./TASK_INDEX.md) · Graph: [`TASK_DEPENDENCY_GRAPH.md`](./TASK_DEPENDENCY_GRAPH.md).

**Sprint objective:** build the 100-question benchmark, compare the four retrieval strategies
(Recall@5/@10, MRR, Hit Rate), evaluate LLM answers (Faithfulness, Correctness, Citation
Quality, Completeness), and expose a CLI + regression gate. See
[`EvaluationPlan.md`](../01_architecture/EvaluationPlan.md).

---

### TASK-032 — Benchmark dataset loader + 100 questions

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_07_EVALUATION |
| **REQ covered** | REQ-018 |
| **Depends on** | TASK-003 |
| **Unblocks** | TASK-034, TASK-035 |
| **Files affected** | `src/pokemon_tcg_rag/evaluation/dataset.py`, `src/pokemon_tcg_rag/evaluation/__init__.py`, `data/evaluation/benchmark_100_questions.json`, `tests/evaluation/test_dataset.py` |
| **Branch** | `feat/task-032-benchmark-dataset` |

**Description.** Implement `EvalTestCase` and `EvaluationDatasetLoader.load_dataset()` and author
the 100-question benchmark: each item has a question, expected relevant document ids/sources, and
an expected/reference answer.

**Definition of Ready.** TASK-003 merged; sources indexed (Sprint 3) for id references.

**Steps.**
1. Define `EvalTestCase` (question, ground_truth_doc_ids, expected_source, reference_answer).
2. Author `benchmark_100_questions.json` spanning all sources (rulings, rulebook, errata, ban, promo, mega).
3. `load_dataset()` parses + validates the file; raise on malformed entries.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-102 | `test_load_dataset_parses_cases` | evaluation |
| TEST-103 | `test_dataset_has_100_cases` | evaluation |
| TEST-104 | `test_malformed_case_raises` | evaluation |

**Definition of Done.** 100 validated test cases load; all sources represented; ≥90% coverage.

**Acceptance criteria.** `load_dataset()` returns exactly 100 valid `EvalTestCase`s.

**Commit message.** `feat(evaluation): benchmark dataset loader and 100 questions (TASK-032)`

---

### TASK-033 — Retrieval metrics

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_07_EVALUATION |
| **REQ covered** | REQ-018 |
| **Depends on** | TASK-003 |
| **Unblocks** | TASK-034 |
| **Files affected** | `src/pokemon_tcg_rag/evaluation/metrics.py`, `tests/evaluation/test_retrieval_eval.py` |
| **Branch** | `feat/task-033-retrieval-metrics` |

**Description.** Implement `calculate_recall_at_k`, `calculate_mrr`, and `calculate_hit_rate` over
retrieved chunks vs ground-truth doc ids, with exact, hand-verifiable formulas.

**Definition of Ready.** TASK-003 merged.

**Steps.**
1. `recall_at_k`: |relevant ∩ retrieved@k| / |relevant|.
2. `mrr`: mean reciprocal rank of first relevant hit.
3. `hit_rate`: fraction of queries with ≥1 relevant hit in top-k.
4. Handle empty ground-truth / empty retrieval.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-105 | `test_recall_at_k_value` | evaluation |
| TEST-106 | `test_mrr_value` | evaluation |
| TEST-107 | `test_hit_rate_value` | evaluation |
| TEST-108 | `test_metrics_handle_empty` | evaluation |

**Definition of Done.** Metrics match hand-computed values on fixtures; edge cases handled; ≥90%.

**Acceptance criteria.** On a known fixture, Recall@5, MRR, and Hit Rate equal expected constants.

**Commit message.** `feat(evaluation): retrieval metrics recall/mrr/hitrate (TASK-033)`

---

### TASK-034 — Retrieval strategy comparison evaluator

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_07_EVALUATION |
| **REQ covered** | REQ-018 |
| **Depends on** | TASK-023, TASK-032, TASK-033 |
| **Unblocks** | TASK-036 |
| **Files affected** | `src/pokemon_tcg_rag/evaluation/evaluator.py`, `tests/evaluation/test_retrieval_eval.py` |
| **Branch** | `feat/task-034-retrieval-evaluator` |

**Description.** Implement `RAGEvaluator` (retrieval side) running the benchmark across **Dense,
BM25, Hybrid, and Hybrid+Rerank**, producing an `EvaluationReport` comparing Recall@5/@10, MRR,
and Hit Rate so the best strategy can be selected (rubric: multiple approaches, pick best).

**Definition of Ready.** TASK-023, TASK-032, TASK-033 merged.

**Steps.**
1. For each strategy (toggling `RetrievalPipeline` stages), run all 100 cases.
2. Aggregate metrics per strategy into `EvaluationReport`.
3. Emit a comparison table (Markdown/JSON) and flag the winning strategy.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-109 | `test_evaluates_all_four_strategies` | evaluation (mocked retrieval) |
| TEST-110 | `test_report_contains_metrics_per_strategy` | evaluation |
| TEST-111 | `test_best_strategy_selected` | evaluation |

**Definition of Done.** Report compares all four strategies and names the best; ≥90% coverage.

**Acceptance criteria.** The evaluator ranks strategies by MRR/Recall and records the winner.

**Commit message.** `feat(evaluation): retrieval strategy comparison (TASK-034)`

---

### TASK-035 — LLM answer evaluation

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_07_EVALUATION |
| **REQ covered** | REQ-019 |
| **Depends on** | TASK-025, TASK-032 |
| **Unblocks** | TASK-036 |
| **Files affected** | `src/pokemon_tcg_rag/evaluation/metrics.py`, `src/pokemon_tcg_rag/evaluation/evaluator.py`, `tests/evaluation/test_llm_eval.py` |
| **Branch** | `feat/task-035-llm-evaluation` |

**Description.** Add LLM-output evaluation — Faithfulness, Correctness, Citation Quality,
Completeness — via RAGAS/DeepEval, comparing **multiple prompts (A/B) and models
(gpt-4o-mini vs gpt-4.1-mini)** so the best configuration is selected (rubric: multiple
approaches, pick best).

**Definition of Ready.** TASK-025, TASK-032 merged. `calculate_faithfulness` exists in metrics.

**Steps.**
1. Implement/extend `calculate_faithfulness` and add correctness/citation/completeness scorers (RAGAS/DeepEval, mocked in tests).
2. Run the benchmark for each prompt×model combination; aggregate into the report.
3. Select the best-scoring configuration.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-112 | `test_faithfulness_score_range` | evaluation (mocked judge) |
| TEST-113 | `test_prompt_ab_comparison` | evaluation |
| TEST-114 | `test_model_comparison_records_best` | evaluation |

**Definition of Done.** LLM metrics computed; A/B prompt and model comparison recorded with a winner; ≥90%.

**Acceptance criteria.** Report shows Faithfulness/Correctness per prompt×model and names the best config.

**Commit message.** `feat(evaluation): LLM answer quality and prompt/model comparison (TASK-035)`

---

### TASK-036 — Evaluation CLI & regression gate

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_07_EVALUATION |
| **REQ covered** | REQ-018, REQ-019 |
| **Depends on** | TASK-034, TASK-035 |
| **Unblocks** | — |
| **Files affected** | `scripts/run_evaluation.py`, `tests/performance/test_benchmarks.py`, `Makefile` |
| **Branch** | `feat/task-036-evaluation-cli` |

**Description.** Expose evaluation as a CLI (`scripts/run_evaluation.py`) that runs retrieval + LLM
evaluation, writes reports, and enforces a **regression gate** against
[`SUCCESS_CRITERIA.md`](../00_project/SUCCESS_CRITERIA.md) thresholds (fail if Recall/Faithfulness
drop below target).

**Definition of Ready.** TASK-034, TASK-035 merged.

**Steps.**
1. CLI runs both evaluators; write JSON/Markdown reports to `data/evaluation/reports/`.
2. Compare against success thresholds; exit non-zero on regression.
3. Add `make evaluate`; record a latency benchmark (P50/P95/P99).

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-115 | `test_cli_runs_and_writes_report` | performance/integration (mocked) |
| TEST-116 | `test_regression_gate_fails_below_threshold` | performance |
| TEST-117 | `test_latency_percentiles_recorded` | performance |

**Definition of Done.** CLI produces reports and fails on regression; `make evaluate` works; ≥90%.

**Acceptance criteria.** A sub-threshold run exits non-zero; an above-threshold run exits 0 with a report.

**Commit message.** `feat(evaluation): evaluation CLI and regression gate (TASK-036)`

---

## Sprint 7 Definition of Done (roll-up)

- [ ] 100-question benchmark loads; retrieval metrics verified.
- [ ] All four retrieval strategies compared and best selected.
- [ ] LLM answers evaluated across prompts and models; best config selected.
- [ ] Evaluation CLI + regression gate enforced; ≥90% coverage.
- [ ] Sprint 7 tasks `Done` in [`TASK_INDEX.md`](./TASK_INDEX.md).
