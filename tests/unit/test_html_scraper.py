"""
TASK-008 — TEST-022, TEST-023, TEST-024

Unit tests for the HTML page scraper.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pokemon_tcg_rag.domain.exceptions import IngestionError
from pokemon_tcg_rag.domain.models import DocumentSource, RuleType
from pokemon_tcg_rag.ingestion.html_scraper import HTMLPageScraper

SAMPLE_HTML = """
<html>
  <head>
    <title>Should be ignored</title>
    <script>var x = 1;</script>
  </head>
  <body>
    <header>Header should be stripped</header>
    <nav>Nav should be stripped</nav>
    <main>
      <h1>Pokemon TCG Banned Card List</h1>
      <p>Important rules content.</p>
    </main>
    <footer>Footer should be stripped</footer>
  </body>
</html>
"""


@pytest.mark.unit
def test_scrape_ban_list_content(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """TEST-022: scrape should emit a ban list document with main content only."""

    class DummyResponse:
        def __init__(self, text: str) -> None:
            self.text = text

        def raise_for_status(self) -> None:
            return None

    def fake_get(url: str, timeout: int, headers: dict[str, str]) -> DummyResponse:
        return DummyResponse(SAMPLE_HTML)

    monkeypatch.setattr("pokemon_tcg_rag.ingestion.html_scraper.requests.get", fake_get)

    scraper = HTMLPageScraper(raw_output_dir=tmp_path)
    documents = scraper.fetch_all_html_pages()

    assert len(documents) == 3
    ban_doc = documents[0]
    assert ban_doc.metadata.source == DocumentSource.BAN_LIST_HTML
    assert ban_doc.metadata.rule_type == RuleType.BAN_STATUS
    assert "Important rules content." in ban_doc.content
    assert "Header should be stripped" not in ban_doc.content
    assert (tmp_path / "ban_list_html.html").exists()


@pytest.mark.unit
def test_source_and_ruletype_mapping() -> None:
    """TEST-023: every target page must map to the expected source/rule type."""
    mapping = {
        item["url"]: (item["source"], item["rule_type"]) for item in HTMLPageScraper.TARGET_PAGES
    }

    assert mapping[
        "https://www.pokemon.com/us/play-pokemon/about/pokemon-tcg-banned-card-list"
    ] == (DocumentSource.BAN_LIST_HTML, RuleType.BAN_STATUS)
    assert mapping[
        "https://www.pokemon.com/us/play-pokemon/about/pokemon-tcg-promo-card-legality-status"
    ] == (DocumentSource.PROMO_LEGALITY_HTML, RuleType.PROMO_STATUS)
    assert mapping[
        "https://www.pokemon.com/us/play-pokemon/about/mega-evolution/mega-evolution-pitch-black-rule-changes-announcement"
    ] == (DocumentSource.MEGA_RULES_HTML, RuleType.MECHANIC_RULE)


@pytest.mark.unit
def test_boilerplate_stripped() -> None:
    """TEST-024: navigation and footer boilerplate must be removed from extracted content."""
    scraper = HTMLPageScraper()
    content = scraper._extract_main_content(SAMPLE_HTML)

    assert "Header should be stripped" not in content
    assert "Nav should be stripped" not in content
    assert "Footer should be stripped" not in content
    assert "Important rules content." in content


@pytest.mark.unit
def test_network_error_raises_ingestion_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fetch failure must surface as IngestionError."""

    def fake_get(*args: object, **kwargs: object) -> None:
        raise RuntimeError("offline")

    monkeypatch.setattr("pokemon_tcg_rag.ingestion.html_scraper.requests.get", fake_get)

    scraper = HTMLPageScraper()
    with pytest.raises(IngestionError):
        scraper.fetch_all_html_pages()
