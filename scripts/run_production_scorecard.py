#!/usr/bin/env python3
"""
Build the final production scorecard from existing artifacts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pokemon_tcg_rag.operations.scorecard import build_scorecard, load_evidence


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a production scorecard.")
    parser.add_argument("--evidence", type=Path, default=Path("docs/05_agent_harness/SECURITY_CLOSURE.md"))
    parser.add_argument("--output", type=Path, default=Path("data/evaluation/reports/scorecard.json"))
    args = parser.parse_args(argv)

    required_artifacts = {
        "security_closure": args.evidence,
        "evaluation_report": Path("data/evaluation/reports/evaluation_report.json"),
        "capacity_report": Path("data/evaluation/reports/capacity.json"),
        "recovery_report": Path("data/evaluation/reports/recovery.json"),
    }
    evidence = load_evidence(args.evidence) if args.evidence.exists() and args.evidence.suffix == ".json" else {"path": str(args.evidence)}
    scorecard = build_scorecard(required_artifacts, evidence)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(scorecard.to_dict(), indent=2), encoding="utf-8")
    print(json.dumps(scorecard.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
