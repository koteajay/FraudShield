"""Tests for health and API endpoints."""

from fastapi.testclient import TestClient
from app.main import app
from app.database import verify_database_connection

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_info_endpoint():
    response = client.get("/api")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "FraudShield"
    assert data["status"] == "running"
    assert "version" in data


def test_database_connection():
    assert verify_database_connection() is True
