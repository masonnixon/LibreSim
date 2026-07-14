"""Tests for the model compiler."""

import pytest
from pydantic import ValidationError

from src.models.block import Block, Connection
from src.models.model import Model, ModelMetadata
from src.models.simulation import SimulationConfig
from src.simulation.compiler import ModelCompiler
from src.simulation.osk_adapter import OSKAdapter


def make_metadata(name: str) -> ModelMetadata:
    """Create a test ModelMetadata instance."""
    return ModelMetadata(name=name)


class TestModelCompiler:
    """Tests for the ModelCompiler class."""

    def test_compile_empty_model(self):
        """Test compiling an empty model fails."""
        compiler = ModelCompiler()
        model = Model(id="test", metadata=make_metadata("Empty"), blocks=[], connections=[])

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
        model = Model(id="test", metadata=make_metadata("Simple"), blocks=blocks, connections=[])

        result = compiler.compile(model)

        assert result.success
        assert len(result.blocks) == 1
        assert result.blocks[0].type == "constant"

    def test_nested_subsystems_are_flattened_recursively(self):
        def make_block(
            block_id: str,
            block_type: str,
            parameters: dict | None = None,
            *,
            num_inputs: int = 1,
            num_outputs: int = 1,
            children: list[Block] | None = None,
            child_connections: list[Connection] | None = None,
        ) -> Block:
            return Block(
                id=block_id,
                type=block_type,
                name=block_id,
                position={"x": 0, "y": 0},
                parameters=parameters or {},
                inputPorts=[
                    {"id": f"{block_id}-in-{index}", "name": "in"}
                    for index in range(num_inputs)
                ],
                outputPorts=[
                    {"id": f"{block_id}-out-{index}", "name": "out"}
                    for index in range(num_outputs)
                ],
                children=children,
                childConnections=child_connections,
            )

        def connect(connection_id: str, source: str, target: str) -> Connection:
            return Connection(
                id=connection_id,
                sourceBlockId=source,
                sourcePortId=f"{source}-out-0",
                targetBlockId=target,
                targetPortId=f"{target}-in-0",
            )

        inner_in = make_block("inner-in", "inport", {"portNumber": 1})
        gain = make_block("gain", "gain", {"gain": 3.0})
        inner_out = make_block("inner-out", "outport", {"portNumber": 1})
        inner = Block(
            id="inner",
            type="subsystem",
            name="Inner",
            position={"x": 0, "y": 0},
            inputPorts=[{"id": "inner-in-0", "name": "in"}],
            outputPorts=[{"id": "inner-out-0", "name": "out"}],
            children=[inner_in, gain, inner_out],
            childConnections=[
                connect("inner-in-to-gain", "inner-in", "gain"),
                connect("gain-to-inner-out", "gain", "inner-out"),
            ],
        )
        outer_in = make_block("outer-in", "inport", {"portNumber": 1})
        outer_out = make_block("outer-out", "outport", {"portNumber": 1})
        outer = Block(
            id="outer",
            type="subsystem",
            name="Outer",
            position={"x": 0, "y": 0},
            inputPorts=[{"id": "outer-in-0", "name": "in"}],
            outputPorts=[{"id": "outer-out-0", "name": "out"}],
            children=[outer_in, inner, outer_out],
            childConnections=[
                connect("outer-in-to-inner", "outer-in", "inner"),
                connect("inner-to-outer-out", "inner", "outer-out"),
            ],
        )
        source = make_block(
            "source", "constant", {"value": 4.0}, num_inputs=0
        )
        scope = make_block("scope", "scope", num_outputs=0)
        model = Model(
            id="nested",
            metadata=make_metadata("Nested"),
            blocks=[source, outer, scope],
            connections=[
                connect("source-to-outer", "source", "outer"),
                connect("outer-to-scope", "outer", "scope"),
            ],
            simulationConfig=SimulationConfig(stopTime=0.1, stepSize=0.1),
        )

        compiler = ModelCompiler()
        flattened_blocks, flattened_connections = compiler._flatten_subsystems(
            model.blocks, model.connections
        )
        expected_order = [
            "source",
            "outer__outer-in",
            "outer__inner__inner-in",
            "outer__inner__gain",
            "outer__inner__inner-out",
            "outer__outer-out",
            "scope",
        ]
        assert [block.id for block in flattened_blocks] == expected_order

        endpoints = {
            (
                connection.source_block_id,
                connection.source_port_id,
                connection.target_block_id,
                connection.target_port_id,
            )
            for connection in flattened_connections
        }
        assert endpoints == {
            ("source", "source-out-0", "outer__outer-in", "outer__outer-in-in-0"),
            (
                "outer__outer-in",
                "outer__outer-in-out-0",
                "outer__inner__inner-in",
                "outer__inner__inner-in-in-0",
            ),
            (
                "outer__inner__inner-in",
                "outer__inner__inner-in-out-0",
                "outer__inner__gain",
                "outer__inner__gain-in-0",
            ),
            (
                "outer__inner__gain",
                "outer__inner__gain-out-0",
                "outer__inner__inner-out",
                "outer__inner__inner-out-in-0",
            ),
            (
                "outer__inner__inner-out",
                "outer__inner__inner-out-out-0",
                "outer__outer-out",
                "outer__outer-out-in-0",
            ),
            (
                "outer__outer-out",
                "outer__outer-out-out-0",
                "scope",
                "scope-in-0",
            ),
        }

        result = compiler.compile(model)

        assert result.success
        assert result.execution_order == expected_order

        adapter = OSKAdapter()
        adapter.initialize(result, model.simulation_config)
        outputs = adapter.step(0.0, model.simulation_config.step_size)
        assert list(outputs.values()) == pytest.approx([12.0])

    def test_recursive_block_payload_is_rejected_by_schema(self):
        recursive_block = {
            "id": "recursive",
            "type": "subsystem",
            "name": "Recursive",
            "position": {"x": 0, "y": 0},
        }
        recursive_block["children"] = [recursive_block]

        with pytest.raises(ValidationError) as exc_info:
            Block.model_validate(recursive_block)

        assert exc_info.value.errors()[0]["type"] == "recursion_loop"

    def test_subsystem_boundary_requires_a_parseable_port_index(self):
        """Malformed boundary IDs must not silently connect to subsystem port zero."""
        source = Block(
            id="source",
            type="constant",
            name="Source",
            position={"x": 0, "y": 0},
            parameters={"value": 1.0},
            inputPorts=[],
            outputPorts=[{"id": "custom-source-output", "name": "out"}],
        )
        first_inport = Block(
            id="in-1",
            type="inport",
            name="In 1",
            position={"x": 0, "y": 0},
            parameters={"portNumber": 1},
            inputPorts=[{"id": "in-1-in-0", "name": "in"}],
            outputPorts=[{"id": "in-1-out-0", "name": "out"}],
        )
        second_inport = Block(
            id="in-2",
            type="inport",
            name="In 2",
            position={"x": 0, "y": 0},
            parameters={"portNumber": 2},
            inputPorts=[{"id": "in-2-in-0", "name": "in"}],
            outputPorts=[{"id": "in-2-out-0", "name": "out"}],
        )
        subsystem = Block(
            id="sub",
            type="subsystem",
            name="Subsystem",
            position={"x": 0, "y": 0},
            inputPorts=[
                {"id": "sub-in-0", "name": "in 1"},
                {"id": "sub-in-1", "name": "in 2"},
            ],
            outputPorts=[],
            children=[first_inport, second_inport],
            childConnections=[],
        )
        connections = [
            Connection(
                id="valid-second-port",
                sourceBlockId="source",
                sourcePortId="custom-source-output",
                targetBlockId="sub",
                targetPortId="sub-in-1",
            ),
            Connection(
                id="malformed-boundary",
                sourceBlockId="source",
                sourcePortId="custom-source-output",
                targetBlockId="sub",
                targetPortId="not-an-index",
            ),
        ]

        flattened_blocks, flattened_connections = ModelCompiler()._flatten_subsystems(
            [source, subsystem], connections
        )

        assert next(block for block in flattened_blocks if block.id == "source").output_ports[
            0
        ].id == "custom-source-output"
        assert len(flattened_connections) == 1
        assert flattened_connections[0].source_port_id == "custom-source-output"
        assert flattened_connections[0].target_block_id == "sub__in-2"

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
        model = Model(
            id="test",
            metadata=make_metadata("Connected"),
            blocks=blocks,
            connections=connections,
        )

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
        model = Model(
            id="test",
            metadata=make_metadata("PortTest"),
            blocks=blocks,
            connections=connections,
        )

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
        model = Model(
            id="test",
            metadata=make_metadata("Loop"),
            blocks=blocks,
            connections=connections,
        )

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
        model = Model(
            id="test",
            metadata=make_metadata("Feedback"),
            blocks=blocks,
            connections=connections,
        )

        result = compiler.compile(model)

        # Should succeed because integrator breaks the algebraic loop
        assert result.success
