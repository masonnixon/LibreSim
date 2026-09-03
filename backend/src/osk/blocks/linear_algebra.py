"""Native linear solver block for LibreSim.

Implements Phase 2 of
``docs/plans/as2-nonlinear-parity-implementation.md``: a general, native
linear solver for ``A x = b`` built on ``scipy.linalg`` LU factorization with
partial pivoting.

Design points, fixed by the plan and the solver state contract:

- The factorization is rebuilt on every call.  There is no cross-step cache,
  so the block's outputs are a pure function of the current step's inputs and
  a reset, a failed evaluation, a step-back, or a repeated run can never
  re-emit a previous step's solution.
- The right-hand side ``b`` may be a vector ``[n]`` (a single solution) or a
  matrix ``[n, m]`` (``m`` simultaneous solutions); both use identical LU
  semantics because the same factorization is applied to every column.
- The solver never uses an explicit inverse and never silently substitutes a
  pseudoinverse.  Structural problems (nonsquare ``A``, dimension-mismatched
  ``b``) and numerical problems (singular, ill-conditioned) are reported
  through deterministic status outputs, and the solution port is filled with
  a fresh failure value rather than the last good one.
"""

import math
from typing import Any

import numpy as np
from scipy import linalg as sla

from ..block import Block


#: Machine-precision lower bound used as the default ill-conditioning limit:
#: a system whose condition number exceeds 1/eps has lost essentially all
#: digits and cannot be solved reliably in double precision.
_DEFAULT_CONDITION_LIMIT = 1.0 / np.finfo(float).eps


def _stored_to_array(value: Any) -> np.ndarray:
    """Convert a stored (pushed) input value into an ndarray.

    Mirrors the convention in ``matrix_ops``: a single-element list is a 0-D
    scalar (matching a declared ``[1]`` port), longer lists are 1-D vectors,
    and nested lists keep their 2-D shape.
    """
    if isinstance(value, (list, tuple)):
        if len(value) == 0:
            return np.asarray(0.0)
        if len(value) == 1 and not isinstance(value[0], (list, tuple)):
            return np.asarray(float(value[0]))
        return np.asarray(value, dtype=float)
    return np.asarray(float(value))


def _reference_to_array(reference) -> np.ndarray:
    """Read a wired input reference as an ndarray with its declared shape.

    Wired references are ``_OutputPortView`` objects shaped by the declared
    port dimensions; the legacy ``getOutputVector()``/``getOutput()`` pair is
    the fallback for minimal stand-ins.
    """
    if hasattr(reference, "getOutputArray"):
        return np.asarray(reference.getOutputArray())
    vector = reference.getOutputVector()
    if vector is not None:
        return np.asarray([float(element) for element in vector])
    return np.asarray(float(reference.getOutput()))


class LinearSolve(Block):
    """Solve ``A x = b`` by LU factorization with partial pivoting.

    Inputs:
        port 0 -- ``A``: a square matrix ``[n, n]`` (2-D).
        port 1 -- ``b``: a right-hand side, either a vector ``[n]`` or a
            matrix of right-hand sides ``[n, m]``.

    Solution output (port 0):
        A vector ``[n]`` when ``b`` is a vector, or a matrix ``[n, m]`` when
        ``b`` is a matrix, exposed flat row-major (``getOutputVector``) and as
        a shaped ndarray (``getOutputArray``).

    Status outputs (never alter the numeric solution):
        ``status``    -- 1.0 on success, 0.0 on failure.
        ``residual``  -- ``||A x - b||`` of the published solution (inf on failure).
        ``condition`` -- ``np.linalg.cond(A)`` estimate (inf when not computable).
        ``dimension`` -- active problem size ``n`` on success, 0 on failure.
        ``get_status()`` -- all of the above plus a human-readable ``reason``.
    """

    # -- construction -----------------------------------------------------

    def __init__(
        self,
        method: str = "lu",
        pivoting: str = "partial",
        singularity_tolerance: float = 1e-12,
        condition_limit: float = _DEFAULT_CONDITION_LIMIT,
        failure_policy: str = "status",
    ):
        super().__init__()
        method = str(method).strip().lower()
        if method not in {"lu"}:
            raise ValueError(
                "LinearSolve block: unsupported method "
                f"{method!r}; only 'lu' (LU with partial pivoting) is provided"
            )
        pivoting = str(pivoting).strip().lower()
        if pivoting not in {"partial"}:
            raise ValueError(
                "LinearSolve block: unsupported pivoting "
                f"{pivoting!r}; only 'partial' is provided"
            )
        failure_policy = str(failure_policy).strip().lower()
        if failure_policy not in {"status", "raise"}:
            raise ValueError(
                "LinearSolve block: unsupported failure_policy "
                f"{failure_policy!r}; expected 'status' or 'raise'"
            )
        if singularity_tolerance < 0.0:
            raise ValueError(
                "LinearSolve block: singularity_tolerance must be non-negative, "
                f"got {singularity_tolerance!r}"
            )
        if condition_limit <= 0.0:
            raise ValueError(
                "LinearSolve block: condition_limit must be positive, "
                f"got {condition_limit!r}"
            )

        self.method = method
        self.pivoting = pivoting
        self.singularity_tolerance = float(singularity_tolerance)
        self.condition_limit = float(condition_limit)
        self.failure_policy = failure_policy

        # Solution storage: flat row-major elements plus an explicit shape.
        self.output: list[float] = []
        self._solution_shape: tuple[int, ...] = ()

        # Status outputs (deterministic; never alter the numeric solution).
        self.status = 0.0
        self.residual = math.inf
        self.condition = math.inf
        self.dimension = 0
        self._failure_reason = ""

        # Inputs.
        self.input_blocks = [None, None]
        self._inputs: list[Any] = [[], []]

    def init(self):
        """Reset to a clean, non-stale state at the start of each stage."""
        self.output = []
        self._solution_shape = ()
        self.status = 0.0
        self.residual = math.inf
        self.condition = math.inf
        self.dimension = 0
        self._failure_reason = ""

    # -- inputs -----------------------------------------------------------

    def setInput(self, value, port=0):
        if port in (0, 1):
            self._inputs[port] = value

    def connectInput(self, block, port=0, source_port=0):
        if port in (0, 1):
            self.input_blocks[port] = block

    # -- solution output accessors ---------------------------------------

    def getOutput(self, port=0):
        if 0 <= port < len(self.output):
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        """Flat row-major solution elements, or None when there is no output."""
        if self._solution_shape == ():
            return None
        return list(self.output)

    def getOutputArray(self, port=0):
        """The solution as an ndarray with its computed shape."""
        if self._solution_shape == () or not self.output:
            value = self.output[0] if self.output else 0.0
            return np.asarray(value, dtype=float)
        return np.asarray(self.output, dtype=float).reshape(self._solution_shape)

    # -- status accessors -------------------------------------------------

    def get_status(self):
        """Return the deterministic status bundle for the current step."""
        return {
            "status": self.status,
            "residual": self.residual,
            "condition": self.condition,
            "dimension": self.dimension,
            "reason": self._failure_reason,
        }

    # -- stepping ---------------------------------------------------------

    def update(self):
        a = self._read_input(0)
        b = self._read_input(1)
        self._solve(a, b)

    def _read_input(self, port):
        reference = self.input_blocks[port]
        if reference is not None:
            return _reference_to_array(reference)
        return _stored_to_array(self._inputs[port])

    # -- solver -----------------------------------------------------------

    def _solve(self, a, b):
        a = np.asarray(a, dtype=float)
        b = np.asarray(b, dtype=float)

        # Normalize A to 2-D; a lone element is a 1x1 matrix.
        if a.ndim == 0:
            a = a.reshape(1, 1)
        elif a.ndim == 1:
            if a.shape[0] == 1:
                a = a.reshape(1, 1)
            else:
                self._fail(
                    a.shape[0], math.inf, f"A must be a square matrix, got shape {list(a.shape)}"
                )
                return

        n_rows, n_cols = a.shape
        if n_rows != n_cols:
            self._fail(
                n_cols,
                math.inf,
                f"A must be square, got [{n_rows}, {n_cols}]",
            )
            return

        # Normalize b to a 2-D matrix of right-hand sides [n, m].
        if b.ndim == 0:
            b = b.reshape(1)
        if b.ndim == 1:
            b_matrix = b.reshape(-1, 1)
        elif b.ndim == 2:
            b_matrix = b
        else:
            self._fail(
                n_cols, math.inf, f"b must be a vector or matrix, got shape {list(b.shape)}"
            )
            return

        if b_matrix.shape[0] != n_rows:
            self._fail(
                n_cols,
                math.inf,
                f"b rows {b_matrix.shape[0]} do not match A rows {n_rows}",
            )
            return

        # Condition estimate is a property of A; report it even when the
        # solve ultimately fails, when it is computable.
        condition = self._condition_estimate(a)

        # Factor with partial pivoting; rebuild on every call (no cache).
        try:
            lu, piv = sla.lu_factor(a, overwrite_a=False, check_finite=False)
        except Exception as exc:  # pragma: no cover - scipy raises LinAlgError
            self._fail(n_cols, condition, f"LU factorization failed: {exc}")
            return

        # Singularity is decided first, from the pivots on the diagonal of U.
        # A pivot at or below the accumulated rounding error of the
        # elimination is indistinguishable from zero: the computed
        # factorization is numerically rank-deficient and the system is
        # reported as singular, taking precedence over the ill-conditioning
        # test (whose floating-point condition number is only a large
        # artifact for such a system).
        #
        # The floor is the machine-precision noise of this arithmetic,
        # singularity_tolerance * eps * n * max_pivot, NOT a fixed fraction
        # of the largest pivot: the pivot *ratio* measures scaling, and a
        # nonsingular but badly scaled system (e.g. diag(1e-6, 1e6), whose
        # pivot ratio is 1e-12) must be solved here; its near-singularity is
        # judged by the condition estimate against condition_limit below.
        pivots = np.abs(np.diag(lu))
        max_pivot = float(pivots.max()) if pivots.size else 0.0
        pivot_floor = self.singularity_tolerance * np.finfo(float).eps * n_cols * max_pivot
        if max_pivot == 0.0 or float(pivots.min()) <= pivot_floor:
            self._fail(
                n_cols,
                condition,
                f"singular system: minimum pivot {float(pivots.min()):.3e} is at or "
                f"below the numerical singularity floor {pivot_floor:.3e}",
            )
            return

        # Ill-conditioned systems (solvable but unreliable) are rejected here.
        if (not math.isfinite(condition)) or condition > self.condition_limit:
            self._fail(
                n_cols,
                condition,
                f"ill-conditioned system: cond(A) ~ {condition:.3e} exceeds limit "
                f"{self.condition_limit:.3e}",
            )
            return

        try:
            x = sla.lu_solve((lu, piv), b_matrix, overwrite_b=False, check_finite=False)
        except Exception as exc:  # pragma: no cover
            self._fail(n_cols, condition, f"LU solve failed: {exc}")
            return

        x = np.asarray(x, dtype=float)
        residual = float(np.linalg.norm(a @ x - b_matrix))
        if not math.isfinite(residual):
            self._fail(n_cols, condition, f"non-finite residual {residual:.3e}")
            return

        # Publish the fresh solution (never a previous step's value).
        flat = [float(element) for element in x.reshape(-1)]
        if b_matrix.shape[1] == 1:
            shape = (int(n_cols),)
        else:
            shape = (int(n_cols), int(b_matrix.shape[1]))
        self.output = flat
        self._solution_shape = shape
        self.status = 1.0
        self.residual = residual
        self.condition = float(condition)
        self.dimension = int(n_cols)
        self._failure_reason = ""

    def _condition_estimate(self, a):
        try:
            return float(np.linalg.cond(a))
        except Exception:
            return math.inf

    def _fail(self, cols, condition, reason):
        """Report a deterministic failure; never re-emit the previous solution."""
        if self.failure_policy == "raise":
            raise RuntimeError(f"linear_solve: {reason}")
        size = max(int(cols), 1)
        self.output = [float("inf")] * size
        self._solution_shape = (size,)
        self.status = 0.0
        self.residual = math.inf
        self.condition = float(condition) if condition is not None else math.inf
        self.dimension = 0
        self._failure_reason = reason
