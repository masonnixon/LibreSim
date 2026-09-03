"""Real matrix operation tests (P1).

These tests assert the Phase 1 behavior described in
docs/plans/as2-nonlinear-parity-implementation.md: true matrix
multiplication, transpose, and inverse against real 2-D shapes, the new
constant matrix constructor blocks, and 2-D row/column addressing for
Selector, Assignment, and Concatenate.  Every model is built the same way
the frontend builds one: standard wire JSON validated into Model, compiled
by ModelCompiler, and executed by OSKAdapter.  No OSK blocks are
constructed directly and the compiler is never bypassed.

The known answers below are fixed by the phase contract; they are not
computed by calling the blocks under test.
"""

import numpy as np
import pytest

from src.models.model import Model
from src.simulation.compiler import ModelCompiler
from src.simulation.osk_adapter import OSKAdapter


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
):
    """Build one block dict in the same wire JSON the frontend submits."""
    return {
        "id": block_id,
        "type": block_type,
        "name": name,
        "position": {"x": 0.0, "y": 0.0},
        "parameters": parameters or {},
        "inputPorts": inputs or [],
        "outputPorts": outputs or [],
    }


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
            "metadata": {"name": model_id, "description": "P1 matrix ops test model"},
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


def capture_error(model):
    """Return the first error text raised while building or stepping a model.

    Model build errors surface from ModelCompiler, wiring and block
    construction errors from OSKAdapter.initialize, and runtime shape
    errors from the first step.  Returns None when the model runs clean.
    """
    compiled = ModelCompiler().compile(model)
    if not compiled.success:
        return compiled.message
    adapter = OSKAdapter()
    try:
        adapter.initialize(compiled, model.simulation_config)
        adapter.step(0.0, model.simulation_config.step_size)
    except Exception as exc:
        return str(exc)
    return None


def constant_block(block_id, values, dimensions):
    """A constant source exposing a flat row-major signal with a port shape."""
    return make_block(
        block_id,
        "constant",
        "Constant",
        {"value": values},
        outputs=[make_port(block_id + "-out-0", "out", dimensions)],
    )


def scope_block(block_id, dimensions):
    return make_block(
        block_id,
        "scope",
        "Scope",
        {"numInputs": 1},
        inputs=[make_port(block_id + "-in-0", "in", dimensions)],
    )


# ---------------------------------------------------------------------------
# MatrixMultiply
# ---------------------------------------------------------------------------


def test_matmul_2x2_known_answer():
    """[2,2] x [2,2] -> [2,2] with the contract's known answer."""
    model = make_model(
        "mm-2x2",
        [
            constant_block("src-a", [1, 2, 3, 4], [2, 2]),
            constant_block("src-b", [5, 6, 7, 8], [2, 2]),
            make_block(
                "mm-1",
                "matrix_multiply",
                "Multiply",
                inputs=[
                    make_port("mm-1-in-0", "A", [2, 2]),
                    make_port("mm-1-in-1", "B", [2, 2]),
                ],
                outputs=[make_port("mm-1-out-0", "out", [2, 2])],
            ),
            scope_block("scope-1", [2, 2]),
        ],
        [
            make_connection("c-a", "src-a", "src-a-out-0", "mm-1", "mm-1-in-0"),
            make_connection("c-b", "src-b", "src-b-out-0", "mm-1", "mm-1-in-1"),
            make_connection("c-o", "mm-1", "mm-1-out-0", "scope-1", "scope-1-in-0"),
        ],
    )

    _, adapter, outputs = run_model(model)

    # [[1,2],[3,4]] @ [[5,6],[7,8]] == [[19,22],[43,50]]
    assert list(outputs.values()) == [19.0, 22.0, 43.0, 50.0]

    multiply = adapter._osk_blocks["mm-1"]
    assert multiply.getOutputVector() == [19.0, 22.0, 43.0, 50.0]
    array = np.asarray(multiply.getOutputArray())
    assert tuple(array.shape) == (2, 2)
    assert array.tolist() == [[19.0, 22.0], [43.0, 50.0]]


def test_matmul_2x3_by_3x2_known_answer():
    """Non-square [2,3] x [3,2] -> [2,2] with the contract's known answer."""
    model = make_model(
        "mm-non-square",
        [
            constant_block("src-a", [1, 2, 3, 4, 5, 6], [2, 3]),
            constant_block("src-b", [7, 8, 9, 10, 11, 12], [3, 2]),
            make_block(
                "mm-1",
                "matrix_multiply",
                "Multiply",
                inputs=[
                    make_port("mm-1-in-0", "A", [2, 3]),
                    make_port("mm-1-in-1", "B", [3, 2]),
                ],
                outputs=[make_port("mm-1-out-0", "out", [2, 2])],
            ),
            scope_block("scope-1", [2, 2]),
        ],
        [
            make_connection("c-a", "src-a", "src-a-out-0", "mm-1", "mm-1-in-0"),
            make_connection("c-b", "src-b", "src-b-out-0", "mm-1", "mm-1-in-1"),
            make_connection("c-o", "mm-1", "mm-1-out-0", "scope-1", "scope-1-in-0"),
        ],
    )

    _, adapter, outputs = run_model(model)

    # [[1,2,3],[4,5,6]] @ [[7,8],[9,10],[11,12]] == [[58,64],[139,154]]
    assert list(outputs.values()) == [58.0, 64.0, 139.0, 154.0]

    multiply = adapter._osk_blocks["mm-1"]
    array = np.asarray(multiply.getOutputArray())
    assert tuple(array.shape) == (2, 2)
    assert array.tolist() == [[58.0, 64.0], [139.0, 154.0]]


def test_matmul_matrix_vector_known_answer():
    """[2,2] x [2] -> [2] with the contract's known answer."""
    model = make_model(
        "mm-matrix-vector",
        [
            constant_block("src-a", [1, 2, 3, 4], [2, 2]),
            constant_block("src-b", [5, 6], [2]),
            make_block(
                "mm-1",
                "matrix_multiply",
                "Multiply",
                inputs=[
                    make_port("mm-1-in-0", "A", [2, 2]),
                    make_port("mm-1-in-1", "B", [2]),
                ],
                outputs=[make_port("mm-1-out-0", "out", [2])],
            ),
            scope_block("scope-1", [2]),
        ],
        [
            make_connection("c-a", "src-a", "src-a-out-0", "mm-1", "mm-1-in-0"),
            make_connection("c-b", "src-b", "src-b-out-0", "mm-1", "mm-1-in-1"),
            make_connection("c-o", "mm-1", "mm-1-out-0", "scope-1", "scope-1-in-0"),
        ],
    )

    _, adapter, outputs = run_model(model)

    # [[1,2],[3,4]] @ [5,6] == [17,39]
    assert list(outputs.values()) == [17.0, 39.0]

    multiply = adapter._osk_blocks["mm-1"]
    assert multiply.getOutputVector() == [17.0, 39.0]
    array = np.asarray(multiply.getOutputArray())
    assert tuple(array.shape) == (2,)


def test_matmul_vector_vector_product_is_defined_vector_product():
    """[3] x [3] is the defined row-by-column vector product (scalar)."""
    model = make_model(
        "mm-vectors",
        [
            constant_block("src-a", [1, 2, 3], [3]),
            constant_block("src-b", [4, 5, 6], [3]),
            make_block(
                "mm-1",
                "matrix_multiply",
                "Multiply",
                inputs=[
                    make_port("mm-1-in-0", "A", [3]),
                    make_port("mm-1-in-1", "B", [3]),
                ],
                outputs=[make_port("mm-1-out-0", "out", [1])],
            ),
            scope_block("scope-1", [1]),
        ],
        [
            make_connection("c-a", "src-a", "src-a-out-0", "mm-1", "mm-1-in-0"),
            make_connection("c-b", "src-b", "src-b-out-0", "mm-1", "mm-1-in-1"),
            make_connection("c-o", "mm-1", "mm-1-out-0", "scope-1", "scope-1-in-0"),
        ],
    )

    _, adapter, outputs = run_model(model)

    # 1*4 + 2*5 + 3*6 = 32, delivered as a scalar signal.
    assert list(outputs.values()) == [32.0]
    multiply = adapter._osk_blocks["mm-1"]
    assert multiply.getOutput() == pytest.approx(32.0)
    assert multiply.getOutputVector() is None


def test_matmul_scalar_vector_product():
    """A scalar scales a vector element-wise: 2.0 x [1,2,3] == [2,4,6]."""
    model = make_model(
        "mm-scalar-vector",
        [
            constant_block("src-a", 2.0, [1]),
            constant_block("src-b", [1, 2, 3], [3]),
            make_block(
                "mm-1",
                "matrix_multiply",
                "Multiply",
                inputs=[
                    make_port("mm-1-in-0", "A", [1]),
                    make_port("mm-1-in-1", "B", [3]),
                ],
                outputs=[make_port("mm-1-out-0", "out", [3])],
            ),
            scope_block("scope-1", [3]),
        ],
        [
            make_connection("c-a", "src-a", "src-a-out-0", "mm-1", "mm-1-in-0"),
            make_connection("c-b", "src-b", "src-b-out-0", "mm-1", "mm-1-in-1"),
            make_connection("c-o", "mm-1", "mm-1-out-0", "scope-1", "scope-1-in-0"),
        ],
    )

    _, _, outputs = run_model(model)
    assert list(outputs.values()) == [2.0, 4.0, 6.0]


def test_matmul_vector_matrix_product():
    """[2] x [2,2] -> [2]: [5,6] @ [[1,2],[3,4]] == [23,34]."""
    model = make_model(
        "mm-vector-matrix",
        [
            constant_block("src-a", [5, 6], [2]),
            constant_block("src-b", [1, 2, 3, 4], [2, 2]),
            make_block(
                "mm-1",
                "matrix_multiply",
                "Multiply",
                inputs=[
                    make_port("mm-1-in-0", "A", [2]),
                    make_port("mm-1-in-1", "B", [2, 2]),
                ],
                outputs=[make_port("mm-1-out-0", "out", [2])],
            ),
            scope_block("scope-1", [2]),
        ],
        [
            make_connection("c-a", "src-a", "src-a-out-0", "mm-1", "mm-1-in-0"),
            make_connection("c-b", "src-b", "src-b-out-0", "mm-1", "mm-1-in-1"),
            make_connection("c-o", "mm-1", "mm-1-out-0", "scope-1", "scope-1-in-0"),
        ],
    )

    _, _, outputs = run_model(model)
    assert list(outputs.values()) == [23.0, 34.0]


def test_matmul_scalar_scalar_product():
    """3.0 x 4.0 == 12.0 stays a scalar signal."""
    model = make_model(
        "mm-scalars",
        [
            constant_block("src-a", 3.0, [1]),
            constant_block("src-b", 4.0, [1]),
            make_block(
                "mm-1",
                "matrix_multiply",
                "Multiply",
                inputs=[
                    make_port("mm-1-in-0", "A", [1]),
                    make_port("mm-1-in-1", "B", [1]),
                ],
                outputs=[make_port("mm-1-out-0", "out", [1])],
            ),
            scope_block("scope-1", [1]),
        ],
        [
            make_connection("c-a", "src-a", "src-a-out-0", "mm-1", "mm-1-in-0"),
            make_connection("c-b", "src-b", "src-b-out-0", "mm-1", "mm-1-in-1"),
            make_connection("c-o", "mm-1", "mm-1-out-0", "scope-1", "scope-1-in-0"),
        ],
    )

    _, _, outputs = run_model(model)
    assert list(outputs.values()) == [12.0]


def test_matmul_incompatible_shapes_raise():
    """[2,3] @ [2,3] has no defined product and must raise, not degrade."""
    model = make_model(
        "mm-incompatible",
        [
            constant_block("src-a", [1, 2, 3, 4, 5, 6], [2, 3]),
            constant_block("src-b", [7, 8, 9, 10, 11, 12], [2, 3]),
            make_block(
                "mm-1",
                "matrix_multiply",
                "Multiply",
                inputs=[
                    make_port("mm-1-in-0", "A", [2, 3]),
                    make_port("mm-1-in-1", "B", [2, 3]),
                ],
                outputs=[make_port("mm-1-out-0", "out", [1])],
            ),
            scope_block("scope-1", [1]),
        ],
        [
            make_connection("c-a", "src-a", "src-a-out-0", "mm-1", "mm-1-in-0"),
            make_connection("c-b", "src-b", "src-b-out-0", "mm-1", "mm-1-in-1"),
            make_connection("c-o", "mm-1", "mm-1-out-0", "scope-1", "scope-1-in-0"),
        ],
    )

    message = capture_error(model)
    assert message is not None, "[2,3] @ [2,3] must be rejected"
    assert "mm-1" in message
    assert "expected" in message.lower()
    assert "3" in message


def test_matmul_scalar_matrix_raise():
    """A scalar cannot be matrix-multiplied with a 2-D matrix."""
    model = make_model(
        "mm-scalar-matrix",
        [
            constant_block("src-a", 2.0, [1]),
            constant_block("src-b", [1, 2, 3, 4], [2, 2]),
            make_block(
                "mm-1",
                "matrix_multiply",
                "Multiply",
                inputs=[
                    make_port("mm-1-in-0", "A", [1]),
                    make_port("mm-1-in-1", "B", [2, 2]),
                ],
                outputs=[make_port("mm-1-out-0", "out", [1])],
            ),
            scope_block("scope-1", [1]),
        ],
        [
            make_connection("c-a", "src-a", "src-a-out-0", "mm-1", "mm-1-in-0"),
            make_connection("c-b", "src-b", "src-b-out-0", "mm-1", "mm-1-in-1"),
            make_connection("c-o", "mm-1", "mm-1-out-0", "scope-1", "scope-1-in-0"),
        ],
    )

    message = capture_error(model)
    assert message is not None, "scalar x [2,2] must be rejected"
    assert "mm-1" in message
    assert "expected" in message.lower()


# ---------------------------------------------------------------------------
# MatrixTranspose
# ---------------------------------------------------------------------------


def test_transpose_2x3_known_answer():
    """transpose([[1,2,3],[4,5,6]]) == [[1,4],[2,5],[3,6]]."""
    model = make_model(
        "transpose-2x3",
        [
            constant_block("src", [1, 2, 3, 4, 5, 6], [2, 3]),
            make_block(
                "mt-1",
                "matrix_transpose",
                "Transpose",
                inputs=[make_port("mt-1-in-0", "in", [2, 3])],
                outputs=[make_port("mt-1-out-0", "out", [3, 2])],
            ),
            scope_block("scope-1", [3, 2]),
        ],
        [
            make_connection("c-i", "src", "src-out-0", "mt-1", "mt-1-in-0"),
            make_connection("c-o", "mt-1", "mt-1-out-0", "scope-1", "scope-1-in-0"),
        ],
    )

    _, adapter, outputs = run_model(model)

    assert list(outputs.values()) == [1.0, 4.0, 2.0, 5.0, 3.0, 6.0]
    transpose = adapter._osk_blocks["mt-1"]
    assert transpose.getOutputVector() == [1.0, 4.0, 2.0, 5.0, 3.0, 6.0]
    array = np.asarray(transpose.getOutputArray())
    assert tuple(array.shape) == (3, 2)
    assert array.tolist() == [[1.0, 4.0], [2.0, 5.0], [3.0, 6.0]]


def test_transpose_round_trip():
    """Transposing twice must return the original [2,3] matrix."""
    model = make_model(
        "transpose-roundtrip",
        [
            constant_block("src", [1, 2, 3, 4, 5, 6], [2, 3]),
            make_block(
                "t-1",
                "matrix_transpose",
                "Transpose 1",
                inputs=[make_port("t-1-in-0", "in", [2, 3])],
                outputs=[make_port("t-1-out-0", "out", [3, 2])],
            ),
            make_block(
                "t-2",
                "matrix_transpose",
                "Transpose 2",
                inputs=[make_port("t-2-in-0", "in", [3, 2])],
                outputs=[make_port("t-2-out-0", "out", [2, 3])],
            ),
            scope_block("scope-1", [2, 3]),
        ],
        [
            make_connection("c-i", "src", "src-out-0", "t-1", "t-1-in-0"),
            make_connection("c-m", "t-1", "t-1-out-0", "t-2", "t-2-in-0"),
            make_connection("c-o", "t-2", "t-2-out-0", "scope-1", "scope-1-in-0"),
        ],
    )

    _, _, outputs = run_model(model)
    assert list(outputs.values()) == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]


# ---------------------------------------------------------------------------
# MatrixInverse
# ---------------------------------------------------------------------------


def test_inverse_2x2_known_answer():
    """inverse([[4,7],[2,6]]) == [[0.6,-0.7],[-0.2,0.4]]."""
    model = make_model(
        "inverse-2x2",
        [
            constant_block("src", [4, 7, 2, 6], [2, 2]),
            make_block(
                "inv-1",
                "matrix_inverse",
                "Inverse",
                inputs=[make_port("inv-1-in-0", "in", [2, 2])],
                outputs=[make_port("inv-1-out-0", "out", [2, 2])],
            ),
            scope_block("scope-1", [2, 2]),
        ],
        [
            make_connection("c-i", "src", "src-out-0", "inv-1", "inv-1-in-0"),
            make_connection("c-o", "inv-1", "inv-1-out-0", "scope-1", "scope-1-in-0"),
        ],
    )

    _, adapter, outputs = run_model(model)

    assert list(outputs.values()) == pytest.approx([0.6, -0.7, -0.2, 0.4])
    inverse = adapter._osk_blocks["inv-1"]
    array = np.asarray(inverse.getOutputArray())
    assert tuple(array.shape) == (2, 2)
    assert np.allclose(array, [[0.6, -0.7], [-0.2, 0.4]], atol=1e-9)


def test_inverse_singular_2d_is_inf():
    """A singular declared [2,2] inverts to inf, never to a stale number."""
    model = make_model(
        "inverse-singular",
        [
            constant_block("src", [1, 2, 2, 4], [2, 2]),
            make_block(
                "inv-1",
                "matrix_inverse",
                "Inverse",
                inputs=[make_port("inv-1-in-0", "in", [2, 2])],
                outputs=[make_port("inv-1-out-0", "out", [2, 2])],
            ),
            scope_block("scope-1", [2, 2]),
        ],
        [
            make_connection("c-i", "src", "src-out-0", "inv-1", "inv-1-in-0"),
            make_connection("c-o", "inv-1", "inv-1-out-0", "scope-1", "scope-1-in-0"),
        ],
    )

    _, _, outputs = run_model(model)
    assert all(value == float("inf") for value in outputs.values())


def test_inverse_nonsquare_2d_raise():
    """A declared [2,3] input is not square and must raise."""
    model = make_model(
        "inverse-nonsquare",
        [
            constant_block("src", [1, 2, 3, 4, 5, 6], [2, 3]),
            make_block(
                "inv-1",
                "matrix_inverse",
                "Inverse",
                inputs=[make_port("inv-1-in-0", "in", [2, 3])],
                outputs=[make_port("inv-1-out-0", "out", [1])],
            ),
            scope_block("scope-1", [1]),
        ],
        [
            make_connection("c-i", "src", "src-out-0", "inv-1", "inv-1-in-0"),
            make_connection("c-o", "inv-1", "inv-1-out-0", "scope-1", "scope-1-in-0"),
        ],
    )

    message = capture_error(model)
    assert message is not None, "a non-square 2-D inverse must be rejected"
    assert "inv-1" in message
    assert "square" in message.lower()


# ---------------------------------------------------------------------------
# Constructor blocks
# ---------------------------------------------------------------------------


def test_matrix_identity_known_answer():
    """matrix_identity(3) is the 3x3 identity matrix."""
    model = make_model(
        "identity-3",
        [
            make_block(
                "id-1",
                "matrix_identity",
                "Identity",
                {"size": 3},
                outputs=[make_port("id-1-out-0", "out", [3, 3])],
            ),
            scope_block("scope-1", [3, 3]),
        ],
        [make_connection("c-o", "id-1", "id-1-out-0", "scope-1", "scope-1-in-0")],
    )

    _, adapter, outputs = run_model(model)

    assert list(outputs.values()) == [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
    identity = adapter._osk_blocks["id-1"]
    array = np.asarray(identity.getOutputArray())
    assert tuple(array.shape) == (3, 3)
    assert np.array_equal(array, np.eye(3))


def test_matrix_zeros_known_answer():
    """matrix_zeros(2, 3) is a 2x3 matrix of zeros."""
    model = make_model(
        "zeros-2x3",
        [
            make_block(
                "z-1",
                "matrix_zeros",
                "Zeros",
                {"rows": 2, "cols": 3},
                outputs=[make_port("z-1-out-0", "out", [2, 3])],
            ),
            scope_block("scope-1", [2, 3]),
        ],
        [make_connection("c-o", "z-1", "z-1-out-0", "scope-1", "scope-1-in-0")],
    )

    _, adapter, outputs = run_model(model)

    assert list(outputs.values()) == [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    zeros = adapter._osk_blocks["z-1"]
    array = np.asarray(zeros.getOutputArray())
    assert tuple(array.shape) == (2, 3)
    assert np.array_equal(array, np.zeros((2, 3)))


def test_matrix_diagonal_known_answer():
    """matrix_diagonal([1,2,3]) is the 3x3 diagonal matrix."""
    model = make_model(
        "diagonal-3",
        [
            make_block(
                "d-1",
                "matrix_diagonal",
                "Diagonal",
                {"values": [1, 2, 3]},
                outputs=[make_port("d-1-out-0", "out", [3, 3])],
            ),
            scope_block("scope-1", [3, 3]),
        ],
        [make_connection("c-o", "d-1", "d-1-out-0", "scope-1", "scope-1-in-0")],
    )

    _, adapter, outputs = run_model(model)

    assert list(outputs.values()) == [1.0, 0.0, 0.0, 0.0, 2.0, 0.0, 0.0, 0.0, 3.0]
    diagonal = adapter._osk_blocks["d-1"]
    array = np.asarray(diagonal.getOutputArray())
    assert tuple(array.shape) == (3, 3)
    assert np.array_equal(array, np.diag([1.0, 2.0, 3.0]))


def test_matrix_reshape_known_answer():
    """matrix_reshape([1,2,3,4,5,6] -> [2,3]) == [[1,2,3],[4,5,6]]."""
    model = make_model(
        "reshape-6",
        [
            constant_block("src", [1, 2, 3, 4, 5, 6], [6]),
            make_block(
                "rs-1",
                "matrix_reshape",
                "Reshape",
                {"rows": 2, "cols": 3},
                inputs=[make_port("rs-1-in-0", "in", [6])],
                outputs=[make_port("rs-1-out-0", "out", [2, 3])],
            ),
            scope_block("scope-1", [2, 3]),
        ],
        [
            make_connection("c-i", "src", "src-out-0", "rs-1", "rs-1-in-0"),
            make_connection("c-o", "rs-1", "rs-1-out-0", "scope-1", "scope-1-in-0"),
        ],
    )

    _, adapter, outputs = run_model(model)

    assert list(outputs.values()) == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    reshape = adapter._osk_blocks["rs-1"]
    array = np.asarray(reshape.getOutputArray())
    assert tuple(array.shape) == (2, 3)
    assert array.tolist() == [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]


def test_matrix_reshape_incompatible_size_raise():
    """Six elements cannot fill a [2,2] target; the step must raise."""
    model = make_model(
        "reshape-bad",
        [
            constant_block("src", [1, 2, 3, 4, 5, 6], [6]),
            make_block(
                "rs-1",
                "matrix_reshape",
                "Reshape",
                {"rows": 2, "cols": 2},
                inputs=[make_port("rs-1-in-0", "in", [6])],
                outputs=[make_port("rs-1-out-0", "out", [4])],
            ),
            scope_block("scope-1", [4]),
        ],
        [
            make_connection("c-i", "src", "src-out-0", "rs-1", "rs-1-in-0"),
            make_connection("c-o", "rs-1", "rs-1-out-0", "scope-1", "scope-1-in-0"),
        ],
    )

    message = capture_error(model)
    assert message is not None, "reshape with a wrong element count must be rejected"
    assert "rs-1" in message
    assert "expected 4 elements" in message


@pytest.mark.parametrize(
    ("block_type", "parameters"),
    [
        ("matrix_identity", {"size": 0}),
        ("matrix_zeros", {"rows": 0, "cols": 2}),
        ("matrix_diagonal", {"values": []}),
        ("matrix_reshape", {"rows": 2, "cols": 0}),
    ],
)
def test_matrix_constructor_invalid_parameters_raise(block_type, parameters):
    """Constructor blocks validate their constant shape parameters at build."""
    block_id = "bad-1"
    block = make_block(
        block_id,
        block_type,
        "Bad",
        parameters,
        outputs=[make_port(block_id + "-out-0", "out", [1])],
    )
    if block_type == "matrix_reshape":
        block["inputPorts"] = [make_port(block_id + "-in-0", "in", [1])]
    model = make_model(block_type, [block], [])

    message = capture_error(model)
    assert message is not None, f"{block_type} with invalid parameters must fail"
    assert block_id in message


# ---------------------------------------------------------------------------
# Selector / Assignment / Concatenate with 2-D addressing
# ---------------------------------------------------------------------------


def test_selector_2d_row_major():
    """Indices address a [3,4] matrix in row-major order; OOB selects 0."""
    model = make_model(
        "selector-2d",
        [
            constant_block("src", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], [3, 4]),
            make_block(
                "sel-1",
                "selector",
                "Selector",
                {"indices": [4, 15]},
                inputs=[make_port("sel-1-in-0", "in", [3, 4])],
                outputs=[make_port("sel-1-out-0", "out", [2])],
            ),
            scope_block("scope-1", [2]),
        ],
        [
            make_connection("c-i", "src", "src-out-0", "sel-1", "sel-1-in-0"),
            make_connection("c-o", "sel-1", "sel-1-out-0", "scope-1", "scope-1-in-0"),
        ],
    )

    _, _, outputs = run_model(model)
    # Row-major element 4 is the start of row 2; index 15 is out of range.
    assert list(outputs.values()) == [5.0, 0.0]


def test_selector_1d_preserved():
    """Flat 1-D selection keeps its existing element-index behavior."""
    model = make_model(
        "selector-1d",
        [
            constant_block("src", [10, 20, 30, 40], [4]),
            make_block(
                "sel-1",
                "selector",
                "Selector",
                {"indices": [0, 2]},
                inputs=[make_port("sel-1-in-0", "in", [4])],
                outputs=[make_port("sel-1-out-0", "out", [2])],
            ),
            scope_block("scope-1", [2]),
        ],
        [
            make_connection("c-i", "src", "src-out-0", "sel-1", "sel-1-in-0"),
            make_connection("c-o", "sel-1", "sel-1-out-0", "scope-1", "scope-1-in-0"),
        ],
    )

    _, _, outputs = run_model(model)
    assert list(outputs.values()) == [10.0, 30.0]


def test_assignment_2d_row_major():
    """Values replace row-major cells of a [2,3] base; OOB indices skip."""
    model = make_model(
        "assignment-2d",
        [
            constant_block("base", [1, 2, 3, 4, 5, 6], [2, 3]),
            constant_block("vals", [99, 88, 77], [3]),
            make_block(
                "as-1",
                "assignment",
                "Assignment",
                {"indices": [0, 5, 99]},
                inputs=[
                    make_port("as-1-in-0", "base", [2, 3]),
                    make_port("as-1-in-1", "values", [3]),
                ],
                outputs=[make_port("as-1-out-0", "out", [2, 3])],
            ),
            scope_block("scope-1", [2, 3]),
        ],
        [
            make_connection("c-b", "base", "base-out-0", "as-1", "as-1-in-0"),
            make_connection("c-v", "vals", "vals-out-0", "as-1", "as-1-in-1"),
            make_connection("c-o", "as-1", "as-1-out-0", "scope-1", "scope-1-in-0"),
        ],
    )

    _, adapter, outputs = run_model(model)

    # Cell 0 <- 99, cell 5 <- 88, index 99 out of range (77 unused).
    assert list(outputs.values()) == [99.0, 2.0, 3.0, 4.0, 5.0, 88.0]
    assignment = adapter._osk_blocks["as-1"]
    array = np.asarray(assignment.getOutputArray())
    assert tuple(array.shape) == (2, 3)
    assert array.tolist() == [[99.0, 2.0, 3.0], [4.0, 5.0, 88.0]]


def test_assignment_1d_preserved():
    """Flat 1-D assignment keeps its existing element-index behavior."""
    model = make_model(
        "assignment-1d",
        [
            constant_block("base", [1, 2, 3, 4], [4]),
            constant_block("vals", [10, 30], [2]),
            make_block(
                "as-1",
                "assignment",
                "Assignment",
                {"indices": [0, 2]},
                inputs=[
                    make_port("as-1-in-0", "base", [4]),
                    make_port("as-1-in-1", "values", [2]),
                ],
                outputs=[make_port("as-1-out-0", "out", [4])],
            ),
            scope_block("scope-1", [4]),
        ],
        [
            make_connection("c-b", "base", "base-out-0", "as-1", "as-1-in-0"),
            make_connection("c-v", "vals", "vals-out-0", "as-1", "as-1-in-1"),
            make_connection("c-o", "as-1", "as-1-out-0", "scope-1", "scope-1-in-0"),
        ],
    )

    _, _, outputs = run_model(model)
    assert list(outputs.values()) == [10.0, 2.0, 30.0, 4.0]


def test_concatenate_vertical_2d():
    """Vertical 2-D concatenation stacks rows: [A;B] -> [4,2]."""
    model = make_model(
        "concat-v",
        [
            constant_block("src-a", [1, 2, 3, 4], [2, 2]),
            constant_block("src-b", [5, 6, 7, 8], [2, 2]),
            make_block(
                "cat-1",
                "concatenate",
                "Concat",
                {"numInputs": 2, "mode": "vertical"},
                inputs=[
                    make_port("cat-1-in-0", "in1", [2, 2]),
                    make_port("cat-1-in-1", "in2", [2, 2]),
                ],
                outputs=[make_port("cat-1-out-0", "out", [4, 2])],
            ),
            scope_block("scope-1", [4, 2]),
        ],
        [
            make_connection("c-a", "src-a", "src-a-out-0", "cat-1", "cat-1-in-0"),
            make_connection("c-b", "src-b", "src-b-out-0", "cat-1", "cat-1-in-1"),
            make_connection("c-o", "cat-1", "cat-1-out-0", "scope-1", "scope-1-in-0"),
        ],
    )

    _, adapter, outputs = run_model(model)

    assert list(outputs.values()) == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    concat = adapter._osk_blocks["cat-1"]
    array = np.asarray(concat.getOutputArray())
    assert tuple(array.shape) == (4, 2)


def test_concatenate_horizontal_2d():
    """Horizontal 2-D concatenation stacks columns: [A B] -> [2,4]."""
    model = make_model(
        "concat-h",
        [
            constant_block("src-a", [1, 2, 3, 4], [2, 2]),
            constant_block("src-b", [5, 6, 7, 8], [2, 2]),
            make_block(
                "cat-1",
                "concatenate",
                "Concat",
                {"numInputs": 2, "mode": "horizontal"},
                inputs=[
                    make_port("cat-1-in-0", "in1", [2, 2]),
                    make_port("cat-1-in-1", "in2", [2, 2]),
                ],
                outputs=[make_port("cat-1-out-0", "out", [2, 4])],
            ),
            scope_block("scope-1", [2, 4]),
        ],
        [
            make_connection("c-a", "src-a", "src-a-out-0", "cat-1", "cat-1-in-0"),
            make_connection("c-b", "src-b", "src-b-out-0", "cat-1", "cat-1-in-1"),
            make_connection("c-o", "cat-1", "cat-1-out-0", "scope-1", "scope-1-in-0"),
        ],
    )

    _, adapter, outputs = run_model(model)

    assert list(outputs.values()) == [1.0, 2.0, 5.0, 6.0, 3.0, 4.0, 7.0, 8.0]
    concat = adapter._osk_blocks["cat-1"]
    array = np.asarray(concat.getOutputArray())
    assert tuple(array.shape) == (2, 4)


def test_concatenate_2d_dimension_mismatch_raise():
    """Vertical 2-D concatenation needs equal column counts."""
    model = make_model(
        "concat-mismatch",
        [
            constant_block("src-a", [1, 2, 3, 4, 5, 6], [2, 3]),
            constant_block("src-b", [5, 6, 7, 8], [2, 2]),
            make_block(
                "cat-1",
                "concatenate",
                "Concat",
                {"numInputs": 2, "mode": "vertical"},
                inputs=[
                    make_port("cat-1-in-0", "in1", [2, 3]),
                    make_port("cat-1-in-1", "in2", [2, 2]),
                ],
                outputs=[make_port("cat-1-out-0", "out", [1])],
            ),
            scope_block("scope-1", [1]),
        ],
        [
            make_connection("c-a", "src-a", "src-a-out-0", "cat-1", "cat-1-in-0"),
            make_connection("c-b", "src-b", "src-b-out-0", "cat-1", "cat-1-in-1"),
            make_connection("c-o", "cat-1", "cat-1-out-0", "scope-1", "scope-1-in-0"),
        ],
    )

    message = capture_error(model)
    assert message is not None, "2-D concat with unequal column counts must raise"
    assert "cat-1" in message
    assert "expected" in message.lower()


def test_concatenate_mixed_rank_raise():
    """Mixing a 2-D input with a 1-D input is not broadcasting; raise."""
    model = make_model(
        "concat-mixed",
        [
            constant_block("src-a", [1, 2, 3, 4], [2, 2]),
            constant_block("src-b", [5, 6, 7, 8], [4]),
            make_block(
                "cat-1",
                "concatenate",
                "Concat",
                {"numInputs": 2, "mode": "vertical"},
                inputs=[
                    make_port("cat-1-in-0", "in1", [2, 2]),
                    make_port("cat-1-in-1", "in2", [4]),
                ],
                outputs=[make_port("cat-1-out-0", "out", [1])],
            ),
            scope_block("scope-1", [1]),
        ],
        [
            make_connection("c-a", "src-a", "src-a-out-0", "cat-1", "cat-1-in-0"),
            make_connection("c-b", "src-b", "src-b-out-0", "cat-1", "cat-1-in-1"),
            make_connection("c-o", "cat-1", "cat-1-out-0", "scope-1", "scope-1-in-0"),
        ],
    )

    message = capture_error(model)
    assert message is not None, "mixed 2-D/1-D concatenation must raise"
    assert "cat-1" in message
    assert "expected" in message.lower()


def test_concatenate_1d_preserved():
    """Flat 1-D concatenation keeps its existing element behavior."""
    model = make_model(
        "concat-1d",
        [
            constant_block("src-a", [1, 2], [2]),
            constant_block("src-b", [3, 4], [2]),
            make_block(
                "cat-1",
                "concatenate",
                "Concat",
                {"numInputs": 2, "mode": "vertical"},
                inputs=[
                    make_port("cat-1-in-0", "in1", [2]),
                    make_port("cat-1-in-1", "in2", [2]),
                ],
                outputs=[make_port("cat-1-out-0", "out", [4])],
            ),
            scope_block("scope-1", [4]),
        ],
        [
            make_connection("c-a", "src-a", "src-a-out-0", "cat-1", "cat-1-in-0"),
            make_connection("c-b", "src-b", "src-b-out-0", "cat-1", "cat-1-in-1"),
            make_connection("c-o", "cat-1", "cat-1-out-0", "scope-1", "scope-1-in-0"),
        ],
    )

    _, _, outputs = run_model(model)
    assert list(outputs.values()) == [1.0, 2.0, 3.0, 4.0]
