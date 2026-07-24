"""
Ingestion Pipeline Coordinator.
"""

import logging
from pokemon_tcg_rag.domain.models import Chunk, Document
from pokemon_tcg_rag.ingestion.chunker import DocumentChunker
from pokemon_tcg_rag.ingestion.crawler_pokegym import PokegymCrawler
from pokemon_tcg_rag.ingestion.html_scraper import HTMLPageScraper
from pokemon_tcg_rag.ingestion.normalizer import DocumentNormalizer
from pokemon_tcg_rag.ingestion.pdf_parser import PDFParser

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Orchestrates end-to-end extraction, normalization, chunking, and storage."""

    def __init__(self) -> None:
        self.pokegym_crawler = PokegymCrawler()
        self.pdf_parser = PDFParser()
        self.html_scraper = HTMLPageScraper()
        self.normalizer = DocumentNormalizer()
        self.chunker = DocumentChunker()

    def run(self) -> list[Chunk]:
        """Execute full ingestion pipeline."""
        logger.info("Executing Ingestion Pipeline...")
        raw_docs: list[Document] = []

        # 1. Fetch Pokegym Rulings
        pokegym_docs = self.pokegym_crawler.fetch_all_rulings()
        raw_docs.extend(pokegym_docs)

        # 2. Fetch Web HTML Pages
        html_docs = self.html_scraper.fetch_all_html_pages()
        raw_docs.extend(html_docs)

        # 3. Process and Chunk Documents
        all_chunks: list[Chunk] = []
        for doc in raw_docs:
            normalized_doc = self.normalizer.normalize(doc)
            chunks = self.chunker.chunk_document(normalized_doc)
            all_chunks.extend(chunks)

        logger.info("Ingestion completed. Total chunks generated: %d", len(all_chunks))
        return all_chunks
