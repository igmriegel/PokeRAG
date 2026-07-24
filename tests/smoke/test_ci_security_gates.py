"""
TASK-058 — CI security gate smoke tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).parents[2]
CI_FILE = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"


@pytest.mark.smoke
def test_ci_pipeline_includes_security_artifacts() -> None:
    config = yaml.safe_load(CI_FILE.read_text(encoding="utf-8"))
    jobs = config["jobs"]
    dependency_scan = jobs["dependency-scan"]["steps"]

    step_names = [step.get("name", "") for step in dependency_scan]
    assert "Run pip-audit" in step_names
    assert "Generate CycloneDX SBOM" in step_names
    assert "Upload SBOM Artifact" in step_names


@pytest.mark.smoke
def test_ci_quality_gate_includes_secret_scan() -> None:
    config = yaml.safe_load(CI_FILE.read_text(encoding="utf-8"))
    steps = config["jobs"]["quality-gate"]["steps"]
    assert any(step.get("name") == "Run Repository Secret Scan" for step in steps)
