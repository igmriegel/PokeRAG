#!/usr/bin/env python3
"""
Run a backup / restore / rollback drill.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pokemon_tcg_rag.operations.recovery import run_recovery_drill


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run recovery drill.")
    parser.add_argument("--source-dir", type=Path, default=Path("data"))
    parser.add_argument("--backup-dir", type=Path, default=Path("data/backups"))
    parser.add_argument("--restore-dir", type=Path, default=Path("data/restores"))
    parser.add_argument("--events", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=Path("data/evaluation/reports/recovery.json"))
    args = parser.parse_args(argv)

    result = run_recovery_drill(args.source_dir, args.backup_dir, args.restore_dir, args.events)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
