"""
End-to-End User Scenarios Test Suite.
"""

import pytest
from fastapi.testclient import TestClient
from pokemon_tcg_rag.api.main import app

client = TestClient(app)


@pytest.mark.e2e
def test_e2e_rare_candy_query() -> None:
    payload = {"question": "Can Rare Candy evolve a Pokemon on Turn 1?", "top_k": 5}
    response = client.post("/api/v1/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "citations" in data
    assert data["query"] == payload["question"]


@pytest.mark.e2e
def test_e2e_feedback_submission() -> None:
    fb_payload = {
        "query": "Is Mew VMAX legal?",
        "answer": "Mew VMAX is currently rotated out of Standard format.",
        "rating": 1,
        "comment": "Accurate ban status citation.",
        "model_name": "gpt-4o-mini",
        "latency_seconds": 0.35
    }
    response = client.post("/api/v1/feedback", json=fb_payload)
    assert response.status_code == 201
    assert response.json()["status"] == "success"
