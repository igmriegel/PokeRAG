"""
TASK-006 — TEST-016, TEST-017

Smoke tests for Docker Compose configuration validity.
These tests do not start Docker, they validate the compose file structure.
"""

from pathlib import Path

import pytest
import yaml


PROJECT_ROOT = Path(__file__).parents[2]
COMPOSE_FILE = PROJECT_ROOT / "docker-compose.yml"

EXPECTED_SERVICES = {"qdrant", "postgres", "ingestion", "api", "ui", "prometheus", "grafana"}


@pytest.mark.smoke
def test_compose_config_valid() -> None:
    """TEST-016: docker-compose.yml must be a valid YAML file parseable by PyYAML."""
    assert COMPOSE_FILE.exists(), f"docker-compose.yml not found at {COMPOSE_FILE}"
    with open(COMPOSE_FILE) as fh:
        config = yaml.safe_load(fh)
    assert isinstance(config, dict), "docker-compose.yml must parse to a dict"
    assert "services" in config, "docker-compose.yml must declare a 'services' key"
    assert "volumes" in config, "docker-compose.yml must declare a 'volumes' key"
    assert "networks" in config, "docker-compose.yml must declare a 'networks' key"


@pytest.mark.smoke
def test_all_seven_services_declared() -> None:
    """TEST-017: All seven required services must be declared in docker-compose.yml."""
    with open(COMPOSE_FILE) as fh:
        config = yaml.safe_load(fh)

    declared_services = set(config.get("services", {}).keys())
    assert EXPECTED_SERVICES == declared_services, (
        f"Service mismatch.\n  Expected: {sorted(EXPECTED_SERVICES)}\n  Found:    {sorted(declared_services)}"
    )


@pytest.mark.smoke
def test_all_services_have_network() -> None:
    """Every service must be attached to the shared pokemon_net network."""
    with open(COMPOSE_FILE) as fh:
        config = yaml.safe_load(fh)

    for service_name, service_cfg in config["services"].items():
        networks = service_cfg.get("networks", [])
        assert "pokemon_net" in networks, (
            f"Service '{service_name}' must be attached to 'pokemon_net' network"
        )


@pytest.mark.smoke
def test_required_volumes_declared() -> None:
    """Named volumes for qdrant/postgres/prometheus/grafana must be declared."""
    with open(COMPOSE_FILE) as fh:
        config = yaml.safe_load(fh)
    volumes = set(config.get("volumes", {}).keys())
    for vol in ("qdrant_storage", "postgres_data", "prometheus_data", "grafana_data"):
        assert vol in volumes, f"Volume '{vol}' must be declared at top level"


@pytest.mark.smoke
def test_postgres_uses_version_16() -> None:
    """Postgres service must use postgres:16 image (TASK-006 spec)."""
    with open(COMPOSE_FILE) as fh:
        config = yaml.safe_load(fh)
    pg_image: str = config["services"]["postgres"]["image"]
    assert pg_image.startswith("postgres:16"), (
        f"postgres image must be postgres:16-*, got '{pg_image}'"
    )
