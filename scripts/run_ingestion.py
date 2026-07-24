#!/usr/bin/env python3
"""
CLI script to run the ingestion pipeline.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from pokemon_tcg_rag.ingestion.pipeline import IngestionPipeline
from pokemon_tcg_rag.monitoring.logger import setup_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Pokemon TCG ingestion pipeline")
    parser.add_argument(
        "--sources",
        nargs="+",
        default=None,
        help="Optional source families to run: pokegym html pdf (space or comma separated)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Override the processed output directory",
    )
    parser.add_argument(
        "--index",
        action="store_true",
        help="Normalize, chunk, and index the ingestion output",
    )
    return parser


def _flatten_sources(values: Sequence[str] | None) -> list[str] | None:
    if values is None:
        return None
    flattened: list[str] = []
    for value in values:
        flattened.extend(token.strip() for token in value.split(",") if token.strip())
    return flattened or None


def main(argv: Sequence[str] | None = None) -> int:
    setup_logging()
    parser = build_parser()
    args = parser.parse_args(argv)

    pipeline = IngestionPipeline(processed_dir=args.out_dir)
    result = pipeline.run(sources=_flatten_sources(args.sources), index=args.index)
    unit = "chunks" if args.index else "documents"
    print(f"Ingestion successful. Generated {len(result)} {unit}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
