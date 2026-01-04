"""Python templates for control design blocks."""

from ....models import BlockInfo


def pid_controller_template(block: BlockInfo, class_name: str) -> str:
    """Generate PID controller block code."""
    kp = block.parameters.get("Kp", 1.0)
    ki = block.parameters.get("Ki", 1.0)
    kd = block.parameters.get("Kd", 0.0)
    n = block.parameters.get("N", 100.0)
    return f'''
class {class_name}:
    """PID Controller block: {block.name}"""

    def __init__(self):
        self.Kp = {kp}
        self.Ki = {ki}
        self.Kd = {kd}
        self.N = {n}  # Derivative filter coefficient
        self.input = 0.0
        self.output = 0.0

        # Primary integrator interface (for integral term)
        # state/derivative are aliases to integrator[0]/integrator[1]
        self.state = 0.0
        self.derivative = 0.0
        self.x0 = 0.0
        self.xd0 = 0.0
        self.xd1 = 0.0
        self.xd2 = 0.0
        self.xd3 = 0.0

        # Derivative filter state (second integrator)
        self.deriv_state = 0.0
        self.deriv_derivative = 0.0
        self.deriv_x0 = 0.0
        self.deriv_xd0 = 0.0
        self.deriv_xd1 = 0.0
        self.deriv_xd2 = 0.0
        self.deriv_xd3 = 0.0

    def init(self):
        self.state = 0.0
        self.derivative = 0.0
        self.deriv_state = 0.0
        self.deriv_derivative = 0.0
        self.output = 0.0

    def update(self, t: float):
        error = self.input

        # P term
        p_term = self.Kp * error

        # I term: derivative is the error, integral accumulates
        self.derivative = error
        i_term = self.Ki * self.state

        # D term (filtered derivative)
        # d/dt(deriv_state) = N * (error - deriv_state)
        self.deriv_derivative = self.N * (error - self.deriv_state)
        d_term = self.Kd * self.deriv_derivative

        self.output = p_term + i_term + d_term

    def propagate_states(self, dt: float, kpass: int):
        """Propagate the derivative filter state using RK4 integration."""
        # The main integral state is handled by the standard propagator
        # We handle the derivative filter state here
        if kpass == 0:
            self.deriv_x0 = self.deriv_state
            self.deriv_xd0 = self.deriv_derivative
            self.deriv_state = self.deriv_x0 + dt / 2.0 * self.deriv_xd0
        elif kpass == 1:
            self.deriv_xd1 = self.deriv_derivative
            self.deriv_state = self.deriv_x0 + dt / 2.0 * self.deriv_xd1
        elif kpass == 2:
            self.deriv_xd2 = self.deriv_derivative
            self.deriv_state = self.deriv_x0 + dt * self.deriv_xd2
        elif kpass == 3:
            self.deriv_xd3 = self.deriv_derivative
            self.deriv_state = self.deriv_x0 + dt / 6.0 * (
                self.deriv_xd0 + 2.0 * self.deriv_xd1 +
                2.0 * self.deriv_xd2 + self.deriv_xd3
            )

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def pi_controller_template(block: BlockInfo, class_name: str) -> str:
    """Generate PI controller block code."""
    kp = block.parameters.get("Kp", 1.0)
    ki = block.parameters.get("Ki", 1.0)
    initial = block.parameters.get("initial_integrator", 0.0)
    return f'''
class {class_name}:
    """PI Controller block: {block.name}"""

    def __init__(self):
        self.Kp = {kp}
        self.Ki = {ki}
        self.initial_integrator = {initial}
        self.input = 0.0
        self.output = 0.0
        # Integrator state [value, derivative]
        self.integrator = [{initial}, 0.0]
        self.xd0 = 0.0
        self.xd1 = 0.0
        self.xd2 = 0.0
        self.xd3 = 0.0

    def init(self):
        self.integrator = [self.initial_integrator, 0.0]
        self.output = 0.0

    def update(self, t: float):
        error = self.input
        self.integrator[1] = error

        p_term = self.Kp * error
        i_term = self.Ki * self.integrator[0]

        self.output = p_term + i_term

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def pd_controller_template(block: BlockInfo, class_name: str) -> str:
    """Generate PD controller block code."""
    kp = block.parameters.get("Kp", 1.0)
    kd = block.parameters.get("Kd", 1.0)
    n = block.parameters.get("N", 100.0)
    return f'''
class {class_name}:
    """PD Controller block: {block.name}"""

    def __init__(self):
        self.Kp = {kp}
        self.Kd = {kd}
        self.N = {n}  # Derivative filter coefficient
        self.input = 0.0
        self.output = 0.0
        # Derivative filter state [value, derivative]
        self.deriv_state = [0.0, 0.0]
        self.xd0 = 0.0
        self.xd1 = 0.0
        self.xd2 = 0.0
        self.xd3 = 0.0

    def init(self):
        self.deriv_state = [0.0, 0.0]
        self.output = 0.0

    def update(self, t: float):
        error = self.input

        # Filtered derivative
        self.deriv_state[1] = self.N * (error - self.deriv_state[0])
        d_term = self.Kd * self.deriv_state[1]

        self.output = self.Kp * error + d_term

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def anti_windup_pid_template(block: BlockInfo, class_name: str) -> str:
    """Generate Anti-windup PID controller block code."""
    kp = block.parameters.get("Kp", 1.0)
    ki = block.parameters.get("Ki", 1.0)
    kd = block.parameters.get("Kd", 0.0)
    n = block.parameters.get("N", 100.0)
    upper = block.parameters.get("upper_limit", "float('inf')")
    lower = block.parameters.get("lower_limit", "float('-inf')")
    kb = block.parameters.get("Kb", 1.0)
    return f'''
class {class_name}:
    """Anti-windup PID Controller block: {block.name}"""

    def __init__(self):
        self.Kp = {kp}
        self.Ki = {ki}
        self.Kd = {kd}
        self.N = {n}
        self.upper_limit = {upper}
        self.lower_limit = {lower}
        self.Kb = {kb}  # Back-calculation gain
        self.input = 0.0
        self.output = 0.0
        # Integrator state
        self.integrator = [0.0, 0.0]
        self.xd0_int = 0.0
        self.xd1_int = 0.0
        self.xd2_int = 0.0
        self.xd3_int = 0.0
        # Derivative filter state
        self.deriv_state = [0.0, 0.0]
        self.xd0_der = 0.0
        self.xd1_der = 0.0
        self.xd2_der = 0.0
        self.xd3_der = 0.0

    def init(self):
        self.integrator = [0.0, 0.0]
        self.deriv_state = [0.0, 0.0]
        self.output = 0.0

    def update(self, t: float):
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

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def lead_lag_compensator_template(block: BlockInfo, class_name: str) -> str:
    """Generate Lead-Lag compensator block code."""
    gain = block.parameters.get("gain", 1.0)
    zero = block.parameters.get("zero", -1.0)
    pole = block.parameters.get("pole", -10.0)
    return f'''
class {class_name}:
    """Lead-Lag Compensator block: {block.name}

    Implements: K * (s + z) / (s + p)
    Lead when |z| < |p|, Lag when |z| > |p|
    """

    def __init__(self):
        self.gain = {gain}
        self.zero = {zero}
        self.pole = {pole}
        self.input = 0.0
        self.output = 0.0
        # State [value, derivative]
        self.x = [0.0, 0.0]
        self.xd0 = 0.0
        self.xd1 = 0.0
        self.xd2 = 0.0
        self.xd3 = 0.0

    def init(self):
        self.x = [0.0, 0.0]
        self.output = 0.0

    def update(self, t: float):
        # State equation: x' = -p*x + u
        self.x[1] = -self.pole * self.x[0] + self.input
        # Output: y = K*(z-p)*x + K*u
        self.output = self.gain * (self.zero - self.pole) * self.x[0] + self.gain * self.input

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def lqr_controller_template(block: BlockInfo, class_name: str) -> str:
    """Generate LQR controller block code."""
    K = block.parameters.get("K", [[1.0]])
    # Infer dimensions from K matrix if not explicitly provided
    num_inputs = block.parameters.get("num_inputs", len(K))
    num_states = block.parameters.get("num_states", len(K[0]) if K else 1)
    return f'''
class {class_name}:
    """LQR Controller block: {block.name}

    Implements optimal state-feedback: u = -K*x
    """

    def __init__(self):
        self.K = {K}
        self.num_states = {num_states}
        self.num_inputs = {num_inputs}
        self.state = [0.0] * {num_states}
        self.output = [0.0] * {num_inputs}
        self.input = 0.0

    def init(self):
        self.state = [0.0] * self.num_states
        self.output = [0.0] * self.num_inputs

    def update(self, t: float):
        # u = -K * x
        for i in range(self.num_inputs):
            u = 0.0
            for j in range(self.num_states):
                u -= self.K[i][j] * self.state[j]
            self.output[i] = u

    def get_output(self, port: int = 0) -> float:
        if port < len(self.output):
            return self.output[port]
        return 0.0
'''


def pole_placement_template(block: BlockInfo, class_name: str) -> str:
    """Generate Pole Placement controller block code."""
    K = block.parameters.get("K", [1.0])
    # Infer dimensions from K vector if not explicitly provided
    num_states = block.parameters.get("num_states", len(K) if isinstance(K, list) else 1)
    return f'''
class {class_name}:
    """Pole Placement Controller block: {block.name}

    Implements state-feedback: u = -K*x
    """

    def __init__(self):
        self.K = {K}
        self.num_states = {num_states}
        self.state = [0.0] * {num_states}
        self.output = 0.0
        self.input = 0.0

    def init(self):
        self.state = [0.0] * self.num_states
        self.output = 0.0

    def update(self, t: float):
        # u = -K * x (SISO)
        self.output = -sum(k * x for k, x in zip(self.K, self.state))

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def model_reference_template(block: BlockInfo, class_name: str) -> str:
    """Generate Model Reference block code."""
    wn = block.parameters.get("natural_frequency", 1.0)
    zeta = block.parameters.get("damping_ratio", 1.0)
    return f'''
class {class_name}:
    """Model Reference block: {block.name}

    Implements: wn^2 / (s^2 + 2*zeta*wn*s + wn^2)
    """

    def __init__(self):
        self.wn = {wn}
        self.zeta = {zeta}
        self.input = 0.0
        self.output = 0.0
        # States [value, derivative]
        self.x1 = [0.0, 0.0]
        self.x2 = [0.0, 0.0]
        self.xd0_1 = 0.0
        self.xd1_1 = 0.0
        self.xd2_1 = 0.0
        self.xd3_1 = 0.0
        self.xd0_2 = 0.0
        self.xd1_2 = 0.0
        self.xd2_2 = 0.0
        self.xd3_2 = 0.0

    def init(self):
        self.x1 = [0.0, 0.0]
        self.x2 = [0.0, 0.0]
        self.output = 0.0

    def update(self, t: float):
        wn = self.wn
        wn2 = wn * wn

        self.x1[1] = self.x2[0]
        self.x2[1] = -wn2 * self.x1[0] - 2 * self.zeta * wn * self.x2[0] + wn2 * self.input

        self.output = self.x1[0]

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


# Template registry for control design blocks
CONTROL_DESIGN_TEMPLATES = {
    "pid_controller": pid_controller_template,
    "pi_controller": pi_controller_template,
    "pd_controller": pd_controller_template,
    "anti_windup_pid": anti_windup_pid_template,
    "lead_lag_compensator": lead_lag_compensator_template,
    "lqr_controller": lqr_controller_template,
    "pole_placement": pole_placement_template,
    "model_reference": model_reference_template,
}
