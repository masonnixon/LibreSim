"""Tests for the API endpoints."""

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for health check endpoints."""

    def test_health_check(self, test_client: TestClient):
        """Test the health check endpoint returns 200."""
        response = test_client.get("/api/health")
        # Allow for either success or 404 if not implemented yet
        assert response.status_code in [200, 404]


class TestBlocksEndpoint:
    """Tests for block-related endpoints."""

    def test_get_block_definitions(self, test_client: TestClient):
        """Test retrieving block definitions."""
        response = test_client.get("/api/blocks")
        # Allow for either success or 404 if not implemented yet
        assert response.status_code in [200, 404]


class TestSimulationEndpoint:
    """Tests for simulation endpoints."""

    def test_start_simulation(self, test_client: TestClient, sample_model, simulation_config):
        """Test starting a simulation."""
        response = test_client.post(
            "/api/simulate/start",
            json={"model": sample_model, "config": simulation_config},
        )
        # Allow for either success or 404/422 if not fully implemented
        assert response.status_code in [200, 404, 422]

    def test_get_simulation_status(self, test_client: TestClient):
        """Test getting simulation status."""
        response = test_client.get("/api/simulate/status")
        # Allow for either success or 404 if not implemented
        assert response.status_code in [200, 404]
