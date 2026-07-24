"""
TASK-059 / TASK-060 — Security regression and release-gate harness smoke tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parents[2]
SECURITY_SCRIPT = PROJECT_ROOT / "scripts" / "run_security_regression.py"
RELEASE_SCRIPT = PROJECT_ROOT / "scripts" / "run_release_gate.py"


@pytest.mark.smoke
def test_security_regression_script_lists_core_security_suites() -> None:
    content = SECURITY_SCRIPT.read_text(encoding="utf-8")
    assert "test_api_security.py" in content
    assert "test_prompt_integrity.py" in content
    assert "test_platform_hardening.py" in content


@pytest.mark.smoke
def test_release_gate_script_composes_security_and_release_checks() -> None:
    content = RELEASE_SCRIPT.read_text(encoding="utf-8")
    assert "run_security_regression.py" in content
    assert "test_full_stack.py" in content
