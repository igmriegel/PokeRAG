"""
TASK-010 — TEST-029, TEST-030, TEST-031

Integration tests for the ingestion orchestrator.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from pokemon_tcg_rag.domain.models import Document, DocumentMetadata, DocumentSource, RuleType
from pokemon_tcg_rag.ingestion.pipeline import IngestionPipeline


def _build_document(
    doc_id: str,
    content: str,
    source: DocumentSource,
    rule_type: RuleType,
) -> Document:
    return Document(
        doc_id=doc_id,
        content=content,
        metadata=DocumentMetadata(
            source=source,
            document_title=f"{source.value} title",
            rule_type=rule_type,
        ),
    )


@pytest.mark.integration
def test_pipeline_aggregates_all_sources(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """TEST-029: pipeline must aggregate docs from Pokegym, HTML, and PDF sources."""

    def fake_fetch_all_rulings(self: object) -> list[Document]:
        return [
            _build_document(
                "pokegym_1",
                "Question: Can I use Rare Candy?\nAnswer: Yes.",
                DocumentSource.POKEGYM,
                RuleType.RULING,
            )
        ]

    def fake_fetch_all_html_pages(self: object) -> list[Document]:
        return [
            _build_document(
                "html_ban",
                "Ban list content",
                DocumentSource.BAN_LIST_HTML,
                RuleType.BAN_STATUS,
            ),
            _build_document(
                "html_promo",
                "Promo legality content",
                DocumentSource.PROMO_LEGALITY_HTML,
                RuleType.PROMO_STATUS,
            ),
            _build_document(
                "html_mega",
                "Mega rules content",
                DocumentSource.MEGA_RULES_HTML,
                RuleType.MECHANIC_RULE,
            ),
        ]

    def fake_download_pdf(self: object, url: str) -> Path:
        pdf_path = tmp_path / "raw" / "pdfs" / f"{Path(url).stem}.pdf"
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(b"%PDF-1.4 fake pdf")
        return pdf_path

    def fake_parse_pdf_file(
        self: object,
        file_path: str | Path,
        source: DocumentSource,
        rule_type: RuleType,
    ) -> list[Document]:
        return [
            _build_document(
                f"{source.value}_1",
                f"{source.value} content",
                source,
                rule_type,
            )
        ]

    monkeypatch.setattr(
        "pokemon_tcg_rag.ingestion.pipeline.PokegymCrawler.fetch_all_rulings",
        fake_fetch_all_rulings,
    )
    monkeypatch.setattr(
        "pokemon_tcg_rag.ingestion.pipeline.HTMLPageScraper.fetch_all_html_pages",
        fake_fetch_all_html_pages,
    )
    monkeypatch.setattr("pokemon_tcg_rag.ingestion.pipeline.IngestionPipeline._download_pdf", fake_download_pdf)
    monkeypatch.setattr("pokemon_tcg_rag.ingestion.pipeline.PDFParser.parse_pdf_file", fake_parse_pdf_file)

    pipeline = IngestionPipeline(raw_data_dir=tmp_path / "raw", processed_dir=tmp_path / "processed")
    documents = pipeline.run()

    assert len(documents) == 9
    assert {document.metadata.source for document in documents} == {
        DocumentSource.POKEGYM,
        DocumentSource.BAN_LIST_HTML,
        DocumentSource.PROMO_LEGALITY_HTML,
        DocumentSource.MEGA_RULES_HTML,
        DocumentSource.RULEBOOK_PDF,
        DocumentSource.TOURNAMENT_HANDBOOK_PDF,
        DocumentSource.ALT_PLAY_HANDBOOK_PDF,
        DocumentSource.ERRATA_PDF,
        DocumentSource.DECK_LIST_GUIDE_PDF,
    }


@pytest.mark.integration
def test_download_dedup_by_checksum(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """TEST-030: downloading the same PDF bytes twice should deduplicate by checksum."""

    class DummyResponse:
        content = b"%PDF-1.4 identical content"

        @staticmethod
        def raise_for_status() -> None:
            return None

    monkeypatch.setattr("pokemon_tcg_rag.ingestion.pipeline.requests.get", lambda *args, **kwargs: DummyResponse())

    pipeline = IngestionPipeline(raw_data_dir=tmp_path / "raw", processed_dir=tmp_path / "processed")
    pdf_url = "https://example.com/rules.pdf"

    first_path = pipeline._download_pdf(pdf_url)
    second_path = pipeline._download_pdf(pdf_url)

    expected_checksum = hashlib.sha256(DummyResponse.content).hexdigest()[:12]
    assert first_path == second_path
    assert first_path.exists()
    assert expected_checksum in first_path.name
    assert len(list((tmp_path / "raw" / "pdfs").glob("*.pdf"))) == 1


@pytest.mark.integration
def test_processed_persistence_written(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """TEST-031: processed JSONL and Parquet artifacts must be written."""

    def fake_fetch_all_rulings(self: object) -> list[Document]:
        return [
            _build_document(
                "pokegym_1",
                "Question: Can I use Rare Candy?\nAnswer: Yes.",
                DocumentSource.POKEGYM,
                RuleType.RULING,
            )
        ]

    monkeypatch.setattr(
        "pokemon_tcg_rag.ingestion.pipeline.PokegymCrawler.fetch_all_rulings",
        fake_fetch_all_rulings,
    )
    monkeypatch.setattr(
        "pokemon_tcg_rag.ingestion.pipeline.HTMLPageScraper.fetch_all_html_pages",
        lambda self: [],
    )
    monkeypatch.setattr(
        "pokemon_tcg_rag.ingestion.pipeline.IngestionPipeline._download_pdf",
        lambda self, url: tmp_path / "raw" / "pdfs" / "dummy.pdf",
    )
    monkeypatch.setattr(
        "pokemon_tcg_rag.ingestion.pipeline.PDFParser.parse_pdf_file",
        lambda self, file_path, source, rule_type: [],
    )

    pipeline = IngestionPipeline(raw_data_dir=tmp_path / "raw", processed_dir=tmp_path / "processed")
    pipeline.run(sources=["pokegym"])

    assert (tmp_path / "processed" / "documents.jsonl").exists()
    assert (tmp_path / "processed" / "documents.parquet").exists()
