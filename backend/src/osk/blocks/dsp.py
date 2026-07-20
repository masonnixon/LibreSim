"""DSP (Digital Signal Processing) Toolbox blocks for LibreSim.

These blocks implement DSP functions similar to MATLAB DSP System Toolbox.
"""

import math
from typing import Any

from ..block import Block

# =============================================================================
# FFT/IFFT Operations
# =============================================================================


class FFT(Block):
    """Compute Fast Fourier Transform of input signal.

    Input: Time-domain signal (real or complex vector)
    Output: Frequency-domain representation (complex vector as [re1,im1,re2,im2,...])
    """

    def __init__(self, n_points: int = 64):
        super().__init__()
        self.n_points = n_points
        self.input = [0.0] * n_points
        self.output = [0.0] * (2 * n_points)  # Complex output: [re, im, re, im, ...]
        self.input_block = None

    def init(self):
        self.input = [0.0] * self.n_points
        self.output = [0.0] * (2 * self.n_points)

    def setInput(self, value, port=0):
        if isinstance(value, list):
            self.input = value[: self.n_points] + [0.0] * max(0, self.n_points - len(value))

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            vec = self.input_block.getOutputVector()
            if vec is not None:
                self.input = vec[: self.n_points] + [0.0] * max(0, self.n_points - len(vec))

        # Simple DFT implementation (O(n^2), but works for any size)
        result = []
        N = self.n_points
        for k in range(N):
            real_sum = 0.0
            imag_sum = 0.0
            for n in range(N):
                angle = -2.0 * math.pi * k * n / N
                real_sum += self.input[n] * math.cos(angle)
                imag_sum += self.input[n] * math.sin(angle)
            result.append(real_sum)
            result.append(imag_sum)
        self.output = result

    def getOutput(self, port=0):
        if port < len(self.output):
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


class IFFT(Block):
    """Compute Inverse Fast Fourier Transform.

    Input: Frequency-domain signal (complex vector as [re1,im1,re2,im2,...])
    Output: Time-domain representation
    """

    def __init__(self, n_points: int = 64):
        super().__init__()
        self.n_points = n_points
        self.input = [0.0] * (2 * n_points)
        self.output = [0.0] * n_points
        self.input_block = None

    def init(self):
        self.input = [0.0] * (2 * self.n_points)
        self.output = [0.0] * self.n_points

    def setInput(self, value, port=0):
        if isinstance(value, list):
            expected_len = 2 * self.n_points
            self.input = value[:expected_len] + [0.0] * max(0, expected_len - len(value))

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            vec = self.input_block.getOutputVector()
            if vec is not None:
                expected_len = 2 * self.n_points
                self.input = vec[:expected_len] + [0.0] * max(0, expected_len - len(vec))

        # Inverse DFT
        result = []
        N = self.n_points
        for n in range(N):
            real_sum = 0.0
            for k in range(N):
                angle = 2.0 * math.pi * k * n / N
                re = self.input[2 * k]
                im = self.input[2 * k + 1]
                real_sum += re * math.cos(angle) - im * math.sin(angle)
            result.append(real_sum / N)
        self.output = result

    def getOutput(self, port=0):
        if port < len(self.output):
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


# =============================================================================
# FIR Filter
# =============================================================================


class FIRFilter(Block):
    """Finite Impulse Response (FIR) filter.

    Implements y[n] = sum(b[k] * x[n-k]) for k=0 to M-1
    Input: Signal sample
    Output: Filtered signal sample
    """

    def __init__(self, coefficients: list | None = None):
        super().__init__()
        self.coefficients = coefficients if coefficients else [1.0]
        self.buffer = [0.0] * len(self.coefficients)
        self.output = 0.0
        self.input_block = None

    def init(self):
        self.buffer = [0.0] * len(self.coefficients)
        self.output = 0.0

    def setInput(self, value, port=0):
        # Shift buffer and add new sample
        self.buffer = [float(value)] + self.buffer[:-1]

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            val = self.input_block.getOutput()
            self.buffer = [float(val)] + self.buffer[:-1]

        # Apply FIR filter
        self.output = sum(b * x for b, x in zip(self.coefficients, self.buffer, strict=False))

    def getOutput(self, port=0):
        return self.output


class IIRFilter(Block):
    """Infinite Impulse Response (IIR) filter.

    Implements Direct Form II Transposed:
    y[n] = sum(b[k] * x[n-k]) - sum(a[k] * y[n-k]) for k>=1

    Parameters:
        numerator: B coefficients [b0, b1, b2, ...]
        denominator: A coefficients [a0, a1, a2, ...] (a0 is normalized to 1)
    """

    def __init__(self, numerator: list | None = None, denominator: list | None = None):
        super().__init__()
        self.numerator = numerator if numerator else [1.0]
        self.denominator = denominator if denominator else [1.0]

        # Normalize by a0
        if self.denominator and self.denominator[0] != 0:
            a0 = self.denominator[0]
            self.numerator = [b / a0 for b in self.numerator]
            self.denominator = [a / a0 for a in self.denominator]

        order = max(len(self.numerator), len(self.denominator))
        self.x_buffer = [0.0] * order
        self.y_buffer = [0.0] * order
        self.output = 0.0
        self.input_block = None

    def init(self):
        order = max(len(self.numerator), len(self.denominator))
        self.x_buffer = [0.0] * order
        self.y_buffer = [0.0] * order
        self.output = 0.0

    def setInput(self, value, port=0):
        self.x_buffer = [float(value)] + self.x_buffer[:-1]

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            val = self.input_block.getOutput()
            self.x_buffer = [float(val)] + self.x_buffer[:-1]

        # Apply IIR filter: y = sum(b*x) - sum(a*y) for a indices >= 1
        y = 0.0
        for i, b in enumerate(self.numerator):
            y += b * self.x_buffer[i]

        for i in range(1, len(self.denominator)):
            y -= self.denominator[i] * self.y_buffer[i - 1]

        self.output = y
        self.y_buffer = [y] + self.y_buffer[:-1]

    def getOutput(self, port=0):
        return self.output


# =============================================================================
# Convolution
# =============================================================================


class Convolution(Block):
    """Discrete convolution of two signals.

    Computes y = x * h (convolution)
    """

    def __init__(self):
        super().__init__()
        self.signal = []
        self.kernel = []
        self.output = []
        self.input_blocks = [None, None]

    def init(self):
        self.signal = []
        self.kernel = []
        self.output = []

    def setInput(self, value, port=0):
        if isinstance(value, list):
            if port == 0:
                self.signal = value
            else:
                self.kernel = value

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block

    def update(self):
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                vec = block.getOutputVector()
                if vec is not None:
                    if i == 0:
                        self.signal = vec
                    else:
                        self.kernel = vec

        if not self.signal or not self.kernel:
            self.output = []
            return

        # Full convolution
        n = len(self.signal)
        m = len(self.kernel)
        result = [0.0] * (n + m - 1)

        for i in range(n):
            for j in range(m):
                result[i + j] += self.signal[i] * self.kernel[j]

        self.output = result

    def getOutput(self, port=0):
        if port < len(self.output):
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


# =============================================================================
# Sample Rate Conversion
# =============================================================================


class Downsampler(Block):
    """Downsample signal by integer factor.

    Keeps every N-th sample and discards the rest.
    """

    def __init__(self, factor: int = 2):
        super().__init__()
        self.factor = max(1, factor)
        self.sample_count = 0
        self.output = 0.0
        self.input_block = None

    def init(self):
        self.sample_count = 0
        self.output = 0.0

    def setInput(self, value, port=0):
        if self.sample_count % self.factor == 0:
            self.output = float(value)
        self.sample_count += 1

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            val = self.input_block.getOutput()
            if self.sample_count % self.factor == 0:
                self.output = float(val)
            self.sample_count += 1

    def getOutput(self, port=0):
        return self.output


class Upsampler(Block):
    """Upsample signal by integer factor.

    Inserts N-1 zeros between each sample (no interpolation).
    """

    def __init__(self, factor: int = 2):
        super().__init__()
        self.factor = max(1, factor)
        self.phase = 0
        self.current_sample = 0.0
        self.output = 0.0
        self.input_block = None

    def init(self):
        self.phase = 0
        self.current_sample = 0.0
        self.output = 0.0

    def setInput(self, value, port=0):
        if self.phase == 0:
            self.current_sample = float(value)
            self.output = self.current_sample
        else:
            self.output = 0.0

        self.phase = (self.phase + 1) % self.factor

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            if self.phase == 0:
                self.current_sample = self.input_block.getOutput()
                self.output = self.current_sample
            else:
                self.output = 0.0

            self.phase = (self.phase + 1) % self.factor

    def getOutput(self, port=0):
        return self.output


class Interpolator(Block):
    """Interpolate signal by integer factor using linear interpolation.

    Upsamples and interpolates between samples.
    """

    def __init__(self, factor: int = 2):
        super().__init__()
        self.factor = max(1, factor)
        self.prev_sample = 0.0
        self.curr_sample = 0.0
        self.phase = 0
        self.output = 0.0
        self.input_block = None

    def init(self):
        self.prev_sample = 0.0
        self.curr_sample = 0.0
        self.phase = 0
        self.output = 0.0

    def setInput(self, value, port=0):
        if self.phase == 0:
            self.prev_sample = self.curr_sample
            self.curr_sample = float(value)

        # Linear interpolation
        alpha = self.phase / self.factor
        self.output = self.prev_sample + alpha * (self.curr_sample - self.prev_sample)
        self.phase = (self.phase + 1) % self.factor

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            if self.phase == 0:
                self.prev_sample = self.curr_sample
                self.curr_sample = self.input_block.getOutput()

            alpha = self.phase / self.factor
            self.output = self.prev_sample + alpha * (self.curr_sample - self.prev_sample)
            self.phase = (self.phase + 1) % self.factor

    def getOutput(self, port=0):
        return self.output


# =============================================================================
# Window Functions
# =============================================================================


class WindowFunction(Block):
    """Apply a window function to input signal.

    Supported windows: hamming, hanning, blackman, rectangular, kaiser
    """

    def __init__(self, window_type: str = "hamming", length: int = 64, beta: float = 5.0):
        super().__init__()
        self.window_type = window_type.lower()
        self.length = length
        self.beta = beta  # For Kaiser window
        self.window = self._generate_window()
        self.input = [0.0] * length
        self.output = [0.0] * length
        self.input_block = None

    def _generate_window(self) -> list:
        """Generate window coefficients."""
        N = self.length
        window = []

        for n in range(N):
            if self.window_type == "rectangular":
                w = 1.0
            elif self.window_type == "hanning":
                w = 0.5 * (1 - math.cos(2 * math.pi * n / (N - 1)))
            elif self.window_type == "hamming":
                w = 0.54 - 0.46 * math.cos(2 * math.pi * n / (N - 1))
            elif self.window_type == "blackman":
                w = (
                    0.42
                    - 0.5 * math.cos(2 * math.pi * n / (N - 1))
                    + 0.08 * math.cos(4 * math.pi * n / (N - 1))
                )
            elif self.window_type == "kaiser":
                # Simplified Kaiser window (uses approximation for Bessel function)
                alpha = (N - 1) / 2
                ratio = (n - alpha) / alpha
                # n is in [0, N - 1], so ratio is always in [-1, 1].
                w = self._bessel_i0(self.beta * math.sqrt(1 - ratio * ratio)) / self._bessel_i0(
                    self.beta
                )
            else:
                w = 1.0  # Default to rectangular

            window.append(w)

        return window

    def _bessel_i0(self, x: float) -> float:
        """Approximate modified Bessel function of first kind, order 0."""
        sum_val = 1.0
        term = 1.0
        for k in range(1, 25):
            term *= (x / (2 * k)) ** 2
            sum_val += term
            if term < 1e-12:
                break
        return sum_val

    def init(self):
        self.input = [0.0] * self.length
        self.output = [0.0] * self.length

    def setInput(self, value, port=0):
        if isinstance(value, list):
            self.input = value[: self.length] + [0.0] * max(0, self.length - len(value))

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            vec = self.input_block.getOutputVector()
            if vec is not None:
                self.input = vec[: self.length] + [0.0] * max(0, self.length - len(vec))

        # Apply window
        self.output = [x * w for x, w in zip(self.input, self.window, strict=False)]

    def getOutput(self, port=0):
        if port < len(self.output):
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


# =============================================================================
# Signal Statistics
# =============================================================================


class Mean(Block):
    """Compute running mean of input signal over a window."""

    def __init__(self, window_size: int = 10):
        super().__init__()
        self.window_size = max(1, window_size)
        self.buffer: list[float] = []
        self.output = 0.0
        self.input_block: Any = None

    def init(self) -> None:
        self.buffer = []
        self.output = 0.0

    def setInput(self, value: Any, port: int = 0) -> None:
        self.buffer.append(float(value))
        if len(self.buffer) > self.window_size:
            self.buffer.pop(0)

    def connectInput(self, block: Any, port: int = 0, source_port: int = 0) -> None:
        self.input_block = block

    def update(self) -> None:
        if self.input_block is not None:
            self.buffer.append(self.input_block.getOutput())
            if len(self.buffer) > self.window_size:
                self.buffer.pop(0)

        if self.buffer:
            self.output = sum(self.buffer) / len(self.buffer)
        else:
            self.output = 0.0

    def getOutput(self, port: int = 0) -> float:
        return self.output


class Variance(Block):
    """Compute running variance of input signal over a window."""

    def __init__(self, window_size: int = 10):
        super().__init__()
        self.window_size = max(1, window_size)
        self.buffer: list[float] = []
        self.output = 0.0
        self.input_block: Any = None

    def init(self) -> None:
        self.buffer = []
        self.output = 0.0

    def setInput(self, value: Any, port: int = 0) -> None:
        self.buffer.append(float(value))
        if len(self.buffer) > self.window_size:
            self.buffer.pop(0)

    def connectInput(self, block: Any, port: int = 0, source_port: int = 0) -> None:
        self.input_block = block

    def update(self) -> None:
        if self.input_block is not None:
            self.buffer.append(self.input_block.getOutput())
            if len(self.buffer) > self.window_size:
                self.buffer.pop(0)

        if len(self.buffer) > 1:
            mean = sum(self.buffer) / len(self.buffer)
            self.output = sum((x - mean) ** 2 for x in self.buffer) / (len(self.buffer) - 1)
        else:
            self.output = 0.0

    def getOutput(self, port: int = 0) -> float:
        return self.output


class RMS(Block):
    """Compute running RMS (root mean square) of input signal over a window."""

    def __init__(self, window_size: int = 10):
        super().__init__()
        self.window_size = max(1, window_size)
        self.buffer: list[float] = []
        self.output = 0.0
        self.input_block: Any = None

    def init(self) -> None:
        self.buffer = []
        self.output = 0.0

    def setInput(self, value, port=0):
        self.buffer.append(float(value))
        if len(self.buffer) > self.window_size:
            self.buffer.pop(0)

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.buffer.append(self.input_block.getOutput())
            if len(self.buffer) > self.window_size:
                self.buffer.pop(0)

        if self.buffer:
            mean_sq = sum(x * x for x in self.buffer) / len(self.buffer)
            self.output = math.sqrt(mean_sq)
        else:
            self.output = 0.0

    def getOutput(self, port=0):
        return self.output


class PeakDetector(Block):
    """Detect peaks in the input signal.

    Outputs 1 when current sample is a local maximum, 0 otherwise.
    """

    def __init__(self, threshold: float = 0.0):
        super().__init__()
        self.threshold = threshold
        self.prev_prev = 0.0
        self.prev = 0.0
        self.current = 0.0
        self.output = 0.0
        self.input_block = None

    def init(self):
        self.prev_prev = 0.0
        self.prev = 0.0
        self.current = 0.0
        self.output = 0.0

    def setInput(self, value, port=0):
        self.prev_prev = self.prev
        self.prev = self.current
        self.current = float(value)

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.prev_prev = self.prev
            self.prev = self.current
            self.current = self.input_block.getOutput()

        # Check if prev is a peak
        if self.prev > self.prev_prev and self.prev > self.current and self.prev > self.threshold:
            self.output = 1.0
        else:
            self.output = 0.0

    def getOutput(self, port=0):
        return self.output


class ZeroCrossingDetector(Block):
    """Detect zero crossings in the input signal.

    Outputs 1 when signal crosses zero, 0 otherwise.
    Parameters:
        direction: 'rising', 'falling', or 'both'
    """

    def __init__(self, direction: str = "both"):
        super().__init__()
        self.direction = direction.lower()
        self.prev = 0.0
        self.current = 0.0
        self.output = 0.0
        self.input_block = None

    def init(self):
        self.prev = 0.0
        self.current = 0.0
        self.output = 0.0

    def setInput(self, value, port=0):
        self.prev = self.current
        self.current = float(value)

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.prev = self.current
            self.current = self.input_block.getOutput()

        is_crossing = False
        if self.direction == "rising":
            is_crossing = self.prev <= 0 < self.current
        elif self.direction == "falling":
            is_crossing = self.prev >= 0 > self.current
        else:  # both
            is_crossing = (self.prev <= 0 < self.current) or (self.prev >= 0 > self.current)

        self.output = 1.0 if is_crossing else 0.0

    def getOutput(self, port=0):
        return self.output
