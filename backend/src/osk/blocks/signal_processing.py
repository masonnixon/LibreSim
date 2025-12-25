"""Signal processing blocks for OSK-based simulation.

Provides filtering and signal conditioning blocks commonly used in
control systems and signal processing applications.
"""

import math
from collections import deque
from typing import Literal

from ..block import Block
from ..state import State


# Filter design types
FilterDesign = Literal["butterworth", "chebyshev1", "chebyshev2", "bessel"]
FilterResponse = Literal["lowpass", "highpass", "bandpass", "bandstop"]


class RateLimiter(Block):
    """Rate Limiter block - limits the rate of change of a signal.

    Useful for modeling actuator rate limits or preventing sudden
    changes that could damage physical systems.
    """

    def __init__(self, rising_rate=1.0, falling_rate=-1.0):
        super().__init__()
        self.rising_rate = abs(rising_rate)  # Max rate of increase per second
        self.falling_rate = -abs(falling_rate) if falling_rate < 0 else -abs(rising_rate)  # Max rate of decrease
        self.input = 0.0
        self.output = 0.0
        self.input_block = None
        self.prev_output = 0.0

    def init(self):
        self.output = 0.0
        self.prev_output = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput()

        # Calculate desired change
        desired_change = self.input - self.prev_output
        max_rise = self.rising_rate * State.dt
        max_fall = self.falling_rate * State.dt

        # Limit the rate of change
        if desired_change > max_rise:
            self.output = self.prev_output + max_rise
        elif desired_change < max_fall:
            self.output = self.prev_output + max_fall
        else:
            self.output = self.input

        self.prev_output = self.output

    def getOutput(self, port=0):
        return self.output


class MovingAverage(Block):
    """Moving Average filter block.

    Smooths a signal by averaging the last N samples.
    Useful for noise reduction in measurements.
    """

    def __init__(self, window_size=10):
        super().__init__()
        self.window_size = max(1, int(window_size))
        self.input = 0.0
        self.output = 0.0
        self.input_block = None
        self.buffer = deque(maxlen=self.window_size)

    def init(self):
        self.output = 0.0
        self.buffer = deque(maxlen=self.window_size)

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput()

        self.buffer.append(self.input)
        self.output = sum(self.buffer) / len(self.buffer)

    def getOutput(self, port=0):
        return self.output


class LowPassFilter(Block):
    """First-order Low Pass Filter (exponential moving average).

    Attenuates high-frequency components of a signal.
    The cutoff frequency determines how aggressively high frequencies are filtered.
    """

    def __init__(self, cutoff_freq=1.0):
        super().__init__()
        self.cutoff_freq = cutoff_freq  # Cutoff frequency in Hz
        self.input = 0.0
        self.output = 0.0
        self.input_block = None
        self.alpha = 0.0

    def init(self):
        self.output = 0.0
        # Calculate filter coefficient from cutoff frequency
        # alpha = dt / (RC + dt) where RC = 1 / (2*pi*fc)
        if State.dt > 0 and self.cutoff_freq > 0:
            rc = 1.0 / (2.0 * math.pi * self.cutoff_freq)
            self.alpha = State.dt / (rc + State.dt)
        else:
            self.alpha = 1.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput()

        # Recalculate alpha in case dt changed
        if State.dt > 0 and self.cutoff_freq > 0:
            rc = 1.0 / (2.0 * math.pi * self.cutoff_freq)
            self.alpha = State.dt / (rc + State.dt)

        # First-order IIR filter: y[n] = alpha * x[n] + (1-alpha) * y[n-1]
        self.output = self.alpha * self.input + (1.0 - self.alpha) * self.output

    def getOutput(self, port=0):
        return self.output


class HighPassFilter(Block):
    """First-order High Pass Filter.

    Attenuates low-frequency components and DC offset of a signal.
    Useful for removing drift or bias from measurements.
    """

    def __init__(self, cutoff_freq=1.0):
        super().__init__()
        self.cutoff_freq = cutoff_freq
        self.input = 0.0
        self.output = 0.0
        self.input_block = None
        self.prev_input = 0.0
        self.prev_output = 0.0
        self.alpha = 0.0

    def init(self):
        self.output = 0.0
        self.prev_input = 0.0
        self.prev_output = 0.0
        if State.dt > 0 and self.cutoff_freq > 0:
            rc = 1.0 / (2.0 * math.pi * self.cutoff_freq)
            self.alpha = rc / (rc + State.dt)
        else:
            self.alpha = 1.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput()

        if State.dt > 0 and self.cutoff_freq > 0:
            rc = 1.0 / (2.0 * math.pi * self.cutoff_freq)
            self.alpha = rc / (rc + State.dt)

        # High pass: y[n] = alpha * (y[n-1] + x[n] - x[n-1])
        self.output = self.alpha * (self.prev_output + self.input - self.prev_input)

        self.prev_input = self.input
        self.prev_output = self.output

    def getOutput(self, port=0):
        return self.output


class BandPassFilter(Block):
    """Band Pass Filter - combines low pass and high pass.

    Passes frequencies within a specified band and attenuates
    frequencies outside that band.
    """

    def __init__(self, low_cutoff=0.1, high_cutoff=10.0):
        super().__init__()
        self.low_cutoff = low_cutoff  # Lower cutoff (high pass)
        self.high_cutoff = high_cutoff  # Upper cutoff (low pass)
        self.input = 0.0
        self.output = 0.0
        self.input_block = None
        # Internal filter states
        self.hp_prev_input = 0.0
        self.hp_prev_output = 0.0
        self.lp_output = 0.0

    def init(self):
        self.output = 0.0
        self.hp_prev_input = 0.0
        self.hp_prev_output = 0.0
        self.lp_output = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput()

        # High pass filter first
        if State.dt > 0 and self.low_cutoff > 0:
            rc_hp = 1.0 / (2.0 * math.pi * self.low_cutoff)
            alpha_hp = rc_hp / (rc_hp + State.dt)
            hp_output = alpha_hp * (self.hp_prev_output + self.input - self.hp_prev_input)
        else:
            hp_output = self.input

        self.hp_prev_input = self.input
        self.hp_prev_output = hp_output

        # Then low pass filter
        if State.dt > 0 and self.high_cutoff > 0:
            rc_lp = 1.0 / (2.0 * math.pi * self.high_cutoff)
            alpha_lp = State.dt / (rc_lp + State.dt)
            self.lp_output = alpha_lp * hp_output + (1.0 - alpha_lp) * self.lp_output
        else:
            self.lp_output = hp_output

        self.output = self.lp_output

    def getOutput(self, port=0):
        return self.output


class Backlash(Block):
    """Backlash block - models mechanical backlash/deadband.

    Simulates the play in mechanical systems like gears,
    where the output doesn't change until the input moves
    beyond a deadband threshold.
    """

    def __init__(self, deadband_width=0.1, initial_output=0.0):
        super().__init__()
        self.deadband_width = abs(deadband_width)
        self.half_width = self.deadband_width / 2.0
        self.input = 0.0
        self.output = initial_output
        self.input_block = None

    def init(self):
        pass  # Keep output from initialization

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput()

        # Output only changes when input moves beyond deadband
        if self.input > self.output + self.half_width:
            self.output = self.input - self.half_width
        elif self.input < self.output - self.half_width:
            self.output = self.input + self.half_width
        # else: output stays the same (in deadband)

    def getOutput(self, port=0):
        return self.output


def _butterworth_poles(n: int) -> list[complex]:
    """Calculate Butterworth filter poles for order n.

    Butterworth poles are equally spaced on the left half of the unit circle.
    """
    poles = []
    for k in range(n):
        theta = math.pi * (2 * k + n + 1) / (2 * n)
        poles.append(complex(math.cos(theta), math.sin(theta)))
    return poles


def _chebyshev1_poles(n: int, ripple_db: float) -> list[complex]:
    """Calculate Chebyshev Type I filter poles.

    Chebyshev Type I has equiripple in the passband and monotonic in the stopband.
    """
    epsilon = math.sqrt(10 ** (ripple_db / 10) - 1)
    # sinh and cosh of (1/n) * arcsinh(1/epsilon)
    v0 = math.asinh(1 / epsilon) / n
    sinh_v0 = math.sinh(v0)
    cosh_v0 = math.cosh(v0)

    poles = []
    for k in range(n):
        theta = math.pi * (2 * k + 1) / (2 * n)
        sigma = -sinh_v0 * math.sin(theta)
        omega = cosh_v0 * math.cos(theta)
        poles.append(complex(sigma, omega))
    return poles


def _chebyshev2_poles(n: int, stopband_db: float) -> list[complex]:
    """Calculate Chebyshev Type II filter poles.

    Chebyshev Type II has monotonic passband and equiripple in the stopband.
    """
    epsilon = 1 / math.sqrt(10 ** (stopband_db / 10) - 1)
    v0 = math.asinh(1 / epsilon) / n
    sinh_v0 = math.sinh(v0)
    cosh_v0 = math.cosh(v0)

    poles = []
    for k in range(n):
        theta = math.pi * (2 * k + 1) / (2 * n)
        sigma = -sinh_v0 * math.sin(theta)
        omega = cosh_v0 * math.cos(theta)
        # Invert to get Type II poles
        denom = sigma**2 + omega**2
        if abs(denom) > 1e-10:
            poles.append(complex(sigma / denom, -omega / denom))
        else:
            poles.append(complex(-1, 0))
    return poles


def _bessel_poles(n: int) -> list[complex]:
    """Calculate Bessel filter poles (maximally flat group delay).

    Uses precomputed poles for common orders, approximates for higher orders.
    """
    # Precomputed Bessel poles (normalized to unity delay at DC)
    bessel_poles_table = {
        1: [complex(-1.0, 0.0)],
        2: [complex(-1.1030, 0.6368), complex(-1.1030, -0.6368)],
        3: [complex(-1.0509, 0.9991), complex(-1.0509, -0.9991), complex(-1.3270, 0.0)],
        4: [complex(-0.9952, 1.2571), complex(-0.9952, -1.2571),
            complex(-1.3700, 0.4103), complex(-1.3700, -0.4103)],
        5: [complex(-0.9576, 1.4711), complex(-0.9576, -1.4711),
            complex(-1.3809, 0.7179), complex(-1.3809, -0.7179),
            complex(-1.5023, 0.0)],
    }

    if n in bessel_poles_table:
        return bessel_poles_table[n]

    # For higher orders, approximate with Butterworth-like distribution
    # scaled for Bessel characteristics
    poles = []
    for k in range(n):
        theta = math.pi * (2 * k + n + 1) / (2 * n)
        # Bessel poles are further from origin than Butterworth
        r = 1.0 + 0.2 * n
        poles.append(complex(r * math.cos(theta), r * math.sin(theta)))
    return poles


class AnalogFilter(Block):
    """Configurable analog filter block supporting multiple design methods.

    Implements IIR filters using Butterworth, Chebyshev Type I, Chebyshev Type II,
    and Bessel design methods. Supports lowpass, highpass, bandpass, and bandstop
    response types with configurable order.

    Similar to Simulink's Analog Filter Design block.

    Parameters:
        design: Filter design method ('butterworth', 'chebyshev1', 'chebyshev2', 'bessel')
        response: Filter response type ('lowpass', 'highpass', 'bandpass', 'bandstop')
        order: Filter order (1-10 for single band, 1-5 for bandpass/bandstop)
        cutoff_freq: Cutoff frequency in Hz (single value for LP/HP, ignored for BP/BS)
        low_cutoff: Lower cutoff frequency for bandpass/bandstop
        high_cutoff: Upper cutoff frequency for bandpass/bandstop
        passband_ripple: Passband ripple in dB for Chebyshev I (default 1.0)
        stopband_atten: Stopband attenuation in dB for Chebyshev II (default 40.0)
    """

    def __init__(
        self,
        design: str = "butterworth",
        response: str = "lowpass",
        order: int = 2,
        cutoff_freq: float = 10.0,
        low_cutoff: float = 1.0,
        high_cutoff: float = 10.0,
        passband_ripple: float = 1.0,
        stopband_atten: float = 40.0,
    ):
        super().__init__()
        self.design = design
        self.response = response
        self.order = max(1, min(10, int(order)))
        self.cutoff_freq = cutoff_freq
        self.low_cutoff = low_cutoff
        self.high_cutoff = high_cutoff
        self.passband_ripple = passband_ripple
        self.stopband_atten = stopband_atten

        self.input = 0.0
        self.output = 0.0
        self.input_block = None

        # State arrays for cascaded biquad sections
        self._biquads: list[dict] = []
        self._initialized = False

    def _design_filter(self, dt: float):
        """Design the filter and create biquad cascade sections."""
        if dt <= 0:
            return

        # Get analog prototype poles
        if self.design == "butterworth":
            poles = _butterworth_poles(self.order)
        elif self.design == "chebyshev1":
            poles = _chebyshev1_poles(self.order, self.passband_ripple)
        elif self.design == "chebyshev2":
            poles = _chebyshev2_poles(self.order, self.stopband_atten)
        elif self.design == "bessel":
            poles = _bessel_poles(self.order)
        else:
            poles = _butterworth_poles(self.order)

        # Convert to angular frequency
        if self.response in ("lowpass", "highpass"):
            wc = 2 * math.pi * self.cutoff_freq
        else:
            wc_low = 2 * math.pi * self.low_cutoff
            wc_high = 2 * math.pi * self.high_cutoff
            wc = math.sqrt(wc_low * wc_high)  # Center frequency

        # Create biquad sections from pole pairs
        self._biquads = []

        # Process poles in conjugate pairs
        i = 0
        while i < len(poles):
            pole = poles[i]

            if abs(pole.imag) < 1e-10:
                # Real pole - first order section implemented as biquad
                # Scale pole by cutoff frequency
                p_scaled = pole.real * wc

                # Bilinear transform: s -> 2/T * (z-1)/(z+1)
                # For first order: H(s) = wc / (s - p) -> H(z)
                k = 2 / dt
                a0 = k - p_scaled
                a1 = -k - p_scaled
                b0 = -p_scaled if self.response == "lowpass" else k
                b1 = -p_scaled if self.response == "lowpass" else -k

                # Normalize
                if abs(a0) > 1e-10:
                    self._biquads.append({
                        "b0": b0 / a0,
                        "b1": b1 / a0,
                        "b2": 0.0,
                        "a1": a1 / a0,
                        "a2": 0.0,
                        "x1": 0.0, "x2": 0.0,
                        "y1": 0.0, "y2": 0.0,
                    })
                i += 1
            else:
                # Complex conjugate pair - second order section
                sigma = pole.real * wc
                omega = pole.imag * wc

                # Second order analog section: wc^2 / (s^2 - 2*sigma*s + (sigma^2 + omega^2))
                k = 2 / dt
                w0_sq = sigma**2 + omega**2

                # Bilinear transform coefficients
                a0 = k**2 - 2 * sigma * k + w0_sq
                a1 = 2 * w0_sq - 2 * k**2
                a2 = k**2 + 2 * sigma * k + w0_sq

                if self.response == "lowpass":
                    b0 = w0_sq
                    b1 = 2 * w0_sq
                    b2 = w0_sq
                elif self.response == "highpass":
                    b0 = k**2
                    b1 = -2 * k**2
                    b2 = k**2
                else:  # bandpass approximation
                    bw = abs(omega) * 2
                    b0 = bw * k
                    b1 = 0.0
                    b2 = -bw * k

                # Normalize
                if abs(a0) > 1e-10:
                    self._biquads.append({
                        "b0": b0 / a0,
                        "b1": b1 / a0,
                        "b2": b2 / a0,
                        "a1": a1 / a0,
                        "a2": a2 / a0,
                        "x1": 0.0, "x2": 0.0,
                        "y1": 0.0, "y2": 0.0,
                    })
                i += 2  # Skip conjugate

        # If no biquads were created, create a simple passthrough
        if not self._biquads:
            self._biquads.append({
                "b0": 1.0, "b1": 0.0, "b2": 0.0,
                "a1": 0.0, "a2": 0.0,
                "x1": 0.0, "x2": 0.0,
                "y1": 0.0, "y2": 0.0,
            })

        self._initialized = True

    def init(self):
        self.output = 0.0
        self._biquads = []
        self._initialized = False

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput()

        # Design filter on first update (when dt is available)
        if not self._initialized and State.dt > 0:
            self._design_filter(State.dt)

        # Process through cascaded biquad sections
        x = self.input
        for bq in self._biquads:
            # Direct Form II Transposed
            y = bq["b0"] * x + bq["b1"] * bq["x1"] + bq["b2"] * bq["x2"] \
                - bq["a1"] * bq["y1"] - bq["a2"] * bq["y2"]

            # Shift state
            bq["x2"] = bq["x1"]
            bq["x1"] = x
            bq["y2"] = bq["y1"]
            bq["y1"] = y

            x = y  # Output of this section feeds next

        self.output = x

    def getOutput(self, port=0):
        return self.output


class NotchFilter(Block):
    """Notch (band-reject) filter for removing specific frequency components.

    Useful for removing power line interference (50/60 Hz), mechanical resonances,
    or other narrowband disturbances from signals.

    Parameters:
        notch_freq: Center frequency to reject (Hz)
        bandwidth: Width of the notch in Hz (3 dB bandwidth)
        depth: Notch depth in dB (default 40 dB)
    """

    def __init__(self, notch_freq: float = 60.0, bandwidth: float = 2.0, depth: float = 40.0):
        super().__init__()
        self.notch_freq = notch_freq
        self.bandwidth = bandwidth
        self.depth = depth

        self.input = 0.0
        self.output = 0.0
        self.input_block = None

        # Biquad filter coefficients
        self.b0 = 1.0
        self.b1 = 0.0
        self.b2 = 1.0
        self.a1 = 0.0
        self.a2 = 0.0

        # State variables
        self.x1 = 0.0
        self.x2 = 0.0
        self.y1 = 0.0
        self.y2 = 0.0

        self._initialized = False

    def _design_notch(self, dt: float):
        """Design the notch filter coefficients."""
        if dt <= 0 or self.notch_freq <= 0:
            return

        # Normalized frequency
        fs = 1.0 / dt
        w0 = 2 * math.pi * self.notch_freq / fs

        # Q factor from bandwidth
        Q = self.notch_freq / max(self.bandwidth, 0.01)

        # Notch filter coefficients (peaking EQ at negative gain)
        alpha = math.sin(w0) / (2 * Q)

        # Normalize
        a0 = 1 + alpha
        self.b0 = 1.0 / a0
        self.b1 = -2 * math.cos(w0) / a0
        self.b2 = 1.0 / a0
        self.a1 = -2 * math.cos(w0) / a0
        self.a2 = (1 - alpha) / a0

        self._initialized = True

    def init(self):
        self.output = 0.0
        self.x1 = 0.0
        self.x2 = 0.0
        self.y1 = 0.0
        self.y2 = 0.0
        self._initialized = False

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput()

        if not self._initialized and State.dt > 0:
            self._design_notch(State.dt)

        # Biquad filter
        y = self.b0 * self.input + self.b1 * self.x1 + self.b2 * self.x2 \
            - self.a1 * self.y1 - self.a2 * self.y2

        self.x2 = self.x1
        self.x1 = self.input
        self.y2 = self.y1
        self.y1 = y

        self.output = y

    def getOutput(self, port=0):
        return self.output
