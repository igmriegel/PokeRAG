"""
PyMuPDF / PyMuPDF4LLM PDF Document Parser.
"""

import logging
from pathlib import Path
import fitz  # PyMuPDF
import pymupdf4llm

from pokemon_tcg_rag.domain.models import Document, DocumentMetadata, DocumentSource, RuleType

logger = logging.getLogger(__name__)


class PDFParser:
    """Extracts structured text and layout markdown from official Pokemon TCG PDF files."""

    PDF_SOURCES = {
        "rulebook": ("https://www.pokemon.com/static-assets/content-assets/cms2/pdf/trading-card-game/rulebook/cri_rulebook_en.pdf", DocumentSource.RULEBOOK_PDF, RuleType.GENERAL_RULE),
        "tournament_handbook": ("https://www.pokemon.com/static-assets/content-assets/cms2/pdf/play-pokemon/rules/play-pokemon-tcg-tournament-handbook-en.pdf", DocumentSource.TOURNAMENT_HANDBOOK_PDF, RuleType.TOURNAMENT_RULE),
        "alt_play": ("https://www.pokemon.com/static-assets/content-assets/cms2/pdf/trading-card-game/tcg-alternative-play-handbook-en.pdf", DocumentSource.ALT_PLAY_HANDBOOK_PDF, RuleType.GENERAL_RULE),
        "errata": ("https://www.pokemon.com/static-assets/content-assets/cms2/pdf/trading-card-game/tcg_errata.pdf", DocumentSource.ERRATA_PDF, RuleType.ERRATA),
        "deck_list_guide": ("https://www.pokemon.com/static-assets/content-assets/cms2/pdf/play-pokemon/rules/play-pokemon-deck-list-85x11.pdf", DocumentSource.DECK_LIST_GUIDE_PDF, RuleType.TOURNAMENT_RULE),
    }

    def parse_pdf_file(self, file_path: str, source: DocumentSource, rule_type: RuleType) -> list[Document]:
        """Parse a local PDF file into a collection of page-level Document domain objects."""
        logger.info("Parsing PDF file: %s", file_path)
        documents: list[Document] = []
        path = Path(file_path)
        if not path.exists():
            logger.error("PDF File not found at path: %s", file_path)
            return documents

        try:
            # Extract markdown preservation with pymupdf4llm
            md_text = pymupdf4llm.to_markdown(file_path)
            doc = fitz.open(file_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                doc_obj = Document(
                    doc_id=f"{path.stem}_p{page_num + 1}",
                    content=text,
                    metadata=DocumentMetadata(
                        source=source,
                        document_title=path.name,
                        page_number=page_num + 1,
                        rule_type=rule_type,
                    )
                )
                documents.append(doc_obj)
        except Exception as exc:
            logger.error("Failed to parse PDF %s: %s", file_path, exc)

        return documents
