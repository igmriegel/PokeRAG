"""
TASK-051..TASK-055 — Platform hardening smoke tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).parents[2]
APP_DOCKERFILE = PROJECT_ROOT / "docker" / "Dockerfile.app"
INGESTION_DOCKERFILE = PROJECT_ROOT / "docker" / "Dockerfile.ingestion"
DOCKERIGNORE_FILE = PROJECT_ROOT / ".dockerignore"
K8S_STACK_FILE = PROJECT_ROOT / "deploy" / "k8s" / "stack.yaml"
K8S_SECURITY_FILE = PROJECT_ROOT / "deploy" / "k8s" / "security.yaml"
INFRA_K8S_DEPLOYMENT = PROJECT_ROOT / "infra" / "k8s" / "deployment.yaml"


@pytest.mark.smoke
def test_dockerfiles_are_multistage_and_rootless() -> None:
    for dockerfile in (APP_DOCKERFILE, INGESTION_DOCKERFILE):
        content = dockerfile.read_text(encoding="utf-8")
        assert "AS builder" in content
        assert "COPY --from=builder" in content
        assert "USER 10001:10001" in content
        assert "python:3.11-slim" in content


@pytest.mark.smoke
def test_dockerignore_present() -> None:
    assert DOCKERIGNORE_FILE.exists()
    content = DOCKERIGNORE_FILE.read_text(encoding="utf-8")
    assert ".venv" in content
    assert "tests" in content


@pytest.mark.smoke
def test_k8s_stack_has_restricted_workloads() -> None:
    docs = list(yaml.safe_load_all(K8S_STACK_FILE.read_text(encoding="utf-8")))
    api = next(
        doc for doc in docs if doc.get("kind") == "Deployment" and doc["metadata"]["name"] == "api"
    )
    api_spec = api["spec"]["template"]["spec"]
    api_container = api_spec["containers"][0]

    assert api_spec["serviceAccountName"] == "api-sa"
    assert api_spec["automountServiceAccountToken"] is False
    assert api_container["securityContext"]["allowPrivilegeEscalation"] is False
    assert api_container["resources"]["limits"]["cpu"] == "1000m"
    assert api_container["readinessProbe"]["httpGet"]["path"] == "/health"


@pytest.mark.smoke
def test_k8s_security_docs_include_networkpolicy_and_ingress() -> None:
    docs = list(yaml.safe_load_all(K8S_SECURITY_FILE.read_text(encoding="utf-8")))
    kinds = {doc["kind"] for doc in docs if isinstance(doc, dict)}
    assert {"NetworkPolicy", "Ingress"}.issubset(kinds)


@pytest.mark.smoke
def test_no_latest_tags_remain_in_deploy_manifests() -> None:
    for path in (K8S_STACK_FILE, INFRA_K8S_DEPLOYMENT):
        content = path.read_text(encoding="utf-8")
        assert ":latest" not in content
