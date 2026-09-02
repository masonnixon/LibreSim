"""Failing shape tests for matrix-valued ports (P0-RED).

These tests assert the DESIRED Phase 0 behavior described in
docs/plans/as2-nonlinear-parity-implementation.md, not the current
behavior.  Every model is built the same way the frontend builds one:
standard wire JSON validated into ``Model``, compiled by
``ModelCompiler``, and executed by ``OSKAdapter``.  No OSK blocks are
constructed directly and the compiler is never bypassed.

At P0-RED every test in this module is expected to FAIL against the
current tree, each for the right reason: 2-D declared dimensions make
``_OutputPortView._is_vector`` False
(backend/src/simulation/osk_adapter.py), so ``getOutputVector()``
returns None and consumers fall back to the first scalar of the signal.
The shape-carrying port view, the model-build tripwire, and the base
block array bridge are the RED gaps under test here.
"""

import numpy as np

from src.models.model import Model
from src.simulation.compiler import ModelCompiler
from src.simulation.osk_adapter import OSKAdapter

VALUES_3X4 = [float(value) for value in range(1, 13)]
VALUES_3X3 = [float(value) for value in range(1, 10)]
VALUES_4 = [1.0, 2.0, 3.0, 4.0]


def make_port(port_id, name, dimensions=None):
    """Build one port dict; omit dimensions to leave the [1] legacy default."""
    port = {"id": port_id, "name": name}
    if dimensions is not None:
        port["dimensions"] = dimensions
    return port


def make_block(
    block_id,
    block_type,
    name,
    parameters=None,
    inputs=None,
    outputs=None,
    children=None,
    child_connections=None,
):
    """Build one block dict in the same wire JSON the frontend submits."""
    block = {
        "id": block_id,
        "type": block_type,
        "name": name,
        "position": {"x": 0.0, "y": 0.0},
        "parameters": parameters or {},
        "inputPorts": inputs or [],
        "outputPorts": outputs or [],
    }
    if children is not None:
        block["children"] = children
        block["childConnections"] = child_connections or []
    return block


def make_connection(conn_id, source, source_port, target, target_port):
    return {
        "id": conn_id,
        "sourceBlockId": source,
        "sourcePortId": source_port,
        "targetBlockId": target,
        "targetPortId": target_port,
    }


def make_model(model_id, blocks, connections):
    return Model.model_validate(
        {
            "id": model_id,
            "metadata": {"name": model_id, "description": "P0-RED shape test model"},
            "blocks": blocks,
            "connections": connections,
            "simulationConfig": {"startTime": 0.0, "stopTime": 0.2, "stepSize": 0.1},
        }
    )


def run_model(model):
    """Compile and step one model through the normal build path.

    Returns (compiled, adapter, recorded_outputs) after a single step at
    t=0, where a constant-driven chain has reached steady state.
    """
    compiled = ModelCompiler().compile(model)
    assert compiled.success, f"model build failed: {compiled.message}"
    adapter = OSKAdapter()
    adapter.initialize(compiled, model.simulation_config)
    outputs = adapter.step(0.0, model.simulation_config.step_size)
    return compiled, adapter, outputs


def build_error_message(model):
    """Return the model-build error text for a model, or None when it builds.

    The Phase 0 tripwire must reject a 2-D signal feeding a flat-list-only
    consumer at model build time, either as a compile failure or as an
    exception while the OSK graph is wired.
    """
    compiled = ModelCompiler().compile(model)
    if not compiled.success:
        return compiled.message
    adapter = OSKAdapter()
    try:
        adapter.initialize(compiled, model.simulation_config)
    except Exception as exc:
        return str(exc)
    return None


def model_3x4_between_blocks():
    """constant [3,4] -> gain -> scope with [3, 4] declared on every port."""
    return make_model(
        "matrix-3x4",
        [
            make_block(
                "src",
                "constant",
                "Constant",
                {"value": VALUES_3X4},
                outputs=[make_port("src-out-0", "out", [3, 4])],
            ),
            make_block(
                "gain-1",
                "gain",
                "Gain",
                {"gain": 1.0},
                inputs=[make_port("gain-1-in-0", "in", [3, 4])],
                outputs=[make_port("gain-1-out-0", "out", [3, 4])],
            ),
            make_block(
                "scope-1",
                "scope",
                "Scope",
                {"numInputs": 1},
                inputs=[make_port("scope-1-in-0", "in", [3, 4])],
            ),
        ],
        [
            make_connection("c-src-gain", "src", "src-out-0", "gain-1", "gain-1-in-0"),
            make_connection("c-gain-scope", "gain-1", "gain-1-out-0", "scope-1", "scope-1-in-0"),
        ],
    )


def test_3x4_signal_passes_between_blocks_with_shape_intact():
    """A declared [3,4] matrix must reach the consumer with all values and shape."""
    compiled, adapter, outputs = run_model(model_3x4_between_blocks())

    constant_block = next(block for block in compiled.blocks if block.id == "src")
    assert constant_block.output_dimensions == [[3, 4]]

    # All twelve elements must arrive at the consumer, not the first scalar.
    assert list(outputs.values()) == VALUES_3X4

    # The wired consumer port must expose the matrix with its shape intact.
    view = adapter._osk_blocks["gain-1"].input_block
    array = np.asarray(view.getOutputArray())
    assert tuple(array.shape) == (3, 4)
    assert array.reshape(-1).tolist() == VALUES_3X4


def model_1x1():
    """constant [1,1] -> gain -> scope with [1, 1] declared on every port."""
    return make_model(
        "matrix-1x1",
        [
            make_block(
                "src",
                "constant",
                "Constant",
                {"value": [7.5]},
                outputs=[make_port("src-out-0", "out", [1, 1])],
            ),
            make_block(
                "gain-1",
                "gain",
                "Gain",
                {"gain": 2.0},
                inputs=[make_port("gain-1-in-0", "in", [1, 1])],
                outputs=[make_port("gain-1-out-0", "out", [1, 1])],
            ),
            make_block(
                "scope-1",
                "scope",
                "Scope",
                {"numInputs": 1},
                inputs=[make_port("scope-1-in-0", "in", [1, 1])],
            ),
        ],
        [
            make_connection("c-src-gain", "src", "src-out-0", "gain-1", "gain-1-in-0"),
            make_connection("c-gain-scope", "gain-1", "gain-1-out-0", "scope-1", "scope-1-in-0"),
        ],
    )


def test_1x1_signal_does_not_degrade_to_scalar():
    """A declared 1x1 matrix must reach the consumer as a 1x1, not a scalar."""
    _, adapter, _ = run_model(model_1x1())

    view = adapter._osk_blocks["gain-1"].input_block
    # The 1x1 signal must still read back as a one-element vector.
    assert view.getOutputVector() == [7.5]

    gain_osk = adapter._osk_blocks["gain-1"]
    assert gain_osk._is_vector is True
    assert gain_osk.getOutputVector() == [15.0]

    array = np.asarray(view.getOutputArray())
    assert tuple(array.shape) == (1, 1)
    assert array.reshape(-1).tolist() == [7.5]


def test_shape_survives_json_roundtrip_and_compile():
    """A [3,4] declaration must survive serialize -> deserialize -> compile."""
    model = model_3x4_between_blocks()
    wire = model.model_dump_json()
    model_back = Model.model_validate_json(wire)

    compiled, adapter, outputs = run_model(model_back)

    constant_block = next(block for block in compiled.blocks if block.id == "src")
    assert constant_block.output_dimensions == [[3, 4]]
    assert list(outputs.values()) == VALUES_3X4

    view = adapter._osk_blocks["gain-1"].input_block
    array = np.asarray(view.getOutputArray())
    assert tuple(array.shape) == (3, 4)
    assert array.reshape(-1).tolist() == VALUES_3X4


def _passthrough_subsystem(sub_id, prefix):
    """An inport -> gain -> outport chain with [3, 4] declared on every port."""
    in_block = make_block(
        prefix + "in-1",
        "inport",
        "In 1",
        {"portNumber": 1},
        inputs=[make_port(prefix + "in-1-in-0", "in", [3, 4])],
        outputs=[make_port(prefix + "in-1-out-0", "out", [3, 4])],
    )
    gain_block = make_block(
        prefix + "gain-1",
        "gain",
        "Gain",
        {"gain": 1.0},
        inputs=[make_port(prefix + "gain-1-in-0", "in", [3, 4])],
        outputs=[make_port(prefix + "gain-1-out-0", "out", [3, 4])],
    )
    out_block = make_block(
        prefix + "out-1",
        "outport",
        "Out 1",
        {"portNumber": 1},
        inputs=[make_port(prefix + "out-1-in-0", "in", [3, 4])],
        outputs=[make_port(prefix + "out-1-out-0", "out", [3, 4])],
    )
    return make_block(
        sub_id,
        "subsystem",
        sub_id.capitalize(),
        {},
        inputs=[make_port(sub_id + "-in-0", "in", [3, 4])],
        outputs=[make_port(sub_id + "-out-0", "out", [3, 4])],
        children=[in_block, gain_block, out_block],
        child_connections=[
            make_connection(
                sub_id + "-in-to-gain",
                prefix + "in-1",
                prefix + "in-1-out-0",
                prefix + "gain-1",
                prefix + "gain-1-in-0",
            ),
            make_connection(
                sub_id + "-gain-to-out",
                prefix + "gain-1",
                prefix + "gain-1-out-0",
                prefix + "out-1",
                prefix + "out-1-in-0",
            ),
        ],
    )


def model_3x4_one_level_nested():
    """constant [3,4] -> subsystem(inport, gain, outport) -> scope."""
    return make_model(
        "nested-1-level",
        [
            make_block(
                "src",
                "constant",
                "Constant",
                {"value": VALUES_3X4},
                outputs=[make_port("src-out-0", "out", [3, 4])],
            ),
            _passthrough_subsystem("sub", ""),
            make_block(
                "scope-1",
                "scope",
                "Scope",
                {"numInputs": 1},
                inputs=[make_port("scope-1-in-0", "in", [3, 4])],
            ),
        ],
        [
            make_connection("c-src-sub", "src", "src-out-0", "sub", "sub-in-0"),
            make_connection("c-sub-scope", "sub", "sub-out-0", "scope-1", "scope-1-in-0"),
        ],
    )


def test_shape_survives_one_level_subsystem_nesting():
    """A [3,4] matrix must cross one subsystem boundary with shape intact."""
    compiled, adapter, outputs = run_model(model_3x4_one_level_nested())

    assert [block.id for block in compiled.blocks] == [
        "src", "sub__in-1", "sub__gain-1", "sub__out-1", "scope-1",
    ]
    assert list(outputs.values()) == VALUES_3X4

    view = adapter._osk_blocks["scope-1"].input_blocks[0]
    array = np.asarray(view.getOutputArray())
    assert tuple(array.shape) == (3, 4)
    assert array.reshape(-1).tolist() == VALUES_3X4


def model_3x4_two_level_nested():
    """constant [3,4] -> outer(inport, inner(inport, gain, outport), outport) -> scope."""
    inner = _passthrough_subsystem("inner", "")
    outer_in = make_block(
        "oin",
        "inport",
        "In 1",
        {"portNumber": 1},
        inputs=[make_port("oin-in-0", "in", [3, 4])],
        outputs=[make_port("oin-out-0", "out", [3, 4])],
    )
    outer_out = make_block(
        "oout",
        "outport",
        "Out 1",
        {"portNumber": 1},
        inputs=[make_port("oout-in-0", "in", [3, 4])],
        outputs=[make_port("oout-out-0", "out", [3, 4])],
    )
    outer = make_block(
        "outer",
        "subsystem",
        "Outer",
        {},
        inputs=[make_port("outer-in-0", "in", [3, 4])],
        outputs=[make_port("outer-out-0", "out", [3, 4])],
        children=[outer_in, inner, outer_out],
        child_connections=[
            make_connection(
                "outer-in-to-inner",
                "oin",
                "oin-out-0",
                "inner",
                "inner-in-0",
            ),
            make_connection(
                "inner-to-outer-out",
                "inner",
                "inner-out-0",
                "oout",
                "oout-in-0",
            ),
        ],
    )
    return make_model(
        "nested-2-level",
        [
            make_block(
                "src",
                "constant",
                "Constant",
                {"value": VALUES_3X4},
                outputs=[make_port("src-out-0", "out", [3, 4])],
            ),
            outer,
            make_block(
                "scope-1",
                "scope",
                "Scope",
                {"numInputs": 1},
                inputs=[make_port("scope-1-in-0", "in", [3, 4])],
            ),
        ],
        [
            make_connection("c-src-outer", "src", "src-out-0", "outer", "outer-in-0"),
            make_connection("c-outer-scope", "outer", "outer-out-0", "scope-1", "scope-1-in-0"),
        ],
    )


def test_shape_survives_two_level_subsystem_nesting():
    """A [3,4] matrix must cross two nested subsystem boundaries intact."""
    compiled, adapter, outputs = run_model(model_3x4_two_level_nested())

    assert [block.id for block in compiled.blocks] == [
        "src",
        "outer__oin",
        "outer__inner__in-1",
        "outer__inner__gain-1",
        "outer__inner__out-1",
        "outer__oout",
        "scope-1",
    ]
    assert list(outputs.values()) == VALUES_3X4

    view = adapter._osk_blocks["scope-1"].input_blocks[0]
    array = np.asarray(view.getOutputArray())
    assert tuple(array.shape) == (3, 4)
    assert array.reshape(-1).tolist() == VALUES_3X4


def model_3x3_into_legacy_flat_consumer():
    """A [3,3] matrix feeding a legacy gain whose input port stays flat [1]."""
    return make_model(
        "matrix-into-legacy",
        [
            make_block(
                "src",
                "constant",
                "Constant",
                {"value": VALUES_3X3},
                outputs=[make_port("src-out-0", "out", [3, 3])],
            ),
            make_block(
                "legacy-gain",
                "gain",
                "Legacy Gain",
                {"gain": 1.0},
                inputs=[make_port("legacy-gain-in-0", "in", [1])],
                outputs=[make_port("legacy-gain-out-0", "out", [1])],
            ),
        ],
        [
            make_connection("c-src-legacy", "src", "src-out-0", "legacy-gain", "legacy-gain-in-0"),
        ],
    )


def test_3x3_into_legacy_flat_consumer_rejected_at_model_build():
    """A [3,3] matrix into a flat-list-only consumer must fail model build.

    The rejection must name the block, the port, and the offending shape
    instead of silently degrading the matrix to its first scalar.
    """
    message = build_error_message(model_3x3_into_legacy_flat_consumer())
    assert message is not None, (
        "a [3,3] matrix into a flat-list consumer must be rejected at model build"
    )
    assert "legacy-gain" in message or "legacy gain" in message.lower()
    assert "port" in message.lower()
    assert "3" in message


def model_flat_vector_into_matrix_consumer():
    """A legacy flat [4] vector feeding a matrix-capable consumer (input [1, 4])."""
    return make_model(
        "flat-vector-bridge",
        [
            make_block(
                "src",
                "constant",
                "Constant",
                {"value": VALUES_4},
                outputs=[make_port("src-out-0", "out", [4])],
            ),
            make_block(
                "gain-1",
                "gain",
                "Gain",
                {"gain": 1.0},
                inputs=[make_port("gain-1-in-0", "in", [1, 4])],
                outputs=[make_port("gain-1-out-0", "out", [4])],
            ),
            make_block(
                "scope-1",
                "scope",
                "Scope",
                {"numInputs": 1},
                inputs=[make_port("scope-1-in-0", "in", [4])],
            ),
        ],
        [
            make_connection("c-src-gain", "src", "src-out-0", "gain-1", "gain-1-in-0"),
            make_connection("c-gain-scope", "gain-1", "gain-1-out-0", "scope-1", "scope-1-in-0"),
        ],
    )


def test_legacy_flat_vector_reaches_matrix_consumer_through_bridge():
    """A legacy flat vector must still reach a matrix-capable consumer.

    The consumer reads it through the base-class array bridge, which
    defaults to the existing getOutputVector()/getOutput() path, so the
    1-D vector semantics of the legacy path must be unchanged.
    """
    _, adapter, outputs = run_model(model_flat_vector_into_matrix_consumer())

    # The flat vector path must keep working end to end (KEEP).
    assert list(outputs.values()) == VALUES_4

    gain_osk = adapter._osk_blocks["gain-1"]
    bridge = getattr(gain_osk, "getOutputArray", None)
    array = bridge() if callable(bridge) else None
    assert array is not None, (
        "base Block must expose a getOutputArray() bridge for legacy vector outputs"
    )
    flat = np.asarray(array).reshape(-1).tolist()
    assert flat == VALUES_4
