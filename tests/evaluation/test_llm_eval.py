"""
Evaluation test suite for LLM output quality.
"""

import pytest
from pokemon_tcg_rag.evaluation.metrics import calculate_faithfulness


@pytest.mark.evaluation
def test_faithfulness_baseline() -> None:
    score = calculate_faithfulness("Rare Candy cannot be played on turn 1.", [])
    assert score >= 0.0
