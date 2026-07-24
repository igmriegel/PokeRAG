"""
TASK-032 — Benchmark dataset loader tests.
"""

from __future__ import annotations

import json

import pytest

from pokemon_tcg_rag.evaluation.dataset import EvaluationDatasetLoader


@pytest.mark.evaluation
def test_load_dataset_parses_cases() -> None:
    loader = EvaluationDatasetLoader()

    cases = loader.load_dataset()

    assert len(cases) == 100
    assert cases[0].question_id == "Q001"
    assert cases[0].expected_source.value == "rulebook_pdf"
    assert cases[-1].question_id == "Q100"
    assert all(case.reference_answer for case in cases)


@pytest.mark.evaluation
def test_dataset_has_100_cases() -> None:
    loader = EvaluationDatasetLoader()

    cases = loader.load_dataset()
    sources = {case.expected_source for case in cases}

    assert len(cases) == 100
    assert len(sources) == 9


@pytest.mark.evaluation
def test_malformed_case_raises(tmp_path) -> None:
    dataset_path = tmp_path / "broken.json"
    dataset_path.write_text(
        json.dumps(
            [
                {
                    "question_id": "Q001",
                    "question": "Broken case without document ids",
                    "expected_source": "rulebook_pdf",
                    "reference_answer": "Answer",
                }
            ]
        ),
        encoding="utf-8",
    )

    loader = EvaluationDatasetLoader(dataset_path)

    with pytest.raises(ValueError):
        loader.load_dataset()
