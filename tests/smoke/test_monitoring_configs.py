"""
TASK-038 — Monitoring configuration smoke tests.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).parents[2]
PROMETHEUS_FILE = PROJECT_ROOT / "docker" / "prometheus" / "prometheus.yml"
DATASOURCE_FILE = (
    PROJECT_ROOT
    / "docker"
    / "grafana"
    / "provisioning"
    / "datasources"
    / "datasource.yml"
)
DASHBOARD_FILE = PROJECT_ROOT / "docker" / "grafana" / "dashboards" / "pokemon_rag.json"


@pytest.mark.smoke
def test_prometheus_config_valid_yaml() -> None:
    with PROMETHEUS_FILE.open(encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    assert isinstance(config, dict)
    assert config["scrape_configs"][0]["static_configs"][0]["targets"] == ["api:8000"]


@pytest.mark.smoke
def test_dashboard_has_min_5_panels() -> None:
    with DASHBOARD_FILE.open(encoding="utf-8") as fh:
        dashboard = json.load(fh)
    assert len(dashboard.get("panels", [])) >= 5


@pytest.mark.smoke
def test_grafana_datasource_provisioned() -> None:
    with DATASOURCE_FILE.open(encoding="utf-8") as fh:
        datasource = yaml.safe_load(fh)
    assert isinstance(datasource, dict)
    datasources = datasource.get("datasources", [])
    assert any(item["name"] == "Prometheus" for item in datasources)
