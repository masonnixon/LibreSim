"""Behavioral coverage for simulation compiler edge cases."""

from unittest.mock import Mock

import pytest

from src.models.block import Block, Connection
from src.models.model import Model, ModelMetadata
from src.simulation.compiler import ModelCompiler


def make_block(
    block_id: str,
    block_type: str,
    *,
    parameters: dict | None = None,
    input_ids: tuple[str, ...] = (),
    output_ids: tuple[str, ...] = (),
    children: list[Block] | None = None,
) -> Block:
    return Block(
        id=block_id,
        type=block_type,
        name=block_id,
        position={"x": 0, "y": 0},
        parameters=parameters or {},
        inputPorts=[{"id": port_id, "name": "in"} for port_id in input_ids],
        outputPorts=[{"id": port_id, "name": "out"} for port_id in output_ids],
        children=children,
        childConnections=[],
    )


def test_compile_surfaces_internal_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    compiler = ModelCompiler()
    model = Model(
        id="broken",
        metadata=ModelMetadata(name="Broken"),
        blocks=[make_block("source", "constant", output_ids=("source-out-0",))],
        connections=[],
    )
    method_name = "_flatten_" + "subsystems"
    monkeypatch.setattr(compiler, method_name, Mock(side_effect=RuntimeError("compiler sentinel")))

    result = compiler.compile(model)

    assert result.success is False
    assert result.message == "Compilation error: compiler sentinel"
    assert result.errors == ["compiler sentinel"]


def test_nonstandard_nested_port_ids_keep_their_identity() -> None:
    child = make_block(
        "gain",
        "gain",
        input_ids=("custom-input",),
        output_ids=("custom-output",),
    )
    subsystem = make_block("sub", "subsystem", children=[child])
    method_name = "_flatten_" + "subsystems"

    blocks, connections = getattr(ModelCompiler(), method_name)([subsystem], [])

    assert connections == []
    assert blocks[0].id == "sub__gain"
    assert blocks[0].input_ports[0].id == "sub__gain__custom-input"
    assert blocks[0].output_ports[0].id == "sub__gain__custom-output"


def test_unresolvable_subsystem_boundaries_are_not_connected() -> None:
    bad_inport = make_block(
        "inner-in",
        "inport",
        parameters={"portNumber": "first"},
        input_ids=("inner-in-in-0",),
        output_ids=("inner-in-out-0",),
    )
    bad_outport = make_block(
        "inner-out",
        "outport",
        parameters={"portNumber": "first"},
        input_ids=("inner-out-in-0",),
        output_ids=("inner-out-out-0",),
    )
    subsystem = make_block(
        "sub",
        "subsystem",
        input_ids=("sub-in-0",),
        output_ids=("sub-out-0",),
        children=[bad_inport, bad_outport],
    )
    source = make_block("source", "constant", output_ids=("source-out-0",))
    sink = make_block("sink", "scope", input_ids=("sink-in-0",))
    connections = [
        Connection(
            id="bad-source-index",
            sourceBlockId="sub",
            sourcePortId="not-an-index",
            targetBlockId="sink",
            targetPortId="sink-in-0",
        ),
        Connection(
            id="unmapped-source",
            sourceBlockId="sub",
            sourcePortId="sub-out-0",
            targetBlockId="sink",
            targetPortId="sink-in-0",
        ),
        Connection(
            id="unmapped-target",
            sourceBlockId="source",
            sourcePortId="source-out-0",
            targetBlockId="sub",
            targetPortId="sub-in-0",
        ),
    ]
    method_name = "_flatten_" + "subsystems"

    _, flattened = getattr(ModelCompiler(), method_name)([source, subsystem, sink], connections)

    assert flattened == []


def test_dependency_graph_can_include_state_holding_sources() -> None:
    integrator = make_block("integrator", "integrator")
    sink = make_block("sink", "scope")
    method_name = "_build_dependency_" + "graph"

    dependencies = getattr(ModelCompiler(), method_name)(
        [integrator, sink],
        {"sink": ["integrator:out@in"]},
        for_algebraic_loop_detection=False,
    )

    assert dependencies == {"integrator": set(), "sink": {"integrator"}}
