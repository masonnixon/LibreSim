"""Nonlinear blocks for OSK-based simulation.

Provides nonlinear elements commonly used in control systems
including lookup tables, quantizers, and relay blocks.
"""

import bisect

from ..block import Block
from ..state import State


class LookupTable1D(Block):
    """1D Lookup Table with linear interpolation.

    Maps input values to output values using a table with
    linear interpolation between points. Useful for modeling
    nonlinear relationships from measured data.
    """

    def __init__(self, x_data=None, y_data=None):
        super().__init__()
        # Default to identity mapping if no data provided
        self.x_data = x_data if x_data is not None else [0.0, 1.0]
        self.y_data = y_data if y_data is not None else [0.0, 1.0]
        self.input = 0.0
        self.output = 0.0
        self.input_block = None

    def init(self):
        self.output = self._interpolate(0.0)

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0):
        self.input_block = block

    def _interpolate(self, x):
        """Linear interpolation with extrapolation at boundaries."""
        if len(self.x_data) == 0 or len(self.y_data) == 0:
            return 0.0
        if len(self.x_data) == 1:
            return self.y_data[0]

        # Find the interval containing x
        if x <= self.x_data[0]:
            # Extrapolate below
            if len(self.x_data) >= 2:
                slope = (self.y_data[1] - self.y_data[0]) / (self.x_data[1] - self.x_data[0])
                return self.y_data[0] + slope * (x - self.x_data[0])
            return self.y_data[0]

        if x >= self.x_data[-1]:
            # Extrapolate above
            if len(self.x_data) >= 2:
                slope = (self.y_data[-1] - self.y_data[-2]) / (self.x_data[-1] - self.x_data[-2])
                return self.y_data[-1] + slope * (x - self.x_data[-1])
            return self.y_data[-1]

        # Binary search for interval
        idx = bisect.bisect_right(self.x_data, x) - 1
        idx = max(0, min(idx, len(self.x_data) - 2))

        # Linear interpolation
        x0, x1 = self.x_data[idx], self.x_data[idx + 1]
        y0, y1 = self.y_data[idx], self.y_data[idx + 1]

        if x1 == x0:
            return y0

        t = (x - x0) / (x1 - x0)
        return y0 + t * (y1 - y0)

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput()

        self.output = self._interpolate(self.input)

    def getOutput(self, port=0):
        return self.output


class LookupTable2D(Block):
    """2D Lookup Table with bilinear interpolation.

    Maps two input values to an output value using a 2D table.
    Useful for modeling surfaces or functions of two variables.
    """

    def __init__(self, x_data=None, y_data=None, z_data=None):
        super().__init__()
        # Default to simple plane if no data provided
        self.x_data = x_data if x_data is not None else [0.0, 1.0]
        self.y_data = y_data if y_data is not None else [0.0, 1.0]
        # z_data should be a 2D list: z_data[i][j] = f(x_data[j], y_data[i])
        self.z_data = z_data if z_data is not None else [[0.0, 0.0], [0.0, 1.0]]
        self.inputs = [0.0, 0.0]
        self.output = 0.0
        self.input_blocks = [None, None]

    def init(self):
        self.output = self._interpolate(0.0, 0.0)

    def setInput(self, value, port=0):
        if port < 2:
            self.inputs[port] = value

    def connectInput(self, block, port=0):
        if port < 2:
            self.input_blocks[port] = block

    def _interpolate(self, x, y):
        """Bilinear interpolation."""
        if len(self.x_data) == 0 or len(self.y_data) == 0:
            return 0.0

        # Find x interval
        if x <= self.x_data[0]:
            xi = 0
            tx = 0.0
        elif x >= self.x_data[-1]:
            xi = len(self.x_data) - 2
            tx = 1.0
        else:
            xi = bisect.bisect_right(self.x_data, x) - 1
            xi = max(0, min(xi, len(self.x_data) - 2))
            dx = self.x_data[xi + 1] - self.x_data[xi]
            tx = (x - self.x_data[xi]) / dx if dx != 0 else 0.0

        # Find y interval
        if y <= self.y_data[0]:
            yi = 0
            ty = 0.0
        elif y >= self.y_data[-1]:
            yi = len(self.y_data) - 2
            ty = 1.0
        else:
            yi = bisect.bisect_right(self.y_data, y) - 1
            yi = max(0, min(yi, len(self.y_data) - 2))
            dy = self.y_data[yi + 1] - self.y_data[yi]
            ty = (y - self.y_data[yi]) / dy if dy != 0 else 0.0

        # Get the four corner values
        try:
            z00 = self.z_data[yi][xi]
            z01 = self.z_data[yi][xi + 1]
            z10 = self.z_data[yi + 1][xi]
            z11 = self.z_data[yi + 1][xi + 1]
        except IndexError:
            return 0.0

        # Bilinear interpolation
        z0 = z00 + tx * (z01 - z00)
        z1 = z10 + tx * (z11 - z10)
        return z0 + ty * (z1 - z0)

    def update(self):
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                self.inputs[i] = block.getOutput()

        self.output = self._interpolate(self.inputs[0], self.inputs[1])

    def getOutput(self, port=0):
        return self.output


class Quantizer(Block):
    """Quantizer block - rounds signal to discrete levels.

    Useful for modeling A/D converters or discrete actuator positions.
    """

    def __init__(self, interval=1.0):
        super().__init__()
        self.interval = abs(interval) if interval != 0 else 1.0
        self.input = 0.0
        self.output = 0.0
        self.input_block = None

    def init(self):
        self.output = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput()

        # Round to nearest quantization level
        self.output = round(self.input / self.interval) * self.interval

    def getOutput(self, port=0):
        return self.output


class Relay(Block):
    """Relay block - on/off switch with hysteresis.

    Models a relay or comparator with adjustable on/off thresholds
    and output levels. Useful for modeling bang-bang controllers
    or thermostats.
    """

    def __init__(self, switch_on=0.5, switch_off=-0.5, output_on=1.0, output_off=0.0):
        super().__init__()
        self.switch_on = switch_on  # Threshold to turn on (input > switch_on)
        self.switch_off = switch_off  # Threshold to turn off (input < switch_off)
        self.output_on = output_on  # Output value when on
        self.output_off = output_off  # Output value when off
        self.input = 0.0
        self.output = output_off
        self.input_block = None
        self.is_on = False

    def init(self):
        self.output = self.output_off
        self.is_on = False

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput()

        # Hysteresis logic
        if self.is_on:
            if self.input < self.switch_off:
                self.is_on = False
        else:
            if self.input > self.switch_on:
                self.is_on = True

        self.output = self.output_on if self.is_on else self.output_off

    def getOutput(self, port=0):
        return self.output


class Coulomb(Block):
    """Coulomb friction block.

    Models static and dynamic friction forces. Output is a friction
    force that opposes motion, with a higher breakaway force.
    """

    def __init__(self, static_gain=1.0, dynamic_gain=0.8, velocity_threshold=0.01):
        super().__init__()
        self.static_gain = static_gain  # Static friction coefficient
        self.dynamic_gain = dynamic_gain  # Dynamic friction coefficient
        self.velocity_threshold = abs(velocity_threshold)  # Threshold for static/dynamic transition
        self.input = 0.0  # Velocity input
        self.output = 0.0
        self.input_block = None

    def init(self):
        self.output = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput()

        velocity = self.input
        if abs(velocity) < self.velocity_threshold:
            # Static friction region - output opposes any force trying to move
            # In practice, we output maximum static friction scaled by input
            self.output = -self.static_gain * (velocity / self.velocity_threshold)
        else:
            # Dynamic friction - constant magnitude opposing motion
            self.output = -self.dynamic_gain if velocity > 0 else self.dynamic_gain

    def getOutput(self, port=0):
        return self.output


class VariableTransportDelay(Block):
    """Variable Transport Delay block.

    Delays the input signal by a variable amount of time.
    Useful for modeling conveyor belts or fluid transport.
    """

    def __init__(self, max_delay=1.0, initial_delay=0.1):
        super().__init__()
        self.max_delay = max(0.001, max_delay)
        self.delay_time = min(initial_delay, self.max_delay)
        self.inputs = [0.0, 0.0]  # [signal, delay]
        self.output = 0.0
        self.input_blocks = [None, None]
        self.buffer = []  # List of (time, value) tuples

    def init(self):
        self.output = 0.0
        self.buffer = []

    def setInput(self, value, port=0):
        if port < 2:
            self.inputs[port] = value

    def connectInput(self, block, port=0):
        if port < 2:
            self.input_blocks[port] = block

    def update(self):
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                self.inputs[i] = block.getOutput()

        signal = self.inputs[0]
        self.delay_time = max(0.0, min(self.inputs[1], self.max_delay))

        # Add current sample to buffer
        self.buffer.append((State.t, signal))

        # Find the delayed output
        target_time = State.t - self.delay_time

        # Remove old samples
        while len(self.buffer) > 1 and self.buffer[1][0] < target_time:
            self.buffer.pop(0)

        # Interpolate or use oldest value
        if len(self.buffer) == 0:
            self.output = signal
        elif len(self.buffer) == 1 or target_time <= self.buffer[0][0]:
            self.output = self.buffer[0][1]
        else:
            # Linear interpolation between two nearest samples
            for i in range(len(self.buffer) - 1):
                if self.buffer[i][0] <= target_time <= self.buffer[i + 1][0]:
                    t0, v0 = self.buffer[i]
                    t1, v1 = self.buffer[i + 1]
                    if t1 != t0:
                        alpha = (target_time - t0) / (t1 - t0)
                        self.output = v0 + alpha * (v1 - v0)
                    else:
                        self.output = v0
                    break
            else:
                self.output = self.buffer[-1][1]

    def getOutput(self, port=0):
        return self.output
