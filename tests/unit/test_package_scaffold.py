"""
TASK-001 — TEST-001, TEST-002

Unit tests for package scaffold and dependency pinning.
"""

import re
from pathlib import Path

import pytest


REQUIREMENTS_PATH = Path(__file__).parents[2] / "requirements.txt"


@pytest.mark.unit
def test_package_importable() -> None:
    """TEST-001: The pokemon_tcg_rag package must be importable."""
    import pokemon_tcg_rag  # noqa: F401

    assert hasattr(pokemon_tcg_rag, "__version__"), "Package must expose __version__"


@pytest.mark.unit
def test_requirements_are_pinned() -> None:
    """TEST-002: Every non-comment, non-blank line in requirements.txt must use == pinning."""
    assert REQUIREMENTS_PATH.exists(), f"requirements.txt not found at {REQUIREMENTS_PATH}"

    unpinned: list[str] = []
    for raw_line in REQUIREMENTS_PATH.read_text().splitlines():
        line = raw_line.strip()
        # Skip blank lines and comments
        if not line or line.startswith("#"):
            continue
        # A correctly pinned line must have == and no loose specifiers
        has_exact_pin = "==" in line
        has_loose_specifier = any(op in line for op in [">=", "<=", "!=", "~="])
        # Also reject lines with bare > or < not part of >=, <=, !=
        has_bare_gt = bool(re.search(r">(?!=)", line))
        has_bare_lt = bool(re.search(r"<(?!=)", line))
        if not has_exact_pin or has_loose_specifier or has_bare_gt or has_bare_lt:
            unpinned.append(line)

    assert not unpinned, (
        f"Found {len(unpinned)} unpinned dependency/dependencies in requirements.txt:\n"
        + "\n".join(f"  {u}" for u in unpinned)
    )
