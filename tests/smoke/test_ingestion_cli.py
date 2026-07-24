"""
TASK-011 — TEST-032, TEST-033

Smoke tests for the ingestion CLI and compose service.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import yaml

from pokemon_tcg_rag.domain.models import Document, DocumentMetadata, DocumentSource, RuleType

PROJECT_ROOT = Path(__file__).parents[2]
COMPOSE_FILE = PROJECT_ROOT / "docker-compose.yml"


class DummyPipeline:
    def __init__(self, processed_dir: Path | None = None) -> None:
        self.processed_dir = processed_dir

    def run(self, sources: list[str] | None = None, index: bool = False) -> list[Document]:
        return [
            Document(
                doc_id="cli_doc_001",
                content="CLI smoke test content",
                metadata=DocumentMetadata(
                    source=DocumentSource.RULEBOOK_PDF,
                    document_title="Official Rulebook",
                    rule_type=RuleType.GENERAL_RULE,
                ),
            )
        ]


def _load_run_ingestion_module() -> object:
    spec = importlib.util.spec_from_file_location(
        "run_ingestion",
        PROJECT_ROOT / "scripts" / "run_ingestion.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.smoke
def test_run_ingestion_cli_smoke(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """TEST-032: CLI should execute the pipeline and report success."""
    run_ingestion = _load_run_ingestion_module()

    monkeypatch.setattr(run_ingestion, "IngestionPipeline", DummyPipeline)

    exit_code = run_ingestion.main(["--sources", "pdf", "--out-dir", str(tmp_path / "processed")])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Generated 1 documents" in captured.out


@pytest.mark.smoke
def test_ingestion_service_in_compose() -> None:
    """TEST-033: compose must declare the ingestion service with the expected command."""
    assert COMPOSE_FILE.exists(), f"docker-compose.yml not found at {COMPOSE_FILE}"

    with COMPOSE_FILE.open(encoding="utf-8") as fh:
        config = yaml.safe_load(fh)

    ingestion = config["services"]["ingestion"]
    assert ingestion["build"]["dockerfile"] == "docker/Dockerfile.ingestion"
    assert ingestion["command"] == ["python3", "scripts/run_ingestion.py"]
    assert ingestion.get("volumes") == ["./data:/app/data", "./config:/app/config"]
    assert ingestion.get("env_file") == [".env"]
