"""
Tests for the FastAPI server: routing, HTTP behavior, and dev tooling.

These tests are stable for the life of the project — they don't depend on
any specific feature and should always pass as long as the server starts.

Run with: uv run pytest tests/test_api_server.py -v
"""

from fastapi.testclient import TestClient

from app.main import app

# TestClient is httpx under the hood — it spins up the FastAPI app in-process
# so no server needs to be running. Think of it like React Testing Library
# for the backend: you get a fake HTTP client that calls your handlers directly.
client = TestClient(app)


def test_server_health_check_reports_ok():
    """The /health endpoint confirms the server is running and reachable."""
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "app" in body


def test_swagger_ui_accessible_when_debug_is_enabled():
    """Interactive API docs at /docs are available when DEBUG=true in .env.
    This is how we manually explore and test endpoints during development."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_unregistered_routes_return_not_found():
    """FastAPI should return 404 for any path that has no registered handler,
    rather than raising an unhandled exception."""
    response = client.get("/this-route-does-not-exist")
    assert response.status_code == 404

