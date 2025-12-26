"""Source blocks for OSK-based simulation."""

import math
import random

from ..block import Block
from ..state import State


class Constant(Block):
    """Constant value source block.

    Supports both scalar and vector/array values. When a list or array
    is provided, the block outputs a vector signal accessible via
    getOutputVector() or individual elements via getOutput(port).
    """

    def __init__(self, value=1.0):
        super().__init__()
        self._is_vector = False
        self._values = []
        self.output = 0.0

        # Parse value - it might be a string, number, list, or array
        parsed = self._parse_value(value)
        if isinstance(parsed, list):
            self._is_vector = True
            self._values = parsed
            self.output = parsed[0] if parsed else 0.0
        else:
            self._is_vector = False
            self._values = [parsed]
            self.output = parsed

    def _parse_value(self, value):
        """Parse the input value into a number or list of numbers."""
        if value is None:
            return 1.0

        # Already a list or tuple
        if isinstance(value, (list, tuple)):
            return [float(v) for v in value]

        # String value - could be number, array literal, or expression
        if isinstance(value, str):
            value = value.strip()

            # Try parsing as a simple number first
            try:
                return float(value)
            except ValueError:
                pass

            # Try parsing as array literal: [1, 2, 3] or [1 2 3]
            if value.startswith('[') and value.endswith(']'):
                inner = value[1:-1].strip()
                if inner:
                    # Handle comma-separated or space-separated values
                    if ',' in inner:
                        parts = [p.strip() for p in inner.split(',')]
                    elif ';' in inner:
                        # Handle semicolon-separated (MATLAB row separator)
                        parts = [p.strip() for p in inner.split(';')]
                    else:
                        parts = inner.split()

                    try:
                        return [float(p) for p in parts if p]
                    except ValueError:
                        pass

            # Try parsing as comma-separated values without brackets: 1,2,3,4
            if ',' in value:
                parts = [p.strip() for p in value.split(',')]
                try:
                    parsed = [float(p) for p in parts if p]
                    if len(parsed) > 1:
                        return parsed
                except ValueError:
                    pass

            # Default for unparseable strings
            return 1.0

        # Numeric value
        try:
            return float(value)
        except (TypeError, ValueError):
            return 1.0

    def init(self):
        if self._is_vector:
            self.output = self._values[0] if self._values else 0.0
        else:
            self.output = self._values[0] if self._values else 0.0

    def update(self):
        # Constants don't change, but update output for consistency
        if self._is_vector:
            self.output = self._values[0] if self._values else 0.0
        else:
            self.output = self._values[0] if self._values else 0.0

    def getOutput(self, port=0):
        """Get output value. For vectors, port indexes into the array."""
        if port < len(self._values):
            return self._values[port]
        return 0.0

    def getOutputVector(self):
        """Get the full output vector. Returns None for scalar values."""
        if self._is_vector:
            return self._values.copy()
        return None

    @property
    def value(self):
        """Get the scalar value (for backward compatibility)."""
        return self._values[0] if self._values else 0.0

    @value.setter
    def value(self, v):
        """Set the value (for backward compatibility)."""
        parsed = self._parse_value(v)
        if isinstance(parsed, list):
            self._is_vector = True
            self._values = parsed
        else:
            self._is_vector = False
            self._values = [parsed]

    def getNumOutputs(self):
        """Get the number of output signals."""
        return len(self._values)


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
