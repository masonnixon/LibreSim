"""Continuous-time blocks for OSK-based simulation."""

from ..block import Block
from ..state import State


class Integrator(Block):
    """Integrator block - integrates input signal."""

    def __init__(self, initial_condition=0.0, limit_output=False,
                 upper_limit=float('inf'), lower_limit=float('-inf')):
        super().__init__()
        self.initial_condition = initial_condition
        self.limit_output = limit_output
        self.upper_limit = upper_limit
        self.lower_limit = lower_limit
        self.input = 0.0
        self.input_block = None
        self.x = self.addIntegrator([initial_condition, 0.0])

    def init(self):
        self.x[0] = self.initial_condition
        self.x[1] = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput()

        # Set derivative
        self.x[1] = self.input

        # Apply limits if enabled
        if self.limit_output:
            if self.x[0] >= self.upper_limit and self.x[1] > 0:
                self.x[1] = 0.0
            elif self.x[0] <= self.lower_limit and self.x[1] < 0:
                self.x[1] = 0.0

    def getOutput(self, port=0):
        output = self.x[0]
        if self.limit_output:
            output = max(self.lower_limit, min(self.upper_limit, output))
        return output


class Derivative(Block):
    """Derivative block - differentiates input signal.

    Uses filtered derivative: Ns/(s+N) to avoid noise amplification.
    """

    def __init__(self, coefficient=100.0):
        super().__init__()
        self.coefficient = coefficient  # N in Ns/(s+N)
        self.input = 0.0
        self.input_block = None
        self.x = self.addIntegrator([0.0, 0.0])
        self.output = 0.0

    def init(self):
        self.x[0] = 0.0
        self.x[1] = 0.0
        self.output = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput()

        # Filtered derivative: y = N*(u - x), x' = y
        # This implements transfer function Ns/(s+N)
        self.output = self.coefficient * (self.input - self.x[0])
        self.x[1] = self.output

    def getOutput(self, port=0):
        return self.output


class TransferFunction(Block):
    """Transfer function block - continuous-time transfer function.

    Implements H(s) = num(s)/den(s) using state-space realization.
    """

    def __init__(self, numerator=None, denominator=None):
        super().__init__()
        self.numerator = numerator if numerator else [1.0]
        self.denominator = denominator if denominator else [1.0, 1.0]
        self.input = 0.0
        self.input_block = None
        self.output = 0.0

        # Create state variables for controllable canonical form
        self.order = len(self.denominator) - 1
        self.states = []
        for _ in range(self.order):
            self.states.append(self.addIntegrator([0.0, 0.0]))

    def init(self):
        for state in self.states:
            state[0] = 0.0
            state[1] = 0.0
        self.output = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput()

        if self.order == 0:
            # Static gain
            self.output = self.numerator[0] / self.denominator[0] * self.input
            return

        # Normalize coefficients
        a0 = self.denominator[0]
        num = [n / a0 for n in self.numerator]
        den = [d / a0 for d in self.denominator]

        # Pad numerator if needed
        while len(num) < len(den):
            num.insert(0, 0.0)

        # Controllable canonical form state equations
        # x' = Ax + Bu, y = Cx + Du
        for i in range(self.order):
            if i < self.order - 1:
                # x_i' = x_{i+1}
                self.states[i][1] = self.states[i + 1][0]
            else:
                # Last state derivative
                deriv = self.input
                for j in range(self.order):
                    deriv -= den[j + 1] * self.states[self.order - 1 - j][0]
                self.states[i][1] = deriv

        # Compute output
        self.output = num[-1] * self.input
        for i in range(self.order):
            self.output += (num[i] - num[-1] * den[i + 1]) * self.states[self.order - 1 - i][0]

    def getOutput(self, port=0):
        return self.output


class StateSpace(Block):
    """State-space model block.

    Implements: x' = Ax + Bu, y = Cx + Du
    """

    def __init__(self, A=None, B=None, C=None, D=None, initial_state=None):
        super().__init__()
        self.A = A if A else [[0.0]]
        self.B = B if B else [[1.0]]
        self.C = C if C else [[1.0]]
        self.D = D if D else [[0.0]]

        self.n = len(self.A)  # Number of states
        self.initial_state = initial_state if initial_state else [0.0] * self.n

        self.input = 0.0
        self.input_block = None
        self.output = 0.0

        # Create state variables
        self.states = []
        for i in range(self.n):
            self.states.append(self.addIntegrator([self.initial_state[i], 0.0]))

    def init(self):
        for i, state in enumerate(self.states):
            state[0] = self.initial_state[i] if i < len(self.initial_state) else 0.0
            state[1] = 0.0
        self.output = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput()

        # State derivatives: x' = Ax + Bu
        for i in range(self.n):
            deriv = 0.0
            for j in range(self.n):
                deriv += self.A[i][j] * self.states[j][0]
            deriv += self.B[i][0] * self.input
            self.states[i][1] = deriv

        # Output: y = Cx + Du
        self.output = 0.0
        for i in range(self.n):
            self.output += self.C[0][i] * self.states[i][0]
        self.output += self.D[0][0] * self.input

    def getOutput(self, port=0):
        return self.output


class PIDController(Block):
    """PID Controller block.

    Implements: u = Kp*e + Ki*integral(e) + Kd*de/dt
    with filtered derivative.
    """

    def __init__(self, Kp=1.0, Ki=0.0, Kd=0.0, N=100.0, initial_integrator=0.0):
        super().__init__()
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.N = N  # Derivative filter coefficient
        self.initial_integrator = initial_integrator

        self.input = 0.0
        self.input_block = None
        self.output = 0.0

        # Integrator state
        self.integral = self.addIntegrator([initial_integrator, 0.0])

        # Derivative filter state
        self.deriv_state = self.addIntegrator([0.0, 0.0])

    def init(self):
        self.integral[0] = self.initial_integrator
        self.integral[1] = 0.0
        self.deriv_state[0] = 0.0
        self.deriv_state[1] = 0.0
        self.output = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput()

        error = self.input

        # Proportional term
        p_term = self.Kp * error

        # Integral term
        self.integral[1] = error
        i_term = self.Ki * self.integral[0]

        # Derivative term (filtered)
        # Using: d/dt filter state = N * (error - filter state)
        # derivative output = N * (error - filter state)
        d_term = self.Kd * self.N * (error - self.deriv_state[0])
        self.deriv_state[1] = self.N * (error - self.deriv_state[0])

        self.output = p_term + i_term + d_term

    def getOutput(self, port=0):
        return self.output
