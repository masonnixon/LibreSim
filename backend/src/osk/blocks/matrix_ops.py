"""Matrix operation blocks for LibreSim.

These blocks handle matrix and vector operations similar to Simulink's
Matrix Operations blocks.
"""

import math

from ..block import Block


class MatrixMultiply(Block):
    """Multiply matrices or matrix-vector products.

    Performs matrix multiplication of two inputs.
    For vectors, treats first as row vector, second as column vector.
    """

    def __init__(self):
        super().__init__()
        self.input_a = []
        self.input_b = []
        self.output = []
        self.input_blocks = [None, None]
        self._is_vector = False

    def init(self):
        self.output = []

    def setInput(self, value, port=0):
        if port == 0:
            self.input_a = value if isinstance(value, list) else [value]
        elif port == 1:
            self.input_b = value if isinstance(value, list) else [value]

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block

    def update(self):
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                vec = block.getOutputVector()
                if vec is not None:
                    if i == 0:
                        self.input_a = vec
                    else:
                        self.input_b = vec
                else:
                    val = block.getOutput()
                    if i == 0:
                        self.input_a = [val]
                    else:
                        self.input_b = [val]

        # For 1D vectors, compute dot product
        if len(self.input_a) == len(self.input_b):
            result = sum(a * b for a, b in zip(self.input_a, self.input_b, strict=False))
            self.output = [result]
            self._is_vector = False
        else:
            # Treat as scalars
            self.output = [
                self.input_a[0] * self.input_b[0] if self.input_a and self.input_b else 0.0
            ]
            self._is_vector = False

    def getOutput(self, port=0):
        if self.output:
            return self.output[0] if port < len(self.output) else 0.0
        return 0.0

    def getOutputVector(self):
        return self.output if len(self.output) > 1 else None


class MatrixTranspose(Block):
    """Transpose a matrix or vector.

    For vectors, converts row to column and vice versa.
    Since we work with 1D arrays, this is essentially a pass-through.
    """

    def __init__(self):
        super().__init__()
        self.input = []
        self.output = []
        self.input_block = None
        self._is_vector = False

    def init(self):
        self.output = []

    def setInput(self, value, port=0):
        self.input = value if isinstance(value, list) else [value]

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            vec = self.input_block.getOutputVector()
            if vec is not None:
                self.input = vec
                self._is_vector = True
            else:
                self.input = [self.input_block.getOutput()]
                self._is_vector = False

        # For 1D representation, transpose is identity
        self.output = self.input.copy()

    def getOutput(self, port=0):
        if port < len(self.output):
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output if self._is_vector else None


class MatrixInverse(Block):
    """Compute inverse of a matrix.

    For scalars, returns 1/x.
    For 2x2 matrices (4-element vector), computes actual inverse.
    """

    def __init__(self):
        super().__init__()
        self.input = []
        self.output = []
        self.input_block = None
        self._is_vector = False

    def init(self):
        self.output = []

    def setInput(self, value, port=0):
        self.input = value if isinstance(value, list) else [value]

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            vec = self.input_block.getOutputVector()
            if vec is not None:
                self.input = vec
                self._is_vector = True
            else:
                self.input = [self.input_block.getOutput()]
                self._is_vector = False

        n = len(self.input)

        if n == 1:
            # Scalar inverse
            self.output = [1.0 / self.input[0]] if self.input[0] != 0 else [float("inf")]
        elif n == 4:
            # 2x2 matrix inverse: [[a,b],[c,d]] stored as [a,b,c,d]
            a, b, c, d = self.input
            det = a * d - b * c
            if abs(det) > 1e-15:
                self.output = [d / det, -b / det, -c / det, a / det]
            else:
                self.output = [float("inf")] * 4
        else:
            # Pass through for unsupported sizes
            self.output = self.input.copy()

    def getOutput(self, port=0):
        if port < len(self.output):
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output if self._is_vector else None


class Selector(Block):
    """Select elements from a vector or matrix.

    Selects specific elements or ranges from the input signal.
    """

    def __init__(self, indices=None, output_size=1):
        super().__init__()
        self.indices = indices if indices else [0]
        self.output_size = output_size
        self.input = []
        self.output = []
        self.input_block = None
        self._is_vector = False

    def init(self):
        self.output = [0.0] * self.output_size

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

        self.output = []
        for idx in self.indices:
            if 0 <= idx < len(self.input):
                self.output.append(self.input[idx])
            else:
                self.output.append(0.0)

        self._is_vector = len(self.output) > 1

    def getOutput(self, port=0):
        if port < len(self.output):
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output if self._is_vector else None


class Assignment(Block):
    """Assign values to specific elements of a vector.

    Takes an input vector and replaces elements at specified indices
    with values from a second input.
    """

    def __init__(self, indices=None):
        super().__init__()
        self.indices = indices if indices else [0]
        self.input_base = []
        self.input_values = []
        self.output = []
        self.input_blocks = [None, None]
        self._is_vector = True

    def init(self):
        self.output = []

    def setInput(self, value, port=0):
        if port == 0:
            self.input_base = value if isinstance(value, list) else [value]
        elif port == 1:
            self.input_values = value if isinstance(value, list) else [value]

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block

    def update(self):
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                vec = block.getOutputVector()
                if vec is not None:
                    if i == 0:
                        self.input_base = vec
                    else:
                        self.input_values = vec
                else:
                    val = block.getOutput()
                    if i == 0:
                        self.input_base = [val]
                    else:
                        self.input_values = [val]

        # Copy base input
        self.output = self.input_base.copy()

        # Assign values at specified indices
        for i, idx in enumerate(self.indices):
            if 0 <= idx < len(self.output) and i < len(self.input_values):
                self.output[idx] = self.input_values[i]

    def getOutput(self, port=0):
        if port < len(self.output):
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output if len(self.output) > 1 else None


class Concatenate(Block):
    """Concatenate vectors into a single vector.

    Combines multiple input vectors into one output vector.
    """

    def __init__(self, num_inputs=2, mode="vector"):
        super().__init__()
        self.num_inputs = num_inputs
        self.mode = mode  # 'vector' or 'matrix'
        self.inputs = [[] for _ in range(num_inputs)]
        self.output = []
        self.input_blocks = [None] * num_inputs

    def init(self):
        self.output = []

    def setInput(self, value, port=0):
        if port < self.num_inputs:
            self.inputs[port] = value if isinstance(value, list) else [value]

    def connectInput(self, block, port=0, source_port=0):
        if port < self.num_inputs:
            self.input_blocks[port] = block

    def update(self):
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                vec = block.getOutputVector()
                if vec is not None:
                    self.inputs[i] = vec
                else:
                    self.inputs[i] = [block.getOutput()]

        # Concatenate all inputs
        self.output = []
        for inp in self.inputs:
            self.output.extend(inp)

    def getOutput(self, port=0):
        if port < len(self.output):
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output if len(self.output) > 1 else None

    def getNumOutputs(self):
        return len(self.output) if self.output else 1


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
