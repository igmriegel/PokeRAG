#!/usr/bin/env python3
"""
CLI script to run data ingestion and indexing pipeline.
"""

import sys
from pokemon_tcg_rag.ingestion.pipeline import IngestionPipeline
from pokemon_tcg_rag.monitoring.logger import setup_logging

def main() -> None:
    setup_logging()
    print("Starting Pokemon TCG Rules Ingestion Pipeline...")
    pipeline = IngestionPipeline()
    chunks = pipeline.run()
    print(f"Ingestion successful. Generated {len(chunks)} chunks.")

if __name__ == "__main__":
    main()
