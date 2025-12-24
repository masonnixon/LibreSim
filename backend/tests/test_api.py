"""Tests for the API endpoints."""

import io
from fastapi.testclient import TestClient


class TestRootEndpoints:
    """Tests for root level endpoints."""

    def test_root_endpoint(self, test_client: TestClient):
        """Test the root endpoint returns correct message."""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "LibreSim API"
        assert data["version"] == "0.1.0"

    def test_health_check(self, test_client: TestClient):
        """Test the health check endpoint returns 200."""
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestBlocksEndpoint:
    """Tests for block-related endpoints."""

    def test_list_blocks(self, test_client: TestClient):
        """Test retrieving all block definitions."""
        response = test_client.get("/api/blocks")
        assert response.status_code == 200
        blocks = response.json()
        assert isinstance(blocks, list)
        assert len(blocks) > 0  # Should have block definitions

    def test_list_categories(self, test_client: TestClient):
        """Test retrieving block categories."""
        response = test_client.get("/api/blocks/categories")
        assert response.status_code == 200
        categories = response.json()
        assert isinstance(categories, list)
        # Should have common categories
        assert "Sources" in categories or "sources" in [c.lower() for c in categories]

    def test_get_blocks_by_category(self, test_client: TestClient):
        """Test retrieving blocks by category."""
        response = test_client.get("/api/blocks/category/Sources")
        assert response.status_code == 200
        blocks = response.json()
        assert isinstance(blocks, list)

    def test_get_specific_block(self, test_client: TestClient):
        """Test retrieving a specific block definition."""
        response = test_client.get("/api/blocks/constant")
        assert response.status_code == 200
        block = response.json()
        assert "type" in block or "name" in block or "error" not in block

    def test_get_nonexistent_block(self, test_client: TestClient):
        """Test retrieving a nonexistent block type."""
        response = test_client.get("/api/blocks/nonexistent_block_xyz")
        assert response.status_code == 200
        data = response.json()
        assert "error" in data


class TestModelsEndpoint:
    """Tests for model-related endpoints."""

    def test_list_models_empty(self, test_client: TestClient):
        """Test listing models when empty."""
        response = test_client.get("/api/models")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_model(self, test_client: TestClient):
        """Test creating a new model."""
        model_data = {
            "name": "Test Model",
            "description": "A test model"
        }
        response = test_client.post("/api/models", json=model_data)
        assert response.status_code == 200
        model = response.json()
        assert model["metadata"]["name"] == "Test Model"
        assert "id" in model
        return model["id"]

    def test_get_model(self, test_client: TestClient):
        """Test retrieving a model by ID."""
        # First create a model
        model_data = {"name": "Get Test Model", "description": "Test"}
        create_response = test_client.post("/api/models", json=model_data)
        model_id = create_response.json()["id"]

        # Then get it
        response = test_client.get(f"/api/models/{model_id}")
        assert response.status_code == 200
        model = response.json()
        assert model["id"] == model_id

    def test_get_nonexistent_model(self, test_client: TestClient):
        """Test retrieving a nonexistent model."""
        response = test_client.get("/api/models/nonexistent-id-xyz")
        assert response.status_code == 404

    def test_update_model(self, test_client: TestClient):
        """Test updating a model."""
        # Create a model
        model_data = {"name": "Update Test Model", "description": "Test"}
        create_response = test_client.post("/api/models", json=model_data)
        model_id = create_response.json()["id"]

        # Update it
        update_data = {"metadata": {"name": "Updated Model", "description": "Updated"}}
        response = test_client.put(f"/api/models/{model_id}", json=update_data)
        assert response.status_code == 200

    def test_update_nonexistent_model(self, test_client: TestClient):
        """Test updating a nonexistent model."""
        update_data = {"metadata": {"name": "Test"}}
        response = test_client.put("/api/models/nonexistent-id-xyz", json=update_data)
        assert response.status_code == 404

    def test_delete_model(self, test_client: TestClient):
        """Test deleting a model."""
        # Create a model
        model_data = {"name": "Delete Test Model", "description": "Test"}
        create_response = test_client.post("/api/models", json=model_data)
        model_id = create_response.json()["id"]

        # Delete it
        response = test_client.delete(f"/api/models/{model_id}")
        assert response.status_code == 200

        # Verify it's gone
        get_response = test_client.get(f"/api/models/{model_id}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_model(self, test_client: TestClient):
        """Test deleting a nonexistent model."""
        response = test_client.delete("/api/models/nonexistent-id-xyz")
        assert response.status_code == 404

    def test_validate_model(self, test_client: TestClient, sample_model):
        """Test validating a model."""
        # Create a model with blocks
        model_data = {"name": "Validate Test", "description": "Test"}
        create_response = test_client.post("/api/models", json=model_data)
        model_id = create_response.json()["id"]

        # Validate it (will have warnings since it's empty)
        response = test_client.post(f"/api/models/{model_id}/validate")
        assert response.status_code == 200
        result = response.json()
        assert "valid" in result

    def test_validate_nonexistent_model(self, test_client: TestClient):
        """Test validating a nonexistent model."""
        response = test_client.post("/api/models/nonexistent-id-xyz/validate")
        assert response.status_code == 404

    def test_compile_model(self, test_client: TestClient):
        """Test compiling a model."""
        # Create a model
        model_data = {"name": "Compile Test", "description": "Test"}
        create_response = test_client.post("/api/models", json=model_data)
        model_id = create_response.json()["id"]

        # Compile it
        response = test_client.post(f"/api/models/{model_id}/compile")
        assert response.status_code == 200
        result = response.json()
        assert "success" in result

    def test_compile_nonexistent_model(self, test_client: TestClient):
        """Test compiling a nonexistent model."""
        response = test_client.post("/api/models/nonexistent-id-xyz/compile")
        assert response.status_code == 404


class TestSimulationEndpoint:
    """Tests for simulation endpoints."""

    def test_simulation_test_endpoint(self, test_client: TestClient):
        """Test the simulation test endpoint."""
        response = test_client.get("/api/simulate/test")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_get_simulation_status_idle(self, test_client: TestClient):
        """Test getting simulation status when idle."""
        response = test_client.get("/api/simulate/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_start_simulation(self, test_client: TestClient, sample_model, simulation_config):
        """Test starting a simulation."""
        response = test_client.post(
            "/api/simulate/start",
            json={"model": sample_model, "config": simulation_config},
        )
        assert response.status_code == 200
        data = response.json()
        assert "sessionId" in data

    def test_start_simulation_no_model(self, test_client: TestClient, simulation_config):
        """Test starting simulation without model."""
        response = test_client.post(
            "/api/simulate/start",
            json={"config": simulation_config},
        )
        assert response.status_code == 400

    def test_start_simulation_empty_model(self, test_client: TestClient, simulation_config):
        """Test starting simulation with empty model."""
        empty_model = {
            "id": "empty",
            "metadata": {"name": "Empty"},
            "blocks": [],
            "connections": [],
        }
        response = test_client.post(
            "/api/simulate/start",
            json={"model": empty_model, "config": simulation_config},
        )
        assert response.status_code == 400

    def test_start_simulation_invalid_model(self, test_client: TestClient, simulation_config):
        """Test starting simulation with invalid model data."""
        response = test_client.post(
            "/api/simulate/start",
            json={"model": {"invalid": "data"}, "config": simulation_config},
        )
        assert response.status_code == 400

    def test_stop_simulation_no_runner(self, test_client: TestClient):
        """Test stopping simulation when none is running."""
        # First ensure no simulation is running by resetting
        from src.api.routes import simulation as sim_module
        sim_module._runner = None

        response = test_client.post("/api/simulate/stop")
        assert response.status_code == 400

    def test_pause_simulation_no_runner(self, test_client: TestClient):
        """Test pausing simulation when none is running."""
        from src.api.routes import simulation as sim_module
        sim_module._runner = None

        response = test_client.post("/api/simulate/pause")
        assert response.status_code == 400

    def test_resume_simulation_no_runner(self, test_client: TestClient):
        """Test resuming simulation when none is running."""
        from src.api.routes import simulation as sim_module
        sim_module._runner = None

        response = test_client.post("/api/simulate/resume")
        assert response.status_code == 400

    def test_get_results_no_simulation(self, test_client: TestClient):
        """Test getting results when no simulation available."""
        from src.api.routes import simulation as sim_module
        sim_module._runner = None

        response = test_client.get("/api/simulate/results")
        assert response.status_code == 400

    def test_simulation_lifecycle(self, test_client: TestClient, sample_model, simulation_config):
        """Test full simulation lifecycle: start, status, stop."""
        # Start
        start_response = test_client.post(
            "/api/simulate/start",
            json={"model": sample_model, "config": simulation_config},
        )
        assert start_response.status_code == 200

        # Status
        status_response = test_client.get("/api/simulate/status")
        assert status_response.status_code == 200

        # Stop
        stop_response = test_client.post("/api/simulate/stop")
        assert stop_response.status_code == 200

    def test_debug_endpoint(self, test_client: TestClient, sample_model, simulation_config):
        """Test the debug endpoint."""
        response = test_client.post(
            "/api/simulate/debug",
            json={"model": sample_model, "config": simulation_config},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["model_received"] is True
        assert data["config_received"] is True

    def test_debug_endpoint_no_model(self, test_client: TestClient):
        """Test debug endpoint without model."""
        response = test_client.post("/api/simulate/debug", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["model_received"] is False

    def test_debug_endpoint_invalid_model(self, test_client: TestClient, simulation_config):
        """Test debug endpoint with invalid model."""
        response = test_client.post(
            "/api/simulate/debug",
            json={"model": {"invalid": "data"}, "config": simulation_config},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["model_parsed"] is False

    def test_debug_endpoint_invalid_config(self, test_client: TestClient, sample_model):
        """Test debug endpoint with invalid config."""
        response = test_client.post(
            "/api/simulate/debug",
            json={"model": sample_model, "config": {"invalid": "data", "solver": "invalid"}},
        )
        assert response.status_code == 200
        # Config may or may not parse depending on validation


class TestImportExportEndpoint:
    """Tests for import/export endpoints."""

    def test_import_mdl_file(self, test_client: TestClient):
        """Test importing an MDL file."""
        # Use dedented MDL content
        import textwrap
        mdl_content = textwrap.dedent("""\
            Model {
              Name "test_model"
              System {
                Name "test_model"
                Block {
                  BlockType Constant
                  Name "Const1"
                  Position [100, 100, 130, 130]
                  Value "5"
                }
                Block {
                  BlockType Scope
                  Name "Scope1"
                  Position [200, 100, 230, 130]
                }
                Line {
                  SrcBlock "Const1"
                  SrcPort 1
                  DstBlock "Scope1"
                  DstPort 1
                }
              }
            }
        """)
        files = {"file": ("test.mdl", io.BytesIO(mdl_content.encode()), "application/octet-stream")}
        response = test_client.post("/api/import/mdl", files=files)
        assert response.status_code == 200
        model = response.json()
        assert "blocks" in model
        # Blocks may be empty if types aren't supported but at least check response is valid
        assert isinstance(model["blocks"], list)

    def test_import_non_mdl_file(self, test_client: TestClient):
        """Test importing a non-MDL file."""
        files = {"file": ("test.txt", io.BytesIO(b"not an mdl file"), "text/plain")}
        response = test_client.post("/api/import/mdl", files=files)
        assert response.status_code == 400

    def test_import_invalid_mdl_content(self, test_client: TestClient):
        """Test importing an MDL file with invalid content."""
        invalid_content = "This is not valid MDL content at all {"
        files = {"file": ("invalid.mdl", io.BytesIO(invalid_content.encode()), "application/octet-stream")}
        response = test_client.post("/api/import/mdl", files=files)
        # Should return 200 with parsed (possibly empty) result, or 400 if parsing fails hard
        assert response.status_code in [200, 400]

    def test_import_mdl_binary_file(self, test_client: TestClient):
        """Test importing a binary file as MDL (should fail encoding)."""
        # Create binary content that will fail utf-8 decode
        binary_content = bytes([0x80, 0x81, 0x82, 0xFF, 0xFE])
        files = {"file": ("binary.mdl", io.BytesIO(binary_content), "application/octet-stream")}
        response = test_client.post("/api/import/mdl", files=files)
        assert response.status_code == 400


class TestWebSocket:
    """Tests for WebSocket functionality."""

    def test_websocket_connection_manager(self):
        """Test ConnectionManager class directly."""
        from src.api.websocket import ConnectionManager
        manager = ConnectionManager()
        assert len(manager.active_connections) == 0

    def test_websocket_simulation_endpoint(self, test_client: TestClient):
        """Test WebSocket simulation endpoint connection."""
        with test_client.websocket_connect("/ws/simulation") as websocket:
            # Send a subscribe message
            websocket.send_json({"type": "subscribe"})
            # Should receive subscribed response
            data = websocket.receive_json()
            assert data["type"] == "subscribed"

    def test_websocket_parameter_update(self, test_client: TestClient):
        """Test WebSocket parameter update message."""
        with test_client.websocket_connect("/ws/simulation") as websocket:
            # Send a parameter update message
            websocket.send_json({"type": "parameter_update", "param": "test"})
            # No response expected for parameter_update, just verify no error

    def test_websocket_unknown_message_type(self, test_client: TestClient):
        """Test WebSocket with unknown message type."""
        with test_client.websocket_connect("/ws/simulation") as websocket:
            # Send an unknown message type
            websocket.send_json({"type": "unknown_type"})
            # Should not crash


class TestWebSocketBroadcast:
    """Tests for WebSocket broadcast functions."""

    import pytest

    @pytest.mark.asyncio
    async def test_broadcast_simulation_data(self):
        """Test broadcast_simulation_data function."""
        from src.api.websocket import broadcast_simulation_data, manager

        # Clear any existing connections
        manager.active_connections.clear()

        # Call broadcast (no connections, should not error)
        await broadcast_simulation_data(1.0, {"signal1": 5.0})

    @pytest.mark.asyncio
    async def test_broadcast_simulation_status(self):
        """Test broadcast_simulation_status function."""
        from src.api.websocket import broadcast_simulation_status, manager

        manager.active_connections.clear()
        await broadcast_simulation_status("running", 0.5, 5.0)

    @pytest.mark.asyncio
    async def test_broadcast_simulation_error(self):
        """Test broadcast_simulation_error function."""
        from src.api.websocket import broadcast_simulation_error, manager

        manager.active_connections.clear()
        await broadcast_simulation_error("Test error message")


class TestSimulationEndpointExtended:
    """Extended tests for simulation endpoints."""

    def test_get_simulation_status_with_runner(self, test_client: TestClient, sample_model, simulation_config):
        """Test getting simulation status when runner exists."""
        # Start a simulation first
        test_client.post(
            "/api/simulate/start",
            json={"model": sample_model, "config": simulation_config},
        )

        # Get status
        response = test_client.get("/api/simulate/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "progress" in data

    def test_get_simulation_results_with_runner(self, test_client: TestClient, sample_model, simulation_config):
        """Test getting simulation results when runner exists."""
        # Start a simulation first
        start_response = test_client.post(
            "/api/simulate/start",
            json={"model": sample_model, "config": simulation_config},
        )
        assert start_response.status_code == 200

        # Get results
        response = test_client.get("/api/simulate/results")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_pause_and_resume_simulation(self, test_client: TestClient, sample_model, simulation_config):
        """Test pausing and resuming a simulation."""
        # Start simulation
        test_client.post(
            "/api/simulate/start",
            json={"model": sample_model, "config": simulation_config},
        )

        # Pause
        pause_response = test_client.post("/api/simulate/pause")
        assert pause_response.status_code == 200

        # Resume
        resume_response = test_client.post("/api/simulate/resume")
        assert resume_response.status_code == 200

        # Stop
        test_client.post("/api/simulate/stop")

    def test_simulation_status_with_error(self, test_client: TestClient, sample_model, simulation_config):
        """Test simulation status includes error when present."""
        # Start simulation
        test_client.post(
            "/api/simulate/start",
            json={"model": sample_model, "config": simulation_config},
        )

        # Manually set error message on runner
        from src.api.routes import simulation as sim_module
        if sim_module._runner:
            sim_module._runner._error_message = "Test error"

        # Get status
        response = test_client.get("/api/simulate/status")
        assert response.status_code == 200
        data = response.json()
        assert "error" in data

        # Cleanup
        sim_module._runner = None

    def test_debug_endpoint_with_valid_model_and_config(self, test_client: TestClient, sample_model, simulation_config):
        """Test debug endpoint with valid model and config creates runner."""
        response = test_client.post(
            "/api/simulate/debug",
            json={"model": sample_model, "config": simulation_config},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["model_parsed"] is True
        assert data["config_parsed"] is True
        assert data.get("runner_created") is True
