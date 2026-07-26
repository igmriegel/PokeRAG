"""
TASK-067 — Clean-clone CI and coverage gate smoke tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).parents[2]
CI_FILE = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"


@pytest.mark.smoke
def test_ci_uses_runtime_matrix_and_coverage_gate() -> None:
    config = yaml.safe_load(CI_FILE.read_text(encoding="utf-8"))

    quality_job = config["jobs"]["quality-gate"]
    matrix = quality_job["strategy"]["matrix"]["python-version"]
    assert matrix == ["3.11", "3.12"]

    unit_job = config["jobs"]["unit-and-integration-tests"]
    assert unit_job["strategy"]["matrix"]["python-version"] == ["3.11", "3.12"]

    coverage_job = config["jobs"]["coverage-gate"]
    coverage_steps = [step.get("name", "") for step in coverage_job["steps"]]
    assert (
        "Execute Unit and Integration Tests with Coverage (Min 90%)" in coverage_steps
    )
