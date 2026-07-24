#!/usr/bin/env python3
"""
Run a capacity and cost qualification sweep.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pokemon_tcg_rag.operations.qualification import run_qualification


class _SyntheticHandler:
    def __init__(self, delay_seconds: float) -> None:
        self.delay_seconds = delay_seconds

    def query(self, question: str, top_k: int | None = None) -> object:
        import time

        time.sleep(self.delay_seconds)
        return {"question": question, "top_k": top_k}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run capacity qualification.")
    parser.add_argument("--scenario", default="warm")
    parser.add_argument("--output", type=Path, default=Path("data/evaluation/reports/capacity.json"))
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args(argv)

    handler = _SyntheticHandler(delay_seconds=0.01 if args.scenario != "cold" else 0.05)
    questions = [f"benchmark question {index}" for index in range(1, 21)]
    result = run_qualification(
        handler,
        questions,
        scenario=args.scenario,
        concurrency=args.concurrency,
        warmup_count=2 if args.scenario == "warm" else 0,
        cost_per_call_usd=0.0,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    print(json.dumps(result.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
