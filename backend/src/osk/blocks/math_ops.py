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
