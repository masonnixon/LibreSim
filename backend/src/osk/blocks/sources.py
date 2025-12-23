"""Source blocks for OSK-based simulation."""

import math

from ..block import Block
from ..state import State


class Constant(Block):
    """Constant value source block."""

    def __init__(self, value=1.0):
        super().__init__()
        # Parse value - it might be a string from the frontend
        if isinstance(value, str):
            try:
                self.value = float(value)
            except ValueError:
                # Could be an expression - for now default to 1.0
                self.value = 1.0
        else:
            self.value = float(value) if value is not None else 1.0
        self.output = 0.0

    def init(self):
        self.output = self.value

    def update(self):
        self.output = self.value

    def getOutput(self, port=0):
        return self.output


class Step(Block):
    """Step function source block."""

    def __init__(self, step_time=1.0, initial_value=0.0, final_value=1.0):
        super().__init__()
        self.step_time = step_time
        self.initial_value = initial_value
        self.final_value = final_value
        self.output = 0.0

    def init(self):
        self.output = self.initial_value

    def update(self):
        if State.t >= self.step_time:
            self.output = self.final_value
        else:
            self.output = self.initial_value

    def getOutput(self, port=0):
        return self.output


class Ramp(Block):
    """Ramp function source block."""

    def __init__(self, slope=1.0, start_time=0.0, initial_output=0.0):
        super().__init__()
        self.slope = slope
        self.start_time = start_time
        self.initial_output = initial_output
        self.output = 0.0

    def init(self):
        self.output = self.initial_output

    def update(self):
        if State.t >= self.start_time:
            self.output = self.initial_output + self.slope * (State.t - self.start_time)
        else:
            self.output = self.initial_output

    def getOutput(self, port=0):
        return self.output


class SineWave(Block):
    """Sinusoidal source block."""

    def __init__(self, amplitude=1.0, frequency=1.0, phase=0.0, bias=0.0):
        super().__init__()
        self.amplitude = amplitude
        self.frequency = frequency
        self.phase = phase
        self.bias = bias
        self.output = 0.0

    def init(self):
        self.output = self.amplitude * math.sin(self.phase) + self.bias

    def update(self):
        self.output = (
            self.amplitude * math.sin(2.0 * math.pi * self.frequency * State.t + self.phase)
            + self.bias
        )

    def getOutput(self, port=0):
        return self.output


class Clock(Block):
    """Simulation time source block."""

    def __init__(self):
        super().__init__()
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def update(self):
        self.output = State.t

    def getOutput(self, port=0):
        return self.output


class PulseGenerator(Block):
    """Pulse train generator block."""

    def __init__(self, amplitude=1.0, period=1.0, duty_cycle=50.0, phase_delay=0.0):
        super().__init__()
        self.amplitude = amplitude
        self.period = period
        self.duty_cycle = duty_cycle / 100.0  # Convert percentage to fraction
        self.phase_delay = phase_delay
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def update(self):
        if State.t < self.phase_delay:
            self.output = 0.0
        else:
            t_in_period = (State.t - self.phase_delay) % self.period
            if t_in_period < self.period * self.duty_cycle:
                self.output = self.amplitude
            else:
                self.output = 0.0

    def getOutput(self, port=0):
        return self.output
