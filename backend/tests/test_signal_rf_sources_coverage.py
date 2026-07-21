"""Behavioral edge coverage for signal-processing, RF, and source blocks."""

import math

import pytest

from src.osk.blocks.rf import (
    AMModulator,
    FMModulator,
    RFBudgetElement,
    RFFilter,
    RFMixer,
    SParameterNetwork,
)
from src.osk.blocks.signal_processing import (
    AnalogFilter,
    Backlash,
    BandPassFilter,
    HighPassFilter,
    LowPassFilter,
    NotchFilter,
    RateLimiter,
    _bessel_poles,
)
from src.osk.blocks.sources import (
    BandLimitedWhiteNoise,
    Constant,
    FromWorkspace,
    RepeatingSequence,
    SignalGenerator,
    UniformNoise,
    WhiteNoise,
)
from src.osk.context import SimContext


class Source:
    def __init__(self, value=0.0, vector=None):
        self.value = value
        self.vector = vector

    def getOutput(self, port=0):
        return self.value

    def getOutputVector(self):
        return self.vector


def test_first_order_filters_invalid_timing_and_connected_source():
    context = SimContext(dt=0.0)

    low = LowPassFilter(cutoff_freq=0.0)
    low.context = context
    low.init()
    assert low.alpha == 1.0
    low.setInput(3.0)
    low.update()
    assert low.getOutput() == 3.0

    high = HighPassFilter(cutoff_freq=0.0)
    high.context = context
    high.init()
    assert high.alpha == 1.0
    high.connectInput(Source(3.0), source_port=2)
    high.update()
    assert high.getOutput() == 3.0
    high.context.dt = 0.1
    high.cutoff_freq = 1.0
    high.update()
    expected_alpha = (1 / (2 * math.pi)) / (1 / (2 * math.pi) + 0.1)
    assert high.alpha == pytest.approx(expected_alpha)


def test_bandpass_fallbacks_and_backlash_initial_state():
    limiter = RateLimiter(rising_limit=2.0, falling_limit=-3.0)
    assert (limiter.rising_rate, limiter.falling_rate) == (2.0, -3.0)

    block = BandPassFilter(low_cutoff=0.0, high_cutoff=0.0)
    block.context = SimContext(dt=0.0)
    block.setInput(2.5)
    block.update()
    assert block.getOutput() == 2.5

    backlash = Backlash(initial_output=4.0)
    backlash.init()
    assert backlash.getOutput() == 4.0


@pytest.mark.parametrize(
    ("design", "response", "order"),
    [
        ("unknown", "lowpass", 1),
        ("bessel", "highpass", 1),
        ("chebyshev2", "bandpass", 2),
        ("butterworth", "bandstop", 2),
    ],
)
def test_analog_filter_design_variants_produce_finite_sections(design, response, order):
    block = AnalogFilter(design=design, response=response, order=order)
    block._design_filter(0.0)
    assert block._biquads == []
    block._design_filter(0.01)
    assert block._biquads
    assert all(math.isfinite(section["b0"]) for section in block._biquads)


def test_bessel_high_order_and_invalid_notch_design():
    poles = _bessel_poles(6)
    assert len(poles) == 6
    assert all(pole.real < 0 for pole in poles)

    notch = NotchFilter(notch_freq=0.0)
    notch._design_notch(0.1)
    assert (notch.b0, notch.b1, notch.b2) == (1.0, 0.0, 1.0)


def test_rf_filter_modes_connections_and_invalid_ports():
    mixer = RFMixer(conversion_loss_db=2.0)
    mixer.connectInput(Source(12.0), 0)
    mixer.connectInput(Source(3.0), 1)
    mixer.connectInput(Source(99.0), 2)
    mixer.update()
    assert mixer.getOutput() == 10.0

    expected = {
        "bandpass": (1.0, 31.0),
        "bandstop": (31.0, 1.0),
        "lowpass": (1.0, 31.0),
        "highpass": (31.0, 1.0),
        "unknown": (1.0, 1.0),
    }
    for mode, attenuations in expected.items():
        filt = RFFilter(
            center_freq_hz=10.0,
            bandwidth_hz=4.0,
            insertion_loss_db=1.0,
            rejection_db=30.0,
            filter_type=mode,
        )
        assert (
            filt._compute_attenuation(10.0 if mode in {"bandpass", "bandstop"} else 5.0)
            == attenuations[0]
        )
        assert filt._compute_attenuation(20.0) == attenuations[1]
        filt.connectInput(Source(50.0), 0)
        filt.connectInput(Source(20.0), 1)
        filt.connectInput(Source(99.0), 2)
        filt.update()
        assert filt.getOutput() == pytest.approx(50.0 - attenuations[1])


def test_s_parameter_invalid_shapes_and_budget_cascade_edges():
    network = SParameterNetwork()
    network.setInput([1.0])
    network.connectInput(Source(vector=[2.0, 3.0]))
    network.update()
    assert network.getOutputVector() == [0.0, 0.0, 2.0, 3.0]
    assert network.getOutput() == 0.0
    assert network.getOutput(9) == 0.0
    network.connectInput(Source(vector=[1.0]))
    network.update()
    assert network.getOutputVector() == [0.0, 0.0, 2.0, 3.0]

    first = RFBudgetElement(gain_db=10.0, noise_figure_db=2.0)
    first.setInput(1.0, 4)
    first.connectInput(Source(99.0), 4)
    first.update()
    assert first.getOutputVector() == pytest.approx([10.0, 10.0, 2.0])
    assert first.getOutput(4) == 0.0

    cascaded = RFBudgetElement(gain_db=1.0, noise_figure_db=3.0)
    for port, value in enumerate((5.0, -200.0, 2.0)):
        cascaded.connectInput(Source(value), port)
    cascaded.update()
    expected_factor = 10 ** (2.0 / 10) + 10 ** (3.0 / 10) - 1
    assert cascaded.getOutput(2) == pytest.approx(10 * math.log10(expected_factor))


def test_modulators_external_and_connected_inputs():
    am = AMModulator(modulation_index=0.5)
    am.setInput(2.0, 0)
    am.setInput(3.0, 1)
    am.setInput(99.0, 2)
    am.connectInput(Source(99.0), 2)
    am.update()
    assert am.getOutput() == 6.0

    carrier = Source(4.0)
    am.connectInput(Source(1.0), 0)
    am.connectInput(carrier, 1)
    am.update()
    assert am.getOutput() == 6.0

    fm = FMModulator(carrier_freq=0.0, carrier_amplitude=2.0, freq_deviation=1.0)
    fm.context = SimContext(t=0.0, dt=0.25)
    fm.connectInput(Source(1.0))
    fm.update()
    assert fm.phase_integral == pytest.approx(math.pi / 2)
    assert fm.getOutput() == pytest.approx(0.0, abs=1e-12)


def test_constant_parsing_noise_stage_guards_and_sequence_edges():
    parser = Constant()
    assert parser._parse_value("[bad]") == 1.0
    assert parser._parse_value("bad,also-bad") == 1.0
    assert parser._parse_value("1,") == 1.0
    assert parser._parse_value(object()) == 1.0

    context = SimContext(t=1.0, ready=0)
    uniform = UniformNoise(seed=1)
    uniform.context = context
    uniform.output = 7.0
    uniform.update()
    assert uniform.getOutput() == 7.0

    white = WhiteNoise(seed=1)
    white.context = context
    white.output = 6.0
    white.update()
    assert white.getOutput() == 6.0

    band_limited = BandLimitedWhiteNoise(seed=1)
    band_limited.context = context
    band_limited.output = 8.0
    band_limited.update()
    assert band_limited.getOutput() == 8.0

    sequence = RepeatingSequence([0.0, 0.0, 1.0], [2.0, 3.0, 4.0])
    assert sequence._interpolate(0.0) == 2.0
    assert sequence._interpolate(2.0) == 4.0


def test_workspace_interpolation_and_random_generator_stage_guard():
    empty = FromWorkspace()
    empty.time_data = []
    empty.value_data = []
    assert empty._interpolate(1.0) == 0.0
    duplicate = FromWorkspace([0.0, 0.0, 1.0], [2.0, 3.0, 4.0])
    assert duplicate._interpolate(0.0) == 2.0
    assert duplicate._interpolate(2.0) == 4.0

    generator = SignalGenerator(wave_type="random", amplitude=2.0, frequency=1.0)
    generator.context = SimContext(t=0.25, ready=0)
    generator.output = 1.25
    generator.update()
    assert generator.getOutput() == 1.25
