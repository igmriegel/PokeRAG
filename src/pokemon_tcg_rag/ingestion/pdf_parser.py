"""
PyMuPDF / PyMuPDF4LLM PDF document parser.

Extracts page-level documents from the official Pokemon TCG PDFs while preserving page numbers,
basic section titles, and source metadata for downstream ingestion.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import fitz
import pymupdf4llm

from pokemon_tcg_rag.domain.exceptions import ParsingError
from pokemon_tcg_rag.domain.models import Document, DocumentMetadata, DocumentSource, RuleType
from pokemon_tcg_rag.monitoring.logger import get_logger

LOGGER = get_logger(__name__)


class PDFParser:
    """Extract structured text from official Pokemon TCG PDF files."""

    PDF_SOURCES = {
        "rulebook": (
            "https://www.pokemon.com/static-assets/content-assets/cms2/pdf/trading-card-game/rulebook/cri_rulebook_en.pdf",
            DocumentSource.RULEBOOK_PDF,
            RuleType.GENERAL_RULE,
        ),
        "tournament_handbook": (
            "https://www.pokemon.com/static-assets/content-assets/cms2/pdf/play-pokemon/rules/play-pokemon-tcg-tournament-handbook-en.pdf",
            DocumentSource.TOURNAMENT_HANDBOOK_PDF,
            RuleType.TOURNAMENT_RULE,
        ),
        "alt_play": (
            "https://www.pokemon.com/static-assets/content-assets/cms2/pdf/trading-card-game/tcg-alternative-play-handbook-en.pdf",
            DocumentSource.ALT_PLAY_HANDBOOK_PDF,
            RuleType.GENERAL_RULE,
        ),
        "errata": (
            "https://www.pokemon.com/static-assets/content-assets/cms2/pdf/trading-card-game/tcg_errata.pdf",
            DocumentSource.ERRATA_PDF,
            RuleType.ERRATA,
        ),
        "deck_list_guide": (
            "https://www.pokemon.com/static-assets/content-assets/cms2/pdf/play-pokemon/rules/play-pokemon-deck-list-85x11.pdf",
            DocumentSource.DECK_LIST_GUIDE_PDF,
            RuleType.TOURNAMENT_RULE,
        ),
    }

    def parse_pdf_file(
        self,
        file_path: str | Path,
        source: DocumentSource,
        rule_type: RuleType,
    ) -> list[Document]:
        """Parse a local PDF file into page-level ``Document`` objects."""
        path = Path(file_path)
        if not path.exists():
            raise ParsingError(f"PDF file not found: {path}")

        try:
            with fitz.open(path) as pdf_doc:
                markdown_text = self._render_markdown(path)
                documents: list[Document] = []
                for page_number in range(pdf_doc.page_count):
                    page = pdf_doc.load_page(page_number)
                    page_text = page.get_text("text").strip()
                    if not page_text:
                        continue

                    section_title = self._extract_section_title(page_text, markdown_text)
                    document = Document(
                        doc_id=f"{path.stem}_p{page_number + 1}",
                        content=page_text,
                        metadata=DocumentMetadata(
                            source=source,
                            document_title=self._document_title_for(path, source),
                            page_number=page_number + 1,
                            section_title=section_title,
                            rule_type=rule_type,
                            checksum=self._checksum(page_text),
                        ),
                    )
                    documents.append(document)
        except ParsingError:
            raise
        except Exception as exc:  # pragma: no cover - defensive wrapper
            raise ParsingError(f"Failed to parse PDF {path}: {exc}") from exc

        if not documents:
            raise ParsingError(f"No readable content extracted from PDF {path}")

        LOGGER.info("pdf_parsed", file_path=str(path), pages=len(documents))
        return documents

    def _render_markdown(self, path: Path) -> str:
        try:
            rendered = pymupdf4llm.to_markdown(str(path))
        except Exception:  # pragma: no cover - optional extraction path
            return ""
        return rendered if isinstance(rendered, str) else ""

    def _extract_section_title(self, page_text: str, markdown_text: str) -> str | None:
        for candidate in (page_text, markdown_text):
            if not candidate:
                continue
            for line in candidate.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                header_match = re.match(r"^#{1,6}\s+(.+)$", stripped)
                if header_match:
                    return header_match.group(1).strip()
                if stripped.endswith(":") and len(stripped.split()) <= 12:
                    return stripped[:-1].strip()
                if stripped.isupper() and len(stripped) > 4:
                    return stripped.title()
                return stripped
        return None

    def _document_title_for(self, path: Path, source: DocumentSource) -> str:
        title_map = {
            DocumentSource.RULEBOOK_PDF: "Official Rulebook",
            DocumentSource.TOURNAMENT_HANDBOOK_PDF: "Tournament Handbook",
            DocumentSource.ALT_PLAY_HANDBOOK_PDF: "Alternative Play Handbook",
            DocumentSource.ERRATA_PDF: "TCG Errata",
            DocumentSource.DECK_LIST_GUIDE_PDF: "Deck List Guide",
        }
        return title_map.get(source, path.stem.replace("_", " ").title())

    def _checksum(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
