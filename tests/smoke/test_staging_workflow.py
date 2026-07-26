"""
Smoke test for staging deployment workflow.
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_staging_workflow_mentions_immutable_deploy_and_smoke() -> None:
    content = (PROJECT_ROOT / ".github/workflows/staging-deploy.yml").read_text(encoding="utf-8")

    assert "workflow_dispatch" in content
    assert "image_digest" in content
    assert "kubectl apply -f deploy/k8s/stack.yaml" in content
    assert "curl --fail" in content
