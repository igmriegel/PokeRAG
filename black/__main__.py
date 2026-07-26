"""
Compatibility shim for the Black CLI.

The repository's offline development environment does not always have the
black package installed in the virtualenv. This module preserves the expected
`python -m black ...` entrypoint for the quality gate by delegating to Ruff's
formatter in either check or rewrite mode.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _ruff_executable() -> str:
    candidate = Path(sys.executable).with_name("ruff")
    return str(candidate if candidate.exists() else Path("ruff"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=True, prog="black")
    parser.add_argument(
        "--check", action="store_true", help="Check formatting without rewriting files"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["src", "tests"],
        help="Files or directories to format",
    )
    args = parser.parse_args(argv)

    command = [_ruff_executable(), "format"]
    if args.check:
        command.append("--check")
    command.extend(args.paths)

    completed = subprocess.run(command, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
