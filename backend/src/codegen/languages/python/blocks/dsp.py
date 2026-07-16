"""Python templates for DSP (Digital Signal Processing) blocks."""

from ....dsp_utils import window_coefficients
from ....models import BlockInfo


def fft_template(block: BlockInfo, class_name: str) -> str:
    """Generate a real-input DFT with OSK-compatible interleaved output."""
    n_points = block.parameters.get("nPoints", block.parameters.get("n_points", 64))
    return f'''
class {class_name}:
    """Real-input DFT block: {block.name}"""

    def __init__(self):
        self.input = [0.0] * {n_points}
        self.output = [0.0] * {2 * n_points}

    def init(self):
        self.input = [0.0] * {n_points}
        self.output = [0.0] * {2 * n_points}

    def update(self, t: float):
        result = []
        for k in range({n_points}):
            real_sum = 0.0
            imag_sum = 0.0
            for n in range({n_points}):
                angle = -2.0 * math.pi * k * n / {n_points}
                real_sum += self.input[n] * math.cos(angle)
                imag_sum += self.input[n] * math.sin(angle)
            result.append(real_sum)
            result.append(imag_sum)
        self.output = result

    def get_output(self, port: int = 0) -> float:
        return self.output[port] if 0 <= port < len(self.output) else 0.0

    def get_output_vector(self) -> list:
        return list(self.output)
'''


def window_function_template(block: BlockInfo, class_name: str) -> str:
    """Generate a frame window with coefficients identical to the OSK."""
    window_type = block.parameters.get("windowType", block.parameters.get("window_type", "hamming"))
    length = block.parameters.get("length", 64)
    beta = block.parameters.get("beta", 5.0)
    coefficients = window_coefficients(str(window_type), int(length), float(beta))
    return f'''
class {class_name}:
    """{window_type} window block: {block.name}"""

    def __init__(self):
        self.window = {coefficients!r}
        self.input = [0.0] * {length}
        self.output = [0.0] * {length}

    def init(self):
        self.input = [0.0] * {length}
        self.output = [0.0] * {length}

    def update(self, t: float):
        self.output = [value * weight for value, weight in zip(self.input, self.window)]

    def get_output(self, port: int = 0) -> float:
        return self.output[port] if 0 <= port < len(self.output) else 0.0

    def get_output_vector(self) -> list:
        return list(self.output)
'''


def fir_filter_template(block: BlockInfo, class_name: str) -> str:
    """Generate FIR filter block code."""
    coefficients = block.parameters.get("coefficients", [1.0])
    if not isinstance(coefficients, list):
        coefficients = [coefficients]

    return f'''
class {class_name}:
    """FIR filter block: {block.name}

    Implements y[n] = sum(b[k] * x[n-k]) for k=0 to M-1
    """

    def __init__(self):
        self.coefficients = {coefficients}
        self.buffer = [0.0] * len(self.coefficients)
        self.input = 0.0
        self.output = 0.0

    def init(self):
        self.buffer = [0.0] * len(self.coefficients)
        self.output = 0.0

    def update(self, t: float):
        # Shift buffer and add new sample
        self.buffer = [float(self.input)] + self.buffer[:-1]
        # Apply FIR filter
        self.output = sum(b * x for b, x in zip(self.coefficients, self.buffer))

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def iir_filter_template(block: BlockInfo, class_name: str) -> str:
    """Generate IIR filter block code."""
    numerator = block.parameters.get("numerator", [1.0])
    denominator = block.parameters.get("denominator", [1.0])
    if not isinstance(numerator, list):
        numerator = [numerator]
    if not isinstance(denominator, list):
        denominator = [denominator]

    order = max(len(numerator), len(denominator))

    return f'''
class {class_name}:
    """IIR filter block: {block.name}

    Implements Direct Form II Transposed IIR filter.
    """

    def __init__(self):
        self.numerator = {numerator}
        self.denominator = {denominator}
        self.order = {order}
        self.x_buffer = [0.0] * self.order
        self.y_buffer = [0.0] * self.order
        self.input = 0.0
        self.output = 0.0

        # Normalize by a0
        if self.denominator and self.denominator[0] != 0:
            a0 = self.denominator[0]
            self.numerator = [b / a0 for b in self.numerator]
            self.denominator = [a / a0 for a in self.denominator]

    def init(self):
        self.x_buffer = [0.0] * self.order
        self.y_buffer = [0.0] * self.order
        self.output = 0.0

    def update(self, t: float):
        # Shift input buffer
        self.x_buffer = [float(self.input)] + self.x_buffer[:-1]

        # Apply IIR filter: y = sum(b*x) - sum(a*y) for a indices >= 1
        y = 0.0
        for i, b in enumerate(self.numerator):
            if i < len(self.x_buffer):
                y += b * self.x_buffer[i]

        for i in range(1, len(self.denominator)):
            if i <= len(self.y_buffer):
                y -= self.denominator[i] * self.y_buffer[i - 1]

        self.output = y
        self.y_buffer = [y] + self.y_buffer[:-1]

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def mean_template(block: BlockInfo, class_name: str) -> str:
    """Generate Mean (running average) block code."""
    window_size = block.parameters.get("windowSize", block.parameters.get("window_size", 10))

    return f'''
class {class_name}:
    """Running mean block: {block.name}

    Computes running mean over a sliding window.
    """

    def __init__(self):
        self.window_size = {window_size}
        self.buffer = []
        self.input = 0.0
        self.output = 0.0

    def init(self):
        self.buffer = []
        self.output = 0.0

    def update(self, t: float):
        # Add new sample to buffer
        self.buffer.append(float(self.input))
        if len(self.buffer) > self.window_size:
            self.buffer.pop(0)

        # Compute mean
        if self.buffer:
            self.output = sum(self.buffer) / len(self.buffer)
        else:
            self.output = 0.0

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def variance_template(block: BlockInfo, class_name: str) -> str:
    """Generate Variance block code."""
    window_size = block.parameters.get("windowSize", block.parameters.get("window_size", 10))

    return f'''
class {class_name}:
    """Running variance block: {block.name}

    Computes running variance over a sliding window.
    """

    def __init__(self):
        self.window_size = {window_size}
        self.buffer = []
        self.input = 0.0
        self.output = 0.0

    def init(self):
        self.buffer = []
        self.output = 0.0

    def update(self, t: float):
        # Add new sample to buffer
        self.buffer.append(float(self.input))
        if len(self.buffer) > self.window_size:
            self.buffer.pop(0)

        # Compute variance
        if len(self.buffer) > 1:
            mean = sum(self.buffer) / len(self.buffer)
            self.output = sum((x - mean) ** 2 for x in self.buffer) / (len(self.buffer) - 1)
        else:
            self.output = 0.0

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def rms_template(block: BlockInfo, class_name: str) -> str:
    """Generate RMS (root mean square) block code."""
    window_size = block.parameters.get("windowSize", block.parameters.get("window_size", 10))

    return f'''
import math

class {class_name}:
    """Running RMS block: {block.name}

    Computes running RMS (root mean square) over a sliding window.
    """

    def __init__(self):
        self.window_size = {window_size}
        self.buffer = []
        self.input = 0.0
        self.output = 0.0

    def init(self):
        self.buffer = []
        self.output = 0.0

    def update(self, t: float):
        # Add new sample to buffer
        self.buffer.append(float(self.input))
        if len(self.buffer) > self.window_size:
            self.buffer.pop(0)

        # Compute RMS
        if self.buffer:
            mean_sq = sum(x * x for x in self.buffer) / len(self.buffer)
            self.output = math.sqrt(mean_sq)
        else:
            self.output = 0.0

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def downsampler_template(block: BlockInfo, class_name: str) -> str:
    """Generate Downsampler block code."""
    factor = block.parameters.get("factor", 2)

    return f'''
class {class_name}:
    """Downsampler block: {block.name}

    Keeps every N-th sample.
    """

    def __init__(self):
        self.factor = {factor}
        self.sample_count = 0
        self.input = 0.0
        self.output = 0.0

    def init(self):
        self.sample_count = 0
        self.output = 0.0

    def update(self, t: float):
        if self.sample_count % self.factor == 0:
            self.output = float(self.input)
        self.sample_count += 1

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def upsampler_template(block: BlockInfo, class_name: str) -> str:
    """Generate Upsampler block code."""
    factor = block.parameters.get("factor", 2)

    return f'''
class {class_name}:
    """Upsampler block: {block.name}

    Inserts zeros between samples.
    """

    def __init__(self):
        self.factor = {factor}
        self.phase = 0
        self.current_sample = 0.0
        self.input = 0.0
        self.output = 0.0

    def init(self):
        self.phase = 0
        self.current_sample = 0.0
        self.output = 0.0

    def update(self, t: float):
        if self.phase == 0:
            self.current_sample = float(self.input)
            self.output = self.current_sample
        else:
            self.output = 0.0
        self.phase = (self.phase + 1) % self.factor

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def peak_detector_template(block: BlockInfo, class_name: str) -> str:
    """Generate Peak Detector block code."""
    threshold = block.parameters.get("threshold", 0.0)

    return f'''
class {class_name}:
    """Peak detector block: {block.name}

    Outputs 1 when input is a local maximum.
    """

    def __init__(self):
        self.threshold = {threshold}
        self.prev_prev = 0.0
        self.prev = 0.0
        self.current = 0.0
        self.input = 0.0
        self.output = 0.0

    def init(self):
        self.prev_prev = 0.0
        self.prev = 0.0
        self.current = 0.0
        self.output = 0.0

    def update(self, t: float):
        self.prev_prev = self.prev
        self.prev = self.current
        self.current = float(self.input)

        # Check if prev is a peak
        if self.prev > self.prev_prev and self.prev > self.current and self.prev > self.threshold:
            self.output = 1.0
        else:
            self.output = 0.0

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def zero_crossing_detector_template(block: BlockInfo, class_name: str) -> str:
    """Generate Zero Crossing Detector block code."""
    direction = block.parameters.get("direction", "both")

    return f'''
class {class_name}:
    """Zero crossing detector block: {block.name}

    Outputs 1 when signal crosses zero.
    """

    def __init__(self):
        self.direction = "{direction}"
        self.prev = 0.0
        self.current = 0.0
        self.input = 0.0
        self.output = 0.0

    def init(self):
        self.prev = 0.0
        self.current = 0.0
        self.output = 0.0

    def update(self, t: float):
        self.prev = self.current
        self.current = float(self.input)

        is_crossing = False
        if self.direction == "rising":
            is_crossing = self.prev <= 0 < self.current
        elif self.direction == "falling":
            is_crossing = self.prev >= 0 > self.current
        else:  # both
            is_crossing = (self.prev <= 0 < self.current) or (self.prev >= 0 > self.current)

        self.output = 1.0 if is_crossing else 0.0

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


# Template registry for DSP blocks
DSP_TEMPLATES = {
    "fft": fft_template,
    "window_function": window_function_template,
    "fir_filter": fir_filter_template,
    "iir_filter": iir_filter_template,
    "mean": mean_template,
    "variance": variance_template,
    "rms": rms_template,
    "downsampler": downsampler_template,
    "upsampler": upsampler_template,
    "peak_detector": peak_detector_template,
    "zero_crossing_detector": zero_crossing_detector_template,
}
