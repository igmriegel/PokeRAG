"""
TASK-070 — Documentation reconciliation smoke tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parents[2]
README_FILE = PROJECT_ROOT / "README.md"
CHANGELOG_FILE = PROJECT_ROOT / "CHANGELOG.md"


@pytest.mark.smoke
def test_readme_uses_current_repo_and_commands() -> None:
    content = README_FILE.read_text(encoding="utf-8")
    assert "git@github.com:igmriegel/PokeRAG.git" in content
    assert "make quality" in content
    assert "make seed" in content
    assert "docker compose up --build -d" in content


@pytest.mark.smoke
def test_changelog_exists_and_is_unreleased() -> None:
    content = CHANGELOG_FILE.read_text(encoding="utf-8")
    assert "## [Unreleased]" in content
    assert "Security hardening" in content
