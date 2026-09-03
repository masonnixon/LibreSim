"""Matrix operation blocks for LibreSim.

These blocks handle matrix and vector operations similar to Simulink's
Matrix Operations blocks.

Since Phase 1 of docs/plans/as2-nonlinear-parity-implementation.md the
matrix-capable blocks operate on the shaped signal path: wired inputs are
read through the port view's getOutputArray() (declared 1-D/2-D shape),
computed with numpy, and published back as a flat row-major list plus an
explicit output shape.  Matrices are never silently flattened or degraded
to scalars; shape mismatches raise an error naming the block, the port, and
the expected and actual shapes.
"""

import math
from typing import Any

import numpy as np

from ..block import Block


def _stored_to_array(value):
    """Convert a stored (pushed) input value into an ndarray.

    A single-element list is treated as a 0-D scalar, matching how a
    declared [1] port (a scalar) is exposed on the signal path.  Longer
    lists are 1-D vectors.
    """
    if isinstance(value, (list, tuple)):
        if len(value) == 0:
            return np.asarray(0.0)
        if len(value) == 1:
            return np.asarray(float(value[0]))
        return np.asarray([float(element) for element in value])
    return np.asarray(float(value))


def _reference_to_array(reference):
    """Read a wired input reference as an ndarray with its declared shape.

    Wired references are _OutputPortView objects shaped by the declared
    port dimensions, or (in direct use) raw blocks.  Both expose
    getOutputArray(); the legacy getOutputVector()/getOutput() pair is the
    fallback for minimal stand-ins.
    """
    if hasattr(reference, "getOutputArray"):
        return np.asarray(reference.getOutputArray())
    vector = reference.getOutputVector()
    if vector is not None:
        return np.asarray([float(element) for element in vector])
    return np.asarray(float(reference.getOutput()))


class _MatrixBlock(Block):
    """Flat row-major output storage shared by the matrix-capable blocks.

    A block publishes its result as a flat row-major list (the legacy
    signal path) plus an explicit output shape.  The base class array
    bridge and the port views use that shape to expose the shaped ndarray
    downstream.
    """

    def __init__(self):
        super().__init__()
        self.output = []
        self._output_shape = ()
        self._is_vector = False

    def init(self):
        self.output = []
        self._output_shape = ()
        self._is_vector = False

    def _store_result(self, result):
        array = np.asarray(result, dtype=float)
        self.output = [float(element) for element in array.reshape(-1)]
        self._output_shape = tuple(int(dim) for dim in array.shape)
        self._is_vector = self._output_shape != ()

    def getOutput(self, port=0):
        if 0 <= port < len(self.output):
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        """Flat row-major elements, or None for a scalar (0-D) result."""
        if self._output_shape == ():
            return None
        return list(self.output)

    def getOutputArray(self, port=0):
        """This block's output as an ndarray with its computed shape."""
        if self._output_shape == () or not self.output:
            value = float(self.output[0]) if self.output else 0.0
            return np.asarray(value)
        return np.asarray(self.output, dtype=float).reshape(self._output_shape)

    def _shape_error(self, label, expected, actual, port=None):
        name = getattr(self, "block_id", None) or label
        port_text = f" input port {port}" if port is not None else ""
        return ValueError(
            f"{label} block '{name}':{port_text} shape mismatch - "
            f"expected {expected}, actual {actual}"
        )


class MatrixMultiply(_MatrixBlock):
    """True matrix multiplication.

    Supported products (no broadcasting, exact shapes only):

    - [m, k] x [k, n] -> [m, n]
    - [m, n] x [n]    -> [m]
    - [k] x [k, n]    -> [n]
    - [k] x [k]       -> scalar (the defined row-by-column vector product)
    - scalar x scalar -> scalar; scalar x [n] -> [n]

    A single-element list is a scalar, matching a declared [1] port.
    Anything else is a dimension error naming the block, the port, and the
    expected and actual shapes.
    """

    def __init__(self):
        super().__init__()
        self.input_a = []
        self.input_b = []
        self.input_blocks = [None, None]

    def setInput(self, value, port=0):
        if port == 0:
            self.input_a = value
        elif port == 1:
            self.input_b = value

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block

    def update(self):
        a = self._read_input(0)
        b = self._read_input(1)
        self._store_result(self._multiply(a, b))

    def _read_input(self, port):
        reference = self.input_blocks[port]
        if reference is not None:
            return _reference_to_array(reference)
        stored = self.input_a if port == 0 else self.input_b
        return _stored_to_array(stored)

    def _multiply(self, a, b):
        if a.ndim == 0 and b.ndim == 0:
            return a * b
        if a.ndim == 2 and b.ndim == 2:
            if a.shape[1] == b.shape[0]:
                return a @ b
            raise self._shape_error(
                "MatrixMultiply",
                f"[{a.shape[1]}, n] (inner dimension {a.shape[1]})",
                f"[{b.shape[0]}, {b.shape[1]}]",
                port=1,
            )
        if a.ndim == 2 and b.ndim == 1:
            if b.shape[0] == a.shape[1]:
                return a @ b
            raise self._shape_error(
                "MatrixMultiply",
                f"[{a.shape[1]}] (columns of A)",
                f"[{b.shape[0]}]",
                port=1,
            )
        if a.ndim == 1 and b.ndim == 2:
            if a.shape[0] == b.shape[0]:
                return a @ b
            raise self._shape_error(
                "MatrixMultiply",
                f"[{b.shape[0]}] (rows of B)",
                f"[{a.shape[0]}]",
                port=0,
            )
        if a.ndim == 1 and b.ndim == 1:
            if a.shape[0] == b.shape[0]:
                return a @ b
            raise self._shape_error(
                "MatrixMultiply",
                f"[{b.shape[0]}] (equal length to B)",
                f"[{a.shape[0]}]",
                port=0,
            )
        if a.ndim == 0 and b.ndim == 1:
            return a * b
        if a.ndim == 1 and b.ndim == 0:
            return a * b
        raise self._shape_error(
            "MatrixMultiply",
            "a matching vector or matrix",
            "a scalar combined with a 2-D matrix",
            port=0 if a.ndim == 0 else 1,
        )


class MatrixTranspose(_MatrixBlock):
    """Transpose a matrix.

    [m, n] -> [n, m]; 1-D vectors and scalars are unchanged.
    """

    def __init__(self):
        super().__init__()
        self.input = []
        self.input_block = None

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            array = _reference_to_array(self.input_block)
        else:
            array = _stored_to_array(self.input)
        self._store_result(array.T)


class MatrixInverse(_MatrixBlock):
    """Inverse of a 2-D square matrix.

    A declared [n, n] input is inverted with numpy.  A flat 4-element input
    is interpreted as a row-major 2x2 matrix (legacy convention); any other
    flat vector passes through unchanged; a scalar inverts as 1/x (zero
    inverts to inf, never an exception).  A non-square 2-D input is a
    dimension error.
    """

    def __init__(self):
        super().__init__()
        self.input = []
        self.input_block = None

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            array = _reference_to_array(self.input_block)
        else:
            array = _stored_to_array(self.input)
        self._invert(array)

    def _invert(self, array):
        if array.ndim == 0:
            value = float(array)
            self.output = [1.0 / value if value != 0.0 else float("inf")]
            self._output_shape = ()
            self._is_vector = False
            return
        if array.ndim == 1:
            if array.shape[0] == 4:
                matrix = array.reshape(2, 2)
            else:
                # Legacy flat pass-through for non-matrix vectors.
                self.output = [float(element) for element in array]
                self._output_shape = (int(array.shape[0]),)
                self._is_vector = True
                return
        else:
            if array.shape[0] != array.shape[1]:
                raise self._shape_error(
                    "MatrixInverse",
                    "a square matrix",
                    f"[{array.shape[0]}, {array.shape[1]}]",
                    port=0,
                )
            matrix = array
        try:
            inverted = np.linalg.inv(matrix)
        except np.linalg.LinAlgError:
            self.output = [float("inf")] * int(matrix.size)
            self._output_shape = (int(matrix.shape[0]), int(matrix.shape[1]))
            self._is_vector = True
            return
        self._store_result(inverted)


class Selector(_MatrixBlock):
    """Select elements from a vector or matrix.

    Indices address elements in row-major order, so a 2-D input can be
    sliced by rows, columns, or individual cells.  Out-of-range (including
    negative) indices select 0.0.  A single index produces a scalar output;
    multiple indices produce a 1-D vector.
    """

    def __init__(self, indices=None, output_size=1):
        super().__init__()
        self.indices = indices if indices else [0]
        self.output_size = output_size
        self.input = []
        self.input_block = None

    def init(self):
        self.output = [0.0] * len(self.indices)
        self._output_shape = () if len(self.indices) == 1 else (len(self.indices),)
        self._is_vector = len(self.indices) > 1

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            array = _reference_to_array(self.input_block)
        else:
            array = _stored_to_array(self.input)
        flat = [float(element) for element in array.reshape(-1)]
        selected = []
        for index in self.indices:
            if 0 <= index < len(flat):
                selected.append(flat[index])
            else:
                selected.append(0.0)
        self.output = selected
        self._output_shape = () if len(self.indices) == 1 else (len(selected),)
        self._is_vector = len(self.indices) > 1


class Assignment(_MatrixBlock):
    """Assign values to elements of a vector or matrix.

    Indices address the base signal in row-major order, so a 2-D base can
    have rows, columns, or individual cells replaced.  Out-of-range indices
    are skipped.  The output keeps the base signal's shape.
    """

    def __init__(self, indices=None):
        super().__init__()
        self.indices = indices if indices else [0]
        self.input_base = []
        self.input_values = []
        self.input_blocks = [None, None]

    def setInput(self, value, port=0):
        if port == 0:
            self.input_base = value
        elif port == 1:
            self.input_values = value

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block

    def update(self):
        if self.input_blocks[0] is not None:
            base = _reference_to_array(self.input_blocks[0])
        else:
            base = _stored_to_array(self.input_base)
        if self.input_blocks[1] is not None:
            values = _reference_to_array(self.input_blocks[1])
        else:
            values = _stored_to_array(self.input_values)

        out = [float(element) for element in base.reshape(-1)]
        value_elements = [float(element) for element in values.reshape(-1)]
        for i, index in enumerate(self.indices):
            if 0 <= index < len(out) and i < len(value_elements):
                out[index] = value_elements[i]
        self.output = out
        self._output_shape = tuple(int(dim) for dim in base.shape)
        self._is_vector = base.ndim > 0


class Concatenate(_MatrixBlock):
    """Concatenate vectors or matrices.

    1-D and scalar inputs concatenate flat (legacy behavior).  2-D inputs
    require every input to be 2-D: mode "horizontal" stacks columns
    ([A B], rows must match), any other mode stacks rows ([A; B], columns
    must match).  Mixing 2-D and lower-rank inputs is an error.
    """

    def __init__(self, num_inputs=2, mode="vector"):
        super().__init__()
        self.num_inputs = num_inputs
        self.mode = mode
        self.inputs: list[Any] = [[] for _ in range(num_inputs)]
        self.input_blocks: list[Any] = [None] * num_inputs

    def setInput(self, value, port=0):
        if port < self.num_inputs:
            self.inputs[port] = value

    def connectInput(self, block, port=0, source_port=0):
        if port < self.num_inputs:
            self.input_blocks[port] = block

    def update(self):
        arrays = []
        for i, reference in enumerate(self.input_blocks):
            if reference is not None:
                arrays.append(_reference_to_array(reference))
            else:
                arrays.append(_stored_to_array(self.inputs[i]))

        if any(array.ndim == 2 for array in arrays):
            if any(array.ndim != 2 for array in arrays):
                ranks = sorted({array.ndim for array in arrays})
                raise self._shape_error(
                    "Concatenate",
                    "all inputs to be 2-D matrices",
                    f"mixed ranks {ranks}",
                )
            if self.mode == "horizontal":
                rows = arrays[0].shape[0]
                for i, array in enumerate(arrays):
                    if array.shape[0] != rows:
                        raise self._shape_error(
                            "Concatenate",
                            f"{rows} rows (horizontal concatenation)",
                            f"[{array.shape[0]}, {array.shape[1]}]",
                            port=i,
                        )
                combined = np.concatenate(arrays, axis=1)
            else:
                columns = arrays[0].shape[1]
                for i, array in enumerate(arrays):
                    if array.shape[1] != columns:
                        raise self._shape_error(
                            "Concatenate",
                            f"{columns} columns (vertical concatenation)",
                            f"[{array.shape[0]}, {array.shape[1]}]",
                            port=i,
                        )
                combined = np.concatenate(arrays, axis=0)
            self._store_result(combined)
            return

        flat = []
        for array in arrays:
            flat.extend(float(element) for element in array.reshape(-1))
        self.output = flat
        self._output_shape = (len(flat),) if len(flat) > 1 else ()
        self._is_vector = len(flat) > 1

    def getNumOutputs(self):
        return len(self.output) if self.output else 1


class MatrixIdentity(_MatrixBlock):
    """Constant n x n identity matrix source (no inputs)."""

    def __init__(self, n=1):
        super().__init__()
        self.n = int(n)
        if self.n < 1:
            raise ValueError(
                f"MatrixIdentity block: size must be a positive integer, got {n!r}"
            )
        self._recompute()

    def update(self):
        self._recompute()

    def _recompute(self):
        self.output = [1.0 if i == j else 0.0 for i in range(self.n) for j in range(self.n)]
        self._output_shape = (self.n, self.n)
        self._is_vector = True


class MatrixZeros(_MatrixBlock):
    """Constant rows x cols matrix of zeros (no inputs)."""

    def __init__(self, rows=1, cols=1):
        super().__init__()
        self.rows = int(rows)
        self.cols = int(cols)
        if self.rows < 1 or self.cols < 1:
            raise ValueError(
                f"MatrixZeros block: rows and cols must be positive integers, "
                f"got {rows!r} x {cols!r}"
            )
        self._recompute()

    def update(self):
        self._recompute()

    def _recompute(self):
        self.output = [0.0] * (self.rows * self.cols)
        self._output_shape = (self.rows, self.cols)
        self._is_vector = True


def _parse_vector(values):
    """Coerce a constant vector parameter into a list of numbers."""
    if values is None:
        return []
    if isinstance(values, (list, tuple)):
        return [float(element) for element in values]
    return [float(values)]


class MatrixDiagonal(_MatrixBlock):
    """Constant diagonal matrix built from a vector (no inputs)."""

    def __init__(self, values=None):
        super().__init__()
        self.values = _parse_vector(values)
        if not self.values:
            raise ValueError("MatrixDiagonal block: values must be a non-empty list")
        self._recompute()

    def update(self):
        self._recompute()

    def _recompute(self):
        size = len(self.values)
        flat = [0.0] * (size * size)
        for i, value in enumerate(self.values):
            flat[i * size + i] = value
        self.output = flat
        self._output_shape = (size, size)
        self._is_vector = True


class MatrixReshape(_MatrixBlock):
    """Reshape a flat vector or matrix into a constant rows x cols shape.

    The input's row-major elements are reinterpreted as a [rows, cols]
    matrix; the element count must match rows * cols exactly.
    """

    def __init__(self, rows=1, cols=1):
        super().__init__()
        self.rows = int(rows)
        self.cols = int(cols)
        if self.rows < 1 or self.cols < 1:
            raise ValueError(
                f"MatrixReshape block: rows and cols must be positive integers, "
                f"got {rows!r} x {cols!r}"
            )
        self.input = []
        self.input_block = None

    def init(self):
        super().init()
        self._output_shape = (self.rows, self.cols)
        self._is_vector = True

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            array = _reference_to_array(self.input_block)
        else:
            array = _stored_to_array(self.input)
        flat = array.reshape(-1)
        expected = self.rows * self.cols
        if flat.size != expected:
            raise self._shape_error(
                "MatrixReshape",
                f"{expected} elements to fill shape [{self.rows}, {self.cols}]",
                f"{flat.size} elements (input shape {list(array.shape)})",
                port=0,
            )
        self.output = [float(element) for element in flat]
        self._output_shape = (self.rows, self.cols)
        self._is_vector = True


class MatrixSum(Block):
    """Sum elements of a matrix/vector.

    Computes sum across specified dimension or all elements.
    """

    def __init__(self, dimension="all"):
        super().__init__()
        self.dimension = dimension  # 'all', 'rows', 'columns'
        self.input = []
        self.output = 0.0
        self.input_block = None

    def init(self):
        self.output = 0.0

    def setInput(self, value, port=0):
        self.input = value if isinstance(value, list) else [value]

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            vec = self.input_block.getOutputVector()
            if vec is not None:
                self.input = vec
            else:
                self.input = [self.input_block.getOutput()]

        self.output = sum(self.input)

    def getOutput(self, port=0):
        return self.output


class VectorNorm(Block):
    """Compute norm of a vector.

    Supports: 2-norm (Euclidean), 1-norm (Manhattan), inf-norm (maximum).
    """

    def __init__(self, norm_type="2"):
        super().__init__()
        self.norm_type = norm_type  # '1', '2', 'inf'
        self.input = []
        self.output = 0.0
        self.input_block = None

    def init(self):
        self.output = 0.0

    def setInput(self, value, port=0):
        self.input = value if isinstance(value, list) else [value]

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            vec = self.input_block.getOutputVector()
            if vec is not None:
                self.input = vec
            else:
                self.input = [self.input_block.getOutput()]

        if self.norm_type == "1":
            self.output = sum(abs(x) for x in self.input)
        elif self.norm_type == "2":
            self.output = math.sqrt(sum(x * x for x in self.input))
        elif self.norm_type == "inf":
            self.output = max(abs(x) for x in self.input) if self.input else 0.0
        else:
            self.output = math.sqrt(sum(x * x for x in self.input))

    def getOutput(self, port=0):
        return self.output
