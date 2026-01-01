"""RF (Radio Frequency) Toolbox blocks for LibreSim.

These blocks implement RF system simulation functions similar to
MATLAB RF Blockset and RF Toolbox.
"""

import math
import cmath
from typing import Optional

from ..block import Block


# =============================================================================
# RF Amplifier
# =============================================================================


class RFAmplifier(Block):
    """RF Amplifier model with gain, noise figure, and saturation.

    Models a linear amplifier with:
    - Power gain (dB)
    - Noise figure (dB)
    - Output saturation (1dB compression point)
    - IP3 (third-order intercept point for nonlinearity)

    Input: RF signal power (dBm or linear, depending on mode)
    Output: Amplified signal power
    """

    def __init__(self, gain_db: float = 20.0, noise_figure_db: float = 3.0,
                 p1db_dbm: float = 30.0, oip3_dbm: float = 40.0):
        super().__init__()
        self.gain_db = gain_db
        self.noise_figure_db = noise_figure_db
        self.p1db_dbm = p1db_dbm  # Output 1dB compression point
        self.oip3_dbm = oip3_dbm  # Output IP3
        self.output = 0.0
        self.input_block = None

    def init(self):
        self.output = 0.0

    def setInput(self, value, port=0):
        self._compute_output(float(value))

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def _compute_output(self, input_dbm: float):
        """Compute output power with compression modeling."""
        # Ideal output
        output_ideal = input_dbm + self.gain_db

        # Apply soft compression near P1dB
        # Using a simple approximation: Pout = Pin + G - compression
        # compression = 0.1 * (Pout_ideal - P1dB)^2 when approaching P1dB
        if output_ideal > self.p1db_dbm - 10:
            # Approaching compression
            excess = output_ideal - (self.p1db_dbm - 10)
            compression = 0.01 * excess * excess
            self.output = output_ideal - compression
        else:
            self.output = output_ideal

        # Limit to maximum output
        self.output = min(self.output, self.p1db_dbm + 5)

    def update(self):
        if self.input_block is not None:
            input_val = self.input_block.getOutput()
            self._compute_output(input_val)

    def getOutput(self, port=0):
        return self.output


class RFMixer(Block):
    """RF Mixer for frequency conversion.

    Multiplies input RF signal with LO (local oscillator) to produce
    sum and difference frequencies.

    Inputs:
        - Port 0: RF signal
        - Port 1: LO (local oscillator) signal
    Output: IF (intermediate frequency) signal

    For power budget analysis, models conversion loss.
    """

    def __init__(self, conversion_loss_db: float = 6.0, noise_figure_db: float = 8.0,
                 iip3_dbm: float = 10.0, sideband: str = "lower"):
        super().__init__()
        self.conversion_loss_db = conversion_loss_db
        self.noise_figure_db = noise_figure_db
        self.iip3_dbm = iip3_dbm
        self.sideband = sideband.lower()  # "lower" or "upper"
        self.rf_input = 0.0
        self.lo_input = 0.0
        self.output = 0.0
        self.input_blocks = [None, None]

    def init(self):
        self.rf_input = 0.0
        self.lo_input = 0.0
        self.output = 0.0

    def setInput(self, value, port=0):
        if port == 0:
            self.rf_input = float(value)
        else:
            self.lo_input = float(value)

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block

    def update(self):
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                if i == 0:
                    self.rf_input = block.getOutput()
                else:
                    self.lo_input = block.getOutput()

        # For power budget: output = RF power - conversion loss
        self.output = self.rf_input - self.conversion_loss_db

    def getOutput(self, port=0):
        return self.output


class RFFilter(Block):
    """RF Filter model.

    Models various filter types with insertion loss and selectivity.

    Types: lowpass, highpass, bandpass, bandstop
    """

    def __init__(self, filter_type: str = "bandpass", center_freq_hz: float = 1e9,
                 bandwidth_hz: float = 100e6, insertion_loss_db: float = 1.0,
                 rejection_db: float = 40.0):
        super().__init__()
        self.filter_type = filter_type.lower()
        self.center_freq = center_freq_hz
        self.bandwidth = bandwidth_hz
        self.insertion_loss = insertion_loss_db
        self.rejection = rejection_db
        self.input_power = 0.0
        self.input_freq = 0.0
        self.output = 0.0
        self.input_blocks = [None, None]

    def init(self):
        self.input_power = 0.0
        self.input_freq = 0.0
        self.output = 0.0

    def setInput(self, value, port=0):
        if port == 0:
            self.input_power = float(value)
        else:
            self.input_freq = float(value)

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block

    def _compute_attenuation(self, freq: float) -> float:
        """Compute attenuation at given frequency."""
        low_edge = self.center_freq - self.bandwidth / 2
        high_edge = self.center_freq + self.bandwidth / 2

        if self.filter_type == "bandpass":
            if low_edge <= freq <= high_edge:
                return self.insertion_loss
            else:
                return self.insertion_loss + self.rejection
        elif self.filter_type == "bandstop":
            if low_edge <= freq <= high_edge:
                return self.insertion_loss + self.rejection
            else:
                return self.insertion_loss
        elif self.filter_type == "lowpass":
            if freq <= self.center_freq:
                return self.insertion_loss
            else:
                return self.insertion_loss + self.rejection
        elif self.filter_type == "highpass":
            if freq >= self.center_freq:
                return self.insertion_loss
            else:
                return self.insertion_loss + self.rejection
        else:
            return self.insertion_loss

    def update(self):
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                if i == 0:
                    self.input_power = block.getOutput()
                else:
                    self.input_freq = block.getOutput()

        attenuation = self._compute_attenuation(self.input_freq)
        self.output = self.input_power - attenuation

    def getOutput(self, port=0):
        return self.output


# =============================================================================
# S-Parameter Network
# =============================================================================


class SParameterNetwork(Block):
    """S-parameter (scattering parameter) network.

    Models a 2-port network using S-parameters.
    S-parameters are complex values stored as [S11_re, S11_im, S12_re, S12_im,
                                                S21_re, S21_im, S22_re, S22_im]

    Inputs: [a1_re, a1_im] - incident wave at port 1
    Outputs: [b1_re, b1_im, b2_re, b2_im] - reflected waves
    """

    def __init__(self, s_params: Optional[list] = None):
        super().__init__()
        # Default: ideal through connection (S21 = 1, others = 0)
        if s_params is None:
            self.s_params = [0, 0, 1, 0, 1, 0, 0, 0]  # S11, S12, S21, S22
        else:
            self.s_params = s_params

        self.input = [0.0, 0.0]  # a1 complex
        self.output = [0.0, 0.0, 0.0, 0.0]  # b1, b2 complex
        self.input_block = None

    def init(self):
        self.input = [0.0, 0.0]
        self.output = [0.0, 0.0, 0.0, 0.0]

    def setInput(self, value, port=0):
        if isinstance(value, list) and len(value) >= 2:
            self.input = value[:2]

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            vec = self.input_block.getOutputVector()
            if vec is not None and len(vec) >= 2:
                self.input = vec[:2]

        # Convert to complex
        a1 = complex(self.input[0], self.input[1])

        # S-parameters as complex numbers
        S11 = complex(self.s_params[0], self.s_params[1])
        S12 = complex(self.s_params[2], self.s_params[3])
        S21 = complex(self.s_params[4], self.s_params[5])
        S22 = complex(self.s_params[6], self.s_params[7])

        # Assuming a2 = 0 (matched load at port 2)
        # b1 = S11 * a1
        # b2 = S21 * a1
        b1 = S11 * a1
        b2 = S21 * a1

        self.output = [b1.real, b1.imag, b2.real, b2.imag]

    def getOutput(self, port=0):
        if port < len(self.output):
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


# =============================================================================
# RF Budget Link Analysis
# =============================================================================


class RFBudgetElement(Block):
    """Single element in an RF budget analysis.

    Represents any RF component with gain, noise figure, and IP3.
    Outputs the cumulative cascade parameters.

    Inputs:
        - Port 0: Input power (dBm)
        - Port 1: Cascaded gain up to this point (dB)
        - Port 2: Cascaded noise figure up to this point (dB)

    Outputs:
        - Port 0: Output power (dBm)
        - Port 1: Cumulative gain (dB)
        - Port 2: Cumulative noise figure (dB)
    """

    def __init__(self, gain_db: float = 0.0, noise_figure_db: float = 0.0,
                 oip3_dbm: float = 100.0, name: str = "Element"):
        super().__init__()
        self.gain_db = gain_db
        self.noise_figure_db = noise_figure_db
        self.oip3_dbm = oip3_dbm
        self.name = name
        self.input = [0.0, 0.0, 0.0]  # Pin, Gcasc, NFcasc
        self.output = [0.0, 0.0, 0.0]  # Pout, Gcasc_new, NFcasc_new
        self.input_blocks = [None, None, None]

    def init(self):
        self.input = [0.0, 0.0, 0.0]
        self.output = [0.0, 0.0, 0.0]

    def setInput(self, value, port=0):
        if port < 3:
            self.input[port] = float(value)

    def connectInput(self, block, port=0, source_port=0):
        if port < 3:
            self.input_blocks[port] = block

    def update(self):
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                self.input[i] = block.getOutput()

        Pin_dbm = self.input[0]
        G_cascade_db = self.input[1]
        NF_cascade_db = self.input[2]

        # Output power
        Pout_dbm = Pin_dbm + self.gain_db

        # New cascaded gain
        G_new_db = G_cascade_db + self.gain_db

        # Cascaded noise figure (Friis formula in dB)
        # NF_total = NF1 + (NF2 - 1) / G1 + (NF3 - 1) / (G1 * G2) + ...
        # In dB: complex, so we approximate for now
        if G_cascade_db == 0 and NF_cascade_db == 0:
            # First element
            NF_new_db = self.noise_figure_db
        else:
            # Friis formula: F_new = F_old + (F_this - 1) / G_cascade
            F_old = 10 ** (NF_cascade_db / 10)
            F_this = 10 ** (self.noise_figure_db / 10)
            G_cascade = 10 ** (G_cascade_db / 10)

            if G_cascade > 1e-10:
                F_new = F_old + (F_this - 1) / G_cascade
            else:
                F_new = F_old + F_this - 1

            NF_new_db = 10 * math.log10(max(F_new, 1.0))

        self.output = [Pout_dbm, G_new_db, NF_new_db]

    def getOutput(self, port=0):
        if port < len(self.output):
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


class Attenuator(Block):
    """RF Attenuator.

    Simple attenuation element with specified loss.
    """

    def __init__(self, attenuation_db: float = 3.0):
        super().__init__()
        self.attenuation_db = attenuation_db
        self.output = 0.0
        self.input_block = None

    def init(self):
        self.output = 0.0

    def setInput(self, value, port=0):
        self.output = float(value) - self.attenuation_db

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.output = self.input_block.getOutput() - self.attenuation_db

    def getOutput(self, port=0):
        return self.output


# =============================================================================
# Modulation/Demodulation
# =============================================================================


class AMModulator(Block):
    """Amplitude Modulator.

    Output = Ac * (1 + m * message) * cos(wc * t)

    Inputs:
        - Port 0: Message signal
    Parameters:
        - carrier_freq: Carrier frequency (Hz)
        - carrier_amplitude: Carrier amplitude
        - modulation_index: Modulation depth (0-1)
    """

    def __init__(self, carrier_freq: float = 1e6, carrier_amplitude: float = 1.0,
                 modulation_index: float = 0.5):
        super().__init__()
        self.carrier_freq = carrier_freq
        self.carrier_amplitude = carrier_amplitude
        self.modulation_index = modulation_index
        self.message = 0.0
        self.output = 0.0
        self.input_block = None

    def init(self):
        self.message = 0.0
        self.output = 0.0

    def setInput(self, value, port=0):
        self.message = float(value)

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.message = self.input_block.getOutput()

        from ..state import State
        t = State.t

        carrier = math.cos(2 * math.pi * self.carrier_freq * t)
        envelope = 1 + self.modulation_index * self.message
        self.output = self.carrier_amplitude * envelope * carrier

    def getOutput(self, port=0):
        return self.output


class FMModulator(Block):
    """Frequency Modulator.

    Output = Ac * cos(wc * t + kf * integral(message))

    Inputs:
        - Port 0: Message signal
    Parameters:
        - carrier_freq: Carrier frequency (Hz)
        - carrier_amplitude: Carrier amplitude
        - freq_deviation: Frequency deviation (Hz)
    """

    def __init__(self, carrier_freq: float = 1e6, carrier_amplitude: float = 1.0,
                 freq_deviation: float = 75e3):
        super().__init__()
        self.carrier_freq = carrier_freq
        self.carrier_amplitude = carrier_amplitude
        self.freq_deviation = freq_deviation
        self.message = 0.0
        self.phase_integral = 0.0
        self.output = 0.0
        self.input_block = None

    def init(self):
        self.message = 0.0
        self.phase_integral = 0.0
        self.output = 0.0

    def setInput(self, value, port=0):
        self.message = float(value)

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.message = self.input_block.getOutput()

        from ..state import State
        t = State.t
        dt = State.dt

        # Integrate the message for phase modulation
        self.phase_integral += 2 * math.pi * self.freq_deviation * self.message * dt

        phase = 2 * math.pi * self.carrier_freq * t + self.phase_integral
        self.output = self.carrier_amplitude * math.cos(phase)

    def getOutput(self, port=0):
        return self.output


class PhaseNoise(Block):
    """Add phase noise to a signal.

    Models oscillator phase noise with -20 dB/decade slope.
    """

    def __init__(self, phase_noise_dbcHz: float = -100.0, offset_freq: float = 10e3):
        super().__init__()
        self.phase_noise_dbcHz = phase_noise_dbcHz
        self.offset_freq = offset_freq
        self.phase_error = 0.0
        self.output = 0.0
        self.input_block = None

        # Random state for noise generation
        import random
        self._random = random.Random()

    def init(self):
        self.phase_error = 0.0
        self.output = 0.0

    def setInput(self, value, port=0):
        self.output = float(value)  # Will be modified

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            signal = self.input_block.getOutput()
        else:
            signal = 0.0

        from ..state import State
        dt = State.dt

        # Generate phase noise
        # Convert phase noise from dBc/Hz to radians RMS
        pn_linear = 10 ** (self.phase_noise_dbcHz / 10)
        phase_rms = math.sqrt(pn_linear * self.offset_freq)

        # Random walk phase noise
        self.phase_error += self._random.gauss(0, phase_rms * dt)

        # Apply phase noise to signal (assuming sinusoidal)
        # For simplicity, add noise to signal directly
        self.output = signal + self.phase_error * 0.01

    def getOutput(self, port=0):
        return self.output


# =============================================================================
# Power Conversions
# =============================================================================


class dBmToWatts(Block):
    """Convert power from dBm to Watts."""

    def __init__(self):
        super().__init__()
        self.output = 0.0
        self.input_block = None

    def init(self):
        self.output = 0.0

    def setInput(self, value, port=0):
        # dBm to Watts: P_W = 10^((P_dBm - 30) / 10)
        self.output = 10 ** ((float(value) - 30) / 10)

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            dbm = self.input_block.getOutput()
            self.output = 10 ** ((dbm - 30) / 10)

    def getOutput(self, port=0):
        return self.output


class WattsTodBm(Block):
    """Convert power from Watts to dBm."""

    def __init__(self):
        super().__init__()
        self.output = 0.0
        self.input_block = None

    def init(self):
        self.output = 0.0

    def setInput(self, value, port=0):
        # Watts to dBm: P_dBm = 10 * log10(P_W) + 30
        watts = float(value)
        if watts > 0:
            self.output = 10 * math.log10(watts) + 30
        else:
            self.output = -200  # Floor value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            watts = self.input_block.getOutput()
            if watts > 0:
                self.output = 10 * math.log10(watts) + 30
            else:
                self.output = -200

    def getOutput(self, port=0):
        return self.output
