"""Source blocks for OSK-based simulation."""

import math
import random

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


class WhiteNoise(Block):
    """Additive White Gaussian Noise (AWGN) source block.

    Generates Gaussian-distributed random noise with specified mean and
    standard deviation (or variance). Commonly used for:
    - Modeling sensor measurement noise
    - Process/system noise in state estimation
    - Testing filter performance
    - Communication channel simulation

    Reference: https://www.mathworks.com/help/comm/ref/awgnchannel.html
    """

    def __init__(
        self,
        mean: float = 0.0,
        variance: float = 1.0,
        seed: int | None = None,
        sample_time: float = 0.0,
    ):
        """Initialize WhiteNoise block.

        Args:
            mean: Mean value of the noise distribution (default: 0.0)
            variance: Variance of the noise (sigma^2). Standard deviation = sqrt(variance)
            seed: Optional random seed for reproducibility. If None, uses system random.
            sample_time: Sample time for discrete noise. If 0, generates new sample each step.
        """
        super().__init__()
        self.mean = float(mean)
        self.variance = float(variance)
        self.std_dev = math.sqrt(abs(self.variance))
        self.seed = seed
        self.sample_time = float(sample_time)
        self.output = 0.0
        self._rng = random.Random(seed) if seed is not None else random.Random()
        self._last_sample_time = -float("inf")

    def init(self):
        # Generate initial noise sample
        self.output = self._rng.gauss(self.mean, self.std_dev)
        self._last_sample_time = 0.0

    def update(self):
        # If sample_time is 0, generate new noise every step
        # Otherwise, only generate new noise at sample intervals
        if self.sample_time <= 0:
            self.output = self._rng.gauss(self.mean, self.std_dev)
        else:
            if State.t >= self._last_sample_time + self.sample_time:
                self.output = self._rng.gauss(self.mean, self.std_dev)
                self._last_sample_time = State.t

    def getOutput(self, port=0):
        return self.output


class UniformNoise(Block):
    """Uniform random noise source block.

    Generates uniformly distributed random values between specified
    minimum and maximum bounds.
    """

    def __init__(
        self,
        minimum: float = -1.0,
        maximum: float = 1.0,
        seed: int | None = None,
        sample_time: float = 0.0,
    ):
        """Initialize UniformNoise block.

        Args:
            minimum: Minimum value of uniform distribution
            maximum: Maximum value of uniform distribution
            seed: Optional random seed for reproducibility
            sample_time: Sample time for discrete noise. If 0, generates new sample each step.
        """
        super().__init__()
        self.minimum = float(minimum)
        self.maximum = float(maximum)
        self.seed = seed
        self.sample_time = float(sample_time)
        self.output = 0.0
        self._rng = random.Random(seed) if seed is not None else random.Random()
        self._last_sample_time = -float("inf")

    def init(self):
        self.output = self._rng.uniform(self.minimum, self.maximum)
        self._last_sample_time = 0.0

    def update(self):
        if self.sample_time <= 0:
            self.output = self._rng.uniform(self.minimum, self.maximum)
        else:
            if State.t >= self._last_sample_time + self.sample_time:
                self.output = self._rng.uniform(self.minimum, self.maximum)
                self._last_sample_time = State.t

    def getOutput(self, port=0):
        return self.output
