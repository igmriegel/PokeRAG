"""
Smoke test verifying FastAPI endpoint health.
"""

import pytest
from fastapi.testclient import TestClient
from pokemon_tcg_rag.api.main import app

client = TestClient(app)


@pytest.mark.smoke
def test_api_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "healthy"
