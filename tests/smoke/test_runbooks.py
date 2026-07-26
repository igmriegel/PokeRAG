"""
Smoke tests for operational runbooks.
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_runbooks_reference_safe_commands_and_owners() -> None:
    content = (PROJECT_ROOT / "docs/06_operations/RUNBOOKS.md").read_text(
        encoding="utf-8"
    )

    assert "Tech Lead" in content
    assert "make run-api" in content
    assert "curl -s http://localhost:8000/health" in content
    assert "PokemonRAGHighLatencyP95" in content
