"""
Final production scorecard helpers.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class ScorecardResult:
    passed: bool
    missing_artifacts: list[str]
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "missing_artifacts": self.missing_artifacts,
            "summary": self.summary,
        }


def build_scorecard(required_artifacts: dict[str, Path], evidence: dict[str, Any]) -> ScorecardResult:
    missing = [name for name, path in required_artifacts.items() if not path.exists()]
    summary = {
        "required_artifacts": {name: str(path) for name, path in required_artifacts.items()},
        "evidence": evidence,
    }
    return ScorecardResult(passed=not missing, missing_artifacts=missing, summary=summary)


def load_evidence(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
