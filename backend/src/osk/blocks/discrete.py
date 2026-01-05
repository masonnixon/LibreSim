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

    def __init__(self, method="forward", sample_time=0.1, initial_condition=0.0):
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
            if self.method == "forward":
                # Forward Euler: y[n] = y[n-1] + T*u[n-1]
                self.output += self.sample_time * self.prev_input
            elif self.method == "backward":
                # Backward Euler: y[n] = y[n-1] + T*u[n]
                self.output += self.sample_time * self.input
            elif self.method == "trapezoidal":
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


class Memory(Block):
    """Memory block - outputs previous timestep's input value.

    Unlike Unit Delay which operates at a fixed sample time, Memory
    delays the signal by exactly one simulation time step.
    """

    def __init__(self, initial_condition=0.0):
        super().__init__()
        self.initial_condition = initial_condition
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = initial_condition
        self._prev_value = initial_condition

    def init(self):
        self.output = self.initial_condition
        self._prev_value = self.initial_condition

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput(self.input_source_port)

        # Output previous value
        self.output = self._prev_value

    def rpt(self):
        # Update previous value at end of timestep
        if State.ready:
            self._prev_value = self.input

    def getOutput(self, port=0):
        return self.output


class DiscreteStateSpace(Block):
    """Discrete State-Space block.

    Implements: x[k+1] = A*x[k] + B*u[k], y[k] = C*x[k] + D*u[k]
    """

    def __init__(self, A=None, B=None, C=None, D=None, initial_state=None, sample_time=0.1):
        super().__init__()
        self.A = A if A else [[1.0]]
        self.B = B if B else [[1.0]]
        self.C = C if C else [[1.0]]
        self.D = D if D else [[0.0]]
        self.sample_time = sample_time

        self.n = len(self.A)  # Number of states
        self.initial_state = initial_state if initial_state else [0.0] * self.n

        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = 0.0
        self.last_sample_time = -sample_time

        # State vector
        self.state = list(self.initial_state)

    def init(self):
        self.state = list(self.initial_state)
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
            # Compute output: y = C*x + D*u
            self.output = 0.0
            for i in range(self.n):
                self.output += self.C[0][i] * self.state[i]
            self.output += self.D[0][0] * self.input

            # Compute next state: x[k+1] = A*x[k] + B*u[k]
            new_state = [0.0] * self.n
            for i in range(self.n):
                for j in range(self.n):
                    new_state[i] += self.A[i][j] * self.state[j]
                new_state[i] += self.B[i][0] * self.input

            self.state = new_state
            self.last_sample_time = State.t

    def getOutput(self, port=0):
        return self.output


class FirstOrderHold(Block):
    """First-Order Hold block - sample and extrapolate using derivative.

    Unlike Zero-Order Hold which holds the last sampled value constant,
    First-Order Hold extrapolates using the rate of change.
    """

    def __init__(self, sample_time=0.1):
        super().__init__()
        self.sample_time = sample_time
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = 0.0
        self.last_sample_time = -sample_time
        self._prev_sample = 0.0
        self._curr_sample = 0.0
        self._slope = 0.0

    def init(self):
        self.output = 0.0
        self.last_sample_time = -self.sample_time
        self._prev_sample = 0.0
        self._curr_sample = 0.0
        self._slope = 0.0

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
            self._prev_sample = self._curr_sample
            self._curr_sample = self.input
            # Calculate slope for extrapolation
            if self.sample_time > 0:
                self._slope = (self._curr_sample - self._prev_sample) / self.sample_time
            self.last_sample_time = State.t

        # Extrapolate from last sample
        dt = State.t - self.last_sample_time
        self.output = self._curr_sample + self._slope * dt

    def getOutput(self, port=0):
        return self.output


class DiscretePIDController(Block):
    """Discrete PID Controller block.

    Implements: u[k] = Kp*e[k] + Ki*Ts*sum(e) + Kd/Ts*(e[k] - e[k-1])
    with various discretization methods.
    """

    def __init__(self, Kp=1.0, Ki=0.0, Kd=0.0, N=100.0, sample_time=0.1, method="forward"):
        super().__init__()
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.N = N  # Derivative filter coefficient
        self.sample_time = sample_time
        self.method = method  # 'forward', 'backward', 'trapezoidal'

        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = 0.0
        self.last_sample_time = -sample_time

        # State variables
        self._integral = 0.0
        self._prev_error = 0.0
        self._prev_derivative = 0.0

    def init(self):
        self.output = 0.0
        self.last_sample_time = -self.sample_time
        self._integral = 0.0
        self._prev_error = 0.0
        self._prev_derivative = 0.0

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
            error = self.input
            Ts = self.sample_time

            # Proportional term
            p_term = self.Kp * error

            # Integral term
            if self.method == "forward":
                self._integral += Ts * self._prev_error
            elif self.method == "backward":
                self._integral += Ts * error
            else:  # trapezoidal
                self._integral += Ts * (error + self._prev_error) / 2
            i_term = self.Ki * self._integral

            # Derivative term with filter
            # Using: D[k] = (Td/N) / (Td/N + Ts) * D[k-1] + Kd*N / (Td/N + Ts) * (e[k] - e[k-1])
            # Simplified for Kd only:
            if self.N > 0 and Ts > 0:
                alpha = self.N * Ts
                d_term = (self._prev_derivative + self.Kd * self.N * (error - self._prev_error)) / (
                    1 + alpha
                )
                self._prev_derivative = d_term
            else:
                d_term = self.Kd * (error - self._prev_error) / Ts if Ts > 0 else 0.0

            self.output = p_term + i_term + d_term
            self._prev_error = error
            self.last_sample_time = State.t

    def getOutput(self, port=0):
        return self.output
