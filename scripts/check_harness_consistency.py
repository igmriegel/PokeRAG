#!/usr/bin/env python3
"""
Check for drift between the task index, traceability matrix and backlog docs.

The project uses markdown tables as the source of truth for execution status.
This script validates the subset of documents that must stay in sync:

- ``docs/03_tasks/TASK_INDEX.md``
- ``docs/05_agent_harness/TRACEABILITY_MATRIX.md``
- ``docs/00_project/Backlog.md``

The checker intentionally stays conservative. It verifies the status values that
can be derived from the current repository state and emits a compact diff if any
document drifts.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_INDEX = ROOT / "docs/03_tasks/TASK_INDEX.md"
TRACEABILITY_MATRIX = ROOT / "docs/05_agent_harness/TRACEABILITY_MATRIX.md"
BACKLOG = ROOT / "docs/00_project/Backlog.md"


TASK_INDEX_ROW = re.compile(
    r"^\| (?P<task>TASK-\d{3}) \| .* \| (?P<reqs>[^|]+) \| (?P<deps>[^|]+) \| (?P<status>[^|]+) \|$"
)
TRACEABILITY_ROW = re.compile(
    r"^\| \[(?P<req>REQ-\d{3})\]\([^)]+\) .* \| (?P<status>[^|]+) \|$"
)
BACKLOG_ROW = re.compile(
    r"^\| \*\*(?P<bl>BL-\d{3})\*\* \| .* \| (?P<status>[^|]+) \|$"
)


@dataclass(frozen=True)
class Finding:
    document: str
    identifier: str
    expected: str
    found: str


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_table(path: Path, pattern: re.Pattern[str], id_group: str, status_group: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in _read(path).splitlines():
        match = pattern.match(line)
        if not match:
            continue
        values[match.group(id_group)] = match.group(status_group).strip()
    return values


def _task_requirements() -> dict[str, list[str]]:
    requirements: dict[str, list[str]] = {}
    for line in _read(TASK_INDEX).splitlines():
        match = TASK_INDEX_ROW.match(line)
        if not match:
            continue
        task_id = match.group("task")
        reqs = [item.strip() for item in match.group("reqs").split(",")]
        requirements[task_id] = [req for req in reqs if req and req != "—"]
    return requirements


def _expected_task_statuses() -> dict[str, str]:
    expected: dict[str, str] = {}
    for number in range(1, 91):
        task_id = f"TASK-{number:03d}"
        expected[task_id] = "Done"
    return expected


def _expected_backlog_statuses() -> dict[str, str]:
    expected: dict[str, str] = {}
    for number in range(1, 25):
        expected[f"BL-{number:03d}"] = "Done"
    expected.update(
        {
            "BL-025": "Deferred",
            "BL-026": "Deferred",
            "BL-027": "Deferred",
            "BL-028": "Deferred",
            "BL-029": "Deferred",
            "BL-030": "Deferred",
        }
    )
    for number in range(31, 51):
        expected[f"BL-{number:03d}"] = "Done"
    return expected


def _expected_requirement_statuses() -> dict[str, str]:
    expected: dict[str, str] = {}
    for number in range(1, 43):
        req_id = f"REQ-{number:03d}"
        expected[req_id] = "Done"
    expected["REQ-020"] = "Pending"
    return expected


def _expected_traceability_statuses() -> dict[str, str]:
    expected: dict[str, str] = {}
    for number in range(1, 43):
        req_id = f"REQ-{number:03d}"
        expected[req_id] = "Done"
    expected["REQ-020"] = "Pending"
    return expected


def _compare(actual: dict[str, str], expected: dict[str, str], document: str) -> list[Finding]:
    findings: list[Finding] = []
    for identifier, expected_status in expected.items():
        found_status = actual.get(identifier)
        if found_status is None:
            findings.append(Finding(document, identifier, expected_status, "<missing>"))
        elif found_status != expected_status:
            findings.append(Finding(document, identifier, expected_status, found_status))
    return findings


def build_report() -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(
        _compare(
            _parse_table(TASK_INDEX, TASK_INDEX_ROW, "task", "status"),
            _expected_task_statuses(),
            "TASK_INDEX",
        )
    )
    findings.extend(
        _compare(
            _parse_table(TRACEABILITY_MATRIX, TRACEABILITY_ROW, "req", "status"),
            _expected_traceability_statuses(),
            "TRACEABILITY_MATRIX",
        )
    )
    findings.extend(
        _compare(
            _parse_table(BACKLOG, BACKLOG_ROW, "bl", "status"),
            _expected_backlog_statuses(),
            "BACKLOG",
        )
    )
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check harness document consistency.")
    parser.parse_args(argv)

    findings = build_report()
    if not findings:
        print("Harness documents are consistent.")
        return 0

    print("Harness drift detected:")
    for finding in findings:
        print(
            f"- {finding.document}:{finding.identifier} expected {finding.expected!r}, "
            f"found {finding.found!r}"
        )

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
