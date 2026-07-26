"""
Unit tests for runtime fallbacks and corpus indexing helpers.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from pokemon_tcg_rag.api import runtime as api_runtime
from pokemon_tcg_rag.config.settings import Settings
from pokemon_tcg_rag.domain.exceptions import IngestionError
from pokemon_tcg_rag.domain.models import (
    Chunk,
    DocumentMetadata,
    DocumentSource,
    FeedbackRecord,
    RetrievedChunk,
    RuleType,
)
from pokemon_tcg_rag.storage import indexing as indexing_module
from pokemon_tcg_rag.storage.indexing import (
    ChunkEmbedder,
    CorpusManifest,
    CorpusManifestFile,
    load_chunks,
    load_corpus_manifest,
    seed_chunks,
)


def _metadata() -> DocumentMetadata:
    return DocumentMetadata(
        source=DocumentSource.RULEBOOK_PDF,
        document_title="Rulebook",
        page_number=12,
        card_name="Rare Candy",
        rule_type=RuleType.GENERAL_RULE,
    )


def _chunk(text: str = "Rare Candy lets you evolve faster.") -> Chunk:
    return Chunk(
        chunk_id="chunk-1",
        doc_id="doc-1",
        text=text,
        token_count=len(text.split()),
        metadata=_metadata(),
    )


def _retrieved(text: str = "Rare Candy lets you evolve faster.") -> RetrievedChunk:
    return RetrievedChunk(
        chunk=_chunk(text),
        score=0.9,
        retrieval_method="dense",
    )


@pytest.fixture(autouse=True)
def _reset_runtime_state() -> None:
    api_runtime.load_chunks = load_chunks
    api_runtime.load_corpus_manifest = load_corpus_manifest


def test_offline_runtime_clients_cover_fallback_behaviour() -> None:
    rewriter = api_runtime.OfflineQueryRewriterClient()
    answerer = api_runtime.OfflineAnswerClient()

    assert rewriter.generate_answer("Original question: Can I use Rare Candy?") == (
        "Can I use Rare Candy?"
    )
    assert rewriter.generate_answer("plain prompt") == "plain prompt"

    assert answerer.generate_answer("Question without context") == "I don't know."
    assert (
        answerer.generate_answer("Contexto:\n[1] Demo Reference\n\nPergunta:\n?")
        == "Com base no contexto recuperado: [1] Demo Reference"
    )
    assert (
        answerer.generate_answer(
            "Contexto:\n[1] Demo Reference\nRare Candy lets you evolve.\n\nPergunta:\n?"
        )
        == "Com base em [1] Demo Reference, Rare Candy lets you evolve."
    )


def test_offline_storage_and_runtime_container_close() -> None:
    vector_db = api_runtime.OfflineVectorDatabase("pokemon")
    vector_db.init_collection(metadata={"corpus_id": "demo"})
    assert vector_db.search_dense([0.1, 0.2], top_k=5) == []
    vector_db.upsert_chunks([_chunk()])

    dense = api_runtime.OfflineDenseRetriever(vector_db)
    assert dense.retrieve("Rare Candy") == []

    store = api_runtime.OfflineFeedbackStore()
    record = store.submit_feedback(
        query_id="qid-1",
        query="Can I use Rare Candy?",
        answer="Yes.",
        rating=1,
        comment=None,
        model_name="offline-llm",
        latency=0.1,
    )
    assert isinstance(record, FeedbackRecord)
    assert len(store.records) == 1
    assert store.close() is None

    disposed = {"called": False}

    class Engine:
        def dispose(self) -> None:
            disposed["called"] = True

    container = api_runtime.RuntimeContainer(
        settings=Settings(),
        vector_db=vector_db,
        relational_db=SimpleNamespace(engine=Engine()),
        dense_retriever=dense,
        bm25_retriever=SimpleNamespace(),
        retrieval_pipeline=SimpleNamespace(),
        feedback_store=store,
        rag_chain=SimpleNamespace(),
    )
    container.close()
    assert disposed["called"] is True


def test_manifest_helpers_and_directory_loading(tmp_path: Path) -> None:
    record = {
        "chunk_id": "chunk-1",
        "doc_id": "doc-1",
        "text": "Rare Candy lets you evolve faster.",
        "token_count": 6,
        "source": DocumentSource.RULEBOOK_PDF.value,
        "document_title": "Rulebook",
        "page_number": 12,
        "card_name": "Rare Candy",
        "rule_type": RuleType.GENERAL_RULE.value,
    }
    chunk_path = tmp_path / "corpus.jsonl"
    chunk_path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    digest = hashlib.sha256(chunk_path.read_bytes()).hexdigest()
    manifest = {
        "corpus_id": "demo-corpus",
        "version": "2026-07-24",
        "description": "demo",
        "chunk_count": 1,
        "files": [
            {
                "path": "corpus.jsonl",
                "sha256": digest,
                "chunk_count": 1,
            }
        ],
    }
    (tmp_path / "corpus_manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )

    loaded_manifest = load_corpus_manifest(tmp_path)
    assert loaded_manifest is not None
    assert loaded_manifest.corpus_id == "demo-corpus"
    assert loaded_manifest.chunk_count() == 1
    assert loaded_manifest.to_collection_metadata()["corpus_chunk_count"] == 1

    chunks = load_chunks(tmp_path)
    assert len(chunks) == 1
    assert chunks[0].document_id == "doc-1"
    assert chunks[0].metadata.source == DocumentSource.RULEBOOK_PDF

    manifest_file = CorpusManifestFile(
        path="corpus.jsonl",
        sha256=digest,
        chunk_count=1,
    )
    reconstructed = CorpusManifest.from_dict(manifest)
    assert reconstructed.files == (manifest_file,)
    assert reconstructed.manifest_sha256() == loaded_manifest.manifest_sha256()


def test_manifest_loading_rejects_bad_hash_and_count(tmp_path: Path) -> None:
    chunk_path = tmp_path / "corpus.jsonl"
    chunk_path.write_text(
        json.dumps(
            {
                "chunk_id": "chunk-1",
                "doc_id": "doc-1",
                "text": "Rare Candy",
                "token_count": 2,
                "source": DocumentSource.RULEBOOK_PDF.value,
                "document_title": "Rulebook",
                "rule_type": RuleType.GENERAL_RULE.value,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    bad_manifest = {
        "corpus_id": "demo-corpus",
        "version": "2026-07-24",
        "description": "demo",
        "chunk_count": 2,
        "files": [
            {
                "path": "corpus.jsonl",
                "sha256": "bad",
                "chunk_count": 1,
            }
        ],
    }
    (tmp_path / "corpus_manifest.json").write_text(
        json.dumps(bad_manifest), encoding="utf-8"
    )

    with pytest.raises(IngestionError):
        load_chunks(tmp_path)

    count_dir = tmp_path / "count"
    count_dir.mkdir()
    count_chunk = count_dir / "corpus.jsonl"
    count_chunk.write_text(chunk_path.read_text(encoding="utf-8"), encoding="utf-8")
    count_digest = hashlib.sha256(count_chunk.read_bytes()).hexdigest()
    (count_dir / "corpus_manifest.json").write_text(
        json.dumps(
            {
                "corpus_id": "demo-corpus",
                "version": "2026-07-24",
                "description": "demo",
                "chunk_count": 2,
                "files": [
                    {
                        "path": "corpus.jsonl",
                        "sha256": count_digest,
                        "chunk_count": 1,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(IngestionError):
        load_chunks(count_dir)


def test_manifest_helpers_handle_missing_paths(tmp_path: Path) -> None:
    missing_dir = tmp_path / "missing"
    assert load_chunks(missing_dir) == []

    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    assert load_corpus_manifest(empty_dir) is None


def test_manifest_derived_count_and_missing_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = CorpusManifest.from_dict(
        {
            "corpus_id": "demo-corpus",
            "version": "2026-07-24",
            "description": "demo",
            "files": [
                {"path": "a.jsonl", "sha256": "aaa", "chunk_count": 2},
                {"path": "b.jsonl", "sha256": "bbb", "chunk_count": 3},
            ],
        }
    )
    assert manifest.expected_chunk_count is None
    assert manifest.chunk_count() == 5
    assert manifest.source_hash()
    assert load_corpus_manifest(tmp_path / "missing") is None

    monkeypatch.setattr(indexing_module, "SentenceTransformer", None)
    with pytest.raises(IngestionError):
        ChunkEmbedder()


def test_load_chunks_without_manifest_and_parquet_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    jsonl_path = tmp_path / "plain.jsonl"
    jsonl_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "chunk_id": "chunk-1",
                        "doc_id": "doc-1",
                        "text": "Rare Candy lets you evolve faster.",
                        "token_count": 6,
                        "source": DocumentSource.RULEBOOK_PDF.value,
                        "document_title": "Rulebook",
                        "page_number": "12",
                        "rule_type": RuleType.GENERAL_RULE.value,
                    }
                ),
                "",
            ]
        ),
        encoding="utf-8",
    )
    unsupported = tmp_path / "notes.txt"
    unsupported.write_text("ignore", encoding="utf-8")

    chunks = load_chunks(tmp_path)
    assert len(chunks) == 1
    assert chunks[0].metadata.page_number == 12

    class FakeFrame:
        def to_dict(self, orient: str) -> list[dict[str, object]]:
            return [
                {
                    "chunk_id": "chunk-2",
                    "doc_id": "doc-2",
                    "text": "Stage 2 evolution",
                    "token_count": 3,
                    "source": DocumentSource.RULEBOOK_PDF.value,
                    "document_title": "Rulebook",
                    "page_number": "7",
                    "rule_type": RuleType.GENERAL_RULE.value,
                }
            ]

    fake_parquet = tmp_path / "records.parquet"
    fake_parquet.write_text("placeholder", encoding="utf-8")
    monkeypatch.setattr(indexing_module.pd, "read_parquet", lambda path: FakeFrame())
    parquet_chunks = indexing_module._load_chunks_from_path(fake_parquet)
    assert parquet_chunks[0].metadata.page_number == 7


def test_seed_helpers_and_parser_main(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    chunk = _chunk("Rare Candy lets you evolve faster.")
    assert seed_chunks([], vector_db=api_runtime.OfflineVectorDatabase("pokemon")) == 0

    seed_calls: list[tuple[object, object]] = []

    def fake_load_chunks(_chunks_dir: str | Path | None = None) -> list[Chunk]:
        return [chunk]

    def fake_seed_chunks(
        chunks: list[Chunk],
        *,
        vector_db: object | None = None,
        embedder: object | None = None,
        batch_size: int = 32,
        collection_metadata: dict[str, object] | None = None,
    ) -> int:
        seed_calls.append((vector_db, embedder))
        return len(chunks)

    monkeypatch.setattr(indexing_module, "load_chunks", fake_load_chunks)
    monkeypatch.setattr(indexing_module, "seed_chunks", fake_seed_chunks)
    assert (
        indexing_module.seed_from_directory(
            tmp_path,
            vector_db=SimpleNamespace(name="vector"),
            embedder=SimpleNamespace(name="embedder"),
            batch_size=4,
        )
        == 1
    )
    assert seed_calls == [
        (SimpleNamespace(name="vector"), SimpleNamespace(name="embedder"))
    ]

    parser = indexing_module.build_parser()
    args = parser.parse_args(["--chunks-dir", str(tmp_path), "--batch-size", "8"])
    assert args.chunks_dir == tmp_path
    assert args.batch_size == 8

    monkeypatch.setattr(indexing_module, "setup_logging", lambda: None)
    monkeypatch.setattr(
        indexing_module, "seed_from_directory", lambda *args, **kwargs: 2
    )
    assert indexing_module.main([]) == 0
    assert "Seeded 2 chunks into Qdrant." in capsys.readouterr().out


def test_chunk_embedder_and_seed_chunks() -> None:
    class FakeModel:
        def encode(
            self,
            texts: list[str],
            batch_size: int,
            show_progress_bar: bool,
            convert_to_numpy: bool,
            normalize_embeddings: bool,
        ) -> list[SimpleNamespace]:
            return [
                SimpleNamespace(
                    tolist=lambda index=index, text=text: [
                        float(index),
                        float(len(text)),
                    ]
                )
                for index, text in enumerate(texts)
            ]

    class FakeVectorDatabase:
        def __init__(self) -> None:
            self.collections: list[dict[str, object] | None] = []
            self.upserts: list[list[Chunk]] = []

        def init_collection(self, metadata: dict[str, object] | None = None) -> None:
            self.collections.append(metadata)

        def upsert_chunks(self, chunks: list[Chunk]) -> None:
            self.upserts.append(chunks)

    embedder = ChunkEmbedder(model=FakeModel())
    vectors = embedder.embed_texts(["Rare Candy", "Stage 2"], batch_size=2)
    assert vectors == [[0.0, 10.0], [1.0, 7.0]]

    vector_db = FakeVectorDatabase()
    chunks = [_chunk("Rare Candy"), _chunk("Stage 2 evolution")]
    seeded = seed_chunks(
        chunks,
        vector_db=vector_db,
        embedder=embedder,
        batch_size=2,
        collection_metadata={"corpus_id": "demo"},
    )

    assert seeded == 2
    assert vector_db.collections == [{"corpus_id": "demo"}]
    assert len(vector_db.upserts) == 1
    assert vector_db.upserts[0][0].embedding == [0.0, 10.0]
