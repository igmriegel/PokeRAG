"""
Backup, restore, rollback and DORA helpers.
"""

from __future__ import annotations

import json
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class DORAMetrics:
    deployment_frequency: float
    lead_time_hours: float
    change_failure_rate: float
    mttr_minutes: float

    def to_dict(self) -> dict[str, float]:
        return {
            "deployment_frequency": self.deployment_frequency,
            "lead_time_hours": self.lead_time_hours,
            "change_failure_rate": self.change_failure_rate,
            "mttr_minutes": self.mttr_minutes,
        }


def snapshot_directory(source_dir: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    snapshot_dir = backup_dir / f"snapshot-{int(time.time())}"
    if snapshot_dir.exists():
        shutil.rmtree(snapshot_dir)
    shutil.copytree(source_dir, snapshot_dir)
    return snapshot_dir


def restore_directory(snapshot_dir: Path, restore_dir: Path) -> Path:
    restore_dir.mkdir(parents=True, exist_ok=True)
    target = restore_dir / snapshot_dir.name
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(snapshot_dir, target)
    return target


def calculate_dora_metrics(events: list[dict[str, Any]]) -> DORAMetrics:
    deployments = [event for event in events if event.get("type") == "deploy"]
    failures = [event for event in events if event.get("type") == "change_failure"]
    mttr_values = [float(event.get("mttr_minutes", 0.0)) for event in events if event.get("type") == "incident"]
    lead_times = [float(event.get("lead_time_hours", 0.0)) for event in deployments if event.get("lead_time_hours")]

    deployment_frequency = float(len(deployments))
    lead_time_hours = round(sum(lead_times) / len(lead_times), 4) if lead_times else 0.0
    change_failure_rate = round(len(failures) / len(deployments), 4) if deployments else 0.0
    mttr_minutes = round(sum(mttr_values) / len(mttr_values), 4) if mttr_values else 0.0
    return DORAMetrics(
        deployment_frequency=deployment_frequency,
        lead_time_hours=lead_time_hours,
        change_failure_rate=change_failure_rate,
        mttr_minutes=mttr_minutes,
    )


def run_recovery_drill(
    source_dir: Path, backup_root: Path, restore_root: Path, events_path: Path | None = None
) -> dict[str, Any]:
    start = time.perf_counter()
    snapshot_dir = snapshot_directory(source_dir, backup_root)
    restore_dir = restore_directory(snapshot_dir, restore_root)
    elapsed = round(time.perf_counter() - start, 4)
    events: list[dict[str, Any]] = []
    if events_path and events_path.exists():
        events = json.loads(events_path.read_text(encoding="utf-8"))
    dora = calculate_dora_metrics(events)
    return {
        "snapshot_dir": str(snapshot_dir),
        "restore_dir": str(restore_dir),
        "elapsed_seconds": elapsed,
        "dora": dora.to_dict(),
    }
