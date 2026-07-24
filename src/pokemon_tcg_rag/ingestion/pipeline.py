"""
Ingestion pipeline coordinator.

Downloads the official source PDFs, runs the Pokegym crawler, HTML scraper, and PDF parser,
then persists processed documents and chunks for downstream normalization/chunking/indexing tasks.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

from pokemon_tcg_rag.config.settings import get_settings
from pokemon_tcg_rag.domain.exceptions import IngestionError
from pokemon_tcg_rag.domain.models import Chunk, Document
from pokemon_tcg_rag.ingestion.chunker import DocumentChunker
from pokemon_tcg_rag.ingestion.crawler_pokegym import PokegymCrawler
from pokemon_tcg_rag.ingestion.html_scraper import HTMLPageScraper
from pokemon_tcg_rag.ingestion.normalizer import DocumentNormalizer
from pokemon_tcg_rag.ingestion.pdf_parser import PDFParser
from pokemon_tcg_rag.ingestion.trust_boundary import download_trusted_bytes
from pokemon_tcg_rag.monitoring.logger import get_logger
from pokemon_tcg_rag.storage.indexing import seed_chunks

LOGGER = get_logger(__name__)


class IngestionPipeline:
    """Orchestrate ingestion across Pokegym, HTML pages, and official PDFs."""

    def __init__(
        self,
        raw_data_dir: str | Path | None = None,
        processed_dir: str | Path | None = None,
        chunks_dir: str | Path | None = None,
    ) -> None:
        settings = get_settings()
        self.raw_data_dir = Path(raw_data_dir or settings.DATA_RAW_DIR)
        self.processed_dir = Path(processed_dir or settings.DATA_PROCESSED_DIR)
        self.chunks_dir = Path(chunks_dir or settings.DATA_CHUNKS_DIR)
        self.quarantine_dir = self.raw_data_dir / "quarantine"
        self.pdf_dir = self.raw_data_dir / "pdfs"
        self.crawler = PokegymCrawler(
            raw_html_dir=self.raw_data_dir / "html",
            raw_json_dir=self.raw_data_dir / "json",
            quarantine_dir=self.quarantine_dir,
        )
        self.html_scraper = HTMLPageScraper(
            raw_output_dir=self.raw_data_dir / "html",
            quarantine_dir=self.quarantine_dir,
        )
        self.pdf_parser = PDFParser()
        self.normalizer = DocumentNormalizer()
        self.chunker = DocumentChunker()

    def run(
        self,
        sources: Iterable[str] | None = None,
        index: bool = False,
    ) -> list[Document] | list[Chunk]:
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

        if errors:
            raise IngestionError("; ".join(errors))

        normalized_documents = [self.normalizer.normalize(document) for document in documents]
        chunks = self._chunk_documents(normalized_documents)

        self._persist_processed_documents(normalized_documents)
        self._persist_chunk_documents(chunks)
        self._persist_provenance_manifest(normalized_documents)
        self._log_source_counts(normalized_documents)

        if index:
            seed_chunks(chunks)
            LOGGER.info(
                "ingestion_finished",
                documents=len(normalized_documents),
                chunks=len(chunks),
                indexed=True,
            )
            return chunks

        LOGGER.info(
            "ingestion_finished",
            documents=len(normalized_documents),
            chunks=len(chunks),
            indexed=False,
        )
        return normalized_documents

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
        content, _ = download_trusted_bytes(
            url,
            max_bytes=25_000_000,
            timeout=60,
            user_agent="PokemonTCGRAG/1.0 (+https://github.com/igmriegel/PokeRAG)",
            allowed_content_types=("application/pdf", "application/octet-stream"),
        )
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
        if flattened_records:
            pd.DataFrame(flattened_records).to_parquet(parquet_path, index=False)
        else:
            pd.DataFrame(columns=self._document_columns()).to_parquet(parquet_path, index=False)

    def _persist_chunk_documents(self, chunks: list[Chunk]) -> None:
        self.chunks_dir.mkdir(parents=True, exist_ok=True)
        parquet_path = self.chunks_dir / "chunks.parquet"
        flattened_records = [self._flatten_chunk(chunk) for chunk in chunks]
        if flattened_records:
            pd.DataFrame(flattened_records).to_parquet(parquet_path, index=False)
        else:
            pd.DataFrame(columns=self._chunk_columns()).to_parquet(parquet_path, index=False)

    def _persist_provenance_manifest(self, documents: list[Document]) -> None:
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = self.processed_dir / "provenance.jsonl"
        with manifest_path.open("w", encoding="utf-8") as fh:
            for document in documents:
                payload = {
                    "doc_id": document.doc_id,
                    "source": document.metadata.source.value,
                    "source_url": document.metadata.source_url,
                    "checksum": document.metadata.checksum
                    or hashlib.sha256(document.content.encode("utf-8")).hexdigest(),
                    "parser_version": self._parser_version(document),
                    "retrieved_at": document.created_at.isoformat(),
                }
                fh.write(json.dumps(payload, ensure_ascii=False))
                fh.write("\n")

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

    def _flatten_chunk(self, chunk: Chunk) -> dict[str, object]:
        return {
            "chunk_id": chunk.chunk_id,
            "doc_id": chunk.doc_id,
            "text": chunk.text,
            "token_count": chunk.token_count,
            "source": chunk.metadata.source.value,
            "document_title": chunk.metadata.document_title,
            "page_number": chunk.metadata.page_number,
            "section_title": chunk.metadata.section_title,
            "card_name": chunk.metadata.card_name,
            "rule_type": chunk.metadata.rule_type.value,
            "publication_date": chunk.metadata.publication_date,
            "source_url": chunk.metadata.source_url,
            "checksum": chunk.metadata.checksum,
        }

    def _document_columns(self) -> list[str]:
        return [
            "doc_id",
            "content",
            "created_at",
            "source",
            "document_title",
            "page_number",
            "section_title",
            "card_name",
            "rule_type",
            "publication_date",
            "source_url",
            "checksum",
        ]

    def _chunk_columns(self) -> list[str]:
        return [
            "chunk_id",
            "doc_id",
            "text",
            "token_count",
            "source",
            "document_title",
            "page_number",
            "section_title",
            "card_name",
            "rule_type",
            "publication_date",
            "source_url",
            "checksum",
        ]

    def _log_source_counts(self, documents: list[Document]) -> None:
        counts = Counter(document.metadata.source.value for document in documents)
        LOGGER.info("ingestion_document_counts", **dict(counts), total=len(documents))

    def _chunk_documents(self, documents: list[Document]) -> list[Chunk]:
        chunks: list[Chunk] = []
        for document in documents:
            chunks.extend(self.chunker.chunk_document(document))
        return chunks

    def _parser_version(self, document: Document) -> str:
        source = document.metadata.source.value
        if source in {"pokegym"}:
            return getattr(self.crawler, "PARSER_VERSION", "pokegym-crawler")
        if source in {"ban_list_html", "promo_legality_html", "mega_rules_html"}:
            return getattr(self.html_scraper, "PARSER_VERSION", "html-scraper")
        return getattr(self.pdf_parser, "PARSER_VERSION", "pdf-parser")
