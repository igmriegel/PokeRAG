#!/usr/bin/env python3
"""
Validate the bundled local demo corpus and report its contents.
"""

from __future__ import annotations

from pokemon_tcg_rag.monitoring.logger import setup_logging
from pokemon_tcg_rag.storage.indexing import CORPUS_MANIFEST_NAME, load_chunks


def main() -> int:
    setup_logging()
    chunks = load_chunks("data/chunks")
    if not chunks:
        raise SystemExit(
            f"No chunks found in data/chunks (expected {CORPUS_MANIFEST_NAME})."
        )

    print(f"Bootstrap corpus ready: {len(chunks)} chunks loaded from data/chunks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
