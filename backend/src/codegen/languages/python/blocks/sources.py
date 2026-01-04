"""Python templates for source blocks."""

import math
from ....models import BlockInfo


def constant_template(block: BlockInfo, class_name: str) -> str:
    """Generate Constant block code."""
    value = block.parameters.get("value", 0.0)
    is_vector = isinstance(value, (list, tuple))

    if is_vector:
        return f'''
class {class_name}:
    """Constant source (vector): {block.name}"""

    def __init__(self):
        self.value = {value}
        self.output = list({value})

    def init(self):
        self.output = list(self.value)

    def update(self, t: float):
        pass  # Constant doesn't change

    def get_output(self, port: int = 0) -> float:
        if isinstance(self.output, (list, tuple)) and port < len(self.output):
            return self.output[port]
        return self.output if not isinstance(self.output, (list, tuple)) else 0.0

    def get_output_vector(self) -> list:
        if isinstance(self.output, (list, tuple)):
            return list(self.output)
        return [self.output]
'''
    else:
        return f'''
class {class_name}:
    """Constant source: {block.name}"""

    def __init__(self):
        self.value = {value}
        self.output = {value}

    def init(self):
        self.output = self.value

    def update(self, t: float):
        pass  # Constant doesn't change

    def get_output(self, port: int = 0) -> float:
        return self.output

    def get_output_vector(self) -> list:
        return [self.output]
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
    """Generate WhiteNoise block code.

    Matches OSK WhiteNoise block exactly:
    - Uses variance parameter (power maps to variance)
    - std_dev = sqrt(variance)
    - Uses Python's random.Random for reproducible sequences
    """
    # Support both 'variance' and 'power' (they map to the same thing)
    variance = block.parameters.get("variance", block.parameters.get("power", 1.0))
    mean = block.parameters.get("mean", 0.0)
    seed = block.parameters.get("seed", None)
    sample_time = block.parameters.get("sampleTime", block.parameters.get("sample_time", 0.0))

    # Format seed for Python code
    seed_str = str(seed) if seed is not None else 'None'

    return f'''
class {class_name}:
    """White noise source: {block.name}

    Matches OSK WhiteNoise block exactly.
    """

    def __init__(self):
        import random
        self.mean = {mean}
        self.variance = {variance}
        self.std_dev = math.sqrt(abs(self.variance))
        self.sample_time = {sample_time}
        self.rng = random.Random({seed_str})
        self.output = 0.0
        self._last_sample_time = -float('inf')

    def init(self):
        # Generate initial noise sample (matches OSK init)
        self.output = self.rng.gauss(self.mean, self.std_dev)
        self._last_sample_time = 0.0

    def update(self, t: float):
        # If sample_time is 0, generate new noise every step
        # Otherwise, only generate new noise at sample intervals
        if self.sample_time <= 0:
            self.output = self.rng.gauss(self.mean, self.std_dev)
        else:
            if t >= self._last_sample_time + self.sample_time:
                self.output = self.rng.gauss(self.mean, self.std_dev)
                self._last_sample_time = t

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def band_limited_white_noise_template(block: BlockInfo, class_name: str) -> str:
    """Generate BandLimitedWhiteNoise block code.

    Matches OSK BandLimitedWhiteNoise block exactly:
    - Uses noise_power and sample_time parameters
    - std_dev = sqrt(noise_power / sample_time)
    """
    noise_power = block.parameters.get("noisePower", block.parameters.get("noise_power", 0.1))
    sample_time = block.parameters.get("sampleTime", block.parameters.get("sample_time", 0.1))
    seed = block.parameters.get("seed", None)

    # Ensure non-zero sample time
    if sample_time <= 0:
        sample_time = 1e-6

    seed_str = str(seed) if seed is not None else 'None'

    return f'''
class {class_name}:
    """Band-limited white noise source: {block.name}

    Matches OSK BandLimitedWhiteNoise block exactly.
    """

    def __init__(self):
        import random
        self.noise_power = {noise_power}
        self.sample_time = max({sample_time}, 1e-6)
        self.rng = random.Random({seed_str})
        self.output = 0.0
        self._last_sample_time = -float('inf')
        # Variance = Noise_Power / Sample_Time
        self._std_dev = math.sqrt(self.noise_power / self.sample_time)

    def init(self):
        self.output = self.rng.gauss(0.0, self._std_dev)
        self._last_sample_time = 0.0

    def update(self, t: float):
        if t >= self._last_sample_time + self.sample_time - 1e-10:
            self.output = self.rng.gauss(0.0, self._std_dev)
            self._last_sample_time = t

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
    "band_limited_white_noise": band_limited_white_noise_template,
    "ground": ground_template,
}
