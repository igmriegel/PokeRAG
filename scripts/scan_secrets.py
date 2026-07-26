#!/usr/bin/env python3
"""
Lightweight repository secret scanner for CI.

The scanner is intentionally conservative: it only inspects tracked source/config files
and looks for obviously real credentials in known secret-bearing keys or private key blocks.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

SENSITIVE_KEYS = {
    "OPENAI_API_KEY",
    "POSTGRES_PASSWORD",
    "POSTGRES_USER",
    "QDRANT_API_KEY",
    "GRAFANA_ADMIN_PASSWORD",
    "GRAFANA_ADMIN_USER",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AZURE_CLIENT_SECRET",
    "GCP_SERVICE_ACCOUNT_KEY",
    "SSH_PRIVATE_KEY",
}

SAFE_PLACEHOLDERS = (
    "change_me",
    "your_",
    "example",
    "placeholder",
    "todo",
    "dummy",
    "",
)
INCLUDE_SUFFIXES = {
    ".py",
    ".yml",
    ".yaml",
    ".toml",
    ".txt",
    ".md",
    ".env",
    ".ini",
    ".cfg",
    ".json",
}

PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"(?i)\bsk-[A-Za-z0-9]{20,}\b"),
]


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"], check=True, capture_output=True, text=True
    )
    return [Path(line) for line in result.stdout.splitlines() if line]


def is_safe_value(value: str) -> bool:
    lowered = value.strip().lower()
    return any(token in lowered for token in SAFE_PLACEHOLDERS)


def scan_file(path: Path) -> list[str]:
    findings: list[str] = []
    if path.suffix.lower() not in INCLUDE_SUFFIXES and path.name not in {
        ".env",
        "Dockerfile",
    }:
        return findings

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return findings

    for pattern in PATTERNS:
        if pattern.search(content):
            findings.append(f"{path}: matched secret-pattern '{pattern.pattern}'")

    for line_number, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key not in SENSITIVE_KEYS:
            continue
        if not is_safe_value(value):
            findings.append(
                f"{path}:{line_number}: {key} appears to contain a real secret"
            )

    return findings


def main() -> int:
    findings: list[str] = []
    for path in tracked_files():
        if path.parts and path.parts[0] in {".git", ".venv", "data", "htmlcov"}:
            continue
        findings.extend(scan_file(path))

    if findings:
        print("Potential secret exposure detected:")
        for finding in findings:
            print(f"- {finding}")
        return 1

    print("No obvious secrets detected in tracked repository files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
