"""Math operation blocks for OSK-based simulation."""

import math

from ..block import Block
from ..state import State


class Sum(Block):
    """Sum block - add or subtract inputs."""

    def __init__(self, signs='++'):
        super().__init__()
        self.signs = signs
        self.num_inputs = len(signs)
        self.inputs = [0.0] * self.num_inputs
        self.input_blocks = [None] * self.num_inputs
        self.output = 0.0

    def setInput(self, value, port=0):
        if port < self.num_inputs:
            self.inputs[port] = value

    def connectInput(self, block, port=0):
        if port < self.num_inputs:
            self.input_blocks[port] = block

    def update(self):
        # Get inputs from connected blocks
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                self.inputs[i] = block.getOutput()

        # Compute sum
        self.output = 0.0
        for i, sign in enumerate(self.signs):
            if i < len(self.inputs):
                if sign == '+':
                    self.output += self.inputs[i]
                else:
                    self.output -= self.inputs[i]

    def getOutput(self, port=0):
        return self.output


class Gain(Block):
    """Gain block - multiply input by constant."""

    def __init__(self, gain=1.0):
        super().__init__()
        self.gain = gain
        self.input = 0.0
        self.input_block = None
        self.output = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput()
        self.output = self.gain * self.input

    def getOutput(self, port=0):
        return self.output


class Product(Block):
    """Product block - multiply or divide inputs."""

    def __init__(self, operations='**'):
        super().__init__()
        self.operations = operations
        self.num_inputs = len(operations)
        self.inputs = [1.0] * self.num_inputs
        self.input_blocks = [None] * self.num_inputs
        self.output = 0.0

    def setInput(self, value, port=0):
        if port < self.num_inputs:
            self.inputs[port] = value

    def connectInput(self, block, port=0):
        if port < self.num_inputs:
            self.input_blocks[port] = block

    def update(self):
        # Get inputs from connected blocks
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                self.inputs[i] = block.getOutput()

        # Compute product
        self.output = 1.0
        for i, op in enumerate(self.operations):
            if i < len(self.inputs):
                if op == '*':
                    self.output *= self.inputs[i]
                else:  # Division
                    if abs(self.inputs[i]) > State.EPS:
                        self.output /= self.inputs[i]
                    else:
                        self.output /= State.EPS  # Avoid division by zero

    def getOutput(self, port=0):
        return self.output


class Abs(Block):
    """Absolute value block."""

    def __init__(self):
        super().__init__()
        self.input = 0.0
        self.input_block = None
        self.output = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput()
        self.output = abs(self.input)

    def getOutput(self, port=0):
        return self.output


class Sign(Block):
    """Sign block - returns -1, 0, or 1."""

    def __init__(self):
        super().__init__()
        self.input = 0.0
        self.input_block = None
        self.output = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput()

        if self.input > State.EPS:
            self.output = 1.0
        elif self.input < -State.EPS:
            self.output = -1.0
        else:
            self.output = 0.0

    def getOutput(self, port=0):
        return self.output


class Saturation(Block):
    """Saturation block - limits signal to range."""

    def __init__(self, upper_limit=1.0, lower_limit=-1.0):
        super().__init__()
        self.upper_limit = upper_limit
        self.lower_limit = lower_limit
        self.input = 0.0
        self.input_block = None
        self.output = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput()
        self.output = max(self.lower_limit, min(self.upper_limit, self.input))

    def getOutput(self, port=0):
        return self.output


class MathFunction(Block):
    """Mathematical function block."""

    def __init__(self, function='exp', exponent=2.0):
        super().__init__()
        self.function = function
        self.exponent = exponent
        self.input = 0.0
        self.input_block = None
        self.output = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput()

        if self.function == 'exp':
            self.output = math.exp(self.input)
        elif self.function == 'log':
            self.output = math.log(max(self.input, State.EPS))
        elif self.function == 'log10':
            self.output = math.log10(max(self.input, State.EPS))
        elif self.function == 'sqrt':
            self.output = math.sqrt(max(self.input, 0.0))
        elif self.function == 'square':
            self.output = self.input ** 2
        elif self.function == 'pow':
            self.output = self.input ** self.exponent
        elif self.function == 'reciprocal':
            if abs(self.input) > State.EPS:
                self.output = 1.0 / self.input
            else:
                self.output = 1.0 / State.EPS
        else:
            self.output = self.input

    def getOutput(self, port=0):
        return self.output


class Trigonometry(Block):
    """Trigonometric function block."""

    def __init__(self, function='sin'):
        super().__init__()
        self.function = function
        self.input = 0.0
        self.input_block = None
        self.output = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput()

        funcs = {
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'asin': math.asin,
            'acos': math.acos,
            'atan': math.atan,
            'sinh': math.sinh,
            'cosh': math.cosh,
            'tanh': math.tanh,
        }

        func = funcs.get(self.function, math.sin)
        try:
            self.output = func(self.input)
        except (ValueError, OverflowError):
            self.output = 0.0

    def getOutput(self, port=0):
        return self.output


class DeadZone(Block):
    """Dead zone block - zero output within zone."""

    def __init__(self, start=-0.5, end=0.5):
        super().__init__()
        self.start = start
        self.end = end
        self.input = 0.0
        self.input_block = None
        self.output = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput()

        if self.input > self.end:
            self.output = self.input - self.end
        elif self.input < self.start:
            self.output = self.input - self.start
        else:
            self.output = 0.0

    def getOutput(self, port=0):
        return self.output


class Switch(Block):
    """Switch block - selects between inputs based on control signal."""

    def __init__(self, threshold=0.0, criteria='gte'):
        super().__init__()
        self.threshold = threshold
        self.criteria = criteria  # 'gte', 'gt', 'neq'
        self.inputs = [0.0, 0.0, 0.0]  # [in1, control, in2]
        self.input_blocks = [None, None, None]
        self.output = 0.0

    def setInput(self, value, port=0):
        if port < 3:
            self.inputs[port] = value

    def connectInput(self, block, port=0):
        if port < 3:
            self.input_blocks[port] = block

    def update(self):
        # Get inputs from connected blocks
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                self.inputs[i] = block.getOutput()

        control = self.inputs[1]

        if self.criteria == 'gte':
            use_first = control >= self.threshold
        elif self.criteria == 'gt':
            use_first = control > self.threshold
        else:  # 'neq'
            use_first = abs(control - self.threshold) > State.EPS

        self.output = self.inputs[0] if use_first else self.inputs[2]

    def getOutput(self, port=0):
        return self.output


class Mux(Block):
    """Mux block - combines multiple scalar inputs into a vector output.

    The Mux block concatenates multiple scalar inputs into a single
    vector (array) output. This preserves dimensionality for downstream
    blocks that need to process the combined signal.
    """

    def __init__(self, num_inputs=2):
        super().__init__()
        # Ensure num_inputs is an integer (may come as float from JSON)
        self.num_inputs = int(num_inputs)
        self.inputs = [0.0] * self.num_inputs
        self.input_blocks = [None] * self.num_inputs
        # Output is a vector containing all inputs
        self.outputs = [0.0] * self.num_inputs

    def init(self):
        self.inputs = [0.0] * self.num_inputs
        self.outputs = [0.0] * self.num_inputs

    def setInput(self, value, port=0):
        if port < self.num_inputs:
            self.inputs[port] = value

    def connectInput(self, block, port=0):
        if port < self.num_inputs:
            self.input_blocks[port] = block

    def update(self):
        # Get inputs from connected blocks
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                self.inputs[i] = block.getOutput()

        # Copy inputs to outputs (the muxed vector)
        for i in range(self.num_inputs):
            self.outputs[i] = self.inputs[i]

    def getOutput(self, port=0):
        """Get output - port 0 returns first element for scalar compat,
        but the full vector is available via outputs attribute."""
        if port < len(self.outputs):
            return self.outputs[port]
        return 0.0

    def getOutputVector(self):
        """Get the full output vector."""
        return self.outputs.copy()


class Demux(Block):
    """Demux block - splits a vector input into multiple scalar outputs.

    The Demux block takes a vector (array) input and splits it into
    separate scalar outputs. It's the inverse of the Mux block.
    """

    def __init__(self, num_outputs=2):
        super().__init__()
        # Ensure num_outputs is an integer (may come as float from JSON)
        self.num_outputs = int(num_outputs)
        self.input = 0.0
        self.input_vector = [0.0] * self.num_outputs
        self.input_block = None
        self.outputs = [0.0] * self.num_outputs

    def init(self):
        self.input_vector = [0.0] * self.num_outputs
        self.outputs = [0.0] * self.num_outputs

    def setInput(self, value, port=0):
        """Set input - can accept scalar or vector."""
        if isinstance(value, (list, tuple)):
            for i, v in enumerate(value):
                if i < len(self.input_vector):
                    self.input_vector[i] = v
        else:
            self.input = value
            # For scalar input, put it in the first slot
            if len(self.input_vector) > 0:
                self.input_vector[0] = value

    def connectInput(self, block, port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            # Check if the input block has a vector output (like Mux)
            if hasattr(self.input_block, 'getOutputVector'):
                vec = self.input_block.getOutputVector()
                for i, v in enumerate(vec):
                    if i < len(self.input_vector):
                        self.input_vector[i] = v
            elif hasattr(self.input_block, 'outputs') and isinstance(self.input_block.outputs, list):
                # Access outputs array directly if available
                for i, v in enumerate(self.input_block.outputs):
                    if i < len(self.input_vector):
                        self.input_vector[i] = v
            elif hasattr(self.input_block, 'x_hat'):
                # Handle observer blocks with state estimate (KalmanFilter, etc.)
                x_hat = self.input_block.x_hat
                for i in range(min(len(x_hat), len(self.input_vector))):
                    self.input_vector[i] = float(x_hat[i])
            else:
                # Scalar input - put in first slot
                self.input = self.input_block.getOutput()
                if len(self.input_vector) > 0:
                    self.input_vector[0] = self.input

        # Copy to outputs
        for i in range(self.num_outputs):
            if i < len(self.input_vector):
                self.outputs[i] = self.input_vector[i]
            else:
                self.outputs[i] = 0.0

    def getOutput(self, port=0):
        """Get output at specified port."""
        if port < len(self.outputs):
            return self.outputs[port]
        return 0.0


class Reshape(Block):
    """Reshape block - passes through vector signals unchanged.

    In LibreSim, Reshape is primarily used as a pass-through for vector signals
    that may need reshaping in Simulink (e.g., from column to row vector).
    Since we handle vectors as simple lists, this block just passes the signal through.
    """

    def __init__(self, output_dimensions=None, **kwargs):
        super().__init__()
        self.output_dimensions = output_dimensions
        self.input = 0.0
        self.input_block = None
        self._input_vector = None
        self._output_vector = None

    def init(self):
        self.input = 0.0
        self._input_vector = None
        self._output_vector = None

    def setInput(self, value, port=0):
        if isinstance(value, (list, tuple)):
            self._input_vector = list(value)
            self.input = value[0] if value else 0.0
        else:
            self.input = value
            self._input_vector = None

    def connectInput(self, block, port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            # Check if source has vector output
            if hasattr(self.input_block, 'getOutputVector'):
                vec = self.input_block.getOutputVector()
                if vec is not None:
                    self._input_vector = vec
                    self._output_vector = vec.copy()
                    self.input = vec[0] if vec else 0.0
                else:
                    self.input = self.input_block.getOutput()
                    self._input_vector = None
                    self._output_vector = None
            else:
                self.input = self.input_block.getOutput()
                self._input_vector = None
                self._output_vector = None

    def getOutput(self, port=0):
        return self.input

    def getOutputVector(self):
        """Get the full output vector (pass-through from input)."""
        return self._output_vector.copy() if self._output_vector else None
