"""
TASK-007 — TEST-018, TEST-019, TEST-020, TEST-021

Unit tests for the Pokegym crawler.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pokemon_tcg_rag.domain.exceptions import IngestionError
from pokemon_tcg_rag.domain.models import DocumentSource, RuleType
from pokemon_tcg_rag.ingestion.crawler_pokegym import PokegymCrawler

SAMPLE_HTML = """
<html>
  <body>
    <table>
      <thead>
        <tr>
          <th>Date</th>
          <th>Set</th>
          <th>Card</th>
          <th>Question</th>
          <th>Answer</th>
          <th>URL</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>2024-01-01</td>
          <td>Scarlet &amp; Violet</td>
          <td>Rare Candy</td>
          <td>Can I evolve?</td>
          <td>No, not on your first turn.</td>
          <td><a href="/ruling/1">link</a></td>
        </tr>
      </tbody>
    </table>
  </body>
</html>
"""

CURRENT_HTML = """
<section class="cpdm-rulings">
  <div class="entry-summary">
    <div class="ruling-2377">
      <div class="ruling-categories">
        <a href="/category/5-trainers/">Trainers</a>
        <a href="/category/5-trainers/roto-stick/">Roto-Stick</a>
      </div>
      <dl class="q-and-a">
        <dt>Must I shuffle after revealing four Supporters?</dt>
        <dd>No, you do not shuffle.</dd>
      </dl>
      <div id="source">Source: TPCi Rules Team (2026-06-04)</div>
      <a href="/ruling/2377/">View relevant cards</a>
    </div>
  </div>
</section>
"""


@pytest.mark.unit
def test_parse_ruling_row_fields() -> None:
    """TEST-018: crawler must parse the expected row fields from HTML."""
    crawler = PokegymCrawler()
    rows = crawler._parse_rulings(SAMPLE_HTML)

    assert len(rows) == 1
    row = rows[0]
    assert row["date"] == "2024-01-01"
    assert row["set"] == "Scarlet & Violet"
    assert row["card"] == "Rare Candy"
    assert row["question"] == "Can I evolve?"
    assert row["answer"] == "No, not on your first turn."
    assert row["url"].endswith("/ruling/1")


@pytest.mark.unit
def test_missing_field_handled() -> None:
    """TEST-019: missing fields should not crash parsing."""
    html = SAMPLE_HTML.replace("<td>Rare Candy</td>", "<td></td>")
    crawler = PokegymCrawler()
    rows = crawler._parse_rulings(html)

    assert len(rows) == 1
    assert rows[0]["card"] == ""


@pytest.mark.unit
def test_parse_current_definition_list_layout() -> None:
    crawler = PokegymCrawler()

    rows = crawler._parse_rulings(CURRENT_HTML)

    assert rows == [
        {
            "date": "2026-06-04",
            "set": "",
            "card": "Roto-Stick",
            "question": "Must I shuffle after revealing four Supporters?",
            "answer": "No, you do not shuffle.",
            "url": "https://compendium.pokegym.net/ruling/2377/",
        }
    ]


@pytest.mark.unit
def test_emits_documents_with_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """TEST-020: fetch_all_rulings must emit Documents with Pokegym metadata."""

    class DummyResponse:
        def __init__(self, text: str) -> None:
            self.text = text
            self.content = text.encode("utf-8")
            self.headers = {"content-type": "text/html; charset=utf-8"}

        def raise_for_status(self) -> None:
            return None

    def fake_get(*args: object, **kwargs: object) -> DummyResponse:
        return DummyResponse(SAMPLE_HTML)

    monkeypatch.setattr(
        "pokemon_tcg_rag.ingestion.trust_boundary.requests.get", fake_get
    )

    crawler = PokegymCrawler(
        raw_html_dir=tmp_path / "html", raw_json_dir=tmp_path / "json"
    )
    documents = crawler.fetch_all_rulings()

    assert len(documents) == 1
    doc = documents[0]
    assert doc.metadata.source == DocumentSource.POKEGYM
    assert doc.metadata.rule_type == RuleType.RULING
    assert doc.metadata.card_name == "Rare Candy"
    assert doc.metadata.source_url.endswith("/ruling/1")
    assert (tmp_path / "html" / "pokegym_all_rulings_by_date.html").exists()
    assert (tmp_path / "json" / "pokegym_rulings.jsonl").exists()


@pytest.mark.unit
def test_network_error_raises_ingestion_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """TEST-021: network failures must surface as IngestionError."""

    def fake_get(*args: object, **kwargs: object) -> None:
        raise RuntimeError("network down")

    monkeypatch.setattr(
        "pokemon_tcg_rag.ingestion.trust_boundary.requests.get", fake_get
    )

    crawler = PokegymCrawler()
    with pytest.raises(IngestionError):
        crawler.fetch_all_rulings()
