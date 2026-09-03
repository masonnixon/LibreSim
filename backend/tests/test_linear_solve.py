"""Native linear solver tests (P2).

These tests assert the Phase 2 behavior described in
docs/plans/as2-nonlinear-parity-implementation.md: a native ``linear_solve``
block that solves ``A x = b`` with LU factorization and partial pivoting, for a
vector or a matrix of right-hand sides, with deterministic status outputs and
failure behavior.

Every model is built the same way the frontend builds one: standard wire JSON
validated into Model, compiled by ModelCompiler, and executed by OSKAdapter.
No OSK blocks are constructed directly and the compiler is never bypassed.

The known answers below are fixed by the phase contract; they are not computed
by calling the block under test.  The only independent numerical reference used
is ``numpy.linalg.solve`` / ``numpy.linalg.cond``.
"""

import math

import numpy as np
import pytest

from src.models.model import Model
from src.simulation.compiler import ModelCompiler
from src.simulation.osk_adapter import OSKAdapter


DT = 0.1


def make_port(port_id, name, dimensions=None):
    """Build one port dict; omit dimensions to leave the [1] legacy default."""
    port = {"id": port_id, "name": name}
    if dimensions is not None:
        port["dimensions"] = dimensions
    return port


def make_block(block_id, block_type, name, parameters=None, inputs=None, outputs=None):
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
            "metadata": {"name": model_id, "description": "P2 linear solve test model"},
            "blocks": blocks,
            "connections": connections,
            "simulationConfig": {"startTime": 0.0, "stopTime": 0.2, "stepSize": DT},
        }
    )


def constant_block(block_id, values, dimensions):
    """A constant source exposing a flat row-major signal with a port shape."""
    return make_block(
        block_id,
        "constant",
        "Constant",
        {"value": values},
        outputs=[make_port(block_id + "-out-0", "out", dimensions)],
    )


def linear_solve_block(block_id, a_dims, b_dims, out_dims, parameters=None):
    """A linear_solve block with wired A (in-0), b (in-1), and x (out-0)."""
    return make_block(
        block_id,
        "linear_solve",
        "LinearSolve",
        parameters or {},
        inputs=[
            make_port(block_id + "-in-0", "A", a_dims),
            make_port(block_id + "-in-1", "b", b_dims),
        ],
        outputs=[make_port(block_id + "-out-0", "x", out_dims)],
    )


def scope_block(block_id, dimensions):
    return make_block(
        block_id,
        "scope",
        "Scope",
        {"numInputs": 1},
        inputs=[make_port(block_id + "-in-0", "in", dimensions)],
    )


def build_and_step(model, block_id):
    """Compile, initialize, and step one model at t=0; return the OSK block."""
    compiled = ModelCompiler().compile(model)
    assert compiled.success, f"model build failed: {compiled.message}"
    adapter = OSKAdapter()
    adapter.initialize(compiled, model.simulation_config)
    adapter.step(0.0, model.simulation_config.step_size)
    return adapter._osk_blocks[block_id]


def solve_model(a_values, a_dims, b_values, b_dims, out_dims, parameters=None):
    """Wire constant A and b into a linear_solve block and step once.

    Returns the configured LinearSolve OSK block after a single step.
    """
    ls_id = "ls-1"
    model = make_model(
        "ls-model",
        [
            constant_block("src-a", a_values, a_dims),
            constant_block("src-b", b_values, b_dims),
            linear_solve_block(ls_id, a_dims, b_dims, out_dims, parameters),
            scope_block("scope-1", out_dims),
        ],
        [
            make_connection("c-a", "src-a", "src-a-out-0", ls_id, ls_id + "-in-0"),
            make_connection("c-b", "src-b", "src-b-out-0", ls_id, ls_id + "-in-1"),
            make_connection("c-o", ls_id, ls_id + "-out-0", "scope-1", "scope-1-in-0"),
        ],
    )
    return build_and_step(model, ls_id)


# ---------------------------------------------------------------------------
# Known-answer solves (fixed by the phase contract)
# ---------------------------------------------------------------------------


def test_solve_1x1_known_answer():
    """[[4]] x = [8] -> x == [2]."""
    block = solve_model([4.0], [1, 1], [8.0], [1], [1])
    assert block.status == 1.0
    assert block.dimension == 1
    assert list(block.getOutputVector()) == pytest.approx([2.0])
    assert np.asarray(block.getOutputArray()).tolist() == pytest.approx([2.0])
    # cond([[4]]) == 1.0; the residual of the exact solution is ~ machine eps.
    assert block.condition == pytest.approx(1.0)
    assert 0.0 <= block.residual < 1e-9
    assert block.get_status()["reason"] == ""


def test_solve_2x2_known_answer():
    """[[2,1],[1,3]] x = [3,5] -> x == [0.8, 1.4]."""
    a = [[2.0, 1.0], [1.0, 3.0]]
    block = solve_model([2.0, 1.0, 1.0, 3.0], [2, 2], [3.0, 5.0], [2], [2])
    assert block.status == 1.0
    assert block.dimension == 2
    assert list(block.getOutputVector()) == pytest.approx([0.8, 1.4])
    assert np.asarray(block.getOutputArray()).shape == (2,)
    # Status outputs must match the independent numpy reference.
    assert block.condition == pytest.approx(float(np.linalg.cond(np.array(a))))
    assert 0.0 <= block.residual < 1e-9


def test_solve_3x3_known_answer():
    """[[2,1,-1],[-3,-1,2],[-2,1,2]] x = [8,-11,-3] -> x == [2, 3, -1]."""
    block = solve_model(
        [2.0, 1.0, -1.0, -3.0, -1.0, 2.0, -2.0, 1.0, 2.0],
        [3, 3],
        [8.0, -11.0, -3.0],
        [3],
        [3],
    )
    assert block.status == 1.0
    assert block.dimension == 3
    assert list(block.getOutputVector()) == pytest.approx([2.0, 3.0, -1.0])
    assert 0.0 <= block.residual < 1e-9


def test_solve_multiple_right_hand_sides():
    """[[2,1],[1,3]] X = [[3,1],[5,0]] -> X == [[0.8,0.6],[1.4,-0.2]].

    The first column must equal the single-RHS solution for the same b, which
    proves vector and matrix right-hand sides share numerical semantics.
    """
    block = solve_model(
        [2.0, 1.0, 1.0, 3.0],
        [2, 2],
        [3.0, 1.0, 5.0, 0.0],
        [2, 2],
        [2, 2],
    )
    assert block.status == 1.0
    assert block.dimension == 2
    array = np.asarray(block.getOutputArray())
    assert array.shape == (2, 2)
    # Compare the nested result directly; pytest.approx rejects nested lists.
    assert np.allclose(array, [[0.8, 0.6], [1.4, -0.2]])
    # First column matches the single-RHS answer for b1 = [3,5].
    assert array[:, 0].tolist() == pytest.approx([0.8, 1.4])
    assert 0.0 <= block.residual < 1e-9


# ---------------------------------------------------------------------------
# Scaling and conditioning
# ---------------------------------------------------------------------------


def test_solve_30x30_well_conditioned_against_numpy():
    """A 30x30 well-conditioned system must match numpy.linalg.solve."""
    rng = np.random.default_rng(42)
    m = rng.standard_normal((30, 30))
    a = m @ m.T + 30.0 * np.eye(30)  # symmetric positive definite
    b = rng.standard_normal(30)
    x_ref = np.linalg.solve(a, b)

    block = solve_model(
        [float(v) for v in a.reshape(-1)], [30, 30], [float(v) for v in b], [30], [30]
    )
    assert block.status == 1.0
    assert block.dimension == 30
    got = np.asarray(block.getOutputArray()).reshape(30)
    assert np.allclose(got, x_ref, rtol=1e-9, atol=1e-9)
    # The residual against the true (numpy) solution is tiny.
    assert float(np.linalg.norm(a @ got - b)) < 1e-6
    assert block.condition == pytest.approx(float(np.linalg.cond(a)), rel=1e-6)


def test_solve_badly_scaled_still_solved():
    """A badly scaled (but solvable) system is solved, with a large condition."""
    a = np.array([[1e-6, 0.0], [0.0, 1e6]])
    b = np.array([2e-6, 3e6])
    block = solve_model([1e-6, 0.0, 0.0, 1e6], [2, 2], [2e-6, 3e6], [2], [2])
    assert block.status == 1.0
    assert block.dimension == 2
    assert list(block.getOutputVector()) == pytest.approx([2.0, 3.0])
    # cond is ~1e12: large, but far under the default 1/eps limit, so it solves.
    assert 1e11 < block.condition < 1e13
    assert 0.0 <= block.residual < 1e-6


# ---------------------------------------------------------------------------
# Failure behavior
# ---------------------------------------------------------------------------


def test_solve_nonsquare_a_rejected():
    """A nonsquare A is reported as a failure, never solved or inverted."""
    # A is 3x2 (nonsquare); b has 3 rows to match A's rows, so the only
    # problem is that A is not square.
    block = solve_model(
        [1.0, 2.0, 3.0, 4.0, 5.0, 6.0], [3, 2], [1.0, 2.0, 3.0], [3], [2]
    )
    assert block.status == 0.0
    assert block.dimension == 0
    assert block.get_status()["reason"] != ""
    # The solution port holds a fresh failure value, not a solution.
    assert all(math.isinf(v) for v in block.getOutputVector())


def test_solve_mismatched_b_rejected():
    """A b whose row count does not match A is reported as a failure."""
    # A is 2x2 (n=2) but b has 3 elements.  The b input port is declared [3]
    # so the *connection* is shape-consistent and the model builds; the solver
    # then rejects the semantic dimension mismatch at runtime.
    block = solve_model([2.0, 1.0, 1.0, 3.0], [2, 2], [1.0, 2.0, 3.0], [3], [2])
    assert block.status == 0.0
    assert block.dimension == 0
    assert block.get_status()["reason"] != ""
    assert all(math.isinf(v) for v in block.getOutputVector())


def test_solve_singular_reported_as_failure():
    """Singular [[1,2],[2,4]] is reported as a failure (not a pseudoinverse)."""
    block = solve_model([1.0, 2.0, 2.0, 4.0], [2, 2], [1.0, 2.0], [2], [2])
    assert block.status == 0.0
    assert block.dimension == 0
    assert "singular" in block.get_status()["reason"].lower()
    assert all(math.isinf(v) for v in block.getOutputVector())


def test_solve_ill_conditioned_reported_as_failure():
    """A system whose condition exceeds the (lowered) limit is a failure."""
    # cond([[2,1],[1,3]]) is ~9.5; lowering the limit to 1.0 flags it as
    # ill-conditioned even though it is mathematically solvable.
    block = solve_model(
        [2.0, 1.0, 1.0, 3.0], [2, 2], [3.0, 5.0], [2], [2],
        {"conditionLimit": 1.0},
    )
    assert block.status == 0.0
    assert block.dimension == 0
    assert "ill-conditioned" in block.get_status()["reason"].lower()


# ---------------------------------------------------------------------------
# Stale-output invariant (required)
# ---------------------------------------------------------------------------


def test_stale_output_not_reemitted_after_singular():
    """A successful solve followed by a singular A must not re-emit x_before.

    This is the P2 stale-output test: drive one successful solve, then feed a
    singular A on the next step, and assert the earlier solution is not
    re-emitted (the block reports a fresh failure instead).
    """
    ls_id = "ls-1"
    model = make_model(
        "ls-stale",
        [
            constant_block("src-a", [2.0, 1.0, 1.0, 3.0], [2, 2]),
            constant_block("src-b", [3.0, 5.0], [2]),
            linear_solve_block(ls_id, [2, 2], [2], [2]),
            scope_block("scope-1", [2]),
        ],
        [
            make_connection("c-a", "src-a", "src-a-out-0", ls_id, ls_id + "-in-0"),
            make_connection("c-b", "src-b", "src-b-out-0", ls_id, ls_id + "-in-1"),
            make_connection("c-o", ls_id, ls_id + "-out-0", "scope-1", "scope-1-in-0"),
        ],
    )
    compiled = ModelCompiler().compile(model)
    assert compiled.success, f"model build failed: {compiled.message}"
    adapter = OSKAdapter()
    adapter.initialize(compiled, model.simulation_config)

    # Step 1: successful solve.
    adapter.step(0.0, model.simulation_config.step_size)
    block = adapter._osk_blocks[ls_id]
    assert block.status == 1.0
    x_before = list(block.getOutputVector())
    assert x_before == pytest.approx([0.8, 1.4])

    # Feed a singular A on the next step by driving the upstream source.
    a_const = adapter._osk_blocks["src-a"]
    a_const._values = [1.0, 2.0, 2.0, 4.0]
    a_const._is_vector = True
    a_const.output = 1.0

    # Step 2: singular A -> the block must not re-emit x_before.
    adapter.step(0.1, model.simulation_config.step_size)
    x_after = list(block.getOutputVector())
    assert x_after != x_before
    assert block.status == 0.0
    assert block.dimension == 0
    assert all(math.isinf(v) for v in x_after)
