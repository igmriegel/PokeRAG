"""
Smoke tests for observability assets.
"""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_grafana_dashboard_includes_cost_and_tokens() -> None:
    dashboard = json.loads(
        (PROJECT_ROOT / "docker/grafana/dashboards/pokemon_rag.json").read_text(
            encoding="utf-8"
        )
    )

    titles = {panel["title"] for panel in dashboard["panels"]}
    assert "Provider Tokens by Model and Stage" in titles
    assert "Provider Cost by Model and Stage" in titles
    assert any(
        target["expr"] == "pokemon_rag_feedback_total"
        for panel in dashboard["panels"]
        for target in panel.get("targets", [])
    )


def test_prometheus_alert_rules_exist() -> None:
    alerts = (PROJECT_ROOT / "docker/prometheus/alerts.yml").read_text(encoding="utf-8")

    assert "PokemonRAGHighErrorRate" in alerts
    assert "PokemonRAGHighLatencyP95" in alerts
    assert "PokemonRAGHighProviderSpend" in alerts
