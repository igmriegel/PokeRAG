"""
TASK-001 — TEST-001, TEST-002

Unit tests for package scaffold and dependency pinning.
"""

import re
from pathlib import Path

import pytest

REQUIREMENTS_PATH = Path(__file__).parents[2] / "requirements.txt"
RUNTIME_REQUIREMENTS_PATH = Path(__file__).parents[2] / "requirements.runtime.txt"
DEV_REQUIREMENTS_PATH = Path(__file__).parents[2] / "requirements.dev.txt"
EVAL_REQUIREMENTS_PATH = Path(__file__).parents[2] / "requirements.eval.txt"


@pytest.mark.unit
def test_package_importable() -> None:
    """TEST-001: The pokemon_tcg_rag package must be importable."""
    import pokemon_tcg_rag  # noqa: F401

    assert hasattr(pokemon_tcg_rag, "__version__"), "Package must expose __version__"


@pytest.mark.unit
def test_requirements_are_pinned() -> None:
    """TEST-002: Every non-comment, non-blank line in requirements.txt must use == pinning."""
    assert (
        REQUIREMENTS_PATH.exists()
    ), f"requirements.txt not found at {REQUIREMENTS_PATH}"

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


@pytest.mark.unit
def test_profile_locks_are_pinned() -> None:
    """Runtime, dev and evaluation locks must stay exact-pinned."""
    for path in (
        RUNTIME_REQUIREMENTS_PATH,
        DEV_REQUIREMENTS_PATH,
        EVAL_REQUIREMENTS_PATH,
    ):
        assert path.exists(), f"{path.name} not found at {path}"
        for raw_line in path.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            assert "==" in line, f"Unpinned dependency found in {path.name}: {line}"


@pytest.mark.unit
def test_runtime_lock_includes_observability_dependencies() -> None:
    """Runtime containers import OpenTelemetry during application startup."""
    dependencies = {
        line.split("==", maxsplit=1)[0]
        for line in RUNTIME_REQUIREMENTS_PATH.read_text().splitlines()
        if line and not line.startswith("#")
    }
    assert {"opentelemetry-api", "opentelemetry-sdk"}.issubset(dependencies)
