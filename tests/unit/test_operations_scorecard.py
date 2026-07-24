"""
Unit tests for production scorecard helpers.
"""

from __future__ import annotations

from pathlib import Path

from pokemon_tcg_rag.operations.scorecard import build_scorecard


def test_build_scorecard_reports_missing_artifacts(tmp_path: Path) -> None:
    present = tmp_path / "present.json"
    present.write_text("{}", encoding="utf-8")
    scorecard = build_scorecard({"present": present, "missing": tmp_path / "missing.json"}, {})

    assert scorecard.passed is False
    assert scorecard.missing_artifacts == ["missing"]
