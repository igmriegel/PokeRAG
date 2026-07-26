"""
TASK-068 — Real infrastructure integration layer.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from qdrant_client import QdrantClient
from sqlalchemy import create_engine, text

from pokemon_tcg_rag.storage.relational_db import Base


def _env_or_skip(name: str) -> str:
    value = pytest.importorskip("os").environ.get(name)
    if not value:
        pytest.skip(f"{name} is not configured")
    return value


@pytest.mark.integration
def test_postgres_feedback_roundtrip_with_real_engine() -> None:
    uri = _env_or_skip("POKERAG_INTEGRATION_POSTGRES_URI")
    engine = create_engine(uri, pool_pre_ping=True)
    try:
        Base.metadata.create_all(bind=engine)
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO user_feedback (feedback_id, query_id, query, answer, rating, comment, model_name, latency_seconds, created_at) "
                    "VALUES ('fb-test', 'qid-test', 'q', 'a', 1, 'ok', 'gpt-4o-mini', 0.1, CURRENT_TIMESTAMP)"
                )
            )
            rows = connection.execute(text("SELECT query_id, rating FROM user_feedback")).fetchall()
        assert rows
        assert rows[0][0] == "qid-test"
    finally:
        engine.dispose()


@pytest.mark.integration
def test_qdrant_collection_contract_with_real_client() -> None:
    host = pytest.importorskip("os").environ.get("POKERAG_INTEGRATION_QDRANT_HOST")
    if not host:
        pytest.skip("POKERAG_INTEGRATION_QDRANT_HOST is not configured")
    port = int(pytest.importorskip("os").environ.get("POKERAG_INTEGRATION_QDRANT_PORT", "6333"))
    client = QdrantClient(host=host, port=port, prefer_grpc=False)
    assert client.get_collections() is not None


class _ProviderHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("content-length", "0"))
        self.rfile.read(length)
        payload = json.dumps({"answer": "provider-ok"}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format_str: str, *args: object) -> None:  # noqa: A002
        return None


@pytest.mark.integration
def test_http_provider_stub_contract() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _ProviderHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        import httpx

        url = f"http://127.0.0.1:{server.server_port}"
        response = httpx.post(url, json={"prompt": "hello"}, timeout=5.0)
        assert response.status_code == 200
        assert response.json()["answer"] == "provider-ok"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
