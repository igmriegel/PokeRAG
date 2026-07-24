"""
Ingestion pipeline coordinator.

Downloads the official source PDFs, runs the Pokegym crawler, HTML scraper, and PDF parser,
then persists a processed Document corpus for downstream normalization/chunking tasks.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests

from pokemon_tcg_rag.config.settings import get_settings
from pokemon_tcg_rag.domain.exceptions import IngestionError
from pokemon_tcg_rag.domain.models import Document
from pokemon_tcg_rag.ingestion.crawler_pokegym import PokegymCrawler
from pokemon_tcg_rag.ingestion.html_scraper import HTMLPageScraper
from pokemon_tcg_rag.ingestion.pdf_parser import PDFParser
from pokemon_tcg_rag.monitoring.logger import get_logger

LOGGER = get_logger(__name__)


class IngestionPipeline:
    """Orchestrate ingestion across Pokegym, HTML pages, and official PDFs."""

    def __init__(
        self,
        raw_data_dir: str | Path | None = None,
        processed_dir: str | Path | None = None,
    ) -> None:
        settings = get_settings()
        self.raw_data_dir = Path(raw_data_dir or settings.DATA_RAW_DIR)
        self.processed_dir = Path(processed_dir or settings.DATA_PROCESSED_DIR)
        self.pdf_dir = self.raw_data_dir / "pdfs"
        self.crawler = PokegymCrawler(raw_html_dir=self.raw_data_dir / "html", raw_json_dir=self.raw_data_dir / "json")
        self.html_scraper = HTMLPageScraper(raw_output_dir=self.raw_data_dir / "html")
        self.pdf_parser = PDFParser()

    def run(self, sources: Iterable[str] | None = None) -> list[Document]:
        """
        Run the configured ingestion sources and persist processed artifacts.

        ``sources`` may be used to limit execution to ``pokegym``, ``html``, ``pdf``,
        or any comma-separated combination of those family names.
        """
        selected = self._normalize_sources(sources)
        documents: list[Document] = []
        errors: list[str] = []

        LOGGER.info("ingestion_started", sources=sorted(selected))

        if "pokegym" in selected:
            try:
                documents.extend(self.crawler.fetch_all_rulings())
            except IngestionError as exc:
                errors.append(str(exc))

        if "html" in selected:
            try:
                documents.extend(self.html_scraper.fetch_all_html_pages())
            except IngestionError as exc:
                errors.append(str(exc))

        if "pdf" in selected:
            try:
                documents.extend(self._collect_pdf_documents())
            except IngestionError as exc:
                errors.append(str(exc))

        self._persist_processed_documents(documents)
        self._log_source_counts(documents)

        if errors:
            raise IngestionError("; ".join(errors))

        LOGGER.info("ingestion_finished", documents=len(documents))
        return documents

    def _normalize_sources(self, sources: Iterable[str] | None) -> set[str]:
        if not sources:
            return {"pokegym", "html", "pdf"}

        normalized: set[str] = set()
        for item in sources:
            for token in str(item).split(","):
                cleaned = token.strip().lower()
                if cleaned:
                    normalized.add(cleaned)
        if not normalized:
            return {"pokegym", "html", "pdf"}
        return normalized

    def _collect_pdf_documents(self) -> list[Document]:
        documents: list[Document] = []
        for _, (url, source, rule_type) in self.pdf_parser.PDF_SOURCES.items():
            pdf_path = self._download_pdf(url)
            documents.extend(self.pdf_parser.parse_pdf_file(pdf_path, source, rule_type))
        return documents

    def _download_pdf(self, url: str) -> Path:
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        response = requests.get(
            url,
            timeout=60,
            headers={
                "User-Agent": "PokemonTCGRAG/1.0 (+https://github.com/igmriegel/PokeRAG)",
            },
        )
        response.raise_for_status()

        content = response.content
        checksum = hashlib.sha256(content).hexdigest()
        filename = f"{Path(urlparse(url).path).stem}_{checksum[:12]}.pdf"
        pdf_path = self.pdf_dir / filename
        if not pdf_path.exists():
            pdf_path.write_bytes(content)
        return pdf_path

    def _persist_processed_documents(self, documents: list[Document]) -> None:
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        jsonl_path = self.processed_dir / "documents.jsonl"
        with jsonl_path.open("w", encoding="utf-8") as fh:
            for document in documents:
                fh.write(json.dumps(document.model_dump(mode="json"), ensure_ascii=False))
                fh.write("\n")

        parquet_path = self.processed_dir / "documents.parquet"
        flattened_records = [self._flatten_document(document) for document in documents]
        pd.DataFrame(flattened_records).to_parquet(parquet_path, index=False)

    def _flatten_document(self, document: Document) -> dict[str, object]:
        return {
            "doc_id": document.doc_id,
            "content": document.content,
            "created_at": document.created_at.isoformat(),
            "source": document.metadata.source.value,
            "document_title": document.metadata.document_title,
            "page_number": document.metadata.page_number,
            "section_title": document.metadata.section_title,
            "card_name": document.metadata.card_name,
            "rule_type": document.metadata.rule_type.value,
            "publication_date": document.metadata.publication_date,
            "source_url": document.metadata.source_url,
            "checksum": document.metadata.checksum,
        }

    def _log_source_counts(self, documents: list[Document]) -> None:
        counts = Counter(document.metadata.source.value for document in documents)
        LOGGER.info("ingestion_document_counts", **dict(counts), total=len(documents))
