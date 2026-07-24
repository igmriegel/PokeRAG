# SPRINT_15 — Retrieval Quality

## Objective

Replace synthetic retrieval claims with a reviewed benchmark, real production-strategy runs,
controlled ablations, incremental corpus lifecycle and an enforceable regression baseline.

| Item | Outcome | Depends on |
| :--- | :--- | :--- |
| TASK-071 | Reviewed versioned benchmark | TASK-063 |
| TASK-072 | Production retrieval evaluation | TASK-061, TASK-071 |
| TASK-073 | Retrieval ablation matrix | TASK-072 |
| TASK-074 | Incremental corpus lifecycle | TASK-056, TASK-063 |
| TASK-075 | Retrieval report/regression gate | TASK-072..074 |

## Delivery sequence and capacity

TASK-071 and TASK-074 can run in parallel; TASK-072 follows benchmark completion, then TASK-073;
all converge at TASK-075. Planned load: 37 SP.

## Risks and mitigations

- Label quality/domain availability: two-person sampled review and explicit adjudication.
- Experiment cost: preregister a bounded matrix and cache only content-addressed artifacts.
- Benchmark leakage: fixed held-out split and corpus/config hash matching.

## Deliverables

Dataset card and reviewed benchmark, real strategy adapters, raw ranked results, ablation report,
incremental ingestion engine and retrieval baseline registry.

## Success criteria

SC-039 and SC-040 pass; TEST-159..163 are green; selected configuration achieves Recall@10 >0.90
and MRR ≥0.75, or a human-approved criterion revision explains infeasibility.
