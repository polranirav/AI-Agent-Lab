"""End-to-end API tests using FastAPI's TestClient (no live LLM calls)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_orchestrate_route_registered():
    # The orchestrate endpoint should be present in the OpenAPI schema.
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/orchestrate" in paths
    assert "post" in paths["/api/orchestrate"]


def test_orchestrate_validates_request():
    # Missing required 'topic' should be a 422 validation error (no LLM call).
    resp = client.post("/api/orchestrate", json={"brief": "no topic here"})
    assert resp.status_code == 422
