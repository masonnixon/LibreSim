"""Signal processing blocks for OSK-based simulation.

Provides filtering and signal conditioning blocks commonly used in
control systems and signal processing applications.
"""

import math
from collections import deque
from ..block import Block
from ..state import State


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
