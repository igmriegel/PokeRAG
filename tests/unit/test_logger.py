"""
TASK-005 — TEST-014, TEST-015

Unit tests for structured JSON logging via structlog.
"""

import json

import pytest

from pokemon_tcg_rag.config.settings import get_settings
from pokemon_tcg_rag.monitoring.logger import get_logger, setup_logging

# ─────────────────────────────────────────────
# TEST-014  JSON output from setup_logging
# ─────────────────────────────────────────────


@pytest.mark.unit
def test_setup_logging_json_output(capsys: pytest.CaptureFixture[str]) -> None:
    """TEST-014: A logged event must serialize to JSON with expected keys."""
    get_settings.cache_clear()
    setup_logging()

    logger = get_logger("test.module")
    logger.info("pokemon_test_event", card="Charizard", rule="attack_rule")

    captured = capsys.readouterr()
    # structlog outputs one JSON object per line
    output = captured.out.strip()
    assert output, "Expected at least one log line in stdout"

    # The last non-empty line should be valid JSON
    last_line = [ln for ln in output.splitlines() if ln.strip()][-1]
    payload = json.loads(last_line)

    assert "event" in payload, "JSON log must include 'event' key"
    assert payload["event"] == "pokemon_test_event"
    assert "timestamp" in payload, "JSON log must include 'timestamp' key"
    assert "level" in payload, "JSON log must include 'level' key"
    assert payload.get("card") == "Charizard"


# ─────────────────────────────────────────────
# TEST-015  Log level is honoured from Settings
# ─────────────────────────────────────────────


@pytest.mark.unit
def test_log_level_from_settings(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """TEST-015: setup_logging() must respect LOG_LEVEL from Settings."""
    get_settings.cache_clear()
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    setup_logging()

    logger = get_logger("test.level")

    # DEBUG message must be suppressed when level is WARNING
    logger.debug("debug_message_suppressed")
    captured_debug = capsys.readouterr()
    debug_lines = [ln for ln in captured_debug.out.splitlines() if "debug_message_suppressed" in ln]
    assert not debug_lines, "DEBUG messages must be suppressed at WARNING level"

    # WARNING message must appear
    logger.warning("warning_message_visible")
    captured_warn = capsys.readouterr()
    warning_lines = [ln for ln in captured_warn.out.splitlines() if "warning_message_visible" in ln]
    assert warning_lines, "WARNING messages must be visible at WARNING level"

    get_settings.cache_clear()


@pytest.mark.unit
def test_get_logger_returns_bound_logger() -> None:
    """get_logger(name) must return a structlog logger-like object."""
    logger = get_logger("test.bound")
    # Must have common log-level methods
    assert callable(getattr(logger, "info", None))
    assert callable(getattr(logger, "warning", None))
    assert callable(getattr(logger, "error", None))
    assert callable(getattr(logger, "debug", None))
