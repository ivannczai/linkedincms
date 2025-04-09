"""
Tests for the main API endpoints.
"""
from fastapi.testclient import TestClient


def test_read_root(client: TestClient):
    """
    Test the root endpoint returns the expected welcome message.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Winning Sales Content Hub API"}


def test_healthcheck(client: TestClient):
    """
    Test the healthcheck endpoint returns a healthy status.
    """
    response = client.get("/healthcheck")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert "database" in response.json()
