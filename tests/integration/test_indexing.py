"""
TASK-015 — TEST-049, TEST-050, TEST-051

Integration tests for embedding and indexing chunks into Qdrant.
"""

from __future__ import annotations

import pytest

from pokemon_tcg_rag.domain.models import (
    Chunk,
    DocumentMetadata,
    DocumentSource,
    RuleType,
)
from pokemon_tcg_rag.storage import indexing as seed_db
from pokemon_tcg_rag.storage.indexing import (
    ChunkEmbedder,
    _record_to_chunk,
    seed_chunks,
)


class FakeSentenceTransformer:
    def encode(
        self,
        texts,
        batch_size=32,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ):  # noqa: D401
        return [[0.1] * 1024 for _ in texts]


def _make_chunk(chunk_id: str) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        doc_id="doc-1",
        text=f"Text for {chunk_id}",
        token_count=3,
        metadata=DocumentMetadata(
            source=DocumentSource.RULEBOOK_PDF,
            document_title="Rulebook",
            rule_type=RuleType.GENERAL_RULE,
        ),
    )


@pytest.mark.integration
def test_embedding_dimension_1024(monkeypatch: pytest.MonkeyPatch) -> None:
    """TEST-049: embeddings must be 1024-dimensional."""
    monkeypatch.setattr(
        seed_db,
        "SentenceTransformer",
        lambda *args, **kwargs: FakeSentenceTransformer(),
    )

    embedder = ChunkEmbedder()
    vectors = embedder.embed_texts(["a", "b"])

    assert len(vectors) == 2
    assert all(len(vector) == 1024 for vector in vectors)


@pytest.mark.integration
def test_seed_upserts_all_chunks(monkeypatch: pytest.MonkeyPatch) -> None:
    """TEST-050: all chunks must be embedded and upserted."""
    monkeypatch.setattr(
        seed_db,
        "SentenceTransformer",
        lambda *args, **kwargs: FakeSentenceTransformer(),
    )

    class DummyVectorDb:
        def __init__(self) -> None:
            self.collection_initialized = False
            self.upserted = None

        def init_collection(self, metadata=None) -> None:
            self.collection_initialized = True

        def upsert_chunks(self, chunks):
            self.upserted = list(chunks)

    vector_db = DummyVectorDb()
    chunks = [_make_chunk("chunk-1"), _make_chunk("chunk-2")]

    total = seed_chunks(chunks, vector_db=vector_db, embedder=ChunkEmbedder())

    assert total == 2
    assert vector_db.collection_initialized is True
    assert len(vector_db.upserted) == 2
    assert all(len(chunk.embedding or []) == 1024 for chunk in vector_db.upserted)


@pytest.mark.integration
def test_parquet_nan_optional_fields_are_loaded_as_none() -> None:
    """Pandas NaN values must not break corpus loading."""
    chunk = _record_to_chunk(
        {
            "chunk_id": "chunk-1",
            "doc_id": "doc-1",
            "text": "Rule text",
            "token_count": 2,
            "source": DocumentSource.POKEGYM.value,
            "document_title": "Ruling",
            "page_number": float("nan"),
            "section_title": float("nan"),
            "card_name": float("nan"),
            "rule_type": RuleType.RULING.value,
            "publication_date": float("nan"),
            "source_url": float("nan"),
            "checksum": float("nan"),
        }
    )

    assert chunk.metadata.page_number is None
    assert chunk.metadata.card_name is None
    assert chunk.metadata.source_url is None


@pytest.mark.integration
def test_seed_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    """TEST-051: rerunning the seed job against the same chunks must not duplicate points."""
    monkeypatch.setattr(
        seed_db,
        "SentenceTransformer",
        lambda *args, **kwargs: FakeSentenceTransformer(),
    )

    class DummyVectorDb:
        def __init__(self) -> None:
            self.collection_initialized = False
            self.points_by_id: dict[str, Chunk] = {}

        def init_collection(self, metadata=None) -> None:
            self.collection_initialized = True

        def upsert_chunks(self, chunks):
            for chunk in chunks:
                self.points_by_id[chunk.chunk_id] = chunk

        def count(self) -> int:
            return len(self.points_by_id)

    vector_db = DummyVectorDb()
    chunks = [_make_chunk("chunk-1"), _make_chunk("chunk-2")]

    first_total = seed_chunks(chunks, vector_db=vector_db, embedder=ChunkEmbedder())
    second_total = seed_chunks(chunks, vector_db=vector_db, embedder=ChunkEmbedder())

    assert first_total == 2
    assert second_total == 2
    assert vector_db.collection_initialized is True
    assert vector_db.count() == 2
