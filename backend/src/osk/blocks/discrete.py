"""Discrete-time blocks for OSK-based simulation."""

from ..block import Block
from ..state import State


class UnitDelay(Block):
    """Unit Delay block - delays signal by one sample period."""

    def __init__(self, initial_condition=0.0, sample_time=0.1):
        super().__init__()
        self.initial_condition = initial_condition
        self.sample_time = sample_time
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.prev_value = initial_condition
        self.output = initial_condition
        self.last_sample_time = -sample_time

    def init(self):
        self.prev_value = self.initial_condition
        self.output = self.initial_condition
        self.last_sample_time = -self.sample_time

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput(self.input_source_port)

        # Check if it's time to sample
        if State.t - self.last_sample_time >= self.sample_time - State.EPS:
            self.output = self.prev_value
            self.prev_value = self.input
            self.last_sample_time = State.t

    def getOutput(self, port=0):
        return self.output


class ZeroOrderHold(Block):
    """Zero-Order Hold block - sample and hold input signal."""

    def __init__(self, sample_time=0.1):
        super().__init__()
        self.sample_time = sample_time
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.held_value = 0.0
        self.last_sample_time = -sample_time

    def init(self):
        self.held_value = 0.0
        self.last_sample_time = -self.sample_time

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput(self.input_source_port)

        # Check if it's time to sample
        if State.t - self.last_sample_time >= self.sample_time - State.EPS:
            self.held_value = self.input
            self.last_sample_time = State.t

    def getOutput(self, port=0):
        return self.held_value


class DiscreteIntegrator(Block):
    """Discrete-time integrator block."""

    def __init__(self, method='forward', sample_time=0.1, initial_condition=0.0):
        super().__init__()
        self.method = method  # 'forward', 'backward', 'trapezoidal'
        self.sample_time = sample_time
        self.initial_condition = initial_condition
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.prev_input = 0.0
        self.output = initial_condition
        self.last_sample_time = -sample_time

    def init(self):
        self.prev_input = 0.0
        self.output = self.initial_condition
        self.last_sample_time = -self.sample_time

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput(self.input_source_port)

        # Check if it's time to update
        if State.t - self.last_sample_time >= self.sample_time - State.EPS:
            if self.method == 'forward':
                # Forward Euler: y[n] = y[n-1] + T*u[n-1]
                self.output += self.sample_time * self.prev_input
            elif self.method == 'backward':
                # Backward Euler: y[n] = y[n-1] + T*u[n]
                self.output += self.sample_time * self.input
            elif self.method == 'trapezoidal':
                # Trapezoidal: y[n] = y[n-1] + T/2*(u[n] + u[n-1])
                self.output += self.sample_time / 2.0 * (self.input + self.prev_input)

            self.prev_input = self.input
            self.last_sample_time = State.t

    def getOutput(self, port=0):
        return self.output


class DiscreteDerivative(Block):
    """Discrete-time derivative block."""

    def __init__(self, sample_time=0.1, initial_condition=0.0):
        super().__init__()
        self.sample_time = sample_time
        self.initial_condition = initial_condition
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.prev_input = initial_condition
        self.output = 0.0
        self.last_sample_time = -sample_time

    def init(self):
        self.prev_input = self.initial_condition
        self.output = 0.0
        self.last_sample_time = -self.sample_time

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput(self.input_source_port)

        # Check if it's time to update
        if State.t - self.last_sample_time >= self.sample_time - State.EPS:
            # Discrete derivative: y[n] = (u[n] - u[n-1]) / T
            self.output = (self.input - self.prev_input) / self.sample_time
            self.prev_input = self.input
            self.last_sample_time = State.t

    def getOutput(self, port=0):
        return self.output


class DiscreteTransferFunction(Block):
    """Discrete-time transfer function block.

    Implements H(z) = num(z)/den(z)
    """

    def __init__(self, numerator=None, denominator=None, sample_time=0.1):
        super().__init__()
        self.numerator = numerator if numerator else [1.0]
        self.denominator = denominator if denominator else [1.0, -0.5]
        self.sample_time = sample_time
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = 0.0
        self.last_sample_time = -sample_time

        # State buffers for past inputs and outputs
        self.order = max(len(self.numerator), len(self.denominator)) - 1
        self.input_buffer = [0.0] * (self.order + 1)
        self.output_buffer = [0.0] * (self.order + 1)

    def init(self):
        self.input_buffer = [0.0] * (self.order + 1)
        self.output_buffer = [0.0] * (self.order + 1)
        self.output = 0.0
        self.last_sample_time = -self.sample_time

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput(self.input_source_port)

        # Check if it's time to update
        if State.t - self.last_sample_time >= self.sample_time - State.EPS:
            # Shift buffers
            for i in range(self.order, 0, -1):
                self.input_buffer[i] = self.input_buffer[i - 1]
                self.output_buffer[i] = self.output_buffer[i - 1]

            self.input_buffer[0] = self.input

            # Compute output: y[n] = (b0*u[n] + b1*u[n-1] + ... - a1*y[n-1] - ...) / a0
            a0 = self.denominator[0]
            result = 0.0

            # Add numerator terms
            for i, b in enumerate(self.numerator):
                if i < len(self.input_buffer):
                    result += b * self.input_buffer[i]

            # Subtract denominator terms (except a0)
            for i in range(1, len(self.denominator)):
                if i < len(self.output_buffer):
                    result -= self.denominator[i] * self.output_buffer[i]

            self.output = result / a0
            self.output_buffer[0] = self.output
            self.last_sample_time = State.t

    def getOutput(self, port=0):
        return self.output
