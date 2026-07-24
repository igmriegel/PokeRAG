"""
TASK-071 — Benchmark dataset policy tests.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pokemon_tcg_rag.evaluation.dataset import EvaluationDatasetLoader

PROJECT_ROOT = Path(__file__).parents[2]
CARD_FILE = PROJECT_ROOT / "data" / "evaluation" / "benchmark_card.md"
MANIFEST_FILE = PROJECT_ROOT / "data" / "evaluation" / "benchmark_manifest.json"


@pytest.mark.evaluation
def test_benchmark_artifacts_present() -> None:
    assert CARD_FILE.exists()
    assert MANIFEST_FILE.exists()


@pytest.mark.evaluation
def test_benchmark_manifest_matches_dataset() -> None:
    manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    cases = EvaluationDatasetLoader().load_dataset()

    assert manifest["total_cases"] == len(cases) == 100
    assert manifest["benchmark_sha256"]
    assert manifest["corpus_manifest_sha256"]
    assert manifest["review_status"] == "reviewed"


@pytest.mark.evaluation
def test_benchmark_review_policy_documents_splits() -> None:
    guide = CARD_FILE.read_text(encoding="utf-8")
    review_guide = (PROJECT_ROOT / "data" / "evaluation" / "review_guide.md").read_text(
        encoding="utf-8"
    )

    assert "train/dev/test" in guide or "train/dev/test" in review_guide
    assert "No leakage" in review_guide
