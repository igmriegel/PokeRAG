"""
Chunk embedding and Qdrant seeding helpers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from sentence_transformers import SentenceTransformer

from pokemon_tcg_rag.config.settings import get_settings
from pokemon_tcg_rag.domain.exceptions import IngestionError
from pokemon_tcg_rag.domain.models import Chunk, DocumentMetadata, DocumentSource, RuleType
from pokemon_tcg_rag.monitoring.logger import get_logger, setup_logging
from pokemon_tcg_rag.storage.vector_db import VectorDatabase

LOGGER = get_logger(__name__)
CORPUS_MANIFEST_NAME = "corpus_manifest.json"


@dataclass(frozen=True, slots=True)
class CorpusManifestFile:
    """Single file entry within a versioned corpus manifest."""

    path: str
    sha256: str
    chunk_count: int | None = None


@dataclass(frozen=True, slots=True)
class CorpusManifest:
    """Versioned corpus descriptor used for reproducible hydration."""

    corpus_id: str
    version: str
    description: str
    expected_chunk_count: int | None
    files: tuple[CorpusManifestFile, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CorpusManifest:
        files = tuple(
            CorpusManifestFile(
                path=str(entry["path"]),
                sha256=str(entry["sha256"]),
                chunk_count=int(entry["chunk_count"]) if entry.get("chunk_count") is not None else None,
            )
            for entry in data.get("files", [])
        )
        return cls(
            corpus_id=str(data["corpus_id"]),
            version=str(data["version"]),
            description=str(data.get("description", "")),
            expected_chunk_count=int(data["chunk_count"]) if data.get("chunk_count") is not None else None,
            files=files,
        )

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "corpus_id": self.corpus_id,
            "version": self.version,
            "description": self.description,
            "files": [
                {
                    "path": entry.path,
                    "sha256": entry.sha256,
                    "chunk_count": entry.chunk_count,
                }
                for entry in self.files
            ],
        }

    def manifest_sha256(self) -> str:
        canonical = json.dumps(self.canonical_payload(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def chunk_count(self) -> int:
        if self.expected_chunk_count is not None:
            return self.expected_chunk_count
        return sum(entry.chunk_count or 0 for entry in self.files)

    def source_hash(self) -> str:
        joined = "|".join(entry.sha256 for entry in self.files)
        return hashlib.sha256(joined.encode("utf-8")).hexdigest()

    def to_collection_metadata(self) -> dict[str, Any]:
        return {
            "corpus_id": self.corpus_id,
            "corpus_version": self.version,
            "corpus_description": self.description,
            "corpus_manifest_sha256": self.manifest_sha256(),
            "corpus_source_hash": self.source_hash(),
            "corpus_chunk_count": self.chunk_count(),
            "corpus_files": [entry.path for entry in self.files],
        }


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
    manifest = _load_manifest(directory)
    if manifest is not None:
        for entry in manifest["files"]:
            file_path = directory / entry["path"]
            _assert_file_hash(file_path, entry["sha256"])
            loaded = _load_chunks_from_path(file_path)
            if entry.get("chunk_count") is not None and len(loaded) != int(entry["chunk_count"]):
                raise IngestionError(
                    f"Corpus manifest chunk count mismatch for {file_path.name}: "
                    f"expected {entry['chunk_count']}, got {len(loaded)}"
                )
            chunks.extend(loaded)
        manifest_count = manifest.get("chunk_count")
        if manifest_count is not None and len(chunks) != int(manifest_count):
            raise IngestionError(
                f"Corpus manifest total chunk count mismatch: expected {manifest_count}, got {len(chunks)}"
            )
        return chunks

    for path in sorted(directory.rglob("*")):
        chunks.extend(_load_chunks_from_path(path))
    return chunks


def load_corpus_manifest(chunks_dir: str | Path | None = None) -> CorpusManifest | None:
    settings = get_settings()
    directory = Path(chunks_dir or settings.DATA_CHUNKS_DIR)
    if not directory.exists():
        return None
    raw_manifest = _load_manifest(directory)
    if raw_manifest is None:
        return None
    return CorpusManifest.from_dict(raw_manifest)


def _load_manifest(directory: Path) -> dict[str, Any] | None:
    manifest_path = directory / CORPUS_MANIFEST_NAME
    if not manifest_path.exists():
        return None
    with manifest_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_chunks_from_path(path: Path) -> list[Chunk]:
    if path.suffix.lower() == ".parquet":
        frame = pd.read_parquet(path)
        return [_record_to_chunk(record) for record in frame.to_dict(orient="records")]
    if path.suffix.lower() in {".jsonl", ".ndjson"}:
        chunks: list[Chunk] = []
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                stripped = line.strip()
                if not stripped:
                    continue
                chunks.append(_record_to_chunk(json.loads(stripped)))
        return chunks
    return []


def _assert_file_hash(path: Path, expected_sha256: str) -> None:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != expected_sha256:
        raise IngestionError(
            f"Corpus manifest hash mismatch for {path.name}: expected {expected_sha256}, got {digest}"
        )


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
