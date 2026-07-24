"""
TASK-040 — Deployment IaC smoke tests.
"""

from __future__ import annotations

import pathlib

import pytest
import yaml

PROJECT_ROOT = pathlib.Path(__file__).parents[2]
RENDER_FILE = PROJECT_ROOT / "deploy" / "render.yaml"
K8S_FILE = PROJECT_ROOT / "deploy" / "k8s" / "stack.yaml"
EXPECTED_SERVICE_NAMES = {"qdrant", "postgres", "api", "ui", "prometheus", "grafana", "ingestion"}


@pytest.mark.smoke
def test_k8s_manifests_valid() -> None:
    with K8S_FILE.open(encoding="utf-8") as fh:
        docs = list(yaml.safe_load_all(fh))

    assert docs
    kinds = {doc["kind"] for doc in docs if isinstance(doc, dict) and doc.get("kind")}
    assert {"Deployment", "Service", "StatefulSet", "Job"}.issubset(kinds)


@pytest.mark.smoke
def test_all_services_have_manifests() -> None:
    with RENDER_FILE.open(encoding="utf-8") as fh:
        render = yaml.safe_load(fh)

    service_names = {service["name"] for service in render.get("services", [])}
    assert service_names == EXPECTED_SERVICE_NAMES
