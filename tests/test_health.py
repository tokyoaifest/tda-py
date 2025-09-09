"""
Test health endpoint functionality.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test health check endpoint returns expected response."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert "version" in data
    assert data["status"] == "healthy"


def test_config_endpoint():
    """Test config endpoint returns expected configuration."""
    response = client.get("/config")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "mode" in data
    assert "version" in data
    assert "features" in data
    assert isinstance(data["features"], dict)


def test_health_endpoint_structure():
    """Test health endpoint response structure matches model."""
    response = client.get("/health")
    data = response.json()
    
    # Should match HealthResponse model
    required_fields = ["status", "version"]
    for field in required_fields:
        assert field in data
    
    # Status should be string
    assert isinstance(data["status"], str)
    assert isinstance(data["version"], str)