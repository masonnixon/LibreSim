"""Behavioral coverage for DSP source protocols and uncommon modes."""

import math

import pytest

from src.osk.blocks.dsp import (
    FFT,
    IFFT,
    RMS,
    Convolution,
    Downsampler,
    FIRFilter,
    IIRFilter,
    Interpolator,
    Mean,
    PeakDetector,
    Upsampler,
    Variance,
    WindowFunction,
    ZeroCrossingDetector,
)


class Source:
    def __init__(self, scalar=0.0, vector=None):
        self.scalar = scalar
        self.vector = vector

    def getOutput(self, port=0):
        return self.scalar

    def getOutputVector(self):
        return self.vector


def test_fft_and_ifft_source_protocol_and_input_guards():
    fft = FFT(2)
    fft.init()
    fft.setInput(12.0)
    fft.connectInput(Source(vector=[1.0]))
    fft.update()
    assert fft.getOutputVector() == pytest.approx([1.0, 0.0, 1.0, 0.0])
    assert fft.getOutput() == pytest.approx(1.0)
    assert fft.getOutput(9) == 0.0

    fft.connectInput(Source(vector=None))
    fft.update()
    assert fft.getOutputVector() == pytest.approx([1.0, 0.0, 1.0, 0.0])

    ifft = IFFT(2)
    ifft.init()
    ifft.setInput(12.0)
    ifft.connectInput(Source(vector=[2.0, 0.0]))
    ifft.update()
    assert ifft.getOutputVector() == pytest.approx([1.0, 1.0])
    assert ifft.getOutput() == pytest.approx(1.0)
    assert ifft.getOutput(9) == 0.0
    ifft.connectInput(Source(vector=None))
    ifft.update()
    assert ifft.output == pytest.approx([1.0, 1.0])


def test_fir_and_iir_connected_sources_and_zero_denominator():
    fir = FIRFilter([0.25, 0.75])
    fir.init()
    fir.connectInput(Source(scalar=4.0))
    fir.update()
    assert fir.getOutput() == pytest.approx(1.0)

    iir = IIRFilter([2.0], [2.0, -1.0])
    assert iir.numerator == [1.0]
    assert iir.denominator == [1.0, -0.5]
    iir.init()
    iir.connectInput(Source(scalar=3.0))
    iir.update()
    assert iir.getOutput() == pytest.approx(3.0)

    unnormalizable = IIRFilter([2.0], [0.0])
    unnormalizable.setInput(3.0)
    unnormalizable.update()
    assert unnormalizable.getOutput() == pytest.approx(6.0)


def test_convolution_source_protocol_empty_and_port_behavior():
    convolution = Convolution()
    convolution.init()
    convolution.setInput(4.0)
    convolution.connectInput(Source(vector=[1.0, 2.0]), 0)
    convolution.connectInput(Source(vector=[1.0, -1.0]), 1)
    convolution.connectInput(Source(vector=[99.0]), 2)
    convolution.update()
    assert convolution.getOutputVector() == pytest.approx([1.0, 1.0, -2.0])
    assert convolution.getOutput() == pytest.approx(1.0)
    assert convolution.getOutput(9) == 0.0

    convolution.connectInput(Source(vector=None), 0)
    convolution.input_blocks[1] = None
    convolution.kernel = []
    convolution.update()
    assert convolution.getOutputVector() == []


def test_rate_conversion_connected_source_phases():
    downsampler = Downsampler(2)
    downsampler.init()
    downsampler.connectInput(Source(scalar=5.0))
    downsampler.update()
    assert downsampler.getOutput() == 5.0
    downsampler.input_block.scalar = 9.0
    downsampler.update()
    assert downsampler.getOutput() == 5.0

    upsampler = Upsampler(2)
    upsampler.init()
    upsampler.connectInput(Source(scalar=4.0))
    upsampler.update()
    assert upsampler.getOutput() == 4.0
    upsampler.update()
    assert upsampler.getOutput() == 0.0

    interpolator = Interpolator(2)
    interpolator.init()
    interpolator.connectInput(Source(scalar=4.0))
    interpolator.update()
    assert interpolator.getOutput() == 0.0
    interpolator.update()
    assert interpolator.getOutput() == pytest.approx(2.0)


@pytest.mark.parametrize(
    ("window_type", "expected"),
    [
        ("blackman", [0.0, 0.63, 0.63, 0.0]),
        ("unknown", [1.0, 1.0, 1.0, 1.0]),
    ],
)
def test_additional_window_modes(window_type, expected):
    window = WindowFunction(window_type, 4)
    window.setInput([1.0] * 4)
    window.update()
    assert window.getOutputVector() == pytest.approx(expected, abs=1e-12)


def test_kaiser_window_source_protocol_and_bessel_full_series():
    window = WindowFunction("kaiser", 5, beta=5.0)
    window.init()
    window.setInput(12.0)
    window.connectInput(Source(vector=[1.0, 1.0]))
    window.update()
    assert window.window[0] == pytest.approx(window.window[-1])
    assert window.output[0] == pytest.approx(window.window[0])
    assert window.output[2] == 0.0
    assert window.getOutput() == pytest.approx(window.window[0])
    assert window.getOutput(9) == 0.0
    window.connectInput(Source(vector=None))
    window.update()
    assert window.getOutputVector() == pytest.approx(window.output)
    assert window._bessel_i0(100.0) > 1e20


@pytest.mark.parametrize(
    ("block_type", "empty_expected", "samples", "expected"),
    [
        (Mean, 0.0, [1.0, 3.0, 5.0], 4.0),
        (Variance, 0.0, [1.0, 3.0, 5.0], 2.0),
        (RMS, 0.0, [3.0, 4.0, 0.0], math.sqrt(8.0)),
    ],
)
def test_running_statistics_empty_connected_and_eviction(
    block_type, empty_expected, samples, expected
):
    block = block_type(window_size=2)
    block.init()
    block.update()
    assert block.getOutput() == empty_expected
    for sample in samples:
        block.setInput(sample)
    assert block.buffer == samples[-2:]
    block.init()
    source = Source()
    block.connectInput(source)
    for sample in samples:
        source.scalar = sample
        block.update()
    assert block.buffer == samples[-2:]
    assert block.getOutput() == pytest.approx(expected)


def test_peak_and_zero_crossing_connected_sources():
    peak = PeakDetector(threshold=1.0)
    peak.init()
    source = Source()
    peak.connectInput(source)
    for sample in [0.0, 3.0, 0.0]:
        source.scalar = sample
        peak.update()
    assert peak.getOutput() == 1.0

    for direction, samples, expected in [
        ("rising", [1.0, 2.0], [1.0, 0.0]),
        ("falling", [-1.0, -2.0], [1.0, 0.0]),
        ("both", [-1.0, 1.0], [1.0, 1.0]),
    ]:
        detector = ZeroCrossingDetector(direction)
        detector.init()
        source = Source()
        detector.connectInput(source)
        actual = []
        for sample in samples:
            source.scalar = sample
            detector.update()
            actual.append(detector.getOutput())
        assert actual == expected
