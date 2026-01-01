"""Python templates for signal processing blocks."""

import math
from ....models import BlockInfo


def rate_limiter_template(block: BlockInfo, class_name: str) -> str:
    """Generate RateLimiter block code."""
    rising_slew = block.parameters.get("risingSlewRate", 1.0)
    falling_slew = block.parameters.get("fallingSlewRate", -1.0)
    sample_time = block.parameters.get("sampleTime", 0.01)

    return f'''
class {class_name}:
    """Rate limiter block: {block.name}"""

    def __init__(self):
        self.rising_slew = {rising_slew}
        self.falling_slew = {falling_slew}
        self.sample_time = {sample_time}
        self.input = 0.0
        self.output = 0.0
        self.prev_output = 0.0
        self.first_step = True

    def init(self):
        self.prev_output = 0.0
        self.output = 0.0
        self.first_step = True

    def update(self, t: float):
        if self.first_step:
            self.output = self.input
            self.first_step = False
        else:
            delta = self.input - self.prev_output
            max_rise = self.rising_slew * self.sample_time
            max_fall = self.falling_slew * self.sample_time

            if delta > max_rise:
                self.output = self.prev_output + max_rise
            elif delta < max_fall:
                self.output = self.prev_output + max_fall
            else:
                self.output = self.input

        self.prev_output = self.output

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def moving_average_template(block: BlockInfo, class_name: str) -> str:
    """Generate MovingAverage block code."""
    window_size = block.parameters.get("windowSize", 10)

    return f'''
class {class_name}:
    """Moving average filter: {block.name}"""

    def __init__(self):
        self.window_size = {window_size}
        self.input = 0.0
        self.output = 0.0
        self.buffer = [0.0] * {window_size}
        self.index = 0
        self.count = 0
        self.sum = 0.0

    def init(self):
        self.buffer = [0.0] * self.window_size
        self.index = 0
        self.count = 0
        self.sum = 0.0
        self.output = 0.0

    def update(self, t: float):
        # Remove old value from sum
        self.sum -= self.buffer[self.index]
        # Add new value
        self.buffer[self.index] = self.input
        self.sum += self.input
        # Update index
        self.index = (self.index + 1) % self.window_size
        if self.count < self.window_size:
            self.count += 1
        # Compute average
        self.output = self.sum / self.count if self.count > 0 else 0.0

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def low_pass_filter_template(block: BlockInfo, class_name: str) -> str:
    """Generate first-order LowPassFilter block code."""
    cutoff_freq = block.parameters.get("cutoffFrequency", 10.0)
    sample_time = block.parameters.get("sampleTime", 0.01)

    return f'''
class {class_name}:
    """First-order low-pass filter: {block.name}"""

    def __init__(self):
        self.cutoff_freq = {cutoff_freq}
        self.sample_time = {sample_time}
        self.input = 0.0
        self.output = 0.0
        # Calculate filter coefficient (alpha)
        tau = 1.0 / (2.0 * math.pi * self.cutoff_freq)
        self.alpha = self.sample_time / (tau + self.sample_time)

    def init(self):
        self.output = 0.0

    def update(self, t: float):
        # y[n] = alpha * x[n] + (1-alpha) * y[n-1]
        self.output = self.alpha * self.input + (1.0 - self.alpha) * self.output

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def high_pass_filter_template(block: BlockInfo, class_name: str) -> str:
    """Generate first-order HighPassFilter block code."""
    cutoff_freq = block.parameters.get("cutoffFrequency", 10.0)
    sample_time = block.parameters.get("sampleTime", 0.01)

    return f'''
class {class_name}:
    """First-order high-pass filter: {block.name}"""

    def __init__(self):
        self.cutoff_freq = {cutoff_freq}
        self.sample_time = {sample_time}
        self.input = 0.0
        self.output = 0.0
        self.prev_input = 0.0
        self.prev_output = 0.0
        # Calculate filter coefficient (alpha)
        tau = 1.0 / (2.0 * math.pi * self.cutoff_freq)
        self.alpha = tau / (tau + self.sample_time)

    def init(self):
        self.output = 0.0
        self.prev_input = 0.0
        self.prev_output = 0.0

    def update(self, t: float):
        # y[n] = alpha * (y[n-1] + x[n] - x[n-1])
        self.output = self.alpha * (self.prev_output + self.input - self.prev_input)
        self.prev_input = self.input
        self.prev_output = self.output

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def band_pass_filter_template(block: BlockInfo, class_name: str) -> str:
    """Generate BandPassFilter block code (cascaded HP + LP)."""
    low_cutoff = block.parameters.get("lowCutoffFrequency", 5.0)
    high_cutoff = block.parameters.get("highCutoffFrequency", 50.0)
    sample_time = block.parameters.get("sampleTime", 0.01)

    return f'''
class {class_name}:
    """Band-pass filter (cascaded HP + LP): {block.name}"""

    def __init__(self):
        self.low_cutoff = {low_cutoff}
        self.high_cutoff = {high_cutoff}
        self.sample_time = {sample_time}
        self.input = 0.0
        self.output = 0.0

        # High-pass coefficients
        tau_hp = 1.0 / (2.0 * math.pi * self.low_cutoff)
        self.alpha_hp = tau_hp / (tau_hp + self.sample_time)
        self.hp_prev_input = 0.0
        self.hp_prev_output = 0.0

        # Low-pass coefficients
        tau_lp = 1.0 / (2.0 * math.pi * self.high_cutoff)
        self.alpha_lp = self.sample_time / (tau_lp + self.sample_time)
        self.lp_output = 0.0

    def init(self):
        self.output = 0.0
        self.hp_prev_input = 0.0
        self.hp_prev_output = 0.0
        self.lp_output = 0.0

    def update(self, t: float):
        # High-pass stage
        hp_out = self.alpha_hp * (self.hp_prev_output + self.input - self.hp_prev_input)
        self.hp_prev_input = self.input
        self.hp_prev_output = hp_out

        # Low-pass stage
        self.lp_output = self.alpha_lp * hp_out + (1.0 - self.alpha_lp) * self.lp_output
        self.output = self.lp_output

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def backlash_template(block: BlockInfo, class_name: str) -> str:
    """Generate Backlash block code."""
    deadband = block.parameters.get("deadband", 1.0)
    initial_output = block.parameters.get("initialOutput", 0.0)

    return f'''
class {class_name}:
    """Backlash block: {block.name}"""

    def __init__(self):
        self.deadband = {deadband}
        self.half_width = self.deadband / 2.0
        self.input = 0.0
        self.output = {initial_output}
        self.prev_output = {initial_output}

    def init(self):
        self.output = {initial_output}
        self.prev_output = {initial_output}

    def update(self, t: float):
        diff = self.input - self.prev_output
        if diff > self.half_width:
            self.output = self.input - self.half_width
        elif diff < -self.half_width:
            self.output = self.input + self.half_width
        else:
            self.output = self.prev_output
        self.prev_output = self.output

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def notch_filter_template(block: BlockInfo, class_name: str) -> str:
    """Generate NotchFilter block code."""
    notch_freq = block.parameters.get("notchFrequency", 60.0)
    bandwidth = block.parameters.get("bandwidth", 10.0)
    sample_time = block.parameters.get("sampleTime", 0.01)

    return f'''
class {class_name}:
    """Notch filter: {block.name}"""

    def __init__(self):
        self.notch_freq = {notch_freq}
        self.bandwidth = {bandwidth}
        self.sample_time = {sample_time}
        self.input = 0.0
        self.output = 0.0

        # Compute notch filter coefficients
        fs = 1.0 / self.sample_time
        omega_0 = 2.0 * math.pi * self.notch_freq / fs
        bw = 2.0 * math.pi * self.bandwidth / fs

        # Pre-warp
        alpha = math.sin(omega_0) * math.sinh(math.log(2.0) / 2.0 * bw * omega_0 / math.sin(omega_0))

        # Coefficients (normalized)
        b0 = 1.0
        b1 = -2.0 * math.cos(omega_0)
        b2 = 1.0
        a0 = 1.0 + alpha
        a1 = -2.0 * math.cos(omega_0)
        a2 = 1.0 - alpha

        self.b = [b0/a0, b1/a0, b2/a0]
        self.a = [1.0, a1/a0, a2/a0]

        # State
        self.x = [0.0, 0.0, 0.0]  # Input history
        self.y = [0.0, 0.0, 0.0]  # Output history

    def init(self):
        self.output = 0.0
        self.x = [0.0, 0.0, 0.0]
        self.y = [0.0, 0.0, 0.0]

    def update(self, t: float):
        # Shift history
        self.x[2] = self.x[1]
        self.x[1] = self.x[0]
        self.x[0] = self.input
        self.y[2] = self.y[1]
        self.y[1] = self.y[0]

        # Compute output
        self.y[0] = (self.b[0] * self.x[0] + self.b[1] * self.x[1] + self.b[2] * self.x[2]
                     - self.a[1] * self.y[1] - self.a[2] * self.y[2])
        self.output = self.y[0]

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


# Template registry for signal processing blocks
SIGNAL_PROCESSING_TEMPLATES = {
    "rate_limiter": rate_limiter_template,
    "moving_average": moving_average_template,
    "low_pass_filter": low_pass_filter_template,
    "high_pass_filter": high_pass_filter_template,
    "band_pass_filter": band_pass_filter_template,
    "backlash": backlash_template,
    "notch_filter": notch_filter_template,
}
