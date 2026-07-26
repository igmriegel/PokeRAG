"""
Unit tests for recovery drill helpers.
"""

from __future__ import annotations

from pathlib import Path

from pokemon_tcg_rag.operations.recovery import (
    calculate_dora_metrics,
    run_recovery_drill,
)


def test_calculate_dora_metrics() -> None:
    metrics = calculate_dora_metrics(
        [
            {"type": "deploy", "lead_time_hours": 2.0},
            {"type": "deploy", "lead_time_hours": 4.0},
            {"type": "change_failure"},
            {"type": "incident", "mttr_minutes": 30},
        ]
    )

    assert metrics.deployment_frequency == 2.0
    assert metrics.change_failure_rate == 0.5
    assert metrics.mttr_minutes == 30.0


def test_run_recovery_drill_copies_artifacts(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "file.txt").write_text("content", encoding="utf-8")
    output = run_recovery_drill(source, tmp_path / "backup", tmp_path / "restore")

    assert Path(output["snapshot_dir"]).exists()
    assert Path(output["restore_dir"]).exists()
