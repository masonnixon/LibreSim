"""Pytest configuration and fixtures for LibreSim backend tests."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI application."""
    from src.main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture
def sample_model():
    """Create a sample model for testing."""
    return {
        "id": "test-model-1",
        "name": "Test Model",
        "blocks": [
            {
                "id": "const-1",
                "type": "constant",
                "name": "Constant",
                "position": {"x": 100, "y": 100},
                "parameters": {"value": 5.0},
                "inputPorts": [],
                "outputPorts": [{"id": "const-1-out-0", "name": "out"}],
            },
            {
                "id": "scope-1",
                "type": "scope",
                "name": "Scope",
                "position": {"x": 300, "y": 100},
                "parameters": {"numInputs": 1},
                "inputPorts": [{"id": "scope-1-in-0", "name": "in"}],
                "outputPorts": [],
            },
        ],
        "connections": [
            {
                "id": "conn-1",
                "sourceBlockId": "const-1",
                "sourcePortId": "const-1-out-0",
                "targetBlockId": "scope-1",
                "targetPortId": "scope-1-in-0",
            }
        ],
    }


@pytest.fixture
def simulation_config():
    """Create a sample simulation configuration."""
    return {
        "startTime": 0.0,
        "stopTime": 10.0,
        "stepSize": 0.01,
        "solver": "RK4",
    }
