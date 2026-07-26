"""
HTML scraper for the official Pokemon TCG rule pages.

Extracts the ban list, promo legality, and mega rules pages into domain ``Document`` objects
while persisting the raw HTML for reproducibility and auditing.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypedDict

from bs4 import BeautifulSoup

from pokemon_tcg_rag.domain.exceptions import IngestionError
from pokemon_tcg_rag.domain.models import (
    Document,
    DocumentMetadata,
    DocumentSource,
    RuleType,
)
from pokemon_tcg_rag.ingestion.trust_boundary import (
    download_trusted_bytes,
    is_instruction_poisoned,
    quarantine_payload,
)
from pokemon_tcg_rag.monitoring.logger import get_logger

LOGGER = get_logger(__name__)


class TargetPage(TypedDict):
    url: str
    source: DocumentSource
    title: str
    rule_type: RuleType


class HTMLPageScraper:
    """Scrape the official HTML pages into domain documents."""

    PARSER_VERSION = "html-scraper-v2"

    TARGET_PAGES: list[TargetPage] = [
        {
            "url": "https://www.pokemon.com/us/play-pokemon/about/pokemon-tcg-banned-card-list",
            "source": DocumentSource.BAN_LIST_HTML,
            "title": "Pokemon TCG Banned Card List",
            "rule_type": RuleType.BAN_STATUS,
        },
        {
            "url": "https://www.pokemon.com/us/play-pokemon/about/pokemon-tcg-promo-card-legality-status",
            "source": DocumentSource.PROMO_LEGALITY_HTML,
            "title": "Pokemon TCG Promo Card Legality Status",
            "rule_type": RuleType.PROMO_STATUS,
        },
        {
            "url": "https://www.pokemon.com/us/play-pokemon/about/mega-evolution/mega-evolution-pitch-black-rule-changes-announcement",
            "source": DocumentSource.MEGA_RULES_HTML,
            "title": "Pokemon TCG Mega Evolution Rule Changes",
            "rule_type": RuleType.MECHANIC_RULE,
        },
    ]

    def __init__(
        self,
        raw_output_dir: str | Path = "data/raw_data/html",
        quarantine_dir: str | Path = "data/raw_data/quarantine",
    ) -> None:
        self.raw_output_dir = Path(raw_output_dir)
        self.quarantine_dir = Path(quarantine_dir)

    def fetch_all_html_pages(self) -> list[Document]:
        """Fetch the configured HTML pages and return one document per page."""
        documents: list[Document] = []
        for page in self.TARGET_PAGES:
            try:
                html_bytes, _ = download_trusted_bytes(
                    page["url"],
                    max_bytes=2_000_000,
                    timeout=30,
                    user_agent="PokemonTCGRAG/1.0 (+https://github.com/igmriegel/PokeRAG)",
                    allowed_content_types=("text/html", "application/xhtml+xml"),
                )
            except Exception as exc:
                raise IngestionError(f"Failed to fetch HTML page {page['url']}: {exc}") from exc

            html = html_bytes.decode("utf-8", errors="ignore")
            self._persist_raw_html(page["source"], html)
            content = self._extract_main_content(html)
            if not content.strip():
                raise IngestionError(f"Empty HTML content extracted from {page['url']}")
            if is_instruction_poisoned(content):
                quarantine_payload(
                    self.quarantine_dir,
                    source_url=page["url"],
                    reason="instruction-poisoning",
                    payload=content,
                )
                raise IngestionError(
                    f"Suspicious instruction-like content detected in {page['url']}"
                )

            documents.append(
                Document(
                    doc_id=f"html_{page['source'].value}",
                    content=content,
                    metadata=DocumentMetadata(
                        source=page["source"],
                        document_title=page["title"],
                        rule_type=page["rule_type"],
                        publication_date=datetime.now(UTC).date().isoformat(),
                        source_url=page["url"],
                    ),
                )
            )

        LOGGER.info("html_pages_fetched", count=len(documents))
        return documents

    def _persist_raw_html(self, source: DocumentSource, html: str) -> Path:
        self.raw_output_dir.mkdir(parents=True, exist_ok=True)
        path = self.raw_output_dir / f"{source.value}.html"
        path.write_text(html, encoding="utf-8")
        return path

    def _extract_main_content(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "noscript"]):
            tag.decompose()

        container = soup.find("main") or soup.find("article") or soup.body or soup
        text = container.get_text(separator="\n", strip=True)
        cleaned_lines = [line.strip() for line in text.splitlines() if line.strip()]
        content = "\n".join(cleaned_lines)
        if content and is_instruction_poisoned(content):
            quarantine_payload(
                self.quarantine_dir,
                source_url="unknown",
                reason="instruction-poisoning",
                payload=content,
            )
            raise IngestionError("Suspicious instruction-like content detected in HTML body")
        return content

    def _dump_json_summary(self, documents: list[Document]) -> Path:
        self.raw_output_dir.mkdir(parents=True, exist_ok=True)
        path = self.raw_output_dir / "html_pages.json"
        payload: list[dict[str, Any]] = []
        for document in documents:
            payload.append(
                {
                    "doc_id": document.doc_id,
                    "source": document.metadata.source.value,
                    "document_title": document.metadata.document_title,
                    "source_url": document.metadata.source_url,
                    "rule_type": document.metadata.rule_type.value,
                }
            )
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path
