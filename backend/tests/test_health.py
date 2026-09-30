"""Phase 1 Backend Foundation Tests."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db, check_db_health
from unittest.mock import patch

# Attach test routes to verify error handling behavior
@app.get("/_test_error/validation")
def _test_validation_route(required_int: int):
    return {"value": required_int}


@app.get("/_test_error/server-error")
def _test_server_error_route():
    raise RuntimeError("Intentional server crash for testing")


client = TestClient(app, raise_server_exceptions=False)


def test_app_loads():
    """Verify FastAPI application instance loads and responds."""
    response = client.get("/api")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "FraudShield"
    assert data["status"] == "running"
    assert "version" in data


def test_health_endpoint_success():
    """Verify GET /health returns 200 with status ok and database connected."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"


def test_api_health_endpoint_success():
    """Verify GET /api/health also returns valid health check."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_database_initialization():
    """Verify database init_db runs safely and check_db_health passes."""
    init_db()
    assert check_db_health() is True


def test_health_endpoint_database_failure():
    """Verify GET /health returns 503 degraded when database connectivity fails."""
    with patch("app.routers.health.check_db_health", return_value=False):
        response = client.get("/health")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["database"] == "disconnected"


def test_validation_error_handling():
    """Verify invalid request payloads trigger standardized 422 JSON errors."""
    response = client.get("/_test_error/validation?required_int=not_a_number")
    assert response.status_code == 422
    body = response.json()
    assert "error" in body
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "Request validation failed" in body["error"]["message"]
    assert isinstance(body["error"]["details"], list)


def test_not_found_error_handling():
    """Verify 404 endpoints return standardized error structure."""
    response = client.get("/non-existent-route-12345")
    assert response.status_code == 404
    body = response.json()
    assert "error" in body
    assert body["error"]["code"] == "NOT_FOUND"


def test_unhandled_exception_no_stack_trace_leak():
    """Verify 500 errors return structured responses without leaking stack traces."""
    response = client.get("/_test_error/server-error")
    assert response.status_code == 500
    body = response.json()
    assert "error" in body
    assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert body["error"]["message"] == "An unexpected server error occurred"
    # Ensure no internal traceback or file paths leaked to client
    assert "Traceback" not in response.text
    assert "Intentional server crash" not in response.text
