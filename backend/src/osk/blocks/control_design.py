"""Control system design blocks for LibreSim.

These blocks implement control system design functions similar to
MATLAB Control System Toolbox.
"""

from typing import Any

from ..block import Block


class LQRController(Block):
    """Linear Quadratic Regulator (LQR) controller.

    Implements optimal state-feedback control: u = -K*x
    where K is the LQR gain matrix.
    """

    def __init__(self, K: Any = None, num_states: int = 1, num_inputs: int = 1):
        super().__init__()
        # K is the feedback gain matrix (num_inputs x num_states)
        self.K: list[list[float]] = K if K else [[1.0] * num_states for _ in range(num_inputs)]
        self.num_states = num_states
        self.num_inputs = num_inputs
        self._x_state: list[float] = [0.0] * num_states
        self._output: list[float] = [0.0] * num_inputs
        self.input_block: Any = None
        self._is_vector = num_inputs > 1

    def init(self) -> None:
        self._output = [0.0] * self.num_inputs

    def setInput(self, value: Any, port: int = 0) -> None:
        if port < self.num_states:
            self._x_state[port] = value

    def connectInput(self, block: Any, port: int = 0, source_port: int = 0) -> None:
        self.input_block = block

    def update(self) -> None:
        if self.input_block is not None:
            vec = self.input_block.getOutputVector()
            if vec is not None:
                for i in range(min(len(vec), self.num_states)):
                    self._x_state[i] = vec[i]
            else:
                self._x_state[0] = self.input_block.getOutput()

        # u = -K * x
        for i in range(self.num_inputs):
            u = 0.0
            for j in range(self.num_states):
                u -= self.K[i][j] * self._x_state[j]
            self._output[i] = u

    def getOutput(self, port: int = 0) -> float:
        if port < len(self._output):
            return self._output[port]
        return 0.0

    def getOutputVector(self) -> list[float] | None:
        return self._output if self._is_vector else None


class PolePlacement(Block):
    """Pole Placement state-feedback controller.

    Implements state-feedback u = -K*x where K places poles
    at desired locations (Ackermann's formula for SISO).
    """

    def __init__(self, K: Any = None, num_states: int = 1):
        super().__init__()
        self.K: list[float] = K if K else [1.0] * num_states
        self.num_states = num_states
        self._x_state: list[float] = [0.0] * num_states
        self._output: float = 0.0
        self.input_block: Any = None

    def init(self) -> None:
        self._output = 0.0

    def setInput(self, value: Any, port: int = 0) -> None:
        if port < self.num_states:
            self._x_state[port] = value

    def connectInput(self, block: Any, port: int = 0, source_port: int = 0) -> None:
        self.input_block = block

    def update(self) -> None:
        if self.input_block is not None:
            vec = self.input_block.getOutputVector()
            if vec is not None:
                for i in range(min(len(vec), self.num_states)):
                    self._x_state[i] = vec[i]
            else:
                self._x_state[0] = self.input_block.getOutput()

        # u = -K * x (SISO case)
        self._output = -sum(k * x for k, x in zip(self.K, self._x_state, strict=False))

    def getOutput(self, port: int = 0) -> float:
        return self._output


class LeadLagCompensator(Block):
    """Lead-Lag Compensator.

    Implements transfer function: K * (s + z) / (s + p)
    Lead: z < p (phase lead)
    Lag: z > p (phase lag)
    """

    def __init__(self, gain=1.0, zero=-1.0, pole=-10.0):
        super().__init__()
        self.gain = gain
        self.zero = zero  # zero location
        self.pole = pole  # pole location
        self.input = 0.0
        self.output = 0.0
        self.input_block = None
        self.input_source_port = 0

        # State for first-order system
        self.x = self.addIntegrator([0.0, 0.0])

    def init(self):
        self.x[0] = 0.0
        self.x[1] = 0.0
        self.output = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput(self.input_source_port)

        # State equation: x' = -p*x + u
        # Output: y = K*(z-p)*x + K*u
        self.x[1] = -self.pole * self.x[0] + self.input
        self.output = self.gain * (self.zero - self.pole) * self.x[0] + self.gain * self.input

    def getOutput(self, port=0):
        return self.output


class PIController(Block):
    """Proportional-Integral Controller.

    Simple PI controller: u = Kp*e + Ki*integral(e)
    """

    def __init__(self, Kp=1.0, Ki=1.0, initial_integrator=0.0):
        super().__init__()
        self.Kp = Kp
        self.Ki = Ki
        self.initial_integrator = initial_integrator
        self.input = 0.0
        self.output = 0.0
        self.input_block = None
        self.input_source_port = 0

        self.integrator = self.addIntegrator([initial_integrator, 0.0])

    def init(self):
        self.integrator[0] = self.initial_integrator
        self.integrator[1] = 0.0
        self.output = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput(self.input_source_port)

        error = self.input
        self.integrator[1] = error

        p_term = self.Kp * error
        i_term = self.Ki * self.integrator[0]

        self.output = p_term + i_term

    def getOutput(self, port=0):
        return self.output


class PDController(Block):
    """Proportional-Derivative Controller.

    PD controller with filtered derivative: u = Kp*e + Kd*N*e/(1 + N/s)
    """

    def __init__(self, Kp=1.0, Kd=1.0, N=100.0):
        super().__init__()
        self.Kp = Kp
        self.Kd = Kd
        self.N = N  # Derivative filter coefficient
        self.input = 0.0
        self.output = 0.0
        self.input_block = None
        self.input_source_port = 0

        # Derivative filter state
        self.deriv_state = self.addIntegrator([0.0, 0.0])

    def init(self):
        self.deriv_state[0] = 0.0
        self.deriv_state[1] = 0.0
        self.output = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput(self.input_source_port)

        error = self.input

        # Filtered derivative
        self.deriv_state[1] = self.N * (error - self.deriv_state[0])
        d_term = self.Kd * self.deriv_state[1]

        self.output = self.Kp * error + d_term

    def getOutput(self, port=0):
        return self.output


class AntiWindupPID(Block):
    """PID Controller with anti-windup.

    Implements back-calculation anti-windup to prevent integrator
    saturation when output limits are reached.
    """

    def __init__(
        self,
        Kp=1.0,
        Ki=1.0,
        Kd=0.0,
        N=100.0,
        upper_limit=float("inf"),
        lower_limit=float("-inf"),
        Kb=1.0,
    ):
        super().__init__()
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.N = N
        self.upper_limit = upper_limit
        self.lower_limit = lower_limit
        self.Kb = Kb  # Back-calculation gain

        self.input = 0.0
        self.output = 0.0
        self.input_block = None
        self.input_source_port = 0

        self.integrator = self.addIntegrator([0.0, 0.0])
        self.deriv_state = self.addIntegrator([0.0, 0.0])

    def init(self):
        self.integrator[0] = 0.0
        self.integrator[1] = 0.0
        self.deriv_state[0] = 0.0
        self.deriv_state[1] = 0.0
        self.output = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput(self.input_source_port)

        error = self.input

        # P term
        p_term = self.Kp * error

        # I term
        i_term = self.Ki * self.integrator[0]

        # D term (filtered)
        self.deriv_state[1] = self.N * (error - self.deriv_state[0])
        d_term = self.Kd * self.deriv_state[1]

        # Unsaturated output
        u_unsat = p_term + i_term + d_term

        # Saturate output
        u_sat = max(self.lower_limit, min(self.upper_limit, u_unsat))
        self.output = u_sat

        # Back-calculation: modify integrator input
        saturation_error = u_sat - u_unsat
        self.integrator[1] = error + self.Kb * saturation_error

    def getOutput(self, port=0):
        return self.output


class ModelReference(Block):
    """Model Reference block for adaptive control.

    Generates reference trajectory from a reference model.
    Implements: G_m(s) = wn^2 / (s^2 + 2*zeta*wn*s + wn^2)
    """

    def __init__(self, natural_frequency=1.0, damping_ratio=1.0):
        super().__init__()
        self.wn = natural_frequency
        self.zeta = damping_ratio
        self.input = 0.0
        self.output = 0.0
        self.input_block = None
        self.input_source_port = 0

        self.x1 = self.addIntegrator([0.0, 0.0])
        self.x2 = self.addIntegrator([0.0, 0.0])

    def init(self):
        self.x1[0] = 0.0
        self.x1[1] = 0.0
        self.x2[0] = 0.0
        self.x2[1] = 0.0
        self.output = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput(self.input_source_port)

        wn = self.wn
        wn2 = wn * wn

        self.x1[1] = self.x2[0]
        self.x2[1] = -wn2 * self.x1[0] - 2 * self.zeta * wn * self.x2[0] + wn2 * self.input

        self.output = self.x1[0]

    def getOutput(self, port=0):
        return self.output
