"""
TASK-014 — TEST-044, TEST-045, TEST-046, TEST-047

Unit tests for the Qdrant vector database client.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from pokemon_tcg_rag.domain.exceptions import VectorStoreError
from pokemon_tcg_rag.domain.models import (
    Chunk,
    DocumentMetadata,
    DocumentSource,
    RuleType,
)
from pokemon_tcg_rag.storage.vector_db import VectorDatabase


class DummyClient:
    def __init__(self) -> None:
        self.created = False
        self.created_kwargs: dict[str, object] | None = None
        self.upserted = None
        self.upsert_calls: list[dict[str, object]] = []
        self.query_filter = None
        self.collection_metadata: dict[str, object] = {}
        self.points = [
            SimpleNamespace(
                id="chunk-1",
                score=0.99,
                payload={
                    "doc_id": "doc-1",
                    "text": "Rare Candy lets you evolve faster.",
                    "source": DocumentSource.RULEBOOK_PDF.value,
                    "document_title": "Rulebook",
                    "page_number": 10,
                    "section_title": "Setup",
                    "rule_type": RuleType.GENERAL_RULE.value,
                    "card_name": "Rare Candy",
                    "publication_date": "2026-07-24",
                    "source_url": "https://example.com/rulebook.pdf",
                    "checksum": "abc",
                },
            )
        ]

    def collection_exists(self, name: str) -> bool:
        return self.created

    def create_collection(self, *args, **kwargs) -> bool:
        self.created = True
        self.created_kwargs = kwargs
        metadata = kwargs.get("metadata")
        if isinstance(metadata, dict):
            self.collection_metadata = metadata
        return True

    def get_collection(self, name: str) -> SimpleNamespace:
        return SimpleNamespace(
            config=SimpleNamespace(metadata=self.collection_metadata),
        )

    def upsert(self, *args, **kwargs) -> SimpleNamespace:
        self.upserted = kwargs
        self.upsert_calls.append(kwargs)
        for point in kwargs.get("points", []):
            if point.payload.get("_record_type") == "collection_metadata":
                self.collection_metadata = point.payload["metadata"]
        return SimpleNamespace()

    def retrieve(self, *args, **kwargs) -> list[SimpleNamespace]:
        if not self.collection_metadata:
            return []
        return [
            SimpleNamespace(
                payload={
                    "_record_type": "collection_metadata",
                    "metadata": self.collection_metadata,
                }
            )
        ]

    def query_points(self, *args, **kwargs) -> SimpleNamespace:
        self.query_filter = kwargs.get("query_filter")
        return SimpleNamespace(points=self.points)


def _make_chunk(embedding: list[float] | None = None) -> Chunk:
    return Chunk(
        chunk_id="chunk-1",
        doc_id="doc-1",
        text="Rare Candy lets you evolve faster.",
        token_count=6,
        metadata=DocumentMetadata(
            source=DocumentSource.RULEBOOK_PDF,
            document_title="Rulebook",
            page_number=10,
            section_title="Setup",
            card_name="Rare Candy",
            rule_type=RuleType.GENERAL_RULE,
            publication_date="2026-07-24",
            source_url="https://example.com/rulebook.pdf",
            checksum="abc",
        ),
        embedding=embedding,
    )


@pytest.mark.unit
def test_init_collection_dim_1024() -> None:
    """TEST-044: collection must be initialized with the configured size and cosine distance."""
    client = DummyClient()
    db = VectorDatabase(client=client)  # type: ignore[arg-type]

    db.init_collection()

    assert client.created is True
    assert client.created_kwargs is not None
    assert "metadata" not in client.created_kwargs


@pytest.mark.unit
def test_init_collection_validates_manifest_metadata() -> None:
    """TASK-061: collection metadata must match the corpus manifest."""
    client = DummyClient()
    db = VectorDatabase(client=client)  # type: ignore[arg-type]
    metadata = {
        "corpus_id": "bootstrap-demo-corpus",
        "corpus_version": "2026-07-24",
        "corpus_manifest_sha256": "abc",
        "corpus_source_hash": "def",
        "corpus_chunk_count": 4,
    }

    db.init_collection(metadata=metadata)

    assert db.collection_metadata()["corpus_id"] == "bootstrap-demo-corpus"


@pytest.mark.unit
def test_init_collection_backfills_missing_manifest_metadata() -> None:
    """Existing pre-metadata collections should be upgraded in place."""
    client = DummyClient()
    client.created = True
    db = VectorDatabase(client=client)  # type: ignore[arg-type]

    db.init_collection(
        metadata={
            "corpus_id": "pokemon-tcg-official-corpus",
            "corpus_version": "2026-07-24",
        }
    )

    assert client.collection_metadata["corpus_id"] == "pokemon-tcg-official-corpus"


@pytest.mark.unit
def test_init_collection_rejects_manifest_mismatch() -> None:
    """TASK-061: a manifest mismatch must fail closed."""
    client = DummyClient()
    client.created = True
    client.collection_metadata = {
        "corpus_id": "other-corpus",
        "corpus_version": "2026-07-24",
    }
    db = VectorDatabase(client=client)  # type: ignore[arg-type]

    with pytest.raises(VectorStoreError):
        db.init_collection(
            metadata={
                "corpus_id": "bootstrap-demo-corpus",
                "corpus_version": "2026-07-24",
            }
        )


@pytest.mark.unit
def test_upsert_maps_payload() -> None:
    """TEST-045: chunk fields must be mapped into the Qdrant payload."""
    client = DummyClient()
    db = VectorDatabase(client=client)  # type: ignore[arg-type]
    chunk = _make_chunk(embedding=[0.1] * 1024)

    db.upsert_chunks([chunk])

    assert client.upserted is not None
    points = client.upserted["points"]
    assert points[0].payload["chunk_id"] == "chunk-1"
    assert points[0].payload["source"] == DocumentSource.RULEBOOK_PDF.value
    assert points[0].payload["rule_type"] == RuleType.GENERAL_RULE.value
    assert points[0].payload["page_number"] == 10


@pytest.mark.unit
def test_upsert_splits_large_corpora_into_batches() -> None:
    client = DummyClient()
    db = VectorDatabase(client=client)  # type: ignore[arg-type]
    chunks = [
        _make_chunk(embedding=[0.1] * 1024).model_copy(update={"chunk_id": f"chunk-{index}"})
        for index in range(130)
    ]

    db.upsert_chunks(chunks, batch_size=64)

    assert [len(call["points"]) for call in client.upsert_calls] == [64, 64, 2]


@pytest.mark.unit
def test_search_returns_retrieved_chunks() -> None:
    """TEST-046: query results must be mapped back into RetrievedChunk objects."""
    client = DummyClient()
    db = VectorDatabase(client=client)  # type: ignore[arg-type]

    results = db.search_dense([0.1] * 1024, top_k=1)

    assert len(results) == 1
    assert results[0].chunk.chunk_id == "chunk-1"
    assert results[0].chunk.metadata.source == DocumentSource.RULEBOOK_PDF
    assert results[0].score == pytest.approx(0.99)


@pytest.mark.unit
def test_search_error_raises() -> None:
    """TEST-047: client failures must raise VectorStoreError."""

    class BrokenClient(DummyClient):
        def query_points(self, *args, **kwargs) -> SimpleNamespace:
            raise RuntimeError("boom")

    db = VectorDatabase(client=BrokenClient())  # type: ignore[arg-type]

    with pytest.raises(VectorStoreError):
        db.search_dense([0.1] * 1024, top_k=1)
