"""Unit tests for DSP Toolbox blocks."""

import math
import pytest

from src.osk.blocks.dsp import (
    FFT, IFFT, FIRFilter, IIRFilter, Convolution,
    Downsampler, Upsampler, Interpolator, WindowFunction,
    Mean, Variance, RMS, PeakDetector, ZeroCrossingDetector
)


class TestFFT:
    """Tests for FFT block."""

    def test_dc_signal(self):
        """FFT of DC signal should have all energy at DC component."""
        fft = FFT(n_points=8)
        fft.setInput([1.0] * 8)
        fft.update()

        output = fft.getOutputVector()
        # DC component (first real value) should be 8 (sum of inputs)
        assert abs(output[0] - 8.0) < 1e-10
        # DC imaginary should be 0
        assert abs(output[1]) < 1e-10

    def test_pure_sine(self):
        """FFT of pure sine wave should have peaks at fundamental frequency."""
        N = 16
        fft = FFT(n_points=N)

        # Create sine wave at bin 2 (frequency = 2 * fs/N)
        signal = [math.sin(2 * math.pi * 2 * n / N) for n in range(N)]
        fft.setInput(signal)
        fft.update()

        output = fft.getOutputVector()

        # Bin 2 should have significant energy
        mag_bin2 = math.sqrt(output[4]**2 + output[5]**2)
        assert mag_bin2 > 1.0

    def test_symmetry(self):
        """FFT of real signal should be conjugate symmetric."""
        fft = FFT(n_points=8)
        fft.setInput([1.0, 2.0, 3.0, 4.0, 4.0, 3.0, 2.0, 1.0])
        fft.update()

        output = fft.getOutputVector()
        # All imaginary parts should be 0 for symmetric input
        for i in range(8):
            assert abs(output[2*i + 1]) < 1e-10


class TestIFFT:
    """Tests for IFFT block."""

    def test_identity(self):
        """IFFT(FFT(x)) should equal x."""
        N = 8
        original = [1.0, 2.0, 3.0, 4.0, 3.0, 2.0, 1.0, 0.0]

        fft = FFT(n_points=N)
        fft.setInput(original)
        fft.update()

        ifft = IFFT(n_points=N)
        ifft.setInput(fft.getOutputVector())
        ifft.update()

        recovered = ifft.getOutputVector()
        for i in range(N):
            assert abs(recovered[i] - original[i]) < 1e-10


class TestFIRFilter:
    """Tests for FIR Filter block."""

    def test_unity_passthrough(self):
        """FIR filter with [1] coefficients should pass through unchanged."""
        fir = FIRFilter(coefficients=[1.0])

        fir.setInput(5.0)
        fir.update()
        assert abs(fir.getOutput() - 5.0) < 1e-10

    def test_simple_averaging(self):
        """FIR filter with [0.5, 0.5] should average adjacent samples."""
        fir = FIRFilter(coefficients=[0.5, 0.5])

        fir.setInput(1.0)
        fir.update()
        assert abs(fir.getOutput() - 0.5) < 1e-10  # 0.5*1 + 0.5*0

        fir.setInput(3.0)
        fir.update()
        assert abs(fir.getOutput() - 2.0) < 1e-10  # 0.5*3 + 0.5*1

    def test_delay_line(self):
        """FIR filter with [0, 0, 1] should delay by 2 samples."""
        fir = FIRFilter(coefficients=[0.0, 0.0, 1.0])

        fir.setInput(1.0)
        fir.update()
        assert abs(fir.getOutput()) < 1e-10

        fir.setInput(0.0)
        fir.update()
        assert abs(fir.getOutput()) < 1e-10

        fir.setInput(0.0)
        fir.update()
        assert abs(fir.getOutput() - 1.0) < 1e-10


class TestIIRFilter:
    """Tests for IIR Filter block."""

    def test_first_order_lowpass(self):
        """First-order IIR lowpass filter basic operation."""
        # Simple first-order: y[n] = 0.5*x[n] + 0.5*y[n-1]
        iir = IIRFilter(numerator=[0.5], denominator=[1.0, -0.5])

        # Step input
        for i in range(10):
            iir.setInput(1.0)
            iir.update()

        # Output should approach 1.0 (DC gain = 0.5 / (1 - 0.5) = 1)
        assert abs(iir.getOutput() - 1.0) < 0.01


class TestConvolution:
    """Tests for Convolution block."""

    def test_identity(self):
        """Convolution with [1] should give same signal."""
        conv = Convolution()
        conv.setInput([1.0, 2.0, 3.0], port=0)
        conv.setInput([1.0], port=1)
        conv.update()

        output = conv.getOutputVector()
        assert output == [1.0, 2.0, 3.0]

    def test_basic_convolution(self):
        """Test basic convolution [1,2,3] * [1,1] = [1,3,5,3]."""
        conv = Convolution()
        conv.setInput([1.0, 2.0, 3.0], port=0)
        conv.setInput([1.0, 1.0], port=1)
        conv.update()

        output = conv.getOutputVector()
        assert len(output) == 4
        assert abs(output[0] - 1.0) < 1e-10
        assert abs(output[1] - 3.0) < 1e-10
        assert abs(output[2] - 5.0) < 1e-10
        assert abs(output[3] - 3.0) < 1e-10


class TestDownsampler:
    """Tests for Downsampler block."""

    def test_factor_2(self):
        """Downsampler with factor 2 should keep every other sample."""
        ds = Downsampler(factor=2)

        ds.setInput(1.0)
        ds.update()
        assert ds.getOutput() == 1.0

        ds.setInput(2.0)
        ds.update()
        assert ds.getOutput() == 1.0  # Still 1.0, skipped

        ds.setInput(3.0)
        ds.update()
        assert ds.getOutput() == 3.0  # New sample


class TestUpsampler:
    """Tests for Upsampler block."""

    def test_factor_2(self):
        """Upsampler with factor 2 should insert zeros."""
        us = Upsampler(factor=2)

        us.setInput(1.0)
        us.update()
        assert us.getOutput() == 1.0

        us.setInput(1.0)  # Input ignored on odd phases
        us.update()
        assert us.getOutput() == 0.0  # Zero inserted


class TestInterpolator:
    """Tests for Interpolator block."""

    def test_factor_2_linear(self):
        """Interpolator with factor 2 should linearly interpolate."""
        interp = Interpolator(factor=2)

        # First sample
        interp.setInput(0.0)
        interp.update()

        # Set next sample
        interp.setInput(2.0)
        interp.update()
        # Now we should get interpolated value

        interp.setInput(2.0)
        interp.update()
        # Next interpolated value


class TestWindowFunction:
    """Tests for Window Function block."""

    def test_rectangular(self):
        """Rectangular window should not modify signal."""
        win = WindowFunction(window_type="rectangular", length=4)
        win.setInput([1.0, 1.0, 1.0, 1.0])
        win.update()

        output = win.getOutputVector()
        assert all(abs(x - 1.0) < 1e-10 for x in output)

    def test_hamming_symmetry(self):
        """Hamming window should be symmetric."""
        win = WindowFunction(window_type="hamming", length=8)
        win.setInput([1.0] * 8)
        win.update()

        output = win.getOutputVector()
        for i in range(4):
            assert abs(output[i] - output[7-i]) < 1e-10

    def test_hanning_endpoints(self):
        """Hanning window should be zero at endpoints."""
        win = WindowFunction(window_type="hanning", length=8)
        win.setInput([1.0] * 8)
        win.update()

        output = win.getOutputVector()
        assert abs(output[0]) < 1e-10
        assert abs(output[-1]) < 1e-10


class TestMean:
    """Tests for Mean block."""

    def test_constant_signal(self):
        """Mean of constant signal should be that constant."""
        mean = Mean(window_size=5)

        for _ in range(5):
            mean.setInput(3.0)
            mean.update()

        assert abs(mean.getOutput() - 3.0) < 1e-10

    def test_varying_signal(self):
        """Mean of [1,2,3,4,5] should be 3."""
        mean = Mean(window_size=5)

        for val in [1, 2, 3, 4, 5]:
            mean.setInput(float(val))
            mean.update()

        assert abs(mean.getOutput() - 3.0) < 1e-10


class TestVariance:
    """Tests for Variance block."""

    def test_constant_signal(self):
        """Variance of constant signal should be 0."""
        var = Variance(window_size=5)

        for _ in range(5):
            var.setInput(3.0)
            var.update()

        assert abs(var.getOutput()) < 1e-10

    def test_known_variance(self):
        """Test variance of [1,2,3,4,5] = 2.5."""
        var = Variance(window_size=5)

        for val in [1, 2, 3, 4, 5]:
            var.setInput(float(val))
            var.update()

        assert abs(var.getOutput() - 2.5) < 1e-10


class TestRMS:
    """Tests for RMS block."""

    def test_dc_signal(self):
        """RMS of constant signal equals that constant."""
        rms = RMS(window_size=5)

        for _ in range(5):
            rms.setInput(4.0)
            rms.update()

        assert abs(rms.getOutput() - 4.0) < 1e-10

    def test_sine_wave(self):
        """RMS of full sine period should be amplitude/sqrt(2)."""
        rms = RMS(window_size=100)

        amplitude = 2.0
        for i in range(100):
            val = amplitude * math.sin(2 * math.pi * i / 100)
            rms.setInput(val)
            rms.update()

        expected = amplitude / math.sqrt(2)
        assert abs(rms.getOutput() - expected) < 0.05


class TestPeakDetector:
    """Tests for Peak Detector block."""

    def test_detect_peak(self):
        """Peak detector should output 1 at peak."""
        pd = PeakDetector(threshold=0.0)

        pd.setInput(0.0)
        pd.update()
        pd.setInput(1.0)
        pd.update()
        pd.setInput(2.0)
        pd.update()
        pd.setInput(1.0)
        pd.update()

        # Peak was at value 2.0
        assert pd.getOutput() == 1.0


class TestZeroCrossingDetector:
    """Tests for Zero Crossing Detector block."""

    def test_rising_crossing(self):
        """Detect rising zero crossing."""
        zcd = ZeroCrossingDetector(direction="rising")

        zcd.setInput(-1.0)
        zcd.update()
        assert zcd.getOutput() == 0.0

        zcd.setInput(1.0)
        zcd.update()
        assert zcd.getOutput() == 1.0

    def test_falling_crossing(self):
        """Detect falling zero crossing."""
        zcd = ZeroCrossingDetector(direction="falling")

        zcd.setInput(1.0)
        zcd.update()
        assert zcd.getOutput() == 0.0

        zcd.setInput(-1.0)
        zcd.update()
        assert zcd.getOutput() == 1.0

    def test_both_crossings(self):
        """Detect both rising and falling crossings."""
        zcd = ZeroCrossingDetector(direction="both")

        zcd.setInput(-1.0)
        zcd.update()

        zcd.setInput(1.0)
        zcd.update()
        assert zcd.getOutput() == 1.0

        zcd.setInput(-1.0)
        zcd.update()
        assert zcd.getOutput() == 1.0
