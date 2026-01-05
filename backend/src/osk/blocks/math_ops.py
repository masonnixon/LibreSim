"""Math operation blocks for OSK-based simulation."""

import math
from typing import Any

from ..block import Block
from ..state import State


class Sum(Block):
    """Sum block - add or subtract inputs.

    Supports both scalar and vector inputs. When vector inputs are detected,
    performs element-wise addition/subtraction.
    """

    def __init__(self, signs="++"):
        super().__init__()
        self.signs = signs
        self.num_inputs = len(signs)
        self.inputs: list[float] = [0.0] * self.num_inputs
        self.input_blocks: list[Any] = [None] * self.num_inputs
        self.output: float = 0.0
        self._is_vector: bool = False
        self._output_vector: list[float] | None = None
        self._input_vectors: list[list[float] | None] = [None] * self.num_inputs

    def init(self) -> None:
        self.inputs = [0.0] * self.num_inputs
        self.output = 0.0
        self._is_vector = False
        self._output_vector = None
        self._input_vectors = [None] * self.num_inputs

    def setInput(self, value, port=0):
        if port < self.num_inputs:
            if isinstance(value, (list, tuple)):
                self._input_vectors[port] = list(value)
                self.inputs[port] = value[0] if value else 0.0
            else:
                self._input_vectors[port] = None
                self.inputs[port] = value

    def connectInput(self, block, port=0):
        if port < self.num_inputs:
            self.input_blocks[port] = block

    def update(self):
        # Get inputs from connected blocks
        self._is_vector = False
        max_len = 1

        for i, block in enumerate(self.input_blocks):
            if block is not None:
                # Check for vector output
                if hasattr(block, "getOutputVector"):
                    vec = block.getOutputVector()
                    if vec is not None:
                        self._input_vectors[i] = vec
                        self.inputs[i] = vec[0] if vec else 0.0
                        self._is_vector = True
                        max_len = max(max_len, len(vec))
                        continue
                # Scalar output
                self._input_vectors[i] = None
                self.inputs[i] = block.getOutput()
            elif self._input_vectors[i] is not None:
                self._is_vector = True
                max_len = max(max_len, len(self._input_vectors[i]))

        if self._is_vector:
            # Vector sum
            self._output_vector = [0.0] * max_len
            for i, sign in enumerate(self.signs):
                if i < self.num_inputs:
                    sign_mult = 1.0 if sign == "+" else -1.0
                    if self._input_vectors[i] is not None:
                        for j in range(len(self._input_vectors[i])):
                            if j < max_len:
                                self._output_vector[j] += sign_mult * self._input_vectors[i][j]
                    else:
                        # Scalar input - add to first element only (or broadcast)
                        self._output_vector[0] += sign_mult * self.inputs[i]
            self.output = self._output_vector[0] if self._output_vector else 0.0
        else:
            # Scalar sum
            self._output_vector = None
            self.output = 0.0
            for i, sign in enumerate(self.signs):
                if i < len(self.inputs):
                    if sign == "+":
                        self.output += self.inputs[i]
                    else:
                        self.output -= self.inputs[i]

    def getOutput(self, port=0):
        if self._is_vector and self._output_vector:
            if port < len(self._output_vector):
                return self._output_vector[port]
            return 0.0
        return self.output

    def getOutputVector(self):
        """Get the full output vector. Returns None for scalar operation."""
        if self._is_vector and self._output_vector:
            return self._output_vector.copy()
        return None


class Gain(Block):
    """Gain block - multiply input by constant.

    Supports both scalar and vector inputs. For vector inputs,
    multiplies each element by the gain value.
    """

    def __init__(self, gain=1.0):
        super().__init__()
        self.gain = gain
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = 0.0
        self._is_vector = False
        self._input_vector = None
        self._output_vector = None

    def init(self):
        self.input = 0.0
        self.output = 0.0
        self._is_vector = False
        self._input_vector = None
        self._output_vector = None

    def setInput(self, value, port=0):
        if isinstance(value, (list, tuple)):
            self._is_vector = True
            self._input_vector = list(value)
            self.input = value[0] if value else 0.0
        else:
            self._is_vector = False
            self._input_vector = None
            self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            # If source_port > 0, we're selecting a specific port - use scalar mode
            if self.input_source_port > 0:
                self._is_vector = False
                self._input_vector = None
                self.input = self.input_block.getOutput(self.input_source_port)
            # Check for vector output (only when source_port == 0)
            elif hasattr(self.input_block, "getOutputVector"):
                vec = self.input_block.getOutputVector()
                if vec is not None:
                    self._is_vector = True
                    self._input_vector = vec
                    self.input = vec[0] if vec else 0.0
                else:
                    self._is_vector = False
                    self._input_vector = None
                    self.input = self.input_block.getOutput(self.input_source_port)
            else:
                self._is_vector = False
                self._input_vector = None
                self.input = self.input_block.getOutput(self.input_source_port)

        if self._is_vector and self._input_vector:
            self._output_vector = [self.gain * v for v in self._input_vector]
            self.output = self._output_vector[0] if self._output_vector else 0.0
        else:
            self._output_vector = None
            self.output = self.gain * self.input

    def getOutput(self, port=0):
        if self._is_vector and self._output_vector:
            if port < len(self._output_vector):
                return self._output_vector[port]
            return 0.0
        return self.output

    def getOutputVector(self):
        """Get the full output vector. Returns None for scalar operation."""
        if self._is_vector and self._output_vector:
            return self._output_vector.copy()
        return None


class Product(Block):
    """Product block - multiply or divide inputs.

    Supports both scalar and vector inputs. For vector inputs,
    performs element-wise multiplication/division.
    """

    def __init__(self, operations="**"):
        super().__init__()
        self.operations = operations
        self.num_inputs = len(operations)
        self.inputs: list[float] = [1.0] * self.num_inputs
        self.input_blocks: list[Any] = [None] * self.num_inputs
        self.output: float = 0.0
        self._is_vector: bool = False
        self._output_vector: list[float] | None = None
        self._input_vectors: list[list[float] | None] = [None] * self.num_inputs

    def init(self) -> None:
        self.inputs = [1.0] * self.num_inputs
        self.output = 0.0
        self._is_vector = False
        self._output_vector = None
        self._input_vectors = [None] * self.num_inputs

    def setInput(self, value, port=0):
        if port < self.num_inputs:
            if isinstance(value, (list, tuple)):
                self._input_vectors[port] = list(value)
                self.inputs[port] = value[0] if value else 1.0
            else:
                self._input_vectors[port] = None
                self.inputs[port] = value

    def connectInput(self, block, port=0):
        if port < self.num_inputs:
            self.input_blocks[port] = block

    def update(self):
        # Get inputs from connected blocks
        self._is_vector = False
        max_len = 1

        for i, block in enumerate(self.input_blocks):
            if block is not None:
                if hasattr(block, "getOutputVector"):
                    vec = block.getOutputVector()
                    if vec is not None:
                        self._input_vectors[i] = vec
                        self.inputs[i] = vec[0] if vec else 1.0
                        self._is_vector = True
                        max_len = max(max_len, len(vec))
                        continue
                self._input_vectors[i] = None
                self.inputs[i] = block.getOutput()
            elif self._input_vectors[i] is not None:
                self._is_vector = True
                max_len = max(max_len, len(self._input_vectors[i]))

        if self._is_vector:
            # Vector product
            self._output_vector = [1.0] * max_len
            for i, op in enumerate(self.operations):
                if i < self.num_inputs:
                    if self._input_vectors[i] is not None:
                        for j in range(len(self._input_vectors[i])):
                            if j < max_len:
                                val = self._input_vectors[i][j]
                                if op == "*":
                                    self._output_vector[j] *= val
                                else:
                                    if abs(val) > State.EPS:
                                        self._output_vector[j] /= val
                                    else:
                                        self._output_vector[j] /= State.EPS
                    else:
                        # Apply scalar to all elements
                        val = self.inputs[i]
                        for j in range(max_len):
                            if op == "*":
                                self._output_vector[j] *= val
                            else:
                                if abs(val) > State.EPS:
                                    self._output_vector[j] /= val
                                else:
                                    self._output_vector[j] /= State.EPS
            self.output = self._output_vector[0] if self._output_vector else 0.0
        else:
            # Scalar product
            self._output_vector = None
            self.output = 1.0
            for i, op in enumerate(self.operations):
                if i < len(self.inputs):
                    if op == "*":
                        self.output *= self.inputs[i]
                    else:
                        if abs(self.inputs[i]) > State.EPS:
                            self.output /= self.inputs[i]
                        else:
                            self.output /= State.EPS

    def getOutput(self, port=0):
        if self._is_vector and self._output_vector:
            if port < len(self._output_vector):
                return self._output_vector[port]
            return 0.0
        return self.output

    def getOutputVector(self):
        """Get the full output vector. Returns None for scalar operation."""
        if self._is_vector and self._output_vector:
            return self._output_vector.copy()
        return None


class Abs(Block):
    """Absolute value block.

    Supports both scalar and vector inputs.
    """

    def __init__(self):
        super().__init__()
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = 0.0
        self._is_vector = False
        self._input_vector = None
        self._output_vector = None

    def init(self):
        self.input = 0.0
        self.output = 0.0
        self._is_vector = False
        self._input_vector = None
        self._output_vector = None

    def setInput(self, value, port=0):
        if isinstance(value, (list, tuple)):
            self._is_vector = True
            self._input_vector = list(value)
            self.input = value[0] if value else 0.0
        else:
            self._is_vector = False
            self._input_vector = None
            self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            if hasattr(self.input_block, "getOutputVector"):
                vec = self.input_block.getOutputVector()
                if vec is not None:
                    self._is_vector = True
                    self._input_vector = vec
                    self.input = vec[0] if vec else 0.0
                else:
                    self._is_vector = False
                    self._input_vector = None
                    self.input = self.input_block.getOutput(self.input_source_port)
            else:
                self._is_vector = False
                self._input_vector = None
                self.input = self.input_block.getOutput(self.input_source_port)

        if self._is_vector and self._input_vector:
            self._output_vector = [abs(v) for v in self._input_vector]
            self.output = self._output_vector[0] if self._output_vector else 0.0
        else:
            self._output_vector = None
            self.output = abs(self.input)

    def getOutput(self, port=0):
        if self._is_vector and self._output_vector:
            if port < len(self._output_vector):
                return self._output_vector[port]
            return 0.0
        return self.output

    def getOutputVector(self):
        if self._is_vector and self._output_vector:
            return self._output_vector.copy()
        return None


class Sign(Block):
    """Sign block - returns -1, 0, or 1.

    Supports both scalar and vector inputs.
    """

    def __init__(self):
        super().__init__()
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = 0.0
        self._is_vector = False
        self._input_vector = None
        self._output_vector = None

    def init(self):
        self.input = 0.0
        self.output = 0.0
        self._is_vector = False
        self._input_vector = None
        self._output_vector = None

    def _compute_sign(self, val):
        if val > State.EPS:
            return 1.0
        elif val < -State.EPS:
            return -1.0
        return 0.0

    def setInput(self, value, port=0):
        if isinstance(value, (list, tuple)):
            self._is_vector = True
            self._input_vector = list(value)
            self.input = value[0] if value else 0.0
        else:
            self._is_vector = False
            self._input_vector = None
            self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            if hasattr(self.input_block, "getOutputVector"):
                vec = self.input_block.getOutputVector()
                if vec is not None:
                    self._is_vector = True
                    self._input_vector = vec
                    self.input = vec[0] if vec else 0.0
                else:
                    self._is_vector = False
                    self._input_vector = None
                    self.input = self.input_block.getOutput(self.input_source_port)
            else:
                self._is_vector = False
                self._input_vector = None
                self.input = self.input_block.getOutput(self.input_source_port)

        if self._is_vector and self._input_vector:
            self._output_vector = [self._compute_sign(v) for v in self._input_vector]
            self.output = self._output_vector[0] if self._output_vector else 0.0
        else:
            self._output_vector = None
            self.output = self._compute_sign(self.input)

    def getOutput(self, port=0):
        if self._is_vector and self._output_vector:
            if port < len(self._output_vector):
                return self._output_vector[port]
            return 0.0
        return self.output

    def getOutputVector(self):
        if self._is_vector and self._output_vector:
            return self._output_vector.copy()
        return None


class Saturation(Block):
    """Saturation block - limits signal to range.

    Supports both scalar and vector inputs.
    """

    def __init__(self, upper_limit=1.0, lower_limit=-1.0):
        super().__init__()
        self.upper_limit = upper_limit
        self.lower_limit = lower_limit
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = 0.0
        self._is_vector = False
        self._input_vector = None
        self._output_vector = None

    def init(self):
        self.input = 0.0
        self.output = 0.0
        self._is_vector = False
        self._input_vector = None
        self._output_vector = None

    def setInput(self, value, port=0):
        if isinstance(value, (list, tuple)):
            self._is_vector = True
            self._input_vector = list(value)
            self.input = value[0] if value else 0.0
        else:
            self._is_vector = False
            self._input_vector = None
            self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            if hasattr(self.input_block, "getOutputVector"):
                vec = self.input_block.getOutputVector()
                if vec is not None:
                    self._is_vector = True
                    self._input_vector = vec
                    self.input = vec[0] if vec else 0.0
                else:
                    self._is_vector = False
                    self._input_vector = None
                    self.input = self.input_block.getOutput(self.input_source_port)
            else:
                self._is_vector = False
                self._input_vector = None
                self.input = self.input_block.getOutput(self.input_source_port)

        if self._is_vector and self._input_vector:
            self._output_vector = [
                max(self.lower_limit, min(self.upper_limit, v)) for v in self._input_vector
            ]
            self.output = self._output_vector[0] if self._output_vector else 0.0
        else:
            self._output_vector = None
            self.output = max(self.lower_limit, min(self.upper_limit, self.input))

    def getOutput(self, port=0):
        if self._is_vector and self._output_vector:
            if port < len(self._output_vector):
                return self._output_vector[port]
            return 0.0
        return self.output

    def getOutputVector(self):
        if self._is_vector and self._output_vector:
            return self._output_vector.copy()
        return None


class MathFunction(Block):
    """Mathematical function block.

    Supports both scalar and vector inputs.
    """

    def __init__(self, function="exp", exponent=2.0):
        super().__init__()
        self.function = function
        self.exponent = exponent
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = 0.0
        self._is_vector = False
        self._input_vector = None
        self._output_vector = None

    def init(self):
        self.input = 0.0
        self.output = 0.0
        self._is_vector = False
        self._input_vector = None
        self._output_vector = None

    def _compute_function(self, val):
        if self.function == "exp":
            return math.exp(val)
        elif self.function == "log":
            return math.log(max(val, State.EPS))
        elif self.function == "log10":
            return math.log10(max(val, State.EPS))
        elif self.function == "sqrt":
            return math.sqrt(max(val, 0.0))
        elif self.function == "square":
            return val**2
        elif self.function == "pow":
            return val**self.exponent
        elif self.function == "reciprocal":
            if abs(val) > State.EPS:
                return 1.0 / val
            return 1.0 / State.EPS
        return val

    def setInput(self, value, port=0):
        if isinstance(value, (list, tuple)):
            self._is_vector = True
            self._input_vector = list(value)
            self.input = value[0] if value else 0.0
        else:
            self._is_vector = False
            self._input_vector = None
            self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            if hasattr(self.input_block, "getOutputVector"):
                vec = self.input_block.getOutputVector()
                if vec is not None:
                    self._is_vector = True
                    self._input_vector = vec
                    self.input = vec[0] if vec else 0.0
                else:
                    self._is_vector = False
                    self._input_vector = None
                    self.input = self.input_block.getOutput(self.input_source_port)
            else:
                self._is_vector = False
                self._input_vector = None
                self.input = self.input_block.getOutput(self.input_source_port)

        if self._is_vector and self._input_vector:
            self._output_vector = [self._compute_function(v) for v in self._input_vector]
            self.output = self._output_vector[0] if self._output_vector else 0.0
        else:
            self._output_vector = None
            self.output = self._compute_function(self.input)

    def getOutput(self, port=0):
        if self._is_vector and self._output_vector:
            if port < len(self._output_vector):
                return self._output_vector[port]
            return 0.0
        return self.output

    def getOutputVector(self):
        if self._is_vector and self._output_vector:
            return self._output_vector.copy()
        return None


class Trigonometry(Block):
    """Trigonometric function block.

    Supports both scalar and vector inputs.
    """

    def __init__(self, function="sin"):
        super().__init__()
        self.function = function
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = 0.0
        self._is_vector = False
        self._input_vector = None
        self._output_vector = None

    def init(self):
        self.input = 0.0
        self.output = 0.0
        self._is_vector = False
        self._input_vector = None
        self._output_vector = None

    def _compute_trig(self, val):
        funcs = {
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "asin": math.asin,
            "acos": math.acos,
            "atan": math.atan,
            "sinh": math.sinh,
            "cosh": math.cosh,
            "tanh": math.tanh,
        }
        func = funcs.get(self.function, math.sin)
        try:
            return func(val)
        except (ValueError, OverflowError):
            return 0.0

    def setInput(self, value, port=0):
        if isinstance(value, (list, tuple)):
            self._is_vector = True
            self._input_vector = list(value)
            self.input = value[0] if value else 0.0
        else:
            self._is_vector = False
            self._input_vector = None
            self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            if hasattr(self.input_block, "getOutputVector"):
                vec = self.input_block.getOutputVector()
                if vec is not None:
                    self._is_vector = True
                    self._input_vector = vec
                    self.input = vec[0] if vec else 0.0
                else:
                    self._is_vector = False
                    self._input_vector = None
                    self.input = self.input_block.getOutput(self.input_source_port)
            else:
                self._is_vector = False
                self._input_vector = None
                self.input = self.input_block.getOutput(self.input_source_port)

        if self._is_vector and self._input_vector:
            self._output_vector = [self._compute_trig(v) for v in self._input_vector]
            self.output = self._output_vector[0] if self._output_vector else 0.0
        else:
            self._output_vector = None
            self.output = self._compute_trig(self.input)

    def getOutput(self, port=0):
        if self._is_vector and self._output_vector:
            if port < len(self._output_vector):
                return self._output_vector[port]
            return 0.0
        return self.output

    def getOutputVector(self):
        if self._is_vector and self._output_vector:
            return self._output_vector.copy()
        return None


class DeadZone(Block):
    """Dead zone block - zero output within zone.

    Supports both scalar and vector inputs.
    """

    def __init__(self, start=-0.5, end=0.5):
        super().__init__()
        self.start = start
        self.end = end
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = 0.0
        self._is_vector = False
        self._input_vector = None
        self._output_vector = None

    def init(self):
        self.input = 0.0
        self.output = 0.0
        self._is_vector = False
        self._input_vector = None
        self._output_vector = None

    def _compute_deadzone(self, val):
        if val > self.end:
            return val - self.end
        elif val < self.start:
            return val - self.start
        return 0.0

    def setInput(self, value, port=0):
        if isinstance(value, (list, tuple)):
            self._is_vector = True
            self._input_vector = list(value)
            self.input = value[0] if value else 0.0
        else:
            self._is_vector = False
            self._input_vector = None
            self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            if hasattr(self.input_block, "getOutputVector"):
                vec = self.input_block.getOutputVector()
                if vec is not None:
                    self._is_vector = True
                    self._input_vector = vec
                    self.input = vec[0] if vec else 0.0
                else:
                    self._is_vector = False
                    self._input_vector = None
                    self.input = self.input_block.getOutput(self.input_source_port)
            else:
                self._is_vector = False
                self._input_vector = None
                self.input = self.input_block.getOutput(self.input_source_port)

        if self._is_vector and self._input_vector:
            self._output_vector = [self._compute_deadzone(v) for v in self._input_vector]
            self.output = self._output_vector[0] if self._output_vector else 0.0
        else:
            self._output_vector = None
            self.output = self._compute_deadzone(self.input)

    def getOutput(self, port=0):
        if self._is_vector and self._output_vector:
            if port < len(self._output_vector):
                return self._output_vector[port]
            return 0.0
        return self.output

    def getOutputVector(self):
        if self._is_vector and self._output_vector:
            return self._output_vector.copy()
        return None


class Switch(Block):
    """Switch block - selects between inputs based on control signal."""

    def __init__(self, threshold=0.0, criteria="gte"):
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

        if self.criteria == "gte":
            use_first = control >= self.threshold
        elif self.criteria == "gt":
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
        self.input_source_port = 0
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

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            # Check if the input block has a vector output (like Mux or vector Constant)
            vec = None
            if hasattr(self.input_block, "getOutputVector"):
                vec = self.input_block.getOutputVector()

            if vec is not None:
                # Vector input - distribute to outputs
                for i, v in enumerate(vec):
                    if i < len(self.input_vector):
                        self.input_vector[i] = v
            elif hasattr(self.input_block, "outputs") and isinstance(
                self.input_block.outputs, list
            ):
                # Access outputs array directly if available
                for i, v in enumerate(self.input_block.outputs):
                    if i < len(self.input_vector):
                        self.input_vector[i] = v
            elif hasattr(self.input_block, "x_hat"):
                # Handle observer blocks with state estimate (KalmanFilter, etc.)
                x_hat = self.input_block.x_hat
                for i in range(min(len(x_hat), len(self.input_vector))):
                    self.input_vector[i] = float(x_hat[i])
            else:
                # Scalar input - put in first slot, use source_port for multi-output sources
                self.input = self.input_block.getOutput(self.input_source_port)
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

    def getOutputVector(self):
        """Get all outputs as a vector.

        This allows downstream blocks that expect vector input to read
        from the Demux outputs as if it were a single vector signal.
        """
        return self.outputs.copy()


class Bias(Block):
    """Bias block - adds a constant bias value to the input.

    Supports both scalar and vector inputs.
    """

    def __init__(self, bias=0.0):
        super().__init__()
        self.bias = bias
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = 0.0
        self._is_vector = False
        self._input_vector = None
        self._output_vector = None

    def init(self):
        self.input = 0.0
        self.output = 0.0
        self._is_vector = False
        self._input_vector = None
        self._output_vector = None

    def setInput(self, value, port=0):
        if isinstance(value, (list, tuple)):
            self._is_vector = True
            self._input_vector = list(value)
            self.input = value[0] if value else 0.0
        else:
            self._is_vector = False
            self._input_vector = None
            self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            if hasattr(self.input_block, "getOutputVector"):
                vec = self.input_block.getOutputVector()
                if vec is not None:
                    self._is_vector = True
                    self._input_vector = vec
                    self.input = vec[0] if vec else 0.0
                else:
                    self._is_vector = False
                    self._input_vector = None
                    self.input = self.input_block.getOutput(self.input_source_port)
            else:
                self._is_vector = False
                self._input_vector = None
                self.input = self.input_block.getOutput(self.input_source_port)

        if self._is_vector and self._input_vector:
            self._output_vector = [v + self.bias for v in self._input_vector]
            self.output = self._output_vector[0] if self._output_vector else 0.0
        else:
            self._output_vector = None
            self.output = self.input + self.bias

    def getOutput(self, port=0):
        if self._is_vector and self._output_vector:
            if port < len(self._output_vector):
                return self._output_vector[port]
            return 0.0
        return self.output

    def getOutputVector(self):
        if self._is_vector and self._output_vector:
            return self._output_vector.copy()
        return None


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
        self.input_source_port = 0
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

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            # Check if source has vector output
            if hasattr(self.input_block, "getOutputVector"):
                vec = self.input_block.getOutputVector()
                if vec is not None:
                    self._input_vector = vec
                    self._output_vector = vec.copy()
                    self.input = vec[0] if vec else 0.0
                else:
                    self.input = self.input_block.getOutput(self.input_source_port)
                    self._input_vector = None
                    self._output_vector = None
            else:
                self.input = self.input_block.getOutput(self.input_source_port)
                self._input_vector = None
                self._output_vector = None

    def getOutput(self, port=0):
        return self.input

    def getOutputVector(self):
        """Get the full output vector (pass-through from input)."""
        return self._output_vector.copy() if self._output_vector else None


class Divide(Block):
    """Divide block - divides first input by second.

    Supports both scalar and vector inputs.
    """

    def __init__(self):
        super().__init__()
        self.inputs = [0.0, 1.0]
        self.input_blocks = [None, None]
        self.input_source_ports = [0, 0]
        self.output = 0.0
        self._is_vector = False
        self._input_vectors = [None, None]
        self._output_vector = None

    def init(self):
        self.output = 0.0
        self._output_vector = None

    def setInput(self, value, port=0):
        if port < 2:
            if isinstance(value, (list, tuple)):
                self._setup_vector_mode(len(value))
                self._input_vectors[port] = list(value)
                self.inputs[port] = value[0] if value else (0.0 if port == 0 else 1.0)
            else:
                self.inputs[port] = value

    def _setup_vector_mode(self, n):
        if not self._is_vector or (self._output_vector and len(self._output_vector) != n):
            self._is_vector = True
            self._output_vector = [0.0] * n

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block
            self.input_source_ports[port] = source_port

    def update(self):
        for i in range(2):
            block = self.input_blocks[i]
            if block is not None:
                if hasattr(block, "getOutputVector"):
                    vec = block.getOutputVector()
                    if vec is not None:
                        self._setup_vector_mode(len(vec))
                        self._input_vectors[i] = list(vec)
                        self.inputs[i] = vec[0] if vec else self.inputs[i]
                    else:
                        self.inputs[i] = block.getOutput(self.input_source_ports[i])
                else:
                    self.inputs[i] = block.getOutput(self.input_source_ports[i])

        if self._is_vector and self._output_vector:
            n = len(self._output_vector)
            for i in range(n):
                a = (
                    self._input_vectors[0][i]
                    if self._input_vectors[0] and i < len(self._input_vectors[0])
                    else self.inputs[0]
                )
                b = (
                    self._input_vectors[1][i]
                    if self._input_vectors[1] and i < len(self._input_vectors[1])
                    else self.inputs[1]
                )
                if abs(b) > State.EPS:
                    self._output_vector[i] = a / b
                else:
                    self._output_vector[i] = a / State.EPS if b >= 0 else -a / State.EPS
            self.output = self._output_vector[0]
        else:
            b = self.inputs[1]
            if abs(b) > State.EPS:
                self.output = self.inputs[0] / b
            else:
                self.output = self.inputs[0] / State.EPS if b >= 0 else -self.inputs[0] / State.EPS

    def getOutput(self, port=0):
        if self._is_vector and self._output_vector and port < len(self._output_vector):
            return self._output_vector[port]
        return self.output

    def getOutputVector(self):
        if self._is_vector and self._output_vector:
            return self._output_vector.copy()
        return None


class Mod(Block):
    """Modulo (remainder) block - computes a mod b.

    Supports both scalar and vector inputs.
    """

    def __init__(self):
        super().__init__()
        self.inputs = [0.0, 1.0]
        self.input_blocks = [None, None]
        self.input_source_ports = [0, 0]
        self.output = 0.0
        self._is_vector = False
        self._input_vectors = [None, None]
        self._output_vector = None

    def init(self):
        self.output = 0.0
        self._output_vector = None

    def setInput(self, value, port=0):
        if port < 2:
            if isinstance(value, (list, tuple)):
                self._setup_vector_mode(len(value))
                self._input_vectors[port] = list(value)
                self.inputs[port] = value[0] if value else self.inputs[port]
            else:
                self.inputs[port] = value

    def _setup_vector_mode(self, n):
        if not self._is_vector or (self._output_vector and len(self._output_vector) != n):
            self._is_vector = True
            self._output_vector = [0.0] * n

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block
            self.input_source_ports[port] = source_port

    def update(self):
        for i in range(2):
            block = self.input_blocks[i]
            if block is not None:
                if hasattr(block, "getOutputVector"):
                    vec = block.getOutputVector()
                    if vec is not None:
                        self._setup_vector_mode(len(vec))
                        self._input_vectors[i] = list(vec)
                        self.inputs[i] = vec[0] if vec else self.inputs[i]
                    else:
                        self.inputs[i] = block.getOutput(self.input_source_ports[i])
                else:
                    self.inputs[i] = block.getOutput(self.input_source_ports[i])

        if self._is_vector and self._output_vector:
            n = len(self._output_vector)
            for i in range(n):
                a = (
                    self._input_vectors[0][i]
                    if self._input_vectors[0] and i < len(self._input_vectors[0])
                    else self.inputs[0]
                )
                b = (
                    self._input_vectors[1][i]
                    if self._input_vectors[1] and i < len(self._input_vectors[1])
                    else self.inputs[1]
                )
                if abs(b) > State.EPS:
                    self._output_vector[i] = math.fmod(a, b)
                else:
                    self._output_vector[i] = 0.0
            self.output = self._output_vector[0]
        else:
            b = self.inputs[1]
            if abs(b) > State.EPS:
                self.output = math.fmod(self.inputs[0], b)
            else:
                self.output = 0.0

    def getOutput(self, port=0):
        if self._is_vector and self._output_vector and port < len(self._output_vector):
            return self._output_vector[port]
        return self.output

    def getOutputVector(self):
        if self._is_vector and self._output_vector:
            return self._output_vector.copy()
        return None


class Atan2(Block):
    """Atan2 block - four-quadrant arctangent.

    Computes atan2(y, x) where y is port 0 and x is port 1.
    Supports both scalar and vector inputs.
    """

    def __init__(self):
        super().__init__()
        self.inputs = [0.0, 1.0]  # [y, x]
        self.input_blocks = [None, None]
        self.input_source_ports = [0, 0]
        self.output = 0.0
        self._is_vector = False
        self._input_vectors = [None, None]
        self._output_vector = None

    def init(self):
        self.output = 0.0
        self._output_vector = None

    def setInput(self, value, port=0):
        if port < 2:
            if isinstance(value, (list, tuple)):
                self._setup_vector_mode(len(value))
                self._input_vectors[port] = list(value)
                self.inputs[port] = value[0] if value else self.inputs[port]
            else:
                self.inputs[port] = value

    def _setup_vector_mode(self, n):
        if not self._is_vector or (self._output_vector and len(self._output_vector) != n):
            self._is_vector = True
            self._output_vector = [0.0] * n

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block
            self.input_source_ports[port] = source_port

    def update(self):
        for i in range(2):
            block = self.input_blocks[i]
            if block is not None:
                if hasattr(block, "getOutputVector"):
                    vec = block.getOutputVector()
                    if vec is not None:
                        self._setup_vector_mode(len(vec))
                        self._input_vectors[i] = list(vec)
                        self.inputs[i] = vec[0] if vec else self.inputs[i]
                    else:
                        self.inputs[i] = block.getOutput(self.input_source_ports[i])
                else:
                    self.inputs[i] = block.getOutput(self.input_source_ports[i])

        if self._is_vector and self._output_vector:
            n = len(self._output_vector)
            for i in range(n):
                y = (
                    self._input_vectors[0][i]
                    if self._input_vectors[0] and i < len(self._input_vectors[0])
                    else self.inputs[0]
                )
                x = (
                    self._input_vectors[1][i]
                    if self._input_vectors[1] and i < len(self._input_vectors[1])
                    else self.inputs[1]
                )
                self._output_vector[i] = math.atan2(y, x)
            self.output = self._output_vector[0]
        else:
            self.output = math.atan2(self.inputs[0], self.inputs[1])

    def getOutput(self, port=0):
        if self._is_vector and self._output_vector and port < len(self._output_vector):
            return self._output_vector[port]
        return self.output

    def getOutputVector(self):
        if self._is_vector and self._output_vector:
            return self._output_vector.copy()
        return None


class Rounding(Block):
    """Rounding block - rounds input to specified mode.

    Supports: floor, ceil, round, fix (truncate toward zero)
    Supports both scalar and vector inputs.
    """

    def __init__(self, mode="round"):
        super().__init__()
        self.mode = mode  # 'floor', 'ceil', 'round', 'fix'
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = 0.0
        self._is_vector = False
        self._input_vector = None
        self._output_vector = None

    def init(self):
        self.output = 0.0
        self._output_vector = None

    def _compute_round(self, val):
        if self.mode == "floor":
            return math.floor(val)
        elif self.mode == "ceil":
            return math.ceil(val)
        elif self.mode == "round":
            return round(val)
        elif self.mode == "fix":
            return math.trunc(val)
        return val

    def setInput(self, value, port=0):
        if isinstance(value, (list, tuple)):
            self._is_vector = True
            self._input_vector = list(value)
            self.input = value[0] if value else 0.0
        else:
            self._is_vector = False
            self._input_vector = None
            self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            if hasattr(self.input_block, "getOutputVector"):
                vec = self.input_block.getOutputVector()
                if vec is not None:
                    self._is_vector = True
                    self._input_vector = vec
                    self.input = vec[0] if vec else 0.0
                else:
                    self._is_vector = False
                    self._input_vector = None
                    self.input = self.input_block.getOutput(self.input_source_port)
            else:
                self._is_vector = False
                self._input_vector = None
                self.input = self.input_block.getOutput(self.input_source_port)

        if self._is_vector and self._input_vector:
            self._output_vector = [self._compute_round(v) for v in self._input_vector]
            self.output = self._output_vector[0] if self._output_vector else 0.0
        else:
            self._output_vector = None
            self.output = self._compute_round(self.input)

    def getOutput(self, port=0):
        if self._is_vector and self._output_vector and port < len(self._output_vector):
            return self._output_vector[port]
        return self.output

    def getOutputVector(self):
        if self._is_vector and self._output_vector:
            return self._output_vector.copy()
        return None


class MinMax(Block):
    """MinMax block - outputs minimum or maximum of inputs.

    Supports both scalar and vector inputs.
    """

    def __init__(self, function="min", num_inputs=2):
        super().__init__()
        self.function = function  # 'min' or 'max'
        self.num_inputs = int(num_inputs)
        self.inputs = [0.0] * self.num_inputs
        self.input_blocks = [None] * self.num_inputs
        self.input_source_ports = [0] * self.num_inputs
        self.output = 0.0
        self._is_vector = False
        self._input_vectors = [None] * self.num_inputs
        self._output_vector = None

    def init(self):
        self.output = 0.0
        self._output_vector = None

    def setInput(self, value, port=0):
        if port < self.num_inputs:
            if isinstance(value, (list, tuple)):
                self._setup_vector_mode(len(value))
                self._input_vectors[port] = list(value)
                self.inputs[port] = value[0] if value else 0.0
            else:
                self.inputs[port] = value

    def _setup_vector_mode(self, n):
        if not self._is_vector or (self._output_vector and len(self._output_vector) != n):
            self._is_vector = True
            self._output_vector = [0.0] * n
            while len(self._input_vectors) < self.num_inputs:
                self._input_vectors.append(None)

    def connectInput(self, block, port=0, source_port=0):
        if port < self.num_inputs:
            self.input_blocks[port] = block
            self.input_source_ports[port] = source_port

    def update(self):
        for i in range(self.num_inputs):
            block = self.input_blocks[i]
            if block is not None:
                if hasattr(block, "getOutputVector"):
                    vec = block.getOutputVector()
                    if vec is not None:
                        self._setup_vector_mode(len(vec))
                        self._input_vectors[i] = list(vec)
                        self.inputs[i] = vec[0] if vec else 0.0
                    else:
                        self.inputs[i] = block.getOutput(self.input_source_ports[i])
                else:
                    self.inputs[i] = block.getOutput(self.input_source_ports[i])

        op = min if self.function == "min" else max

        if self._is_vector and self._output_vector:
            n = len(self._output_vector)
            for i in range(n):
                values = []
                for j in range(self.num_inputs):
                    if self._input_vectors[j] and i < len(self._input_vectors[j]):
                        values.append(self._input_vectors[j][i])
                    else:
                        values.append(self.inputs[j])
                self._output_vector[i] = op(values) if values else 0.0
            self.output = self._output_vector[0]
        else:
            self.output = op(self.inputs) if self.inputs else 0.0

    def getOutput(self, port=0):
        if self._is_vector and self._output_vector and port < len(self._output_vector):
            return self._output_vector[port]
        return self.output

    def getOutputVector(self):
        if self._is_vector and self._output_vector:
            return self._output_vector.copy()
        return None


class DotProduct(Block):
    """Dot Product block - computes dot product of two vectors.

    Takes two vector inputs and outputs their dot product (scalar).
    If scalar inputs are provided, outputs their product.
    """

    def __init__(self):
        super().__init__()
        self.inputs = [0.0, 0.0]
        self.input_blocks = [None, None]
        self.input_source_ports = [0, 0]
        self._input_vectors = [None, None]
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def setInput(self, value, port=0):
        if port < 2:
            if isinstance(value, (list, tuple)):
                self._input_vectors[port] = list(value)
                self.inputs[port] = value[0] if value else 0.0
            else:
                self._input_vectors[port] = None
                self.inputs[port] = value

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block
            self.input_source_ports[port] = source_port

    def update(self):
        for i in range(2):
            block = self.input_blocks[i]
            if block is not None:
                if hasattr(block, "getOutputVector"):
                    vec = block.getOutputVector()
                    if vec is not None:
                        self._input_vectors[i] = list(vec)
                        self.inputs[i] = vec[0] if vec else 0.0
                    else:
                        self._input_vectors[i] = None
                        self.inputs[i] = block.getOutput(self.input_source_ports[i])
                else:
                    self._input_vectors[i] = None
                    self.inputs[i] = block.getOutput(self.input_source_ports[i])

        # Compute dot product
        vec1 = self._input_vectors[0]
        vec2 = self._input_vectors[1]

        if vec1 is not None and vec2 is not None:
            # Both are vectors - compute dot product
            n = min(len(vec1), len(vec2))
            self.output = sum(vec1[i] * vec2[i] for i in range(n))
        elif vec1 is not None:
            # First is vector, second is scalar - multiply each element
            self.output = sum(v * self.inputs[1] for v in vec1)
        elif vec2 is not None:
            # First is scalar, second is vector
            self.output = sum(self.inputs[0] * v for v in vec2)
        else:
            # Both scalars - just multiply
            self.output = self.inputs[0] * self.inputs[1]

    def getOutput(self, port=0):
        return self.output


class CrossProduct(Block):
    """Cross Product block - computes cross product of two 3D vectors.

    Takes two 3-element vector inputs and outputs their cross product.
    """

    def __init__(self):
        super().__init__()
        self.inputs: list[list[float]] = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
        self.input_blocks: list[Any] = [None, None]
        self.input_source_ports: list[int] = [0, 0]
        self._input_vectors: list[list[float] | None] = [None, None]
        self._output_vector: list[float] = [0.0, 0.0, 0.0]

    def init(self) -> None:
        self._output_vector = [0.0, 0.0, 0.0]

    def setInput(self, value: Any, port: int = 0) -> None:
        if port < 2:
            if isinstance(value, (list, tuple)):
                self._input_vectors[port] = list(value)
            else:
                self._input_vectors[port] = [float(value), 0.0, 0.0]

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block
            self.input_source_ports[port] = source_port

    def update(self):
        for i in range(2):
            block = self.input_blocks[i]
            if block is not None:
                if hasattr(block, "getOutputVector"):
                    vec = block.getOutputVector()
                    if vec is not None:
                        self._input_vectors[i] = list(vec)
                    else:
                        val = block.getOutput(self.input_source_ports[i])
                        self._input_vectors[i] = [val, 0.0, 0.0]
                else:
                    val = block.getOutput(self.input_source_ports[i])
                    self._input_vectors[i] = [val, 0.0, 0.0]

        # Ensure vectors have at least 3 elements
        a = self._input_vectors[0] if self._input_vectors[0] else [0.0, 0.0, 0.0]
        b = self._input_vectors[1] if self._input_vectors[1] else [0.0, 0.0, 0.0]

        while len(a) < 3:
            a.append(0.0)
        while len(b) < 3:
            b.append(0.0)

        # Cross product: a x b
        self._output_vector[0] = a[1] * b[2] - a[2] * b[1]
        self._output_vector[1] = a[2] * b[0] - a[0] * b[2]
        self._output_vector[2] = a[0] * b[1] - a[1] * b[0]

    def getOutput(self, port=0):
        if port < 3:
            return self._output_vector[port]
        return 0.0

    def getOutputVector(self):
        return self._output_vector.copy()


class Hypot(Block):
    """Hypot block - computes sqrt(x^2 + y^2).

    Robust computation of hypotenuse without overflow.
    Supports both scalar and vector inputs.
    """

    def __init__(self):
        super().__init__()
        self.inputs = [0.0, 0.0]
        self.input_blocks = [None, None]
        self.input_source_ports = [0, 0]
        self.output = 0.0
        self._is_vector = False
        self._input_vectors = [None, None]
        self._output_vector = None

    def init(self):
        self.output = 0.0
        self._output_vector = None

    def setInput(self, value, port=0):
        if port < 2:
            if isinstance(value, (list, tuple)):
                self._setup_vector_mode(len(value))
                self._input_vectors[port] = list(value)
                self.inputs[port] = value[0] if value else 0.0
            else:
                self.inputs[port] = value

    def _setup_vector_mode(self, n):
        if not self._is_vector or (self._output_vector and len(self._output_vector) != n):
            self._is_vector = True
            self._output_vector = [0.0] * n

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block
            self.input_source_ports[port] = source_port

    def update(self):
        for i in range(2):
            block = self.input_blocks[i]
            if block is not None:
                if hasattr(block, "getOutputVector"):
                    vec = block.getOutputVector()
                    if vec is not None:
                        self._setup_vector_mode(len(vec))
                        self._input_vectors[i] = list(vec)
                        self.inputs[i] = vec[0] if vec else 0.0
                    else:
                        self.inputs[i] = block.getOutput(self.input_source_ports[i])
                else:
                    self.inputs[i] = block.getOutput(self.input_source_ports[i])

        if self._is_vector and self._output_vector:
            n = len(self._output_vector)
            for i in range(n):
                x = (
                    self._input_vectors[0][i]
                    if self._input_vectors[0] and i < len(self._input_vectors[0])
                    else self.inputs[0]
                )
                y = (
                    self._input_vectors[1][i]
                    if self._input_vectors[1] and i < len(self._input_vectors[1])
                    else self.inputs[1]
                )
                self._output_vector[i] = math.hypot(x, y)
            self.output = self._output_vector[0]
        else:
            self.output = math.hypot(self.inputs[0], self.inputs[1])

    def getOutput(self, port=0):
        if self._is_vector and self._output_vector and port < len(self._output_vector):
            return self._output_vector[port]
        return self.output

    def getOutputVector(self):
        if self._is_vector and self._output_vector:
            return self._output_vector.copy()
        return None


class UnaryMinus(Block):
    """Unary Minus block - negates input signal.

    Supports both scalar and vector inputs.
    """

    def __init__(self):
        super().__init__()
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = 0.0
        self._is_vector = False
        self._input_vector = None
        self._output_vector = None

    def init(self):
        self.output = 0.0
        self._output_vector = None

    def setInput(self, value, port=0):
        if isinstance(value, (list, tuple)):
            self._is_vector = True
            self._input_vector = list(value)
            self.input = value[0] if value else 0.0
        else:
            self._is_vector = False
            self._input_vector = None
            self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            if hasattr(self.input_block, "getOutputVector"):
                vec = self.input_block.getOutputVector()
                if vec is not None:
                    self._is_vector = True
                    self._input_vector = vec
                    self.input = vec[0] if vec else 0.0
                else:
                    self._is_vector = False
                    self._input_vector = None
                    self.input = self.input_block.getOutput(self.input_source_port)
            else:
                self._is_vector = False
                self._input_vector = None
                self.input = self.input_block.getOutput(self.input_source_port)

        if self._is_vector and self._input_vector:
            self._output_vector = [-v for v in self._input_vector]
            self.output = self._output_vector[0] if self._output_vector else 0.0
        else:
            self._output_vector = None
            self.output = -self.input

    def getOutput(self, port=0):
        if self._is_vector and self._output_vector and port < len(self._output_vector):
            return self._output_vector[port]
        return self.output

    def getOutputVector(self):
        if self._is_vector and self._output_vector:
            return self._output_vector.copy()
        return None


class SliderGain(Block):
    """Slider Gain block - gain with adjustable range.

    Functionally identical to Gain but includes min/max parameters
    for UI slider display.
    """

    def __init__(self, gain=1.0, min_val=0.0, max_val=10.0):
        super().__init__()
        self.gain = gain
        self.min_val = min_val
        self.max_val = max_val
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = 0.0
        self._is_vector = False
        self._input_vector = None
        self._output_vector = None

    def init(self):
        self.output = 0.0
        self._output_vector = None

    def setInput(self, value, port=0):
        if isinstance(value, (list, tuple)):
            self._is_vector = True
            self._input_vector = list(value)
            self.input = value[0] if value else 0.0
        else:
            self._is_vector = False
            self._input_vector = None
            self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            if hasattr(self.input_block, "getOutputVector"):
                vec = self.input_block.getOutputVector()
                if vec is not None:
                    self._is_vector = True
                    self._input_vector = vec
                    self.input = vec[0] if vec else 0.0
                else:
                    self._is_vector = False
                    self._input_vector = None
                    self.input = self.input_block.getOutput(self.input_source_port)
            else:
                self._is_vector = False
                self._input_vector = None
                self.input = self.input_block.getOutput(self.input_source_port)

        if self._is_vector and self._input_vector:
            self._output_vector = [self.gain * v for v in self._input_vector]
            self.output = self._output_vector[0] if self._output_vector else 0.0
        else:
            self._output_vector = None
            self.output = self.gain * self.input

    def getOutput(self, port=0):
        if self._is_vector and self._output_vector and port < len(self._output_vector):
            return self._output_vector[port]
        return self.output

    def getOutputVector(self):
        if self._is_vector and self._output_vector:
            return self._output_vector.copy()
        return None


class WeightedSum(Block):
    """Weighted Sum block - sum inputs with weights.

    Each input is multiplied by a weight before summing.
    """

    def __init__(self, weights=None):
        super().__init__()
        self.weights = weights if weights is not None else [1.0, 1.0]
        self.num_inputs = len(self.weights)
        self.inputs = [0.0] * self.num_inputs
        self.input_blocks = [None] * self.num_inputs
        self.input_source_ports = [0] * self.num_inputs
        self.output = 0.0
        self._is_vector = False
        self._input_vectors = [None] * self.num_inputs
        self._output_vector = None

    def init(self):
        self.output = 0.0
        self._output_vector = None

    def setInput(self, value, port=0):
        if port < self.num_inputs:
            if isinstance(value, (list, tuple)):
                self._setup_vector_mode(len(value))
                self._input_vectors[port] = list(value)
                self.inputs[port] = value[0] if value else 0.0
            else:
                self.inputs[port] = value

    def _setup_vector_mode(self, n):
        if not self._is_vector or (self._output_vector and len(self._output_vector) != n):
            self._is_vector = True
            self._output_vector = [0.0] * n

    def connectInput(self, block, port=0, source_port=0):
        if port < self.num_inputs:
            self.input_blocks[port] = block
            self.input_source_ports[port] = source_port

    def update(self):
        for i in range(self.num_inputs):
            block = self.input_blocks[i]
            if block is not None:
                if hasattr(block, "getOutputVector"):
                    vec = block.getOutputVector()
                    if vec is not None:
                        self._setup_vector_mode(len(vec))
                        self._input_vectors[i] = list(vec)
                        self.inputs[i] = vec[0] if vec else 0.0
                    else:
                        self.inputs[i] = block.getOutput(self.input_source_ports[i])
                else:
                    self.inputs[i] = block.getOutput(self.input_source_ports[i])

        if self._is_vector and self._output_vector:
            n = len(self._output_vector)
            for j in range(n):
                self._output_vector[j] = 0.0
                for i in range(self.num_inputs):
                    w = self.weights[i] if i < len(self.weights) else 1.0
                    if self._input_vectors[i] and j < len(self._input_vectors[i]):
                        self._output_vector[j] += w * self._input_vectors[i][j]
                    else:
                        self._output_vector[j] += w * self.inputs[i]
            self.output = self._output_vector[0]
        else:
            self.output = sum(w * v for w, v in zip(self.weights, self.inputs, strict=False))

    def getOutput(self, port=0):
        if self._is_vector and self._output_vector and port < len(self._output_vector):
            return self._output_vector[port]
        return self.output

    def getOutputVector(self):
        if self._is_vector and self._output_vector:
            return self._output_vector.copy()
        return None


class Polynomial(Block):
    """Polynomial block - evaluate polynomial expression.

    Evaluates polynomial with coefficients [a_n, ..., a_1, a_0]
    giving output = a_n*u^n + ... + a_1*u + a_0
    """

    def __init__(self, coefficients=None):
        super().__init__()
        self.coefficients = coefficients if coefficients is not None else [1.0, 0.0, 0.0]
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = 0.0
        self._is_vector = False
        self._input_vector = None
        self._output_vector = None

    def init(self):
        self.output = 0.0
        self._output_vector = None

    def _eval_poly(self, x):
        """Evaluate polynomial using Horner's method."""
        result = 0.0
        for coef in self.coefficients:
            result = result * x + coef
        return result

    def setInput(self, value, port=0):
        if isinstance(value, (list, tuple)):
            self._is_vector = True
            self._input_vector = list(value)
            self.input = value[0] if value else 0.0
        else:
            self._is_vector = False
            self._input_vector = None
            self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            if hasattr(self.input_block, "getOutputVector"):
                vec = self.input_block.getOutputVector()
                if vec is not None:
                    self._is_vector = True
                    self._input_vector = vec
                    self.input = vec[0] if vec else 0.0
                else:
                    self._is_vector = False
                    self._input_vector = None
                    self.input = self.input_block.getOutput(self.input_source_port)
            else:
                self._is_vector = False
                self._input_vector = None
                self.input = self.input_block.getOutput(self.input_source_port)

        if self._is_vector and self._input_vector:
            self._output_vector = [self._eval_poly(v) for v in self._input_vector]
            self.output = self._output_vector[0] if self._output_vector else 0.0
        else:
            self._output_vector = None
            self.output = self._eval_poly(self.input)

    def getOutput(self, port=0):
        if self._is_vector and self._output_vector and port < len(self._output_vector):
            return self._output_vector[port]
        return self.output

    def getOutputVector(self):
        if self._is_vector and self._output_vector:
            return self._output_vector.copy()
        return None


class MagnitudeAngle(Block):
    """Magnitude-Angle to Complex block.

    Converts magnitude and angle (in radians) to real and imaginary parts.
    real = mag * cos(angle)
    imag = mag * sin(angle)
    """

    def __init__(self):
        super().__init__()
        self.inputs = [0.0, 0.0]  # [magnitude, angle]
        self.input_blocks = [None, None]
        self.input_source_ports = [0, 0]
        self.outputs = [0.0, 0.0]  # [real, imag]

    def init(self):
        self.outputs = [0.0, 0.0]

    def setInput(self, value, port=0):
        if port < 2:
            self.inputs[port] = value

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block
            self.input_source_ports[port] = source_port

    def update(self):
        for i in range(2):
            block = self.input_blocks[i]
            if block is not None:
                self.inputs[i] = block.getOutput(self.input_source_ports[i])

        mag = self.inputs[0]
        angle = self.inputs[1]
        self.outputs[0] = mag * math.cos(angle)  # real
        self.outputs[1] = mag * math.sin(angle)  # imag

    def getOutput(self, port=0):
        if port < 2:
            return self.outputs[port]
        return 0.0


class ComplexToMagnitudeAngle(Block):
    """Complex to Magnitude-Angle block.

    Converts real and imaginary parts to magnitude and angle.
    mag = sqrt(real^2 + imag^2)
    angle = atan2(imag, real)
    """

    def __init__(self):
        super().__init__()
        self.inputs = [0.0, 0.0]  # [real, imag]
        self.input_blocks = [None, None]
        self.input_source_ports = [0, 0]
        self.outputs = [0.0, 0.0]  # [magnitude, angle]

    def init(self):
        self.outputs = [0.0, 0.0]

    def setInput(self, value, port=0):
        if port < 2:
            self.inputs[port] = value

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block
            self.input_source_ports[port] = source_port

    def update(self):
        for i in range(2):
            block = self.input_blocks[i]
            if block is not None:
                self.inputs[i] = block.getOutput(self.input_source_ports[i])

        real = self.inputs[0]
        imag = self.inputs[1]
        self.outputs[0] = math.hypot(real, imag)  # magnitude
        self.outputs[1] = math.atan2(imag, real)  # angle

    def getOutput(self, port=0):
        if port < 2:
            return self.outputs[port]
        return 0.0


class Sqrt(Block):
    """Square root block.

    Supports both scalar and vector inputs.
    """

    def __init__(self):
        super().__init__()
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = 0.0
        self._is_vector = False
        self._input_vector = None
        self._output_vector = None

    def init(self):
        self.output = 0.0
        self._output_vector = None

    def setInput(self, value, port=0):
        if isinstance(value, (list, tuple)):
            self._is_vector = True
            self._input_vector = list(value)
            self.input = value[0] if value else 0.0
        else:
            self._is_vector = False
            self._input_vector = None
            self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            if hasattr(self.input_block, "getOutputVector"):
                vec = self.input_block.getOutputVector()
                if vec is not None:
                    self._is_vector = True
                    self._input_vector = vec
                    self.input = vec[0] if vec else 0.0
                else:
                    self._is_vector = False
                    self._input_vector = None
                    self.input = self.input_block.getOutput(self.input_source_port)
            else:
                self._is_vector = False
                self._input_vector = None
                self.input = self.input_block.getOutput(self.input_source_port)

        if self._is_vector and self._input_vector:
            self._output_vector = [math.sqrt(max(v, 0.0)) for v in self._input_vector]
            self.output = self._output_vector[0] if self._output_vector else 0.0
        else:
            self._output_vector = None
            self.output = math.sqrt(max(self.input, 0.0))

    def getOutput(self, port=0):
        if self._is_vector and self._output_vector and port < len(self._output_vector):
            return self._output_vector[port]
        return self.output

    def getOutputVector(self):
        """Get the full output vector. Returns None for scalar operation."""
        if self._is_vector and self._output_vector:
            return self._output_vector.copy()
        return None


class Reciprocal(Block):
    """Reciprocal block - computes 1/u.

    Supports both scalar and vector inputs.
    """

    def __init__(self):
        super().__init__()
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = 0.0
        self._is_vector = False
        self._input_vector = None
        self._output_vector = None

    def init(self):
        self.output = 0.0
        self._output_vector = None

    def setInput(self, value, port=0):
        if isinstance(value, (list, tuple)):
            self._is_vector = True
            self._input_vector = list(value)
            self.input = value[0] if value else 0.0
        else:
            self._is_vector = False
            self._input_vector = None
            self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            if hasattr(self.input_block, "getOutputVector"):
                vec = self.input_block.getOutputVector()
                if vec is not None:
                    self._is_vector = True
                    self._input_vector = vec
                    self.input = vec[0] if vec else 0.0
                else:
                    self._is_vector = False
                    self._input_vector = None
                    self.input = self.input_block.getOutput(self.input_source_port)
            else:
                self._is_vector = False
                self._input_vector = None
                self.input = self.input_block.getOutput(self.input_source_port)

        if self._is_vector and self._input_vector:
            self._output_vector = [1.0 / v if v != 0 else float("inf") for v in self._input_vector]
            self.output = self._output_vector[0] if self._output_vector else 0.0
        else:
            self._output_vector = None
            self.output = 1.0 / self.input if self.input != 0 else float("inf")

    def getOutput(self, port=0):
        if self._is_vector and self._output_vector and port < len(self._output_vector):
            return self._output_vector[port]
        return self.output

    def getOutputVector(self):
        """Get the full output vector. Returns None for scalar operation."""
        if self._is_vector and self._output_vector:
            return self._output_vector.copy()
        return None


class Square(Block):
    """Square block - computes u².

    Supports both scalar and vector inputs.
    """

    def __init__(self):
        super().__init__()
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = 0.0
        self._is_vector = False
        self._input_vector = None
        self._output_vector = None

    def init(self):
        self.output = 0.0
        self._output_vector = None

    def setInput(self, value, port=0):
        if isinstance(value, (list, tuple)):
            self._is_vector = True
            self._input_vector = list(value)
            self.input = value[0] if value else 0.0
        else:
            self._is_vector = False
            self._input_vector = None
            self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            if hasattr(self.input_block, "getOutputVector"):
                vec = self.input_block.getOutputVector()
                if vec is not None:
                    self._is_vector = True
                    self._input_vector = vec
                    self.input = vec[0] if vec else 0.0
                else:
                    self._is_vector = False
                    self._input_vector = None
                    self.input = self.input_block.getOutput(self.input_source_port)
            else:
                self._is_vector = False
                self._input_vector = None
                self.input = self.input_block.getOutput(self.input_source_port)

        if self._is_vector and self._input_vector:
            self._output_vector = [v * v for v in self._input_vector]
            self.output = self._output_vector[0] if self._output_vector else 0.0
        else:
            self._output_vector = None
            self.output = self.input * self.input

    def getOutput(self, port=0):
        if self._is_vector and self._output_vector and port < len(self._output_vector):
            return self._output_vector[port]
        return self.output

    def getOutputVector(self):
        """Get the full output vector. Returns None for scalar operation."""
        if self._is_vector and self._output_vector:
            return self._output_vector.copy()
        return None


class Power(Block):
    """Power block - computes u^v.

    Raises first input to the power of second input.
    """

    def __init__(self):
        super().__init__()
        self.inputs = [0.0, 0.0]  # [base, exponent]
        self.input_blocks = [None, None]
        self.input_source_ports = [0, 0]
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def setInput(self, value, port=0):
        if port < 2:
            self.inputs[port] = value

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block
            self.input_source_ports[port] = source_port

    def update(self):
        for i in range(2):
            block = self.input_blocks[i]
            if block is not None:
                self.inputs[i] = block.getOutput(self.input_source_ports[i])

        base = self.inputs[0]
        exponent = self.inputs[1]

        try:
            self.output = math.pow(base, exponent)
        except (ValueError, OverflowError):
            self.output = 0.0

    def getOutput(self, port=0):
        return self.output


class Exp(Block):
    """Exp block - computes e^u.

    Supports both scalar and vector inputs.
    """

    def __init__(self):
        super().__init__()
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = 1.0
        self._is_vector = False
        self._input_vector = None
        self._output_vector = None

    def init(self):
        self.output = 1.0
        self._output_vector = None

    def setInput(self, value, port=0):
        if isinstance(value, (list, tuple)):
            self._is_vector = True
            self._input_vector = list(value)
            self.input = value[0] if value else 0.0
        else:
            self._is_vector = False
            self._input_vector = None
            self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            if hasattr(self.input_block, "getOutputVector"):
                vec = self.input_block.getOutputVector()
                if vec is not None:
                    self._is_vector = True
                    self._input_vector = vec
                    self.input = vec[0] if vec else 0.0
                else:
                    self._is_vector = False
                    self._input_vector = None
                    self.input = self.input_block.getOutput(self.input_source_port)
            else:
                self._is_vector = False
                self._input_vector = None
                self.input = self.input_block.getOutput(self.input_source_port)

        if self._is_vector and self._input_vector:
            self._output_vector = [
                math.exp(min(v, 700)) for v in self._input_vector
            ]  # Clamp to avoid overflow
            self.output = self._output_vector[0] if self._output_vector else 1.0
        else:
            self._output_vector = None
            self.output = math.exp(min(self.input, 700))  # Clamp to avoid overflow

    def getOutput(self, port=0):
        if self._is_vector and self._output_vector and port < len(self._output_vector):
            return self._output_vector[port]
        return self.output

    def getOutputVector(self):
        """Get the full output vector. Returns None for scalar operation."""
        if self._is_vector and self._output_vector:
            return self._output_vector.copy()
        return None


class Log(Block):
    """Log block - computes natural logarithm.

    Supports both scalar and vector inputs.
    """

    def __init__(self):
        super().__init__()
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = 0.0
        self._is_vector = False
        self._input_vector = None
        self._output_vector = None

    def init(self):
        self.output = 0.0
        self._output_vector = None

    def setInput(self, value, port=0):
        if isinstance(value, (list, tuple)):
            self._is_vector = True
            self._input_vector = list(value)
            self.input = value[0] if value else 0.0
        else:
            self._is_vector = False
            self._input_vector = None
            self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            if hasattr(self.input_block, "getOutputVector"):
                vec = self.input_block.getOutputVector()
                if vec is not None:
                    self._is_vector = True
                    self._input_vector = vec
                    self.input = vec[0] if vec else 0.0
                else:
                    self._is_vector = False
                    self._input_vector = None
                    self.input = self.input_block.getOutput(self.input_source_port)
            else:
                self._is_vector = False
                self._input_vector = None
                self.input = self.input_block.getOutput(self.input_source_port)

        if self._is_vector and self._input_vector:
            self._output_vector = [math.log(max(v, 1e-300)) for v in self._input_vector]
            self.output = self._output_vector[0] if self._output_vector else 0.0
        else:
            self._output_vector = None
            self.output = math.log(max(self.input, 1e-300))

    def getOutput(self, port=0):
        if self._is_vector and self._output_vector and port < len(self._output_vector):
            return self._output_vector[port]
        return self.output

    def getOutputVector(self):
        """Get the full output vector. Returns None for scalar operation."""
        if self._is_vector and self._output_vector:
            return self._output_vector.copy()
        return None


class Log10(Block):
    """Log10 block - computes base-10 logarithm.

    Supports both scalar and vector inputs.
    """

    def __init__(self):
        super().__init__()
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = 0.0
        self._is_vector = False
        self._input_vector = None
        self._output_vector = None

    def init(self):
        self.output = 0.0
        self._output_vector = None

    def setInput(self, value, port=0):
        if isinstance(value, (list, tuple)):
            self._is_vector = True
            self._input_vector = list(value)
            self.input = value[0] if value else 0.0
        else:
            self._is_vector = False
            self._input_vector = None
            self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            if hasattr(self.input_block, "getOutputVector"):
                vec = self.input_block.getOutputVector()
                if vec is not None:
                    self._is_vector = True
                    self._input_vector = vec
                    self.input = vec[0] if vec else 0.0
                else:
                    self._is_vector = False
                    self._input_vector = None
                    self.input = self.input_block.getOutput(self.input_source_port)
            else:
                self._is_vector = False
                self._input_vector = None
                self.input = self.input_block.getOutput(self.input_source_port)

        if self._is_vector and self._input_vector:
            self._output_vector = [math.log10(max(v, 1e-300)) for v in self._input_vector]
            self.output = self._output_vector[0] if self._output_vector else 0.0
        else:
            self._output_vector = None
            self.output = math.log10(max(self.input, 1e-300))

    def getOutput(self, port=0):
        if self._is_vector and self._output_vector and port < len(self._output_vector):
            return self._output_vector[port]
        return self.output

    def getOutputVector(self):
        """Get the full output vector. Returns None for scalar operation."""
        if self._is_vector and self._output_vector:
            return self._output_vector.copy()
        return None
