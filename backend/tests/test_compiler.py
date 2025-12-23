"""Tests for the model compiler."""

import pytest

from src.simulation.compiler import ModelCompiler, CompiledModel
from src.models.block import Block, Connection
from src.models.model import Model


class TestModelCompiler:
    """Tests for the ModelCompiler class."""

    def test_compile_empty_model(self):
        """Test compiling an empty model fails."""
        compiler = ModelCompiler()
        model = Model(id="test", name="Empty", blocks=[], connections=[])

        result = compiler.compile(model)

        assert not result.success
        assert "no blocks" in result.message.lower()

    def test_compile_simple_model(self):
        """Test compiling a simple model with one block."""
        compiler = ModelCompiler()

        blocks = [
            Block(
                id="const-1",
                type="constant",
                name="Constant",
                position={"x": 0, "y": 0},
                parameters={"value": 5.0},
                input_ports=[],
                output_ports=[{"id": "const-1-out-0", "name": "out"}],
            )
        ]
        model = Model(id="test", name="Simple", blocks=blocks, connections=[])

        result = compiler.compile(model)

        assert result.success
        assert len(result.blocks) == 1
        assert result.blocks[0].type == "constant"

    def test_compile_connected_blocks(self):
        """Test compiling connected blocks with proper execution order."""
        compiler = ModelCompiler()

        blocks = [
            Block(
                id="const-1",
                type="constant",
                name="Constant",
                position={"x": 0, "y": 0},
                parameters={"value": 5.0},
                input_ports=[],
                output_ports=[{"id": "const-1-out-0", "name": "out"}],
            ),
            Block(
                id="gain-1",
                type="gain",
                name="Gain",
                position={"x": 100, "y": 0},
                parameters={"gain": 2.0},
                input_ports=[{"id": "gain-1-in-0", "name": "in"}],
                output_ports=[{"id": "gain-1-out-0", "name": "out"}],
            ),
        ]
        connections = [
            Connection(
                id="conn-1",
                source_block_id="const-1",
                source_port_id="const-1-out-0",
                target_block_id="gain-1",
                target_port_id="gain-1-in-0",
            )
        ]
        model = Model(id="test", name="Connected", blocks=blocks, connections=connections)

        result = compiler.compile(model)

        assert result.success
        assert len(result.blocks) == 2
        # Constant should be executed before Gain
        const_order = next(b.execution_order for b in result.blocks if b.type == "constant")
        gain_order = next(b.execution_order for b in result.blocks if b.type == "gain")
        assert const_order < gain_order

    def test_connection_format_includes_target_port(self):
        """Test that compiled connections include target port ID."""
        compiler = ModelCompiler()

        blocks = [
            Block(
                id="const-1",
                type="constant",
                name="Constant",
                position={"x": 0, "y": 0},
                parameters={"value": 5.0},
                input_ports=[],
                output_ports=[{"id": "const-1-out-0", "name": "out"}],
            ),
            Block(
                id="scope-1",
                type="scope",
                name="Scope",
                position={"x": 200, "y": 0},
                parameters={"numInputs": 2},
                input_ports=[
                    {"id": "scope-1-in-0", "name": "in1"},
                    {"id": "scope-1-in-1", "name": "in2"},
                ],
                output_ports=[],
            ),
        ]
        connections = [
            Connection(
                id="conn-1",
                source_block_id="const-1",
                source_port_id="const-1-out-0",
                target_block_id="scope-1",
                target_port_id="scope-1-in-1",  # Connect to second port
            )
        ]
        model = Model(id="test", name="PortTest", blocks=blocks, connections=connections)

        result = compiler.compile(model)

        assert result.success
        scope_block = next(b for b in result.blocks if b.type == "scope")
        assert len(scope_block.input_connections) == 1
        # Connection should include target port info
        assert "@scope-1-in-1" in scope_block.input_connections[0]

    def test_detect_algebraic_loop(self):
        """Test that algebraic loops are detected."""
        compiler = ModelCompiler()

        # Create a loop: A -> B -> A (without state-holding blocks)
        blocks = [
            Block(
                id="gain-1",
                type="gain",
                name="Gain1",
                position={"x": 0, "y": 0},
                parameters={"gain": 2.0},
                input_ports=[{"id": "gain-1-in-0", "name": "in"}],
                output_ports=[{"id": "gain-1-out-0", "name": "out"}],
            ),
            Block(
                id="gain-2",
                type="gain",
                name="Gain2",
                position={"x": 100, "y": 0},
                parameters={"gain": 0.5},
                input_ports=[{"id": "gain-2-in-0", "name": "in"}],
                output_ports=[{"id": "gain-2-out-0", "name": "out"}],
            ),
        ]
        connections = [
            Connection(
                id="conn-1",
                source_block_id="gain-1",
                source_port_id="gain-1-out-0",
                target_block_id="gain-2",
                target_port_id="gain-2-in-0",
            ),
            Connection(
                id="conn-2",
                source_block_id="gain-2",
                source_port_id="gain-2-out-0",
                target_block_id="gain-1",
                target_port_id="gain-1-in-0",
            ),
        ]
        model = Model(id="test", name="Loop", blocks=blocks, connections=connections)

        result = compiler.compile(model)

        assert not result.success
        assert "algebraic loop" in result.message.lower()

    def test_no_loop_with_integrator(self):
        """Test that feedback through integrator is not an algebraic loop."""
        compiler = ModelCompiler()

        # Create a feedback loop with an integrator (valid for control systems)
        blocks = [
            Block(
                id="sum-1",
                type="sum",
                name="Sum",
                position={"x": 0, "y": 0},
                parameters={"signs": "+-"},
                input_ports=[
                    {"id": "sum-1-in-0", "name": "in1"},
                    {"id": "sum-1-in-1", "name": "in2"},
                ],
                output_ports=[{"id": "sum-1-out-0", "name": "out"}],
            ),
            Block(
                id="int-1",
                type="integrator",
                name="Integrator",
                position={"x": 100, "y": 0},
                parameters={"initialCondition": 0.0},
                input_ports=[{"id": "int-1-in-0", "name": "in"}],
                output_ports=[{"id": "int-1-out-0", "name": "out"}],
            ),
        ]
        connections = [
            Connection(
                id="conn-1",
                source_block_id="sum-1",
                source_port_id="sum-1-out-0",
                target_block_id="int-1",
                target_port_id="int-1-in-0",
            ),
            Connection(
                id="conn-2",
                source_block_id="int-1",
                source_port_id="int-1-out-0",
                target_block_id="sum-1",
                target_port_id="sum-1-in-1",
            ),
        ]
        model = Model(id="test", name="Feedback", blocks=blocks, connections=connections)

        result = compiler.compile(model)

        # Should succeed because integrator breaks the algebraic loop
        assert result.success
