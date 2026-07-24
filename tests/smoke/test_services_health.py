"""
Smoke test verifying FastAPI endpoint health.
"""

from __future__ import annotations

import pytest

from pokemon_tcg_rag.api.main import health_check


@pytest.mark.smoke
def test_api_health_endpoint() -> None:
    response = health_check()
    assert response.status == "healthy"
