"""
Pokegym Rulings Web Crawler.
Scrapes https://compendium.pokegym.net/all-rulings-by-date/
"""

import logging
from typing import Any
from bs4 import BeautifulSoup
import requests

from pokemon_tcg_rag.domain.models import Document, DocumentMetadata, DocumentSource, RuleType

logger = logging.getLogger(__name__)


class PokegymCrawler:
    """Crawler for extracting rulings from Pokegym Compendium."""

    BASE_URL = "https://compendium.pokegym.net/all-rulings-by-date/"

    def __init__(self, raw_output_dir: str = "data/raw_data/json") -> None:
        self.raw_output_dir = raw_output_dir

    def fetch_all_rulings(self) -> list[Document]:
        """Fetch all rulings by date from Pokegym and parse structured documents."""
        logger.info("Starting Pokegym rulings scrape from %s", self.BASE_URL)
        # Interface contract - returns list of Document domain objects
        documents: list[Document] = []
        try:
            response = requests.get(self.BASE_URL, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Parsing logic stub
            ruling_blocks = soup.find_all("div", class_="ruling")
            for idx, block in enumerate(ruling_blocks):
                question_text = block.find("div", class_="question")
                answer_text = block.find("div", class_="answer")
                date_text = block.find("span", class_="date")
                card_name = block.find("span", class_="card")

                content = f"Question: {question_text.text.strip() if question_text else ''}\nAnswer: {answer_text.text.strip() if answer_text else ''}"
                
                doc = Document(
                    doc_id=f"pokegym_{idx}",
                    content=content,
                    metadata=DocumentMetadata(
                        source=DocumentSource.POKEGYM,
                        document_title="Pokegym Rulings Compendium",
                        card_name=card_name.text.strip() if card_name else None,
                        rule_type=RuleType.RULING,
                        publication_date=date_text.text.strip() if date_text else None,
                        source_url=self.BASE_URL,
                    )
                )
                documents.append(doc)
        except Exception as exc:
            logger.warning("Pokegym scraping simulation or HTTP fallback due to network: %s", exc)
        return documents
