"""Tests for OSK simulation blocks."""

import math

import pytest

from src.osk.blocks.continuous import Derivative, Integrator, TransferFunction
from src.osk.blocks.math_ops import (
    Abs,
    DeadZone,
    Demux,
    Gain,
    MathFunction,
    Mux,
    Product,
    Reshape,
    Saturation,
    Sign,
    Sum,
    Switch,
    Trigonometry,
)
from src.osk.blocks.sinks import Display, Scope, ToWorkspace
from src.osk.blocks.sources import Clock, Constant, PulseGenerator, Ramp, SineWave, Step
from src.osk.blocks.subsystems import Outport
from src.osk.state import State


# =============================================================================
# Source Block Tests
# =============================================================================


class TestConstantBlock:
    """Tests for the Constant block."""

    def test_constant_output(self):
        """Test that Constant block outputs the configured value."""
        const = Constant(value=5.0)
        const.init()
        assert const.getOutput() == 5.0

    def test_constant_string_value(self):
        """Test that Constant block parses string values."""
        const = Constant(value="3.14")
        const.init()
        assert const.getOutput() == pytest.approx(3.14)

    def test_constant_default_value(self):
        """Test that Constant block has default value of 1.0."""
        const = Constant()
        const.init()
        assert const.getOutput() == 1.0

    def test_constant_invalid_string(self):
        """Test that Constant block handles invalid string values."""
        const = Constant(value="invalid")
        const.init()
        assert const.getOutput() == 1.0  # Default value

    def test_constant_none_value(self):
        """Test that Constant block handles None value."""
        const = Constant(value=None)
        const.init()
        assert const.getOutput() == 1.0

    def test_constant_update(self):
        """Test that Constant block update maintains value."""
        const = Constant(value=42.0)
        const.init()
        const.update()
        assert const.getOutput() == 42.0

    def test_constant_list_value(self):
        """Test that Constant block handles list values."""
        const = Constant(value=[1.0, 2.0, 3.0])
        const.init()
        assert const.getOutput(0) == 1.0
        assert const.getOutput(1) == 2.0
        assert const.getOutput(2) == 3.0
        vec = const.getOutputVector()
        assert vec == [1.0, 2.0, 3.0]

    def test_constant_tuple_value(self):
        """Test that Constant block handles tuple values."""
        const = Constant(value=(4.0, 5.0))
        const.init()
        assert const.getOutput(0) == 4.0
        assert const.getOutput(1) == 5.0
        assert const.getOutputVector() == [4.0, 5.0]

    def test_constant_string_array_comma(self):
        """Test that Constant block parses comma-separated array strings."""
        const = Constant(value="[1, 2, 3, 4]")
        const.init()
        assert const.getOutput(0) == 1.0
        assert const.getOutput(1) == 2.0
        assert const.getOutput(2) == 3.0
        assert const.getOutput(3) == 4.0
        assert const.getOutputVector() == [1.0, 2.0, 3.0, 4.0]

    def test_constant_string_array_space(self):
        """Test that Constant block parses space-separated array strings."""
        const = Constant(value="[10 20 30]")
        const.init()
        assert const.getOutputVector() == [10.0, 20.0, 30.0]

    def test_constant_string_array_semicolon(self):
        """Test that Constant block parses semicolon-separated array strings."""
        const = Constant(value="[1; 2; 3]")
        const.init()
        assert const.getOutputVector() == [1.0, 2.0, 3.0]

    def test_constant_comma_separated_no_brackets(self):
        """Test that Constant block parses comma-separated values without brackets."""
        const = Constant(value="0.1,0.2,0.3,0.4")
        const.init()
        assert const.getOutputVector() == [0.1, 0.2, 0.3, 0.4]
        assert const.getNumOutputs() == 4

    def test_constant_comma_separated_no_brackets_quaternion(self):
        """Test Constant block with quaternion-like values."""
        const = Constant(value="0.999,0,0.0436,0")
        const.init()
        vec = const.getOutputVector()
        assert len(vec) == 4
        assert vec[0] == pytest.approx(0.999)
        assert vec[1] == 0.0
        assert vec[2] == pytest.approx(0.0436)
        assert vec[3] == 0.0

    def test_constant_scalar_no_vector(self):
        """Test that scalar Constant returns None for getOutputVector."""
        const = Constant(value=5.0)
        const.init()
        assert const.getOutputVector() is None
        assert const.getOutput() == 5.0

    def test_constant_vector_port_out_of_range(self):
        """Test that out-of-range port returns 0."""
        const = Constant(value=[1.0, 2.0])
        const.init()
        assert const.getOutput(5) == 0.0

    def test_constant_num_outputs(self):
        """Test getNumOutputs for scalar and vector."""
        scalar = Constant(value=5.0)
        assert scalar.getNumOutputs() == 1

        vector = Constant(value=[1.0, 2.0, 3.0])
        assert vector.getNumOutputs() == 3

    def test_constant_value_property_setter(self):
        """Test the value property setter with array."""
        const = Constant(value=1.0)
        const.value = [10.0, 20.0]
        assert const.getOutputVector() == [10.0, 20.0]
        assert const.value == 10.0  # First element


class TestStepBlock:
    """Tests for the Step block."""

    def test_step_before_step_time(self):
        """Test Step block output before step time."""
        step = Step(step_time=5.0, initial_value=0.0, final_value=1.0)
        State.t = 2.0
        step.update()
        assert step.getOutput() == 0.0

    def test_step_after_step_time(self):
        """Test Step block output after step time."""
        step = Step(step_time=5.0, initial_value=0.0, final_value=1.0)
        State.t = 7.0
        step.update()
        assert step.getOutput() == 1.0

    def test_step_at_step_time(self):
        """Test Step block output exactly at step time."""
        step = Step(step_time=5.0, initial_value=0.0, final_value=1.0)
        State.t = 5.0
        step.update()
        assert step.getOutput() == 1.0

    def test_step_init(self):
        """Test Step block initialization."""
        step = Step(step_time=5.0, initial_value=2.0, final_value=8.0)
        step.init()
        assert step.getOutput() == 2.0


class TestRampBlock:
    """Tests for the Ramp block."""

    def test_ramp_before_start(self):
        """Test Ramp block output before start time."""
        ramp = Ramp(slope=2.0, start_time=1.0, initial_output=0.0)
        State.t = 0.5
        ramp.update()
        assert ramp.getOutput() == 0.0

    def test_ramp_after_start(self):
        """Test Ramp block output after start time."""
        ramp = Ramp(slope=2.0, start_time=1.0, initial_output=0.0)
        State.t = 3.0  # 2 seconds after start
        ramp.update()
        assert ramp.getOutput() == pytest.approx(4.0)  # 2.0 * 2.0

    def test_ramp_init(self):
        """Test Ramp block initialization."""
        ramp = Ramp(slope=1.0, start_time=0.0, initial_output=5.0)
        ramp.init()
        assert ramp.getOutput() == 5.0

    def test_ramp_with_initial_offset(self):
        """Test Ramp with initial output offset."""
        ramp = Ramp(slope=1.0, start_time=0.0, initial_output=10.0)
        State.t = 5.0
        ramp.update()
        assert ramp.getOutput() == pytest.approx(15.0)


class TestSineWaveBlock:
    """Tests for the SineWave block."""

    def test_sinewave_at_zero(self):
        """Test SineWave at t=0."""
        sine = SineWave(amplitude=1.0, frequency=1.0, phase=0.0, bias=0.0)
        State.t = 0.0
        sine.update()
        assert sine.getOutput() == pytest.approx(0.0, abs=1e-10)

    def test_sinewave_at_quarter_period(self):
        """Test SineWave at quarter period."""
        sine = SineWave(amplitude=1.0, frequency=1.0, phase=0.0, bias=0.0)
        State.t = 0.25  # Quarter period for 1Hz
        sine.update()
        assert sine.getOutput() == pytest.approx(1.0, abs=1e-10)

    def test_sinewave_with_bias(self):
        """Test SineWave with DC bias."""
        sine = SineWave(amplitude=1.0, frequency=1.0, phase=0.0, bias=5.0)
        State.t = 0.0
        sine.update()
        assert sine.getOutput() == pytest.approx(5.0, abs=1e-10)

    def test_sinewave_init(self):
        """Test SineWave initialization."""
        sine = SineWave(amplitude=2.0, frequency=1.0, phase=math.pi / 2, bias=0.0)
        sine.init()
        assert sine.getOutput() == pytest.approx(2.0, abs=1e-10)


class TestClockBlock:
    """Tests for the Clock block."""

    def test_clock_output(self):
        """Test Clock outputs simulation time."""
        clock = Clock()
        State.t = 3.14
        clock.update()
        assert clock.getOutput() == pytest.approx(3.14)

    def test_clock_init(self):
        """Test Clock initialization."""
        clock = Clock()
        clock.init()
        assert clock.getOutput() == 0.0


class TestPulseGeneratorBlock:
    """Tests for the PulseGenerator block."""

    def test_pulse_during_on(self):
        """Test PulseGenerator during on phase."""
        pulse = PulseGenerator(amplitude=1.0, period=1.0, duty_cycle=50.0, phase_delay=0.0)
        State.t = 0.25  # 25% into period, should be on
        pulse.update()
        assert pulse.getOutput() == 1.0

    def test_pulse_during_off(self):
        """Test PulseGenerator during off phase."""
        pulse = PulseGenerator(amplitude=1.0, period=1.0, duty_cycle=50.0, phase_delay=0.0)
        State.t = 0.75  # 75% into period, should be off
        pulse.update()
        assert pulse.getOutput() == 0.0

    def test_pulse_before_phase_delay(self):
        """Test PulseGenerator before phase delay."""
        pulse = PulseGenerator(amplitude=1.0, period=1.0, duty_cycle=50.0, phase_delay=1.0)
        State.t = 0.5
        pulse.update()
        assert pulse.getOutput() == 0.0

    def test_pulse_init(self):
        """Test PulseGenerator initialization."""
        pulse = PulseGenerator()
        pulse.init()
        assert pulse.getOutput() == 0.0


# =============================================================================
# Math Operation Block Tests
# =============================================================================


class TestGainBlock:
    """Tests for the Gain block."""

    def test_gain_multiplication(self):
        """Test that Gain block multiplies input by gain."""
        gain = Gain(gain=2.5)
        gain.setInput(4.0)
        gain.update()
        assert gain.getOutput() == pytest.approx(10.0)

    def test_gain_negative(self):
        """Test Gain block with negative gain."""
        gain = Gain(gain=-1.0)
        gain.setInput(5.0)
        gain.update()
        assert gain.getOutput() == pytest.approx(-5.0)

    def test_gain_connected_block(self):
        """Test Gain with connected input block."""
        const = Constant(value=3.0)
        const.init()
        gain = Gain(gain=4.0)
        gain.connectInput(const)
        gain.update()
        assert gain.getOutput() == pytest.approx(12.0)


class TestSumBlock:
    """Tests for the Sum block."""

    def test_sum_addition(self):
        """Test Sum block with addition."""
        sum_block = Sum(signs="++")
        sum_block.setInput(3.0, 0)
        sum_block.setInput(2.0, 1)
        sum_block.update()
        assert sum_block.getOutput() == pytest.approx(5.0)

    def test_sum_subtraction(self):
        """Test Sum block with subtraction."""
        sum_block = Sum(signs="+-")
        sum_block.setInput(10.0, 0)
        sum_block.setInput(3.0, 1)
        sum_block.update()
        assert sum_block.getOutput() == pytest.approx(7.0)

    def test_sum_three_inputs(self):
        """Test Sum block with three inputs."""
        sum_block = Sum(signs="++-")
        sum_block.setInput(10.0, 0)
        sum_block.setInput(5.0, 1)
        sum_block.setInput(3.0, 2)
        sum_block.update()
        assert sum_block.getOutput() == pytest.approx(12.0)

    def test_sum_connected_blocks(self):
        """Test Sum with connected input blocks."""
        c1 = Constant(value=5.0)
        c2 = Constant(value=3.0)
        c1.init()
        c2.init()
        sum_block = Sum(signs="++")
        sum_block.connectInput(c1, 0)
        sum_block.connectInput(c2, 1)
        sum_block.update()
        assert sum_block.getOutput() == pytest.approx(8.0)


class TestProductBlock:
    """Tests for the Product block."""

    def test_product_multiplication(self):
        """Test Product block multiplication."""
        prod = Product(operations="**")
        prod.setInput(3.0, 0)
        prod.setInput(4.0, 1)
        prod.update()
        assert prod.getOutput() == pytest.approx(12.0)

    def test_product_division(self):
        """Test Product block division."""
        prod = Product(operations="*/")
        prod.setInput(12.0, 0)
        prod.setInput(4.0, 1)
        prod.update()
        assert prod.getOutput() == pytest.approx(3.0)

    def test_product_division_by_zero(self):
        """Test Product block handles division by near-zero."""
        prod = Product(operations="*/")
        prod.setInput(12.0, 0)
        prod.setInput(0.0, 1)
        prod.update()
        # Should not crash, uses State.EPS
        assert prod.getOutput() != float("inf")


class TestAbsBlock:
    """Tests for the Abs block."""

    def test_abs_positive(self):
        """Test Abs with positive input."""
        abs_block = Abs()
        abs_block.setInput(5.0)
        abs_block.update()
        assert abs_block.getOutput() == 5.0

    def test_abs_negative(self):
        """Test Abs with negative input."""
        abs_block = Abs()
        abs_block.setInput(-5.0)
        abs_block.update()
        assert abs_block.getOutput() == 5.0

    def test_abs_connected(self):
        """Test Abs with connected block."""
        const = Constant(value=-10.0)
        const.init()
        abs_block = Abs()
        abs_block.connectInput(const)
        abs_block.update()
        assert abs_block.getOutput() == 10.0


class TestSignBlock:
    """Tests for the Sign block."""

    def test_sign_positive(self):
        """Test Sign with positive input."""
        sign = Sign()
        sign.setInput(5.0)
        sign.update()
        assert sign.getOutput() == 1.0

    def test_sign_negative(self):
        """Test Sign with negative input."""
        sign = Sign()
        sign.setInput(-5.0)
        sign.update()
        assert sign.getOutput() == -1.0

    def test_sign_zero(self):
        """Test Sign with zero input."""
        sign = Sign()
        sign.setInput(0.0)
        sign.update()
        assert sign.getOutput() == 0.0


class TestSaturationBlock:
    """Tests for the Saturation block."""

    def test_saturation_within_limits(self):
        """Test Saturation within limits."""
        sat = Saturation(upper_limit=10.0, lower_limit=-10.0)
        sat.setInput(5.0)
        sat.update()
        assert sat.getOutput() == 5.0

    def test_saturation_upper_limit(self):
        """Test Saturation at upper limit."""
        sat = Saturation(upper_limit=10.0, lower_limit=-10.0)
        sat.setInput(15.0)
        sat.update()
        assert sat.getOutput() == 10.0

    def test_saturation_lower_limit(self):
        """Test Saturation at lower limit."""
        sat = Saturation(upper_limit=10.0, lower_limit=-10.0)
        sat.setInput(-15.0)
        sat.update()
        assert sat.getOutput() == -10.0


class TestMathFunctionBlock:
    """Tests for the MathFunction block."""

    def test_math_exp(self):
        """Test MathFunction exp."""
        mf = MathFunction(function="exp")
        mf.setInput(1.0)
        mf.update()
        assert mf.getOutput() == pytest.approx(math.e)

    def test_math_log(self):
        """Test MathFunction log."""
        mf = MathFunction(function="log")
        mf.setInput(math.e)
        mf.update()
        assert mf.getOutput() == pytest.approx(1.0)

    def test_math_log10(self):
        """Test MathFunction log10."""
        mf = MathFunction(function="log10")
        mf.setInput(100.0)
        mf.update()
        assert mf.getOutput() == pytest.approx(2.0)

    def test_math_sqrt(self):
        """Test MathFunction sqrt."""
        mf = MathFunction(function="sqrt")
        mf.setInput(16.0)
        mf.update()
        assert mf.getOutput() == pytest.approx(4.0)

    def test_math_square(self):
        """Test MathFunction square."""
        mf = MathFunction(function="square")
        mf.setInput(5.0)
        mf.update()
        assert mf.getOutput() == pytest.approx(25.0)

    def test_math_pow(self):
        """Test MathFunction pow."""
        mf = MathFunction(function="pow", exponent=3.0)
        mf.setInput(2.0)
        mf.update()
        assert mf.getOutput() == pytest.approx(8.0)

    def test_math_reciprocal(self):
        """Test MathFunction reciprocal."""
        mf = MathFunction(function="reciprocal")
        mf.setInput(4.0)
        mf.update()
        assert mf.getOutput() == pytest.approx(0.25)

    def test_math_unknown(self):
        """Test MathFunction with unknown function passes through."""
        mf = MathFunction(function="unknown")
        mf.setInput(5.0)
        mf.update()
        assert mf.getOutput() == 5.0


class TestTrigonometryBlock:
    """Tests for the Trigonometry block."""

    def test_trig_sin(self):
        """Test Trigonometry sin."""
        trig = Trigonometry(function="sin")
        trig.setInput(math.pi / 2)
        trig.update()
        assert trig.getOutput() == pytest.approx(1.0)

    def test_trig_cos(self):
        """Test Trigonometry cos."""
        trig = Trigonometry(function="cos")
        trig.setInput(0.0)
        trig.update()
        assert trig.getOutput() == pytest.approx(1.0)

    def test_trig_tan(self):
        """Test Trigonometry tan."""
        trig = Trigonometry(function="tan")
        trig.setInput(math.pi / 4)
        trig.update()
        assert trig.getOutput() == pytest.approx(1.0)

    def test_trig_asin(self):
        """Test Trigonometry asin."""
        trig = Trigonometry(function="asin")
        trig.setInput(1.0)
        trig.update()
        assert trig.getOutput() == pytest.approx(math.pi / 2)

    def test_trig_sinh(self):
        """Test Trigonometry sinh."""
        trig = Trigonometry(function="sinh")
        trig.setInput(0.0)
        trig.update()
        assert trig.getOutput() == pytest.approx(0.0)

    def test_trig_error_handling(self):
        """Test Trigonometry handles domain errors."""
        trig = Trigonometry(function="asin")
        trig.setInput(2.0)  # Invalid for asin
        trig.update()
        assert trig.getOutput() == 0.0  # Returns 0 on error


class TestDeadZoneBlock:
    """Tests for the DeadZone block."""

    def test_deadzone_within_zone(self):
        """Test DeadZone within zone."""
        dz = DeadZone(start=-0.5, end=0.5)
        dz.setInput(0.25)
        dz.update()
        assert dz.getOutput() == 0.0

    def test_deadzone_above_zone(self):
        """Test DeadZone above zone."""
        dz = DeadZone(start=-0.5, end=0.5)
        dz.setInput(2.0)
        dz.update()
        assert dz.getOutput() == pytest.approx(1.5)

    def test_deadzone_below_zone(self):
        """Test DeadZone below zone."""
        dz = DeadZone(start=-0.5, end=0.5)
        dz.setInput(-2.0)
        dz.update()
        assert dz.getOutput() == pytest.approx(-1.5)


class TestSwitchBlock:
    """Tests for the Switch block."""

    def test_switch_gte_true(self):
        """Test Switch with gte criteria true."""
        sw = Switch(threshold=0.0, criteria="gte")
        sw.setInput(5.0, 0)  # in1
        sw.setInput(1.0, 1)  # control >= 0
        sw.setInput(10.0, 2)  # in2
        sw.update()
        assert sw.getOutput() == 5.0

    def test_switch_gte_false(self):
        """Test Switch with gte criteria false."""
        sw = Switch(threshold=0.0, criteria="gte")
        sw.setInput(5.0, 0)  # in1
        sw.setInput(-1.0, 1)  # control < 0
        sw.setInput(10.0, 2)  # in2
        sw.update()
        assert sw.getOutput() == 10.0

    def test_switch_gt(self):
        """Test Switch with gt criteria."""
        sw = Switch(threshold=0.0, criteria="gt")
        sw.setInput(5.0, 0)
        sw.setInput(0.0, 1)  # control == 0, not > 0
        sw.setInput(10.0, 2)
        sw.update()
        assert sw.getOutput() == 10.0

    def test_switch_neq(self):
        """Test Switch with neq criteria."""
        sw = Switch(threshold=5.0, criteria="neq")
        sw.setInput(1.0, 0)
        sw.setInput(3.0, 1)  # control != 5
        sw.setInput(2.0, 2)
        sw.update()
        assert sw.getOutput() == 1.0


class TestMuxBlock:
    """Tests for the Mux block."""

    def test_mux_basic(self):
        """Test Mux basic operation."""
        mux = Mux(num_inputs=3)
        mux.setInput(1.0, 0)
        mux.setInput(2.0, 1)
        mux.setInput(3.0, 2)
        mux.update()
        assert mux.getOutput(0) == 1.0
        assert mux.getOutput(1) == 2.0
        assert mux.getOutput(2) == 3.0

    def test_mux_vector_output(self):
        """Test Mux vector output."""
        mux = Mux(num_inputs=2)
        mux.setInput(5.0, 0)
        mux.setInput(10.0, 1)
        mux.update()
        vec = mux.getOutputVector()
        assert vec == [5.0, 10.0]

    def test_mux_init(self):
        """Test Mux initialization."""
        mux = Mux(num_inputs=2)
        mux.init()
        assert mux.outputs == [0.0, 0.0]


class TestDemuxBlock:
    """Tests for the Demux block."""

    def test_demux_basic(self):
        """Test Demux basic operation."""
        demux = Demux(num_outputs=2)
        demux.setInput([5.0, 10.0])
        demux.update()
        assert demux.getOutput(0) == 5.0
        assert demux.getOutput(1) == 10.0

    def test_demux_scalar_input(self):
        """Test Demux with scalar input."""
        demux = Demux(num_outputs=2)
        demux.setInput(5.0)
        demux.update()
        assert demux.getOutput(0) == 5.0
        assert demux.getOutput(1) == 0.0

    def test_demux_from_mux(self):
        """Test Demux connected to Mux."""
        mux = Mux(num_inputs=2)
        mux.setInput(3.0, 0)
        mux.setInput(7.0, 1)
        mux.update()

        demux = Demux(num_outputs=2)
        demux.connectInput(mux)
        demux.update()
        assert demux.getOutput(0) == 3.0
        assert demux.getOutput(1) == 7.0


class TestReshapeBlock:
    """Tests for the Reshape block."""

    def test_reshape_scalar(self):
        """Test Reshape with scalar input."""
        reshape = Reshape()
        reshape.setInput(5.0)
        reshape.update()
        assert reshape.getOutput() == 5.0

    def test_reshape_vector(self):
        """Test Reshape with vector input."""
        reshape = Reshape()
        reshape.setInput([1.0, 2.0, 3.0])
        assert reshape.getOutput() == 1.0

    def test_reshape_from_mux(self):
        """Test Reshape connected to Mux."""
        mux = Mux(num_inputs=3)
        mux.setInput(1.0, 0)
        mux.setInput(2.0, 1)
        mux.setInput(3.0, 2)
        mux.update()

        reshape = Reshape()
        reshape.connectInput(mux)
        reshape.update()
        vec = reshape.getOutputVector()
        assert vec == [1.0, 2.0, 3.0]


# =============================================================================
# Sink Block Tests
# =============================================================================


class TestScopeBlock:
    """Tests for the Scope block."""

    def test_scope_initialization(self):
        """Test Scope block initialization."""
        scope = Scope(num_inputs=3)
        assert scope.num_inputs == 3
        assert len(scope.inputs) == 3
        assert len(scope.input_blocks) == 3

    def test_scope_only_records_connected_inputs(self):
        """Test that Scope only records data for connected inputs."""
        scope = Scope(num_inputs=3)
        const = Constant(value=5.0)

        # Connect only to port 1 (second input)
        scope.connectInput(const, 1)

        # Initialize state
        State.t = 0.0
        State.ready = 1

        # Update and record
        scope.update()
        scope.rpt()

        # Check data
        data = scope.getData()
        assert data["numInputs"] == 1  # Only one connected input
        assert len(data["values"]) == 1


class TestDisplayBlock:
    """Tests for the Display block."""

    def test_display_basic(self):
        """Test Display basic operation."""
        display = Display()
        State.ready = 1
        display.setInput(42.0)
        display.update()
        display.rpt()  # rpt() sets current_value which getOutput returns
        assert display.getOutput() == 42.0

    def test_display_connected(self):
        """Test Display with connected block."""
        const = Constant(value=100.0)
        const.init()
        State.ready = 1
        display = Display()
        display.connectInput(const)
        display.update()
        display.rpt()  # rpt() sets current_value
        assert display.getOutput() == 100.0


class TestOutportBlock:
    """Tests for the Outport block."""

    def test_outport_basic(self):
        """Test Outport basic operation."""
        outport = Outport(port_number=1)
        outport.setInput(10.0)
        outport.update()
        assert outport.getOutput() == 10.0

    def test_outport_port_number(self):
        """Test Outport port number attribute."""
        outport = Outport(port_number=3)
        assert outport.port_number == 3

    def test_outport_vector_passthrough(self):
        """Test Outport vector pass-through."""
        mux = Mux(num_inputs=2)
        mux.setInput(1.0, 0)
        mux.setInput(2.0, 1)
        mux.update()

        outport = Outport(port_number=1)
        outport.connectInput(mux)
        outport.update()

        vec = outport.getOutputVector()
        assert vec == [1.0, 2.0]


class TestToWorkspaceBlock:
    """Tests for the ToWorkspace block."""

    def test_to_workspace_basic(self):
        """Test ToWorkspace basic operation."""
        tw = ToWorkspace(variable_name="test_var")
        tw.setInput(5.0)
        tw.update()
        assert tw.getOutput() == 5.0

    def test_to_workspace_recording(self):
        """Test ToWorkspace data recording."""
        tw = ToWorkspace(variable_name="my_data")
        State.t = 0.0
        State.ready = 1
        tw.setInput(10.0)
        tw.update()
        tw.rpt()

        State.t = 1.0
        tw.setInput(20.0)
        tw.update()
        tw.rpt()

        data = tw.getData()
        assert data["name"] == "my_data"
        assert len(data["times"]) == 2
        assert len(data["values"]) == 2


# =============================================================================
# Continuous Block Tests
# =============================================================================


class TestIntegratorBlock:
    """Tests for the Integrator block."""

    def test_integrator_initial_condition(self):
        """Test Integrator block initial condition."""
        integrator = Integrator(initial_condition=5.0)
        assert integrator.getOutput() == pytest.approx(5.0)

    def test_integrator_integration(self):
        """Test basic integration."""
        integrator = Integrator(initial_condition=0.0)
        integrator.setInput(1.0)  # Constant input of 1

        State.dt = 0.1
        State.method = "Euler"

        # Take a step
        integrator.update()
        integrator.propagateStates()

        # After integrating 1 for dt=0.1, output should be 0.1
        assert integrator.getOutput() == pytest.approx(0.1, rel=0.01)

    def test_integrator_connected(self):
        """Test Integrator with connected block."""
        const = Constant(value=2.0)
        const.init()
        integrator = Integrator(initial_condition=0.0)
        integrator.connectInput(const)

        State.dt = 0.1
        State.method = "Euler"

        integrator.update()
        integrator.propagateStates()

        assert integrator.getOutput() == pytest.approx(0.2, rel=0.01)


class TestDerivativeBlock:
    """Tests for the Derivative block."""

    def test_derivative_basic(self):
        """Test Derivative basic operation.

        The derivative uses a filtered derivative: output = N*(u - x)
        where N is the coefficient (default 100.0) and x is an internal state.
        For step change from 0 to 1, output = 100*(1 - 0) = 100
        """
        deriv = Derivative()  # coefficient=100.0 by default
        State.dt = 0.1

        # First update - internal state x[0] = 0
        deriv.setInput(0.0)
        deriv.update()

        # Second update with changed input
        # output = coefficient * (input - x[0]) = 100 * (1 - 0) = 100
        deriv.setInput(1.0)
        deriv.update()

        assert deriv.getOutput() == pytest.approx(100.0)

    def test_derivative_with_custom_coefficient(self):
        """Test Derivative with custom coefficient."""
        deriv = Derivative(coefficient=10.0)
        State.dt = 0.1

        deriv.setInput(0.0)
        deriv.update()

        deriv.setInput(1.0)
        deriv.update()

        # output = 10 * (1 - 0) = 10
        assert deriv.getOutput() == pytest.approx(10.0)


class TestTransferFunctionBlock:
    """Tests for the TransferFunction block."""

    def test_transfer_function_init(self):
        """Test TransferFunction initialization."""
        tf = TransferFunction(numerator=[1.0], denominator=[1.0, 1.0])
        tf.init()
        assert tf.getOutput() == 0.0

    def test_transfer_function_gain(self):
        """Test TransferFunction as simple gain (num=[2], den=[1])."""
        tf = TransferFunction(numerator=[2.0], denominator=[1.0])
        tf.setInput(5.0)
        tf.update()
        # For a pure gain, output = num/den * input
        assert tf.getOutput() == pytest.approx(10.0)


# =============================================================================
# Discrete Block Tests
# =============================================================================

from src.osk.blocks.discrete import (
    DiscreteDerivative,
    DiscreteIntegrator,
    DiscreteTransferFunction,
    UnitDelay,
    ZeroOrderHold,
)


class TestUnitDelayBlock:
    """Tests for the UnitDelay block."""

    def test_unit_delay_initial_condition(self):
        """Test UnitDelay initial condition."""
        delay = UnitDelay(initial_condition=5.0, sample_time=0.1)
        delay.init()
        assert delay.getOutput() == 5.0

    def test_unit_delay_one_step(self):
        """Test UnitDelay after one step."""
        delay = UnitDelay(initial_condition=0.0, sample_time=0.1)
        delay.init()
        State.t = 0.0
        delay.setInput(10.0)
        delay.update()
        # Output is previous value (initial condition)
        assert delay.getOutput() == 0.0

    def test_unit_delay_two_steps(self):
        """Test UnitDelay after two steps."""
        delay = UnitDelay(initial_condition=0.0, sample_time=0.1)
        delay.init()

        State.t = 0.0
        delay.setInput(10.0)
        delay.update()

        State.t = 0.1
        delay.setInput(20.0)
        delay.update()
        # Output is now previous input (10.0)
        assert delay.getOutput() == 10.0

    def test_unit_delay_connected(self):
        """Test UnitDelay with connected block."""
        const = Constant(value=7.0)
        const.init()
        delay = UnitDelay(initial_condition=0.0, sample_time=0.1)
        delay.init()
        delay.connectInput(const)

        State.t = 0.0
        delay.update()
        assert delay.getOutput() == 0.0

        State.t = 0.1
        delay.update()
        assert delay.getOutput() == 7.0


class TestZeroOrderHoldBlock:
    """Tests for the ZeroOrderHold block."""

    def test_zoh_initial(self):
        """Test ZeroOrderHold initial output."""
        zoh = ZeroOrderHold(sample_time=0.1)
        zoh.init()
        assert zoh.getOutput() == 0.0

    def test_zoh_sample(self):
        """Test ZeroOrderHold sampling."""
        zoh = ZeroOrderHold(sample_time=0.1)
        zoh.init()

        State.t = 0.0
        zoh.setInput(5.0)
        zoh.update()
        assert zoh.getOutput() == 5.0

    def test_zoh_hold(self):
        """Test ZeroOrderHold holds value between samples."""
        zoh = ZeroOrderHold(sample_time=0.1)
        zoh.init()

        State.t = 0.0
        zoh.setInput(5.0)
        zoh.update()

        # Change input but don't reach sample time
        State.t = 0.05
        zoh.setInput(10.0)
        zoh.update()
        # Still holds previous value
        assert zoh.getOutput() == 5.0

    def test_zoh_connected(self):
        """Test ZeroOrderHold with connected block."""
        const = Constant(value=3.0)
        const.init()
        zoh = ZeroOrderHold(sample_time=0.1)
        zoh.init()
        zoh.connectInput(const)

        State.t = 0.0
        zoh.update()
        assert zoh.getOutput() == 3.0


class TestDiscreteIntegratorBlock:
    """Tests for the DiscreteIntegrator block."""

    def test_discrete_integrator_initial(self):
        """Test DiscreteIntegrator initial condition."""
        di = DiscreteIntegrator(initial_condition=5.0, sample_time=0.1)
        di.init()
        assert di.getOutput() == 5.0

    def test_discrete_integrator_forward(self):
        """Test DiscreteIntegrator forward Euler method."""
        di = DiscreteIntegrator(method='forward', sample_time=0.1, initial_condition=0.0)
        di.init()

        State.t = 0.0
        di.setInput(1.0)
        di.update()  # First step, output += T * prev_input (prev_input=0)

        State.t = 0.1
        di.setInput(1.0)
        di.update()  # output += 0.1 * 1 = 0.1
        assert di.getOutput() == pytest.approx(0.1)

    def test_discrete_integrator_backward(self):
        """Test DiscreteIntegrator backward Euler method."""
        di = DiscreteIntegrator(method='backward', sample_time=0.1, initial_condition=0.0)
        di.init()

        State.t = 0.0
        di.setInput(1.0)
        di.update()
        # backward: output += T * u[n]
        assert di.getOutput() == pytest.approx(0.1)

    def test_discrete_integrator_trapezoidal(self):
        """Test DiscreteIntegrator trapezoidal method."""
        di = DiscreteIntegrator(method='trapezoidal', sample_time=0.1, initial_condition=0.0)
        di.init()

        State.t = 0.0
        di.setInput(1.0)
        di.update()
        # trapezoidal: output += T/2 * (u[n] + u[n-1]) = 0.1/2 * (1 + 0) = 0.05
        assert di.getOutput() == pytest.approx(0.05)

    def test_discrete_integrator_connected(self):
        """Test DiscreteIntegrator with connected block."""
        const = Constant(value=2.0)
        const.init()
        di = DiscreteIntegrator(method='backward', sample_time=0.1, initial_condition=0.0)
        di.init()
        di.connectInput(const)

        State.t = 0.0
        di.update()
        assert di.getOutput() == pytest.approx(0.2)


class TestDiscreteDerivativeBlock:
    """Tests for the DiscreteDerivative block."""

    def test_discrete_derivative_initial(self):
        """Test DiscreteDerivative initial output."""
        dd = DiscreteDerivative(sample_time=0.1)
        dd.init()
        assert dd.getOutput() == 0.0

    def test_discrete_derivative_basic(self):
        """Test DiscreteDerivative basic operation."""
        dd = DiscreteDerivative(sample_time=0.1, initial_condition=0.0)
        dd.init()

        State.t = 0.0
        dd.setInput(0.0)
        dd.update()

        State.t = 0.1
        dd.setInput(1.0)
        dd.update()
        # (1.0 - 0.0) / 0.1 = 10.0
        assert dd.getOutput() == pytest.approx(10.0)

    def test_discrete_derivative_connected(self):
        """Test DiscreteDerivative with connected block."""
        const = Constant(value=5.0)
        const.init()
        dd = DiscreteDerivative(sample_time=0.1, initial_condition=0.0)
        dd.init()
        dd.connectInput(const)

        State.t = 0.0
        dd.update()

        State.t = 0.1
        dd.update()
        # Constant input, derivative is 0 after first step
        assert dd.getOutput() == pytest.approx(0.0)


class TestDiscreteTransferFunctionBlock:
    """Tests for the DiscreteTransferFunction block."""

    def test_discrete_tf_init(self):
        """Test DiscreteTransferFunction initialization."""
        dtf = DiscreteTransferFunction(numerator=[1.0], denominator=[1.0, -0.5], sample_time=0.1)
        dtf.init()
        assert dtf.getOutput() == 0.0

    def test_discrete_tf_unit_gain(self):
        """Test DiscreteTransferFunction with unit gain."""
        # H(z) = 1/1 = 1 (pure gain)
        dtf = DiscreteTransferFunction(numerator=[1.0], denominator=[1.0], sample_time=0.1)
        dtf.init()

        State.t = 0.0
        dtf.setInput(5.0)
        dtf.update()
        assert dtf.getOutput() == pytest.approx(5.0)

    def test_discrete_tf_connected(self):
        """Test DiscreteTransferFunction with connected block."""
        const = Constant(value=1.0)
        const.init()
        dtf = DiscreteTransferFunction(numerator=[1.0], denominator=[1.0], sample_time=0.1)
        dtf.init()
        dtf.connectInput(const)

        State.t = 0.0
        dtf.update()
        assert dtf.getOutput() == pytest.approx(1.0)


# =============================================================================
# Signal Processing Block Tests
# =============================================================================

from src.osk.blocks.signal_processing import (
    Backlash,
    BandPassFilter,
    HighPassFilter,
    LowPassFilter,
    MovingAverage,
    RateLimiter,
)


class TestRateLimiterBlock:
    """Tests for the RateLimiter block."""

    def test_rate_limiter_within_limits(self):
        """Test RateLimiter when rate is within limits."""
        rl = RateLimiter(rising_rate=10.0, falling_rate=-10.0)
        rl.init()
        State.dt = 0.1

        rl.setInput(0.5)
        rl.update()
        # 0.5 is within max change of 10*0.1=1.0
        assert rl.getOutput() == pytest.approx(0.5)

    def test_rate_limiter_rising(self):
        """Test RateLimiter rising rate limit."""
        rl = RateLimiter(rising_rate=1.0, falling_rate=-1.0)
        rl.init()
        State.dt = 0.1

        rl.setInput(10.0)  # Wants to jump to 10
        rl.update()
        # Max rise is 1.0*0.1=0.1
        assert rl.getOutput() == pytest.approx(0.1)

    def test_rate_limiter_falling(self):
        """Test RateLimiter falling rate limit."""
        rl = RateLimiter(rising_rate=10.0, falling_rate=-1.0)
        rl.init()
        State.dt = 0.1

        # First go up quickly (within limit of 10*0.1=1.0)
        rl.setInput(0.5)
        rl.update()
        assert rl.getOutput() == pytest.approx(0.5)

        # Then try to go down fast
        rl.setInput(-10.0)
        rl.update()
        # Max fall is -1.0*0.1=-0.1, so from 0.5 to 0.4
        assert rl.getOutput() == pytest.approx(0.4)

    def test_rate_limiter_connected(self):
        """Test RateLimiter with connected block."""
        const = Constant(value=0.05)
        const.init()
        rl = RateLimiter(rising_rate=1.0, falling_rate=-1.0)
        rl.init()
        rl.connectInput(const)
        State.dt = 0.1

        rl.update()
        assert rl.getOutput() == pytest.approx(0.05)


class TestMovingAverageBlock:
    """Tests for the MovingAverage block."""

    def test_moving_average_single(self):
        """Test MovingAverage with single sample."""
        ma = MovingAverage(window_size=5)
        ma.init()
        ma.setInput(10.0)
        ma.update()
        assert ma.getOutput() == pytest.approx(10.0)

    def test_moving_average_fill(self):
        """Test MovingAverage as buffer fills."""
        ma = MovingAverage(window_size=3)
        ma.init()

        ma.setInput(3.0)
        ma.update()
        assert ma.getOutput() == pytest.approx(3.0)

        ma.setInput(6.0)
        ma.update()
        # (3 + 6) / 2 = 4.5
        assert ma.getOutput() == pytest.approx(4.5)

        ma.setInput(9.0)
        ma.update()
        # (3 + 6 + 9) / 3 = 6.0
        assert ma.getOutput() == pytest.approx(6.0)

    def test_moving_average_sliding(self):
        """Test MovingAverage sliding window."""
        ma = MovingAverage(window_size=2)
        ma.init()

        ma.setInput(1.0)
        ma.update()
        ma.setInput(3.0)
        ma.update()
        # (1 + 3) / 2 = 2.0
        assert ma.getOutput() == pytest.approx(2.0)

        ma.setInput(5.0)
        ma.update()
        # (3 + 5) / 2 = 4.0
        assert ma.getOutput() == pytest.approx(4.0)

    def test_moving_average_connected(self):
        """Test MovingAverage with connected block."""
        const = Constant(value=5.0)
        const.init()
        ma = MovingAverage(window_size=3)
        ma.init()
        ma.connectInput(const)

        ma.update()
        assert ma.getOutput() == pytest.approx(5.0)


class TestLowPassFilterBlock:
    """Tests for the LowPassFilter block."""

    def test_low_pass_init(self):
        """Test LowPassFilter initialization."""
        lpf = LowPassFilter(cutoff_freq=1.0)
        State.dt = 0.01
        lpf.init()
        assert lpf.getOutput() == 0.0

    def test_low_pass_step_response(self):
        """Test LowPassFilter step response."""
        lpf = LowPassFilter(cutoff_freq=10.0)
        State.dt = 0.01
        lpf.init()

        lpf.setInput(1.0)
        lpf.update()
        # First output should be between 0 and 1
        assert 0.0 < lpf.getOutput() < 1.0

    def test_low_pass_connected(self):
        """Test LowPassFilter with connected block."""
        const = Constant(value=1.0)
        const.init()
        lpf = LowPassFilter(cutoff_freq=10.0)
        State.dt = 0.01
        lpf.init()
        lpf.connectInput(const)

        lpf.update()
        assert 0.0 < lpf.getOutput() < 1.0


class TestHighPassFilterBlock:
    """Tests for the HighPassFilter block."""

    def test_high_pass_init(self):
        """Test HighPassFilter initialization."""
        hpf = HighPassFilter(cutoff_freq=1.0)
        State.dt = 0.01
        hpf.init()
        assert hpf.getOutput() == 0.0

    def test_high_pass_step_response(self):
        """Test HighPassFilter step response."""
        hpf = HighPassFilter(cutoff_freq=1.0)
        State.dt = 0.01
        hpf.init()

        hpf.setInput(1.0)
        hpf.update()
        # Step response should produce output
        assert hpf.getOutput() != 0.0

    def test_high_pass_dc_rejection(self):
        """Test HighPassFilter DC rejection over time."""
        hpf = HighPassFilter(cutoff_freq=10.0)
        State.dt = 0.01
        hpf.init()

        # Apply constant input
        for _ in range(100):
            hpf.setInput(1.0)
            hpf.update()

        # Output should approach 0 for DC
        assert abs(hpf.getOutput()) < 0.1


class TestBandPassFilterBlock:
    """Tests for the BandPassFilter block."""

    def test_band_pass_init(self):
        """Test BandPassFilter initialization."""
        bpf = BandPassFilter(low_cutoff=0.1, high_cutoff=10.0)
        State.dt = 0.01
        bpf.init()
        assert bpf.getOutput() == 0.0

    def test_band_pass_step_response(self):
        """Test BandPassFilter step response."""
        bpf = BandPassFilter(low_cutoff=0.1, high_cutoff=10.0)
        State.dt = 0.01
        bpf.init()

        bpf.setInput(1.0)
        bpf.update()
        # Should produce some output initially
        assert bpf.getOutput() != 0.0

    def test_band_pass_connected(self):
        """Test BandPassFilter with connected block."""
        const = Constant(value=1.0)
        const.init()
        bpf = BandPassFilter(low_cutoff=0.1, high_cutoff=10.0)
        State.dt = 0.01
        bpf.init()
        bpf.connectInput(const)

        bpf.update()
        assert isinstance(bpf.getOutput(), float)


class TestAnalogFilterBlock:
    """Tests for the AnalogFilter block with multiple design methods."""

    def test_analog_filter_butterworth_lowpass(self):
        """Test Butterworth lowpass filter."""
        from src.osk.blocks.signal_processing import AnalogFilter

        filt = AnalogFilter(design="butterworth", response="lowpass", order=2, cutoff_freq=10.0)
        State.dt = 0.001
        filt.init()

        # Apply step input
        filt.setInput(1.0)
        for _ in range(100):
            filt.update()

        # Should approach 1.0 for lowpass with DC input
        assert filt.getOutput() > 0.5

    def test_analog_filter_butterworth_highpass(self):
        """Test Butterworth highpass filter."""
        from src.osk.blocks.signal_processing import AnalogFilter

        filt = AnalogFilter(design="butterworth", response="highpass", order=2, cutoff_freq=10.0)
        State.dt = 0.001
        filt.init()

        # Apply step input (DC)
        filt.setInput(1.0)
        for _ in range(200):
            filt.update()

        # Highpass should reject DC - output near zero
        assert abs(filt.getOutput()) < 0.2

    def test_analog_filter_chebyshev1(self):
        """Test Chebyshev Type I filter."""
        from src.osk.blocks.signal_processing import AnalogFilter

        filt = AnalogFilter(design="chebyshev1", response="lowpass", order=2, cutoff_freq=10.0, passband_ripple=1.0)
        State.dt = 0.001
        filt.init()

        filt.setInput(1.0)
        for _ in range(100):
            filt.update()

        assert filt.getOutput() > 0.5

    def test_analog_filter_chebyshev2(self):
        """Test Chebyshev Type II filter."""
        from src.osk.blocks.signal_processing import AnalogFilter

        filt = AnalogFilter(design="chebyshev2", response="lowpass", order=2, cutoff_freq=10.0, stopband_atten=40.0)
        State.dt = 0.001
        filt.init()

        filt.setInput(1.0)
        for _ in range(500):  # Chebyshev II may need more time to settle
            filt.update()

        # Chebyshev II has different gain characteristics; check it responds
        assert filt.getOutput() > 0.2

    def test_analog_filter_bessel(self):
        """Test Bessel filter (maximally flat group delay)."""
        from src.osk.blocks.signal_processing import AnalogFilter

        filt = AnalogFilter(design="bessel", response="lowpass", order=2, cutoff_freq=10.0)
        State.dt = 0.001
        filt.init()

        filt.setInput(1.0)
        for _ in range(100):
            filt.update()

        assert filt.getOutput() > 0.5

    def test_analog_filter_higher_order(self):
        """Test higher order filter."""
        from src.osk.blocks.signal_processing import AnalogFilter

        filt = AnalogFilter(design="butterworth", response="lowpass", order=5, cutoff_freq=10.0)
        State.dt = 0.001
        filt.init()

        filt.setInput(1.0)
        for _ in range(200):
            filt.update()

        assert filt.getOutput() > 0.5

    def test_analog_filter_connected(self):
        """Test AnalogFilter with connected block."""
        from src.osk.blocks.signal_processing import AnalogFilter

        const = Constant(value=1.0)
        const.init()
        filt = AnalogFilter(design="butterworth", response="lowpass", order=2, cutoff_freq=10.0)
        State.dt = 0.001
        filt.init()
        filt.connectInput(const)

        for _ in range(100):
            filt.update()

        assert filt.getOutput() > 0.5


class TestNotchFilterBlock:
    """Tests for the NotchFilter block."""

    def test_notch_filter_init(self):
        """Test NotchFilter initialization."""
        from src.osk.blocks.signal_processing import NotchFilter

        nf = NotchFilter(notch_freq=60.0, bandwidth=2.0)
        State.dt = 0.001
        nf.init()
        assert nf.getOutput() == 0.0

    def test_notch_filter_dc_passthrough(self):
        """Test NotchFilter passes DC unchanged."""
        from src.osk.blocks.signal_processing import NotchFilter

        nf = NotchFilter(notch_freq=60.0, bandwidth=2.0)
        State.dt = 0.001
        nf.init()

        # Apply DC input
        for _ in range(200):
            nf.setInput(1.0)
            nf.update()

        # DC should pass through notch filter
        assert nf.getOutput() > 0.9

    def test_notch_filter_rejects_notch_frequency(self):
        """Test NotchFilter attenuates the notch frequency."""
        import math
        from src.osk.blocks.signal_processing import NotchFilter

        notch_freq = 50.0
        nf = NotchFilter(notch_freq=notch_freq, bandwidth=5.0)  # Wider bandwidth for cleaner test
        dt = 0.0001  # Small step for accurate sine at 50 Hz
        State.dt = dt
        nf.init()

        # Apply sine wave at notch frequency
        max_output = 0.0
        for i in range(2000):  # More iterations to settle
            t = i * dt
            sine_input = math.sin(2 * math.pi * notch_freq * t)
            nf.setInput(sine_input)
            nf.update()
            if i > 1000:  # Allow filter to settle
                max_output = max(max_output, abs(nf.getOutput()))

        # Output at notch frequency should be attenuated (< 50% of input)
        assert max_output < 0.5  # Input amplitude is 1.0

    def test_notch_filter_connected(self):
        """Test NotchFilter with connected block."""
        from src.osk.blocks.signal_processing import NotchFilter

        const = Constant(value=1.0)
        const.init()
        nf = NotchFilter(notch_freq=60.0, bandwidth=2.0)
        State.dt = 0.001
        nf.init()
        nf.connectInput(const)

        for _ in range(200):
            nf.update()

        assert nf.getOutput() > 0.9


class TestBacklashBlock:
    """Tests for the Backlash block."""

    def test_backlash_init(self):
        """Test Backlash initialization."""
        bl = Backlash(deadband_width=0.2, initial_output=1.0)
        assert bl.getOutput() == 1.0

    def test_backlash_within_deadband(self):
        """Test Backlash within deadband."""
        bl = Backlash(deadband_width=0.2, initial_output=0.0)

        bl.setInput(0.05)
        bl.update()
        # Input within deadband, output unchanged
        assert bl.getOutput() == 0.0

    def test_backlash_above_deadband(self):
        """Test Backlash above deadband."""
        bl = Backlash(deadband_width=0.2, initial_output=0.0)

        bl.setInput(1.0)
        bl.update()
        # Input is 1.0, half_width is 0.1, so output = 1.0 - 0.1 = 0.9
        assert bl.getOutput() == pytest.approx(0.9)

    def test_backlash_below_deadband(self):
        """Test Backlash below deadband."""
        bl = Backlash(deadband_width=0.2, initial_output=0.0)

        bl.setInput(-1.0)
        bl.update()
        # Input is -1.0, output = -1.0 + 0.1 = -0.9
        assert bl.getOutput() == pytest.approx(-0.9)

    def test_backlash_connected(self):
        """Test Backlash with connected block."""
        const = Constant(value=2.0)
        const.init()
        bl = Backlash(deadband_width=0.2, initial_output=0.0)
        bl.connectInput(const)

        bl.update()
        assert bl.getOutput() == pytest.approx(1.9)


# =============================================================================
# Nonlinear Block Tests
# =============================================================================

from src.osk.blocks.nonlinear import (
    Coulomb,
    LookupTable1D,
    LookupTable2D,
    Quantizer,
    Relay,
    VariableTransportDelay,
)


class TestLookupTable1DBlock:
    """Tests for the LookupTable1D block."""

    def test_lookup_1d_interpolation(self):
        """Test LookupTable1D linear interpolation."""
        lut = LookupTable1D(x_data=[0.0, 1.0, 2.0], y_data=[0.0, 10.0, 30.0])
        lut.init()

        lut.setInput(0.5)
        lut.update()
        # Interpolate between (0,0) and (1,10): 5.0
        assert lut.getOutput() == pytest.approx(5.0)

    def test_lookup_1d_exact(self):
        """Test LookupTable1D at exact data point."""
        lut = LookupTable1D(x_data=[0.0, 1.0, 2.0], y_data=[0.0, 10.0, 30.0])
        lut.init()

        lut.setInput(1.0)
        lut.update()
        assert lut.getOutput() == pytest.approx(10.0)

    def test_lookup_1d_extrapolate_low(self):
        """Test LookupTable1D extrapolation below range."""
        lut = LookupTable1D(x_data=[0.0, 1.0], y_data=[0.0, 10.0])
        lut.init()

        lut.setInput(-1.0)
        lut.update()
        # Extrapolate: slope is 10, at x=-1: 0 + 10*(-1) = -10
        assert lut.getOutput() == pytest.approx(-10.0)

    def test_lookup_1d_extrapolate_high(self):
        """Test LookupTable1D extrapolation above range."""
        lut = LookupTable1D(x_data=[0.0, 1.0], y_data=[0.0, 10.0])
        lut.init()

        lut.setInput(2.0)
        lut.update()
        # Extrapolate: at x=2: 10 + 10*(2-1) = 20
        assert lut.getOutput() == pytest.approx(20.0)

    def test_lookup_1d_connected(self):
        """Test LookupTable1D with connected block."""
        const = Constant(value=0.5)
        const.init()
        lut = LookupTable1D(x_data=[0.0, 1.0], y_data=[0.0, 10.0])
        lut.init()
        lut.connectInput(const)

        lut.update()
        assert lut.getOutput() == pytest.approx(5.0)


class TestLookupTable2DBlock:
    """Tests for the LookupTable2D block."""

    def test_lookup_2d_init(self):
        """Test LookupTable2D initialization."""
        lut = LookupTable2D()
        lut.init()
        assert lut.getOutput() == 0.0

    def test_lookup_2d_corner(self):
        """Test LookupTable2D at corner."""
        lut = LookupTable2D(
            x_data=[0.0, 1.0],
            y_data=[0.0, 1.0],
            z_data=[[0.0, 1.0], [2.0, 3.0]]
        )
        lut.init()

        lut.setInput(0.0, 0)
        lut.setInput(0.0, 1)
        lut.update()
        assert lut.getOutput() == pytest.approx(0.0)

    def test_lookup_2d_interpolation(self):
        """Test LookupTable2D bilinear interpolation."""
        lut = LookupTable2D(
            x_data=[0.0, 1.0],
            y_data=[0.0, 1.0],
            z_data=[[0.0, 1.0], [2.0, 3.0]]
        )
        lut.init()

        lut.setInput(0.5, 0)
        lut.setInput(0.5, 1)
        lut.update()
        # Center of grid: average of corners = (0+1+2+3)/4 = 1.5
        assert lut.getOutput() == pytest.approx(1.5)

    def test_lookup_2d_connected(self):
        """Test LookupTable2D with connected blocks."""
        c1 = Constant(value=0.0)
        c2 = Constant(value=0.0)
        c1.init()
        c2.init()
        lut = LookupTable2D()
        lut.connectInput(c1, 0)
        lut.connectInput(c2, 1)
        lut.update()
        assert isinstance(lut.getOutput(), float)


class TestQuantizerBlock:
    """Tests for the Quantizer block."""

    def test_quantizer_round_up(self):
        """Test Quantizer rounds up."""
        q = Quantizer(interval=1.0)
        q.setInput(1.7)
        q.update()
        assert q.getOutput() == pytest.approx(2.0)

    def test_quantizer_round_down(self):
        """Test Quantizer rounds down."""
        q = Quantizer(interval=1.0)
        q.setInput(1.2)
        q.update()
        assert q.getOutput() == pytest.approx(1.0)

    def test_quantizer_custom_interval(self):
        """Test Quantizer with custom interval."""
        q = Quantizer(interval=0.25)
        q.setInput(0.37)
        q.update()
        # 0.37 / 0.25 = 1.48, rounds to 1, so 1 * 0.25 = 0.25
        # Actually round(1.48) = 1, so 0.25
        assert q.getOutput() == pytest.approx(0.25)

    def test_quantizer_negative(self):
        """Test Quantizer with negative values."""
        q = Quantizer(interval=1.0)
        q.setInput(-2.3)
        q.update()
        assert q.getOutput() == pytest.approx(-2.0)

    def test_quantizer_connected(self):
        """Test Quantizer with connected block."""
        const = Constant(value=3.7)
        const.init()
        q = Quantizer(interval=1.0)
        q.connectInput(const)
        q.update()
        assert q.getOutput() == pytest.approx(4.0)


class TestRelayBlock:
    """Tests for the Relay block."""

    def test_relay_initial_off(self):
        """Test Relay initial state is off."""
        r = Relay(switch_on=0.5, switch_off=-0.5, output_on=1.0, output_off=0.0)
        r.init()
        assert r.getOutput() == 0.0

    def test_relay_turn_on(self):
        """Test Relay turns on above threshold."""
        r = Relay(switch_on=0.5, switch_off=-0.5, output_on=1.0, output_off=0.0)
        r.init()

        r.setInput(1.0)
        r.update()
        assert r.getOutput() == 1.0

    def test_relay_hysteresis(self):
        """Test Relay hysteresis behavior."""
        r = Relay(switch_on=0.5, switch_off=-0.5, output_on=1.0, output_off=0.0)
        r.init()

        # Turn on
        r.setInput(1.0)
        r.update()
        assert r.getOutput() == 1.0

        # Go to middle, should stay on
        r.setInput(0.0)
        r.update()
        assert r.getOutput() == 1.0

        # Go below switch_off, should turn off
        r.setInput(-1.0)
        r.update()
        assert r.getOutput() == 0.0

    def test_relay_connected(self):
        """Test Relay with connected block."""
        const = Constant(value=1.0)
        const.init()
        r = Relay(switch_on=0.5, switch_off=-0.5)
        r.init()
        r.connectInput(const)

        r.update()
        assert r.getOutput() == 1.0


class TestCoulombBlock:
    """Tests for the Coulomb block."""

    def test_coulomb_init(self):
        """Test Coulomb initialization."""
        c = Coulomb(static_gain=1.0, dynamic_gain=0.8, velocity_threshold=0.01)
        c.init()
        assert c.getOutput() == 0.0

    def test_coulomb_static_region(self):
        """Test Coulomb in static friction region."""
        c = Coulomb(static_gain=1.0, dynamic_gain=0.8, velocity_threshold=0.1)
        c.init()

        c.setInput(0.05)  # Below threshold
        c.update()
        # Static friction: -static_gain * (velocity / threshold) = -1 * (0.05/0.1) = -0.5
        assert c.getOutput() == pytest.approx(-0.5)

    def test_coulomb_dynamic_positive(self):
        """Test Coulomb dynamic friction positive velocity."""
        c = Coulomb(static_gain=1.0, dynamic_gain=0.8, velocity_threshold=0.1)
        c.init()

        c.setInput(1.0)  # Above threshold
        c.update()
        # Dynamic: -dynamic_gain = -0.8
        assert c.getOutput() == pytest.approx(-0.8)

    def test_coulomb_dynamic_negative(self):
        """Test Coulomb dynamic friction negative velocity."""
        c = Coulomb(static_gain=1.0, dynamic_gain=0.8, velocity_threshold=0.1)
        c.init()

        c.setInput(-1.0)  # Negative above threshold
        c.update()
        # Dynamic: +dynamic_gain = 0.8
        assert c.getOutput() == pytest.approx(0.8)


class TestVariableTransportDelayBlock:
    """Tests for the VariableTransportDelay block."""

    def test_vtd_init(self):
        """Test VariableTransportDelay initialization."""
        vtd = VariableTransportDelay(max_delay=1.0, initial_delay=0.1)
        vtd.init()
        assert vtd.getOutput() == 0.0

    def test_vtd_zero_delay(self):
        """Test VariableTransportDelay with zero delay."""
        vtd = VariableTransportDelay(max_delay=1.0, initial_delay=0.0)
        vtd.init()

        State.t = 0.0
        vtd.setInput(5.0, 0)  # Signal
        vtd.setInput(0.0, 1)  # Delay = 0
        vtd.update()
        # With zero delay, output should be current input
        assert vtd.getOutput() == pytest.approx(5.0)

    def test_vtd_connected(self):
        """Test VariableTransportDelay with connected blocks."""
        c1 = Constant(value=1.0)
        c2 = Constant(value=0.0)
        c1.init()
        c2.init()
        vtd = VariableTransportDelay(max_delay=1.0)
        vtd.init()
        vtd.connectInput(c1, 0)
        vtd.connectInput(c2, 1)

        State.t = 0.0
        vtd.update()
        assert isinstance(vtd.getOutput(), float)


# =============================================================================
# Observer Block Tests
# =============================================================================

import numpy as np

from src.osk.blocks.observers import ExtendedKalmanFilter, KalmanFilter, LuenbergerObserver


class TestLuenbergerObserverBlock:
    """Tests for the LuenbergerObserver block."""

    def test_luenberger_init(self):
        """Test LuenbergerObserver initialization."""
        obs = LuenbergerObserver(
            A=[[0.0]],
            B=[[1.0]],
            C=[[1.0]],
            L=[[1.0]]
        )
        obs.init()
        assert obs.getOutput() == 0.0

    def test_luenberger_state_estimate(self):
        """Test LuenbergerObserver state estimate."""
        obs = LuenbergerObserver(
            A=[[0.0]],
            B=[[1.0]],
            C=[[1.0]],
            L=[[1.0]]
        )
        obs.init()

        obs.setInput(1.0, 0)  # Control input
        obs.setInput(1.0, 1)  # Measurement
        obs.update()

        # State should start at 0, but update modifies x_hat_dot
        assert isinstance(obs.getOutput(), float)

    def test_luenberger_full_state(self):
        """Test LuenbergerObserver full state estimate."""
        obs = LuenbergerObserver(
            A=[[0.0]],
            B=[[1.0]],
            C=[[1.0]],
            L=[[1.0]]
        )
        obs.init()

        state = obs.getStateEstimate()
        assert len(state) == 1
        assert state[0] == 0.0

    def test_luenberger_connected(self):
        """Test LuenbergerObserver with connected blocks."""
        c1 = Constant(value=1.0)
        c2 = Constant(value=1.0)
        c1.init()
        c2.init()

        obs = LuenbergerObserver()
        obs.connectInput(c1, 0)
        obs.connectInput(c2, 1)
        obs.update()

        assert isinstance(obs.getOutput(), float)


class TestKalmanFilterBlock:
    """Tests for the KalmanFilter block."""

    def test_kalman_init(self):
        """Test KalmanFilter initialization."""
        kf = KalmanFilter(
            A=[[1.0]],
            B=[[1.0]],
            C=[[1.0]],
            Q=[[0.01]],
            R=[[0.1]]
        )
        kf.init()
        assert kf.getOutput() == 0.0

    def test_kalman_update(self):
        """Test KalmanFilter update step."""
        kf = KalmanFilter(
            A=[[1.0]],
            B=[[0.1]],
            C=[[1.0]],
            Q=[[0.01]],
            R=[[0.1]]
        )
        kf.init()

        kf.setInput(1.0, 0)  # Control input
        kf.setInput(1.0, 1)  # Measurement
        kf.update()

        # After update, state estimate should have moved toward measurement
        assert kf.getOutput() != 0.0

    def test_kalman_state_estimate(self):
        """Test KalmanFilter state estimate retrieval."""
        kf = KalmanFilter()
        kf.init()

        state = kf.getStateEstimate()
        assert len(state) >= 1

    def test_kalman_covariance(self):
        """Test KalmanFilter covariance retrieval."""
        kf = KalmanFilter()
        kf.init()

        P = kf.getCovariance()
        assert P.shape[0] == P.shape[1]  # Should be square

    def test_kalman_connected(self):
        """Test KalmanFilter with connected blocks."""
        c1 = Constant(value=1.0)
        c2 = Constant(value=0.5)
        c1.init()
        c2.init()

        kf = KalmanFilter()
        kf.init()
        kf.connectInput(c1, 0)
        kf.connectInput(c2, 1)
        kf.update()

        assert isinstance(kf.getOutput(), float)


class TestExtendedKalmanFilterBlock:
    """Tests for the ExtendedKalmanFilter block."""

    def test_ekf_init(self):
        """Test ExtendedKalmanFilter initialization."""
        ekf = ExtendedKalmanFilter(n_states=2)
        ekf.init()
        assert ekf.getOutput() == 0.0

    def test_ekf_update(self):
        """Test ExtendedKalmanFilter update."""
        ekf = ExtendedKalmanFilter(n_states=1)
        ekf.init()
        State.dt = 0.1

        ekf.setInput(1.0, 0)  # Control
        ekf.setInput(1.0, 1)  # Measurement
        ekf.update()

        # State should have been updated
        assert isinstance(ekf.getOutput(), float)

    def test_ekf_multiple_states(self):
        """Test ExtendedKalmanFilter with multiple states."""
        ekf = ExtendedKalmanFilter(n_states=3)
        ekf.init()

        assert ekf.getOutput(0) == 0.0
        assert ekf.getOutput(1) == 0.0
        assert ekf.getOutput(2) == 0.0

    def test_ekf_connected(self):
        """Test ExtendedKalmanFilter with connected blocks."""
        c1 = Constant(value=0.5)
        c2 = Constant(value=1.0)
        c1.init()
        c2.init()

        ekf = ExtendedKalmanFilter(n_states=1)
        ekf.init()
        ekf.connectInput(c1, 0)
        ekf.connectInput(c2, 1)
        State.dt = 0.1
        ekf.update()

        assert isinstance(ekf.getOutput(), float)


# =============================================================================
# Additional Continuous Block Tests
# =============================================================================

from src.osk.blocks.continuous import PIDController, StateSpace


class TestStateSpaceBlock:
    """Tests for the StateSpace block."""

    def test_state_space_init(self):
        """Test StateSpace initialization."""
        ss = StateSpace(
            A=[[0.0]],
            B=[[1.0]],
            C=[[1.0]],
            D=[[0.0]]
        )
        ss.init()
        assert ss.getOutput() == 0.0

    def test_state_space_with_initial_state(self):
        """Test StateSpace with initial state."""
        ss = StateSpace(
            A=[[0.0]],
            B=[[1.0]],
            C=[[1.0]],
            D=[[0.0]],
            initial_state=[5.0]
        )
        # Output is C*x, x[0]=5, so output=5
        ss.update()
        assert ss.getOutput() == pytest.approx(5.0)

    def test_state_space_feedthrough(self):
        """Test StateSpace with direct feedthrough."""
        ss = StateSpace(
            A=[[0.0]],
            B=[[0.0]],
            C=[[0.0]],
            D=[[2.0]]  # Direct feedthrough
        )
        ss.init()
        ss.setInput(3.0)
        ss.update()
        # Output is D*u = 2*3 = 6
        assert ss.getOutput() == pytest.approx(6.0)

    def test_state_space_connected(self):
        """Test StateSpace with connected block."""
        const = Constant(value=1.0)
        const.init()
        ss = StateSpace(D=[[1.0]])
        ss.init()
        ss.connectInput(const)
        ss.update()
        assert ss.getOutput() == pytest.approx(1.0)


class TestPIDControllerBlock:
    """Tests for the PIDController block."""

    def test_pid_proportional(self):
        """Test PIDController proportional term."""
        pid = PIDController(Kp=2.0, Ki=0.0, Kd=0.0)
        pid.init()
        pid.setInput(5.0)
        pid.update()
        # P term only: 2 * 5 = 10
        assert pid.getOutput() == pytest.approx(10.0)

    def test_pid_integral(self):
        """Test PIDController integral term."""
        pid = PIDController(Kp=0.0, Ki=1.0, Kd=0.0, initial_integrator=5.0)
        pid.init()
        pid.setInput(1.0)
        pid.update()
        # I term: Ki * integral[0] = 1 * 5 = 5
        assert pid.getOutput() == pytest.approx(5.0)

    def test_pid_derivative(self):
        """Test PIDController derivative term."""
        pid = PIDController(Kp=0.0, Ki=0.0, Kd=1.0, N=100.0)
        pid.init()
        State.dt = 0.01

        pid.setInput(0.0)
        pid.update()

        pid.setInput(1.0)
        pid.update()
        # D term uses filtered derivative
        assert pid.getOutput() != 0.0

    def test_pid_full(self):
        """Test PIDController with all terms."""
        pid = PIDController(Kp=1.0, Ki=0.5, Kd=0.1, N=100.0, initial_integrator=0.0)
        pid.init()
        State.dt = 0.01

        pid.setInput(1.0)
        pid.update()

        # Should have P + I + D contribution
        output = pid.getOutput()
        assert output > 0.0  # Error of 1 should give positive output

    def test_pid_connected(self):
        """Test PIDController with connected block."""
        const = Constant(value=1.0)
        const.init()
        pid = PIDController(Kp=2.0)
        pid.init()
        pid.connectInput(const)
        pid.update()
        assert pid.getOutput() == pytest.approx(2.0)


# =============================================================================
# Additional Sink Block Tests
# =============================================================================

from src.osk.blocks.sinks import Terminator


class TestTerminatorBlock:
    """Tests for the Terminator block."""

    def test_terminator_absorbs_signal(self):
        """Test Terminator absorbs signal."""
        term = Terminator()
        term.setInput(100.0)
        term.update()
        assert term.getOutput() == 0.0

    def test_terminator_no_output(self):
        """Test Terminator always returns 0."""
        term = Terminator()
        term.setInput(42.0)
        assert term.getOutput() == 0.0
        assert term.getOutput(1) == 0.0


# =============================================================================
# Additional Subsystem Block Tests
# =============================================================================

from src.osk.blocks.subsystems import Inport, Subsystem


class TestInportBlock:
    """Tests for the Inport block."""

    def test_inport_basic(self):
        """Test Inport basic operation."""
        inport = Inport(port_number=1)
        inport.setInput(10.0)
        inport.update()
        assert inport.getOutput() == 10.0

    def test_inport_port_number(self):
        """Test Inport port number."""
        inport = Inport(port_number=3)
        assert inport.port_number == 3

    def test_inport_float_port_number(self):
        """Test Inport handles float port number."""
        inport = Inport(port_number=2.0)
        assert inport.port_number == 2
        assert isinstance(inport.port_number, int)

    def test_inport_vector(self):
        """Test Inport vector pass-through."""
        inport = Inport(port_number=1)
        inport.setInput([1.0, 2.0, 3.0])
        inport.update()
        vec = inport.getOutputVector()
        assert vec == [1.0, 2.0, 3.0]

    def test_inport_connected(self):
        """Test Inport with connected block."""
        const = Constant(value=5.0)
        const.init()
        inport = Inport()
        inport.connectInput(const)
        inport.update()
        assert inport.getOutput() == 5.0


class TestSubsystemBlock:
    """Tests for the Subsystem block."""

    def test_subsystem_basic(self):
        """Test Subsystem basic operation."""
        sub = Subsystem(num_inputs=2, num_outputs=2)
        assert sub.num_inputs == 2
        assert sub.num_outputs == 2

    def test_subsystem_init(self):
        """Test Subsystem initialization."""
        sub = Subsystem(num_inputs=2, num_outputs=2)
        sub.init()
        assert sub.inputs == [0.0, 0.0]
        assert sub.outputs == [0.0, 0.0]

    def test_subsystem_passthrough(self):
        """Test Subsystem passthrough mode."""
        sub = Subsystem(num_inputs=2, num_outputs=2)
        sub.setInput(5.0, 0)
        sub.setInput(10.0, 1)
        sub.update()
        assert sub.getOutput(0) == 5.0
        assert sub.getOutput(1) == 10.0

    def test_subsystem_connected(self):
        """Test Subsystem with connected blocks."""
        c1 = Constant(value=3.0)
        c2 = Constant(value=7.0)
        c1.init()
        c2.init()

        sub = Subsystem(num_inputs=2, num_outputs=2)
        sub.connectInput(c1, 0)
        sub.connectInput(c2, 1)
        sub.update()
        assert sub.getOutput(0) == 3.0
        assert sub.getOutput(1) == 7.0

    def test_subsystem_float_params(self):
        """Test Subsystem handles float parameters."""
        sub = Subsystem(num_inputs=2.0, num_outputs=3.0)
        assert sub.num_inputs == 2
        assert sub.num_outputs == 3
        assert isinstance(sub.num_inputs, int)
        assert isinstance(sub.num_outputs, int)

    def test_subsystem_output_vectors(self):
        """Test Subsystem output vector functionality."""
        sub = Subsystem(num_inputs=1, num_outputs=2)
        # Test getOutputVector returns None initially
        assert sub.getOutputVector(0) is None

    def test_subsystem_set_outport_block(self):
        """Test Subsystem setOutportBlock."""
        outport = Outport(port_number=1)
        outport.setInput([1.0, 2.0, 3.0])
        outport.update()

        sub = Subsystem(num_inputs=1, num_outputs=1)
        sub.setOutportBlock(1, outport)
        sub.update()

        # Output vector should be available after update
        vec = sub.getOutputVector(0)
        assert vec is not None
        assert vec == [1.0, 2.0, 3.0]


class TestScopeSinkExtended:
    """Extended tests for the Scope sink block."""

    def test_scope_vector_input_from_mux(self):
        """Test Scope with vector input from Mux-like source."""
        mux = Mux(num_inputs=2)
        c1 = Constant(value=3.0)
        c2 = Constant(value=7.0)
        c1.init()
        c2.init()
        mux.connectInput(c1, 0)
        mux.connectInput(c2, 1)
        mux.update()

        scope = Scope(num_inputs=1)
        scope.connectInput(mux, 0)
        scope.setInputName("MuxSignal", 0)

        State.t = 0.0
        State.ready = 1
        scope.update()
        scope.rpt()

        # Check that vector is expanded into traces
        data = scope.getData()
        assert data["numInputs"] >= 2

    def test_scope_unconnected_inputs(self):
        """Test Scope only records connected inputs."""
        scope = Scope(num_inputs=3)
        const = Constant(value=5.0)
        const.init()

        # Only connect port 1
        scope.connectInput(const, 1)
        scope.setInputName("Signal1", 1)

        State.t = 0.0
        State.ready = 1
        scope.update()
        scope.rpt()

        data = scope.getData()
        # Only 1 trace should be recorded
        assert data["numInputs"] == 1

    def test_scope_set_input_with_vector(self):
        """Test Scope setInput with vector value."""
        scope = Scope(num_inputs=2)

        # Set port 0 with vector
        scope.setInput([1.0, 2.0, 3.0], 0)
        assert 0 in scope._vector_inputs
        assert scope.inputs[0] == 1.0

        # Set port 0 with scalar (should clear vector)
        scope.setInput(5.0, 0)
        assert 0 not in scope._vector_inputs
        assert scope.inputs[0] == 5.0

    def test_scope_input_name_beyond_range(self):
        """Test Scope setInputName with port beyond range."""
        scope = Scope(num_inputs=2)
        # Should not raise error
        scope.setInputName("OutOfRange", 10)


class TestToWorkspaceSink:
    """Tests for the ToWorkspace sink block."""

    def test_to_workspace_basic(self):
        """Test ToWorkspace basic recording."""
        tw = ToWorkspace(variable_name="my_signal")
        assert tw.variable_name == "my_signal"

    def test_to_workspace_recording(self):
        """Test ToWorkspace records data."""
        tw = ToWorkspace()
        const = Constant(value=5.0)
        const.init()
        tw.connectInput(const)

        State.t = 0.0
        State.ready = 1
        tw.update()
        tw.rpt()

        State.t = 0.1
        tw.update()
        tw.rpt()

        data = tw.getData()
        assert data["name"] == "simout"
        assert len(data["times"]) == 2
        assert len(data["values"]) == 2
        assert all(v == 5.0 for v in data["values"])

    def test_to_workspace_init_clears_data(self):
        """Test ToWorkspace init clears recorded data."""
        tw = ToWorkspace()
        tw.times = [1.0, 2.0]
        tw.values = [10.0, 20.0]
        tw.init()
        assert tw.times == []
        assert tw.values == []

    def test_to_workspace_get_output(self):
        """Test ToWorkspace getOutput returns current input."""
        tw = ToWorkspace()
        tw.setInput(7.5)
        assert tw.getOutput() == 7.5


class TestDisplaySinkExtended:
    """Extended tests for the Display sink block."""

    def test_display_connect_input(self):
        """Test Display connectInput method."""
        display = Display()
        const = Constant(value=3.0)
        const.init()
        display.connectInput(const)
        assert display.input_block is const

    def test_display_update_without_connection(self):
        """Test Display update without connected block."""
        display = Display()
        display.setInput(5.0)
        display.update()
        # Should still have the manually set value
        assert display.input == 5.0


class TestTerminatorSink:
    """Tests for the Terminator sink block."""

    def test_terminator_basic(self):
        """Test Terminator absorbs signal."""
        term = Terminator()
        term.setInput(100.0)
        assert term.input == 100.0

    def test_terminator_update(self):
        """Test Terminator update does nothing."""
        term = Terminator()
        term.setInput(100.0)
        term.update()
        # Input should remain
        assert term.input == 100.0

    def test_terminator_output(self):
        """Test Terminator always outputs 0."""
        term = Terminator()
        term.setInput(100.0)
        assert term.getOutput() == 0.0


class TestOutportExtended:
    """Extended tests for Outport block."""

    def test_outport_init_clears_state(self):
        """Test Outport init clears state."""
        outport = Outport(port_number=1)
        outport.output = 5.0
        outport._output_vector = [1.0, 2.0]
        outport.init()
        assert outport.output == 0.0
        assert outport._output_vector is None

    def test_outport_vector_from_connected_block(self):
        """Test Outport receives vector from connected block."""
        mux = Mux(num_inputs=2)
        c1 = Constant(value=1.0)
        c2 = Constant(value=2.0)
        c1.init()
        c2.init()
        mux.connectInput(c1, 0)
        mux.connectInput(c2, 1)
        mux.update()

        outport = Outport(port_number=1)
        outport.connectInput(mux)
        outport.update()

        vec = outport.getOutputVector()
        assert vec is not None
        assert vec == [1.0, 2.0]

    def test_outport_scalar_clears_vector(self):
        """Test Outport receiving scalar clears vector."""
        outport = Outport(port_number=1)
        outport._output_vector = [1.0, 2.0]
        outport.setInput(5.0)
        assert outport._output_vector is None
        assert outport.input == 5.0


class TestInportExtended:
    """Extended tests for Inport block."""

    def test_inport_init_clears_state(self):
        """Test Inport init clears state."""
        inport = Inport(port_number=1)
        inport.output = 5.0
        inport._output_vector = [1.0, 2.0]
        inport.init()
        assert inport.output == 0.0
        assert inport._output_vector is None

    def test_inport_vector_from_connected_block(self):
        """Test Inport receives vector from connected block."""
        mux = Mux(num_inputs=2)
        c1 = Constant(value=1.0)
        c2 = Constant(value=2.0)
        c1.init()
        c2.init()
        mux.connectInput(c1, 0)
        mux.connectInput(c2, 1)
        mux.update()

        inport = Inport(port_number=1)
        inport.connectInput(mux)
        inport.update()

        vec = inport.getOutputVector()
        assert vec is not None
        assert vec == [1.0, 2.0]

    def test_inport_scalar_clears_vector(self):
        """Test Inport receiving scalar clears vector."""
        inport = Inport(port_number=1)
        inport._output_vector = [1.0, 2.0]
        inport.setInput(5.0)
        assert inport._output_vector is None
        assert inport.input == 5.0

    def test_inport_connected_scalar(self):
        """Test Inport with connected block outputting scalar."""
        const = Constant(value=7.0)
        const.init()

        inport = Inport(port_number=1)
        inport.connectInput(const)
        inport.update()

        assert inport.getOutput() == 7.0
        assert inport.getOutputVector() is None


class TestIntegratorExtended:
    """Extended tests for the Integrator block."""

    def test_integrator_init(self):
        """Test Integrator init method."""
        integrator = Integrator(initial_condition=5.0)
        integrator.x[0] = 10.0  # Change value
        integrator.init()
        assert integrator.x[0] == 5.0
        assert integrator.x[1] == 0.0

    def test_integrator_limit_upper(self):
        """Test Integrator with upper limit."""
        integrator = Integrator(initial_condition=9.0, limit_output=True, upper_limit=10.0)
        integrator.setInput(1.0)  # Positive input
        integrator.x[0] = 10.0  # At upper limit
        integrator.update()
        # Derivative should be zeroed when at limit and trying to increase
        assert integrator.x[1] == 0.0

    def test_integrator_limit_lower(self):
        """Test Integrator with lower limit."""
        integrator = Integrator(initial_condition=1.0, limit_output=True, lower_limit=0.0)
        integrator.setInput(-1.0)  # Negative input
        integrator.x[0] = 0.0  # At lower limit
        integrator.update()
        # Derivative should be zeroed when at limit and trying to decrease
        assert integrator.x[1] == 0.0

    def test_integrator_output_clamping(self):
        """Test Integrator output clamping."""
        integrator = Integrator(initial_condition=5.0, limit_output=True, upper_limit=3.0, lower_limit=-3.0)
        assert integrator.getOutput() == 3.0  # Clamped to upper

        integrator.x[0] = -5.0
        assert integrator.getOutput() == -3.0  # Clamped to lower


class TestDerivativeExtended:
    """Extended tests for the Derivative block."""

    def test_derivative_init(self):
        """Test Derivative init method."""
        deriv = Derivative(coefficient=50.0)
        deriv.x[0] = 10.0
        deriv.output = 5.0
        deriv.init()
        assert deriv.x[0] == 0.0
        assert deriv.x[1] == 0.0
        assert deriv.output == 0.0

    def test_derivative_with_connected_block(self):
        """Test Derivative with connected input block."""
        const = Constant(value=2.0)
        const.init()

        deriv = Derivative(coefficient=100.0)
        deriv.connectInput(const)
        assert deriv.input_block is const

        deriv.update()
        # With const input of 2.0 and x[0] = 0, output = 100 * (2 - 0) = 200
        assert deriv.getOutput() == 200.0


class TestTransferFunctionExtended:
    """Extended tests for the TransferFunction block."""

    def test_tf_static_gain(self):
        """Test TransferFunction as static gain (order 0)."""
        tf = TransferFunction(numerator=[2.0], denominator=[1.0])
        tf.setInput(3.0)
        tf.update()
        # Output should be 2.0/1.0 * 3.0 = 6.0
        assert tf.getOutput() == pytest.approx(6.0)

    def test_tf_init(self):
        """Test TransferFunction init method."""
        tf = TransferFunction(numerator=[1.0], denominator=[1.0, 1.0])
        tf.states[0][0] = 5.0
        tf.output = 10.0
        tf.init()
        assert tf.states[0][0] == 0.0
        assert tf.output == 0.0

    def test_tf_connect_input(self):
        """Test TransferFunction with connected input block."""
        const = Constant(value=1.0)
        const.init()

        tf = TransferFunction(numerator=[1.0], denominator=[1.0, 1.0])
        tf.connectInput(const)
        assert tf.input_block is const

        tf.update()
        # Should use input from connected block
        assert tf.input == 1.0

    def test_tf_higher_order(self):
        """Test TransferFunction with higher order."""
        # Second order: 1 / (s^2 + 2s + 1)
        tf = TransferFunction(numerator=[1.0], denominator=[1.0, 2.0, 1.0])
        assert tf.order == 2
        assert len(tf.states) == 2

        tf.setInput(1.0)
        tf.update()
        # Should execute without error
        assert isinstance(tf.getOutput(), float)


class TestStateSpaceExtended:
    """Extended tests for the StateSpace block."""

    def test_state_space_init_custom(self):
        """Test StateSpace with custom initial state."""
        A = [[0, 1], [-1, -1]]
        B = [[0], [1]]
        C = [[1, 0]]
        D = [[0]]
        initial = [1.0, 0.5]

        ss = StateSpace(A=A, B=B, C=C, D=D, initial_state=initial)
        assert len(ss.states) == 2
        assert ss.states[0][0] == 1.0
        assert ss.states[1][0] == 0.5

    def test_state_space_connect_input(self):
        """Test StateSpace with connected input block."""
        const = Constant(value=2.0)
        const.init()

        ss = StateSpace()
        ss.connectInput(const)
        assert ss.input_block is const

        ss.update()
        assert ss.input == 2.0


class TestPIDControllerExtended:
    """Extended tests for the PIDController block."""

    def test_pid_init(self):
        """Test PIDController init method."""
        pid = PIDController(Kp=1.0, Ki=0.5, Kd=0.1, initial_integrator=2.0)
        pid.integral[0] = 10.0
        pid.deriv_state[0] = 5.0
        pid.output = 20.0
        pid.init()
        assert pid.integral[0] == 2.0
        assert pid.deriv_state[0] == 0.0
        assert pid.output == 0.0

    def test_pid_connect_input(self):
        """Test PIDController with connected input block."""
        const = Constant(value=1.0)
        const.init()

        pid = PIDController(Kp=1.0)
        pid.connectInput(const)
        assert pid.input_block is const

        pid.update()
        assert pid.input == 1.0


# =============================================================================
# Extended Math Ops Tests for Full Coverage
# =============================================================================


class TestProductExtended:
    """Extended tests for Product block to cover connectInput and division."""

    def test_product_connect_input(self):
        """Test Product connectInput method."""
        const1 = Constant(value=3.0)
        const2 = Constant(value=4.0)
        const1.init()
        const2.init()

        prod = Product(operations='**')
        prod.connectInput(const1, 0)
        prod.connectInput(const2, 1)

        assert prod.input_blocks[0] is const1
        assert prod.input_blocks[1] is const2

        prod.update()
        assert prod.getOutput() == pytest.approx(12.0)

    def test_product_division_by_zero(self):
        """Test Product handles division by near-zero."""
        prod = Product(operations='*/')
        prod.setInput(10.0, 0)
        prod.setInput(0.0, 1)  # Near zero
        prod.update()
        # Should handle gracefully without crashing
        assert prod.getOutput() != float('inf')


class TestSignExtended:
    """Extended tests for Sign block."""

    def test_sign_connect_input(self):
        """Test Sign connectInput method."""
        const = Constant(value=-5.0)
        const.init()

        sign = Sign()
        sign.connectInput(const)
        assert sign.input_block is const

        sign.update()
        assert sign.getOutput() == -1.0


class TestSaturationExtended:
    """Extended tests for Saturation block."""

    def test_saturation_connect_input(self):
        """Test Saturation connectInput method."""
        const = Constant(value=100.0)
        const.init()

        sat = Saturation(upper_limit=10.0, lower_limit=-10.0)
        sat.connectInput(const)
        assert sat.input_block is const

        sat.update()
        assert sat.getOutput() == 10.0


class TestMathFunctionExtended:
    """Extended tests for MathFunction block."""

    def test_math_function_connect_input(self):
        """Test MathFunction connectInput method."""
        const = Constant(value=1.0)
        const.init()

        mf = MathFunction(function='exp')
        mf.connectInput(const)
        assert mf.input_block is const

        mf.update()
        assert mf.getOutput() == pytest.approx(math.e)

    def test_math_function_log(self):
        """Test MathFunction log function."""
        mf = MathFunction(function='log')
        mf.setInput(math.e)
        mf.update()
        assert mf.getOutput() == pytest.approx(1.0)

    def test_math_function_log_negative(self):
        """Test MathFunction log with near-zero input."""
        mf = MathFunction(function='log')
        mf.setInput(0.0)
        mf.update()
        # Should not crash, uses EPS
        assert isinstance(mf.getOutput(), float)

    def test_math_function_log10(self):
        """Test MathFunction log10 function."""
        mf = MathFunction(function='log10')
        mf.setInput(100.0)
        mf.update()
        assert mf.getOutput() == pytest.approx(2.0)

    def test_math_function_sqrt(self):
        """Test MathFunction sqrt function."""
        mf = MathFunction(function='sqrt')
        mf.setInput(16.0)
        mf.update()
        assert mf.getOutput() == pytest.approx(4.0)

    def test_math_function_sqrt_negative(self):
        """Test MathFunction sqrt with negative input."""
        mf = MathFunction(function='sqrt')
        mf.setInput(-5.0)
        mf.update()
        assert mf.getOutput() == 0.0

    def test_math_function_square(self):
        """Test MathFunction square function."""
        mf = MathFunction(function='square')
        mf.setInput(5.0)
        mf.update()
        assert mf.getOutput() == pytest.approx(25.0)

    def test_math_function_pow(self):
        """Test MathFunction pow function."""
        mf = MathFunction(function='pow', exponent=3.0)
        mf.setInput(2.0)
        mf.update()
        assert mf.getOutput() == pytest.approx(8.0)

    def test_math_function_reciprocal(self):
        """Test MathFunction reciprocal function."""
        mf = MathFunction(function='reciprocal')
        mf.setInput(5.0)
        mf.update()
        assert mf.getOutput() == pytest.approx(0.2)

    def test_math_function_reciprocal_zero(self):
        """Test MathFunction reciprocal with zero."""
        mf = MathFunction(function='reciprocal')
        mf.setInput(0.0)
        mf.update()
        # Should handle gracefully
        assert mf.getOutput() != float('inf')

    def test_math_function_unknown(self):
        """Test MathFunction with unknown function (pass-through)."""
        mf = MathFunction(function='unknown_func')
        mf.setInput(42.0)
        mf.update()
        assert mf.getOutput() == 42.0


class TestTrigonometryExtended:
    """Extended tests for Trigonometry block."""

    def test_trig_connect_input(self):
        """Test Trigonometry connectInput method."""
        const = Constant(value=0.0)
        const.init()

        trig = Trigonometry(function='sin')
        trig.connectInput(const)
        assert trig.input_block is const

        trig.update()
        assert trig.getOutput() == pytest.approx(0.0)

    def test_trig_tan(self):
        """Test Trigonometry tan function."""
        trig = Trigonometry(function='tan')
        trig.setInput(0.0)
        trig.update()
        assert trig.getOutput() == pytest.approx(0.0)

    def test_trig_asin(self):
        """Test Trigonometry asin function."""
        trig = Trigonometry(function='asin')
        trig.setInput(0.5)
        trig.update()
        assert trig.getOutput() == pytest.approx(math.asin(0.5))

    def test_trig_acos(self):
        """Test Trigonometry acos function."""
        trig = Trigonometry(function='acos')
        trig.setInput(0.5)
        trig.update()
        assert trig.getOutput() == pytest.approx(math.acos(0.5))

    def test_trig_atan(self):
        """Test Trigonometry atan function."""
        trig = Trigonometry(function='atan')
        trig.setInput(1.0)
        trig.update()
        assert trig.getOutput() == pytest.approx(math.atan(1.0))

    def test_trig_sinh(self):
        """Test Trigonometry sinh function."""
        trig = Trigonometry(function='sinh')
        trig.setInput(1.0)
        trig.update()
        assert trig.getOutput() == pytest.approx(math.sinh(1.0))

    def test_trig_cosh(self):
        """Test Trigonometry cosh function."""
        trig = Trigonometry(function='cosh')
        trig.setInput(1.0)
        trig.update()
        assert trig.getOutput() == pytest.approx(math.cosh(1.0))

    def test_trig_tanh(self):
        """Test Trigonometry tanh function."""
        trig = Trigonometry(function='tanh')
        trig.setInput(1.0)
        trig.update()
        assert trig.getOutput() == pytest.approx(math.tanh(1.0))

    def test_trig_overflow_handling(self):
        """Test Trigonometry handles overflow."""
        trig = Trigonometry(function='sinh')
        trig.setInput(1000.0)  # Large value that may overflow
        trig.update()
        # Should handle gracefully
        assert isinstance(trig.getOutput(), float)


class TestDeadZoneExtended:
    """Extended tests for DeadZone block."""

    def test_dead_zone_connect_input(self):
        """Test DeadZone connectInput method."""
        const = Constant(value=0.0)
        const.init()

        dz = DeadZone(start=-0.5, end=0.5)
        dz.connectInput(const)
        assert dz.input_block is const

        dz.update()
        assert dz.getOutput() == 0.0


class TestSwitchExtended:
    """Extended tests for Switch block."""

    def test_switch_connect_input(self):
        """Test Switch connectInput method."""
        const1 = Constant(value=10.0)
        control = Constant(value=1.0)
        const2 = Constant(value=20.0)
        const1.init()
        control.init()
        const2.init()

        sw = Switch(threshold=0.5, criteria='gte')
        sw.connectInput(const1, 0)
        sw.connectInput(control, 1)
        sw.connectInput(const2, 2)

        sw.update()
        # Control (1.0) >= threshold (0.5), so use first input (10.0)
        assert sw.getOutput() == 10.0

    def test_switch_gt_criteria(self):
        """Test Switch with 'gt' criteria."""
        sw = Switch(threshold=0.5, criteria='gt')
        sw.setInput(10.0, 0)  # First input
        sw.setInput(0.5, 1)   # Control - exactly at threshold
        sw.setInput(20.0, 2)  # Second input
        sw.update()
        # Control (0.5) is NOT > threshold (0.5), so use second input
        assert sw.getOutput() == 20.0

    def test_switch_neq_criteria(self):
        """Test Switch with 'neq' criteria."""
        sw = Switch(threshold=0.5, criteria='neq')
        sw.setInput(10.0, 0)  # First input
        sw.setInput(0.5, 1)   # Control - exactly at threshold
        sw.setInput(20.0, 2)  # Second input
        sw.update()
        # Control == threshold, so use second input
        assert sw.getOutput() == 20.0

        # Now try with different control value
        sw.setInput(1.0, 1)  # Control != threshold
        sw.update()
        # Control != threshold, so use first input
        assert sw.getOutput() == 10.0


class TestMuxExtended:
    """Extended tests for Mux block."""

    def test_mux_init(self):
        """Test Mux init method."""
        mux = Mux(num_inputs=3)
        mux.inputs = [1.0, 2.0, 3.0]
        mux.outputs = [1.0, 2.0, 3.0]
        mux.init()
        assert mux.inputs == [0.0, 0.0, 0.0]
        assert mux.outputs == [0.0, 0.0, 0.0]

    def test_mux_connect_input(self):
        """Test Mux connectInput method."""
        const1 = Constant(value=1.0)
        const2 = Constant(value=2.0)
        const1.init()
        const2.init()

        mux = Mux(num_inputs=2)
        mux.connectInput(const1, 0)
        mux.connectInput(const2, 1)

        assert mux.input_blocks[0] is const1
        assert mux.input_blocks[1] is const2

        mux.update()
        assert mux.getOutput(0) == 1.0
        assert mux.getOutput(1) == 2.0

    def test_mux_get_output_out_of_range(self):
        """Test Mux getOutput with out of range port."""
        mux = Mux(num_inputs=2)
        mux.setInput(1.0, 0)
        mux.setInput(2.0, 1)
        mux.update()
        assert mux.getOutput(10) == 0.0  # Out of range


class TestDemuxExtended:
    """Extended tests for Demux block."""

    def test_demux_init(self):
        """Test Demux init method."""
        demux = Demux(num_outputs=3)
        demux.input_vector = [1.0, 2.0, 3.0]
        demux.outputs = [1.0, 2.0, 3.0]
        demux.init()
        assert demux.input_vector == [0.0, 0.0, 0.0]
        assert demux.outputs == [0.0, 0.0, 0.0]

    def test_demux_set_input_vector(self):
        """Test Demux setInput with vector."""
        demux = Demux(num_outputs=3)
        demux.setInput([1.0, 2.0, 3.0])
        demux.update()
        assert demux.getOutput(0) == 1.0
        assert demux.getOutput(1) == 2.0
        assert demux.getOutput(2) == 3.0

    def test_demux_from_mux(self):
        """Test Demux connected to Mux (vector transfer)."""
        mux = Mux(num_inputs=2)
        mux.setInput(5.0, 0)
        mux.setInput(10.0, 1)
        mux.update()

        demux = Demux(num_outputs=2)
        demux.connectInput(mux)
        demux.update()

        assert demux.getOutput(0) == 5.0
        assert demux.getOutput(1) == 10.0

    def test_demux_from_scalar(self):
        """Test Demux connected to scalar block."""
        const = Constant(value=42.0)
        const.init()

        demux = Demux(num_outputs=2)
        demux.connectInput(const)
        demux.update()

        assert demux.getOutput(0) == 42.0
        assert demux.getOutput(1) == 0.0

    def test_demux_get_output_out_of_range(self):
        """Test Demux getOutput with out of range port."""
        demux = Demux(num_outputs=2)
        demux.setInput([1.0, 2.0])
        demux.update()
        assert demux.getOutput(10) == 0.0  # Out of range


class TestReshapeExtended:
    """Extended tests for Reshape block."""

    def test_reshape_init(self):
        """Test Reshape init method."""
        rs = Reshape()
        rs.input = 5.0
        rs._input_vector = [1.0, 2.0]
        rs._output_vector = [1.0, 2.0]
        rs.init()
        assert rs.input == 0.0
        assert rs._input_vector is None
        assert rs._output_vector is None

    def test_reshape_set_input_vector(self):
        """Test Reshape setInput with vector."""
        rs = Reshape()
        rs.setInput([1.0, 2.0, 3.0])
        assert rs._input_vector == [1.0, 2.0, 3.0]
        assert rs.input == 1.0

    def test_reshape_set_input_scalar(self):
        """Test Reshape setInput with scalar."""
        rs = Reshape()
        rs.setInput(5.0)
        assert rs.input == 5.0
        assert rs._input_vector is None

    def test_reshape_from_mux(self):
        """Test Reshape connected to Mux."""
        mux = Mux(num_inputs=2)
        mux.setInput(5.0, 0)
        mux.setInput(10.0, 1)
        mux.update()

        rs = Reshape()
        rs.connectInput(mux)
        rs.update()

        assert rs.getOutput() == 5.0
        vec = rs.getOutputVector()
        assert vec == [5.0, 10.0]

    def test_reshape_from_scalar(self):
        """Test Reshape connected to scalar block."""
        const = Constant(value=42.0)
        const.init()

        rs = Reshape()
        rs.connectInput(const)
        rs.update()

        assert rs.getOutput() == 42.0
        assert rs.getOutputVector() is None


# =============================================================================
# Nonlinear Block Extended Tests
# =============================================================================


class TestNonlinearBlocks:
    """Extended tests for nonlinear blocks."""

    def test_lookup_table_1d_connect_input(self):
        """Test LookupTable1D with connected input."""
        from src.osk.blocks.nonlinear import LookupTable1D

        const = Constant(value=1.5)
        const.init()

        lut = LookupTable1D(x_data=[0, 1, 2], y_data=[0, 10, 20])
        lut.connectInput(const)
        lut.update()

        assert lut.getOutput() == pytest.approx(15.0)  # Linear interpolation

    def test_lookup_table_1d_extrapolation_low(self):
        """Test LookupTable1D extrapolation below range."""
        from src.osk.blocks.nonlinear import LookupTable1D

        lut = LookupTable1D(x_data=[0, 1, 2], y_data=[0, 10, 20])
        lut.setInput(-1.0)
        lut.update()
        # Linear extrapolation continues below range
        assert isinstance(lut.getOutput(), float)

    def test_lookup_table_1d_extrapolation_high(self):
        """Test LookupTable1D extrapolation above range."""
        from src.osk.blocks.nonlinear import LookupTable1D

        lut = LookupTable1D(x_data=[0, 1, 2], y_data=[0, 10, 20])
        lut.setInput(5.0)
        lut.update()
        # Linear extrapolation continues above range
        assert isinstance(lut.getOutput(), float)

    def test_lookup_table_2d_connect_input(self):
        """Test LookupTable2D with connected inputs."""
        from src.osk.blocks.nonlinear import LookupTable2D

        const_x = Constant(value=0.5)
        const_y = Constant(value=0.5)
        const_x.init()
        const_y.init()

        z_data = [[0, 1], [2, 3]]  # 2x2 table
        lut = LookupTable2D(x_data=[0, 1], y_data=[0, 1], z_data=z_data)
        lut.connectInput(const_x, 0)
        lut.connectInput(const_y, 1)
        lut.update()

        # Bilinear interpolation at center
        assert isinstance(lut.getOutput(), float)

    def test_quantizer_connect_input(self):
        """Test Quantizer with connected input."""
        from src.osk.blocks.nonlinear import Quantizer

        const = Constant(value=2.3)
        const.init()

        quant = Quantizer(interval=0.5)
        quant.connectInput(const)
        quant.update()

        # 2.3 rounds to 2.5
        assert quant.getOutput() == pytest.approx(2.5)

    def test_relay_connect_input(self):
        """Test Relay with connected input."""
        from src.osk.blocks.nonlinear import Relay

        const = Constant(value=1.0)
        const.init()

        relay = Relay(switch_on=0.5, switch_off=-0.5, output_on=1.0, output_off=-1.0)
        relay.connectInput(const)
        relay.update()

        # 1.0 > switch_on (0.5), so output_on
        assert relay.getOutput() == 1.0

    def test_relay_hysteresis(self):
        """Test Relay hysteresis behavior."""
        from src.osk.blocks.nonlinear import Relay

        relay = Relay(switch_on=0.5, switch_off=-0.5, output_on=1.0, output_off=-1.0)

        # Start below switch_off
        relay.setInput(-1.0)
        relay.update()
        assert relay.getOutput() == -1.0

        # Go above switch_on
        relay.setInput(1.0)
        relay.update()
        assert relay.getOutput() == 1.0

        # Drop between switch_off and switch_on (stays on)
        relay.setInput(0.0)
        relay.update()
        assert relay.getOutput() == 1.0

        # Drop below switch_off
        relay.setInput(-1.0)
        relay.update()
        assert relay.getOutput() == -1.0

    def test_coulomb_friction_connect_input(self):
        """Test Coulomb friction with connected input."""
        from src.osk.blocks.nonlinear import Coulomb

        const = Constant(value=5.0)
        const.init()

        coulomb = Coulomb(static_gain=2.0, dynamic_gain=1.0, velocity_threshold=0.1)
        coulomb.connectInput(const)
        coulomb.update()

        # velocity > threshold, produces sign(velocity) * dynamic_gain
        assert isinstance(coulomb.getOutput(), float)

    def test_coulomb_friction_static(self):
        """Test Coulomb friction static region."""
        from src.osk.blocks.nonlinear import Coulomb

        coulomb = Coulomb(static_gain=2.0, dynamic_gain=1.0, velocity_threshold=0.1)
        coulomb.setInput(0.05)  # Below threshold
        coulomb.update()

        # Within threshold, uses static interpolation
        assert isinstance(coulomb.getOutput(), float)

    def test_variable_transport_delay(self):
        """Test VariableTransportDelay block."""
        from src.osk.blocks.nonlinear import VariableTransportDelay

        const = Constant(value=5.0)
        const.init()

        vtd = VariableTransportDelay(max_delay=1.0, initial_delay=0.1)
        vtd.connectInput(const)

        State.t = 0.0
        vtd.update()
        vtd.rpt()

        State.t = 0.5
        vtd.update()
        vtd.rpt()

        # Output should reflect delayed input
        assert isinstance(vtd.getOutput(), float)


# =============================================================================
# Observer Block Extended Tests
# =============================================================================


class TestObserverBlocks:
    """Extended tests for observer blocks."""

    def test_luenberger_observer_connect(self):
        """Test LuenbergerObserver with connected inputs."""
        from src.osk.blocks.observers import LuenbergerObserver

        u_block = Constant(value=1.0)
        y_block = Constant(value=0.5)
        u_block.init()
        y_block.init()

        A = [[0, 1], [-1, -1]]
        B = [[0], [1]]
        C = [[1, 0]]
        L = [[1], [1]]

        obs = LuenbergerObserver(A=A, B=B, C=C, L=L)
        obs.connectInput(u_block, 0)
        obs.connectInput(y_block, 1)
        obs.update()

        assert isinstance(obs.getOutput(), float)

    def test_kalman_filter_connect(self):
        """Test KalmanFilter with connected inputs."""
        from src.osk.blocks.observers import KalmanFilter

        u_block = Constant(value=1.0)
        y_block = Constant(value=0.5)
        u_block.init()
        y_block.init()

        A = [[1]]
        B = [[1]]
        C = [[1]]
        Q = [[0.1]]
        R = [[0.1]]

        kf = KalmanFilter(A=A, B=B, C=C, Q=Q, R=R)
        kf.connectInput(u_block, 0)
        kf.connectInput(y_block, 1)
        kf.update()

        assert isinstance(kf.getOutput(), float)

    def test_kalman_filter_rpt(self):
        """Test KalmanFilter rpt method."""
        from src.osk.blocks.observers import KalmanFilter

        kf = KalmanFilter()
        State.ready = 1
        kf.rpt()  # Should not crash

    def test_extended_kalman_filter_connect(self):
        """Test ExtendedKalmanFilter with connected inputs."""
        from src.osk.blocks.observers import ExtendedKalmanFilter

        u_block = Constant(value=1.0)
        y_block = Constant(value=0.5)
        u_block.init()
        y_block.init()

        ekf = ExtendedKalmanFilter(n_states=1, Q=[[0.1]], R=[[0.1]])
        ekf.connectInput(u_block, 0)
        ekf.connectInput(y_block, 1)
        ekf.update()

        assert isinstance(ekf.getOutput(), float)

    def test_extended_kalman_filter_rpt(self):
        """Test ExtendedKalmanFilter rpt method."""
        from src.osk.blocks.observers import ExtendedKalmanFilter

        ekf = ExtendedKalmanFilter()
        State.ready = 1
        ekf.rpt()  # Should not crash


# =============================================================================
# Sink Block Extended Tests
# =============================================================================


class TestSinkBlocksExtended:
    """Extended tests for sink blocks."""

    def test_scope_set_input_name(self):
        """Test Scope setInputName method."""
        scope = Scope(num_inputs=2)
        scope.setInputName("Signal1", 0)
        scope.setInputName("Signal2", 1)

        assert scope.input_names[0] == "Signal1"
        assert scope.input_names[1] == "Signal2"

    def test_scope_vector_input(self):
        """Test Scope with vector input (from Mux)."""
        mux = Mux(num_inputs=2)
        mux.setInput(1.0, 0)
        mux.setInput(2.0, 1)
        mux.update()

        scope = Scope(num_inputs=1)
        scope.connectInput(mux, 0)
        scope.update()
        scope.rpt()

        # Should record vector elements separately
        data = scope.getData()
        assert "numInputs" in data

    def test_display_connect_input(self):
        """Test Display with connected input."""
        const = Constant(value=42.0)
        const.init()

        display = Display()
        display.connectInput(const)
        display.update()
        State.ready = 1
        display.rpt()  # rpt() sets current_value

        assert display.getOutput() == 42.0

    def test_to_workspace_connect_input(self):
        """Test ToWorkspace with connected input."""
        const = Constant(value=10.0)
        const.init()

        ws = ToWorkspace(variable_name="test_var")
        ws.connectInput(const)
        ws.update()
        State.ready = 1
        ws.rpt()

        assert ws.getOutput() == 10.0
        data = ws.getData()
        assert data["name"] == "test_var"  # ToWorkspace uses 'name', not 'variableName'


class TestObserverBlocksExtended:
    """Extended tests for observer blocks to increase coverage."""

    def test_luenberger_init_with_initial_state(self):
        """Test LuenbergerObserver init() with _initial_state set."""
        from src.osk.blocks.observers import LuenbergerObserver
        import numpy as np

        obs = LuenbergerObserver()
        obs._initial_state = [5.0]
        obs.init()
        assert obs.x_hat[0] == 5.0

    def test_luenberger_propagate_states(self):
        """Test LuenbergerObserver propagateStates method."""
        from src.osk.blocks.observers import LuenbergerObserver
        import numpy as np

        State.dt = 0.01
        obs = LuenbergerObserver()
        obs.x_hat = np.array([1.0])
        obs.x_hat_dot = np.array([10.0])
        obs.propagateStates()
        assert obs.x_hat[0] == pytest.approx(1.1, rel=0.01)

    def test_luenberger_get_state_estimate(self):
        """Test LuenbergerObserver getStateEstimate method."""
        from src.osk.blocks.observers import LuenbergerObserver
        import numpy as np

        obs = LuenbergerObserver()
        obs.x_hat = np.array([3.14])
        estimate = obs.getStateEstimate()
        assert estimate[0] == 3.14
        # Verify it's a copy
        estimate[0] = 0.0
        assert obs.x_hat[0] == 3.14

    def test_luenberger_get_output_invalid_port(self):
        """Test LuenbergerObserver getOutput with invalid port."""
        from src.osk.blocks.observers import LuenbergerObserver

        obs = LuenbergerObserver()
        obs.output = 99.0
        # Port beyond state vector returns self.output
        result = obs.getOutput(port=100)
        assert result == 99.0

    def test_kalman_filter_init(self):
        """Test KalmanFilter init() method."""
        from src.osk.blocks.observers import KalmanFilter
        import numpy as np

        kf = KalmanFilter()
        kf.x_hat = np.array([5.0])
        kf.P = np.array([[10.0]])
        kf.init()
        assert kf.x_hat[0] == 0.0
        assert kf.P[0, 0] == 1.0

    def test_kalman_filter_get_covariance(self):
        """Test KalmanFilter getCovariance method."""
        from src.osk.blocks.observers import KalmanFilter
        import numpy as np

        kf = KalmanFilter()
        kf.P = np.array([[2.5]])
        cov = kf.getCovariance()
        assert cov[0, 0] == 2.5
        # Verify it's a copy
        cov[0, 0] = 0.0
        assert kf.P[0, 0] == 2.5

    def test_kalman_filter_get_output_invalid_port(self):
        """Test KalmanFilter getOutput with invalid port."""
        from src.osk.blocks.observers import KalmanFilter

        kf = KalmanFilter()
        kf.output = 42.0
        result = kf.getOutput(port=50)
        assert result == 42.0

    def test_extended_kalman_filter_init(self):
        """Test ExtendedKalmanFilter init() method."""
        from src.osk.blocks.observers import ExtendedKalmanFilter
        import numpy as np

        ekf = ExtendedKalmanFilter(n_states=2)
        ekf.x_hat = np.array([1.0, 2.0])
        ekf.init()
        assert ekf.x_hat[0] == 0.0
        assert ekf.x_hat[1] == 0.0

    def test_extended_kalman_filter_get_output_port1(self):
        """Test ExtendedKalmanFilter getOutput with port 1."""
        from src.osk.blocks.observers import ExtendedKalmanFilter
        import numpy as np

        ekf = ExtendedKalmanFilter(n_states=2)
        ekf.x_hat = np.array([1.0, 2.0])
        assert ekf.getOutput(0) == 1.0
        assert ekf.getOutput(1) == 2.0

    def test_extended_kalman_filter_get_output_invalid_port(self):
        """Test ExtendedKalmanFilter getOutput with invalid port."""
        from src.osk.blocks.observers import ExtendedKalmanFilter

        ekf = ExtendedKalmanFilter(n_states=1)
        ekf.output = 99.0
        result = ekf.getOutput(port=10)
        assert result == 99.0

    def test_luenberger_with_2d_matrices(self):
        """Test LuenbergerObserver with proper 2D matrices."""
        from src.osk.blocks.observers import LuenbergerObserver
        import numpy as np

        A = [[0, 1], [-1, -1]]
        B = [[0], [1]]
        C = [[1, 0]]
        L = [[1], [1]]
        obs = LuenbergerObserver(A=A, B=B, C=C, L=L)
        assert obs.n == 2
        assert obs.m == 1
        assert obs.p == 1

    def test_kalman_filter_with_singular_S(self):
        """Test KalmanFilter handles near-singular innovation covariance."""
        from src.osk.blocks.observers import KalmanFilter
        import numpy as np

        # Create filter with very small R (may cause numerical issues)
        kf = KalmanFilter(R=[[1e-15]])
        kf.inputs = [0.0, 1.0]
        # Should not raise error
        kf.update()

    def test_extended_kalman_filter_update(self):
        """Test ExtendedKalmanFilter update with inputs."""
        from src.osk.blocks.observers import ExtendedKalmanFilter

        State.dt = 0.01
        ekf = ExtendedKalmanFilter(n_states=1)
        ekf.inputs = [1.0, 0.5]  # u, y
        ekf.update()
        assert isinstance(ekf.output, float)


class TestDiscreteBlocksExtended:
    """Extended tests for discrete blocks."""

    def test_discrete_transfer_function_higher_order(self):
        """Test DiscreteTransferFunction with second order system."""
        from src.osk.blocks.discrete import DiscreteTransferFunction

        # Second order: (1 + z^-1) / (1 + 0.5*z^-1 + 0.25*z^-2)
        State.t = 0.0
        State.dt = 0.01

        dtf = DiscreteTransferFunction(
            numerator=[1.0, 1.0],
            denominator=[1.0, 0.5, 0.25],
            sample_time=0.01
        )
        dtf.init()
        dtf.input = 1.0

        # Run multiple iterations to exercise buffer operations
        outputs = []
        for i in range(5):
            State.t = i * 0.01
            dtf.update()
            outputs.append(dtf.getOutput())

        assert len(outputs) == 5
        assert all(isinstance(o, float) for o in outputs)


class TestNonlinearBlocksExtended:
    """Extended tests for nonlinear blocks."""

    def test_lookup_table_1d_with_different_methods(self):
        """Test LookupTable1D with different interpolation."""
        from src.osk.blocks.nonlinear import LookupTable1D

        # Test with default method (linear)
        lut = LookupTable1D(
            x_data=[0, 1, 2],
            y_data=[0, 10, 20]
        )
        lut.input = 0.5
        lut.update()
        assert lut.getOutput() == 5.0

    def test_quantizer_connect_input(self):
        """Test Quantizer with connected input."""
        from src.osk.blocks.nonlinear import Quantizer
        from src.osk.blocks.sources import Constant

        const = Constant(value=3.7)
        const.init()

        q = Quantizer(interval=1.0)
        q.connectInput(const)
        q.update()

        assert q.getOutput() == 4.0

    def test_variable_transport_delay_with_delay(self):
        """Test VariableTransportDelay over time."""
        from src.osk.blocks.nonlinear import VariableTransportDelay

        State.t = 0.0
        State.dt = 0.01

        vtd = VariableTransportDelay(max_delay=0.1)
        vtd.init()

        # Simulate several steps
        for i in range(20):
            State.t = i * 0.01
            vtd.setInput(float(i), 0)  # Signal
            vtd.setInput(0.05, 1)  # Delay time
            vtd.update()

        assert isinstance(vtd.getOutput(), float)


class TestSignalProcessingExtended:
    """Extended tests for signal processing blocks."""

    def test_moving_average_with_time(self):
        """Test MovingAverage over multiple time steps."""
        from src.osk.blocks.signal_processing import MovingAverage

        State.t = 0.0
        State.dt = 0.01

        ma = MovingAverage(window_size=5)
        ma.init()

        # Feed in values
        for i in range(10):
            State.t = i * 0.01
            ma.input = float(i)
            ma.update()

        assert isinstance(ma.getOutput(), float)

    def test_rate_limiter_connect_input(self):
        """Test RateLimiter with connected input."""
        from src.osk.blocks.signal_processing import RateLimiter
        from src.osk.blocks.sources import Constant

        State.dt = 0.01

        const = Constant(value=100.0)
        const.init()

        rl = RateLimiter(rising_rate=10.0, falling_rate=-10.0)
        rl.init()
        rl.connectInput(const)
        rl.update()

        # Output should be limited by rising rate
        assert rl.getOutput() <= 10.0 * State.dt


class TestObserverMatrixEdgeCases:
    """Test observer blocks with matrix edge cases."""

    def test_kalman_filter_reshape_q_r(self):
        """Test KalmanFilter handles improper Q/R shapes."""
        from src.osk.blocks.observers import KalmanFilter
        import numpy as np

        # Pass scalar Q and R which need reshaping
        kf = KalmanFilter(Q=0.01, R=0.1)
        assert kf.Q.shape == (1, 1)
        assert kf.R.shape == (1, 1)

    def test_extended_kalman_filter_reshape_q_r(self):
        """Test ExtendedKalmanFilter handles improper Q/R shapes."""
        from src.osk.blocks.observers import ExtendedKalmanFilter
        import numpy as np

        # Pass improper Q which needs reshaping
        ekf = ExtendedKalmanFilter(n_states=2, Q=[[1]])  # Wrong size
        assert ekf.Q.shape == (2, 2)

        # Pass 1D R
        ekf2 = ExtendedKalmanFilter(n_states=1, R=[0.5])
        assert ekf2.R.shape == (1, 1)


class TestObserverVectorOutput:
    """Test that observer blocks properly support getOutputVector for subsystem scenarios.

    This is critical for ensuring simulation results don't change when blocks are
    grouped into subsystems. Without getOutputVector(), Inport blocks can't properly
    pass through multi-element state estimates from observers.
    """

    def test_kalman_filter_get_output_vector(self):
        """Test KalmanFilter getOutputVector returns all state estimates."""
        from src.osk.blocks.observers import KalmanFilter

        # 2-state Kalman filter (position-velocity)
        kf = KalmanFilter(
            A=[[1, 0.01], [0, 1]],
            B=[[0], [0]],
            C=[[1, 0]],
            initial_state=[1.0, 2.0]
        )
        kf.init()

        vec = kf.getOutputVector()
        assert vec is not None
        assert len(vec) == 2
        assert vec[0] == pytest.approx(0.0)  # After init, states are reset to zeros
        assert vec[1] == pytest.approx(0.0)

        # Set specific values and verify
        kf.x_hat = [5.0, 10.0]
        vec = kf.getOutputVector()
        assert vec[0] == pytest.approx(5.0)
        assert vec[1] == pytest.approx(10.0)

    def test_luenberger_observer_get_output_vector(self):
        """Test LuenbergerObserver getOutputVector returns all state estimates."""
        from src.osk.blocks.observers import LuenbergerObserver

        # 2-state observer
        obs = LuenbergerObserver(
            A=[[0, 1], [0, 0]],
            B=[[0], [1]],
            C=[[1, 0]],
            L=[[1], [1]],
            initial_state=[3.0, 4.0]
        )
        obs.init()

        vec = obs.getOutputVector()
        assert vec is not None
        assert len(vec) == 2

    def test_extended_kalman_filter_get_output_vector(self):
        """Test ExtendedKalmanFilter getOutputVector returns all state estimates."""
        from src.osk.blocks.observers import ExtendedKalmanFilter

        # 3-state EKF
        ekf = ExtendedKalmanFilter(n_states=3)
        ekf.init()

        vec = ekf.getOutputVector()
        assert vec is not None
        assert len(vec) == 3

    def test_kalman_via_inport_passthrough(self):
        """Test that KalmanFilter state vector passes through Inport correctly.

        This simulates the subsystem scenario where:
        KalmanFilter -> Inport -> Demux

        Without getOutputVector(), the Inport would only read the first state.
        """
        from src.osk.blocks.observers import KalmanFilter
        from src.osk.blocks.subsystems import Inport
        from src.osk.blocks.math_ops import Demux

        # Create 2-state Kalman filter
        kf = KalmanFilter(
            A=[[1, 0.01], [0, 1]],
            B=[[0], [0]],
            C=[[1, 0]],
        )
        kf.init()
        kf.x_hat = [1.5, 2.5]  # Set known state values

        # Create Inport and connect to KalmanFilter
        inport = Inport(port_number=1)
        inport.connectInput(kf, port=0, source_port=0)
        inport.update()

        # Verify Inport passes through the vector
        vec = inport.getOutputVector()
        assert vec is not None
        assert len(vec) == 2
        assert vec[0] == pytest.approx(1.5)
        assert vec[1] == pytest.approx(2.5)

        # Create Demux and connect to Inport
        demux = Demux(num_outputs=2)
        demux.connectInput(inport, port=0, source_port=0)
        demux.update()

        # Verify Demux correctly receives both values
        assert demux.getOutput(0) == pytest.approx(1.5)
        assert demux.getOutput(1) == pytest.approx(2.5)

    def test_kalman_via_inport_outport_passthrough(self):
        """Test full subsystem scenario: KalmanFilter -> Inport -> Outport -> Demux.

        This is the exact scenario that was broken before the fix.
        """
        from src.osk.blocks.observers import KalmanFilter
        from src.osk.blocks.subsystems import Inport, Outport
        from src.osk.blocks.math_ops import Demux

        # Create 2-state Kalman filter
        kf = KalmanFilter(
            A=[[1, 0.01], [0, 1]],
            B=[[0], [0]],
            C=[[1, 0]],
        )
        kf.init()
        kf.x_hat = [10.0, 20.0]  # Position=10, Velocity=20

        # Simulate subsystem: KalmanFilter -> Inport -> Outport
        inport = Inport(port_number=1)
        inport.connectInput(kf, port=0, source_port=0)
        inport.update()

        outport = Outport(port_number=1)
        outport.connectInput(inport, port=0, source_port=0)
        outport.update()

        # Demux connected to Outport (outside subsystem)
        demux = Demux(num_outputs=2)
        demux.connectInput(outport, port=0, source_port=0)
        demux.update()

        # CRITICAL: Both values should be correctly passed through
        assert demux.getOutput(0) == pytest.approx(10.0), "Position should be 10.0"
        assert demux.getOutput(1) == pytest.approx(20.0), "Velocity should be 20.0"
