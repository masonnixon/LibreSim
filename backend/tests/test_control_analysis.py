"""Tests for control analysis blocks."""

import pytest
import math


# =============================================================================
# Control Analysis Block Tests
# =============================================================================


class TestBodePlot:
    """Tests for the BodePlot analysis block."""

    def test_bode_first_order_system(self):
        """Test Bode plot of first-order system H(s) = 1/(s+1)."""
        from src.osk.blocks.control_analysis import BodePlot

        bode = BodePlot(
            numerator=[1.0],
            denominator=[1.0, 1.0],
            minFrequency=0.01,
            maxFrequency=100.0,
            numPoints=100
        )
        bode.init()

        data = bode.get_bode_data()

        assert len(data['frequencies']) == 100
        assert len(data['magnitude_db']) == 100
        assert len(data['phase_deg']) == 100

        # DC gain should be 0 dB (gain = 1)
        assert abs(data['magnitude_db'][0]) < 0.5

        # At corner frequency (1 rad/s = 0.159 Hz), gain should be -3 dB
        # Find closest frequency to 0.159 Hz
        corner_idx = min(range(len(data['frequencies'])),
                        key=lambda i: abs(data['frequencies'][i] - 0.159))
        assert abs(data['magnitude_db'][corner_idx] + 3) < 1.5  # Within 1.5 dB

    def test_bode_second_order_system(self):
        """Test Bode plot of second-order system."""
        from src.osk.blocks.control_analysis import BodePlot

        # H(s) = 1/(s^2 + s + 1) - second order with wn=1, zeta=0.5
        bode = BodePlot(
            numerator=[1.0],
            denominator=[1.0, 1.0, 1.0],
            numPoints=50
        )
        bode.init()

        data = bode.get_bode_data()

        # Should have computed frequency response
        assert len(data['frequencies']) == 50
        assert data['magnitude_db'][0] == pytest.approx(0, abs=0.5)  # DC gain = 1

    def test_bode_stability_margins(self):
        """Test gain and phase margin computation."""
        from src.osk.blocks.control_analysis import BodePlot

        # Open-loop system with known margins
        # H(s) = 10/(s*(s+1)*(s+2))
        bode = BodePlot(
            numerator=[10.0],
            denominator=[1.0, 3.0, 2.0, 0.0],  # s^3 + 3s^2 + 2s
            minFrequency=0.01,
            maxFrequency=10.0,
            numPoints=200
        )
        bode.init()

        data = bode.get_bode_data()

        # Should compute margins (values depend on specific system)
        # Just verify they are computed or None
        assert data['gain_margin'] is None or isinstance(data['gain_margin'], float)
        assert data['phase_margin'] is None or isinstance(data['phase_margin'], float)

    def test_bode_high_order(self):
        """Test Bode plot of higher-order system."""
        from src.osk.blocks.control_analysis import BodePlot

        # Third-order Butterworth low-pass
        bode = BodePlot(
            numerator=[1.0],
            denominator=[1.0, 2.0, 2.0, 1.0],
            numPoints=100
        )
        bode.init()

        data = bode.get_bode_data()

        # DC gain should be 0 dB
        assert abs(data['magnitude_db'][0]) < 0.5

        # High frequency should have significant attenuation
        assert data['magnitude_db'][-1] < -20


class TestNyquistPlot:
    """Tests for the NyquistPlot analysis block."""

    def test_nyquist_first_order(self):
        """Test Nyquist plot of first-order system."""
        from src.osk.blocks.control_analysis import NyquistPlot

        nyq = NyquistPlot(
            numerator=[1.0],
            denominator=[1.0, 1.0],
            numPoints=100
        )
        nyq.init()

        data = nyq.get_nyquist_data()

        assert len(data['real']) == 100
        assert len(data['imag']) == 100

        # First-order system starts at (1, 0) for low frequency
        assert data['real'][0] == pytest.approx(1.0, abs=0.1)
        assert abs(data['imag'][0]) < 0.1

    def test_nyquist_encirclements_stable(self):
        """Test encirclement count for stable system."""
        from src.osk.blocks.control_analysis import NyquistPlot

        # Stable first-order system - no encirclements of -1
        nyq = NyquistPlot(
            numerator=[1.0],
            denominator=[1.0, 1.0]
        )
        nyq.init()

        data = nyq.get_nyquist_data()
        assert data['encirclements'] == 0

    def test_nyquist_second_order(self):
        """Test Nyquist plot of second-order system."""
        from src.osk.blocks.control_analysis import NyquistPlot

        nyq = NyquistPlot(
            numerator=[1.0],
            denominator=[1.0, 1.0, 1.0],
            numPoints=200
        )
        nyq.init()

        data = nyq.get_nyquist_data()

        assert len(data['real']) == 200
        # Curve should stay in left half of complex plane for stable system


class TestPoleZeroMap:
    """Tests for the PoleZeroMap analysis block."""

    def test_poles_first_order(self):
        """Test pole computation for first-order system."""
        from src.osk.blocks.control_analysis import PoleZeroMap

        pz = PoleZeroMap(
            numerator=[1.0],
            denominator=[1.0, 1.0]  # Pole at s = -1
        )
        pz.init()

        data = pz.get_pole_zero_data()

        assert len(data['poles']) == 1
        assert data['poles'][0][0] == pytest.approx(-1.0, abs=0.01)  # Real part
        assert data['poles'][0][1] == pytest.approx(0.0, abs=0.01)   # Imag part

    def test_poles_second_order_complex(self):
        """Test complex conjugate poles."""
        from src.osk.blocks.control_analysis import PoleZeroMap

        # s^2 + 2s + 5 has poles at -1 +/- 2j
        pz = PoleZeroMap(
            numerator=[1.0],
            denominator=[1.0, 2.0, 5.0]
        )
        pz.init()

        data = pz.get_pole_zero_data()

        assert len(data['poles']) == 2
        # Both poles have real part -1
        assert all(abs(p[0] + 1) < 0.01 for p in data['poles'])

    def test_stability_detection_stable(self):
        """Test stability detection for stable system."""
        from src.osk.blocks.control_analysis import PoleZeroMap

        # Stable system
        pz_stable = PoleZeroMap(
            numerator=[1.0],
            denominator=[1.0, 2.0, 1.0]  # Poles at s = -1 (double)
        )
        pz_stable.init()
        assert pz_stable.get_pole_zero_data()['is_stable'] == True

    def test_stability_detection_unstable(self):
        """Test stability detection for unstable system."""
        from src.osk.blocks.control_analysis import PoleZeroMap

        # Unstable system
        pz_unstable = PoleZeroMap(
            numerator=[1.0],
            denominator=[1.0, -1.0]  # Pole at s = +1
        )
        pz_unstable.init()
        assert pz_unstable.get_pole_zero_data()['is_stable'] == False

    def test_zeros_computation(self):
        """Test zero computation."""
        from src.osk.blocks.control_analysis import PoleZeroMap

        # (s + 2)/(s + 1) has zero at s = -2
        pz = PoleZeroMap(
            numerator=[1.0, 2.0],
            denominator=[1.0, 1.0]
        )
        pz.init()

        data = pz.get_pole_zero_data()

        assert len(data['zeros']) == 1
        assert data['zeros'][0][0] == pytest.approx(-2.0, abs=0.01)

    def test_dominant_pole(self):
        """Test dominant pole identification."""
        from src.osk.blocks.control_analysis import PoleZeroMap

        # Poles at s = -1, -5 - dominant is -1
        pz = PoleZeroMap(
            numerator=[1.0],
            denominator=[1.0, 6.0, 5.0]  # (s+1)(s+5)
        )
        pz.init()

        data = pz.get_pole_zero_data()

        # Dominant pole is the one closest to imaginary axis
        assert data['dominant_pole'] is not None
        assert abs(data['dominant_pole'][0] + 1) < 0.01


class TestStepInfo:
    """Tests for the StepInfo analysis block."""

    def test_step_first_order(self):
        """Test step response of first-order system."""
        from src.osk.blocks.control_analysis import StepInfo

        step = StepInfo(
            numerator=[1.0],
            denominator=[1.0, 1.0],  # Time constant = 1
            simulationTime=10.0,
            numPoints=500
        )
        step.init()

        data = step.get_step_data()

        # Should reach steady state of 1.0
        assert data['steady_state_value'] == pytest.approx(1.0, abs=0.02)

        # No overshoot for first-order system
        assert data['overshoot_percent'] == pytest.approx(0.0, abs=1.0)

        # Rise time should be around 2.2 * tau = 2.2 seconds
        assert data['rise_time'] is not None
        assert 1.5 < data['rise_time'] < 3.5

    def test_step_second_order_underdamped(self):
        """Test step response of underdamped second-order system."""
        from src.osk.blocks.control_analysis import StepInfo

        # wn = 1, zeta = 0.3 -> overshoot expected
        # H(s) = 1/(s^2 + 0.6s + 1)
        step = StepInfo(
            numerator=[1.0],
            denominator=[1.0, 0.6, 1.0],
            simulationTime=20.0,
            numPoints=1000
        )
        step.init()

        data = step.get_step_data()

        # Should have overshoot for underdamped system
        assert data['overshoot_percent'] > 10

        # Steady state should be 1.0
        assert data['steady_state_value'] == pytest.approx(1.0, abs=0.05)

    def test_step_static_gain(self):
        """Test step response of static gain system."""
        from src.osk.blocks.control_analysis import StepInfo

        # H(s) = 2 (static gain)
        step = StepInfo(
            numerator=[2.0],
            denominator=[1.0],
            simulationTime=1.0
        )
        step.init()

        data = step.get_step_data()

        # Should immediately reach steady state of 2.0
        assert data['steady_state_value'] == pytest.approx(2.0, abs=0.01)

    def test_step_settling_time(self):
        """Test settling time computation."""
        from src.osk.blocks.control_analysis import StepInfo

        # First-order system with tau = 1
        # Settling time (2%) should be about 4*tau = 4 seconds
        step = StepInfo(
            numerator=[1.0],
            denominator=[1.0, 1.0],
            simulationTime=10.0,
            numPoints=500,
            settlingPercent=2.0
        )
        step.init()

        data = step.get_step_data()

        assert data['settling_time'] is not None
        assert 3.0 < data['settling_time'] < 5.0

    def test_step_peak_time(self):
        """Test peak time for underdamped system."""
        from src.osk.blocks.control_analysis import StepInfo

        # Underdamped second-order system
        step = StepInfo(
            numerator=[1.0],
            denominator=[1.0, 0.4, 1.0],  # zeta = 0.2
            simulationTime=20.0,
            numPoints=1000
        )
        step.init()

        data = step.get_step_data()

        # Should have a peak
        assert data['peak_time'] is not None
        assert data['peak_time'] > 0
        assert data['peak_value'] > 1.0  # Overshoot means peak > 1
