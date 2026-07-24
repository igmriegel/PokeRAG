"""
Pokegym rulings crawler.

Fetches the official compendium listing, extracts ruling rows, persists the raw HTML and
JSONL artifacts, and emits domain ``Document`` objects for downstream ingestion.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, cast
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from pokemon_tcg_rag.domain.exceptions import IngestionError
from pokemon_tcg_rag.domain.models import Document, DocumentMetadata, DocumentSource, RuleType
from pokemon_tcg_rag.ingestion.trust_boundary import (
    download_trusted_bytes,
    is_instruction_poisoned,
    quarantine_payload,
)
from pokemon_tcg_rag.monitoring.logger import get_logger

LOGGER = get_logger(__name__)


class PokegymCrawler:
    """Crawler for extracting rulings from the Pokegym compendium."""

    BASE_URL = "https://compendium.pokegym.net/all-rulings-by-date/"
    PARSER_VERSION = "pokegym-crawler-v2"

    def __init__(
        self,
        raw_html_dir: str | Path = "data/raw_data/html",
        raw_json_dir: str | Path = "data/raw_data/json",
        quarantine_dir: str | Path = "data/raw_data/quarantine",
    ) -> None:
        self.raw_html_dir = Path(raw_html_dir)
        self.raw_json_dir = Path(raw_json_dir)
        self.quarantine_dir = Path(quarantine_dir)

    def fetch_all_rulings(self) -> list[Document]:
        """
        Fetch the compendium listing and return one Document per ruling.

        Raw HTML is persisted alongside a JSONL projection of the structured rows.
        """
        try:
            html_bytes, _ = download_trusted_bytes(
                self.BASE_URL,
                max_bytes=6_000_000,
                timeout=30,
                user_agent="PokemonTCGRAG/1.0 (+https://github.com/igmriegel/PokeRAG)",
                allowed_content_types=("text/html", "application/xhtml+xml"),
            )
        except Exception as exc:
            raise IngestionError(f"Failed to fetch Pokegym rulings: {exc}") from exc

        html = html_bytes.decode("utf-8", errors="ignore")
        self._persist_raw_html(html)

        try:
            rulings = self._parse_rulings(html)
        except Exception as exc:  # pragma: no cover - defensive wrapper
            raise IngestionError(f"Failed to parse Pokegym rulings: {exc}") from exc

        documents: list[Document] = []
        structured_rows: list[dict[str, Any]] = []
        for idx, ruling in enumerate(rulings):
            question = ruling.get("question", "").strip()
            answer = ruling.get("answer", "").strip()
            if not question and not answer:
                continue
            if is_instruction_poisoned(question) or is_instruction_poisoned(answer):
                quarantine_payload(
                    self.quarantine_dir,
                    source_url=ruling.get("url") or self.BASE_URL,
                    reason="instruction-poisoning",
                    payload=f"{question}\n{answer}",
                )
                raise IngestionError(
                    "Suspicious instruction-like content detected in Pokegym source"
                )

            content = f"Question: {question}\nAnswer: {answer}".strip()
            metadata = DocumentMetadata(
                source=DocumentSource.POKEGYM,
                document_title="Pokegym Rulings Compendium",
                card_name=ruling.get("card") or None,
                rule_type=RuleType.RULING,
                publication_date=ruling.get("date") or None,
                source_url=ruling.get("url") or self.BASE_URL,
            )
            documents.append(
                Document(
                    doc_id=f"pokegym_{idx:05d}",
                    content=content,
                    metadata=metadata,
                )
            )
            structured_rows.append(
                {
                    "date": ruling.get("date"),
                    "set": ruling.get("set"),
                    "card": ruling.get("card"),
                    "question": ruling.get("question"),
                    "answer": ruling.get("answer"),
                    "url": ruling.get("url"),
                }
            )

        self._persist_jsonl(structured_rows)
        LOGGER.info("pokegym_rulings_fetched", count=len(documents))
        return documents

    def _persist_raw_html(self, html: str) -> Path:
        self.raw_html_dir.mkdir(parents=True, exist_ok=True)
        path = self.raw_html_dir / "pokegym_all_rulings_by_date.html"
        path.write_text(html, encoding="utf-8")
        return path

    def _persist_jsonl(self, rows: list[dict[str, Any]]) -> Path:
        self.raw_json_dir.mkdir(parents=True, exist_ok=True)
        path = self.raw_json_dir / "pokegym_rulings.jsonl"
        with path.open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False))
                fh.write("\n")
        return path

    def _parse_rulings(self, html: str) -> list[dict[str, str]]:
        soup = BeautifulSoup(html, "html.parser")
        records = self._parse_table_rows(soup)
        if records:
            return records

        records = self._parse_definition_rows(soup)
        if records:
            return records

        records = self._parse_block_rows(soup)
        if records:
            return records

        raise ValueError("No Pokegym rulings found in HTML")

    def _parse_table_rows(self, soup: BeautifulSoup) -> list[dict[str, str]]:
        records: list[dict[str, str]] = []
        for table in soup.find_all("table"):
            headers = self._extract_table_headers(table)
            if not headers:
                continue
            for tr in table.find_all("tr"):
                cells = tr.find_all(["td", "th"])
                if not cells:
                    continue
                if any(cell.name == "th" for cell in cells):
                    continue
                row = self._row_from_cells(headers, cells, tr)
                if row:
                    records.append(row)
        return records

    def _parse_definition_rows(self, soup: BeautifulSoup) -> list[dict[str, str]]:
        """Parse the current Pokegym ``dl.q-and-a`` ruling layout."""
        records: list[dict[str, str]] = []
        for qa in soup.select("dl.q-and-a"):
            question = qa.find("dt")
            answers = qa.find_all("dd")
            if question is None or not answers:
                continue

            container = qa.parent if isinstance(qa.parent, Tag) else qa
            category_links = container.select(".ruling-categories a[href]")
            specific_categories = [
                link.get_text(" ", strip=True)
                for link in category_links
                if len(
                    [
                        part
                        for part in cast(str, link.get("href", "")).split("/category/", 1)[-1].split("/")
                        if part
                    ]
                )
                >= 2
            ]
            source = container.find(id="source")
            source_text = source.get_text(" ", strip=True) if source else ""
            date_match = re.search(r"\((\d{4}-\d{2}-\d{2})\)", source_text)
            ruling_link = container.find("a", href=lambda href: href and "/ruling/" in href)

            records.append(
                self._canonicalize_row(
                    {
                        "date": date_match.group(1) if date_match else "",
                        "card": specific_categories[0] if specific_categories else "",
                        "question": question.get_text(" ", strip=True),
                        "answer": " ".join(
                            answer.get_text(" ", strip=True) for answer in answers
                        ),
                        "url": urljoin(
                            self.BASE_URL,
                            cast(str, ruling_link.get("href"))
                            if ruling_link is not None
                            else self.BASE_URL,
                        ),
                    }
                )
            )
        return records

    def _parse_block_rows(self, soup: BeautifulSoup) -> list[dict[str, str]]:
        records: list[dict[str, str]] = []
        for block in soup.select("div.ruling, article, li, section"):
            row = self._extract_block_record(block)
            if row:
                records.append(row)
        return records

    def _extract_table_headers(self, table: Tag) -> list[str]:
        header_cells = table.find_all("th")
        if header_cells:
            return [self._normalize_header(cell.get_text(" ", strip=True)) for cell in header_cells]
        first_row = table.find("tr")
        if not first_row:
            return []
        return [
            self._normalize_header(cell.get_text(" ", strip=True))
            for cell in first_row.find_all(["th", "td"])
        ]

    def _row_from_cells(self, headers: list[str], cells: list[Tag], tr: Tag) -> dict[str, str]:
        values = [cell.get_text(" ", strip=True) for cell in cells]
        data: dict[str, str] = {}
        for idx in range(min(len(headers), len(values))):
            field = self._field_name(headers[idx], idx)
            if field == "url":
                link = cells[idx].find("a", href=True)
                if link:
                    data["url"] = urljoin(self.BASE_URL, cast(str, link.get("href")))
                else:
                    data["url"] = values[idx]
                continue
            data[field] = values[idx]

        if "url" not in data:
            link = tr.find("a", href=True)
            if link:
                data["url"] = urljoin(self.BASE_URL, cast(str, link.get("href")))

        return self._canonicalize_row(data)

    def _extract_block_record(self, block: Tag) -> dict[str, str]:
        data: dict[str, str] = {}
        labels = {
            "date": ["date", "published", "published date"],
            "set": ["set", "expansion"],
            "card": ["card", "pokemon"],
            "question": ["question", "q"],
            "answer": ["answer", "a"],
            "url": ["url", "link"],
        }
        text = block.get_text(" ", strip=True)
        if not text:
            return {}

        for field, synonyms in labels.items():
            value = self._extract_labeled_value(block, synonyms)
            if value:
                data[field] = value

        if "url" not in data:
            link = block.find("a", href=True)
            if link:
                data["url"] = urljoin(self.BASE_URL, cast(str, link.get("href")))

        return self._canonicalize_row(data)

    def _extract_labeled_value(self, block: Tag, labels: list[str]) -> str | None:
        lower_labels = tuple(label.lower() for label in labels)
        for candidate in block.find_all(["span", "div", "p", "li", "td", "th"]):
            text = candidate.get_text(" ", strip=True)
            lowered = text.lower()
            for label in lower_labels:
                if lowered.startswith(f"{label}:"):
                    value = text.split(":", 1)[1].strip()
                    if value:
                        return value
        return None

    def _normalize_header(self, header: str) -> str:
        normalized = header.strip().lower()
        normalized = normalized.replace(" ", "_")
        normalized = normalized.replace("-", "_")
        return normalized

    def _field_name(self, header: str, index: int) -> str:
        mapping = {
            "date": "date",
            "published": "date",
            "set": "set",
            "set_name": "set",
            "card": "card",
            "pokemon": "card",
            "question": "question",
            "answer": "answer",
            "url": "url",
            "link": "url",
        }
        return mapping.get(
            header,
            {0: "date", 1: "set", 2: "card", 3: "question", 4: "answer", 5: "url"}.get(
                index, header
            ),
        )

    def _canonicalize_row(self, data: dict[str, str]) -> dict[str, str]:
        return {
            "date": data.get("date", "").strip(),
            "set": data.get("set", "").strip(),
            "card": data.get("card", "").strip(),
            "question": data.get("question", "").strip(),
            "answer": data.get("answer", "").strip(),
            "url": data.get("url", self.BASE_URL).strip(),
        }
