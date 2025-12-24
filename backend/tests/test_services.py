"""Tests for model_service and related services."""

import pytest

from src.models.block import Block, Connection, Port, Position
from src.models.model import Model, ModelCreate, ModelMetadata, ModelUpdate
from src.models.simulation import SimulationConfig
from src.services.model_service import ModelService


class TestModelService:
    """Tests for the ModelService class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ModelService()
        # Clear any existing models
        self.service._models.clear()

    def test_list_models_empty(self):
        """Test listing models when none exist."""
        result = self.service.list_models()
        assert result == []

    def test_create_model(self):
        """Test creating a new model."""
        data = ModelCreate(name="Test Model", description="A test model")
        model = self.service.create_model(data)

        assert model.id is not None
        assert model.metadata.name == "Test Model"
        assert model.metadata.description == "A test model"
        assert model.blocks == []
        assert model.connections == []
        assert model.simulation_config is not None

    def test_list_models_after_create(self):
        """Test listing models after creating one."""
        data = ModelCreate(name="Test Model", description="A test model")
        self.service.create_model(data)

        result = self.service.list_models()
        assert len(result) == 1
        assert result[0].metadata.name == "Test Model"

    def test_get_model(self):
        """Test getting a model by ID."""
        data = ModelCreate(name="Test Model", description="A test model")
        created = self.service.create_model(data)

        result = self.service.get_model(created.id)
        assert result is not None
        assert result.id == created.id
        assert result.metadata.name == "Test Model"

    def test_get_model_not_found(self):
        """Test getting a model that doesn't exist."""
        result = self.service.get_model("nonexistent-id")
        assert result is None

    def test_update_model(self):
        """Test updating an existing model."""
        data = ModelCreate(name="Test Model", description="A test model")
        created = self.service.create_model(data)

        # Create update with new metadata
        new_metadata = ModelMetadata(
            name="Updated Model",
            description="Updated description",
            createdAt=created.metadata.created_at,
            modifiedAt=created.metadata.modified_at,
        )
        update = ModelUpdate(metadata=new_metadata)
        result = self.service.update_model(created.id, update)

        assert result is not None
        assert result.metadata.name == "Updated Model"
        assert result.metadata.description == "Updated description"

    def test_update_model_blocks(self):
        """Test updating model blocks."""
        data = ModelCreate(name="Test Model", description="A test model")
        created = self.service.create_model(data)

        # Create a block
        block = Block(
            id="block-1",
            type="constant",
            name="Constant1",
            position=Position(x=100, y=100),
            parameters={"value": 5.0},
            inputPorts=[],
            outputPorts=[Port(id="block-1-out-0", name="out", dataType="double", dimensions=[1])],
        )

        update = ModelUpdate(blocks=[block])
        result = self.service.update_model(created.id, update)

        assert result is not None
        assert len(result.blocks) == 1
        assert result.blocks[0].name == "Constant1"

    def test_update_model_connections(self):
        """Test updating model connections."""
        data = ModelCreate(name="Test Model", description="A test model")
        created = self.service.create_model(data)

        connection = Connection(
            id="conn-1",
            sourceBlockId="block-1",
            sourcePortId="block-1-out-0",
            targetBlockId="block-2",
            targetPortId="block-2-in-0",
        )

        update = ModelUpdate(connections=[connection])
        result = self.service.update_model(created.id, update)

        assert result is not None
        assert len(result.connections) == 1

    def test_update_model_simulation_config(self):
        """Test updating simulation config."""
        data = ModelCreate(name="Test Model", description="A test model")
        created = self.service.create_model(data)

        new_config = SimulationConfig(
            solver="euler",
            startTime=0.0,
            stopTime=20.0,
            stepSize=0.001,
        )

        update = ModelUpdate(simulationConfig=new_config)
        result = self.service.update_model(created.id, update)

        assert result is not None
        assert result.simulation_config.stop_time == 20.0
        assert result.simulation_config.step_size == 0.001

    def test_update_model_not_found(self):
        """Test updating a model that doesn't exist."""
        update = ModelUpdate()
        result = self.service.update_model("nonexistent-id", update)
        assert result is None

    def test_delete_model(self):
        """Test deleting a model."""
        data = ModelCreate(name="Test Model", description="A test model")
        created = self.service.create_model(data)

        result = self.service.delete_model(created.id)
        assert result is True

        # Verify it's gone
        assert self.service.get_model(created.id) is None

    def test_delete_model_not_found(self):
        """Test deleting a model that doesn't exist."""
        result = self.service.delete_model("nonexistent-id")
        assert result is False

    def test_validate_model_empty(self):
        """Test validating an empty model."""
        model = Model(
            id="model-1",
            metadata=ModelMetadata(name="Empty Model"),
            blocks=[],
            connections=[],
            simulationConfig=SimulationConfig(),
        )

        result = self.service.validate_model(model)
        assert result["valid"] is False
        assert "Model has no blocks" in result["errors"]

    def test_validate_model_unconnected_input(self):
        """Test validating a model with unconnected required input."""
        gain_block = Block(
            id="gain-1",
            type="gain",
            name="Gain1",
            position=Position(x=100, y=100),
            parameters={"gain": 2.0},
            inputPorts=[Port(id="gain-1-in-0", name="in", dataType="double", dimensions=[1])],
            outputPorts=[Port(id="gain-1-out-0", name="out", dataType="double", dimensions=[1])],
        )

        model = Model(
            id="model-1",
            metadata=ModelMetadata(name="Test Model"),
            blocks=[gain_block],
            connections=[],
            simulationConfig=SimulationConfig(),
        )

        result = self.service.validate_model(model)
        assert result["valid"] is False
        assert any("unconnected input" in err for err in result["errors"])

    def test_validate_model_source_block_no_input(self):
        """Test that source blocks don't require input connections."""
        const_block = Block(
            id="const-1",
            type="constant",
            name="Constant1",
            position=Position(x=100, y=100),
            parameters={"value": 5.0},
            inputPorts=[],
            outputPorts=[Port(id="const-1-out-0", name="out", dataType="double", dimensions=[1])],
        )

        scope_block = Block(
            id="scope-1",
            type="scope",
            name="Scope1",
            position=Position(x=200, y=100),
            parameters={},
            inputPorts=[Port(id="scope-1-in-0", name="in", dataType="double", dimensions=[1])],
            outputPorts=[],
        )

        conn = Connection(
            id="conn-1",
            sourceBlockId="const-1",
            sourcePortId="const-1-out-0",
            targetBlockId="scope-1",
            targetPortId="scope-1-in-0",
        )

        model = Model(
            id="model-1",
            metadata=ModelMetadata(name="Test Model"),
            blocks=[const_block, scope_block],
            connections=[conn],
            simulationConfig=SimulationConfig(),
        )

        result = self.service.validate_model(model)
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_model_unused_output_warning(self):
        """Test that unused outputs generate warnings."""
        const_block = Block(
            id="const-1",
            type="constant",
            name="Constant1",
            position=Position(x=100, y=100),
            parameters={"value": 5.0},
            inputPorts=[],
            outputPorts=[Port(id="const-1-out-0", name="out", dataType="double", dimensions=[1])],
        )

        # A gain block with input but no output connected
        gain_block = Block(
            id="gain-1",
            type="gain",
            name="Gain1",
            position=Position(x=200, y=100),
            parameters={"gain": 2.0},
            inputPorts=[Port(id="gain-1-in-0", name="in", dataType="double", dimensions=[1])],
            outputPorts=[Port(id="gain-1-out-0", name="out", dataType="double", dimensions=[1])],
        )

        conn = Connection(
            id="conn-1",
            sourceBlockId="const-1",
            sourcePortId="const-1-out-0",
            targetBlockId="gain-1",
            targetPortId="gain-1-in-0",
        )

        model = Model(
            id="model-1",
            metadata=ModelMetadata(name="Test Model"),
            blocks=[const_block, gain_block],
            connections=[conn],
            simulationConfig=SimulationConfig(),
        )

        result = self.service.validate_model(model)
        assert result["valid"] is True
        # Gain output is unused, should generate warning
        assert any("not connected" in warn for warn in result["warnings"])

    def test_compile_model_valid(self):
        """Test compiling a valid model."""
        const_block = Block(
            id="const-1",
            type="constant",
            name="Constant1",
            position=Position(x=100, y=100),
            parameters={"value": 5.0},
            inputPorts=[],
            outputPorts=[Port(id="const-1-out-0", name="out", dataType="double", dimensions=[1])],
        )

        scope_block = Block(
            id="scope-1",
            type="scope",
            name="Scope1",
            position=Position(x=200, y=100),
            parameters={},
            inputPorts=[Port(id="scope-1-in-0", name="in", dataType="double", dimensions=[1])],
            outputPorts=[],
        )

        conn = Connection(
            id="conn-1",
            sourceBlockId="const-1",
            sourcePortId="const-1-out-0",
            targetBlockId="scope-1",
            targetPortId="scope-1-in-0",
        )

        model = Model(
            id="model-1",
            metadata=ModelMetadata(name="Test Model"),
            blocks=[const_block, scope_block],
            connections=[conn],
            simulationConfig=SimulationConfig(),
        )

        result = self.service.compile_model(model)
        assert result["success"] is True
        assert result["blockCount"] == 2
        assert result["connectionCount"] == 1

    def test_compile_model_invalid(self):
        """Test compiling an invalid model."""
        # A gain block with unconnected input
        gain_block = Block(
            id="gain-1",
            type="gain",
            name="Gain1",
            position=Position(x=100, y=100),
            parameters={"gain": 2.0},
            inputPorts=[Port(id="gain-1-in-0", name="in", dataType="double", dimensions=[1])],
            outputPorts=[Port(id="gain-1-out-0", name="out", dataType="double", dimensions=[1])],
        )

        model = Model(
            id="model-1",
            metadata=ModelMetadata(name="Test Model"),
            blocks=[gain_block],
            connections=[],
            simulationConfig=SimulationConfig(),
        )

        result = self.service.compile_model(model)
        assert result["success"] is False
        assert "validation failed" in result["message"]
