"""
Integration Tests - API Endpoints
==================================
Test cases cho API endpoints với real database connections

Coverage:
- Health endpoints
- Pipeline endpoints (mocked)
- Data query endpoints
- Authentication

Requirements:
- MongoDB và Redis đang chạy
- Test database được sử dụng (isolated)
"""

# Import pytest
import pytest

# Import FastAPI TestClient
from fastapi.testclient import TestClient

# Import app
from src.main import app

# Create test client
client = TestClient(app)


# ============================================================================
# HEALTH ENDPOINTS TESTS
# ============================================================================

class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_health_endpoint(self):
        """Test: /health trả về healthy status"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_ready_endpoint(self):
        """Test: /ready kiểm tra dependencies"""
        response = client.get("/ready")
        # Có thể 200 hoặc 503 tùy thuộc vào trạng thái
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "checks" in data


# ============================================================================
# PIPELINE ENDPOINTS TESTS
# ============================================================================

class TestPipelineEndpoints:
    """Test pipeline management endpoints (với mocked service)"""
    
    def test_start_pipeline_unauthorized(self):
        """Test: Start pipeline yêu cầu authentication"""
        response = client.post("/api/v1/pipeline/start", json={})
        # Nên trả về 401 hoặc 403 (tùy implementation)
        assert response.status_code in [401, 403, 422]
    
    def test_get_history_unauthorized(self):
        """Test: Get history yêu cầu authentication"""
        response = client.get("/api/v1/pipeline/history")
        assert response.status_code in [401, 403]


# ============================================================================
# DATA QUERY ENDPOINTS TESTS
# ============================================================================

class TestDataQueryEndpoints:
    """Test data query endpoints"""
    
    def test_list_pois_unauthorized(self):
        """Test: List POIs yêu cầu authentication"""
        response = client.get("/api/v1/data/pois")
        assert response.status_code in [401, 403]
    
    def test_get_poi_detail_unauthorized(self):
        """Test: Get POI detail yêu cầu authentication"""
        response = client.get("/api/v1/data/pois/test-id")
        assert response.status_code in [401, 403]


# ============================================================================
# ROOT ENDPOINT TEST
# ============================================================================

class TestRootEndpoint:
    """Test root endpoint"""
    
    def test_root_returns_api_info(self):
        """Test: Root endpoint trả về API information"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "documentation" in data
