"""
HTML Scraper for Web Rules (Ban List, Promo Legality, Mega Rules).
"""

import logging
from bs4 import BeautifulSoup
import requests

from pokemon_tcg_rag.domain.models import Document, DocumentMetadata, DocumentSource, RuleType

logger = logging.getLogger(__name__)


class HTMLPageScraper:
    """Scrapes dynamic HTML rule pages from pokemon.com."""

    TARGET_PAGES = [
        {
            "url": "https://www.pokemon.com/us/play-pokemon/about/pokemon-tcg-banned-card-list",
            "source": DocumentSource.BAN_LIST_HTML,
            "title": "Pokemon TCG Banned Card List",
            "rule_type": RuleType.BAN_STATUS,
        },
        {
            "url": "https://www.pokemon.com/us/play-pokemon/about/mega-evolution/mega-evolution-pitch-black-rule-changes-announcement",
            "source": DocumentSource.MEGA_RULES_HTML,
            "title": "Mega Evolution Rule Changes",
            "rule_type": RuleType.MECHANIC_RULE,
        },
        {
            "url": "https://www.pokemon.com/us/play-pokemon/about/pokemon-tcg-promo-card-legality-status",
            "source": DocumentSource.PROMO_LEGALITY_HTML,
            "title": "Promo Card Legality Status",
            "rule_type": RuleType.PROMO_STATUS,
        },
    ]

    def fetch_all_html_pages(self) -> list[Document]:
        """Fetch and extract content from configured HTML pages."""
        documents: list[Document] = []
        for target in self.TARGET_PAGES:
            try:
                resp = requests.get(target["url"], timeout=30)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                main_content = soup.find("main") or soup.find("article") or soup.body
                text = main_content.get_text(separator="\n", strip=True) if main_content else ""

                doc = Document(
                    doc_id=f"html_{target['source'].value}",
                    content=text,
                    metadata=DocumentMetadata(
                        source=target["source"],
                        document_title=target["title"],
                        rule_type=target["rule_type"],
                        source_url=target["url"],
                    )
                )
                documents.append(doc)
            except Exception as exc:
                logger.warning("HTML scraper fetch failed for %s: %s", target["url"], exc)
        return documents
