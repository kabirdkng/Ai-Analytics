import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app

client = TestClient(app)

def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_analytics_overview():
    """Test analytics overview endpoint"""
    response = client.get("/api/analytics/overview")
    assert response.status_code == 200
    data = response.json()
    assert "total_wallets_analyzed" in data
    assert "total_transactions" in data

def test_invalid_address():
    """Test with invalid address"""
    response = client.get("/api/wallets/invalid_address")
    # Should return error for invalid address
    assert response.status_code in [400, 500]
