"""
Chunk embedding and Qdrant seeding helpers.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

import pandas as pd
from sentence_transformers import SentenceTransformer

from pokemon_tcg_rag.config.settings import get_settings
from pokemon_tcg_rag.domain.exceptions import IngestionError
from pokemon_tcg_rag.domain.models import Chunk, DocumentMetadata, DocumentSource, RuleType
from pokemon_tcg_rag.monitoring.logger import get_logger, setup_logging
from pokemon_tcg_rag.storage.vector_db import VectorDatabase

LOGGER = get_logger(__name__)


class ChunkEmbedder:
    """Encode chunk texts into 1024-dimensional vectors."""

    def __init__(self, model_name: str | None = None, model: SentenceTransformer | None = None) -> None:
        settings = get_settings()
        self.model_name = model_name or settings.EMBEDDING_MODEL_PRIMARY
        self._model = model or SentenceTransformer(self.model_name)

    def embed_texts(self, texts: Sequence[str], batch_size: int = 32) -> list[list[float]]:
        vectors = self._model.encode(
            list(texts),
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return [vector.tolist() if hasattr(vector, "tolist") else list(vector) for vector in vectors]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Embed and seed chunks into Qdrant")
    parser.add_argument(
        "--chunks-dir",
        type=Path,
        default=None,
        help="Directory containing chunk parquet files",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Embedding batch size",
    )
    return parser


def load_chunks(chunks_dir: str | Path | None = None) -> list[Chunk]:
    settings = get_settings()
    directory = Path(chunks_dir or settings.DATA_CHUNKS_DIR)
    if not directory.exists():
        return []

    chunks: list[Chunk] = []
    for path in sorted(directory.rglob("*")):
        if path.suffix.lower() == ".parquet":
            frame = pd.read_parquet(path)
            for record in frame.to_dict(orient="records"):
                chunks.append(_record_to_chunk(record))
        elif path.suffix.lower() in {".jsonl", ".ndjson"}:
            with path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    stripped = line.strip()
                    if not stripped:
                        continue
                    chunks.append(_record_to_chunk(json.loads(stripped)))
    return chunks


def seed_chunks(
    chunks: Sequence[Chunk],
    *,
    vector_db: VectorDatabase | None = None,
    embedder: ChunkEmbedder | None = None,
    batch_size: int = 32,
) -> int:
    if not chunks:
        return 0

    vector_store = vector_db or VectorDatabase()
    embedder = embedder or ChunkEmbedder()

    texts = [chunk.text for chunk in chunks]
    embeddings = embedder.embed_texts(texts, batch_size=batch_size)
    embedded_chunks: list[Chunk] = []
    for chunk, embedding in zip(chunks, embeddings, strict=True):
        embedded_chunks.append(chunk.model_copy(update={"embedding": embedding}))

    vector_store.init_collection()
    vector_store.upsert_chunks(embedded_chunks)
    LOGGER.info("chunks_seeded", count=len(embedded_chunks))
    return len(embedded_chunks)


def seed_from_directory(
    chunks_dir: str | Path | None = None,
    *,
    vector_db: VectorDatabase | None = None,
    embedder: ChunkEmbedder | None = None,
    batch_size: int = 32,
) -> int:
    chunks = load_chunks(chunks_dir)
    return seed_chunks(chunks, vector_db=vector_db, embedder=embedder, batch_size=batch_size)


def _record_to_chunk(record: dict[str, object]) -> Chunk:
    page_number = record.get("page_number")
    if page_number is not None and not isinstance(page_number, int):
        page_number = int(page_number)

    metadata = DocumentMetadata(
        source=DocumentSource(str(record["source"])),
        document_title=str(record["document_title"]),
        page_number=page_number,
        section_title=None if record.get("section_title") is None else str(record["section_title"]),
        card_name=None if record.get("card_name") is None else str(record["card_name"]),
        rule_type=RuleType(str(record["rule_type"])),
        publication_date=None if record.get("publication_date") is None else str(record["publication_date"]),
        source_url=None if record.get("source_url") is None else str(record["source_url"]),
        checksum=None if record.get("checksum") is None else str(record["checksum"]),
    )
    embedding = record.get("embedding")
    return Chunk(
        chunk_id=str(record["chunk_id"]),
        doc_id=str(record["doc_id"]),
        text=str(record["text"]),
        token_count=int(record.get("token_count", 0)),
        metadata=metadata,
        embedding=embedding if isinstance(embedding, list) else None,
    )


def main(argv: Sequence[str] | None = None) -> int:
    setup_logging()
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        total = seed_from_directory(args.chunks_dir, batch_size=args.batch_size)
    except Exception as exc:  # pragma: no cover - CLI boundary
        raise IngestionError(f"Failed to seed Qdrant index: {exc}") from exc

    print(f"Seeded {total} chunks into Qdrant.")
    return 0
