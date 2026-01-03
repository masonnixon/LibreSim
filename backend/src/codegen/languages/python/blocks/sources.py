"""Python templates for source blocks."""

import math
from ....models import BlockInfo


def constant_template(block: BlockInfo, class_name: str) -> str:
    """Generate Constant block code."""
    value = block.parameters.get("value", 0.0)
    return f'''
class {class_name}:
    """Constant source: {block.name}"""

    def __init__(self):
        self.value = {value}
        self.output = {value}

    def init(self):
        self.output = self.value

    def update(self, t: float):
        self.output = self.value

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def step_template(block: BlockInfo, class_name: str) -> str:
    """Generate Step block code."""
    # Support both camelCase (frontend) and snake_case (backend) parameter names
    step_time = block.parameters.get("step_time", block.parameters.get("stepTime", 1.0))
    initial_value = block.parameters.get("initial_value", block.parameters.get("initialValue", 0.0))
    final_value = block.parameters.get("final_value", block.parameters.get("finalValue", 1.0))
    return f'''
class {class_name}:
    """Step source: {block.name}"""

    def __init__(self):
        self.step_time = {step_time}
        self.initial_value = {initial_value}
        self.final_value = {final_value}
        self.output = {initial_value}

    def init(self):
        self.output = self.initial_value

    def update(self, t: float):
        if t >= self.step_time:
            self.output = self.final_value
        else:
            self.output = self.initial_value

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def ramp_template(block: BlockInfo, class_name: str) -> str:
    """Generate Ramp block code."""
    slope = block.parameters.get("slope", 1.0)
    start_time = block.parameters.get("startTime", 0.0)
    initial_output = block.parameters.get("initialOutput", 0.0)
    return f'''
class {class_name}:
    """Ramp source: {block.name}"""

    def __init__(self):
        self.slope = {slope}
        self.start_time = {start_time}
        self.initial_output = {initial_output}
        self.output = {initial_output}

    def init(self):
        self.output = self.initial_output

    def update(self, t: float):
        if t >= self.start_time:
            self.output = self.initial_output + self.slope * (t - self.start_time)
        else:
            self.output = self.initial_output

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def sine_wave_template(block: BlockInfo, class_name: str) -> str:
    """Generate SineWave block code."""
    amplitude = block.parameters.get("amplitude", 1.0)
    frequency = block.parameters.get("frequency", 1.0)
    phase = block.parameters.get("phase", 0.0)
    bias = block.parameters.get("bias", 0.0)
    return f'''
class {class_name}:
    """Sine wave source: {block.name}"""

    def __init__(self):
        self.amplitude = {amplitude}
        self.frequency = {frequency}
        self.phase = {phase}
        self.bias = {bias}
        self.output = 0.0

    def init(self):
        self.output = self.amplitude * math.sin(self.phase) + self.bias

    def update(self, t: float):
        self.output = self.amplitude * math.sin(
            2.0 * math.pi * self.frequency * t + self.phase
        ) + self.bias

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def pulse_template(block: BlockInfo, class_name: str) -> str:
    """Generate Pulse block code."""
    amplitude = block.parameters.get("amplitude", 1.0)
    period = block.parameters.get("period", 1.0)
    pulse_width = block.parameters.get("pulseWidth", 50.0)  # Percentage
    phase_delay = block.parameters.get("phaseDelay", 0.0)
    return f'''
class {class_name}:
    """Pulse source: {block.name}"""

    def __init__(self):
        self.amplitude = {amplitude}
        self.period = {period}
        self.pulse_width = {pulse_width} / 100.0  # Convert percentage to fraction
        self.phase_delay = {phase_delay}
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def update(self, t: float):
        if t < self.phase_delay:
            self.output = 0.0
        else:
            t_shifted = t - self.phase_delay
            t_in_period = t_shifted % self.period
            if t_in_period < self.period * self.pulse_width:
                self.output = self.amplitude
            else:
                self.output = 0.0

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def clock_template(block: BlockInfo, class_name: str) -> str:
    """Generate Clock block code."""
    return f'''
class {class_name}:
    """Clock source: {block.name}"""

    def __init__(self):
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def update(self, t: float):
        self.output = t

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def white_noise_template(block: BlockInfo, class_name: str) -> str:
    """Generate WhiteNoise block code."""
    power = block.parameters.get("power", 1.0)
    sample_time = block.parameters.get("sampleTime", block.parameters.get("sample_time", 0.1))
    # Avoid division by zero - use reasonable default if sample_time is 0
    if sample_time <= 0:
        sample_time = 0.01  # Default to 100Hz sampling
    seed = block.parameters.get("seed", 0)
    return f'''
class {class_name}:
    """White noise source: {block.name}"""

    def __init__(self):
        import random
        self.power = {power}
        self.sample_time = {sample_time}
        self.rng = random.Random({seed if seed else 'None'})
        self.output = 0.0
        self.last_sample_time = -float('inf')
        self.std_dev = math.sqrt(self.power / self.sample_time)

    def init(self):
        self.output = 0.0
        self.last_sample_time = -float('inf')

    def update(self, t: float):
        if t - self.last_sample_time >= self.sample_time - 1e-10:
            self.output = self.rng.gauss(0.0, self.std_dev)
            self.last_sample_time = t

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def ground_template(block: BlockInfo, class_name: str) -> str:
    """Generate Ground block code."""
    return f'''
class {class_name}:
    """Ground (zero) source: {block.name}"""

    def __init__(self):
        self.output = 0.0

    def init(self):
        pass

    def update(self, t: float):
        pass

    def get_output(self, port: int = 0) -> float:
        return 0.0
'''


# Template registry for source blocks
SOURCE_TEMPLATES = {
    "constant": constant_template,
    "step": step_template,
    "ramp": ramp_template,
    "sine_wave": sine_wave_template,
    "pulse": pulse_template,
    "clock": clock_template,
    "white_noise": white_noise_template,
    "ground": ground_template,
}
