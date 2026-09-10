"""Direct-instantiation branch coverage for LinearSolve and matrix_ops blocks.

These exercise construction/accessor/error branches that the acceptance-style
tests (test_linear_solve.py, which builds every model through the full
Model/ModelCompiler/OSKAdapter pipeline) don't reach on their own -
constructor validation, direct setInput/connectInput protocol calls, and a
few numerically hard-to-trigger failure paths. Following the same
direct-construction convention already used in
test_navigation_matrix_coverage.py.
"""

import math
from unittest.mock import patch

import pytest

from src.osk.blocks.linear_algebra import (
    LinearSolve,
    _reference_to_array,
    _stored_to_array,
)
from src.osk.blocks.matrix_ops import (
    Concatenate,
    MatrixDiagonal,
    MatrixMultiply,
    MatrixReshape,
    _parse_vector,
)


class Source:
    """Minimal wired-input stand-in exposing only the legacy vector/scalar
    protocol (no getOutputArray), matching the _reference_to_array fallback.
    """

    def __init__(self, vector=None, scalar=0.0):
        self.vector = vector
        self.scalar = scalar

    def getOutputVector(self):
        return self.vector

    def getOutput(self, port=0):
        return self.scalar


class MatrixSource:
    """Wired-input stand-in exposing a shaped array via getOutputArray,
    for 2-D (or higher) values that Source's flat vector/scalar protocol
    cannot represent.
    """

    def __init__(self, values):
        self.values = values

    def getOutputArray(self):
        return self.values


# ---------------------------------------------------------------------------
# LinearSolve
# ---------------------------------------------------------------------------


def test_constructor_rejects_every_invalid_parameter():
    with pytest.raises(ValueError, match="unsupported method"):
        LinearSolve(method="qr")
    with pytest.raises(ValueError, match="unsupported pivoting"):
        LinearSolve(pivoting="full")
    with pytest.raises(ValueError, match="unsupported failure_policy"):
        LinearSolve(failure_policy="ignore")
    with pytest.raises(ValueError, match="singularity_tolerance must be non-negative"):
        LinearSolve(singularity_tolerance=-1.0)
    with pytest.raises(ValueError, match="condition_limit must be positive"):
        LinearSolve(condition_limit=0.0)


def test_accessors_before_any_solve():
    block = LinearSolve()
    assert block.getOutput(0) == 0.0
    assert block.getOutput(9) == 0.0  # Out-of-range port falls through to 0.0.
    assert block.getOutputVector() is None
    assert block.getOutputArray() == pytest.approx(0.0)


def test_setinput_and_connectinput_protocol():
    block = LinearSolve()
    block.setInput([4.0], 0)
    block.setInput([8.0], 1)
    block.setInput(99.0, 5)  # Out-of-range port is a no-op.
    block.update()
    assert block.status == 1.0
    assert block.getOutputVector() == pytest.approx([2.0])

    block.connectInput(MatrixSource([[2.0, 1.0], [1.0, 3.0]]), 0)
    block.connectInput(Source([3.0, 5.0]), 1)
    block.connectInput(Source(None, 99.0), 5)  # Out-of-range port is a no-op.
    block.update()
    assert block.status == 1.0
    assert block.getOutputVector() == pytest.approx([0.8, 1.4])


def test_a_given_as_a_bare_scalar_is_a_1x1_matrix():
    block = LinearSolve()
    block.setInput([5.0], 0)  # A single-element list collapses to a 0-D scalar.
    block.setInput([10.0], 1)
    block.update()
    assert block.status == 1.0
    assert block.getOutputVector() == pytest.approx([2.0])


def test_a_given_as_a_nonsquare_vector_fails():
    block = LinearSolve()
    block.connectInput(Source([1.0, 2.0, 3.0]), 0)  # 1-D, length 3: not square.
    block.connectInput(Source([1.0, 2.0, 3.0]), 1)
    block.update()
    assert block.status == 0.0
    assert "square matrix" in block.get_status()["reason"]


def test_b_with_more_than_two_dimensions_fails():
    block = LinearSolve()
    block.connectInput(MatrixSource([[1.0, 0.0], [0.0, 1.0]]), 0)
    block.connectInput(MatrixSource([[[1.0]], [[2.0]]]), 1)  # 3-D b.
    block.update()
    assert block.status == 0.0
    assert "vector or matrix" in block.get_status()["reason"]


def test_non_finite_residual_is_reported_as_failure():
    block = LinearSolve()
    block.setInput([1.0], 0)
    block.setInput([math.inf], 1)
    block.update()
    assert block.status == 0.0
    assert "non-finite residual" in block.get_status()["reason"]


def test_condition_estimate_falls_back_to_inf_on_exception():
    block = LinearSolve()
    with patch("src.osk.blocks.linear_algebra.np.linalg.cond", side_effect=ValueError("boom")):
        assert block._condition_estimate([[1.0, 0.0], [0.0, 1.0]]) == math.inf


def test_raise_failure_policy_raises_instead_of_setting_status():
    block = LinearSolve(failure_policy="raise")
    block.setInput([0.0], 0)  # Singular (zero) A.
    block.setInput([1.0], 1)
    with pytest.raises(RuntimeError, match="linear_solve:"):
        block.update()


def test_stored_to_array_helper_branches():
    assert _stored_to_array([]).tolist() == 0.0
    assert _stored_to_array([5.0]).ndim == 0
    assert _stored_to_array([[1.0, 2.0], [3.0, 4.0]]).tolist() == [[1.0, 2.0], [3.0, 4.0]]
    assert _stored_to_array(5.0).tolist() == 5.0  # A bare (non-list) scalar.


def test_a_given_as_a_1d_single_element_array_is_a_1x1_matrix():
    # Unlike a stored single-element list (which _stored_to_array collapses
    # to 0-D), a wired source's getOutputArray() can hand back a genuinely
    # 1-D, length-1 array; that also normalizes to a 1x1 matrix.
    block = LinearSolve()
    block.connectInput(MatrixSource([5.0]), 0)
    block.connectInput(MatrixSource([10.0]), 1)
    block.update()
    assert block.status == 1.0
    assert block.getOutputVector() == pytest.approx([2.0])


def test_reference_to_array_fallback_without_getoutputarray():
    assert _reference_to_array(Source([1.0, 2.0])).tolist() == [1.0, 2.0]
    assert _reference_to_array(Source(None, 7.0)).tolist() == 7.0


# ---------------------------------------------------------------------------
# matrix_ops
# ---------------------------------------------------------------------------


def test_matrix_block_getoutputarray_scalar_branch():
    block = MatrixMultiply()
    block.connectInput(Source(None, 2.0), 0)
    block.connectInput(Source(None, 3.0), 1)
    block.update()
    assert block.getOutputArray().tolist() == pytest.approx(6.0)


def test_matrix_multiply_shape_mismatches():
    matrix_vector = MatrixMultiply()
    matrix_vector.connectInput(MatrixSource([[1.0, 2.0], [3.0, 4.0]]), 0)
    matrix_vector.connectInput(Source([1.0, 2.0, 3.0]), 1)  # Wrong length for [2,2].
    with pytest.raises(ValueError, match="columns of A"):
        matrix_vector.update()

    vector_matrix = MatrixMultiply()
    vector_matrix.connectInput(Source([1.0, 2.0, 3.0]), 0)
    vector_matrix.connectInput(MatrixSource([[1.0, 2.0], [3.0, 4.0]]), 1)  # Rows=2, not 3.
    with pytest.raises(ValueError, match="rows of B"):
        vector_matrix.update()

    vector_vector = MatrixMultiply()
    vector_vector.connectInput(Source([1.0, 2.0]), 0)
    vector_vector.connectInput(Source([1.0, 2.0, 3.0]), 1)
    with pytest.raises(ValueError, match="equal length to B"):
        vector_vector.update()


def test_concatenate_horizontal_row_mismatch():
    concatenate = Concatenate(num_inputs=2, mode="horizontal")
    concatenate.connectInput(MatrixSource([[1.0, 2.0], [3.0, 4.0]]), 0)
    concatenate.connectInput(MatrixSource([[1.0, 2.0]]), 1)  # 1 row vs 2 rows.
    with pytest.raises(ValueError, match="horizontal concatenation"):
        concatenate.update()


def test_parse_vector_none_and_scalar_branches():
    assert _parse_vector(None) == []
    assert _parse_vector(5.0) == [5.0]
    assert _parse_vector([1.0, 2.0]) == [1.0, 2.0]

    with pytest.raises(ValueError, match="non-empty list"):
        MatrixDiagonal(values=None)

    diag = MatrixDiagonal(values=3.0)
    assert diag.output == [3.0]


def test_matrix_reshape_setinput_and_unwired_update():
    reshape = MatrixReshape(rows=2, cols=2)
    reshape.setInput([1.0, 2.0, 3.0, 4.0])
    reshape.update()
    assert reshape.output == [1.0, 2.0, 3.0, 4.0]
    assert reshape._output_shape == (2, 2)
