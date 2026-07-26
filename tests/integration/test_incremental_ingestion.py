"""
TASK-074 — Incremental manifest-driven ingestion tests.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pokemon_tcg_rag.domain.models import (
    Document,
    DocumentMetadata,
    DocumentSource,
    RuleType,
)
from pokemon_tcg_rag.ingestion.pipeline import IngestionPipeline


def _doc(doc_id: str, content: str, source: DocumentSource) -> Document:
    return Document(
        doc_id=doc_id,
        content=content,
        metadata=DocumentMetadata(
            source=source,
            document_title=f"{source.value} title",
            rule_type=RuleType.GENERAL_RULE,
            source_url=f"https://example.com/{doc_id}",
        ),
    )


@pytest.mark.integration
def test_incremental_manifest_tracks_diffs(tmp_path: Path) -> None:
    pipeline = IngestionPipeline(
        raw_data_dir=tmp_path / "raw",
        processed_dir=tmp_path / "processed",
        chunks_dir=tmp_path / "chunks",
    )
    documents = [_doc("doc-1", "one", DocumentSource.RULEBOOK_PDF)]
    chunks = pipeline._chunk_documents(documents)

    state = pipeline._build_ingestion_state(documents, chunks)
    diff = pipeline._diff_ingestion_state(state)
    pipeline._persist_ingestion_state(state, diff)

    manifest_path = tmp_path / "processed" / "ingestion_manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["documents"]["doc-1"]["checksum"]
    assert payload["diff"]["added"] == ["doc-1"]

    same_diff = pipeline._diff_ingestion_state(state)
    assert same_diff == {"added": [], "updated": [], "deleted": []}

    updated_state = dict(state)
    updated_state["doc-1"] = dict(updated_state["doc-1"], checksum="changed")
    changed_diff = pipeline._diff_ingestion_state(updated_state)
    assert changed_diff["updated"] == ["doc-1"]
