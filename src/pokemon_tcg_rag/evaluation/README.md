# Evaluation Module (`evaluation/`)

This directory contains evaluation benchmarks, metrics calculation, and test suites:
- `metrics.py`: Standard IR metrics (Recall@5, Recall@10, MRR, Hit Rate) and Faithfulness evaluators.
- `dataset.py`: Benchmark 100-question ground truth dataset loader.
- `evaluator.py`: Automatic evaluation runner comparing Dense vs. BM25 vs. Hybrid vs. Re-ranking.
