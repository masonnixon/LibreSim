"""Unit tests for RF Toolbox blocks."""

import math

from src.osk.blocks.rf import (
    AMModulator,
    Attenuator,
    RFAmplifier,
    RFBudgetElement,
    RFFilter,
    RFMixer,
    SParameterNetwork,
    WattsTodBm,
    dBmToWatts,
)


class TestRFAmplifier:
    """Tests for RF Amplifier block."""

    def test_linear_gain(self):
        """Amplifier should add gain in dB."""
        amp = RFAmplifier(gain_db=20.0, p1db_dbm=50.0)

        amp.setInput(-10.0)  # -10 dBm input
        amp.update()

        # Expected output: -10 + 20 = 10 dBm
        assert abs(amp.getOutput() - 10.0) < 0.1

    def test_compression_at_p1db(self):
        """Amplifier should compress near P1dB."""
        amp = RFAmplifier(gain_db=20.0, p1db_dbm=20.0)

        # Input that would result in output near P1dB
        amp.setInput(5.0)  # Would be 25 dBm ideal
        amp.update()

        # Should be compressed below 25 dBm
        assert amp.getOutput() < 25.0
        assert amp.getOutput() > 20.0


class TestRFMixer:
    """Tests for RF Mixer block."""

    def test_conversion_loss(self):
        """Mixer should apply conversion loss."""
        mixer = RFMixer(conversion_loss_db=6.0)

        mixer.setInput(-10.0, port=0)  # RF input
        mixer.setInput(10.0, port=1)  # LO input (not used for power calc)
        mixer.update()

        # Output should be RF - conversion loss
        assert abs(mixer.getOutput() - (-16.0)) < 0.1


class TestRFFilter:
    """Tests for RF Filter block."""

    def test_bandpass_passband(self):
        """Bandpass filter should pass in-band frequencies."""
        filt = RFFilter(
            filter_type="bandpass",
            center_freq_hz=1e9,
            bandwidth_hz=100e6,
            insertion_loss_db=1.0,
            rejection_db=40.0,
        )

        # In-band frequency
        filt.setInput(-10.0, port=0)  # Power
        filt.setInput(1e9, port=1)  # Frequency at center
        filt.update()

        assert abs(filt.getOutput() - (-11.0)) < 0.1  # Just insertion loss

    def test_bandpass_stopband(self):
        """Bandpass filter should reject out-of-band frequencies."""
        filt = RFFilter(
            filter_type="bandpass",
            center_freq_hz=1e9,
            bandwidth_hz=100e6,
            insertion_loss_db=1.0,
            rejection_db=40.0,
        )

        # Out-of-band frequency
        filt.setInput(-10.0, port=0)
        filt.setInput(2e9, port=1)  # Way out of band
        filt.update()

        assert abs(filt.getOutput() - (-51.0)) < 0.1  # Insertion + rejection

    def test_lowpass(self):
        """Lowpass filter behavior."""
        filt = RFFilter(
            filter_type="lowpass", center_freq_hz=1e9, insertion_loss_db=0.5, rejection_db=30.0
        )

        # Below cutoff
        filt.setInput(0.0, port=0)
        filt.setInput(500e6, port=1)
        filt.update()
        assert abs(filt.getOutput() - (-0.5)) < 0.1

        # Above cutoff
        filt.setInput(0.0, port=0)
        filt.setInput(2e9, port=1)
        filt.update()
        assert abs(filt.getOutput() - (-30.5)) < 0.1


class TestSParameterNetwork:
    """Tests for S-Parameter Network block."""

    def test_through_connection(self):
        """Default S-params (S21=1) should pass signal through."""
        spn = SParameterNetwork()  # Default is ideal through

        # Input: a1 = 1 + 0j
        spn.setInput([1.0, 0.0])
        spn.update()

        output = spn.getOutputVector()
        # b2 = S21 * a1 = 1 * 1 = 1
        assert abs(output[2] - 1.0) < 1e-10
        assert abs(output[3]) < 1e-10

    def test_attenuator_s_params(self):
        """S-params representing 3dB attenuator."""
        # 3dB attenuation: |S21|^2 = 0.5, so |S21| = 0.707
        s21_mag = 10 ** (-3 / 20)  # 0.707
        spn = SParameterNetwork(s_params=[0, 0, s21_mag, 0, s21_mag, 0, 0, 0])

        spn.setInput([1.0, 0.0])
        spn.update()

        output = spn.getOutputVector()
        b2_mag = math.sqrt(output[2] ** 2 + output[3] ** 2)
        assert abs(b2_mag - s21_mag) < 1e-6


class TestRFBudgetElement:
    """Tests for RF Budget Element block."""

    def test_first_element_gain(self):
        """First element should apply its gain and NF."""
        elem = RFBudgetElement(gain_db=10.0, noise_figure_db=3.0)

        elem.setInput(-20.0, port=0)  # Input power
        elem.setInput(0.0, port=1)  # Cascade gain (0 for first)
        elem.setInput(0.0, port=2)  # Cascade NF (0 for first)
        elem.update()

        output = elem.getOutputVector()
        assert abs(output[0] - (-10.0)) < 0.1  # Output power
        assert abs(output[1] - 10.0) < 0.1  # Cascade gain
        assert abs(output[2] - 3.0) < 0.1  # NF

    def test_cascaded_gain(self):
        """Cascaded elements should sum gains."""
        # First element
        elem1 = RFBudgetElement(gain_db=10.0, noise_figure_db=3.0)
        elem1.setInput(-20.0, port=0)
        elem1.setInput(0.0, port=1)
        elem1.setInput(0.0, port=2)
        elem1.update()

        # Second element
        elem2 = RFBudgetElement(gain_db=15.0, noise_figure_db=5.0)
        out1 = elem1.getOutputVector()
        elem2.setInput(out1[0], port=0)
        elem2.setInput(out1[1], port=1)
        elem2.setInput(out1[2], port=2)
        elem2.update()

        output = elem2.getOutputVector()
        assert abs(output[0] - 5.0) < 0.1  # -20 + 10 + 15 = 5 dBm
        assert abs(output[1] - 25.0) < 0.1  # 10 + 15 = 25 dB


class TestAttenuator:
    """Tests for Attenuator block."""

    def test_attenuation(self):
        """Attenuator should reduce power by specified amount."""
        atten = Attenuator(attenuation_db=10.0)

        atten.setInput(0.0)  # 0 dBm
        atten.update()

        assert abs(atten.getOutput() - (-10.0)) < 0.1


class TestAMModulator:
    """Tests for AM Modulator block."""

    def test_carrier_at_zero_modulation(self):
        """AM with zero message should produce carrier only."""
        from src.osk.state import State

        State.t = 0.0

        am = AMModulator(carrier_freq=1e6, carrier_amplitude=1.0, modulation_index=0.5)
        am.setInput(0.0)  # Zero message
        am.update()

        # At t=0, cos(0) = 1, so output should be amplitude
        assert abs(am.getOutput() - 1.0) < 1e-6

    def test_modulation_envelope(self):
        """AM modulation should affect envelope."""
        from src.osk.state import State

        State.t = 0.0

        am = AMModulator(carrier_freq=1e6, carrier_amplitude=1.0, modulation_index=1.0)

        # Full positive modulation
        am.setInput(1.0)
        am.update()
        assert abs(am.getOutput() - 2.0) < 1e-6  # (1 + 1*1) * 1 = 2


class TestdBmToWatts:
    """Tests for dBm to Watts converter."""

    def test_0dbm(self):
        """0 dBm should equal 1 mW."""
        conv = dBmToWatts()
        conv.setInput(0.0)
        conv.update()

        assert abs(conv.getOutput() - 0.001) < 1e-9

    def test_30dbm(self):
        """30 dBm should equal 1 W."""
        conv = dBmToWatts()
        conv.setInput(30.0)
        conv.update()

        assert abs(conv.getOutput() - 1.0) < 1e-6

    def test_negative_dbm(self):
        """-30 dBm should equal 1 uW."""
        conv = dBmToWatts()
        conv.setInput(-30.0)
        conv.update()

        assert abs(conv.getOutput() - 1e-6) < 1e-12


class TestWattsTodBm:
    """Tests for Watts to dBm converter."""

    def test_1mw(self):
        """1 mW should equal 0 dBm."""
        conv = WattsTodBm()
        conv.setInput(0.001)
        conv.update()

        assert abs(conv.getOutput() - 0.0) < 1e-6

    def test_1w(self):
        """1 W should equal 30 dBm."""
        conv = WattsTodBm()
        conv.setInput(1.0)
        conv.update()

        assert abs(conv.getOutput() - 30.0) < 1e-6

    def test_roundtrip(self):
        """dBm -> W -> dBm should be identity."""
        dbm_to_w = dBmToWatts()
        w_to_dbm = WattsTodBm()

        original = 15.0
        dbm_to_w.setInput(original)
        dbm_to_w.update()

        w_to_dbm.setInput(dbm_to_w.getOutput())
        w_to_dbm.update()

        assert abs(w_to_dbm.getOutput() - original) < 1e-6
