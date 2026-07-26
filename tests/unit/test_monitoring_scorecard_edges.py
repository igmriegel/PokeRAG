"""
Focused coverage for monitoring logging and scorecard helpers.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from types import SimpleNamespace

import pytest

from pokemon_tcg_rag.monitoring import logger as monitoring_logger
from pokemon_tcg_rag.operations.scorecard import build_scorecard, load_evidence


def test_setup_logging_and_trace_context_injection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        monitoring_logger,
        "get_settings",
        lambda: SimpleNamespace(LOG_LEVEL="debug"),
    )
    monkeypatch.setattr(
        monitoring_logger.logging,
        "basicConfig",
        lambda **kwargs: captured.setdefault("basic_config", kwargs),
    )
    monkeypatch.setattr(
        monitoring_logger.structlog,
        "configure",
        lambda **kwargs: captured.setdefault("structlog", kwargs),
    )
    monkeypatch.setattr(
        monitoring_logger,
        "current_trace_context",
        lambda: SimpleNamespace(trace_id="trace-1", span_id="span-2"),
    )

    monitoring_logger.setup_logging()
    event = monitoring_logger._inject_trace_context(None, "event", {})

    assert captured["basic_config"]["level"] == logging.DEBUG
    assert "processors" in captured["structlog"]
    assert event["trace_id"] == "trace-1"
    assert event["span_id"] == "span-2"


def test_scorecard_roundtrip_and_validation(tmp_path: Path) -> None:
    evidence_path = tmp_path / "evidence.json"
    evidence_payload = {"passed": True, "notes": ["ok"]}
    evidence_path.write_text(json.dumps(evidence_payload), encoding="utf-8")

    scorecard = build_scorecard({"artifact": tmp_path / "artifact.txt"}, evidence_payload)
    assert scorecard.passed is False
    assert scorecard.missing_artifacts == ["artifact"]
    assert scorecard.to_dict()["summary"]["evidence"] == evidence_payload
    assert load_evidence(evidence_path) == evidence_payload

    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError):
        load_evidence(invalid_path)
