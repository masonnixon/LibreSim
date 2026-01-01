"""Python templates for continuous blocks."""

from ....models import BlockInfo


def integrator_template(block: BlockInfo, class_name: str) -> str:
    """Generate Integrator block code."""
    initial_condition = block.parameters.get("initialCondition", 0.0)
    limit_output = block.parameters.get("limitOutput", False)
    upper_limit = block.parameters.get("upperLimit", "float('inf')")
    lower_limit = block.parameters.get("lowerLimit", "-float('inf')")

    return f'''
class {class_name}:
    """Integrator block: {block.name}"""

    def __init__(self):
        self.initial_condition = {initial_condition}
        self.limit_output = {limit_output}
        self.upper_limit = {upper_limit}
        self.lower_limit = {lower_limit}
        self.input = 0.0
        self.state = {initial_condition}
        self.derivative = 0.0
        # Integration state for multi-pass methods
        self.x0 = 0.0
        self.xd0 = 0.0
        self.xd1 = 0.0
        self.xd2 = 0.0
        self.xd3 = 0.0
        self.xd4 = 0.0

    def init(self):
        self.state = self.initial_condition
        self.derivative = 0.0

    def update(self, t: float):
        self.derivative = self.input
        # Anti-windup: stop integrating at limits
        if self.limit_output:
            if self.state >= self.upper_limit and self.derivative > 0:
                self.derivative = 0.0
            elif self.state <= self.lower_limit and self.derivative < 0:
                self.derivative = 0.0

    def get_output(self, port: int = 0) -> float:
        output = self.state
        if self.limit_output:
            output = max(self.lower_limit, min(self.upper_limit, output))
        return output
'''


def derivative_template(block: BlockInfo, class_name: str) -> str:
    """Generate Derivative block code."""
    return f'''
class {class_name}:
    """Derivative block: {block.name}"""

    def __init__(self):
        self.input = 0.0
        self.prev_input = 0.0
        self.output = 0.0
        self.dt = 0.01  # Will be set by simulation

    def init(self):
        self.prev_input = 0.0
        self.output = 0.0

    def update(self, t: float):
        if self.dt > 0:
            self.output = (self.input - self.prev_input) / self.dt
        self.prev_input = self.input

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def transfer_function_template(block: BlockInfo, class_name: str) -> str:
    """Generate TransferFunction block code."""
    numerator = block.parameters.get("numerator", [1.0])
    denominator = block.parameters.get("denominator", [1.0, 1.0])

    # Ensure they are lists
    if not isinstance(numerator, list):
        numerator = [numerator]
    if not isinstance(denominator, list):
        denominator = [denominator]

    order = len(denominator) - 1

    return f'''
class {class_name}:
    """Transfer function block: {block.name}"""

    def __init__(self):
        self.numerator = {numerator}
        self.denominator = {denominator}
        self.order = {order}
        self.input = 0.0
        self.output = 0.0
        # State variables for controllable canonical form
        self.states = [0.0] * {order}
        self.derivatives = [0.0] * {order}
        # Integration state
        self.state = 0.0  # Alias for first state
        self.derivative = 0.0  # Alias for first derivative
        self.x0 = 0.0
        self.xd0 = 0.0
        self.xd1 = 0.0
        self.xd2 = 0.0
        self.xd3 = 0.0
        self.xd4 = 0.0

    def init(self):
        self.states = [0.0] * self.order
        self.derivatives = [0.0] * self.order
        self.output = 0.0

    def update(self, t: float):
        if self.order == 0:
            # Static gain
            self.output = self.input * self.numerator[0] / self.denominator[0]
            return

        # Normalize by leading denominator coefficient
        a0 = self.denominator[0]
        den_norm = [d / a0 for d in self.denominator]
        num_norm = [n / a0 for n in self.numerator]

        # Controllable canonical form state equations
        for i in range(self.order):
            if i < self.order - 1:
                self.derivatives[i] = self.states[i + 1]
            else:
                # Last state derivative
                self.derivatives[i] = self.input
                for j in range(1, len(den_norm)):
                    if j - 1 < len(self.states):
                        self.derivatives[i] -= den_norm[j] * self.states[self.order - j]

        # Compute output
        self.output = 0.0
        for i in range(len(num_norm)):
            if i < len(self.states):
                self.output += num_norm[len(num_norm) - 1 - i] * self.states[i]

        # Add direct feedthrough if numerator degree equals denominator degree
        if len(num_norm) > self.order:
            self.output += num_norm[0] * self.input

        # Sync single state/derivative for integration
        if self.order > 0:
            self.state = self.states[0]
            self.derivative = self.derivatives[0]

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def state_space_template(block: BlockInfo, class_name: str) -> str:
    """Generate StateSpace block code."""
    A = block.parameters.get("A", [[0.0]])
    B = block.parameters.get("B", [[1.0]])
    C = block.parameters.get("C", [[1.0]])
    D = block.parameters.get("D", [[0.0]])
    initial_state = block.parameters.get("initialState", None)

    # Determine state order
    if isinstance(A, list) and len(A) > 0:
        order = len(A)
    else:
        order = 1

    return f'''
class {class_name}:
    """State-space block: {block.name}"""

    def __init__(self):
        self.A = {A}
        self.B = {B}
        self.C = {C}
        self.D = {D}
        self.order = {order}
        self.input = 0.0
        self.output = 0.0
        self.states = {initial_state if initial_state else [0.0] * order}
        self.derivatives = [0.0] * {order}
        # Integration aliases
        self.state = 0.0
        self.derivative = 0.0
        self.x0 = 0.0
        self.xd0 = 0.0
        self.xd1 = 0.0
        self.xd2 = 0.0
        self.xd3 = 0.0
        self.xd4 = 0.0

    def init(self):
        self.states = [0.0] * self.order
        self.derivatives = [0.0] * self.order
        self.output = 0.0

    def update(self, t: float):
        # x_dot = A*x + B*u
        for i in range(self.order):
            self.derivatives[i] = 0.0
            for j in range(self.order):
                self.derivatives[i] += self.A[i][j] * self.states[j]
            self.derivatives[i] += self.B[i][0] * self.input

        # y = C*x + D*u
        self.output = 0.0
        for j in range(self.order):
            self.output += self.C[0][j] * self.states[j]
        self.output += self.D[0][0] * self.input

        # Sync for integration
        if self.order > 0:
            self.state = self.states[0]
            self.derivative = self.derivatives[0]

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def second_order_template(block: BlockInfo, class_name: str) -> str:
    """Generate SecondOrder block code."""
    omega = block.parameters.get("naturalFrequency", 1.0)
    zeta = block.parameters.get("dampingRatio", 0.7)

    return f'''
class {class_name}:
    """Second-order system block: {block.name}"""

    def __init__(self):
        self.omega = {omega}  # Natural frequency
        self.zeta = {zeta}    # Damping ratio
        self.input = 0.0
        self.output = 0.0
        # Two states: position and velocity
        self.state = 0.0   # Position
        self.state1 = 0.0  # Velocity
        self.derivative = 0.0   # d(position)/dt = velocity
        self.derivative1 = 0.0  # d(velocity)/dt = acceleration
        # Integration state
        self.x0 = 0.0
        self.xd0 = 0.0
        self.xd1 = 0.0
        self.xd2 = 0.0
        self.xd3 = 0.0
        self.xd4 = 0.0

    def init(self):
        self.state = 0.0
        self.state1 = 0.0
        self.output = 0.0

    def update(self, t: float):
        # Second-order ODE: x'' + 2*zeta*omega*x' + omega^2*x = omega^2*u
        self.derivative = self.state1
        self.derivative1 = (
            self.omega * self.omega * self.input
            - 2.0 * self.zeta * self.omega * self.state1
            - self.omega * self.omega * self.state
        )
        self.output = self.state

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def transport_delay_template(block: BlockInfo, class_name: str) -> str:
    """Generate TransportDelay block code."""
    delay = block.parameters.get("delay", 1.0)
    initial_output = block.parameters.get("initialOutput", 0.0)

    return f'''
class {class_name}:
    """Transport delay block: {block.name}"""

    def __init__(self):
        self.delay = {delay}
        self.initial_output = {initial_output}
        self.input = 0.0
        self.output = {initial_output}
        self.buffer = []  # (time, value) pairs
        self.dt = 0.01  # Will be set by simulation

    def init(self):
        self.buffer = []
        self.output = self.initial_output

    def update(self, t: float):
        # Add current input to buffer
        self.buffer.append((t, self.input))

        # Find output at t - delay
        target_time = t - self.delay
        if target_time < 0:
            self.output = self.initial_output
        else:
            # Find closest sample
            for i in range(len(self.buffer) - 1, -1, -1):
                if self.buffer[i][0] <= target_time:
                    self.output = self.buffer[i][1]
                    break
            else:
                self.output = self.initial_output

        # Trim old buffer entries
        while len(self.buffer) > 1 and self.buffer[0][0] < t - self.delay - self.dt:
            self.buffer.pop(0)

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


# Template registry for continuous blocks
CONTINUOUS_TEMPLATES = {
    "integrator": integrator_template,
    "limited_integrator": integrator_template,  # Same as integrator with limits
    "derivative": derivative_template,
    "transfer_function": transfer_function_template,
    "state_space": state_space_template,
    "second_order": second_order_template,
    "transport_delay": transport_delay_template,
}
