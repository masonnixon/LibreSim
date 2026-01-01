"""Python templates for discrete blocks."""

from ....models import BlockInfo


def unit_delay_template(block: BlockInfo, class_name: str) -> str:
    """Generate UnitDelay block code."""
    initial_condition = block.parameters.get("initialCondition", 0.0)
    sample_time = block.parameters.get("sampleTime", 0.1)

    return f'''
class {class_name}:
    """Unit delay block: {block.name}"""

    def __init__(self):
        self.initial_condition = {initial_condition}
        self.sample_time = {sample_time}
        self.input = 0.0
        self.output = {initial_condition}
        self.prev_value = {initial_condition}
        self.last_sample_time = -float('inf')

    def init(self):
        self.prev_value = self.initial_condition
        self.output = self.initial_condition
        self.last_sample_time = -float('inf')

    def update(self, t: float):
        if t - self.last_sample_time >= self.sample_time - 1e-10:
            self.output = self.prev_value
            self.prev_value = self.input
            self.last_sample_time = t

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def zero_order_hold_template(block: BlockInfo, class_name: str) -> str:
    """Generate ZeroOrderHold block code."""
    sample_time = block.parameters.get("sampleTime", 0.1)

    return f'''
class {class_name}:
    """Zero-order hold block: {block.name}"""

    def __init__(self):
        self.sample_time = {sample_time}
        self.input = 0.0
        self.output = 0.0
        self.held_value = 0.0
        self.last_sample_time = -float('inf')

    def init(self):
        self.held_value = 0.0
        self.output = 0.0
        self.last_sample_time = -float('inf')

    def update(self, t: float):
        if t - self.last_sample_time >= self.sample_time - 1e-10:
            self.held_value = self.input
            self.last_sample_time = t
        self.output = self.held_value

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def first_order_hold_template(block: BlockInfo, class_name: str) -> str:
    """Generate FirstOrderHold block code."""
    sample_time = block.parameters.get("sampleTime", 0.1)

    return f'''
class {class_name}:
    """First-order hold block: {block.name}"""

    def __init__(self):
        self.sample_time = {sample_time}
        self.input = 0.0
        self.output = 0.0
        self.prev_value = 0.0
        self.curr_value = 0.0
        self.last_sample_time = -float('inf')
        self.slope = 0.0

    def init(self):
        self.prev_value = 0.0
        self.curr_value = 0.0
        self.slope = 0.0
        self.output = 0.0
        self.last_sample_time = -float('inf')

    def update(self, t: float):
        if t - self.last_sample_time >= self.sample_time - 1e-10:
            self.prev_value = self.curr_value
            self.curr_value = self.input
            self.slope = (self.curr_value - self.prev_value) / self.sample_time
            self.last_sample_time = t

        # Linear interpolation
        dt = t - self.last_sample_time
        self.output = self.curr_value + self.slope * dt

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def discrete_integrator_template(block: BlockInfo, class_name: str) -> str:
    """Generate DiscreteIntegrator block code."""
    initial_condition = block.parameters.get("initialCondition", 0.0)
    sample_time = block.parameters.get("sampleTime", 0.1)
    method = block.parameters.get("method", "forward")

    return f'''
class {class_name}:
    """Discrete integrator block: {block.name}"""

    def __init__(self):
        self.initial_condition = {initial_condition}
        self.sample_time = {sample_time}
        self.method = "{method}"
        self.input = 0.0
        self.output = {initial_condition}
        self.prev_input = 0.0
        self.state = {initial_condition}
        self.last_sample_time = -float('inf')

    def init(self):
        self.state = self.initial_condition
        self.output = self.initial_condition
        self.prev_input = 0.0
        self.last_sample_time = -float('inf')

    def update(self, t: float):
        if t - self.last_sample_time >= self.sample_time - 1e-10:
            if self.method == "forward":
                self.state += self.sample_time * self.prev_input
            elif self.method == "backward":
                self.state += self.sample_time * self.input
            elif self.method == "trapezoidal":
                self.state += self.sample_time / 2.0 * (self.input + self.prev_input)

            self.prev_input = self.input
            self.last_sample_time = t

        self.output = self.state

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def discrete_derivative_template(block: BlockInfo, class_name: str) -> str:
    """Generate DiscreteDerivative block code."""
    sample_time = block.parameters.get("sampleTime", 0.1)

    return f'''
class {class_name}:
    """Discrete derivative block: {block.name}"""

    def __init__(self):
        self.sample_time = {sample_time}
        self.input = 0.0
        self.output = 0.0
        self.prev_input = 0.0
        self.last_sample_time = -float('inf')

    def init(self):
        self.prev_input = 0.0
        self.output = 0.0
        self.last_sample_time = -float('inf')

    def update(self, t: float):
        if t - self.last_sample_time >= self.sample_time - 1e-10:
            self.output = (self.input - self.prev_input) / self.sample_time
            self.prev_input = self.input
            self.last_sample_time = t

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def discrete_transfer_function_template(block: BlockInfo, class_name: str) -> str:
    """Generate DiscreteTransferFunction block code."""
    numerator = block.parameters.get("numerator", [1.0])
    denominator = block.parameters.get("denominator", [1.0, -0.5])
    sample_time = block.parameters.get("sampleTime", 0.1)

    if not isinstance(numerator, list):
        numerator = [numerator]
    if not isinstance(denominator, list):
        denominator = [denominator]

    order = max(len(numerator), len(denominator)) - 1

    return f'''
class {class_name}:
    """Discrete transfer function block: {block.name}"""

    def __init__(self):
        self.numerator = {numerator}
        self.denominator = {denominator}
        self.sample_time = {sample_time}
        self.order = {order}
        self.input = 0.0
        self.output = 0.0
        self.input_history = [0.0] * {order + 1}
        self.output_history = [0.0] * {order + 1}
        self.last_sample_time = -float('inf')

    def init(self):
        self.input_history = [0.0] * (self.order + 1)
        self.output_history = [0.0] * (self.order + 1)
        self.output = 0.0
        self.last_sample_time = -float('inf')

    def update(self, t: float):
        if t - self.last_sample_time >= self.sample_time - 1e-10:
            # Shift histories
            for i in range(self.order, 0, -1):
                self.input_history[i] = self.input_history[i - 1]
                self.output_history[i] = self.output_history[i - 1]
            self.input_history[0] = self.input

            # Compute new output: sum(b[i]*u[k-i]) - sum(a[i]*y[k-i])
            a0 = self.denominator[0]
            new_output = 0.0

            for i, b in enumerate(self.numerator):
                if i < len(self.input_history):
                    new_output += (b / a0) * self.input_history[i]

            for i in range(1, len(self.denominator)):
                if i < len(self.output_history):
                    new_output -= (self.denominator[i] / a0) * self.output_history[i]

            self.output_history[0] = new_output
            self.output = new_output
            self.last_sample_time = t

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def memory_template(block: BlockInfo, class_name: str) -> str:
    """Generate Memory block code."""
    initial_condition = block.parameters.get("initialCondition", 0.0)

    return f'''
class {class_name}:
    """Memory block: {block.name}"""

    def __init__(self):
        self.initial_condition = {initial_condition}
        self.input = 0.0
        self.output = {initial_condition}
        self.prev_value = {initial_condition}
        self.first_step = True

    def init(self):
        self.prev_value = self.initial_condition
        self.output = self.initial_condition
        self.first_step = True

    def update(self, t: float):
        if self.first_step:
            self.output = self.initial_condition
            self.first_step = False
        else:
            self.output = self.prev_value
        self.prev_value = self.input

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


# Template registry for discrete blocks
DISCRETE_TEMPLATES = {
    "unit_delay": unit_delay_template,
    "zero_order_hold": zero_order_hold_template,
    "first_order_hold": first_order_hold_template,
    "discrete_integrator": discrete_integrator_template,
    "discrete_derivative": discrete_derivative_template,
    "discrete_transfer_function": discrete_transfer_function_template,
    "memory": memory_template,
}
