#!/usr/bin/env python3
"""
CLI script to seed vector database and relational database with baseline collections.
"""

from pokemon_tcg_rag.storage.relational_db import RelationalDatabase
from pokemon_tcg_rag.storage.vector_db import VectorDatabase


def main() -> None:
    print("Seeding Vector Database (Qdrant)...")
    vdb = VectorDatabase()
    vdb.init_collection()

    print("Seeding Relational Database (PostgreSQL)...")
    rdb = RelationalDatabase()
    rdb.init_db()

    print("Database seeding completed successfully.")

if __name__ == "__main__":
    main()
