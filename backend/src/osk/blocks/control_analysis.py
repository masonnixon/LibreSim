"""Control system analysis blocks for LibreSim.

These blocks compute frequency response, stability analysis, and time-domain
characteristics of linear systems defined by transfer functions.
"""

import math
import cmath
import numpy as np
from ..block import Block


class BodePlot(Block):
    """Bode plot analysis block.

    Computes magnitude (dB) and phase (degrees) of a transfer function
    over a logarithmic frequency range. Results are stored for visualization.

    Parameters:
        numerator: Transfer function numerator coefficients [b0, b1, ...]
        denominator: Transfer function denominator coefficients [a0, a1, ...]
        minFrequency: Minimum frequency in Hz (default: 0.01)
        maxFrequency: Maximum frequency in Hz (default: 100)
        numPoints: Number of frequency points (default: 200)

    Outputs:
        Port 0: DC gain (magnitude at lowest frequency)
    """

    def __init__(self, numerator=None, denominator=None,
                 minFrequency=0.01, maxFrequency=100.0, numPoints=200):
        super().__init__()
        self.numerator = numerator if numerator else [1.0]
        self.denominator = denominator if denominator else [1.0, 1.0]
        self.minFrequency = minFrequency
        self.maxFrequency = maxFrequency
        self.numPoints = numPoints

        # Analysis results (computed at init)
        self.frequencies = []  # Hz
        self.magnitude_db = []  # dB
        self.phase_deg = []  # degrees
        self.gain_margin = None  # dB
        self.phase_margin = None  # degrees
        self.gain_crossover_freq = None  # Hz
        self.phase_crossover_freq = None  # Hz

        self.output = 0.0
        self.input = 0.0
        self.input_block = None

    def init(self):
        """Compute frequency response at simulation start."""
        self._compute_frequency_response()
        self._compute_stability_margins()

    def _evaluate_tf(self, s):
        """Evaluate transfer function H(s) at complex frequency s."""
        # Compute numerator polynomial
        num = complex(0, 0)
        for i, coef in enumerate(self.numerator):
            power = len(self.numerator) - 1 - i
            num += coef * (s ** power)

        # Compute denominator polynomial
        den = complex(0, 0)
        for i, coef in enumerate(self.denominator):
            power = len(self.denominator) - 1 - i
            den += coef * (s ** power)

        if abs(den) < 1e-15:
            return complex(1e10, 0)  # Avoid division by zero

        return num / den

    def _compute_frequency_response(self):
        """Compute magnitude and phase over frequency range."""
        self.frequencies = []
        self.magnitude_db = []
        self.phase_deg = []

        # Logarithmic frequency spacing
        log_min = math.log10(self.minFrequency)
        log_max = math.log10(self.maxFrequency)

        for i in range(self.numPoints):
            # Frequency in Hz
            log_f = log_min + (log_max - log_min) * i / (self.numPoints - 1)
            freq_hz = 10 ** log_f

            # Convert to rad/s for s-domain
            omega = 2 * math.pi * freq_hz
            s = complex(0, omega)

            # Evaluate transfer function
            H = self._evaluate_tf(s)

            # Magnitude in dB
            mag = abs(H)
            if mag > 0:
                mag_db = 20 * math.log10(mag)
            else:
                mag_db = -200  # Floor value

            # Phase in degrees (unwrapped would need more logic)
            phase_rad = cmath.phase(H)
            phase_deg = math.degrees(phase_rad)

            self.frequencies.append(freq_hz)
            self.magnitude_db.append(mag_db)
            self.phase_deg.append(phase_deg)

        # Set output to DC gain
        if self.magnitude_db:
            self.output = self.magnitude_db[0]

    def _compute_stability_margins(self):
        """Compute gain and phase margins."""
        # Find gain crossover frequency (where magnitude = 0 dB)
        self.gain_crossover_freq = None
        self.phase_margin = None

        for i in range(len(self.frequencies) - 1):
            if self.magnitude_db[i] >= 0 and self.magnitude_db[i + 1] < 0:
                # Interpolate
                t = -self.magnitude_db[i] / (self.magnitude_db[i + 1] - self.magnitude_db[i])
                self.gain_crossover_freq = self.frequencies[i] + t * (self.frequencies[i + 1] - self.frequencies[i])
                phase_at_gc = self.phase_deg[i] + t * (self.phase_deg[i + 1] - self.phase_deg[i])
                self.phase_margin = 180 + phase_at_gc
                break

        # Find phase crossover frequency (where phase = -180 deg)
        self.phase_crossover_freq = None
        self.gain_margin = None

        for i in range(len(self.frequencies) - 1):
            if self.phase_deg[i] > -180 and self.phase_deg[i + 1] <= -180:
                # Interpolate
                t = (-180 - self.phase_deg[i]) / (self.phase_deg[i + 1] - self.phase_deg[i])
                self.phase_crossover_freq = self.frequencies[i] + t * (self.frequencies[i + 1] - self.frequencies[i])
                mag_at_pc = self.magnitude_db[i] + t * (self.magnitude_db[i + 1] - self.magnitude_db[i])
                self.gain_margin = -mag_at_pc
                break

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0):
        self.input_block = block

    def update(self):
        # Analysis blocks don't update during simulation
        pass

    def getOutput(self, port=0):
        return self.output

    def get_bode_data(self):
        """Return Bode plot data for visualization."""
        return {
            'frequencies': self.frequencies,
            'magnitude_db': self.magnitude_db,
            'phase_deg': self.phase_deg,
            'gain_margin': self.gain_margin,
            'phase_margin': self.phase_margin,
            'gain_crossover_freq': self.gain_crossover_freq,
            'phase_crossover_freq': self.phase_crossover_freq,
        }


class NyquistPlot(Block):
    """Nyquist plot analysis block.

    Computes the Nyquist diagram (real vs imaginary parts) of a transfer function
    for stability analysis using the Nyquist criterion.

    Parameters:
        numerator: Transfer function numerator coefficients
        denominator: Transfer function denominator coefficients
        minFrequency: Minimum frequency in Hz (default: 0.001)
        maxFrequency: Maximum frequency in Hz (default: 1000)
        numPoints: Number of frequency points (default: 500)

    Outputs:
        Port 0: Encirclement count (for stability analysis)
    """

    def __init__(self, numerator=None, denominator=None,
                 minFrequency=0.001, maxFrequency=1000.0, numPoints=500):
        super().__init__()
        self.numerator = numerator if numerator else [1.0]
        self.denominator = denominator if denominator else [1.0, 1.0]
        self.minFrequency = minFrequency
        self.maxFrequency = maxFrequency
        self.numPoints = numPoints

        # Analysis results
        self.real_parts = []
        self.imag_parts = []
        self.frequencies = []
        self.encirclements = 0

        self.output = 0.0
        self.input = 0.0
        self.input_block = None

    def init(self):
        """Compute Nyquist diagram at simulation start."""
        self._compute_nyquist()
        self._count_encirclements()

    def _evaluate_tf(self, s):
        """Evaluate transfer function H(s) at complex frequency s."""
        num = complex(0, 0)
        for i, coef in enumerate(self.numerator):
            power = len(self.numerator) - 1 - i
            num += coef * (s ** power)

        den = complex(0, 0)
        for i, coef in enumerate(self.denominator):
            power = len(self.denominator) - 1 - i
            den += coef * (s ** power)

        if abs(den) < 1e-15:
            return complex(1e10, 0)

        return num / den

    def _compute_nyquist(self):
        """Compute Nyquist diagram data."""
        self.real_parts = []
        self.imag_parts = []
        self.frequencies = []

        # Logarithmic frequency spacing for positive frequencies
        log_min = math.log10(self.minFrequency)
        log_max = math.log10(self.maxFrequency)

        for i in range(self.numPoints):
            log_f = log_min + (log_max - log_min) * i / (self.numPoints - 1)
            freq_hz = 10 ** log_f
            omega = 2 * math.pi * freq_hz
            s = complex(0, omega)

            H = self._evaluate_tf(s)

            self.frequencies.append(freq_hz)
            self.real_parts.append(H.real)
            self.imag_parts.append(H.imag)

    def _count_encirclements(self):
        """Count encirclements of -1+0j point using winding number."""
        # Simplified encirclement counting
        # For a proper implementation, need to handle the full contour
        encirclements = 0
        critical_point = (-1, 0)

        for i in range(len(self.real_parts) - 1):
            # Check if contour crosses the negative real axis
            if (self.imag_parts[i] >= 0 and self.imag_parts[i + 1] < 0):
                # Crossing from positive to negative imaginary
                # Interpolate to find real value at crossing
                t = self.imag_parts[i] / (self.imag_parts[i] - self.imag_parts[i + 1])
                real_at_cross = self.real_parts[i] + t * (self.real_parts[i + 1] - self.real_parts[i])
                if real_at_cross < -1:
                    encirclements += 1
            elif (self.imag_parts[i] < 0 and self.imag_parts[i + 1] >= 0):
                # Crossing from negative to positive imaginary
                t = -self.imag_parts[i] / (self.imag_parts[i + 1] - self.imag_parts[i])
                real_at_cross = self.real_parts[i] + t * (self.real_parts[i + 1] - self.real_parts[i])
                if real_at_cross < -1:
                    encirclements -= 1

        self.encirclements = encirclements
        self.output = float(encirclements)

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0):
        self.input_block = block

    def update(self):
        pass

    def getOutput(self, port=0):
        return self.output

    def get_nyquist_data(self):
        """Return Nyquist plot data for visualization."""
        return {
            'real': self.real_parts,
            'imag': self.imag_parts,
            'frequencies': self.frequencies,
            'encirclements': self.encirclements,
        }


class PoleZeroMap(Block):
    """Pole-Zero map analysis block.

    Computes and displays the poles and zeros of a transfer function
    on the complex s-plane.

    Parameters:
        numerator: Transfer function numerator coefficients
        denominator: Transfer function denominator coefficients

    Outputs:
        Port 0: 1 if stable (all poles in LHP), 0 otherwise
    """

    def __init__(self, numerator=None, denominator=None):
        super().__init__()
        self.numerator = numerator if numerator else [1.0]
        self.denominator = denominator if denominator else [1.0, 1.0]

        # Analysis results
        self.poles = []  # List of (real, imag) tuples
        self.zeros = []  # List of (real, imag) tuples
        self.is_stable = False
        self.dominant_pole = None  # Pole closest to imaginary axis

        self.output = 0.0
        self.input = 0.0
        self.input_block = None

    def init(self):
        """Compute poles and zeros at simulation start."""
        self._compute_poles_zeros()
        self._analyze_stability()

    def _find_roots(self, coefficients):
        """Find roots of a polynomial using numpy."""
        if len(coefficients) <= 1:
            return []

        # Normalize by leading coefficient
        a0 = coefficients[0]
        if abs(a0) < 1e-15:
            return []

        normalized = [c / a0 for c in coefficients]

        # Use numpy for root finding
        try:
            roots = np.roots(normalized)
            return [(r.real, r.imag) for r in roots]
        except Exception:
            return []

    def _compute_poles_zeros(self):
        """Compute poles and zeros of the transfer function."""
        self.poles = self._find_roots(self.denominator)
        self.zeros = self._find_roots(self.numerator)

    def _analyze_stability(self):
        """Determine stability and find dominant pole."""
        # System is stable if all poles have negative real parts
        self.is_stable = all(pole[0] < 0 for pole in self.poles) if self.poles else True
        self.output = 1.0 if self.is_stable else 0.0

        # Find dominant pole (closest to imaginary axis)
        if self.poles:
            self.dominant_pole = min(self.poles, key=lambda p: abs(p[0]))

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0):
        self.input_block = block

    def update(self):
        pass

    def getOutput(self, port=0):
        return self.output

    def get_pole_zero_data(self):
        """Return pole-zero map data for visualization."""
        return {
            'poles': self.poles,
            'zeros': self.zeros,
            'is_stable': self.is_stable,
            'dominant_pole': self.dominant_pole,
        }


class StepInfo(Block):
    """Step response information block.

    Computes step response characteristics of a transfer function:
    - Rise time (10% to 90%)
    - Settling time (within 2% of final value)
    - Overshoot percentage
    - Peak time
    - Steady-state value

    Parameters:
        numerator: Transfer function numerator coefficients
        denominator: Transfer function denominator coefficients
        simulationTime: Time to simulate (default: 10.0 seconds)
        numPoints: Number of time points (default: 1000)
        settlingPercent: Settling threshold (default: 2%)

    Outputs:
        Port 0: Settling time
    """

    def __init__(self, numerator=None, denominator=None,
                 simulationTime=10.0, numPoints=1000, settlingPercent=2.0):
        super().__init__()
        self.numerator = numerator if numerator else [1.0]
        self.denominator = denominator if denominator else [1.0, 1.0]
        self.simulationTime = simulationTime
        self.numPoints = numPoints
        self.settlingPercent = settlingPercent

        # Analysis results
        self.times = []
        self.response = []
        self.rise_time = None  # 10% to 90%
        self.settling_time = None
        self.overshoot_percent = None
        self.peak_time = None
        self.peak_value = None
        self.steady_state_value = None

        self.output = 0.0
        self.input = 0.0
        self.input_block = None

    def init(self):
        """Compute step response at simulation start."""
        self._compute_step_response()
        self._compute_characteristics()

    def _compute_step_response(self):
        """Simulate step response using RK4 integration."""
        # Convert transfer function to state-space (controllable canonical form)
        order = len(self.denominator) - 1
        if order == 0:
            # Static gain
            gain = self.numerator[0] / self.denominator[0]
            self.times = [0.0, self.simulationTime]
            self.response = [gain, gain]
            return

        # Normalize coefficients
        a0 = self.denominator[0]
        num = [n / a0 for n in self.numerator]
        den = [d / a0 for d in self.denominator]

        # Pad numerator
        while len(num) < len(den):
            num.insert(0, 0.0)

        # State-space matrices for controllable canonical form
        # A is companion matrix, B = [0, 0, ..., 1]^T
        dt = self.simulationTime / self.numPoints
        state = [0.0] * order

        self.times = []
        self.response = []

        for i in range(self.numPoints + 1):
            t = i * dt
            u = 1.0  # Step input

            # Compute output: y = D*u + C*x
            d = num[0]  # Direct feedthrough
            y = d * u
            for j in range(order):
                c_j = num[order - j] - d * den[order - j]
                y += c_j * state[j]

            self.times.append(t)
            self.response.append(y)

            # RK4 integration
            def derivatives(s, inp):
                derivs = [0.0] * order
                for j in range(order):
                    if j < order - 1:
                        derivs[j] = s[j + 1]
                    else:
                        deriv = inp
                        for k in range(order):
                            deriv -= den[k + 1] * s[order - 1 - k]
                        derivs[j] = deriv
                return derivs

            k1 = derivatives(state, u)
            s1 = [state[j] + 0.5 * dt * k1[j] for j in range(order)]
            k2 = derivatives(s1, u)
            s2 = [state[j] + 0.5 * dt * k2[j] for j in range(order)]
            k3 = derivatives(s2, u)
            s3 = [state[j] + dt * k3[j] for j in range(order)]
            k4 = derivatives(s3, u)

            for j in range(order):
                state[j] += dt / 6 * (k1[j] + 2 * k2[j] + 2 * k3[j] + k4[j])

    def _compute_characteristics(self):
        """Compute step response characteristics."""
        if not self.response or len(self.response) < 2:
            return

        # Steady-state value (final value)
        self.steady_state_value = self.response[-1]
        final = self.steady_state_value

        if abs(final) < 1e-10:
            final = 1.0  # Avoid division by zero

        # Peak value and time
        self.peak_value = max(self.response)
        peak_idx = self.response.index(self.peak_value)
        self.peak_time = self.times[peak_idx]

        # Overshoot percentage
        if final != 0:
            self.overshoot_percent = max(0, (self.peak_value - final) / abs(final) * 100)
        else:
            self.overshoot_percent = 0

        # Rise time (10% to 90% of final value)
        target_10 = 0.1 * final
        target_90 = 0.9 * final
        time_10 = None
        time_90 = None

        for i, y in enumerate(self.response):
            if time_10 is None and y >= target_10:
                if i > 0:
                    # Interpolate
                    t = (target_10 - self.response[i-1]) / (y - self.response[i-1])
                    time_10 = self.times[i-1] + t * (self.times[i] - self.times[i-1])
                else:
                    time_10 = self.times[i]

            if time_90 is None and y >= target_90:
                if i > 0:
                    t = (target_90 - self.response[i-1]) / (y - self.response[i-1])
                    time_90 = self.times[i-1] + t * (self.times[i] - self.times[i-1])
                else:
                    time_90 = self.times[i]
                break

        if time_10 is not None and time_90 is not None:
            self.rise_time = time_90 - time_10

        # Settling time (within settlingPercent of final value)
        threshold = abs(final) * self.settlingPercent / 100
        self.settling_time = None

        # Search backwards from the end
        for i in range(len(self.response) - 1, -1, -1):
            if abs(self.response[i] - final) > threshold:
                if i < len(self.response) - 1:
                    self.settling_time = self.times[i + 1]
                break

        if self.settling_time is None:
            self.settling_time = 0.0  # Already settled

        self.output = self.settling_time if self.settling_time is not None else 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0):
        self.input_block = block

    def update(self):
        pass

    def getOutput(self, port=0):
        return self.output

    def get_step_data(self):
        """Return step response data for visualization."""
        return {
            'times': self.times,
            'response': self.response,
            'rise_time': self.rise_time,
            'settling_time': self.settling_time,
            'overshoot_percent': self.overshoot_percent,
            'peak_time': self.peak_time,
            'peak_value': self.peak_value,
            'steady_state_value': self.steady_state_value,
        }
