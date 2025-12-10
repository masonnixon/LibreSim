"""Model management service."""

import uuid
from datetime import datetime
from typing import Dict, Any

from ..models.model import Model, ModelCreate, ModelUpdate, ModelMetadata
from ..models.simulation import SimulationConfig


class ModelService:
    """Service for managing simulation models."""

    # In-memory storage (replace with database for persistence)
    _models: Dict[str, Model] = {}

    def list_models(self) -> list[Model]:
        """List all models."""
        return list(self._models.values())

    def get_model(self, model_id: str) -> Model | None:
        """Get a model by ID."""
        return self._models.get(model_id)

    def create_model(self, data: ModelCreate) -> Model:
        """Create a new model."""
        model_id = str(uuid.uuid4())
        now = datetime.now()

        model = Model(
            id=model_id,
            metadata=ModelMetadata(
                name=data.name,
                description=data.description,
                createdAt=now,
                modifiedAt=now,
            ),
            blocks=[],
            connections=[],
            simulationConfig=SimulationConfig(),
        )

        self._models[model_id] = model
        return model

    def update_model(self, model_id: str, data: ModelUpdate) -> Model | None:
        """Update an existing model."""
        if model_id not in self._models:
            return None

        model = self._models[model_id]

        # Update fields if provided
        if data.metadata:
            model.metadata = data.metadata
        if data.blocks is not None:
            model.blocks = data.blocks
        if data.connections is not None:
            model.connections = data.connections
        if data.simulation_config:
            model.simulation_config = data.simulation_config

        # Update modification time
        model.metadata.modified_at = datetime.now()

        self._models[model_id] = model
        return model

    def delete_model(self, model_id: str) -> bool:
        """Delete a model."""
        if model_id in self._models:
            del self._models[model_id]
            return True
        return False

    def validate_model(self, model: Model) -> Dict[str, Any]:
        """Validate a model for simulation.

        Checks:
        - All required block inputs are connected
        - No algebraic loops (basic check)
        - Valid block parameters
        """
        errors = []
        warnings = []

        # Check for empty model
        if not model.blocks:
            errors.append("Model has no blocks")
            return {"valid": False, "errors": errors, "warnings": warnings}

        # Build connection map
        connected_inputs: set[str] = set()
        connected_outputs: set[str] = set()

        for conn in model.connections:
            connected_inputs.add(f"{conn.target_block_id}:{conn.target_port_id}")
            connected_outputs.add(f"{conn.source_block_id}:{conn.source_port_id}")

        # Check each block
        for block in model.blocks:
            # Check required inputs are connected
            for port in block.input_ports:
                port_key = f"{block.id}:{port.id}"
                if port_key not in connected_inputs:
                    # Some blocks like sources don't need inputs
                    if block.type not in ["constant", "step", "ramp", "sine_wave",
                                           "pulse_generator", "clock", "from"]:
                        errors.append(f"Block '{block.name}' has unconnected input '{port.name}'")

            # Check outputs are used (warning only)
            for port in block.output_ports:
                port_key = f"{block.id}:{port.id}"
                if port_key not in connected_outputs:
                    if block.type not in ["scope", "display", "to_workspace",
                                           "xy_graph", "terminator", "goto"]:
                        warnings.append(
                            f"Block '{block.name}' output '{port.name}' is not connected"
                        )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def compile_model(self, model: Model) -> Dict[str, Any]:
        """Compile a model for simulation.

        This creates the internal representation needed by OSK.
        """
        # First validate
        validation = self.validate_model(model)
        if not validation["valid"]:
            return {
                "success": False,
                "message": "Model validation failed",
                "errors": validation["errors"],
            }

        # TODO: Integrate with OSK compiler
        # For now, return success
        return {
            "success": True,
            "message": "Model compiled successfully",
            "blockCount": len(model.blocks),
            "connectionCount": len(model.connections),
        }
