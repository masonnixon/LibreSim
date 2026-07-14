"""API regressions for simulation block-construction failures."""

import time
from typing import Any

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def reset_simulation_runner():
    """Keep the module-level runner from leaking into or out of these tests."""
    from src.api.routes import simulation as simulation_routes

    simulation_routes._runner = None
    yield
    simulation_routes._runner = None


def _single_block_model(
    *, block_id: str, block_type: str, parameters: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Build the smallest API-valid model that reaches adapter initialization."""
    return {
        "id": f"{block_id}-model",
        "metadata": {"name": "Block construction failure"},
        "blocks": [
            {
                "id": block_id,
                "type": block_type,
                "name": "Failing block",
                "position": {"x": 100, "y": 100},
                "parameters": parameters or {},
                "inputPorts": [],
                "outputPorts": [],
            }
        ],
        "connections": [],
    }


def _wait_for_terminal_status(test_client: TestClient) -> dict[str, Any]:
    """Poll the public status endpoint until the background run terminates."""
    deadline = time.monotonic() + 1.0
    while time.monotonic() < deadline:
        response = test_client.get("/api/simulate/status")
        assert response.status_code == 200
        status = response.json()
        if status["status"] in {"completed", "error", "idle"}:
            return status
        time.sleep(0.01)
    pytest.fail("simulation did not reach a terminal status")


def _assert_api_construction_error(
    test_client: TestClient,
    simulation_config: dict[str, Any],
    *,
    model: dict[str, Any],
    block_id: str,
    block_type: str,
) -> None:
    start_response = test_client.post(
        "/api/simulate/start",
        json={"model": model, "config": simulation_config},
    )
    assert start_response.status_code == 200
    assert "sessionId" in start_response.json()

    status = _wait_for_terminal_status(test_client)
    assert status["status"] == "error"
    assert block_id in status["error"]
    assert block_type in status["error"]

    results_response = test_client.get("/api/simulate/results")
    assert results_response.status_code == 200
    results = results_response.json()
    assert results["signals"] == []
    assert results["analyses"] == {}
    assert results["statistics"]["totalSteps"] == 0
    assert results["statistics"]["finalTime"] == 0.0


def test_unknown_block_failure_reaches_api_status(
    test_client: TestClient, simulation_config: dict[str, Any]
) -> None:
    """Unknown block types terminate with an actionable public error."""
    block_id = "unknown-block-1"
    block_type = "does_not_exist"

    _assert_api_construction_error(
        test_client,
        simulation_config,
        model=_single_block_model(block_id=block_id, block_type=block_type),
        block_id=block_id,
        block_type=block_type,
    )


def test_constructor_failure_reaches_api_status(
    test_client: TestClient, simulation_config: dict[str, Any]
) -> None:
    """Externally supplied invalid constructor data retains block context."""
    block_id = "invalid-transfer-function-1"
    block_type = "transfer_function"

    _assert_api_construction_error(
        test_client,
        simulation_config,
        model=_single_block_model(
            block_id=block_id,
            block_type=block_type,
            # Parameters are intentionally arbitrary JSON at the Pydantic boundary.
            # A scalar denominator therefore reaches TransferFunction.__init__,
            # which requires a coefficient sequence and raises TypeError.
            parameters={"numerator": [1.0], "denominator": 1.0},
        ),
        block_id=block_id,
        block_type=block_type,
    )
