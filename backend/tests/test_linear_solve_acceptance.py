"""Acceptance tests for the native linear_solve block (P3).

These tests cover the Phase 3 acceptance criteria in
docs/plans/as2-nonlinear-parity-implementation.md for the ``linear_solve``
block and its acceptance example.  Every model is exercised through the normal
JSON/registry/ModelCompiler path (the example is loaded from disk, validated
into a Model, compiled by ModelCompiler, and executed headless by the OSK
adapter or the SimulationRunner).  No OSK block is constructed directly and
the compiler is never bypassed.

The known answers are fixed by the phase contract:
``A = [[2,1,-1],[-3,-1,2],[-2,1,2]]``, ``b = [8,-11,-3]``, so
``x == [2, 3, -1]``.  The only independent numerical reference used is
``numpy.linalg.cond``.  There are no xfails, skips, or mocks, and no expected
value is computed by calling the block under test.
"""

import json
import math
from pathlib import Path

import numpy as np
import pytest

from src.models.model import Model
from src.simulation.compiler import ModelCompiler
from src.simulation.osk_adapter import OSKAdapter
from src.simulation.runner import SimulationRunner

EXAMPLE_PATH = Path(__file__).parents[2] / "examples" / "51_linear_solve_acceptance.json"

SOLVER_ID = "linear_solve"
A_FLAT_ID = "a_flat"
A_RESHAPE_ID = "a_reshape"
B_VEC_ID = "b_vec"

# The acceptance system, fixed by the phase contract.
A0 = np.array([[2.0, 1.0, -1.0], [-3.0, -1.0, 2.0], [-2.0, 1.0, 2.0]])
X_EXPECTED = [2.0, 3.0, -1.0]


# ---------------------------------------------------------------------------
# Helpers (all models go through the JSON/registry/ModelCompiler path)
# ---------------------------------------------------------------------------


def load_example_model() -> Model:
    """Load the acceptance example from disk and validate it as a Model."""
    return Model.model_validate(json.loads(EXAMPLE_PATH.read_text()))


def run_headless(model: Model, steps: int = 3) -> OSKAdapter:
    """Compile, initialize, and step a model headless; return the adapter."""
    compiled = ModelCompiler().compile(model)
    assert compiled.success, f"model build failed: {compiled.message}"
    adapter = OSKAdapter()
    adapter.initialize(compiled, model.simulation_config)
    dt = model.simulation_config.step_size
    for i in range(steps):
        adapter.step(i * dt, dt)
    return adapter


def solver_outputs(adapter):
    """The solver's published solution and status bundle for the current step."""
    block = adapter._osk_blocks[SOLVER_ID]
    return {
        "solution": list(block.getOutputVector() or []),
        "status": block.status,
        "residual": block.residual,
        "condition": block.condition,
        "dimension": block.dimension,
        "reason": block.get_status()["reason"],
    }


# ---------------------------------------------------------------------------
# (a) The example loads, compiles, and runs headless with the right outputs
# ---------------------------------------------------------------------------


def test_example_loads_compiles_and_runs_headless():
    model = load_example_model()
    out = solver_outputs(run_headless(model, steps=3))

    # The solution is the known answer, reported as a success.
    assert out["status"] == 1.0
    assert out["solution"] == pytest.approx(X_EXPECTED)
    assert out["dimension"] == 3
    # Exact system: the residual is at machine precision.
    assert 0.0 <= out["residual"] < 1e-9
    # Condition estimate is finite and matches the independent numpy reference.
    assert math.isfinite(out["condition"])
    assert out["condition"] == pytest.approx(float(np.linalg.cond(A0)), rel=1e-9)
    # A successful solve carries no failure reason.
    assert out["reason"] == ""


def test_example_is_registered_in_the_manifest():
    """The acceptance example is registered in the examples manifest."""
    from src.api.routes import examples

    manifest_ids = [entry["id"] for entry in examples.EXAMPLE_MANIFEST]
    assert "51_linear_solve_acceptance" in manifest_ids
    # The registered id resolves to the example JSON on disk.
    assert EXAMPLE_PATH.name == "51_linear_solve_acceptance.json"
    assert EXAMPLE_PATH.exists()


# ---------------------------------------------------------------------------
# (b) Determinism: two identical runs produce identical outputs
# ---------------------------------------------------------------------------


def test_two_identical_runs_are_deterministic():
    model = load_example_model()
    first = solver_outputs(run_headless(model, steps=3))
    second = solver_outputs(run_headless(model, steps=3))
    # LU on fixed constant inputs is fully deterministic: bit-identical.
    assert first == second


# ---------------------------------------------------------------------------
# (c) Reset clears the solver's last solution and status
# ---------------------------------------------------------------------------


def test_reset_clears_last_solution_and_status():
    model = load_example_model()
    adapter = run_headless(model, steps=1)
    block = adapter._osk_blocks[SOLVER_ID]

    # A successful solve has published a solution and a success status.
    assert block.status == 1.0
    assert list(block.getOutputVector()) == pytest.approx(X_EXPECTED)

    # Reset: the solver's init() clears the last solution and status.
    block.init()

    assert block.status == 0.0
    assert block.getOutputVector() is None
    assert math.isinf(block.residual)
    assert math.isinf(block.condition)
    assert block.dimension == 0
    assert block.get_status()["reason"] == ""


# ---------------------------------------------------------------------------
# (d) A step-back (rejected step) leaves no stale solution
# ---------------------------------------------------------------------------


def test_step_back_leaves_no_stale_solution():
    model = load_example_model()
    runner = SimulationRunner(model, model.simulation_config)
    assert runner.initialize_step_mode() is True

    # Drive one successful solve.
    assert runner.step_forward(1)["success"] is True
    block = runner._adapter._osk_blocks[SOLVER_ID]
    assert block.status == 1.0
    assert list(block.getOutputVector()) == pytest.approx(X_EXPECTED)

    # Reject the last step: restore the pre-solve checkpoint.
    assert runner.step_backward(1)["success"] is True

    # No stale solution from the rejected step: the solver is back to its
    # clean pre-solve state, not re-emitting the rejected step's result.
    block = runner._adapter._osk_blocks[SOLVER_ID]
    assert block.status == 0.0
    assert block.getOutputVector() is None
    assert math.isinf(block.residual)
    assert block.dimension == 0


# ---------------------------------------------------------------------------
# (e) Step-back replay round-trips the matrix and linear_solve snapshots
# ---------------------------------------------------------------------------


def test_step_back_round_trips_matrix_and_solver_snapshots():
    model = load_example_model()
    runner = SimulationRunner(model, model.simulation_config)
    assert runner.initialize_step_mode() is True
    adapter = runner._adapter

    # Commit one solve of the example system (A0) and record its state.
    assert runner.step_forward(1)["success"] is True
    solver1 = solver_outputs(adapter)
    reshape1 = np.asarray(adapter._osk_blocks[A_RESHAPE_ID].getOutputArray())
    a_flat1 = list(adapter._osk_blocks[A_FLAT_ID].getOutputVector())
    assert solver1["solution"] == pytest.approx(X_EXPECTED)

    # Drive A to a different well-conditioned matrix (2*I), which changes the
    # solution, then commit that step.
    a1_flat = [2.0, 0.0, 0.0, 0.0, 2.0, 0.0, 0.0, 0.0, 2.0]
    const = adapter._osk_blocks[A_FLAT_ID]
    const._values = a1_flat
    const._is_vector = True
    const.output = a1_flat[0]
    assert runner.step_forward(1)["success"] is True
    solver2 = solver_outputs(adapter)
    # Sanity: the driven solve actually changed the solution.
    assert solver2["solution"] == pytest.approx([4.0, -5.5, -1.5])
    assert solver2["solution"] != X_EXPECTED

    # Step back: the committed (A0) snapshot must round-trip exactly.
    assert runner.step_backward(1)["success"] is True

    # The matrix construction blocks are restored to A0.
    assert list(adapter._osk_blocks[A_FLAT_ID].getOutputVector()) == a_flat1
    assert np.allclose(adapter._osk_blocks[A_RESHAPE_ID].getOutputArray(), reshape1)
    # The solver is restored to the A0 solution, not the driven A1 solution.
    assert solver_outputs(adapter) == solver1


# ---------------------------------------------------------------------------
# (f) Deterministic failure: singular A and dimension-invalid inputs
# ---------------------------------------------------------------------------


def test_singular_a_fails_without_stale_or_zero():
    model = load_example_model()
    adapter = run_headless(model, steps=1)
    block = adapter._osk_blocks[SOLVER_ID]

    # A successful solve first, so there is a (stale) solution to check against.
    assert block.status == 1.0
    x_before = list(block.getOutputVector())

    # Drive A to a singular matrix (row 1 = 2 * row 0).
    a_sing_flat = [1.0, 2.0, 3.0, 2.0, 4.0, 6.0, 0.0, 0.0, 1.0]
    const = adapter._osk_blocks[A_FLAT_ID]
    const._values = a_sing_flat
    const._is_vector = True
    const.output = a_sing_flat[0]

    adapter.step(model.simulation_config.step_size, model.simulation_config.step_size)

    # Fails the documented way: reported singular, with a fresh failure value.
    assert block.status == 0.0
    assert block.dimension == 0
    assert "singular" in block.get_status()["reason"].lower()
    out = list(block.getOutputVector())
    # No stale solution, and no zeros substituted for the solution.
    assert out != x_before
    assert all(math.isinf(v) for v in out)
    assert not all(v == 0.0 for v in out)


def test_dimension_invalid_fails_without_stale_or_zero():
    model = load_example_model()
    adapter = run_headless(model, steps=1)
    block = adapter._osk_blocks[SOLVER_ID]

    # A successful solve first, so there is a (stale) solution to check against.
    assert block.status == 1.0
    x_before = list(block.getOutputVector())

    # Drive b to 4 elements while A stays 3x3 -> row-count mismatch.
    b_bad = [1.0, 2.0, 3.0, 4.0]
    const = adapter._osk_blocks[B_VEC_ID]
    const._values = b_bad
    const._is_vector = True
    const.output = b_bad[0]

    adapter.step(model.simulation_config.step_size, model.simulation_config.step_size)

    # Fails the documented way: the dimension mismatch is reported.
    assert block.status == 0.0
    assert block.dimension == 0
    assert block.get_status()["reason"] != ""
    out = list(block.getOutputVector())
    # No stale solution, and no zeros substituted for the solution.
    assert out != x_before
    assert all(math.isinf(v) for v in out)
    assert not all(v == 0.0 for v in out)
