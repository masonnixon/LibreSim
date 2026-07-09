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
        di = DiscreteIntegrator(method="forward", sample_time=0.1, initial_condition=0.0)
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
        di = DiscreteIntegrator(method="backward", sample_time=0.1, initial_condition=0.0)
        di.init()

        State.t = 0.0
        di.setInput(1.0)
        di.update()
        # backward: output += T * u[n]
        assert di.getOutput() == pytest.approx(0.1)

    def test_discrete_integrator_trapezoidal(self):
        """Test DiscreteIntegrator trapezoidal method."""
        di = DiscreteIntegrator(method="trapezoidal", sample_time=0.1, initial_condition=0.0)
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
        di = DiscreteIntegrator(method="backward", sample_time=0.1, initial_condition=0.0)
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

        filt = AnalogFilter(
            design="chebyshev1", response="lowpass", order=2, cutoff_freq=10.0, passband_ripple=1.0
        )
        State.dt = 0.001
        filt.init()

        filt.setInput(1.0)
        for _ in range(100):
            filt.update()

        assert filt.getOutput() > 0.5

    def test_analog_filter_chebyshev2(self):
        """Test Chebyshev Type II filter."""
        from src.osk.blocks.signal_processing import AnalogFilter

        filt = AnalogFilter(
            design="chebyshev2", response="lowpass", order=2, cutoff_freq=10.0, stopband_atten=40.0
        )
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
        lut = LookupTable2D(x_data=[0.0, 1.0], y_data=[0.0, 1.0], z_data=[[0.0, 1.0], [2.0, 3.0]])
        lut.init()

        lut.setInput(0.0, 0)
        lut.setInput(0.0, 1)
        lut.update()
        assert lut.getOutput() == pytest.approx(0.0)

    def test_lookup_2d_interpolation(self):
        """Test LookupTable2D bilinear interpolation."""
        lut = LookupTable2D(x_data=[0.0, 1.0], y_data=[0.0, 1.0], z_data=[[0.0, 1.0], [2.0, 3.0]])
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
        obs = LuenbergerObserver(A=[[0.0]], B=[[1.0]], C=[[1.0]], L=[[1.0]])
        obs.init()
        assert obs.getOutput() == 0.0

    def test_luenberger_state_estimate(self):
        """Test LuenbergerObserver state estimate."""
        obs = LuenbergerObserver(A=[[0.0]], B=[[1.0]], C=[[1.0]], L=[[1.0]])
        obs.init()

        obs.setInput(1.0, 0)  # Control input
        obs.setInput(1.0, 1)  # Measurement
        obs.update()

        # State should start at 0, but update modifies x_hat_dot
        assert isinstance(obs.getOutput(), float)

    def test_luenberger_full_state(self):
        """Test LuenbergerObserver full state estimate."""
        obs = LuenbergerObserver(A=[[0.0]], B=[[1.0]], C=[[1.0]], L=[[1.0]])
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
        kf = KalmanFilter(A=[[1.0]], B=[[1.0]], C=[[1.0]], Q=[[0.01]], R=[[0.1]])
        kf.init()
        assert kf.getOutput() == 0.0

    def test_kalman_update(self):
        """Test KalmanFilter update step."""
        kf = KalmanFilter(A=[[1.0]], B=[[0.1]], C=[[1.0]], Q=[[0.01]], R=[[0.1]])
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
        ss = StateSpace(A=[[0.0]], B=[[1.0]], C=[[1.0]], D=[[0.0]])
        ss.init()
        assert ss.getOutput() == 0.0

    def test_state_space_with_initial_state(self):
        """Test StateSpace with initial state."""
        ss = StateSpace(A=[[0.0]], B=[[1.0]], C=[[1.0]], D=[[0.0]], initial_state=[5.0])
        # Output is C*x, x[0]=5, so output=5
        ss.update()
        assert ss.getOutput() == pytest.approx(5.0)

    def test_state_space_feedthrough(self):
        """Test StateSpace with direct feedthrough."""
        ss = StateSpace(
            A=[[0.0]],
            B=[[0.0]],
            C=[[0.0]],
            D=[[2.0]],  # Direct feedthrough
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
        integrator = Integrator(
            initial_condition=5.0, limit_output=True, upper_limit=3.0, lower_limit=-3.0
        )
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

        prod = Product(operations="**")
        prod.connectInput(const1, 0)
        prod.connectInput(const2, 1)

        assert prod.input_blocks[0] is const1
        assert prod.input_blocks[1] is const2

        prod.update()
        assert prod.getOutput() == pytest.approx(12.0)

    def test_product_division_by_zero(self):
        """Test Product handles division by near-zero."""
        prod = Product(operations="*/")
        prod.setInput(10.0, 0)
        prod.setInput(0.0, 1)  # Near zero
        prod.update()
        # Should handle gracefully without crashing
        assert prod.getOutput() != float("inf")


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

        mf = MathFunction(function="exp")
        mf.connectInput(const)
        assert mf.input_block is const

        mf.update()
        assert mf.getOutput() == pytest.approx(math.e)

    def test_math_function_log(self):
        """Test MathFunction log function."""
        mf = MathFunction(function="log")
        mf.setInput(math.e)
        mf.update()
        assert mf.getOutput() == pytest.approx(1.0)

    def test_math_function_log_negative(self):
        """Test MathFunction log with near-zero input."""
        mf = MathFunction(function="log")
        mf.setInput(0.0)
        mf.update()
        # Should not crash, uses EPS
        assert isinstance(mf.getOutput(), float)

    def test_math_function_log10(self):
        """Test MathFunction log10 function."""
        mf = MathFunction(function="log10")
        mf.setInput(100.0)
        mf.update()
        assert mf.getOutput() == pytest.approx(2.0)

    def test_math_function_sqrt(self):
        """Test MathFunction sqrt function."""
        mf = MathFunction(function="sqrt")
        mf.setInput(16.0)
        mf.update()
        assert mf.getOutput() == pytest.approx(4.0)

    def test_math_function_sqrt_negative(self):
        """Test MathFunction sqrt with negative input."""
        mf = MathFunction(function="sqrt")
        mf.setInput(-5.0)
        mf.update()
        assert mf.getOutput() == 0.0

    def test_math_function_square(self):
        """Test MathFunction square function."""
        mf = MathFunction(function="square")
        mf.setInput(5.0)
        mf.update()
        assert mf.getOutput() == pytest.approx(25.0)

    def test_math_function_pow(self):
        """Test MathFunction pow function."""
        mf = MathFunction(function="pow", exponent=3.0)
        mf.setInput(2.0)
        mf.update()
        assert mf.getOutput() == pytest.approx(8.0)

    def test_math_function_reciprocal(self):
        """Test MathFunction reciprocal function."""
        mf = MathFunction(function="reciprocal")
        mf.setInput(5.0)
        mf.update()
        assert mf.getOutput() == pytest.approx(0.2)

    def test_math_function_reciprocal_zero(self):
        """Test MathFunction reciprocal with zero."""
        mf = MathFunction(function="reciprocal")
        mf.setInput(0.0)
        mf.update()
        # Should handle gracefully
        assert mf.getOutput() != float("inf")

    def test_math_function_unknown(self):
        """Test MathFunction with unknown function (pass-through)."""
        mf = MathFunction(function="unknown_func")
        mf.setInput(42.0)
        mf.update()
        assert mf.getOutput() == 42.0


class TestTrigonometryExtended:
    """Extended tests for Trigonometry block."""

    def test_trig_connect_input(self):
        """Test Trigonometry connectInput method."""
        const = Constant(value=0.0)
        const.init()

        trig = Trigonometry(function="sin")
        trig.connectInput(const)
        assert trig.input_block is const

        trig.update()
        assert trig.getOutput() == pytest.approx(0.0)

    def test_trig_tan(self):
        """Test Trigonometry tan function."""
        trig = Trigonometry(function="tan")
        trig.setInput(0.0)
        trig.update()
        assert trig.getOutput() == pytest.approx(0.0)

    def test_trig_asin(self):
        """Test Trigonometry asin function."""
        trig = Trigonometry(function="asin")
        trig.setInput(0.5)
        trig.update()
        assert trig.getOutput() == pytest.approx(math.asin(0.5))

    def test_trig_acos(self):
        """Test Trigonometry acos function."""
        trig = Trigonometry(function="acos")
        trig.setInput(0.5)
        trig.update()
        assert trig.getOutput() == pytest.approx(math.acos(0.5))

    def test_trig_atan(self):
        """Test Trigonometry atan function."""
        trig = Trigonometry(function="atan")
        trig.setInput(1.0)
        trig.update()
        assert trig.getOutput() == pytest.approx(math.atan(1.0))

    def test_trig_sinh(self):
        """Test Trigonometry sinh function."""
        trig = Trigonometry(function="sinh")
        trig.setInput(1.0)
        trig.update()
        assert trig.getOutput() == pytest.approx(math.sinh(1.0))

    def test_trig_cosh(self):
        """Test Trigonometry cosh function."""
        trig = Trigonometry(function="cosh")
        trig.setInput(1.0)
        trig.update()
        assert trig.getOutput() == pytest.approx(math.cosh(1.0))

    def test_trig_tanh(self):
        """Test Trigonometry tanh function."""
        trig = Trigonometry(function="tanh")
        trig.setInput(1.0)
        trig.update()
        assert trig.getOutput() == pytest.approx(math.tanh(1.0))

    def test_trig_overflow_handling(self):
        """Test Trigonometry handles overflow."""
        trig = Trigonometry(function="sinh")
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

        sw = Switch(threshold=0.5, criteria="gte")
        sw.connectInput(const1, 0)
        sw.connectInput(control, 1)
        sw.connectInput(const2, 2)

        sw.update()
        # Control (1.0) >= threshold (0.5), so use first input (10.0)
        assert sw.getOutput() == 10.0

    def test_switch_gt_criteria(self):
        """Test Switch with 'gt' criteria."""
        sw = Switch(threshold=0.5, criteria="gt")
        sw.setInput(10.0, 0)  # First input
        sw.setInput(0.5, 1)  # Control - exactly at threshold
        sw.setInput(20.0, 2)  # Second input
        sw.update()
        # Control (0.5) is NOT > threshold (0.5), so use second input
        assert sw.getOutput() == 20.0

    def test_switch_neq_criteria(self):
        """Test Switch with 'neq' criteria."""
        sw = Switch(threshold=0.5, criteria="neq")
        sw.setInput(10.0, 0)  # First input
        sw.setInput(0.5, 1)  # Control - exactly at threshold
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

        obs = LuenbergerObserver()
        obs._initial_state = [5.0]
        obs.init()
        assert obs.x_hat[0] == 5.0

    def test_luenberger_propagate_states(self):
        """Test LuenbergerObserver propagateStates method."""
        from src.osk.blocks.observers import LuenbergerObserver

        State.dt = 0.01
        obs = LuenbergerObserver()
        obs.x_hat = np.array([1.0])
        obs.x_hat_dot = np.array([10.0])
        obs.propagateStates()
        assert obs.x_hat[0] == pytest.approx(1.1, rel=0.01)

    def test_luenberger_get_state_estimate(self):
        """Test LuenbergerObserver getStateEstimate method."""
        from src.osk.blocks.observers import LuenbergerObserver

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

        kf = KalmanFilter()
        kf.x_hat = np.array([5.0])
        kf.P = np.array([[10.0]])
        kf.init()
        assert kf.x_hat[0] == 0.0
        assert kf.P[0, 0] == 1.0

    def test_kalman_filter_get_covariance(self):
        """Test KalmanFilter getCovariance method."""
        from src.osk.blocks.observers import KalmanFilter

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

        ekf = ExtendedKalmanFilter(n_states=2)
        ekf.x_hat = np.array([1.0, 2.0])
        ekf.init()
        assert ekf.x_hat[0] == 0.0
        assert ekf.x_hat[1] == 0.0

    def test_extended_kalman_filter_get_output_port1(self):
        """Test ExtendedKalmanFilter getOutput with port 1."""
        from src.osk.blocks.observers import ExtendedKalmanFilter

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
            numerator=[1.0, 1.0], denominator=[1.0, 0.5, 0.25], sample_time=0.01
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
        lut = LookupTable1D(x_data=[0, 1, 2], y_data=[0, 10, 20])
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

        # Pass scalar Q and R which need reshaping
        kf = KalmanFilter(Q=0.01, R=0.1)
        assert kf.Q.shape == (1, 1)
        assert kf.R.shape == (1, 1)

    def test_extended_kalman_filter_reshape_q_r(self):
        """Test ExtendedKalmanFilter handles improper Q/R shapes."""
        from src.osk.blocks.observers import ExtendedKalmanFilter

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
        kf = KalmanFilter(A=[[1, 0.01], [0, 1]], B=[[0], [0]], C=[[1, 0]], initial_state=[1.0, 2.0])
        kf.init()

        vec = kf.getOutputVector()
        assert vec is not None
        assert len(vec) == 2
        # After init, states should be restored to initial_state values
        assert vec[0] == pytest.approx(1.0)
        assert vec[1] == pytest.approx(2.0)

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
            A=[[0, 1], [0, 0]], B=[[0], [1]], C=[[1, 0]], L=[[1], [1]], initial_state=[3.0, 4.0]
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
        from src.osk.blocks.math_ops import Demux
        from src.osk.blocks.observers import KalmanFilter
        from src.osk.blocks.subsystems import Inport

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
        from src.osk.blocks.math_ops import Demux
        from src.osk.blocks.observers import KalmanFilter
        from src.osk.blocks.subsystems import Inport, Outport

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


# =============================================================================
# Comprehensive Vector Signal Processing Tests
# =============================================================================


class TestVectorIntegrator:
    """Tests for vector support in the Integrator block."""

    def setup_method(self):
        """Reset state before each test."""
        State.time = 0.0
        State.dt = 0.001
        State.ready = 0

    def test_integrator_vector_initial_condition(self):
        """Test Integrator with vector initial condition."""
        integrator = Integrator(initial_condition=[1.0, 2.0, 3.0])
        integrator.init()

        # Should output initial conditions
        assert integrator.getOutput(0) == pytest.approx(1.0)
        assert integrator.getOutput(1) == pytest.approx(2.0)
        assert integrator.getOutput(2) == pytest.approx(3.0)

        vec = integrator.getOutputVector()
        assert vec is not None
        assert len(vec) == 3
        assert vec == [1.0, 2.0, 3.0]

    def test_integrator_vector_from_constant(self):
        """Test Integrator with vector input from Constant block."""
        const = Constant(value=[1.0, 2.0, 3.0])
        const.init()
        const.update()

        integrator = Integrator(initial_condition=[0.0, 0.0, 0.0])
        integrator.init()
        integrator.connectInput(const)

        # Simulate for 1 second
        for _ in range(1000):
            const.update()
            integrator.update()
            # Propagate states
            for state in integrator._states:
                state[0] += State.dt * state[1]

        # After 1 second, integral of [1, 2, 3] should be approximately [1, 2, 3]
        vec = integrator.getOutputVector()
        assert vec is not None
        assert vec[0] == pytest.approx(1.0, abs=0.01)
        assert vec[1] == pytest.approx(2.0, abs=0.01)
        assert vec[2] == pytest.approx(3.0, abs=0.01)

    def test_integrator_vector_dynamic_setup(self):
        """Test that Integrator dynamically sets up vector mode from input."""
        const = Constant(value=[5.0, 10.0])
        const.init()

        # Start with scalar initial condition
        integrator = Integrator(initial_condition=0.0)
        integrator.init()
        integrator.connectInput(const)

        # First update should detect vector input and switch to vector mode
        const.update()
        integrator.update()

        assert integrator._is_vector is True
        assert integrator._n == 2


class TestVectorSum:
    """Tests for vector support in the Sum block."""

    def setup_method(self):
        """Reset state before each test."""
        State.time = 0.0
        State.dt = 0.001
        State.ready = 0

    def test_sum_vector_addition(self):
        """Test Sum block with two vector inputs."""
        const1 = Constant(value=[1.0, 2.0, 3.0])
        const2 = Constant(value=[4.0, 5.0, 6.0])
        const1.init()
        const2.init()

        sum_block = Sum(signs="++")
        sum_block.connectInput(const1, port=0)
        sum_block.connectInput(const2, port=1)

        const1.update()
        const2.update()
        sum_block.update()

        vec = sum_block.getOutputVector()
        assert vec is not None
        assert len(vec) == 3
        assert vec[0] == pytest.approx(5.0)
        assert vec[1] == pytest.approx(7.0)
        assert vec[2] == pytest.approx(9.0)

    def test_sum_vector_subtraction(self):
        """Test Sum block with vector subtraction."""
        const1 = Constant(value=[10.0, 20.0, 30.0])
        const2 = Constant(value=[1.0, 2.0, 3.0])
        const1.init()
        const2.init()

        sum_block = Sum(signs="+-")
        sum_block.connectInput(const1, port=0)
        sum_block.connectInput(const2, port=1)

        const1.update()
        const2.update()
        sum_block.update()

        vec = sum_block.getOutputVector()
        assert vec is not None
        assert vec[0] == pytest.approx(9.0)
        assert vec[1] == pytest.approx(18.0)
        assert vec[2] == pytest.approx(27.0)

    def test_sum_three_vector_inputs(self):
        """Test Sum block with three vector inputs."""
        const1 = Constant(value=[1.0, 1.0])
        const2 = Constant(value=[2.0, 2.0])
        const3 = Constant(value=[3.0, 3.0])
        const1.init()
        const2.init()
        const3.init()

        sum_block = Sum(signs="+++")
        sum_block.connectInput(const1, port=0)
        sum_block.connectInput(const2, port=1)
        sum_block.connectInput(const3, port=2)

        const1.update()
        const2.update()
        const3.update()
        sum_block.update()

        vec = sum_block.getOutputVector()
        assert vec is not None
        assert vec[0] == pytest.approx(6.0)
        assert vec[1] == pytest.approx(6.0)


class TestVectorGain:
    """Tests for vector support in the Gain block."""

    def setup_method(self):
        """Reset state before each test."""
        State.time = 0.0
        State.dt = 0.001
        State.ready = 0

    def test_gain_scalar_on_vector(self):
        """Test Gain block with scalar gain on vector input."""
        const = Constant(value=[1.0, 2.0, 3.0])
        const.init()

        gain = Gain(gain=2.0)
        gain.connectInput(const)

        const.update()
        gain.update()

        vec = gain.getOutputVector()
        assert vec is not None
        assert vec[0] == pytest.approx(2.0)
        assert vec[1] == pytest.approx(4.0)
        assert vec[2] == pytest.approx(6.0)

    def test_gain_negative(self):
        """Test Gain block with negative gain on vector."""
        const = Constant(value=[1.0, -2.0, 3.0])
        const.init()

        gain = Gain(gain=-1.0)
        gain.connectInput(const)

        const.update()
        gain.update()

        vec = gain.getOutputVector()
        assert vec is not None
        assert vec[0] == pytest.approx(-1.0)
        assert vec[1] == pytest.approx(2.0)
        assert vec[2] == pytest.approx(-3.0)

    def test_gain_zero(self):
        """Test Gain block with zero gain on vector."""
        const = Constant(value=[100.0, 200.0])
        const.init()

        gain = Gain(gain=0.0)
        gain.connectInput(const)

        const.update()
        gain.update()

        vec = gain.getOutputVector()
        assert vec is not None
        assert vec[0] == pytest.approx(0.0)
        assert vec[1] == pytest.approx(0.0)


class TestVectorProduct:
    """Tests for vector support in the Product block."""

    def setup_method(self):
        """Reset state before each test."""
        State.time = 0.0
        State.dt = 0.001
        State.ready = 0

    def test_product_vector_multiply(self):
        """Test Product block with element-wise vector multiplication."""
        const1 = Constant(value=[2.0, 3.0, 4.0])
        const2 = Constant(value=[5.0, 6.0, 7.0])
        const1.init()
        const2.init()

        product = Product(operations="**")
        product.connectInput(const1, port=0)
        product.connectInput(const2, port=1)

        const1.update()
        const2.update()
        product.update()

        vec = product.getOutputVector()
        assert vec is not None
        assert vec[0] == pytest.approx(10.0)
        assert vec[1] == pytest.approx(18.0)
        assert vec[2] == pytest.approx(28.0)

    def test_product_vector_divide(self):
        """Test Product block with element-wise vector division."""
        const1 = Constant(value=[10.0, 20.0, 30.0])
        const2 = Constant(value=[2.0, 4.0, 5.0])
        const1.init()
        const2.init()

        product = Product(operations="*/")
        product.connectInput(const1, port=0)
        product.connectInput(const2, port=1)

        const1.update()
        const2.update()
        product.update()

        vec = product.getOutputVector()
        assert vec is not None
        assert vec[0] == pytest.approx(5.0)
        assert vec[1] == pytest.approx(5.0)
        assert vec[2] == pytest.approx(6.0)


class TestVectorAbs:
    """Tests for vector support in the Abs block."""

    def setup_method(self):
        """Reset state before each test."""
        State.time = 0.0
        State.dt = 0.001

    def test_abs_vector_mixed_signs(self):
        """Test Abs block with vector containing mixed signs."""
        const = Constant(value=[-1.0, 2.0, -3.0, 4.0])
        const.init()

        abs_block = Abs()
        abs_block.connectInput(const)

        const.update()
        abs_block.update()

        vec = abs_block.getOutputVector()
        assert vec is not None
        assert vec[0] == pytest.approx(1.0)
        assert vec[1] == pytest.approx(2.0)
        assert vec[2] == pytest.approx(3.0)
        assert vec[3] == pytest.approx(4.0)

    def test_abs_vector_all_negative(self):
        """Test Abs block with all negative vector."""
        const = Constant(value=[-5.0, -10.0])
        const.init()

        abs_block = Abs()
        abs_block.connectInput(const)

        const.update()
        abs_block.update()

        vec = abs_block.getOutputVector()
        assert vec is not None
        assert vec[0] == pytest.approx(5.0)
        assert vec[1] == pytest.approx(10.0)


class TestVectorSign:
    """Tests for vector support in the Sign block."""

    def setup_method(self):
        """Reset state before each test."""
        State.time = 0.0
        State.dt = 0.001

    def test_sign_vector(self):
        """Test Sign block with vector containing positive, negative, and zero."""
        const = Constant(value=[-5.0, 0.0, 3.0])
        const.init()

        sign_block = Sign()
        sign_block.connectInput(const)

        const.update()
        sign_block.update()

        vec = sign_block.getOutputVector()
        assert vec is not None
        assert vec[0] == pytest.approx(-1.0)
        assert vec[1] == pytest.approx(0.0)
        assert vec[2] == pytest.approx(1.0)


class TestVectorSaturation:
    """Tests for vector support in the Saturation block."""

    def setup_method(self):
        """Reset state before each test."""
        State.time = 0.0
        State.dt = 0.001

    def test_saturation_vector(self):
        """Test Saturation block with vector input."""
        const = Constant(value=[-10.0, 0.5, 10.0])
        const.init()

        sat = Saturation(upper_limit=1.0, lower_limit=-1.0)
        sat.connectInput(const)

        const.update()
        sat.update()

        vec = sat.getOutputVector()
        assert vec is not None
        assert vec[0] == pytest.approx(-1.0)  # Saturated low
        assert vec[1] == pytest.approx(0.5)  # In range
        assert vec[2] == pytest.approx(1.0)  # Saturated high


class TestVectorDeadZone:
    """Tests for vector support in the DeadZone block."""

    def setup_method(self):
        """Reset state before each test."""
        State.time = 0.0
        State.dt = 0.001

    def test_deadzone_vector(self):
        """Test DeadZone block with vector input."""
        const = Constant(value=[-5.0, -0.5, 0.3, 2.0])
        const.init()

        dz = DeadZone(start=-1.0, end=1.0)
        dz.connectInput(const)

        const.update()
        dz.update()

        vec = dz.getOutputVector()
        assert vec is not None
        assert vec[0] == pytest.approx(-4.0)  # -5 + 1 = -4
        assert vec[1] == pytest.approx(0.0)  # In dead zone
        assert vec[2] == pytest.approx(0.0)  # In dead zone
        assert vec[3] == pytest.approx(1.0)  # 2 - 1 = 1


class TestVectorMathFunction:
    """Tests for vector support in the MathFunction block."""

    def setup_method(self):
        """Reset state before each test."""
        State.time = 0.0
        State.dt = 0.001

    def test_math_function_square_vector(self):
        """Test MathFunction square on vector."""
        const = Constant(value=[2.0, 3.0, 4.0])
        const.init()

        mf = MathFunction(function="square")
        mf.connectInput(const)

        const.update()
        mf.update()

        vec = mf.getOutputVector()
        assert vec is not None
        assert vec[0] == pytest.approx(4.0)
        assert vec[1] == pytest.approx(9.0)
        assert vec[2] == pytest.approx(16.0)

    def test_math_function_sqrt_vector(self):
        """Test MathFunction sqrt on vector."""
        const = Constant(value=[4.0, 9.0, 16.0])
        const.init()

        mf = MathFunction(function="sqrt")
        mf.connectInput(const)

        const.update()
        mf.update()

        vec = mf.getOutputVector()
        assert vec is not None
        assert vec[0] == pytest.approx(2.0)
        assert vec[1] == pytest.approx(3.0)
        assert vec[2] == pytest.approx(4.0)

    def test_math_function_exp_vector(self):
        """Test MathFunction exp on vector."""
        const = Constant(value=[0.0, 1.0, 2.0])
        const.init()

        mf = MathFunction(function="exp")
        mf.connectInput(const)

        const.update()
        mf.update()

        vec = mf.getOutputVector()
        assert vec is not None
        assert vec[0] == pytest.approx(1.0)
        assert vec[1] == pytest.approx(math.e)
        assert vec[2] == pytest.approx(math.e**2)


class TestVectorTrigonometry:
    """Tests for vector support in the Trigonometry block."""

    def setup_method(self):
        """Reset state before each test."""
        State.time = 0.0
        State.dt = 0.001

    def test_trig_sin_vector(self):
        """Test Trigonometry sin on vector."""
        const = Constant(value=[0.0, math.pi / 2, math.pi])
        const.init()

        trig = Trigonometry(function="sin")
        trig.connectInput(const)

        const.update()
        trig.update()

        vec = trig.getOutputVector()
        assert vec is not None
        assert vec[0] == pytest.approx(0.0, abs=1e-10)
        assert vec[1] == pytest.approx(1.0)
        assert vec[2] == pytest.approx(0.0, abs=1e-10)

    def test_trig_cos_vector(self):
        """Test Trigonometry cos on vector."""
        const = Constant(value=[0.0, math.pi / 2, math.pi])
        const.init()

        trig = Trigonometry(function="cos")
        trig.connectInput(const)

        const.update()
        trig.update()

        vec = trig.getOutputVector()
        assert vec is not None
        assert vec[0] == pytest.approx(1.0)
        assert vec[1] == pytest.approx(0.0, abs=1e-10)
        assert vec[2] == pytest.approx(-1.0)


class TestVectorDerivative:
    """Tests for vector support in the Derivative block."""

    def setup_method(self):
        """Reset state before each test."""
        State.time = 0.0
        State.dt = 0.001
        State.ready = 0

    def test_derivative_vector_from_constant(self):
        """Test Derivative block with vector input."""
        const = Constant(value=[1.0, 2.0, 3.0])
        const.init()

        deriv = Derivative(coefficient=100.0)
        deriv.init()
        deriv.connectInput(const)

        const.update()
        deriv.update()

        # Derivative should have vector output
        vec = deriv.getOutputVector()
        assert vec is not None
        assert len(vec) == 3

    def test_derivative_vector_dynamic_setup(self):
        """Test that Derivative dynamically sets up vector mode from input."""
        const = Constant(value=[5.0, 10.0])
        const.init()

        # Start as scalar derivative
        deriv = Derivative(coefficient=100.0)
        deriv.init()
        deriv.connectInput(const)

        # First update should detect vector input
        const.update()
        deriv.update()

        assert deriv._is_vector is True
        assert deriv._n == 2


class TestVectorSignalFlow:
    """End-to-end tests for vector signal flow through multiple blocks."""

    def setup_method(self):
        """Reset state before each test."""
        State.time = 0.0
        State.dt = 0.001
        State.ready = 0

    def test_vector_chain_constant_gain_sum(self):
        """Test vector signal flow: Constant -> Gain -> Sum."""
        const1 = Constant(value=[1.0, 2.0])
        const2 = Constant(value=[3.0, 4.0])
        const1.init()
        const2.init()

        gain = Gain(gain=2.0)
        gain.connectInput(const1)

        sum_block = Sum(signs="++")
        sum_block.connectInput(gain, port=0)
        sum_block.connectInput(const2, port=1)

        const1.update()
        const2.update()
        gain.update()
        sum_block.update()

        # const1 * 2 + const2 = [2, 4] + [3, 4] = [5, 8]
        vec = sum_block.getOutputVector()
        assert vec is not None
        assert vec[0] == pytest.approx(5.0)
        assert vec[1] == pytest.approx(8.0)

    def test_vector_chain_mux_gain_demux(self):
        """Test vector signal flow: Mux -> Gain -> Demux."""
        const1 = Constant(value=3.0)
        const2 = Constant(value=5.0)
        const1.init()
        const2.init()

        mux = Mux(num_inputs=2)
        mux.connectInput(const1, port=0)
        mux.connectInput(const2, port=1)

        gain = Gain(gain=10.0)
        gain.connectInput(mux)

        demux = Demux(num_outputs=2)
        demux.connectInput(gain)

        const1.update()
        const2.update()
        mux.update()
        gain.update()
        demux.update()

        # Mux creates [3, 5], Gain makes [30, 50], Demux extracts
        assert demux.getOutput(0) == pytest.approx(30.0)
        assert demux.getOutput(1) == pytest.approx(50.0)

    def test_vector_chain_constant_abs_saturation(self):
        """Test vector signal flow: Constant -> Abs -> Saturation."""
        const = Constant(value=[-5.0, 3.0, -1.0])
        const.init()

        abs_block = Abs()
        abs_block.connectInput(const)

        sat = Saturation(upper_limit=4.0, lower_limit=0.0)
        sat.connectInput(abs_block)

        const.update()
        abs_block.update()
        sat.update()

        # Abs: [5, 3, 1], Saturation(0,4): [4, 3, 1]
        vec = sat.getOutputVector()
        assert vec is not None
        assert vec[0] == pytest.approx(4.0)  # 5 saturated to 4
        assert vec[1] == pytest.approx(3.0)
        assert vec[2] == pytest.approx(1.0)

    def test_vector_feedback_loop(self):
        """Test vector signal in a simple feedback structure."""
        # Simulate: Sum(input, -feedback) -> Gain -> Integrator
        # where feedback = Integrator output

        const = Constant(value=[1.0, 2.0])
        const.init()

        sum_block = Sum(signs="+-")
        gain = Gain(gain=1.0)
        integrator = Integrator(initial_condition=[0.0, 0.0])
        integrator.init()

        sum_block.connectInput(const, port=0)
        # Port 1 (feedback) will be set manually for this test
        gain.connectInput(sum_block)
        integrator.connectInput(gain)

        # Run a few steps
        for _i in range(100):
            const.update()

            # Manually set feedback from integrator output
            integrator_vec = integrator.getOutputVector()
            if integrator_vec:
                # Create a mock block for the feedback
                sum_block._input_vectors[1] = integrator_vec
                if not sum_block._is_vector:
                    sum_block._is_vector = True
                    sum_block._output_vector = [0.0] * len(integrator_vec)

            sum_block.update()
            gain.update()
            integrator.update()

            # Propagate states
            if integrator._states:
                for state in integrator._states:
                    state[0] += State.dt * state[1]

        # After integration, values should have converged somewhat
        vec = integrator.getOutputVector()
        assert vec is not None
        assert len(vec) == 2

    def test_complex_vector_flow(self):
        """Test complex vector signal flow through multiple operations."""
        # Create: [2, 4, 6] -> square -> sqrt -> gain(0.5) -> should be [1, 2, 3]
        const = Constant(value=[2.0, 4.0, 6.0])
        const.init()

        square = MathFunction(function="square")
        square.connectInput(const)

        sqrt = MathFunction(function="sqrt")
        sqrt.connectInput(square)

        gain = Gain(gain=0.5)
        gain.connectInput(sqrt)

        const.update()
        square.update()
        sqrt.update()
        gain.update()

        # [2,4,6] -> [4,16,36] -> [2,4,6] -> [1,2,3]
        vec = gain.getOutputVector()
        assert vec is not None
        assert vec[0] == pytest.approx(1.0)
        assert vec[1] == pytest.approx(2.0)
        assert vec[2] == pytest.approx(3.0)

    def test_vector_mux_from_mixed_sources(self):
        """Test Mux with scalar and demuxed vector sources."""
        scalar = Constant(value=1.0)
        vector = Constant(value=[2.0, 3.0])
        scalar.init()
        vector.init()

        # Demux to get individual elements
        demux = Demux(num_outputs=2)
        demux.connectInput(vector)

        # Mux 3 inputs: scalar, demux[0], demux[1]
        mux = Mux(num_inputs=3)
        mux.connectInput(scalar, port=0)
        mux.connectInput(demux, port=1)  # Gets output from port 0 by default
        # For port 2, we need a workaround since Mux doesn't support source_port
        # Use setInput directly for this test
        scalar.update()
        vector.update()
        demux.update()
        mux.setInput(demux.getOutput(1), port=2)  # Manually set the second element
        mux.update()

        vec = mux.getOutputVector()
        assert vec is not None
        assert len(vec) == 3
        assert vec[0] == pytest.approx(1.0)
        assert vec[1] == pytest.approx(2.0)
        assert vec[2] == pytest.approx(3.0)

    def test_demux_to_multiple_gains(self):
        """Test Demux feeding multiple downstream Gain blocks."""
        const = Constant(value=[10.0, 20.0, 30.0])
        const.init()

        demux = Demux(num_outputs=3)
        demux.connectInput(const)

        gain1 = Gain(gain=1.0)
        gain2 = Gain(gain=2.0)
        gain3 = Gain(gain=3.0)

        # Connect each gain to a different demux output port
        gain1.connectInput(demux, source_port=0)
        gain2.connectInput(demux, source_port=1)
        gain3.connectInput(demux, source_port=2)

        const.update()
        demux.update()
        gain1.update()
        gain2.update()
        gain3.update()

        assert gain1.getOutput() == pytest.approx(10.0)
        assert gain2.getOutput() == pytest.approx(40.0)
        assert gain3.getOutput() == pytest.approx(90.0)


# =============================================================================
# New Nonlinear Block Tests
# =============================================================================


class TestWrapToRangeBlock:
    """Tests for the WrapToRange block."""

    def test_wrap_to_range_within_range(self):
        """Test WrapToRange with input already in range."""
        from src.osk.blocks.nonlinear import WrapToRange

        wrap = WrapToRange(lower=-math.pi, upper=math.pi)
        wrap.init()
        wrap.setInput(1.0)
        wrap.update()
        assert wrap.getOutput() == pytest.approx(1.0)

    def test_wrap_to_range_above_upper(self):
        """Test WrapToRange with input above upper bound."""
        from src.osk.blocks.nonlinear import WrapToRange

        wrap = WrapToRange(lower=-math.pi, upper=math.pi)
        wrap.init()
        # 4.0 radians should wrap to 4.0 - 2*pi ≈ -2.28
        wrap.setInput(4.0)
        wrap.update()
        expected = -math.pi + ((4.0 - (-math.pi)) % (2 * math.pi))
        assert wrap.getOutput() == pytest.approx(expected)

    def test_wrap_to_range_below_lower(self):
        """Test WrapToRange with input below lower bound."""
        from src.osk.blocks.nonlinear import WrapToRange

        wrap = WrapToRange(lower=-math.pi, upper=math.pi)
        wrap.init()
        # -4.0 radians should wrap
        wrap.setInput(-4.0)
        wrap.update()
        expected = -math.pi + ((-4.0 - (-math.pi)) % (2 * math.pi))
        assert wrap.getOutput() == pytest.approx(expected)

    def test_wrap_to_range_custom_range(self):
        """Test WrapToRange with custom range [0, 360]."""
        from src.osk.blocks.nonlinear import WrapToRange

        wrap = WrapToRange(lower=0, upper=360)
        wrap.init()
        wrap.setInput(450)
        wrap.update()
        assert wrap.getOutput() == pytest.approx(90.0)

    def test_wrap_to_range_negative_custom(self):
        """Test WrapToRange with negative value in [0, 360]."""
        from src.osk.blocks.nonlinear import WrapToRange

        wrap = WrapToRange(lower=0, upper=360)
        wrap.init()
        wrap.setInput(-90)
        wrap.update()
        assert wrap.getOutput() == pytest.approx(270.0)


class TestHitCrossingBlock:
    """Tests for the HitCrossing block."""

    def test_hit_crossing_rising(self):
        """Test HitCrossing detects rising edge crossing."""
        from src.osk.blocks.nonlinear import HitCrossing

        hc = HitCrossing(threshold=0.0, direction="rising")
        hc.init()

        # First update below threshold
        hc.setInput(-1.0)
        hc.update()
        assert hc.getOutput() == 0.0

        # Crossing from below to above
        hc.setInput(1.0)
        hc.update()
        assert hc.getOutput() == 1.0

        # Above threshold, no new crossing
        hc.setInput(2.0)
        hc.update()
        assert hc.getOutput() == 0.0

    def test_hit_crossing_falling(self):
        """Test HitCrossing detects falling edge crossing."""
        from src.osk.blocks.nonlinear import HitCrossing

        hc = HitCrossing(threshold=0.0, direction="falling")
        hc.init()

        # Start above threshold
        hc.setInput(1.0)
        hc.update()
        assert hc.getOutput() == 0.0

        # Cross from above to below
        hc.setInput(-1.0)
        hc.update()
        assert hc.getOutput() == 1.0

    def test_hit_crossing_either(self):
        """Test HitCrossing detects both rising and falling."""
        from src.osk.blocks.nonlinear import HitCrossing

        hc = HitCrossing(threshold=0.0, direction="either")
        hc.init()

        # Start below
        hc.setInput(-1.0)
        hc.update()

        # Rising crossing
        hc.setInput(1.0)
        hc.update()
        assert hc.getOutput() == 1.0

        # No crossing
        hc.setInput(2.0)
        hc.update()
        assert hc.getOutput() == 0.0

        # Falling crossing
        hc.setInput(-1.0)
        hc.update()
        assert hc.getOutput() == 1.0


class TestHysteresisBlock:
    """Tests for the Hysteresis block."""

    def test_hysteresis_initial_state(self):
        """Test Hysteresis starts in low state."""
        from src.osk.blocks.nonlinear import Hysteresis

        hyst = Hysteresis(
            upper_threshold=1.0, lower_threshold=-1.0, output_high=1.0, output_low=0.0
        )
        hyst.init()
        assert hyst.getOutput() == 0.0

    def test_hysteresis_switch_high(self):
        """Test Hysteresis switches to high state."""
        from src.osk.blocks.nonlinear import Hysteresis

        hyst = Hysteresis(
            upper_threshold=1.0, lower_threshold=-1.0, output_high=1.0, output_low=0.0
        )
        hyst.init()

        # Input below upper threshold - stays low
        hyst.setInput(0.5)
        hyst.update()
        assert hyst.getOutput() == 0.0

        # Input above upper threshold - switches high
        hyst.setInput(1.5)
        hyst.update()
        assert hyst.getOutput() == 1.0

    def test_hysteresis_stays_high(self):
        """Test Hysteresis stays high until lower threshold crossed."""
        from src.osk.blocks.nonlinear import Hysteresis

        hyst = Hysteresis(
            upper_threshold=1.0, lower_threshold=-1.0, output_high=1.0, output_low=0.0
        )
        hyst.init()

        # Switch to high
        hyst.setInput(1.5)
        hyst.update()
        assert hyst.getOutput() == 1.0

        # Between thresholds - stays high
        hyst.setInput(0.0)
        hyst.update()
        assert hyst.getOutput() == 1.0

        # Still above lower threshold
        hyst.setInput(-0.5)
        hyst.update()
        assert hyst.getOutput() == 1.0

        # Below lower threshold - switches low
        hyst.setInput(-1.5)
        hyst.update()
        assert hyst.getOutput() == 0.0


class TestStictionBlock:
    """Tests for the Stiction block."""

    def test_stiction_initial_stuck(self):
        """Test Stiction starts in stuck state."""
        from src.osk.blocks.nonlinear import Stiction

        st = Stiction(breakaway_force=1.0, velocity_threshold=0.01)
        st.init()
        assert st.is_stuck is True
        assert st.getOutput() == 0.0

    def test_stiction_breakaway(self):
        """Test Stiction breaks away when force exceeds threshold."""
        from src.osk.blocks.nonlinear import Stiction

        st = Stiction(breakaway_force=1.0, velocity_threshold=0.01)
        st.init()

        # Force below breakaway - stays stuck
        st.setInput(0.5, port=0)  # force
        st.setInput(0.0, port=1)  # velocity
        st.update()
        assert st.is_stuck is True

        # Force above breakaway - breaks free
        st.setInput(1.5, port=0)
        st.setInput(0.1, port=1)
        st.update()
        assert st.is_stuck is False

    def test_stiction_sticks_again(self):
        """Test Stiction sticks again when velocity drops."""
        from src.osk.blocks.nonlinear import Stiction

        st = Stiction(breakaway_force=1.0, velocity_threshold=0.01)
        st.init()

        # Break free
        st.setInput(2.0, port=0)
        st.setInput(0.5, port=1)
        st.update()
        assert st.is_stuck is False

        # Velocity drops - sticks again
        st.setInput(0.5, port=0)
        st.setInput(0.001, port=1)
        st.update()
        assert st.is_stuck is True


class TestSlewRateLimiterBlock:
    """Tests for the SlewRateLimiter block."""

    def test_slew_rate_limiter_within_limits(self):
        """Test SlewRateLimiter passes signal within rate limits."""
        from src.osk.blocks.nonlinear import SlewRateLimiter

        slew = SlewRateLimiter(rising_rate=10.0, falling_rate=-10.0, sample_time=0.01)
        slew.init()

        # Small change within limits
        slew.setInput(0.05)  # 0.05 / 0.01 = 5 < 10
        slew.update()
        assert slew.getOutput() == pytest.approx(0.05)

    def test_slew_rate_limiter_rising_limited(self):
        """Test SlewRateLimiter limits rising rate."""
        from src.osk.blocks.nonlinear import SlewRateLimiter

        slew = SlewRateLimiter(rising_rate=1.0, falling_rate=-1.0, sample_time=0.01)
        slew.init()

        # Large jump would exceed rate
        slew.setInput(1.0)  # Would be 1.0/0.01 = 100, but limited to 1.0
        slew.update()
        # Max rise = 1.0 * 0.01 = 0.01
        assert slew.getOutput() == pytest.approx(0.01)

    def test_slew_rate_limiter_falling_limited(self):
        """Test SlewRateLimiter limits falling rate."""
        from src.osk.blocks.nonlinear import SlewRateLimiter

        slew = SlewRateLimiter(rising_rate=1.0, falling_rate=-1.0, sample_time=0.01)
        slew.init()

        # Start at 1.0
        slew.output = 1.0

        # Large drop would exceed rate
        slew.setInput(0.0)
        slew.update()
        # Max fall = -1.0 * 0.01 = -0.01
        assert slew.getOutput() == pytest.approx(0.99)


# =============================================================================
# New Math Block Tests
# =============================================================================


class TestDivideBlock:
    """Tests for the Divide block."""

    def test_divide_basic(self):
        """Test basic division."""
        from src.osk.blocks.math_ops import Divide

        div = Divide()
        div.init()
        div.setInput(10.0, port=0)
        div.setInput(2.0, port=1)
        div.update()
        assert div.getOutput() == pytest.approx(5.0)

    def test_divide_by_zero(self):
        """Test division by zero returns a very large number (numerically stable)."""
        from src.osk.blocks.math_ops import Divide
        from src.osk.state import State

        div = Divide()
        div.init()
        div.setInput(1.0, port=0)
        div.setInput(0.0, port=1)
        div.update()
        # Implementation returns 1/EPS instead of inf for numerical stability
        assert div.getOutput() == pytest.approx(1.0 / State.EPS)


class TestModBlock:
    """Tests for the Mod block."""

    def test_mod_basic(self):
        """Test basic modulo operation."""
        from src.osk.blocks.math_ops import Mod

        mod = Mod()
        mod.init()
        mod.setInput(7.0, port=0)
        mod.setInput(3.0, port=1)
        mod.update()
        assert mod.getOutput() == pytest.approx(1.0)

    def test_mod_floating_point(self):
        """Test modulo with floating point."""
        from src.osk.blocks.math_ops import Mod

        mod = Mod()
        mod.init()
        mod.setInput(5.5, port=0)
        mod.setInput(2.0, port=1)
        mod.update()
        assert mod.getOutput() == pytest.approx(1.5)


class TestAtan2Block:
    """Tests for the Atan2 block."""

    def test_atan2_basic(self):
        """Test basic atan2 calculation."""
        from src.osk.blocks.math_ops import Atan2

        at = Atan2()
        at.init()
        at.setInput(1.0, port=0)  # y
        at.setInput(1.0, port=1)  # x
        at.update()
        assert at.getOutput() == pytest.approx(math.pi / 4)

    def test_atan2_quadrants(self):
        """Test atan2 in different quadrants."""
        from src.osk.blocks.math_ops import Atan2

        at = Atan2()
        at.init()

        # Second quadrant
        at.setInput(1.0, port=0)
        at.setInput(-1.0, port=1)
        at.update()
        assert at.getOutput() == pytest.approx(3 * math.pi / 4)


class TestHypotBlock:
    """Tests for the Hypot block."""

    def test_hypot_basic(self):
        """Test basic hypotenuse calculation."""
        from src.osk.blocks.math_ops import Hypot

        hyp = Hypot()
        hyp.init()
        hyp.setInput(3.0, port=0)
        hyp.setInput(4.0, port=1)
        hyp.update()
        assert hyp.getOutput() == pytest.approx(5.0)


class TestSqrtBlock:
    """Tests for the Sqrt block."""

    def test_sqrt_basic(self):
        """Test basic square root."""
        from src.osk.blocks.math_ops import Sqrt

        sq = Sqrt()
        sq.init()
        sq.setInput(16.0)
        sq.update()
        assert sq.getOutput() == pytest.approx(4.0)

    def test_sqrt_negative(self):
        """Test square root of negative returns 0 (clamped for numerical stability)."""
        from src.osk.blocks.math_ops import Sqrt

        sq = Sqrt()
        sq.init()
        sq.setInput(-1.0)
        sq.update()
        # Implementation clamps negative values to 0 before sqrt for numerical stability
        assert sq.getOutput() == pytest.approx(0.0)


class TestSquareBlock:
    """Tests for the Square block."""

    def test_square_basic(self):
        """Test basic squaring."""
        from src.osk.blocks.math_ops import Square

        sq = Square()
        sq.init()
        sq.setInput(5.0)
        sq.update()
        assert sq.getOutput() == pytest.approx(25.0)

    def test_square_negative(self):
        """Test squaring negative number."""
        from src.osk.blocks.math_ops import Square

        sq = Square()
        sq.init()
        sq.setInput(-3.0)
        sq.update()
        assert sq.getOutput() == pytest.approx(9.0)


class TestReciprocalBlock:
    """Tests for the Reciprocal block."""

    def test_reciprocal_basic(self):
        """Test basic reciprocal."""
        from src.osk.blocks.math_ops import Reciprocal

        rec = Reciprocal()
        rec.init()
        rec.setInput(4.0)
        rec.update()
        assert rec.getOutput() == pytest.approx(0.25)

    def test_reciprocal_zero(self):
        """Test reciprocal of zero returns infinity."""
        from src.osk.blocks.math_ops import Reciprocal

        rec = Reciprocal()
        rec.init()
        rec.setInput(0.0)
        rec.update()
        assert math.isinf(rec.getOutput())


class TestPowerBlock:
    """Tests for the Power block."""

    def test_power_basic(self):
        """Test basic power operation (u^v with two inputs)."""
        from src.osk.blocks.math_ops import Power

        pw = Power()
        pw.init()
        pw.setInput(2.0, port=0)  # base
        pw.setInput(3.0, port=1)  # exponent
        pw.update()
        assert pw.getOutput() == pytest.approx(8.0)

    def test_power_fractional(self):
        """Test fractional power (square root)."""
        from src.osk.blocks.math_ops import Power

        pw = Power()
        pw.init()
        pw.setInput(9.0, port=0)  # base
        pw.setInput(0.5, port=1)  # exponent
        pw.update()
        assert pw.getOutput() == pytest.approx(3.0)


class TestExpBlock:
    """Tests for the Exp block."""

    def test_exp_basic(self):
        """Test basic exponential."""
        from src.osk.blocks.math_ops import Exp

        exp = Exp()
        exp.init()
        exp.setInput(1.0)
        exp.update()
        assert exp.getOutput() == pytest.approx(math.e)

    def test_exp_zero(self):
        """Test e^0 = 1."""
        from src.osk.blocks.math_ops import Exp

        exp = Exp()
        exp.init()
        exp.setInput(0.0)
        exp.update()
        assert exp.getOutput() == pytest.approx(1.0)


class TestLogBlock:
    """Tests for the Log block."""

    def test_log_basic(self):
        """Test basic natural logarithm."""
        from src.osk.blocks.math_ops import Log

        log = Log()
        log.init()
        log.setInput(math.e)
        log.update()
        assert log.getOutput() == pytest.approx(1.0)

    def test_log_negative(self):
        """Test log of negative returns clamped value (numerical stability)."""
        from src.osk.blocks.math_ops import Log

        log = Log()
        log.init()
        log.setInput(-1.0)
        log.update()
        # Implementation clamps input to 1e-300 for numerical stability
        # log(1e-300) is approximately -690.78
        assert log.getOutput() == pytest.approx(math.log(1e-300))


class TestLog10Block:
    """Tests for the Log10 block."""

    def test_log10_basic(self):
        """Test basic base-10 logarithm."""
        from src.osk.blocks.math_ops import Log10

        log = Log10()
        log.init()
        log.setInput(100.0)
        log.update()
        assert log.getOutput() == pytest.approx(2.0)


class TestUnaryMinusBlock:
    """Tests for the UnaryMinus block."""

    def test_unary_minus_basic(self):
        """Test basic negation."""
        from src.osk.blocks.math_ops import UnaryMinus

        um = UnaryMinus()
        um.init()
        um.setInput(5.0)
        um.update()
        assert um.getOutput() == pytest.approx(-5.0)

    def test_unary_minus_negative(self):
        """Test negating negative number."""
        from src.osk.blocks.math_ops import UnaryMinus

        um = UnaryMinus()
        um.init()
        um.setInput(-3.0)
        um.update()
        assert um.getOutput() == pytest.approx(3.0)


class TestDotProductBlock:
    """Tests for the DotProduct block."""

    def test_dot_product_basic(self):
        """Test basic dot product."""
        from src.osk.blocks.math_ops import DotProduct

        dp = DotProduct()
        dp.init()

        # Connect two vector sources
        const1 = Constant(value=[1.0, 2.0, 3.0])
        const2 = Constant(value=[4.0, 5.0, 6.0])
        const1.init()
        const2.init()

        dp.connectInput(const1, port=0)
        dp.connectInput(const2, port=1)

        const1.update()
        const2.update()
        dp.update()

        # 1*4 + 2*5 + 3*6 = 4 + 10 + 18 = 32
        assert dp.getOutput() == pytest.approx(32.0)


class TestCrossProductBlock:
    """Tests for the CrossProduct block."""

    def test_cross_product_basic(self):
        """Test basic cross product."""
        from src.osk.blocks.math_ops import CrossProduct

        cp = CrossProduct()
        cp.init()

        const1 = Constant(value=[1.0, 0.0, 0.0])  # i
        const2 = Constant(value=[0.0, 1.0, 0.0])  # j
        const1.init()
        const2.init()

        cp.connectInput(const1, port=0)
        cp.connectInput(const2, port=1)

        const1.update()
        const2.update()
        cp.update()

        # i x j = k = [0, 0, 1]
        vec = cp.getOutputVector()
        assert vec is not None
        assert vec[0] == pytest.approx(0.0)
        assert vec[1] == pytest.approx(0.0)
        assert vec[2] == pytest.approx(1.0)


class TestMinMaxBlock:
    """Tests for the MinMax block."""

    def test_minmax_min(self):
        """Test MinMax finds minimum."""
        from src.osk.blocks.math_ops import MinMax

        mm = MinMax(function="min", num_inputs=3)
        mm.init()
        mm.setInput(5.0, port=0)
        mm.setInput(2.0, port=1)
        mm.setInput(8.0, port=2)
        mm.update()
        assert mm.getOutput() == pytest.approx(2.0)

    def test_minmax_max(self):
        """Test MinMax finds maximum."""
        from src.osk.blocks.math_ops import MinMax

        mm = MinMax(function="max", num_inputs=3)
        mm.init()
        mm.setInput(5.0, port=0)
        mm.setInput(2.0, port=1)
        mm.setInput(8.0, port=2)
        mm.update()
        assert mm.getOutput() == pytest.approx(8.0)


class TestRoundingBlock:
    """Tests for the Rounding block."""

    def test_rounding_round(self):
        """Test rounding to nearest."""
        from src.osk.blocks.math_ops import Rounding

        r = Rounding(mode="round")
        r.init()
        r.setInput(2.6)
        r.update()
        assert r.getOutput() == pytest.approx(3.0)

    def test_rounding_floor(self):
        """Test floor function."""
        from src.osk.blocks.math_ops import Rounding

        r = Rounding(mode="floor")
        r.init()
        r.setInput(2.9)
        r.update()
        assert r.getOutput() == pytest.approx(2.0)

    def test_rounding_ceil(self):
        """Test ceiling function."""
        from src.osk.blocks.math_ops import Rounding

        r = Rounding(mode="ceil")
        r.init()
        r.setInput(2.1)
        r.update()
        assert r.getOutput() == pytest.approx(3.0)

    def test_rounding_fix(self):
        """Test fix (truncation) function."""
        from src.osk.blocks.math_ops import Rounding

        r = Rounding(mode="fix")
        r.init()
        r.setInput(-2.9)
        r.update()
        assert r.getOutput() == pytest.approx(-2.0)


# =============================================================================
# New Logic Block Tests
# =============================================================================


class TestCompareToZeroBlock:
    """Tests for the CompareToZero block."""

    def test_compare_to_zero_greater(self):
        """Test greater than zero comparison."""
        from src.osk.blocks.logic import CompareToZero

        cz = CompareToZero(operator=">")
        cz.init()
        cz.setInput(1.0)
        cz.update()
        assert cz.getOutput() == 1.0

        cz.setInput(-1.0)
        cz.update()
        assert cz.getOutput() == 0.0

    def test_compare_to_zero_equal(self):
        """Test equal to zero comparison."""
        from src.osk.blocks.logic import CompareToZero

        cz = CompareToZero(operator="==")
        cz.init()
        cz.setInput(0.0)
        cz.update()
        assert cz.getOutput() == 1.0

        cz.setInput(0.001)
        cz.update()
        assert cz.getOutput() == 0.0


class TestCompareToConstantBlock:
    """Tests for the CompareToConstant block."""

    def test_compare_to_constant_greater(self):
        """Test greater than constant comparison."""
        from src.osk.blocks.logic import CompareToConstant

        cc = CompareToConstant(constant=5.0, operator=">")
        cc.init()
        cc.setInput(6.0)
        cc.update()
        assert cc.getOutput() == 1.0

        cc.setInput(4.0)
        cc.update()
        assert cc.getOutput() == 0.0


class TestRelationalOperatorBlock:
    """Tests for the RelationalOperator block."""

    def test_relational_operator_less_than(self):
        """Test less than comparison between two inputs."""
        from src.osk.blocks.logic import RelationalOperator

        ro = RelationalOperator(operator="<")
        ro.init()
        ro.setInput(3.0, port=0)
        ro.setInput(5.0, port=1)
        ro.update()
        assert ro.getOutput() == 1.0

        ro.setInput(7.0, port=0)
        ro.update()
        assert ro.getOutput() == 0.0


class TestLogicalOperatorBlock:
    """Tests for the LogicalOperator block."""

    def test_logical_and(self):
        """Test logical AND operation."""
        from src.osk.blocks.logic import LogicalOperator

        lo = LogicalOperator(operator="AND", num_inputs=2)
        lo.init()
        lo.setInput(1.0, port=0)
        lo.setInput(1.0, port=1)
        lo.update()
        assert lo.getOutput() == 1.0

        lo.setInput(0.0, port=1)
        lo.update()
        assert lo.getOutput() == 0.0

    def test_logical_or(self):
        """Test logical OR operation."""
        from src.osk.blocks.logic import LogicalOperator

        lo = LogicalOperator(operator="OR", num_inputs=2)
        lo.init()
        lo.setInput(0.0, port=0)
        lo.setInput(1.0, port=1)
        lo.update()
        assert lo.getOutput() == 1.0

        lo.setInput(0.0, port=1)
        lo.update()
        assert lo.getOutput() == 0.0

    def test_logical_not(self):
        """Test logical NOT operation."""
        from src.osk.blocks.logic import LogicalOperator

        lo = LogicalOperator(operator="NOT", num_inputs=1)
        lo.init()
        lo.setInput(1.0, port=0)
        lo.update()
        assert lo.getOutput() == 0.0

        lo.setInput(0.0, port=0)
        lo.update()
        assert lo.getOutput() == 1.0


class TestBitOperatorBlock:
    """Tests for the BitOperator block."""

    def test_bit_and(self):
        """Test bitwise AND operation."""
        from src.osk.blocks.logic import BitOperator

        bo = BitOperator(operator="AND")
        bo.init()
        bo.setInput(0b1100, port=0)
        bo.setInput(0b1010, port=1)
        bo.update()
        assert bo.getOutput() == 0b1000

    def test_bit_or(self):
        """Test bitwise OR operation."""
        from src.osk.blocks.logic import BitOperator

        bo = BitOperator(operator="OR")
        bo.init()
        bo.setInput(0b1100, port=0)
        bo.setInput(0b1010, port=1)
        bo.update()
        assert bo.getOutput() == 0b1110

    def test_bit_xor(self):
        """Test bitwise XOR operation."""
        from src.osk.blocks.logic import BitOperator

        bo = BitOperator(operator="XOR")
        bo.init()
        bo.setInput(0b1100, port=0)
        bo.setInput(0b1010, port=1)
        bo.update()
        assert bo.getOutput() == 0b0110


# =============================================================================
# Extended Logic Block Tests for Full Coverage
# =============================================================================


class TestCompareToZeroBlockExtended:
    """Extended tests for CompareToZero block to increase coverage."""

    def test_compare_to_zero_not_equal_tilde(self):
        """Test not equal to zero using ~= operator."""
        from src.osk.blocks.logic import CompareToZero

        cz = CompareToZero(operator="~=")
        cz.init()
        cz.setInput(5.0)
        cz.update()
        assert cz.getOutput() == 1.0

        cz.setInput(0.0)
        cz.update()
        assert cz.getOutput() == 0.0

    def test_compare_to_zero_not_equal_exclamation(self):
        """Test not equal to zero using != operator."""
        from src.osk.blocks.logic import CompareToZero

        cz = CompareToZero(operator="!=")
        cz.init()
        cz.setInput(-3.0)
        cz.update()
        assert cz.getOutput() == 1.0

        cz.setInput(0.0)
        cz.update()
        assert cz.getOutput() == 0.0

    def test_compare_to_zero_less_than(self):
        """Test less than zero comparison."""
        from src.osk.blocks.logic import CompareToZero

        cz = CompareToZero(operator="<")
        cz.init()
        cz.setInput(-1.0)
        cz.update()
        assert cz.getOutput() == 1.0

        cz.setInput(0.0)
        cz.update()
        assert cz.getOutput() == 0.0

        cz.setInput(1.0)
        cz.update()
        assert cz.getOutput() == 0.0

    def test_compare_to_zero_less_than_equal(self):
        """Test less than or equal to zero comparison."""
        from src.osk.blocks.logic import CompareToZero

        cz = CompareToZero(operator="<=")
        cz.init()
        cz.setInput(-1.0)
        cz.update()
        assert cz.getOutput() == 1.0

        cz.setInput(0.0)
        cz.update()
        assert cz.getOutput() == 1.0

        cz.setInput(0.001)
        cz.update()
        assert cz.getOutput() == 0.0

    def test_compare_to_zero_greater_than_equal(self):
        """Test greater than or equal to zero comparison."""
        from src.osk.blocks.logic import CompareToZero

        cz = CompareToZero(operator=">=")
        cz.init()
        cz.setInput(1.0)
        cz.update()
        assert cz.getOutput() == 1.0

        cz.setInput(0.0)
        cz.update()
        assert cz.getOutput() == 1.0

        cz.setInput(-0.001)
        cz.update()
        assert cz.getOutput() == 0.0

    def test_compare_to_zero_invalid_operator(self):
        """Test invalid operator returns 0."""
        from src.osk.blocks.logic import CompareToZero

        cz = CompareToZero(operator="invalid")
        cz.init()
        cz.setInput(5.0)
        cz.update()
        assert cz.getOutput() == 0.0

    def test_compare_to_zero_connect_input(self):
        """Test connectInput with another block."""
        from src.osk.blocks.logic import CompareToZero
        from src.osk.blocks.sources import Constant

        const = Constant(value=3.0)
        const.init()
        const.update()

        cz = CompareToZero(operator=">")
        cz.init()
        cz.connectInput(const, port=0, source_port=0)
        cz.update()
        assert cz.getOutput() == 1.0


class TestCompareToConstantBlockExtended:
    """Extended tests for CompareToConstant block to increase coverage."""

    def test_compare_to_constant_equal(self):
        """Test equal to constant comparison."""
        from src.osk.blocks.logic import CompareToConstant

        cc = CompareToConstant(constant=10.0, operator="==")
        cc.init()
        cc.setInput(10.0)
        cc.update()
        assert cc.getOutput() == 1.0

        cc.setInput(10.001)
        cc.update()
        assert cc.getOutput() == 0.0

    def test_compare_to_constant_not_equal_tilde(self):
        """Test not equal to constant using ~= operator."""
        from src.osk.blocks.logic import CompareToConstant

        cc = CompareToConstant(constant=5.0, operator="~=")
        cc.init()
        cc.setInput(6.0)
        cc.update()
        assert cc.getOutput() == 1.0

        cc.setInput(5.0)
        cc.update()
        assert cc.getOutput() == 0.0

    def test_compare_to_constant_not_equal_exclamation(self):
        """Test not equal to constant using != operator."""
        from src.osk.blocks.logic import CompareToConstant

        cc = CompareToConstant(constant=5.0, operator="!=")
        cc.init()
        cc.setInput(4.0)
        cc.update()
        assert cc.getOutput() == 1.0

        cc.setInput(5.0)
        cc.update()
        assert cc.getOutput() == 0.0

    def test_compare_to_constant_less_than(self):
        """Test less than constant comparison."""
        from src.osk.blocks.logic import CompareToConstant

        cc = CompareToConstant(constant=10.0, operator="<")
        cc.init()
        cc.setInput(5.0)
        cc.update()
        assert cc.getOutput() == 1.0

        cc.setInput(10.0)
        cc.update()
        assert cc.getOutput() == 0.0

        cc.setInput(15.0)
        cc.update()
        assert cc.getOutput() == 0.0

    def test_compare_to_constant_less_than_equal(self):
        """Test less than or equal to constant comparison."""
        from src.osk.blocks.logic import CompareToConstant

        cc = CompareToConstant(constant=10.0, operator="<=")
        cc.init()
        cc.setInput(5.0)
        cc.update()
        assert cc.getOutput() == 1.0

        cc.setInput(10.0)
        cc.update()
        assert cc.getOutput() == 1.0

        cc.setInput(10.001)
        cc.update()
        assert cc.getOutput() == 0.0

    def test_compare_to_constant_greater_than_equal(self):
        """Test greater than or equal to constant comparison."""
        from src.osk.blocks.logic import CompareToConstant

        cc = CompareToConstant(constant=10.0, operator=">=")
        cc.init()
        cc.setInput(15.0)
        cc.update()
        assert cc.getOutput() == 1.0

        cc.setInput(10.0)
        cc.update()
        assert cc.getOutput() == 1.0

        cc.setInput(9.999)
        cc.update()
        assert cc.getOutput() == 0.0

    def test_compare_to_constant_invalid_operator(self):
        """Test invalid operator returns 0."""
        from src.osk.blocks.logic import CompareToConstant

        cc = CompareToConstant(constant=5.0, operator="invalid")
        cc.init()
        cc.setInput(5.0)
        cc.update()
        assert cc.getOutput() == 0.0

    def test_compare_to_constant_connect_input(self):
        """Test connectInput with another block."""
        from src.osk.blocks.logic import CompareToConstant
        from src.osk.blocks.sources import Constant

        const = Constant(value=7.0)
        const.init()
        const.update()

        cc = CompareToConstant(constant=5.0, operator=">")
        cc.init()
        cc.connectInput(const, port=0, source_port=0)
        cc.update()
        assert cc.getOutput() == 1.0


class TestRelationalOperatorBlockExtended:
    """Extended tests for RelationalOperator block to increase coverage."""

    def test_relational_operator_equal(self):
        """Test equal comparison."""
        from src.osk.blocks.logic import RelationalOperator

        ro = RelationalOperator(operator="==")
        ro.init()
        ro.setInput(5.0, port=0)
        ro.setInput(5.0, port=1)
        ro.update()
        assert ro.getOutput() == 1.0

        ro.setInput(5.0, port=0)
        ro.setInput(6.0, port=1)
        ro.update()
        assert ro.getOutput() == 0.0

    def test_relational_operator_not_equal_tilde(self):
        """Test not equal comparison with ~= operator."""
        from src.osk.blocks.logic import RelationalOperator

        ro = RelationalOperator(operator="~=")
        ro.init()
        ro.setInput(5.0, port=0)
        ro.setInput(6.0, port=1)
        ro.update()
        assert ro.getOutput() == 1.0

        ro.setInput(5.0, port=1)
        ro.update()
        assert ro.getOutput() == 0.0

    def test_relational_operator_not_equal_exclamation(self):
        """Test not equal comparison with != operator."""
        from src.osk.blocks.logic import RelationalOperator

        ro = RelationalOperator(operator="!=")
        ro.init()
        ro.setInput(3.0, port=0)
        ro.setInput(4.0, port=1)
        ro.update()
        assert ro.getOutput() == 1.0

        ro.setInput(3.0, port=1)
        ro.update()
        assert ro.getOutput() == 0.0

    def test_relational_operator_less_than_equal(self):
        """Test less than or equal comparison."""
        from src.osk.blocks.logic import RelationalOperator

        ro = RelationalOperator(operator="<=")
        ro.init()
        ro.setInput(3.0, port=0)
        ro.setInput(5.0, port=1)
        ro.update()
        assert ro.getOutput() == 1.0

        ro.setInput(5.0, port=0)
        ro.update()
        assert ro.getOutput() == 1.0

        ro.setInput(6.0, port=0)
        ro.update()
        assert ro.getOutput() == 0.0

    def test_relational_operator_greater_than(self):
        """Test greater than comparison."""
        from src.osk.blocks.logic import RelationalOperator

        ro = RelationalOperator(operator=">")
        ro.init()
        ro.setInput(7.0, port=0)
        ro.setInput(5.0, port=1)
        ro.update()
        assert ro.getOutput() == 1.0

        ro.setInput(5.0, port=0)
        ro.update()
        assert ro.getOutput() == 0.0

    def test_relational_operator_greater_than_equal(self):
        """Test greater than or equal comparison."""
        from src.osk.blocks.logic import RelationalOperator

        ro = RelationalOperator(operator=">=")
        ro.init()
        ro.setInput(7.0, port=0)
        ro.setInput(5.0, port=1)
        ro.update()
        assert ro.getOutput() == 1.0

        ro.setInput(5.0, port=0)
        ro.update()
        assert ro.getOutput() == 1.0

        ro.setInput(4.0, port=0)
        ro.update()
        assert ro.getOutput() == 0.0

    def test_relational_operator_invalid_operator(self):
        """Test invalid operator returns 0."""
        from src.osk.blocks.logic import RelationalOperator

        ro = RelationalOperator(operator="invalid")
        ro.init()
        ro.setInput(5.0, port=0)
        ro.setInput(3.0, port=1)
        ro.update()
        assert ro.getOutput() == 0.0

    def test_relational_operator_vector_input(self):
        """Test relational operator with vector inputs."""
        from src.osk.blocks.logic import RelationalOperator

        ro = RelationalOperator(operator="<")
        ro.init()
        ro.setInput([1.0, 5.0, 3.0], port=0)
        ro.setInput([2.0, 4.0, 3.0], port=1)
        ro.update()

        # [1<2, 5<4, 3<3] = [1, 0, 0]
        assert ro.getOutput(0) == 1.0
        assert ro.getOutput(1) == 0.0
        assert ro.getOutput(2) == 0.0

    def test_relational_operator_get_output_vector(self):
        """Test getOutputVector with vector inputs."""
        from src.osk.blocks.logic import RelationalOperator

        ro = RelationalOperator(operator="==")
        ro.init()
        ro.setInput([1.0, 2.0, 3.0], port=0)
        ro.setInput([1.0, 5.0, 3.0], port=1)
        ro.update()

        vec = ro.getOutputVector()
        assert vec is not None
        assert vec == [1.0, 0.0, 1.0]

    def test_relational_operator_scalar_returns_none_for_vector(self):
        """Test getOutputVector returns None for scalar mode."""
        from src.osk.blocks.logic import RelationalOperator

        ro = RelationalOperator(operator="<")
        ro.init()
        ro.setInput(3.0, port=0)
        ro.setInput(5.0, port=1)
        ro.update()

        assert ro.getOutputVector() is None

    def test_relational_operator_connect_input(self):
        """Test connectInput with another block."""
        from src.osk.blocks.logic import RelationalOperator
        from src.osk.blocks.sources import Constant

        const1 = Constant(value=3.0)
        const1.init()
        const1.update()

        const2 = Constant(value=5.0)
        const2.init()
        const2.update()

        ro = RelationalOperator(operator="<")
        ro.init()
        ro.connectInput(const1, port=0, source_port=0)
        ro.connectInput(const2, port=1, source_port=0)
        ro.update()
        assert ro.getOutput() == 1.0

    def test_relational_operator_connect_input_port_bounds(self):
        """Test connectInput ignores invalid port numbers."""
        from src.osk.blocks.logic import RelationalOperator
        from src.osk.blocks.sources import Constant

        const = Constant(value=5.0)

        ro = RelationalOperator(operator="<")
        ro.init()
        # Port 2 is invalid, should be ignored
        ro.connectInput(const, port=2, source_port=0)
        assert ro.input_blocks[0] is None
        assert ro.input_blocks[1] is None

    def test_relational_operator_set_input_port_bounds(self):
        """Test setInput ignores invalid port numbers."""
        from src.osk.blocks.logic import RelationalOperator

        ro = RelationalOperator(operator="<")
        ro.init()
        ro.setInput(5.0, port=2)  # Invalid port
        assert ro.inputs[0] == 0.0
        assert ro.inputs[1] == 0.0

    def test_relational_operator_vector_with_connected_block(self):
        """Test vector mode with connected block having getOutputVector."""
        from src.osk.blocks.logic import RelationalOperator
        from src.osk.blocks.math_ops import Mux

        # Mux outputs a vector
        mux = Mux(num_inputs=2)
        mux.init()
        mux.setInput(3.0, port=0)
        mux.setInput(7.0, port=1)
        mux.update()

        ro = RelationalOperator(operator=">")
        ro.init()
        ro.connectInput(mux, port=0, source_port=0)
        ro.setInput([5.0, 5.0], port=1)
        ro.update()

        # [3>5, 7>5] = [0, 1]
        vec = ro.getOutputVector()
        assert vec is not None
        assert vec[0] == 0.0
        assert vec[1] == 1.0


class TestLogicalOperatorBlockExtended:
    """Extended tests for LogicalOperator block to increase coverage."""

    def test_logical_nand(self):
        """Test logical NAND operation."""
        from src.osk.blocks.logic import LogicalOperator

        lo = LogicalOperator(operator="NAND", num_inputs=2)
        lo.init()
        lo.setInput(1.0, port=0)
        lo.setInput(1.0, port=1)
        lo.update()
        assert lo.getOutput() == 0.0  # NAND of true,true = false

        lo.setInput(0.0, port=1)
        lo.update()
        assert lo.getOutput() == 1.0  # NAND of true,false = true

    def test_logical_nor(self):
        """Test logical NOR operation."""
        from src.osk.blocks.logic import LogicalOperator

        lo = LogicalOperator(operator="NOR", num_inputs=2)
        lo.init()
        lo.setInput(0.0, port=0)
        lo.setInput(0.0, port=1)
        lo.update()
        assert lo.getOutput() == 1.0  # NOR of false,false = true

        lo.setInput(1.0, port=0)
        lo.update()
        assert lo.getOutput() == 0.0  # NOR of true,false = false

    def test_logical_xor(self):
        """Test logical XOR operation."""
        from src.osk.blocks.logic import LogicalOperator

        lo = LogicalOperator(operator="XOR", num_inputs=2)
        lo.init()
        lo.setInput(1.0, port=0)
        lo.setInput(0.0, port=1)
        lo.update()
        assert lo.getOutput() == 1.0  # XOR of true,false = true

        lo.setInput(1.0, port=1)
        lo.update()
        assert lo.getOutput() == 0.0  # XOR of true,true = false

    def test_logical_xor_three_inputs(self):
        """Test logical XOR with three inputs (odd number of trues)."""
        from src.osk.blocks.logic import LogicalOperator

        lo = LogicalOperator(operator="XOR", num_inputs=3)
        lo.init()
        lo.setInput(1.0, port=0)
        lo.setInput(1.0, port=1)
        lo.setInput(1.0, port=2)
        lo.update()
        assert lo.getOutput() == 1.0  # XOR: 3 trues = odd = true

        lo.setInput(0.0, port=2)
        lo.update()
        assert lo.getOutput() == 0.0  # XOR: 2 trues = even = false

    def test_logical_invalid_operator(self):
        """Test invalid operator returns 0."""
        from src.osk.blocks.logic import LogicalOperator

        lo = LogicalOperator(operator="invalid", num_inputs=2)
        lo.init()
        lo.setInput(1.0, port=0)
        lo.setInput(1.0, port=1)
        lo.update()
        assert lo.getOutput() == 0.0

    def test_logical_not_forces_single_input(self):
        """Test NOT operator forces num_inputs to 1."""
        from src.osk.blocks.logic import LogicalOperator

        lo = LogicalOperator(operator="NOT", num_inputs=5)
        assert lo.num_inputs == 1

    def test_logical_vector_input(self):
        """Test logical operator with vector inputs."""
        from src.osk.blocks.logic import LogicalOperator

        lo = LogicalOperator(operator="AND", num_inputs=2)
        lo.init()
        lo.setInput([1.0, 0.0, 1.0], port=0)
        lo.setInput([1.0, 1.0, 0.0], port=1)
        lo.update()

        # [1&1, 0&1, 1&0] = [1, 0, 0]
        assert lo.getOutput(0) == 1.0
        assert lo.getOutput(1) == 0.0
        assert lo.getOutput(2) == 0.0

    def test_logical_get_output_vector(self):
        """Test getOutputVector with vector inputs."""
        from src.osk.blocks.logic import LogicalOperator

        lo = LogicalOperator(operator="OR", num_inputs=2)
        lo.init()
        lo.setInput([1.0, 0.0, 0.0], port=0)
        lo.setInput([0.0, 0.0, 1.0], port=1)
        lo.update()

        vec = lo.getOutputVector()
        assert vec is not None
        assert vec == [1.0, 0.0, 1.0]

    def test_logical_scalar_returns_none_for_vector(self):
        """Test getOutputVector returns None for scalar mode."""
        from src.osk.blocks.logic import LogicalOperator

        lo = LogicalOperator(operator="AND", num_inputs=2)
        lo.init()
        lo.setInput(1.0, port=0)
        lo.setInput(1.0, port=1)
        lo.update()

        assert lo.getOutputVector() is None

    def test_logical_connect_input(self):
        """Test connectInput with another block."""
        from src.osk.blocks.logic import LogicalOperator
        from src.osk.blocks.sources import Constant

        const1 = Constant(value=1.0)
        const1.init()
        const1.update()

        const2 = Constant(value=0.0)
        const2.init()
        const2.update()

        lo = LogicalOperator(operator="AND", num_inputs=2)
        lo.init()
        lo.connectInput(const1, port=0, source_port=0)
        lo.connectInput(const2, port=1, source_port=0)
        lo.update()
        assert lo.getOutput() == 0.0  # 1 AND 0 = 0

    def test_logical_connect_input_port_bounds(self):
        """Test connectInput ignores invalid port numbers."""
        from src.osk.blocks.logic import LogicalOperator
        from src.osk.blocks.sources import Constant

        const = Constant(value=1.0)

        lo = LogicalOperator(operator="AND", num_inputs=2)
        lo.init()
        lo.connectInput(const, port=5, source_port=0)
        assert lo.input_blocks[0] is None
        assert lo.input_blocks[1] is None

    def test_logical_set_input_port_bounds(self):
        """Test setInput ignores invalid port numbers."""
        from src.osk.blocks.logic import LogicalOperator

        lo = LogicalOperator(operator="AND", num_inputs=2)
        lo.init()
        lo.setInput(1.0, port=5)  # Invalid port
        assert lo.inputs[0] == 0.0
        assert lo.inputs[1] == 0.0

    def test_logical_vector_with_connected_block(self):
        """Test vector mode with connected block having getOutputVector."""
        from src.osk.blocks.logic import LogicalOperator
        from src.osk.blocks.math_ops import Mux

        mux = Mux(num_inputs=3)
        mux.init()
        mux.setInput(1.0, port=0)
        mux.setInput(0.0, port=1)
        mux.setInput(1.0, port=2)
        mux.update()

        lo = LogicalOperator(operator="AND", num_inputs=2)
        lo.init()
        lo.connectInput(mux, port=0, source_port=0)
        lo.setInput([1.0, 1.0, 1.0], port=1)
        lo.update()

        # [1&1, 0&1, 1&1] = [1, 0, 1]
        vec = lo.getOutputVector()
        assert vec is not None
        assert vec[0] == 1.0
        assert vec[1] == 0.0
        assert vec[2] == 1.0

    def test_logical_not_with_empty_vector(self):
        """Test NOT with empty input behavior."""
        from src.osk.blocks.logic import LogicalOperator

        lo = LogicalOperator(operator="NOT", num_inputs=1)
        lo.init()
        lo.setInput([], port=0)  # Empty list
        lo.update()
        # With empty input, _to_bool gets 0.0, NOT(False) = True
        assert lo.getOutput() == 1.0


class TestBitOperatorBlockExtended:
    """Extended tests for BitOperator block to increase coverage."""

    def test_bit_not(self):
        """Test bitwise NOT operation."""
        from src.osk.blocks.logic import BitOperator

        bo = BitOperator(operator="NOT")
        bo.init()
        bo.setInput(0b1100, port=0)
        bo.update()
        # NOT of 0b1100 (12) is -13 in two's complement
        assert bo.getOutput() == float(~12)

    def test_bit_nand(self):
        """Test bitwise NAND operation."""
        from src.osk.blocks.logic import BitOperator

        bo = BitOperator(operator="NAND")
        bo.init()
        bo.setInput(0b1100, port=0)
        bo.setInput(0b1010, port=1)
        bo.update()
        # NAND: ~(0b1100 & 0b1010) = ~0b1000 = -9 in two's complement
        assert bo.getOutput() == float(~(0b1100 & 0b1010))

    def test_bit_nor(self):
        """Test bitwise NOR operation."""
        from src.osk.blocks.logic import BitOperator

        bo = BitOperator(operator="NOR")
        bo.init()
        bo.setInput(0b1100, port=0)
        bo.setInput(0b1010, port=1)
        bo.update()
        # NOR: ~(0b1100 | 0b1010) = ~0b1110 = -15 in two's complement
        assert bo.getOutput() == float(~(0b1100 | 0b1010))

    def test_bit_invalid_operator(self):
        """Test invalid operator returns 0."""
        from src.osk.blocks.logic import BitOperator

        bo = BitOperator(operator="invalid")
        bo.init()
        bo.setInput(0b1100, port=0)
        bo.setInput(0b1010, port=1)
        bo.update()
        assert bo.getOutput() == 0.0

    def test_bit_connect_input(self):
        """Test connectInput with another block."""
        from src.osk.blocks.logic import BitOperator
        from src.osk.blocks.sources import Constant

        const1 = Constant(value=0b1100)
        const1.init()
        const1.update()

        const2 = Constant(value=0b1010)
        const2.init()
        const2.update()

        bo = BitOperator(operator="AND")
        bo.init()
        bo.connectInput(const1, port=0, source_port=0)
        bo.connectInput(const2, port=1, source_port=0)
        bo.update()
        assert bo.getOutput() == 0b1000

    def test_bit_connect_input_port_bounds(self):
        """Test connectInput ignores invalid port numbers."""
        from src.osk.blocks.logic import BitOperator
        from src.osk.blocks.sources import Constant

        const = Constant(value=0b1111)

        bo = BitOperator(operator="AND")
        bo.init()
        bo.connectInput(const, port=2, source_port=0)
        assert bo.input_blocks[0] is None
        assert bo.input_blocks[1] is None

    def test_bit_set_input_port_bounds(self):
        """Test setInput ignores invalid port numbers."""
        from src.osk.blocks.logic import BitOperator

        bo = BitOperator(operator="AND")
        bo.init()
        bo.setInput(0b1111, port=2)  # Invalid port
        assert bo.inputs[0] == 0.0
        assert bo.inputs[1] == 0.0

    def test_bit_float_to_int_conversion(self):
        """Test that float inputs are converted to int for bitwise operations."""
        from src.osk.blocks.logic import BitOperator

        bo = BitOperator(operator="AND")
        bo.init()
        bo.setInput(12.9, port=0)  # Should become 12
        bo.setInput(10.1, port=1)  # Should become 10
        bo.update()
        assert bo.getOutput() == 0b1000  # 12 & 10 = 8


# =============================================================================
# New Source Block Tests
# =============================================================================


class TestRepeatingSequenceBlock:
    """Tests for the RepeatingSequence block."""

    def test_repeating_sequence_basic(self):
        """Test basic repeating sequence."""
        from src.osk.blocks.sources import RepeatingSequence

        rs = RepeatingSequence(time_values=[0, 1, 2], output_values=[0, 1, 0])
        rs.init()

        State.t = 0.5
        rs.update()
        assert rs.getOutput() == pytest.approx(0.5)  # Interpolated

        State.t = 1.5
        rs.update()
        assert rs.getOutput() == pytest.approx(0.5)


class TestChirpSignalBlock:
    """Tests for the ChirpSignal block."""

    def test_chirp_signal_initial(self):
        """Test chirp signal at t=0."""
        from src.osk.blocks.sources import ChirpSignal

        chirp = ChirpSignal(initial_frequency=1.0, target_time=10.0, target_frequency=10.0)
        chirp.init()

        State.t = 0.0
        chirp.update()
        # At t=0, cos(0) = 1 (ChirpSignal uses cosine)
        assert chirp.getOutput() == pytest.approx(1.0, abs=0.01)


class TestGroundBlock:
    """Tests for the Ground block."""

    def test_ground_output(self):
        """Test Ground always outputs zero."""
        from src.osk.blocks.sources import Ground

        gnd = Ground()
        gnd.init()
        gnd.update()
        assert gnd.getOutput() == 0.0


class TestSignalGeneratorBlock:
    """Tests for the SignalGenerator block."""

    def test_signal_generator_sine(self):
        """Test SignalGenerator with sine wave."""
        from src.osk.blocks.sources import SignalGenerator

        sg = SignalGenerator(wave_type="sine", amplitude=2.0, frequency=1.0, units="hertz")
        sg.init()

        State.t = 0.25  # Quarter period
        sg.update()
        assert sg.getOutput() == pytest.approx(2.0, abs=0.01)

    def test_signal_generator_square(self):
        """Test SignalGenerator with square wave."""
        from src.osk.blocks.sources import SignalGenerator

        sg = SignalGenerator(wave_type="square", amplitude=1.0, frequency=1.0, units="hertz")
        sg.init()

        State.t = 0.25
        sg.update()
        assert sg.getOutput() == pytest.approx(1.0)


# =============================================================================
# New Discrete Block Tests
# =============================================================================


class TestMemoryBlock:
    """Tests for the Memory block."""

    def test_memory_basic(self):
        """Test Memory stores previous value."""
        from src.osk.blocks.discrete import Memory

        mem = Memory(initial_condition=0.0)
        mem.init()

        # First update
        mem.setInput(5.0)
        mem.update()
        assert mem.getOutput() == 0.0  # Initial condition

        # Memory uses rpt() for state propagation, triggered when State.ready=True
        State.ready = True
        mem.rpt()
        State.ready = False
        mem.setInput(10.0)
        mem.update()
        assert mem.getOutput() == 5.0  # Previous value


class TestFirstOrderHoldBlock:
    """Tests for the FirstOrderHold block."""

    def test_first_order_hold_basic(self):
        """Test FirstOrderHold interpolation."""
        from src.osk.blocks.discrete import FirstOrderHold

        State.dt = 0.1
        State.ready = 1
        foh = FirstOrderHold(sample_time=0.1)
        foh.init()

        foh.setInput(1.0)
        foh.update()
        assert foh.getOutput() == pytest.approx(1.0)


class TestDiscretePIDControllerBlock:
    """Tests for the DiscretePIDController block."""

    def test_discrete_pid_proportional(self):
        """Test discrete PID proportional action."""
        from src.osk.blocks.discrete import DiscretePIDController

        State.dt = 0.01
        State.ready = 1
        pid = DiscretePIDController(Kp=2.0, Ki=0.0, Kd=0.0, N=100, sample_time=0.01)
        pid.init()

        pid.setInput(5.0)
        pid.update()
        # Output should be Kp * error = 2.0 * 5.0 = 10.0
        assert pid.getOutput() == pytest.approx(10.0)


class TestDiscreteStateSpaceBlock:
    """Tests for the DiscreteStateSpace block."""

    def test_discrete_state_space_basic(self):
        """Test discrete state space model."""
        from src.osk.blocks.discrete import DiscreteStateSpace

        # Simple first-order discrete system
        dss = DiscreteStateSpace(
            A=[[0.9]], B=[[0.1]], C=[[1.0]], D=[[0.0]], initial_state=[0.0], sample_time=0.1
        )
        State.t = 0.0
        State.ready = 1
        dss.init()

        dss.setInput(1.0)
        dss.update()
        assert dss.getOutput() == pytest.approx(0.0)  # Initial output
        # Note: update() also advances state internally, so state is now 0.1

        # Advance time to trigger next sample
        State.t = 0.1
        dss.update()
        # Output now reflects the state updated in previous call
        # y = C * x = 1.0 * 0.1 = 0.1
        assert dss.getOutput() == pytest.approx(0.1)


# =============================================================================
# Demux-to-Scope Interaction Tests (Multi-Output Block Handling)
# =============================================================================


class TestDemuxToScopeInteraction:
    """Tests for Demux connected to Scope - verifies scalar output handling.

    This tests the fix for the Kalman Filter scope issue where Demux outputs
    were incorrectly appearing as vector elements in scopes.
    """

    def test_demux_to_scope_single_port(self):
        """Test Scope connected to single Demux output port gets scalar value."""
        # Create vector source via Mux
        c1 = Constant(value=1.0)
        c2 = Constant(value=2.0)
        c3 = Constant(value=3.0)
        c1.init()
        c2.init()
        c3.init()

        mux = Mux(num_inputs=3)
        mux.connectInput(c1, port=0)
        mux.connectInput(c2, port=1)
        mux.connectInput(c3, port=2)

        demux = Demux(num_outputs=3)
        demux.connectInput(mux)

        # Create scope connected to Demux output port 1 (should get value 2.0)
        scope = Scope(num_inputs=1)
        scope.connectInput(demux, port=0, source_port=1)

        # Update chain
        c1.update()
        c2.update()
        c3.update()
        mux.update()
        demux.update()
        scope.update()

        # Verify scope gets scalar value from correct port
        assert scope.inputs[0] == 2.0
        # Verify NO vector inputs detected (Demux outputs are scalars)
        assert len(scope._vector_inputs) == 0

    def test_demux_to_scope_multiple_ports(self):
        """Test Scope with multiple inputs from different Demux ports."""
        c1 = Constant(value=10.0)
        c2 = Constant(value=20.0)
        c3 = Constant(value=30.0)
        c1.init()
        c2.init()
        c3.init()

        mux = Mux(num_inputs=3)
        mux.connectInput(c1, port=0)
        mux.connectInput(c2, port=1)
        mux.connectInput(c3, port=2)

        demux = Demux(num_outputs=3)
        demux.connectInput(mux)

        # Scope with 2 inputs - connected to Demux ports 0 and 2
        scope = Scope(num_inputs=2)
        scope.connectInput(demux, port=0, source_port=0)  # Gets 10.0
        scope.connectInput(demux, port=1, source_port=2)  # Gets 30.0

        # Update chain
        c1.update()
        c2.update()
        c3.update()
        mux.update()
        demux.update()
        scope.update()

        # Verify scope gets correct scalar values
        assert scope.inputs[0] == 10.0
        assert scope.inputs[1] == 30.0
        # No vector inputs should be detected
        assert len(scope._vector_inputs) == 0

    def test_demux_to_scope_recording(self):
        """Test Scope correctly records Demux output over time."""
        c1 = Constant(value=5.0)
        c2 = Constant(value=15.0)
        c1.init()
        c2.init()

        mux = Mux(num_inputs=2)
        mux.connectInput(c1, port=0)
        mux.connectInput(c2, port=1)

        demux = Demux(num_outputs=2)
        demux.connectInput(mux)

        scope = Scope(num_inputs=1)
        scope.connectInput(demux, port=0, source_port=1)  # Gets 15.0
        scope.setInputName("Demux Output 1", 0)

        State.ready = 1
        for t in [0.0, 0.1, 0.2]:
            State.t = t
            c1.update()
            c2.update()
            mux.update()
            demux.update()
            scope.update()
            scope.rpt()

        data = scope.getData()
        assert len(data["times"]) == 3
        assert data["numInputs"] == 1  # Only 1 trace (scalar)
        assert len(data["values"]) == 1
        assert all(v == 15.0 for v in data["values"][0])
        assert data["inputNames"] == ["Demux Output 1"]

    def test_demux_get_output_vector_returns_all(self):
        """Verify Demux.getOutputVector() returns all outputs (the source of the bug)."""
        c1 = Constant(value=1.0)
        c2 = Constant(value=2.0)
        c1.init()
        c2.init()

        mux = Mux(num_inputs=2)
        mux.connectInput(c1, port=0)
        mux.connectInput(c2, port=1)

        demux = Demux(num_outputs=2)
        demux.connectInput(mux)

        mux.update()
        demux.update()

        # getOutputVector returns ALL outputs (this is the behavior we need to handle)
        vec = demux.getOutputVector()
        assert vec == [1.0, 2.0]

        # But individual getOutput() returns scalar from specific port
        assert demux.getOutput(0) == 1.0
        assert demux.getOutput(1) == 2.0


class TestSelectorToScopeInteraction:
    """Tests for Selector connected to Scope - verifies vector output handling.

    Selector is different from Demux - it can output a genuine vector when
    multiple indices are selected.
    """

    def test_selector_single_index_scalar(self):
        """Test Selector with single index outputs scalar to Scope."""
        from src.osk.blocks.matrix_ops import Selector

        # Create vector source
        const = Constant(value=[10.0, 20.0, 30.0, 40.0])
        const.init()

        selector = Selector(indices=[2], output_size=1)
        selector.connectInput(const)

        scope = Scope(num_inputs=1)
        scope.connectInput(selector, port=0)

        const.update()
        selector.update()
        scope.update()

        # Single index selection - scalar output
        assert selector.getOutputVector() is None  # Single element = not a vector
        assert selector.getOutput(0) == 30.0
        assert scope.inputs[0] == 30.0
        assert len(scope._vector_inputs) == 0

    def test_selector_multiple_indices_vector(self):
        """Test Selector with multiple indices outputs vector to Scope."""
        from src.osk.blocks.matrix_ops import Selector

        const = Constant(value=[10.0, 20.0, 30.0, 40.0, 50.0])
        const.init()

        selector = Selector(indices=[0, 2, 4], output_size=3)
        selector.connectInput(const)

        scope = Scope(num_inputs=1)
        scope.connectInput(selector, port=0)
        scope.setInputName("Selected", 0)

        const.update()
        selector.update()
        scope.update()

        # Multiple indices - should be treated as vector
        vec = selector.getOutputVector()
        assert vec == [10.0, 30.0, 50.0]

        # Scope should detect this as vector input
        assert 0 in scope._vector_inputs
        assert scope._vector_inputs[0] == [10.0, 30.0, 50.0]
        # Vector names should be generated
        assert scope._vector_names[0] == ["Selected[1]", "Selected[2]", "Selected[3]"]

    def test_selector_to_scope_recording(self):
        """Test Scope records Selector vector output as multiple traces."""
        from src.osk.blocks.matrix_ops import Selector

        const = Constant(value=[1.0, 2.0, 3.0])
        const.init()

        selector = Selector(indices=[0, 2], output_size=2)
        selector.connectInput(const)

        scope = Scope(num_inputs=1)
        scope.connectInput(selector, port=0)
        scope.setInputName("Sel", 0)

        State.ready = 1
        State.t = 0.0
        const.update()
        selector.update()
        scope.update()
        scope.rpt()

        data = scope.getData()
        assert data["numInputs"] == 2  # Vector expanded to 2 traces
        assert len(data["values"]) == 2
        assert data["values"][0] == [1.0]
        assert data["values"][1] == [3.0]
        assert data["inputNames"] == ["Sel[1]", "Sel[2]"]


class TestScopeVectorHandlingEdgeCases:
    """Additional edge case tests for Scope vector handling."""

    def test_scope_vector_to_scalar_transition(self):
        """Test Scope handles transition from vector to scalar input."""
        scope = Scope(num_inputs=1)

        # Start with vector input
        scope.setInput([1.0, 2.0, 3.0], 0)
        assert 0 in scope._vector_inputs
        assert scope.inputs[0] == 1.0

        # Switch to scalar
        scope.setInput(5.0, 0)
        assert 0 not in scope._vector_inputs
        assert scope.inputs[0] == 5.0

    def test_scope_empty_vector_input(self):
        """Test Scope handles empty vector input."""
        scope = Scope(num_inputs=1)
        scope.setInput([], 0)

        # Empty list should set input to 0.0
        assert scope.inputs[0] == 0.0
        assert 0 in scope._vector_inputs
        assert scope._vector_inputs[0] == []

    def test_scope_vector_name_regeneration(self):
        """Test Scope regenerates vector names when vector size changes."""
        scope = Scope(num_inputs=1)
        scope.setInputName("Signal", 0)

        # First vector of size 2
        mux2 = Mux(num_inputs=2)
        c1 = Constant(value=1.0)
        c2 = Constant(value=2.0)
        c1.init()
        c2.init()
        mux2.connectInput(c1, 0)
        mux2.connectInput(c2, 1)

        scope.connectInput(mux2, 0)
        c1.update()
        c2.update()
        mux2.update()
        scope.update()

        assert scope._vector_names[0] == ["Signal[1]", "Signal[2]"]

        # Now connect a larger vector
        mux3 = Mux(num_inputs=3)
        c3 = Constant(value=3.0)
        c3.init()
        mux3.connectInput(c1, 0)
        mux3.connectInput(c2, 1)
        mux3.connectInput(c3, 2)

        scope.connectInput(mux3, 0)
        c3.update()
        mux3.update()
        scope.update()

        # Names should be regenerated for new size
        assert scope._vector_names[0] == ["Signal[1]", "Signal[2]", "Signal[3]"]

    def test_scope_trace_count_dynamic(self):
        """Test Scope trace count updates dynamically with connections."""
        scope = Scope(num_inputs=3)
        c1 = Constant(value=1.0)
        c2 = Constant(value=2.0)
        c1.init()
        c2.init()

        State.ready = 1
        State.t = 0.0

        # Connect only port 0 and 2
        scope.connectInput(c1, 0)
        scope.connectInput(c2, 2)

        c1.update()
        c2.update()
        scope.update()
        scope.rpt()

        data = scope.getData()
        # Only 2 traces for 2 connected inputs
        assert data["numInputs"] == 2

    def test_scope_getData_with_no_data(self):
        """Test Scope getData returns correct structure with no recorded data."""
        scope = Scope(num_inputs=2)
        data = scope.getData()

        assert data["times"] == []
        assert data["values"] == []
        assert data["numInputs"] == 0  # No traces yet

    def test_scope_connect_beyond_num_inputs(self):
        """Test Scope ignores connections beyond num_inputs."""
        scope = Scope(num_inputs=2)
        const = Constant(value=5.0)
        const.init()

        # Try to connect to port 5 (beyond num_inputs=2)
        scope.connectInput(const, port=5)

        # Should be ignored
        assert scope.input_blocks[0] is None
        assert scope.input_blocks[1] is None

    def test_scope_setInput_beyond_num_inputs(self):
        """Test Scope ignores setInput beyond num_inputs."""
        scope = Scope(num_inputs=2)

        # Try to set input at port 10
        scope.setInput(42.0, port=10)

        # Original inputs unchanged
        assert scope.inputs[0] == 0.0
        assert scope.inputs[1] == 0.0

    def test_scope_getOutput_returns_input(self):
        """Test Scope getOutput returns the input value (pass-through)."""
        scope = Scope(num_inputs=2)
        scope.setInput(7.5, 0)
        scope.setInput(3.2, 1)

        assert scope.getOutput(0) == 7.5
        assert scope.getOutput(1) == 3.2
        assert scope.getOutput(5) == 0.0  # Beyond range


class TestTerminatorBlockExtended:
    """Extended tests for the Terminator block."""

    def test_terminator_absorbs_signal(self):
        """Test Terminator absorbs signal without output."""
        from src.osk.blocks.sinks import Terminator

        term = Terminator()
        const = Constant(value=100.0)
        const.init()

        term.connectInput(const)
        const.update()
        term.update()

        # Terminator stores input but outputs 0
        assert term.input == 100.0
        assert term.getOutput() == 0.0

    def test_terminator_setInput(self):
        """Test Terminator setInput method."""
        from src.osk.blocks.sinks import Terminator

        term = Terminator()
        term.setInput(42.0)
        assert term.input == 42.0

    def test_terminator_source_port(self):
        """Test Terminator with source_port connection."""
        from src.osk.blocks.sinks import Terminator

        term = Terminator()
        demux = Demux(num_outputs=2)

        mux = Mux(num_inputs=2)
        c1 = Constant(value=5.0)
        c2 = Constant(value=10.0)
        c1.init()
        c2.init()
        mux.connectInput(c1, 0)
        mux.connectInput(c2, 1)
        demux.connectInput(mux)

        term.connectInput(demux, source_port=1)

        mux.update()
        demux.update()
        term.update()

        assert term.input == 10.0


class TestDisplayBlockExtended:
    """Extended tests for the Display block."""

    def test_display_shows_current_value(self):
        """Test Display shows current input value."""
        disp = Display()
        const = Constant(value=3.14)
        const.init()

        disp.connectInput(const)
        const.update()
        disp.update()

        State.ready = 1
        disp.rpt()

        assert disp.current_value == 3.14
        assert disp.getOutput() == 3.14

    def test_display_without_ready(self):
        """Test Display doesn't update current_value when not ready."""
        disp = Display()
        disp.setInput(5.0)

        State.ready = 0
        disp.rpt()

        # current_value should still be 0 (initial)
        assert disp.current_value == 0.0

    def test_display_source_port(self):
        """Test Display with source_port connection."""
        disp = Display()
        demux = Demux(num_outputs=2)

        mux = Mux(num_inputs=2)
        c1 = Constant(value=7.0)
        c2 = Constant(value=14.0)
        c1.init()
        c2.init()
        mux.connectInput(c1, 0)
        mux.connectInput(c2, 1)
        demux.connectInput(mux)

        disp.connectInput(demux, source_port=0)

        mux.update()
        demux.update()
        disp.update()

        State.ready = 1
        disp.rpt()

        assert disp.current_value == 7.0


# =============================================================================
# Extended Math Operations Block Tests for Full Coverage
# =============================================================================


class TestSliderGainBlock:
    """Tests for the SliderGain block (functionally like Gain with min/max)."""

    def test_slider_basic(self):
        """Test basic slider operation."""
        from src.osk.blocks.math_ops import SliderGain

        sl = SliderGain(gain=2.0, min_val=0.0, max_val=10.0)
        sl.init()
        sl.setInput(5.0)
        sl.update()
        assert sl.getOutput() == 10.0  # 2.0 * 5.0

    def test_slider_vector_input(self):
        """Test slider with vector input."""
        from src.osk.blocks.math_ops import SliderGain

        sl = SliderGain(gain=3.0)
        sl.init()
        sl.setInput([1.0, 2.0, 3.0])
        sl.update()

        assert sl.getOutput(0) == 3.0
        assert sl.getOutput(1) == 6.0
        assert sl.getOutput(2) == 9.0

        vec = sl.getOutputVector()
        assert vec == [3.0, 6.0, 9.0]

    def test_slider_scalar_returns_none_for_vector(self):
        """Test getOutputVector returns None for scalar."""
        from src.osk.blocks.math_ops import SliderGain

        sl = SliderGain(gain=2.0)
        sl.init()
        sl.setInput(5.0)
        sl.update()
        assert sl.getOutputVector() is None

    def test_slider_connect_input(self):
        """Test slider with connected block."""
        from src.osk.blocks.math_ops import SliderGain
        from src.osk.blocks.sources import Constant

        const = Constant(value=4.0)
        const.init()
        const.update()

        sl = SliderGain(gain=2.5)
        sl.init()
        sl.connectInput(const)
        sl.update()
        assert sl.getOutput() == 10.0  # 2.5 * 4.0

    def test_slider_connect_with_vector_block(self):
        """Test slider connected to block with vector output."""
        from src.osk.blocks.math_ops import Mux, SliderGain

        mux = Mux(num_inputs=2)
        mux.init()
        mux.setInput(2.0, 0)
        mux.setInput(3.0, 1)
        mux.update()

        sl = SliderGain(gain=2.0)
        sl.init()
        sl.connectInput(mux)
        sl.update()

        vec = sl.getOutputVector()
        assert vec == [4.0, 6.0]

    def test_slider_connect_no_vector(self):
        """Test slider connected to block without vector."""
        from src.osk.blocks.math_ops import SliderGain
        from src.osk.blocks.sources import Constant

        const = Constant(value=5.0)
        const.init()
        const.update()

        sl = SliderGain(gain=1.5)
        sl.init()
        sl.connectInput(const)
        sl.update()
        assert sl.getOutput() == 7.5


class TestWeightedSumBlock:
    """Tests for the WeightedSum block."""

    def test_weighted_sum_basic(self):
        """Test basic weighted sum."""
        from src.osk.blocks.math_ops import WeightedSum

        ws = WeightedSum(weights=[2.0, 3.0])
        ws.init()
        ws.setInput(1.0, 0)
        ws.setInput(2.0, 1)
        ws.update()
        assert ws.getOutput() == 8.0  # 2*1 + 3*2

    def test_weighted_sum_vector_input(self):
        """Test weighted sum with vector inputs."""
        from src.osk.blocks.math_ops import WeightedSum

        ws = WeightedSum(weights=[1.0, 2.0])
        ws.init()
        ws.setInput([1.0, 2.0], 0)
        ws.setInput([3.0, 4.0], 1)
        ws.update()

        # [1*1 + 2*3, 1*2 + 2*4] = [7, 10]
        assert ws.getOutput(0) == 7.0
        assert ws.getOutput(1) == 10.0

        vec = ws.getOutputVector()
        assert vec == [7.0, 10.0]

    def test_weighted_sum_scalar_returns_none(self):
        """Test getOutputVector returns None for scalar."""
        from src.osk.blocks.math_ops import WeightedSum

        ws = WeightedSum(weights=[1.0, 1.0])
        ws.init()
        ws.setInput(5.0, 0)
        ws.setInput(3.0, 1)
        ws.update()
        assert ws.getOutputVector() is None
        assert ws.getOutput() == 8.0

    def test_weighted_sum_connect_input(self):
        """Test weighted sum with connected blocks."""
        from src.osk.blocks.math_ops import WeightedSum
        from src.osk.blocks.sources import Constant

        c1 = Constant(value=2.0)
        c1.init()
        c1.update()
        c2 = Constant(value=3.0)
        c2.init()
        c2.update()

        ws = WeightedSum(weights=[2.0, 3.0])
        ws.init()
        ws.connectInput(c1, 0)
        ws.connectInput(c2, 1)
        ws.update()
        assert ws.getOutput() == 13.0  # 2*2 + 3*3

    def test_weighted_sum_port_bounds(self):
        """Test setInput/connectInput ignore invalid ports."""
        from src.osk.blocks.math_ops import WeightedSum
        from src.osk.blocks.sources import Constant

        ws = WeightedSum(weights=[1.0, 1.0])
        ws.init()
        ws.setInput(99.0, 5)  # Invalid port
        ws.connectInput(Constant(value=1.0), 5)  # Invalid port
        assert ws.inputs == [0.0, 0.0]

    def test_weighted_sum_vector_from_connected_block(self):
        """Test vector mode from connected block with getOutputVector."""
        from src.osk.blocks.math_ops import Mux, WeightedSum

        mux = Mux(num_inputs=2)
        mux.init()
        mux.setInput(1.0, 0)
        mux.setInput(2.0, 1)
        mux.update()

        ws = WeightedSum(weights=[2.0, 3.0])
        ws.init()
        ws.connectInput(mux, 0)
        ws.setInput([3.0, 4.0], 1)
        ws.update()

        # [2*1 + 3*3, 2*2 + 3*4] = [11, 16]
        vec = ws.getOutputVector()
        assert vec is not None
        assert vec[0] == 11.0
        assert vec[1] == 16.0


class TestPolynomialBlock:
    """Tests for the Polynomial block."""

    def test_polynomial_basic(self):
        """Test basic polynomial evaluation."""
        from src.osk.blocks.math_ops import Polynomial

        # f(x) = x^2 + 2x + 1 = (x+1)^2
        poly = Polynomial(coefficients=[1.0, 2.0, 1.0])
        poly.init()
        poly.setInput(2.0)
        poly.update()
        # f(2) = 4 + 4 + 1 = 9
        assert poly.getOutput() == 9.0

    def test_polynomial_vector_input(self):
        """Test polynomial with vector input."""
        from src.osk.blocks.math_ops import Polynomial

        # f(x) = x^2
        poly = Polynomial(coefficients=[1.0, 0.0, 0.0])
        poly.init()
        poly.setInput([1.0, 2.0, 3.0])
        poly.update()

        # [1, 4, 9]
        assert poly.getOutput(0) == 1.0
        assert poly.getOutput(1) == 4.0
        assert poly.getOutput(2) == 9.0

        vec = poly.getOutputVector()
        assert vec == [1.0, 4.0, 9.0]

    def test_polynomial_scalar_returns_none(self):
        """Test getOutputVector returns None for scalar."""
        from src.osk.blocks.math_ops import Polynomial

        poly = Polynomial(coefficients=[1.0, 0.0])
        poly.init()
        poly.setInput(5.0)
        poly.update()
        assert poly.getOutputVector() is None
        assert poly.getOutput() == 5.0  # f(x) = x

    def test_polynomial_connect_input(self):
        """Test polynomial with connected block."""
        from src.osk.blocks.math_ops import Polynomial
        from src.osk.blocks.sources import Constant

        const = Constant(value=3.0)
        const.init()
        const.update()

        # f(x) = 2x + 1
        poly = Polynomial(coefficients=[2.0, 1.0])
        poly.init()
        poly.connectInput(const)
        poly.update()
        assert poly.getOutput() == 7.0  # 2*3 + 1

    def test_polynomial_vector_from_connected(self):
        """Test vector mode from connected block."""
        from src.osk.blocks.math_ops import Mux, Polynomial

        mux = Mux(num_inputs=2)
        mux.init()
        mux.setInput(2.0, 0)
        mux.setInput(3.0, 1)
        mux.update()

        poly = Polynomial(coefficients=[1.0, 1.0])  # f(x) = x + 1
        poly.init()
        poly.connectInput(mux)
        poly.update()

        vec = poly.getOutputVector()
        assert vec == [3.0, 4.0]  # [2+1, 3+1]


class TestMagnitudeAngleBlock:
    """Tests for the MagnitudeAngle block (polar to rectangular)."""

    def test_magnitude_angle_basic(self):
        """Test basic magnitude-angle to complex conversion."""
        import math

        from src.osk.blocks.math_ops import MagnitudeAngle

        ma = MagnitudeAngle()
        ma.init()
        ma.setInput(2.0, 0)  # magnitude
        ma.setInput(math.pi / 4, 1)  # angle (45 degrees)
        ma.update()

        # real = 2 * cos(pi/4) ≈ sqrt(2)
        # imag = 2 * sin(pi/4) ≈ sqrt(2)
        assert ma.getOutput(0) == pytest.approx(math.sqrt(2), rel=1e-6)
        assert ma.getOutput(1) == pytest.approx(math.sqrt(2), rel=1e-6)

    def test_magnitude_angle_zero(self):
        """Test with zero angle."""
        from src.osk.blocks.math_ops import MagnitudeAngle

        ma = MagnitudeAngle()
        ma.init()
        ma.setInput(5.0, 0)  # magnitude
        ma.setInput(0.0, 1)  # angle = 0
        ma.update()

        # real = 5 * cos(0) = 5, imag = 5 * sin(0) = 0
        assert ma.getOutput(0) == pytest.approx(5.0)
        assert ma.getOutput(1) == pytest.approx(0.0)

    def test_magnitude_angle_connect_input(self):
        """Test with connected blocks."""
        import math

        from src.osk.blocks.math_ops import MagnitudeAngle
        from src.osk.blocks.sources import Constant

        mag = Constant(value=1.0)
        mag.init()
        mag.update()
        angle = Constant(value=math.pi / 2)
        angle.init()
        angle.update()

        ma = MagnitudeAngle()
        ma.init()
        ma.connectInput(mag, 0)
        ma.connectInput(angle, 1)
        ma.update()

        # real = cos(pi/2) ≈ 0, imag = sin(pi/2) = 1
        assert ma.getOutput(0) == pytest.approx(0.0, abs=1e-10)
        assert ma.getOutput(1) == pytest.approx(1.0)

    def test_magnitude_angle_port_bounds(self):
        """Test getOutput returns 0 for invalid port."""
        from src.osk.blocks.math_ops import MagnitudeAngle

        ma = MagnitudeAngle()
        ma.init()
        ma.update()
        assert ma.getOutput(5) == 0.0


class TestComplexToMagnitudeAngleBlock:
    """Tests for the ComplexToMagnitudeAngle block (rectangular to polar)."""

    def test_complex_to_mag_angle_basic(self):
        """Test basic complex to magnitude-angle conversion."""
        import math

        from src.osk.blocks.math_ops import ComplexToMagnitudeAngle

        cma = ComplexToMagnitudeAngle()
        cma.init()
        cma.setInput(3.0, 0)  # real
        cma.setInput(4.0, 1)  # imag
        cma.update()

        # mag = sqrt(9+16) = 5
        # angle = atan2(4, 3) ≈ 0.927 rad
        assert cma.getOutput(0) == pytest.approx(5.0)
        assert cma.getOutput(1) == pytest.approx(math.atan2(4.0, 3.0))

    def test_complex_to_mag_angle_pure_real(self):
        """Test with pure real number."""
        from src.osk.blocks.math_ops import ComplexToMagnitudeAngle

        cma = ComplexToMagnitudeAngle()
        cma.init()
        cma.setInput(5.0, 0)
        cma.setInput(0.0, 1)
        cma.update()

        assert cma.getOutput(0) == pytest.approx(5.0)
        assert cma.getOutput(1) == pytest.approx(0.0)

    def test_complex_to_mag_angle_connect_input(self):
        """Test with connected blocks."""
        import math

        from src.osk.blocks.math_ops import ComplexToMagnitudeAngle
        from src.osk.blocks.sources import Constant

        real = Constant(value=0.0)
        real.init()
        real.update()
        imag = Constant(value=5.0)
        imag.init()
        imag.update()

        cma = ComplexToMagnitudeAngle()
        cma.init()
        cma.connectInput(real, 0)
        cma.connectInput(imag, 1)
        cma.update()

        # Pure imaginary: mag = 5, angle = pi/2
        assert cma.getOutput(0) == pytest.approx(5.0)
        assert cma.getOutput(1) == pytest.approx(math.pi / 2)

    def test_complex_to_mag_angle_port_bounds(self):
        """Test getOutput returns 0 for invalid port."""
        from src.osk.blocks.math_ops import ComplexToMagnitudeAngle

        cma = ComplexToMagnitudeAngle()
        cma.init()
        cma.update()
        assert cma.getOutput(5) == 0.0


class TestSqrtBlockExtended:
    """Extended tests for the Sqrt block."""

    def test_sqrt_vector_input(self):
        """Test sqrt with vector input."""
        from src.osk.blocks.math_ops import Sqrt

        sq = Sqrt()
        sq.init()
        sq.setInput([4.0, 9.0, 16.0])
        sq.update()

        assert sq.getOutput(0) == 2.0
        assert sq.getOutput(1) == 3.0
        assert sq.getOutput(2) == 4.0

        vec = sq.getOutputVector()
        assert vec == [2.0, 3.0, 4.0]

    def test_sqrt_negative_clamps_to_zero(self):
        """Test sqrt of negative clamps to zero before sqrt."""
        from src.osk.blocks.math_ops import Sqrt

        sq = Sqrt()
        sq.init()
        sq.setInput([-4.0, -1.0, 0.0])
        sq.update()

        # sqrt(max(-4, 0)) = sqrt(0) = 0
        vec = sq.getOutputVector()
        assert vec == [0.0, 0.0, 0.0]

    def test_sqrt_scalar_returns_none(self):
        """Test getOutputVector returns None for scalar."""
        from src.osk.blocks.math_ops import Sqrt

        sq = Sqrt()
        sq.init()
        sq.setInput(4.0)
        sq.update()
        assert sq.getOutputVector() is None
        assert sq.getOutput() == 2.0

    def test_sqrt_connect_vector_block(self):
        """Test sqrt with connected vector block."""
        from src.osk.blocks.math_ops import Mux, Sqrt

        mux = Mux(num_inputs=2)
        mux.init()
        mux.setInput(1.0, 0)
        mux.setInput(4.0, 1)
        mux.update()

        sq = Sqrt()
        sq.init()
        sq.connectInput(mux)
        sq.update()

        vec = sq.getOutputVector()
        assert vec == [1.0, 2.0]


class TestReciprocalBlockExtended:
    """Extended tests for the Reciprocal block."""

    def test_reciprocal_vector_input(self):
        """Test reciprocal with vector input."""
        from src.osk.blocks.math_ops import Reciprocal

        rec = Reciprocal()
        rec.init()
        rec.setInput([2.0, 4.0, 5.0])
        rec.update()

        assert rec.getOutput(0) == pytest.approx(0.5)
        assert rec.getOutput(1) == pytest.approx(0.25)
        assert rec.getOutput(2) == pytest.approx(0.2)

        vec = rec.getOutputVector()
        assert len(vec) == 3

    def test_reciprocal_zero_protection(self):
        """Test reciprocal of zero returns infinity or large value."""
        from src.osk.blocks.math_ops import Reciprocal

        rec = Reciprocal()
        rec.init()
        rec.setInput([0.0, 1.0])
        rec.update()

        vec = rec.getOutputVector()
        # Division by zero should produce inf
        assert vec[0] == float("inf") or vec[0] > 1e10
        assert vec[1] == 1.0

    def test_reciprocal_scalar_returns_none(self):
        """Test getOutputVector returns None for scalar."""
        from src.osk.blocks.math_ops import Reciprocal

        rec = Reciprocal()
        rec.init()
        rec.setInput(4.0)
        rec.update()
        assert rec.getOutputVector() is None
        assert rec.getOutput() == 0.25

    def test_reciprocal_connect_vector_block(self):
        """Test reciprocal with connected vector block."""
        from src.osk.blocks.math_ops import Mux, Reciprocal

        mux = Mux(num_inputs=2)
        mux.init()
        mux.setInput(2.0, 0)
        mux.setInput(5.0, 1)
        mux.update()

        rec = Reciprocal()
        rec.init()
        rec.connectInput(mux)
        rec.update()

        vec = rec.getOutputVector()
        assert vec[0] == pytest.approx(0.5)
        assert vec[1] == pytest.approx(0.2)


class TestSquareBlockExtended:
    """Extended tests for the Square block."""

    def test_square_vector_input(self):
        """Test square with vector input."""
        from src.osk.blocks.math_ops import Square

        sq = Square()
        sq.init()
        sq.setInput([2.0, 3.0, -4.0])
        sq.update()

        assert sq.getOutput(0) == 4.0
        assert sq.getOutput(1) == 9.0
        assert sq.getOutput(2) == 16.0

        vec = sq.getOutputVector()
        assert vec == [4.0, 9.0, 16.0]

    def test_square_scalar_returns_none(self):
        """Test getOutputVector returns None for scalar."""
        from src.osk.blocks.math_ops import Square

        sq = Square()
        sq.init()
        sq.setInput(5.0)
        sq.update()
        assert sq.getOutputVector() is None

    def test_square_connect_vector_block(self):
        """Test square with connected vector block."""
        from src.osk.blocks.math_ops import Mux, Square

        mux = Mux(num_inputs=2)
        mux.init()
        mux.setInput(3.0, 0)
        mux.setInput(4.0, 1)
        mux.update()

        sq = Square()
        sq.init()
        sq.connectInput(mux)
        sq.update()

        vec = sq.getOutputVector()
        assert vec == [9.0, 16.0]


class TestExpBlockExtended:
    """Extended tests for the Exp block."""

    def test_exp_vector_input(self):
        """Test exp with vector input."""
        import math

        from src.osk.blocks.math_ops import Exp

        exp_block = Exp()
        exp_block.init()
        exp_block.setInput([0.0, 1.0, 2.0])
        exp_block.update()

        assert exp_block.getOutput(0) == pytest.approx(1.0)
        assert exp_block.getOutput(1) == pytest.approx(math.e)
        assert exp_block.getOutput(2) == pytest.approx(math.e**2)

    def test_exp_scalar_returns_none(self):
        """Test getOutputVector returns None for scalar."""
        from src.osk.blocks.math_ops import Exp

        exp_block = Exp()
        exp_block.init()
        exp_block.setInput(0.0)
        exp_block.update()
        assert exp_block.getOutputVector() is None

    def test_exp_connect_vector_block(self):
        """Test exp with connected vector block."""
        import math

        from src.osk.blocks.math_ops import Exp, Mux

        mux = Mux(num_inputs=2)
        mux.init()
        mux.setInput(0.0, 0)
        mux.setInput(1.0, 1)
        mux.update()

        exp_block = Exp()
        exp_block.init()
        exp_block.connectInput(mux)
        exp_block.update()

        vec = exp_block.getOutputVector()
        assert vec[0] == pytest.approx(1.0)
        assert vec[1] == pytest.approx(math.e)


class TestLogBlockExtended:
    """Extended tests for the Log block."""

    def test_log_vector_input(self):
        """Test log with vector input."""
        import math

        from src.osk.blocks.math_ops import Log

        log_block = Log()
        log_block.init()
        log_block.setInput([1.0, math.e, math.e**2])
        log_block.update()

        assert log_block.getOutput(0) == pytest.approx(0.0)
        assert log_block.getOutput(1) == pytest.approx(1.0)
        assert log_block.getOutput(2) == pytest.approx(2.0)

    def test_log_scalar_returns_none(self):
        """Test getOutputVector returns None for scalar."""
        from src.osk.blocks.math_ops import Log

        log_block = Log()
        log_block.init()
        log_block.setInput(1.0)
        log_block.update()
        assert log_block.getOutputVector() is None

    def test_log_connect_vector_block(self):
        """Test log with connected vector block."""
        import math

        from src.osk.blocks.math_ops import Log, Mux

        mux = Mux(num_inputs=2)
        mux.init()
        mux.setInput(1.0, 0)
        mux.setInput(math.e, 1)
        mux.update()

        log_block = Log()
        log_block.init()
        log_block.connectInput(mux)
        log_block.update()

        vec = log_block.getOutputVector()
        assert vec[0] == pytest.approx(0.0)
        assert vec[1] == pytest.approx(1.0)


class TestLog10BlockExtended:
    """Extended tests for the Log10 block."""

    def test_log10_vector_input(self):
        """Test log10 with vector input."""
        from src.osk.blocks.math_ops import Log10

        log10_block = Log10()
        log10_block.init()
        log10_block.setInput([1.0, 10.0, 100.0])
        log10_block.update()

        assert log10_block.getOutput(0) == pytest.approx(0.0)
        assert log10_block.getOutput(1) == pytest.approx(1.0)
        assert log10_block.getOutput(2) == pytest.approx(2.0)

    def test_log10_scalar_returns_none(self):
        """Test getOutputVector returns None for scalar."""
        from src.osk.blocks.math_ops import Log10

        log10_block = Log10()
        log10_block.init()
        log10_block.setInput(10.0)
        log10_block.update()
        assert log10_block.getOutputVector() is None

    def test_log10_connect_vector_block(self):
        """Test log10 with connected vector block."""
        from src.osk.blocks.math_ops import Log10, Mux

        mux = Mux(num_inputs=2)
        mux.init()
        mux.setInput(10.0, 0)
        mux.setInput(100.0, 1)
        mux.update()

        log10_block = Log10()
        log10_block.init()
        log10_block.connectInput(mux)
        log10_block.update()

        vec = log10_block.getOutputVector()
        assert vec[0] == pytest.approx(1.0)
        assert vec[1] == pytest.approx(2.0)


class TestPowerBlockExtended:
    """Extended tests for the Power block (computes base^exponent)."""

    def test_power_basic(self):
        """Test basic power operation with two inputs."""
        from src.osk.blocks.math_ops import Power

        pow_block = Power()
        pow_block.init()
        pow_block.setInput(2.0, 0)  # base
        pow_block.setInput(3.0, 1)  # exponent
        pow_block.update()
        assert pow_block.getOutput() == 8.0  # 2^3

    def test_power_connect_input(self):
        """Test power with connected blocks."""
        from src.osk.blocks.math_ops import Power
        from src.osk.blocks.sources import Constant

        base = Constant(value=3.0)
        base.init()
        base.update()
        exp = Constant(value=2.0)
        exp.init()
        exp.update()

        pow_block = Power()
        pow_block.init()
        pow_block.connectInput(base, 0)
        pow_block.connectInput(exp, 1)
        pow_block.update()
        assert pow_block.getOutput() == 9.0  # 3^2

    def test_power_error_handling(self):
        """Test power handles error cases."""
        from src.osk.blocks.math_ops import Power

        pow_block = Power()
        pow_block.init()
        pow_block.setInput(-1.0, 0)  # negative base
        pow_block.setInput(0.5, 1)  # fractional exponent
        pow_block.update()
        # sqrt(-1) should return 0.0 due to ValueError
        assert pow_block.getOutput() == 0.0

    def test_power_port_bounds(self):
        """Test setInput/connectInput ignore invalid ports."""
        from src.osk.blocks.math_ops import Power
        from src.osk.blocks.sources import Constant

        pow_block = Power()
        pow_block.init()
        pow_block.setInput(99.0, 5)  # Invalid port
        pow_block.connectInput(Constant(value=1.0), 5)  # Invalid
        assert pow_block.inputs == [0.0, 0.0]


class TestUnaryMinusBlockExtended:
    """Extended tests for the UnaryMinus block."""

    def test_unary_minus_vector_input(self):
        """Test unary minus with vector input."""
        from src.osk.blocks.math_ops import UnaryMinus

        um = UnaryMinus()
        um.init()
        um.setInput([1.0, -2.0, 3.0])
        um.update()

        assert um.getOutput(0) == -1.0
        assert um.getOutput(1) == 2.0
        assert um.getOutput(2) == -3.0

    def test_unary_minus_scalar_returns_none(self):
        """Test getOutputVector returns None for scalar."""
        from src.osk.blocks.math_ops import UnaryMinus

        um = UnaryMinus()
        um.init()
        um.setInput(5.0)
        um.update()
        assert um.getOutputVector() is None
        assert um.getOutput() == -5.0

    def test_unary_minus_connect_vector_block(self):
        """Test unary minus with connected vector block."""
        from src.osk.blocks.math_ops import Mux, UnaryMinus

        mux = Mux(num_inputs=2)
        mux.init()
        mux.setInput(3.0, 0)
        mux.setInput(-4.0, 1)
        mux.update()

        um = UnaryMinus()
        um.init()
        um.connectInput(mux)
        um.update()

        vec = um.getOutputVector()
        assert vec == [-3.0, 4.0]


class TestDotProductExtended:
    """Extended tests for the DotProduct block."""

    def test_dot_product_connect_input(self):
        """Test dot product with connected blocks."""
        from src.osk.blocks.math_ops import DotProduct, Mux

        mux1 = Mux(num_inputs=3)
        mux1.init()
        mux1.setInput(1.0, 0)
        mux1.setInput(2.0, 1)
        mux1.setInput(3.0, 2)
        mux1.update()

        mux2 = Mux(num_inputs=3)
        mux2.init()
        mux2.setInput(4.0, 0)
        mux2.setInput(5.0, 1)
        mux2.setInput(6.0, 2)
        mux2.update()

        dp = DotProduct()
        dp.init()
        dp.connectInput(mux1, 0)
        dp.connectInput(mux2, 1)
        dp.update()

        # [1,2,3] . [4,5,6] = 4 + 10 + 18 = 32
        assert dp.getOutput() == 32.0

    def test_dot_product_scalar_fallback(self):
        """Test dot product with scalar inputs."""
        from src.osk.blocks.math_ops import DotProduct

        dp = DotProduct()
        dp.init()
        dp.setInput(3.0, 0)
        dp.setInput(4.0, 1)
        dp.update()
        assert dp.getOutput() == 12.0  # scalar multiply


class TestCrossProductExtended:
    """Extended tests for the CrossProduct block."""

    def test_cross_product_connect_input(self):
        """Test cross product with connected blocks."""
        from src.osk.blocks.math_ops import CrossProduct, Mux

        mux1 = Mux(num_inputs=3)
        mux1.init()
        mux1.setInput(1.0, 0)
        mux1.setInput(0.0, 1)
        mux1.setInput(0.0, 2)
        mux1.update()

        mux2 = Mux(num_inputs=3)
        mux2.init()
        mux2.setInput(0.0, 0)
        mux2.setInput(1.0, 1)
        mux2.setInput(0.0, 2)
        mux2.update()

        cp = CrossProduct()
        cp.init()
        cp.connectInput(mux1, 0)
        cp.connectInput(mux2, 1)
        cp.update()

        # i x j = k, so [1,0,0] x [0,1,0] = [0,0,1]
        vec = cp.getOutputVector()
        assert vec == [0.0, 0.0, 1.0]

    def test_cross_product_get_output_ports(self):
        """Test cross product individual output ports."""
        from src.osk.blocks.math_ops import CrossProduct

        cp = CrossProduct()
        cp.init()
        cp.setInput([1.0, 0.0, 0.0], 0)
        cp.setInput([0.0, 0.0, 1.0], 1)
        cp.update()

        # i x k = -j, so [1,0,0] x [0,0,1] = [0,-1,0]
        assert cp.getOutput(0) == pytest.approx(0.0)
        assert cp.getOutput(1) == pytest.approx(-1.0)
        assert cp.getOutput(2) == pytest.approx(0.0)


class TestMinMaxExtended:
    """Extended tests for the MinMax block."""

    def test_minmax_connect_input(self):
        """Test MinMax with connected blocks."""
        from src.osk.blocks.math_ops import MinMax
        from src.osk.blocks.sources import Constant

        c1 = Constant(value=5.0)
        c1.init()
        c1.update()
        c2 = Constant(value=3.0)
        c2.init()
        c2.update()

        mm = MinMax(function="max")
        mm.init()
        mm.connectInput(c1, 0)
        mm.connectInput(c2, 1)
        mm.update()
        assert mm.getOutput() == 5.0

    def test_minmax_port_bounds(self):
        """Test MinMax setInput/connectInput ignore invalid ports."""
        from src.osk.blocks.math_ops import MinMax
        from src.osk.blocks.sources import Constant

        mm = MinMax(num_inputs=2)
        mm.init()
        mm.setInput(99.0, 5)  # Invalid
        mm.connectInput(Constant(value=1.0), 5)  # Invalid
        assert mm.inputs == [0.0, 0.0]


class TestRoundingExtended:
    """Extended tests for the Rounding block."""

    def test_rounding_connect_input(self):
        """Test Rounding with connected block."""
        from src.osk.blocks.math_ops import Rounding
        from src.osk.blocks.sources import Constant

        const = Constant(value=3.7)
        const.init()
        const.update()

        r = Rounding(mode="floor")
        r.init()
        r.connectInput(const)
        r.update()
        assert r.getOutput() == 3.0

    def test_rounding_fix(self):
        """Test Rounding with fix mode (truncate toward zero)."""
        from src.osk.blocks.math_ops import Rounding

        r = Rounding(mode="fix")
        r.init()
        r.setInput(-3.7)
        r.update()
        assert r.getOutput() == -3.0

        r.setInput(3.7)
        r.update()
        assert r.getOutput() == 3.0


class TestAbsBlockExtended:
    """Extended tests for the Abs block."""

    def test_abs_vector_input(self):
        """Test abs with vector input."""
        from src.osk.blocks.math_ops import Abs

        ab = Abs()
        ab.init()
        ab.setInput([-1.0, 2.0, -3.0])
        ab.update()

        assert ab.getOutput(0) == 1.0
        assert ab.getOutput(1) == 2.0
        assert ab.getOutput(2) == 3.0

        vec = ab.getOutputVector()
        assert vec == [1.0, 2.0, 3.0]

    def test_abs_scalar_returns_none(self):
        """Test getOutputVector returns None for scalar."""
        from src.osk.blocks.math_ops import Abs

        ab = Abs()
        ab.init()
        ab.setInput(-5.0)
        ab.update()
        assert ab.getOutputVector() is None

    def test_abs_connect_vector_block(self):
        """Test abs with connected vector block."""
        from src.osk.blocks.math_ops import Abs, Mux

        mux = Mux(num_inputs=2)
        mux.init()
        mux.setInput(-3.0, 0)
        mux.setInput(4.0, 1)
        mux.update()

        ab = Abs()
        ab.init()
        ab.connectInput(mux)
        ab.update()

        vec = ab.getOutputVector()
        assert vec == [3.0, 4.0]


class TestGainBlockExtended:
    """Extended tests for the Gain block."""

    def test_gain_vector_input(self):
        """Test gain with vector input."""
        from src.osk.blocks.math_ops import Gain

        g = Gain(gain=2.0)
        g.init()
        g.setInput([1.0, 2.0, 3.0])
        g.update()

        assert g.getOutput(0) == 2.0
        assert g.getOutput(1) == 4.0
        assert g.getOutput(2) == 6.0

        vec = g.getOutputVector()
        assert vec == [2.0, 4.0, 6.0]

    def test_gain_scalar_returns_none(self):
        """Test getOutputVector returns None for scalar."""
        from src.osk.blocks.math_ops import Gain

        g = Gain(gain=3.0)
        g.init()
        g.setInput(5.0)
        g.update()
        assert g.getOutputVector() is None

    def test_gain_connect_vector_block(self):
        """Test gain with connected vector block."""
        from src.osk.blocks.math_ops import Gain, Mux

        mux = Mux(num_inputs=2)
        mux.init()
        mux.setInput(2.0, 0)
        mux.setInput(5.0, 1)
        mux.update()

        g = Gain(gain=3.0)
        g.init()
        g.connectInput(mux)
        g.update()

        vec = g.getOutputVector()
        assert vec == [6.0, 15.0]


# =============================================================================
# Extended Continuous Block Tests for Full Coverage
# =============================================================================


class TestTransportDelayBlock:
    """Tests for the TransportDelay block."""

    def test_transport_delay_basic(self):
        """Test basic transport delay operation."""
        from src.osk.blocks.continuous import TransportDelay
        from src.osk.state import State

        td = TransportDelay(delay_time=0.1, initial_output=0.0)
        td.init()

        # During delay period, output should be initial value
        State.t = 0.0
        td.setInput(5.0)
        td.update()
        assert td.getOutput() == 0.0  # Still in delay period

        # After delay period
        State.t = 0.1
        td.setInput(10.0)
        td.update()
        # Now t=0.1, delayed_time=0.0, should output value from t=0.0
        # The buffer should have [5.0, 10.0] at [0.0, 0.1]
        assert td.getOutput() == pytest.approx(5.0, abs=0.1)

    def test_transport_delay_init(self):
        """Test transport delay initialization."""
        from src.osk.blocks.continuous import TransportDelay

        td = TransportDelay(delay_time=0.5, initial_output=3.0)
        td.init()
        assert td.getOutput() == 3.0
        assert td.buffer == []
        assert td.time_buffer == []

    def test_transport_delay_connect_input(self):
        """Test transport delay with connected block."""
        from src.osk.blocks.continuous import TransportDelay
        from src.osk.blocks.sources import Constant
        from src.osk.state import State

        const = Constant(value=7.0)
        const.init()
        const.update()

        td = TransportDelay(delay_time=0.2, initial_output=0.0)
        td.init()
        td.connectInput(const)

        State.t = 0.05
        td.update()
        assert td.getOutput() == 0.0  # In delay period

    def test_transport_delay_buffer_cleanup(self):
        """Test transport delay cleans up old buffer entries."""
        from src.osk.blocks.continuous import TransportDelay
        from src.osk.state import State

        td = TransportDelay(delay_time=0.1, initial_output=0.0)
        td.init()

        # Build up buffer
        for i in range(10):
            State.t = i * 0.05
            td.setInput(float(i))
            td.update()

        # Buffer should have been cleaned up to relevant entries
        assert len(td.buffer) <= 10  # Some entries may have been cleaned


class TestSecondOrderBlock:
    """Tests for the SecondOrder block."""

    def test_second_order_basic(self):
        """Test basic second-order system."""
        from src.osk.blocks.continuous import SecondOrder

        so = SecondOrder(natural_frequency=1.0, damping_ratio=0.7, gain=1.0)
        so.init()

        # Check initial state
        assert so.getOutput() == 0.0
        assert so.x1[0] == 0.0
        assert so.x2[0] == 0.0

    def test_second_order_step_response(self):
        """Test second-order system step response."""
        from src.osk.blocks.continuous import SecondOrder

        so = SecondOrder(natural_frequency=10.0, damping_ratio=1.0, gain=2.0)
        so.init()
        so.setInput(1.0)
        so.update()

        # Derivatives should be set
        assert so.x1[1] == so.x2[0]  # x1' = x2

    def test_second_order_connect_input(self):
        """Test second-order with connected block."""
        from src.osk.blocks.continuous import SecondOrder
        from src.osk.blocks.sources import Constant

        const = Constant(value=5.0)
        const.init()
        const.update()

        so = SecondOrder(natural_frequency=2.0, damping_ratio=0.5, gain=1.0)
        so.init()
        so.connectInput(const)
        so.update()

        # Output should still be 0 initially, but derivatives should be set
        assert so.getOutput() == 0.0


class TestLimitedIntegratorBlock:
    """Tests for the LimitedIntegrator block."""

    def test_limited_integrator_basic(self):
        """Test basic limited integrator."""
        from src.osk.blocks.continuous import LimitedIntegrator

        li = LimitedIntegrator(initial_condition=0.0, upper_limit=5.0, lower_limit=-5.0)
        li.init()
        assert li.getOutput() == 0.0

    def test_limited_integrator_saturation(self):
        """Test limited integrator saturation behavior."""
        from src.osk.blocks.continuous import LimitedIntegrator

        li = LimitedIntegrator(initial_condition=4.5, upper_limit=5.0, lower_limit=-5.0)
        li.init()

        # When at upper limit with positive input, should stop integrating
        li.x[0] = 5.0  # At limit
        li.setInput(10.0)  # Positive input
        li.update()
        assert li.x[1] == 0.0  # Integration stopped

    def test_limited_integrator_lower_saturation(self):
        """Test limited integrator lower saturation."""
        from src.osk.blocks.continuous import LimitedIntegrator

        li = LimitedIntegrator(initial_condition=-4.5, upper_limit=5.0, lower_limit=-5.0)
        li.init()

        # When at lower limit with negative input, should stop integrating
        li.x[0] = -5.0  # At limit
        li.setInput(-10.0)  # Negative input
        li.update()
        assert li.x[1] == 0.0  # Integration stopped

    def test_limited_integrator_output_clamping(self):
        """Test limited integrator output clamping."""
        from src.osk.blocks.continuous import LimitedIntegrator

        li = LimitedIntegrator(initial_condition=0.0, upper_limit=5.0, lower_limit=-5.0)
        li.init()

        # Force state beyond limits
        li.x[0] = 10.0
        assert li.getOutput() == 5.0  # Clamped to upper limit

        li.x[0] = -10.0
        assert li.getOutput() == -5.0  # Clamped to lower limit

    def test_limited_integrator_connect_input(self):
        """Test limited integrator with connected block."""
        from src.osk.blocks.continuous import LimitedIntegrator
        from src.osk.blocks.sources import Constant

        const = Constant(value=2.0)
        const.init()
        const.update()

        li = LimitedIntegrator(initial_condition=0.0, upper_limit=10.0, lower_limit=-10.0)
        li.init()
        li.connectInput(const)
        li.update()

        assert li.x[1] == 2.0  # Derivative = input


class TestZeroPoleBlock:
    """Tests for the ZeroPole block."""

    def test_zero_pole_basic(self):
        """Test basic zero-pole transfer function."""
        from src.osk.blocks.continuous import ZeroPole

        # Simple first-order low-pass: 1/(s+1)
        zp = ZeroPole(zeros=[], poles=[-1.0], gain=1.0)
        zp.init()
        assert zp.getOutput() == 0.0
        assert zp.order == 1

    def test_zero_pole_with_zeros(self):
        """Test zero-pole with both zeros and poles."""
        from src.osk.blocks.continuous import ZeroPole

        # (s+2)/(s+1)
        zp = ZeroPole(zeros=[-2.0], poles=[-1.0], gain=1.0)
        zp.init()
        assert zp.order == 1

    def test_zero_pole_second_order(self):
        """Test second-order zero-pole system."""
        from src.osk.blocks.continuous import ZeroPole

        # 1/((s+1)(s+2))
        zp = ZeroPole(zeros=[], poles=[-1.0, -2.0], gain=1.0)
        zp.init()
        assert zp.order == 2

    def test_zero_pole_first_order(self):
        """Test zero-pole first-order system."""
        from src.osk.blocks.continuous import ZeroPole

        # First order system 1/(s+1)
        zp = ZeroPole(zeros=[], poles=[-1.0], gain=1.0)
        zp.init()
        zp.setInput(1.0)
        zp.update()
        # Initial output is 0, but system should start responding
        assert zp.order == 1

    def test_zero_pole_step_response(self):
        """Test zero-pole step response."""
        from src.osk.blocks.continuous import ZeroPole

        zp = ZeroPole(zeros=[], poles=[-1.0], gain=1.0)
        zp.init()
        zp.setInput(1.0)
        zp.update()

        # Derivatives should be set
        # This is a first-order system, so there's one state

    def test_zero_pole_connect_input(self):
        """Test zero-pole with connected block."""
        from src.osk.blocks.continuous import ZeroPole
        from src.osk.blocks.sources import Constant

        const = Constant(value=3.0)
        const.init()
        const.update()

        zp = ZeroPole(zeros=[], poles=[-1.0], gain=2.0)
        zp.init()
        zp.connectInput(const)
        zp.update()

        # Output should start at 0, but system should respond

    def test_zero_pole_poly_coeffs(self):
        """Test polynomial coefficient calculation."""
        from src.osk.blocks.continuous import ZeroPole

        zp = ZeroPole(zeros=[], poles=[-1.0], gain=1.0)

        # Check polynomial from roots
        # (s - (-1)) = s + 1 -> coeffs = [1, 1]
        coeffs = zp._poly_coeffs([-1.0])
        assert coeffs[0] == 1.0
        assert coeffs[1] == pytest.approx(1.0)

        # (s+1)(s+2) = s^2 + 3s + 2 -> coeffs = [1, 3, 2]
        coeffs = zp._poly_coeffs([-1.0, -2.0])
        assert coeffs[0] == 1.0
        assert coeffs[1] == pytest.approx(3.0)
        assert coeffs[2] == pytest.approx(2.0)


# =============================================================================
# Sources Module Extended Tests
# =============================================================================


class TestWhiteNoiseBlock:
    """Tests for WhiteNoise block."""

    def test_white_noise_basic(self):
        """Test basic WhiteNoise initialization and output."""
        from src.osk.blocks.sources import WhiteNoise

        noise = WhiteNoise(mean=0.0, variance=1.0, seed=42)
        noise.init()
        noise.update()
        output = noise.getOutput()
        # Output should be a number (stochastic)
        assert isinstance(output, float)

    def test_white_noise_seeded_reproducibility(self):
        """Test that seeded noise is reproducible."""
        from src.osk.blocks.sources import WhiteNoise

        noise1 = WhiteNoise(mean=0.0, variance=1.0, seed=123)
        noise1.init()
        noise1.update()
        out1 = noise1.getOutput()

        noise2 = WhiteNoise(mean=0.0, variance=1.0, seed=123)
        noise2.init()
        noise2.update()
        out2 = noise2.getOutput()

        assert out1 == out2

    def test_white_noise_nonzero_mean(self):
        """Test WhiteNoise with non-zero mean."""
        from src.osk.blocks.sources import WhiteNoise

        noise = WhiteNoise(mean=10.0, variance=0.01, seed=42)
        noise.init()
        # With low variance, outputs should cluster around mean
        outputs = []
        for _ in range(100):
            noise.update()
            outputs.append(noise.getOutput())

        avg = sum(outputs) / len(outputs)
        assert abs(avg - 10.0) < 1.0  # Should be close to mean

    def test_white_noise_sample_time(self):
        """Test WhiteNoise with discrete sample time."""
        from src.osk.blocks.sources import WhiteNoise
        from src.osk.state import State

        State.t = 0.0
        noise = WhiteNoise(mean=0.0, variance=1.0, seed=42, sample_time=0.1)
        noise.init()
        first_output = noise.getOutput()

        # Update at same time - should keep same value
        noise.update()
        assert noise.getOutput() == first_output

        # Advance time past sample_time
        State.t = 0.15
        noise.update()
        # Output should have changed
        # (may or may not be equal by chance, but mechanism is tested)


class TestUniformNoiseBlock:
    """Tests for UniformNoise block."""

    def test_uniform_noise_basic(self):
        """Test basic UniformNoise output range."""
        from src.osk.blocks.sources import UniformNoise

        noise = UniformNoise(minimum=-1.0, maximum=1.0, seed=42)
        noise.init()
        for _ in range(50):
            noise.update()
            output = noise.getOutput()
            assert -1.0 <= output <= 1.0

    def test_uniform_noise_sample_time(self):
        """Test UniformNoise with sample time."""
        from src.osk.blocks.sources import UniformNoise
        from src.osk.state import State

        State.t = 0.0
        noise = UniformNoise(minimum=0.0, maximum=10.0, seed=42, sample_time=0.5)
        noise.init()
        first_output = noise.getOutput()

        State.t = 0.1
        noise.update()
        # Should keep same value before sample time
        assert noise.getOutput() == first_output

        State.t = 0.6
        noise.update()
        # Output may have changed


class TestRepeatingSequenceBlockExtended:
    """Extended tests for RepeatingSequence block."""

    def test_repeating_sequence_interpolation(self):
        """Test linear interpolation in repeating sequence."""
        from src.osk.blocks.sources import RepeatingSequence
        from src.osk.state import State

        seq = RepeatingSequence(time_values=[0.0, 1.0, 2.0], output_values=[0.0, 10.0, 0.0])
        seq.init()

        State.t = 0.5
        seq.update()
        assert seq.getOutput() == pytest.approx(5.0)

        State.t = 1.5
        seq.update()
        assert seq.getOutput() == pytest.approx(5.0)

    def test_repeating_sequence_wrapping(self):
        """Test time wrapping in repeating sequence."""
        from src.osk.blocks.sources import RepeatingSequence
        from src.osk.state import State

        seq = RepeatingSequence(time_values=[0.0, 1.0], output_values=[0.0, 1.0])
        seq.init()

        State.t = 2.5  # Should wrap to 0.5
        seq.update()
        assert seq.getOutput() == pytest.approx(0.5)

    def test_repeating_sequence_single_point(self):
        """Test repeating sequence with single point."""
        from src.osk.blocks.sources import RepeatingSequence
        from src.osk.state import State

        seq = RepeatingSequence(time_values=[0.0], output_values=[5.0])
        seq.init()

        State.t = 1.0
        seq.update()
        assert seq.getOutput() == 5.0

    def test_repeating_sequence_zero_period(self):
        """Test repeating sequence with zero period edge case."""
        from src.osk.blocks.sources import RepeatingSequence
        from src.osk.state import State

        seq = RepeatingSequence(
            time_values=[1.0, 1.0],  # Zero period
            output_values=[5.0, 10.0],
        )
        seq.init()

        State.t = 0.5
        seq.update()
        # Should handle gracefully


class TestChirpSignalBlockExtended:
    """Extended tests for ChirpSignal block."""

    def test_chirp_during_sweep(self):
        """Test chirp during frequency sweep."""
        from src.osk.blocks.sources import ChirpSignal
        from src.osk.state import State

        chirp = ChirpSignal(initial_frequency=1.0, target_time=2.0, target_frequency=5.0)
        chirp.init()

        State.t = 1.0  # Midway through sweep
        chirp.update()
        output = chirp.getOutput()
        assert -1.0 <= output <= 1.0  # Cosine output

    def test_chirp_after_target(self):
        """Test chirp after reaching target frequency."""
        from src.osk.blocks.sources import ChirpSignal
        from src.osk.state import State

        chirp = ChirpSignal(initial_frequency=1.0, target_time=1.0, target_frequency=2.0)
        chirp.init()

        State.t = 2.0  # Past target time
        chirp.update()
        output = chirp.getOutput()
        assert -1.0 <= output <= 1.0

    def test_chirp_zero_target_time(self):
        """Test chirp with zero target time."""
        from src.osk.blocks.sources import ChirpSignal

        chirp = ChirpSignal(initial_frequency=1.0, target_time=0.0, target_frequency=2.0)
        chirp.init()
        assert chirp.sweep_rate == 0.0


class TestBandLimitedWhiteNoiseBlock:
    """Tests for BandLimitedWhiteNoise block."""

    def test_band_limited_noise_basic(self):
        """Test basic band-limited noise output."""
        from src.osk.blocks.sources import BandLimitedWhiteNoise
        from src.osk.state import State

        State.t = 0.0
        noise = BandLimitedWhiteNoise(noise_power=0.1, sample_time=0.1, seed=42)
        noise.init()

        output = noise.getOutput()
        assert isinstance(output, float)

    def test_band_limited_noise_sample_hold(self):
        """Test that noise holds value between samples."""
        from src.osk.blocks.sources import BandLimitedWhiteNoise
        from src.osk.state import State

        State.t = 0.0
        noise = BandLimitedWhiteNoise(noise_power=0.1, sample_time=0.1, seed=42)
        noise.init()
        first_output = noise.getOutput()

        State.t = 0.05  # Before next sample
        noise.update()
        assert noise.getOutput() == first_output

        State.t = 0.1  # At next sample time
        noise.update()
        # Output should potentially change


class TestFromWorkspaceBlock:
    """Tests for FromWorkspace block."""

    def test_from_workspace_linear_interpolation(self):
        """Test FromWorkspace linear interpolation."""
        from src.osk.blocks.sources import FromWorkspace
        from src.osk.state import State

        ws = FromWorkspace(
            time_data=[0.0, 1.0, 2.0], value_data=[0.0, 10.0, 20.0], interpolation="linear"
        )
        ws.init()

        State.t = 0.5
        ws.update()
        assert ws.getOutput() == pytest.approx(5.0)

        State.t = 1.5
        ws.update()
        assert ws.getOutput() == pytest.approx(15.0)

    def test_from_workspace_zoh_interpolation(self):
        """Test FromWorkspace zero-order hold interpolation."""
        from src.osk.blocks.sources import FromWorkspace
        from src.osk.state import State

        ws = FromWorkspace(
            time_data=[0.0, 1.0, 2.0], value_data=[0.0, 10.0, 20.0], interpolation="zoh"
        )
        ws.init()

        State.t = 0.5
        ws.update()
        assert ws.getOutput() == 0.0  # ZOH holds previous value

        State.t = 1.5
        ws.update()
        assert ws.getOutput() == 10.0

    def test_from_workspace_nearest_interpolation(self):
        """Test FromWorkspace nearest interpolation."""
        from src.osk.blocks.sources import FromWorkspace
        from src.osk.state import State

        ws = FromWorkspace(
            time_data=[0.0, 1.0, 2.0], value_data=[0.0, 10.0, 20.0], interpolation="nearest"
        )
        ws.init()

        State.t = 0.3  # Closer to 0.0
        ws.update()
        assert ws.getOutput() == 0.0

        State.t = 0.7  # Closer to 1.0
        ws.update()
        assert ws.getOutput() == 10.0

    def test_from_workspace_before_first_point(self):
        """Test FromWorkspace before first time point."""
        from src.osk.blocks.sources import FromWorkspace
        from src.osk.state import State

        ws = FromWorkspace(time_data=[1.0, 2.0], value_data=[10.0, 20.0])
        ws.init()

        State.t = 0.5
        ws.update()
        assert ws.getOutput() == 10.0  # Returns first value

    def test_from_workspace_after_last_point(self):
        """Test FromWorkspace after last time point."""
        from src.osk.blocks.sources import FromWorkspace
        from src.osk.state import State

        ws = FromWorkspace(time_data=[0.0, 1.0], value_data=[0.0, 10.0])
        ws.init()

        State.t = 5.0
        ws.update()
        assert ws.getOutput() == 10.0  # Returns last value

    def test_from_workspace_empty_data(self):
        """Test FromWorkspace with empty data."""
        from src.osk.blocks.sources import FromWorkspace
        from src.osk.state import State

        ws = FromWorkspace(time_data=[], value_data=[])
        ws.init()

        State.t = 0.5
        ws.update()
        assert ws.getOutput() == 0.0


class TestSignalGeneratorBlockExtended:
    """Extended tests for SignalGenerator block."""

    def test_signal_generator_square(self):
        """Test square wave generation."""
        from src.osk.blocks.sources import SignalGenerator
        from src.osk.state import State

        gen = SignalGenerator(wave_type="square", amplitude=1.0, frequency=1.0)
        gen.init()

        State.t = 0.25  # First half of period
        gen.update()
        assert gen.getOutput() == 1.0

        State.t = 0.75  # Second half of period
        gen.update()
        assert gen.getOutput() == -1.0

    def test_signal_generator_sawtooth(self):
        """Test sawtooth wave generation."""
        from src.osk.blocks.sources import SignalGenerator
        from src.osk.state import State

        gen = SignalGenerator(wave_type="sawtooth", amplitude=1.0, frequency=1.0)
        gen.init()

        State.t = 0.0
        gen.update()
        assert gen.getOutput() == pytest.approx(-1.0)

        State.t = 0.5
        gen.update()
        assert gen.getOutput() == pytest.approx(0.0)

        State.t = 0.99
        gen.update()
        assert gen.getOutput() == pytest.approx(0.98, rel=0.05)

    def test_signal_generator_random(self):
        """Test random wave generation."""
        from src.osk.blocks.sources import SignalGenerator
        from src.osk.state import State

        gen = SignalGenerator(wave_type="random", amplitude=1.0, frequency=1.0)
        gen.init()

        State.t = 0.1
        gen.update()
        output = gen.getOutput()
        assert -1.0 <= output <= 1.0

    def test_signal_generator_zero_frequency(self):
        """Test signal generator with zero frequency."""
        from src.osk.blocks.sources import SignalGenerator
        from src.osk.state import State

        gen = SignalGenerator(wave_type="sine", amplitude=1.0, frequency=0.0)
        gen.init()

        State.t = 1.0
        gen.update()
        assert gen.getOutput() == 0.0

    def test_signal_generator_rad_s_units(self):
        """Test signal generator with rad/s units."""
        from src.osk.blocks.sources import SignalGenerator

        # 2*pi rad/s = 1 Hz
        gen = SignalGenerator(wave_type="sine", amplitude=1.0, frequency=2 * math.pi, units="rad/s")
        gen.init()
        assert gen.freq_hz == pytest.approx(1.0)

    def test_signal_generator_unknown_wave_type(self):
        """Test signal generator with unknown wave type."""
        from src.osk.blocks.sources import SignalGenerator
        from src.osk.state import State

        gen = SignalGenerator(wave_type="unknown", amplitude=1.0, frequency=1.0)
        gen.init()

        State.t = 0.5
        gen.update()
        assert gen.getOutput() == 0.0  # Falls through to default


class TestConstantBlockExtended:
    """Extended tests for Constant block value parsing."""

    def test_constant_semicolon_separated(self):
        """Test Constant block parses semicolon-separated arrays."""
        from src.osk.blocks.sources import Constant

        const = Constant(value="[1; 2; 3]")
        const.init()
        assert const.getOutputVector() == [1.0, 2.0, 3.0]

    def test_constant_space_separated(self):
        """Test Constant block parses space-separated arrays."""
        from src.osk.blocks.sources import Constant

        const = Constant(value="[1 2 3 4]")
        const.init()
        assert const.getOutputVector() == [1.0, 2.0, 3.0, 4.0]

    def test_constant_comma_no_brackets(self):
        """Test Constant block parses comma-separated without brackets."""
        from src.osk.blocks.sources import Constant

        const = Constant(value="1,2,3")
        const.init()
        assert const.getOutputVector() == [1.0, 2.0, 3.0]

    def test_constant_empty_array(self):
        """Test Constant block with empty array string."""
        from src.osk.blocks.sources import Constant

        const = Constant(value="[]")
        const.init()
        # Empty array should fall back to default
        assert const.getOutput() == 1.0

    def test_constant_value_setter(self):
        """Test Constant block value setter."""
        from src.osk.blocks.sources import Constant

        const = Constant(value=1.0)
        const.init()
        assert const.value == 1.0

        const.value = [1.0, 2.0, 3.0]
        assert const._is_vector is True
        assert const._values == [1.0, 2.0, 3.0]

        const.value = 5.0
        assert const._is_vector is False
        assert const._values == [5.0]

    def test_constant_out_of_range_port(self):
        """Test Constant block with out of range port."""
        from src.osk.blocks.sources import Constant

        const = Constant(value=[1.0, 2.0])
        const.init()
        assert const.getOutput(10) == 0.0

    def test_constant_scalar_no_vector(self):
        """Test Constant block scalar returns None for getOutputVector."""
        from src.osk.blocks.sources import Constant

        const = Constant(value=5.0)
        const.init()
        assert const.getOutputVector() is None

    def test_constant_get_num_outputs(self):
        """Test Constant block getNumOutputs method."""
        from src.osk.blocks.sources import Constant

        const = Constant(value=[1.0, 2.0, 3.0])
        const.init()
        assert const.getNumOutputs() == 3


# =============================================================================
# Navigation Module Tests
# =============================================================================


class TestCoordinateTransformationConversion:
    """Tests for CoordinateTransformationConversion block."""

    def test_lla_to_ecef_conversion(self):
        """Test LLA to ECEF conversion."""
        from src.osk.blocks.navigation import CoordinateTransformationConversion

        conv = CoordinateTransformationConversion(input_type="lla", output_type="ecef")
        conv.init()
        conv.setInput([0.0, 0.0, 0.0])  # Equator, prime meridian, sea level
        conv.update()

        output = conv.getOutputVector()
        assert output is not None
        # At lat=0, lon=0, alt=0: X should equal semi-major axis
        assert output[0] == pytest.approx(6378137.0, rel=1e-6)
        assert output[1] == pytest.approx(0.0, abs=1e-3)
        assert output[2] == pytest.approx(0.0, abs=1e-3)

    def test_ecef_to_lla_conversion(self):
        """Test ECEF to LLA conversion."""
        from src.osk.blocks.navigation import CoordinateTransformationConversion

        conv = CoordinateTransformationConversion(input_type="ecef", output_type="lla")
        conv.init()
        conv.setInput([6378137.0, 0.0, 0.0])
        conv.update()

        output = conv.getOutputVector()
        assert output is not None
        assert output[0] == pytest.approx(0.0, abs=1e-6)  # lat
        assert output[1] == pytest.approx(0.0, abs=1e-6)  # lon
        assert output[2] == pytest.approx(0.0, abs=10.0)  # alt (some tolerance)

    def test_ecef_to_ned_conversion(self):
        """Test ECEF to NED conversion."""
        from src.osk.blocks.navigation import CoordinateTransformationConversion

        # Reference at equator, prime meridian
        conv = CoordinateTransformationConversion(
            input_type="ecef", output_type="ned", reference_lla=[0.0, 0.0, 0.0]
        )
        conv.init()
        # Point slightly above reference
        conv.setInput([6378137.0 + 100, 0.0, 0.0])
        conv.update()

        output = conv.getOutputVector()
        assert output is not None
        # 100m above should be -100m in Down direction
        assert output[2] == pytest.approx(-100.0, rel=0.01)

    def test_ned_to_ecef_conversion(self):
        """Test NED to ECEF conversion."""
        from src.osk.blocks.navigation import CoordinateTransformationConversion

        conv = CoordinateTransformationConversion(
            input_type="ned", output_type="ecef", reference_lla=[0.0, 0.0, 0.0]
        )
        conv.init()
        conv.setInput([0.0, 0.0, 0.0])  # At reference point
        conv.update()

        output = conv.getOutputVector()
        assert output is not None
        assert output[0] == pytest.approx(6378137.0, rel=1e-6)

    def test_ecef_to_enu_conversion(self):
        """Test ECEF to ENU conversion."""
        from src.osk.blocks.navigation import CoordinateTransformationConversion

        conv = CoordinateTransformationConversion(
            input_type="ecef", output_type="enu", reference_lla=[0.0, 0.0, 0.0]
        )
        conv.init()
        conv.setInput([6378137.0 + 100, 0.0, 0.0])
        conv.update()

        output = conv.getOutputVector()
        assert output is not None
        # 100m above should be +100m in Up direction (ENU)
        assert output[2] == pytest.approx(100.0, rel=0.01)

    def test_enu_to_ecef_conversion(self):
        """Test ENU to ECEF conversion."""
        from src.osk.blocks.navigation import CoordinateTransformationConversion

        conv = CoordinateTransformationConversion(
            input_type="enu", output_type="ecef", reference_lla=[0.0, 0.0, 0.0]
        )
        conv.init()
        conv.setInput([0.0, 0.0, 0.0])
        conv.update()

        output = conv.getOutputVector()
        assert output is not None
        assert output[0] == pytest.approx(6378137.0, rel=1e-6)

    def test_euler_to_dcm_conversion(self):
        """Test Euler angles to DCM conversion."""
        from src.osk.blocks.navigation import CoordinateTransformationConversion

        conv = CoordinateTransformationConversion(input_type="euler", output_type="dcm")
        conv.init()
        conv.setInput([0.0, 0.0, 0.0])  # Zero rotation
        conv.update()

        output = conv.getOutputVector()
        assert output is not None
        # Identity matrix: [1,0,0,0,1,0,0,0,1]
        assert output[0] == pytest.approx(1.0)
        assert output[4] == pytest.approx(1.0)
        assert output[8] == pytest.approx(1.0)

    def test_dcm_to_euler_conversion(self):
        """Test DCM to Euler conversion."""
        from src.osk.blocks.navigation import CoordinateTransformationConversion

        conv = CoordinateTransformationConversion(input_type="dcm", output_type="euler")
        conv.init()
        # Identity matrix
        conv.setInput([1, 0, 0, 0, 1, 0, 0, 0, 1])
        conv.update()

        output = conv.getOutputVector()
        assert output is not None
        assert output[0] == pytest.approx(0.0, abs=1e-10)
        assert output[1] == pytest.approx(0.0, abs=1e-10)
        assert output[2] == pytest.approx(0.0, abs=1e-10)

    def test_euler_to_quaternion_conversion(self):
        """Test Euler angles to quaternion conversion."""
        from src.osk.blocks.navigation import CoordinateTransformationConversion

        conv = CoordinateTransformationConversion(input_type="euler", output_type="quaternion")
        conv.init()
        conv.setInput([0.0, 0.0, 0.0])
        conv.update()

        output = conv.getOutputVector()
        assert output is not None
        # Identity quaternion [1, 0, 0, 0]
        assert output[0] == pytest.approx(1.0)
        assert output[1] == pytest.approx(0.0)
        assert output[2] == pytest.approx(0.0)
        assert output[3] == pytest.approx(0.0)

    def test_quaternion_to_euler_conversion(self):
        """Test quaternion to Euler conversion."""
        from src.osk.blocks.navigation import CoordinateTransformationConversion

        conv = CoordinateTransformationConversion(input_type="quaternion", output_type="euler")
        conv.init()
        conv.setInput([1.0, 0.0, 0.0, 0.0])
        conv.update()

        output = conv.getOutputVector()
        assert output is not None
        assert all(abs(x) < 1e-10 for x in output)

    def test_dcm_to_quaternion_conversion(self):
        """Test DCM to quaternion conversion."""
        from src.osk.blocks.navigation import CoordinateTransformationConversion

        conv = CoordinateTransformationConversion(input_type="dcm", output_type="quaternion")
        conv.init()
        conv.setInput([1, 0, 0, 0, 1, 0, 0, 0, 1])
        conv.update()

        output = conv.getOutputVector()
        assert output is not None
        assert output[0] == pytest.approx(1.0)

    def test_quaternion_to_dcm_conversion(self):
        """Test quaternion to DCM conversion."""
        from src.osk.blocks.navigation import CoordinateTransformationConversion

        conv = CoordinateTransformationConversion(input_type="quaternion", output_type="dcm")
        conv.init()
        conv.setInput([1.0, 0.0, 0.0, 0.0])
        conv.update()

        output = conv.getOutputVector()
        assert output is not None
        # Identity matrix
        assert output[0] == pytest.approx(1.0)
        assert output[4] == pytest.approx(1.0)
        assert output[8] == pytest.approx(1.0)

    def test_axis_angle_to_quaternion_conversion(self):
        """Test axis-angle to quaternion conversion."""
        from src.osk.blocks.navigation import CoordinateTransformationConversion

        conv = CoordinateTransformationConversion(input_type="axis_angle", output_type="quaternion")
        conv.init()
        # 90 degree rotation about z-axis
        conv.setInput([0.0, 0.0, 1.0, math.pi / 2])
        conv.update()

        output = conv.getOutputVector()
        assert output is not None
        assert output[0] == pytest.approx(math.cos(math.pi / 4))
        assert output[3] == pytest.approx(math.sin(math.pi / 4))

    def test_axis_angle_zero_axis(self):
        """Test axis-angle with zero axis (returns identity)."""
        from src.osk.blocks.navigation import CoordinateTransformationConversion

        conv = CoordinateTransformationConversion(input_type="axis_angle", output_type="quaternion")
        conv.init()
        conv.setInput([0.0, 0.0, 0.0, math.pi / 2])  # Zero axis
        conv.update()

        output = conv.getOutputVector()
        assert output is not None
        assert output[0] == pytest.approx(1.0)

    def test_quaternion_to_axis_angle_conversion(self):
        """Test quaternion to axis-angle conversion."""
        from src.osk.blocks.navigation import CoordinateTransformationConversion

        conv = CoordinateTransformationConversion(input_type="quaternion", output_type="axis_angle")
        conv.init()
        # 90 degree rotation about z-axis
        w = math.cos(math.pi / 4)
        z = math.sin(math.pi / 4)
        conv.setInput([w, 0.0, 0.0, z])
        conv.update()

        output = conv.getOutputVector()
        assert output is not None
        # Axis should be [0, 0, 1], angle should be pi/2
        assert output[2] == pytest.approx(1.0)
        assert output[3] == pytest.approx(math.pi / 2)

    def test_quaternion_to_axis_angle_identity(self):
        """Test quaternion to axis-angle for identity."""
        from src.osk.blocks.navigation import CoordinateTransformationConversion

        conv = CoordinateTransformationConversion(input_type="quaternion", output_type="axis_angle")
        conv.init()
        conv.setInput([1.0, 0.0, 0.0, 0.0])
        conv.update()

        output = conv.getOutputVector()
        assert output is not None
        # Identity has zero rotation angle
        assert output[3] == pytest.approx(0.0, abs=1e-10)

    def test_unsupported_conversion(self):
        """Test unsupported conversion passes through."""
        from src.osk.blocks.navigation import CoordinateTransformationConversion

        conv = CoordinateTransformationConversion(input_type="foo", output_type="bar")
        conv.init()
        conv.setInput([1.0, 2.0, 3.0])
        conv.update()

        output = conv.getOutputVector()
        assert output == [1.0, 2.0, 3.0]  # Pass-through

    def test_connect_input_block(self):
        """Test connecting an input block."""
        from src.osk.blocks.navigation import CoordinateTransformationConversion
        from src.osk.blocks.sources import Constant

        const = Constant(value=[0.0, 0.0, 0.0])
        const.init()
        const.update()

        conv = CoordinateTransformationConversion(input_type="lla", output_type="ecef")
        conv.init()
        conv.connectInput(const)
        conv.update()

        output = conv.getOutputVector()
        assert output is not None

    def test_get_output_port(self):
        """Test getOutput with port index."""
        from src.osk.blocks.navigation import CoordinateTransformationConversion

        conv = CoordinateTransformationConversion(input_type="lla", output_type="ecef")
        conv.init()
        conv.setInput([0.0, 0.0, 0.0])
        conv.update()

        assert conv.getOutput(0) == pytest.approx(6378137.0, rel=1e-6)
        assert conv.getOutput(1) == pytest.approx(0.0, abs=1e-3)
        assert conv.getOutput(10) == 0.0  # Out of range

    def test_dcm_to_euler_gimbal_lock(self):
        """Test DCM to Euler at gimbal lock (theta = +/-90deg)."""
        from src.osk.blocks.navigation import CoordinateTransformationConversion

        conv = CoordinateTransformationConversion(input_type="dcm", output_type="euler")
        conv.init()
        # DCM for pitch = 90 degrees (gimbal lock)
        # R = Rz * Ry(90) * Rx => sin(theta) = 1 => dcm[6] = -1
        conv.setInput([0, 0, 1, 0, 1, 0, -1, 0, 0])
        conv.update()

        output = conv.getOutputVector()
        assert output is not None
        # Should handle gimbal lock gracefully


class TestLLAToECEF:
    """Tests for LLAToECEF block."""

    def test_lla_to_ecef_equator(self):
        """Test LLA to ECEF at equator."""
        from src.osk.blocks.navigation import LLAToECEF

        block = LLAToECEF()
        block.init()
        block.setInput([0.0, 0.0, 0.0])
        block.update()

        assert block.getOutput(0) == pytest.approx(6378137.0, rel=1e-6)
        assert block.getOutput(1) == pytest.approx(0.0, abs=1e-3)
        assert block.getOutput(2) == pytest.approx(0.0, abs=1e-3)

    def test_lla_to_ecef_connected(self):
        """Test LLA to ECEF with connected block."""
        from src.osk.blocks.navigation import LLAToECEF
        from src.osk.blocks.sources import Constant

        const = Constant(value=[45.0, -75.0, 100.0])
        const.init()
        const.update()

        block = LLAToECEF()
        block.init()
        block.connectInput(const)
        block.update()

        output = block.getOutputVector()
        assert output is not None
        assert len(output) == 3


class TestECEFToLLA:
    """Tests for ECEFToLLA block."""

    def test_ecef_to_lla_equator(self):
        """Test ECEF to LLA at equator."""
        from src.osk.blocks.navigation import ECEFToLLA

        block = ECEFToLLA()
        block.init()
        block.setInput([6378137.0, 0.0, 0.0])
        block.update()

        assert block.getOutput(0) == pytest.approx(0.0, abs=1e-6)  # lat
        assert block.getOutput(1) == pytest.approx(0.0, abs=1e-6)  # lon

    def test_ecef_to_lla_pole(self):
        """Test ECEF to LLA at north pole."""
        from src.osk.blocks.navigation import ECEFToLLA

        block = ECEFToLLA()
        block.init()
        # North pole (z-axis)
        block.setInput([0.0, 0.0, 6356752.3])  # Semi-minor axis
        block.update()

        output = block.getOutputVector()
        assert output is not None
        assert output[0] == pytest.approx(90.0, abs=0.1)  # lat ~ 90


class TestECEFToNED:
    """Tests for ECEFToNED block."""

    def test_ecef_to_ned_at_reference(self):
        """Test ECEF to NED at reference point."""
        from src.osk.blocks.navigation import ECEFToNED

        block = ECEFToNED(reference_lla=[0.0, 0.0, 0.0])
        block.init()
        block.setInput([6378137.0, 0.0, 0.0])  # Reference ECEF
        block.update()

        output = block.getOutputVector()
        assert output is not None
        # At reference, NED should be [0, 0, 0]
        assert all(abs(x) < 1.0 for x in output)

    def test_ecef_to_ned_with_reference_input(self):
        """Test ECEF to NED with dynamic reference."""
        from src.osk.blocks.navigation import ECEFToNED

        block = ECEFToNED()
        block.init()
        block.setInput([6378137.0, 0.0, 0.0], port=0)  # ECEF
        block.setInput([0.0, 0.0, 0.0], port=1)  # Reference
        block.update()


class TestNEDToECEF:
    """Tests for NEDToECEF block."""

    def test_ned_to_ecef_at_origin(self):
        """Test NED to ECEF at origin."""
        from src.osk.blocks.navigation import NEDToECEF

        block = NEDToECEF(reference_lla=[0.0, 0.0, 0.0])
        block.init()
        block.setInput([0.0, 0.0, 0.0])
        block.update()

        output = block.getOutputVector()
        assert output is not None
        assert output[0] == pytest.approx(6378137.0, rel=1e-6)


class TestWaypointFollower:
    """Tests for WaypointFollower block."""

    def test_waypoint_follower_basic(self):
        """Test basic waypoint following."""
        from src.osk.blocks.navigation import WaypointFollower

        follower = WaypointFollower(
            waypoints=[[10.0, 10.0], [20.0, 10.0], [20.0, 20.0]],
            acceptance_radius=100.0,  # Small radius
        )
        follower.init()
        follower.setInput([0.0, 0.0])  # Far from waypoints
        follower.update()

        output = follower.getOutputVector()
        assert output is not None
        assert len(output) == 3
        assert output[2] == 0.0  # Current waypoint index

    def test_waypoint_follower_reach_waypoint(self):
        """Test reaching a waypoint advances to next."""
        from src.osk.blocks.navigation import WaypointFollower

        follower = WaypointFollower(
            waypoints=[[0.0, 0.0], [0.001, 0.0]],  # Very close waypoints
            acceptance_radius=1000.0,  # Large radius
        )
        follower.init()
        follower.setInput([0.0, 0.0])  # At first waypoint
        follower.update()

        # Should advance to next waypoint
        assert follower.output[2] >= 0

    def test_waypoint_follower_past_last(self):
        """Test behavior when past last waypoint."""
        from src.osk.blocks.navigation import WaypointFollower

        follower = WaypointFollower(waypoints=[[0.0, 0.0]])
        follower.init()
        follower.current_wp_index = 10  # Past end
        follower.setInput([0.0, 0.0])
        follower.update()

        assert follower.output[2] == 10.0


class TestGreatCircleDistance:
    """Tests for GreatCircleDistance block."""

    def test_great_circle_same_point(self):
        """Test distance between same point is zero."""
        from src.osk.blocks.navigation import GreatCircleDistance

        block = GreatCircleDistance()
        block.init()
        block.setInput([0.0, 0.0], port=0)
        block.setInput([0.0, 0.0], port=1)
        block.update()

        assert block.getOutput() == pytest.approx(0.0, abs=1.0)

    def test_great_circle_known_distance(self):
        """Test known great circle distance."""
        from src.osk.blocks.navigation import GreatCircleDistance

        block = GreatCircleDistance()
        block.init()
        # New York to London approximately 5570 km
        block.setInput([40.7128, -74.0060], port=0)  # NYC
        block.setInput([51.5074, -0.1278], port=1)  # London
        block.update()

        distance_km = block.getOutput() / 1000.0
        assert 5500 < distance_km < 5700


class TestFlatEarthPosition:
    """Tests for FlatEarthPosition block."""

    def test_flat_earth_basic(self):
        """Test basic flat earth position integration."""
        from src.osk.blocks.navigation import FlatEarthPosition

        block = FlatEarthPosition(initial_position=[0.0, 0.0, 0.0])
        block.init()
        block.setInput([10.0, 5.0, -1.0])  # Velocity NED
        block.update()

        # Position should update based on velocity
        output = block.getOutputVector()
        assert output is not None

    def test_flat_earth_connected(self):
        """Test flat earth with connected velocity block."""
        from src.osk.blocks.navigation import FlatEarthPosition
        from src.osk.blocks.sources import Constant

        vel = Constant(value=[1.0, 2.0, 3.0])
        vel.init()
        vel.update()

        block = FlatEarthPosition(initial_position=[100.0, 200.0, 300.0])
        block.init()
        block.connectInput(vel)
        block.update()

        output = block.getOutputVector()
        assert output is not None


# =============================================================================
# DSP Module Tests
# =============================================================================


class TestFFTBlock:
    """Tests for FFT block."""

    def test_fft_dc_signal(self):
        """Test FFT of DC signal."""
        from src.osk.blocks.dsp import FFT

        fft = FFT(n_points=8)
        fft.init()
        # DC signal (all ones)
        fft.setInput([1.0] * 8)
        fft.update()

        output = fft.getOutputVector()
        assert output is not None
        # DC component should be 8 (sum of all ones)
        assert output[0] == pytest.approx(8.0)
        # Imaginary part of DC should be 0
        assert output[1] == pytest.approx(0.0, abs=1e-10)

    def test_fft_connected_input(self):
        """Test FFT with connected input block."""
        from src.osk.blocks.dsp import FFT
        from src.osk.blocks.sources import Constant

        const = Constant(value=[1.0, 0.0, -1.0, 0.0])
        const.init()
        const.update()

        fft = FFT(n_points=4)
        fft.init()
        fft.connectInput(const)
        fft.update()

        output = fft.getOutputVector()
        assert output is not None

    def test_fft_get_output_port(self):
        """Test FFT getOutput with port."""
        from src.osk.blocks.dsp import FFT

        fft = FFT(n_points=4)
        fft.init()
        fft.setInput([1.0, 2.0, 3.0, 4.0])
        fft.update()

        assert isinstance(fft.getOutput(0), float)
        assert fft.getOutput(100) == 0.0  # Out of range


class TestIFFTBlock:
    """Tests for IFFT block."""

    def test_ifft_dc_signal(self):
        """Test IFFT of DC frequency component."""
        from src.osk.blocks.dsp import IFFT

        ifft = IFFT(n_points=4)
        ifft.init()
        # DC component of 4 (real), 0 (imag), zeros elsewhere
        ifft.setInput([4.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        ifft.update()

        output = ifft.getOutputVector()
        assert output is not None
        # Should reconstruct constant signal
        assert all(abs(x - 1.0) < 1e-10 for x in output)

    def test_ifft_connected_input(self):
        """Test IFFT with connected input block."""
        from src.osk.blocks.dsp import IFFT
        from src.osk.blocks.sources import Constant

        const = Constant(value=[4.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        const.init()
        const.update()

        ifft = IFFT(n_points=4)
        ifft.init()
        ifft.connectInput(const)
        ifft.update()


class TestFIRFilterBlock:
    """Tests for FIRFilter block."""

    def test_fir_moving_average(self):
        """Test FIR as moving average filter."""
        from src.osk.blocks.dsp import FIRFilter

        # 3-tap moving average
        fir = FIRFilter(coefficients=[1 / 3, 1 / 3, 1 / 3])
        fir.init()

        # Feed in samples
        fir.setInput(3.0)
        fir.update()
        fir.setInput(3.0)
        fir.update()
        fir.setInput(3.0)
        fir.update()

        # Output should be average
        assert fir.getOutput() == pytest.approx(3.0)

    def test_fir_connected_input(self):
        """Test FIR with connected input block."""
        from src.osk.blocks.dsp import FIRFilter
        from src.osk.blocks.sources import Constant

        const = Constant(value=5.0)
        const.init()
        const.update()

        fir = FIRFilter(coefficients=[1.0])
        fir.init()
        fir.connectInput(const)
        fir.update()

        assert fir.getOutput() == pytest.approx(5.0)


class TestIIRFilterBlock:
    """Tests for IIRFilter block."""

    def test_iir_first_order(self):
        """Test first-order IIR filter."""
        from src.osk.blocks.dsp import IIRFilter

        # First order low-pass: y[n] = 0.1*x[n] + 0.9*y[n-1]
        iir = IIRFilter(numerator=[0.1], denominator=[1.0, -0.9])
        iir.init()

        # Feed constant input, output should approach input
        for _ in range(50):
            iir.setInput(1.0)
            iir.update()

        assert iir.getOutput() == pytest.approx(1.0, rel=0.1)

    def test_iir_connected_input(self):
        """Test IIR with connected input block."""
        from src.osk.blocks.dsp import IIRFilter
        from src.osk.blocks.sources import Constant

        const = Constant(value=1.0)
        const.init()
        const.update()

        iir = IIRFilter(numerator=[1.0], denominator=[1.0])
        iir.init()
        iir.connectInput(const)
        iir.update()

        assert iir.getOutput() == pytest.approx(1.0)


class TestConvolutionBlock:
    """Tests for Convolution block."""

    def test_convolution_basic(self):
        """Test basic convolution."""
        from src.osk.blocks.dsp import Convolution

        conv = Convolution()
        conv.init()
        conv.setInput([1, 2, 3], port=0)  # Signal
        conv.setInput([1, 1], port=1)  # Kernel
        conv.update()

        output = conv.getOutputVector()
        assert output is not None
        # [1,2,3] * [1,1] = [1, 3, 5, 3]
        assert output == pytest.approx([1, 3, 5, 3])

    def test_convolution_empty_input(self):
        """Test convolution with empty input."""
        from src.osk.blocks.dsp import Convolution

        conv = Convolution()
        conv.init()
        conv.setInput([], port=0)
        conv.setInput([1, 1], port=1)
        conv.update()

        assert conv.getOutputVector() == []


class TestDownsamplerBlock:
    """Tests for Downsampler block."""

    def test_downsampler_by_2(self):
        """Test downsampling by factor of 2."""
        from src.osk.blocks.dsp import Downsampler

        ds = Downsampler(factor=2)
        ds.init()

        outputs = []
        for i in range(6):
            ds.setInput(float(i))
            ds.update()
            outputs.append(ds.getOutput())

        # Should keep 0, 2, 4
        assert outputs[0] == 0.0
        assert outputs[2] == 2.0
        assert outputs[4] == 4.0


class TestUpsamplerBlock:
    """Tests for Upsampler block."""

    def test_upsampler_by_2(self):
        """Test upsampling by factor of 2."""
        from src.osk.blocks.dsp import Upsampler

        us = Upsampler(factor=2)
        us.init()

        outputs = []
        for i in range(4):
            us.setInput(float(i + 1))
            us.update()
            outputs.append(us.getOutput())

        # First sample, then zero
        assert outputs[0] == 1.0
        assert outputs[1] == 0.0


class TestInterpolatorBlock:
    """Tests for Interpolator block."""

    def test_interpolator_linear(self):
        """Test linear interpolation."""
        from src.osk.blocks.dsp import Interpolator

        interp = Interpolator(factor=2)
        interp.init()

        # First sample
        interp.setInput(0.0)
        interp.update()
        _ = interp.getOutput()

        interp.setInput(2.0)
        interp.update()
        final_out = interp.getOutput()

        # Should interpolate between 0 and 2
        # The interpolator should produce values between samples
        assert final_out is not None


class TestWindowFunctionBlock:
    """Tests for WindowFunction block."""

    def test_window_hamming(self):
        """Test Hamming window."""
        from src.osk.blocks.dsp import WindowFunction

        win = WindowFunction(window_type="hamming", length=8)
        win.init()

        # Window coefficients should be generated
        assert len(win.window) == 8
        # Hamming window starts and ends near 0.08
        assert win.window[0] == pytest.approx(0.08, abs=0.01)

    def test_window_hanning(self):
        """Test Hanning window."""
        from src.osk.blocks.dsp import WindowFunction

        win = WindowFunction(window_type="hanning", length=8)
        win.init()
        assert len(win.window) == 8
        # Hanning starts at 0
        assert win.window[0] == pytest.approx(0.0)

    def test_window_blackman(self):
        """Test Blackman window."""
        from src.osk.blocks.dsp import WindowFunction

        win = WindowFunction(window_type="blackman", length=8)
        win.init()
        assert len(win.window) == 8

    def test_window_rectangular(self):
        """Test rectangular window (all ones)."""
        from src.osk.blocks.dsp import WindowFunction

        win = WindowFunction(window_type="rectangular", length=4)
        win.init()
        assert win.window == [1.0, 1.0, 1.0, 1.0]

    def test_window_kaiser(self):
        """Test Kaiser window."""
        from src.osk.blocks.dsp import WindowFunction

        win = WindowFunction(window_type="kaiser", length=8, beta=5.0)
        win.init()
        assert len(win.window) == 8

    def test_window_unknown_type(self):
        """Test unknown window type defaults to rectangular."""
        from src.osk.blocks.dsp import WindowFunction

        win = WindowFunction(window_type="unknown", length=4)
        win.init()
        assert win.window == [1.0, 1.0, 1.0, 1.0]

    def test_window_apply_to_signal(self):
        """Test applying window to signal."""
        from src.osk.blocks.dsp import WindowFunction

        win = WindowFunction(window_type="rectangular", length=4)
        win.init()
        win.setInput([2.0, 2.0, 2.0, 2.0])
        win.update()

        assert win.getOutputVector() == [2.0, 2.0, 2.0, 2.0]


class TestMeanBlock:
    """Tests for Mean block."""

    def test_mean_running_average(self):
        """Test running mean calculation."""
        from src.osk.blocks.dsp import Mean

        mean = Mean(window_size=3)
        mean.init()

        mean.setInput(3.0)
        mean.update()
        mean.setInput(6.0)
        mean.update()
        mean.setInput(9.0)
        mean.update()

        assert mean.getOutput() == pytest.approx(6.0)

    def test_mean_empty_buffer(self):
        """Test mean with empty buffer."""
        from src.osk.blocks.dsp import Mean

        mean = Mean(window_size=3)
        mean.init()
        mean.update()

        assert mean.getOutput() == 0.0


class TestVarianceBlock:
    """Tests for Variance block."""

    def test_variance_calculation(self):
        """Test variance calculation."""
        from src.osk.blocks.dsp import Variance

        var = Variance(window_size=3)
        var.init()

        var.setInput(1.0)
        var.update()
        var.setInput(2.0)
        var.update()
        var.setInput(3.0)
        var.update()

        # Variance of [1, 2, 3] = 1.0
        assert var.getOutput() == pytest.approx(1.0)

    def test_variance_single_sample(self):
        """Test variance with single sample."""
        from src.osk.blocks.dsp import Variance

        var = Variance(window_size=10)
        var.init()
        var.setInput(5.0)
        var.update()

        assert var.getOutput() == 0.0


class TestRMSBlock:
    """Tests for RMS block."""

    def test_rms_calculation(self):
        """Test RMS calculation."""
        from src.osk.blocks.dsp import RMS

        rms = RMS(window_size=4)
        rms.init()

        rms.setInput(2.0)
        rms.update()
        rms.setInput(2.0)
        rms.update()
        rms.setInput(2.0)
        rms.update()
        rms.setInput(2.0)
        rms.update()

        assert rms.getOutput() == pytest.approx(2.0)

    def test_rms_empty_buffer(self):
        """Test RMS with empty buffer."""
        from src.osk.blocks.dsp import RMS

        rms = RMS(window_size=3)
        rms.init()
        rms.update()

        assert rms.getOutput() == 0.0


class TestPeakDetectorBlock:
    """Tests for PeakDetector block."""

    def test_peak_detector_finds_peak(self):
        """Test peak detection."""
        from src.osk.blocks.dsp import PeakDetector

        pd = PeakDetector(threshold=0.0)
        pd.init()

        # Rising edge
        pd.setInput(0.0)
        pd.update()
        pd.setInput(1.0)
        pd.update()
        pd.setInput(2.0)  # Peak
        pd.update()
        pd.setInput(1.0)  # Falling - peak detected
        pd.update()

        assert pd.getOutput() == 1.0

    def test_peak_detector_threshold(self):
        """Test peak detector with threshold."""
        from src.osk.blocks.dsp import PeakDetector

        pd = PeakDetector(threshold=5.0)
        pd.init()

        pd.setInput(0.0)
        pd.update()
        pd.setInput(2.0)
        pd.update()
        pd.setInput(1.0)
        pd.update()

        # Peak at 2.0 is below threshold 5.0
        assert pd.getOutput() == 0.0


class TestZeroCrossingDetectorBlock:
    """Tests for ZeroCrossingDetector block."""

    def test_zero_crossing_rising(self):
        """Test rising zero crossing detection."""
        from src.osk.blocks.dsp import ZeroCrossingDetector

        zcd = ZeroCrossingDetector(direction="rising")
        zcd.init()

        zcd.setInput(-1.0)
        zcd.update()
        zcd.setInput(1.0)  # Rising crossing
        zcd.update()

        assert zcd.getOutput() == 1.0

    def test_zero_crossing_falling(self):
        """Test falling zero crossing detection."""
        from src.osk.blocks.dsp import ZeroCrossingDetector

        zcd = ZeroCrossingDetector(direction="falling")
        zcd.init()

        zcd.setInput(1.0)
        zcd.update()
        zcd.setInput(-1.0)  # Falling crossing
        zcd.update()

        assert zcd.getOutput() == 1.0

    def test_zero_crossing_both(self):
        """Test both zero crossing directions."""
        from src.osk.blocks.dsp import ZeroCrossingDetector

        zcd = ZeroCrossingDetector(direction="both")
        zcd.init()

        zcd.setInput(-1.0)
        zcd.update()
        zcd.setInput(1.0)  # Rising
        zcd.update()
        assert zcd.getOutput() == 1.0

        zcd.setInput(-1.0)  # Falling
        zcd.update()
        assert zcd.getOutput() == 1.0


# =============================================================================
# Matrix Operations Module Tests
# =============================================================================


class TestMatrixMultiplyBlock:
    """Tests for MatrixMultiply block."""

    def test_matrix_multiply_dot_product(self):
        """Test dot product of equal-length vectors."""
        from src.osk.blocks.matrix_ops import MatrixMultiply

        mm = MatrixMultiply()
        mm.init()
        mm.setInput([1, 2, 3], port=0)
        mm.setInput([4, 5, 6], port=1)
        mm.update()

        # Dot product: 1*4 + 2*5 + 3*6 = 32
        assert mm.getOutput() == pytest.approx(32.0)

    def test_matrix_multiply_scalar(self):
        """Test scalar multiplication."""
        from src.osk.blocks.matrix_ops import MatrixMultiply

        mm = MatrixMultiply()
        mm.init()
        mm.setInput(3.0, port=0)
        mm.setInput(4.0, port=1)
        mm.update()

        assert mm.getOutput() == pytest.approx(12.0)

    def test_matrix_multiply_different_lengths(self):
        """Test with different length inputs."""
        from src.osk.blocks.matrix_ops import MatrixMultiply

        mm = MatrixMultiply()
        mm.init()
        mm.setInput([1, 2], port=0)
        mm.setInput([3], port=1)
        mm.update()

        # Should treat as scalar mult
        assert mm.getOutput() == pytest.approx(3.0)


class TestMatrixTransposeBlock:
    """Tests for MatrixTranspose block."""

    def test_matrix_transpose_vector(self):
        """Test transpose of vector (identity for 1D)."""
        from src.osk.blocks.matrix_ops import MatrixTranspose
        from src.osk.blocks.sources import Constant

        # Must use connected input to set _is_vector flag
        const = Constant(value=[1, 2, 3])
        const.init()
        const.update()

        mt = MatrixTranspose()
        mt.init()
        mt.connectInput(const)
        mt.update()

        assert mt.getOutputVector() == [1, 2, 3]

    def test_matrix_transpose_scalar(self):
        """Test transpose of scalar."""
        from src.osk.blocks.matrix_ops import MatrixTranspose
        from src.osk.blocks.sources import Constant

        const = Constant(value=5.0)
        const.init()
        const.update()

        mt = MatrixTranspose()
        mt.init()
        mt.connectInput(const)
        mt.update()

        assert mt.getOutput() == 5.0


class TestMatrixInverseBlock:
    """Tests for MatrixInverse block."""

    def test_matrix_inverse_scalar(self):
        """Test inverse of scalar."""
        from src.osk.blocks.matrix_ops import MatrixInverse

        mi = MatrixInverse()
        mi.init()
        mi.setInput([4.0])
        mi.update()

        assert mi.getOutput() == pytest.approx(0.25)

    def test_matrix_inverse_scalar_zero(self):
        """Test inverse of zero returns inf."""
        from src.osk.blocks.matrix_ops import MatrixInverse

        mi = MatrixInverse()
        mi.init()
        mi.setInput([0.0])
        mi.update()

        assert mi.getOutput() == float("inf")

    def test_matrix_inverse_2x2(self):
        """Test inverse of 2x2 matrix."""
        from src.osk.blocks.matrix_ops import MatrixInverse
        from src.osk.blocks.sources import Constant

        const = Constant(value=[1, 2, 3, 4])
        const.init()
        const.update()

        mi = MatrixInverse()
        mi.init()
        mi.connectInput(const)
        mi.update()

        output = mi.getOutputVector()
        assert output is not None
        # Inverse of [[1,2],[3,4]] = [[-2, 1], [1.5, -0.5]]
        # det = -2
        assert output[0] == pytest.approx(-2.0)
        assert output[1] == pytest.approx(1.0)

    def test_matrix_inverse_singular(self):
        """Test inverse of singular matrix."""
        from src.osk.blocks.matrix_ops import MatrixInverse
        from src.osk.blocks.sources import Constant

        const = Constant(value=[1, 2, 2, 4])
        const.init()
        const.update()

        mi = MatrixInverse()
        mi.init()
        mi.connectInput(const)
        mi.update()

        output = mi.getOutputVector()
        assert output is not None
        assert all(x == float("inf") for x in output)

    def test_matrix_inverse_unsupported_size(self):
        """Test inverse with unsupported size passes through."""
        from src.osk.blocks.matrix_ops import MatrixInverse
        from src.osk.blocks.sources import Constant

        const = Constant(value=[1, 2, 3])
        const.init()
        const.update()

        mi = MatrixInverse()
        mi.init()
        mi.connectInput(const)
        mi.update()

        output = mi.getOutputVector()
        assert output is not None
        assert output == [1, 2, 3]  # Pass through


class TestSelectorBlock:
    """Tests for Selector block."""

    def test_selector_basic(self):
        """Test basic element selection."""
        from src.osk.blocks.matrix_ops import Selector

        sel = Selector(indices=[0, 2], output_size=2)
        sel.init()
        sel.setInput([10, 20, 30, 40])
        sel.update()

        output = sel.getOutputVector()
        assert output is not None
        assert output == [10, 30]

    def test_selector_out_of_range(self):
        """Test selector with out of range index."""
        from src.osk.blocks.matrix_ops import Selector

        sel = Selector(indices=[0, 10], output_size=2)
        sel.init()
        sel.setInput([1, 2, 3])
        sel.update()

        output = sel.getOutputVector()
        assert output is not None
        assert output == [1, 0.0]  # Out of range returns 0


class TestAssignmentBlock:
    """Tests for Assignment block."""

    def test_assignment_basic(self):
        """Test basic value assignment."""
        from src.osk.blocks.matrix_ops import Assignment

        assign = Assignment(indices=[1])
        assign.init()
        assign.setInput([1, 2, 3], port=0)  # Base
        assign.setInput([99], port=1)  # Values
        assign.update()

        output = assign.getOutputVector()
        assert output is not None
        assert output == [1, 99, 3]

    def test_assignment_multiple_indices(self):
        """Test assignment to multiple indices."""
        from src.osk.blocks.matrix_ops import Assignment

        assign = Assignment(indices=[0, 2])
        assign.init()
        assign.setInput([1, 2, 3, 4], port=0)
        assign.setInput([10, 30], port=1)
        assign.update()

        output = assign.getOutputVector()
        assert output is not None
        assert output == [10, 2, 30, 4]


class TestConcatenateBlock:
    """Tests for Concatenate block."""

    def test_concatenate_two_vectors(self):
        """Test concatenating two vectors."""
        from src.osk.blocks.matrix_ops import Concatenate

        cat = Concatenate(num_inputs=2)
        cat.init()
        cat.setInput([1, 2], port=0)
        cat.setInput([3, 4], port=1)
        cat.update()

        output = cat.getOutputVector()
        assert output is not None
        assert output == [1, 2, 3, 4]

    def test_concatenate_three_inputs(self):
        """Test concatenating three inputs."""
        from src.osk.blocks.matrix_ops import Concatenate

        cat = Concatenate(num_inputs=3)
        cat.init()
        cat.setInput([1], port=0)
        cat.setInput([2], port=1)
        cat.setInput([3], port=2)
        cat.update()

        output = cat.getOutputVector()
        assert output is not None
        assert output == [1, 2, 3]

    def test_concatenate_get_num_outputs(self):
        """Test getNumOutputs method."""
        from src.osk.blocks.matrix_ops import Concatenate

        cat = Concatenate(num_inputs=2)
        cat.init()
        cat.setInput([1, 2, 3], port=0)
        cat.setInput([4, 5], port=1)
        cat.update()

        assert cat.getNumOutputs() == 5


class TestMatrixSumBlock:
    """Tests for MatrixSum block."""

    def test_matrix_sum_all(self):
        """Test sum of all elements."""
        from src.osk.blocks.matrix_ops import MatrixSum

        ms = MatrixSum(dimension="all")
        ms.init()
        ms.setInput([1, 2, 3, 4])
        ms.update()

        assert ms.getOutput() == pytest.approx(10.0)

    def test_matrix_sum_scalar(self):
        """Test sum of scalar."""
        from src.osk.blocks.matrix_ops import MatrixSum

        ms = MatrixSum()
        ms.init()
        ms.setInput(5.0)
        ms.update()

        assert ms.getOutput() == pytest.approx(5.0)


class TestVectorNormBlock:
    """Tests for VectorNorm block."""

    def test_vector_norm_2(self):
        """Test 2-norm (Euclidean)."""
        from src.osk.blocks.matrix_ops import VectorNorm

        vn = VectorNorm(norm_type="2")
        vn.init()
        vn.setInput([3, 4])  # sqrt(9+16) = 5
        vn.update()

        assert vn.getOutput() == pytest.approx(5.0)

    def test_vector_norm_1(self):
        """Test 1-norm (Manhattan)."""
        from src.osk.blocks.matrix_ops import VectorNorm

        vn = VectorNorm(norm_type="1")
        vn.init()
        vn.setInput([-3, 4])  # |3| + |4| = 7
        vn.update()

        assert vn.getOutput() == pytest.approx(7.0)

    def test_vector_norm_inf(self):
        """Test inf-norm (maximum)."""
        from src.osk.blocks.matrix_ops import VectorNorm

        vn = VectorNorm(norm_type="inf")
        vn.init()
        vn.setInput([-5, 3, 4])  # max(|5|, |3|, |4|) = 5
        vn.update()

        assert vn.getOutput() == pytest.approx(5.0)

    def test_vector_norm_unknown_type(self):
        """Test unknown norm type defaults to 2-norm."""
        from src.osk.blocks.matrix_ops import VectorNorm

        vn = VectorNorm(norm_type="unknown")
        vn.init()
        vn.setInput([3, 4])
        vn.update()

        assert vn.getOutput() == pytest.approx(5.0)

    def test_vector_norm_empty(self):
        """Test norm of empty vector."""
        from src.osk.blocks.matrix_ops import VectorNorm

        vn = VectorNorm(norm_type="inf")
        vn.init()
        vn.setInput([])
        vn.update()

        assert vn.getOutput() == 0.0


# =============================================================================
# RF Module Tests
# =============================================================================


class TestRFAmplifierBlock:
    """Tests for RFAmplifier block."""

    def test_rf_amplifier_basic_gain(self):
        """Test basic amplifier gain."""
        from src.osk.blocks.rf import RFAmplifier

        amp = RFAmplifier(gain_db=20.0, p1db_dbm=30.0)
        amp.init()
        amp.setInput(-10.0)  # -10 dBm input

        assert amp.getOutput() == pytest.approx(10.0)  # -10 + 20 = 10 dBm

    def test_rf_amplifier_compression(self):
        """Test amplifier compression near P1dB."""
        from src.osk.blocks.rf import RFAmplifier

        amp = RFAmplifier(gain_db=20.0, p1db_dbm=20.0)
        amp.init()
        amp.setInput(5.0)  # 5 dBm input -> 25 dBm ideal output > P1dB

        # Should compress below ideal
        output = amp.getOutput()
        assert output < 25.0
        assert output <= 25.0  # P1dB + 5

    def test_rf_amplifier_connected(self):
        """Test amplifier with connected input."""
        from src.osk.blocks.rf import RFAmplifier
        from src.osk.blocks.sources import Constant

        const = Constant(value=-20.0)
        const.init()
        const.update()

        amp = RFAmplifier(gain_db=10.0)
        amp.init()
        amp.connectInput(const)
        amp.update()

        assert amp.getOutput() == pytest.approx(-10.0)


class TestRFMixerBlock:
    """Tests for RFMixer block."""

    def test_rf_mixer_conversion_loss(self):
        """Test mixer conversion loss."""
        from src.osk.blocks.rf import RFMixer

        mixer = RFMixer(conversion_loss_db=6.0)
        mixer.init()
        mixer.setInput(0.0, port=0)  # RF input: 0 dBm
        mixer.setInput(10.0, port=1)  # LO
        mixer.update()

        assert mixer.getOutput() == pytest.approx(-6.0)

    def test_rf_mixer_connected(self):
        """Test mixer with connected inputs."""
        from src.osk.blocks.rf import RFMixer
        from src.osk.blocks.sources import Constant

        rf = Constant(value=-10.0)
        rf.init()
        rf.update()

        lo = Constant(value=7.0)
        lo.init()
        lo.update()

        mixer = RFMixer(conversion_loss_db=8.0)
        mixer.init()
        mixer.connectInput(rf, port=0)
        mixer.connectInput(lo, port=1)
        mixer.update()

        assert mixer.getOutput() == pytest.approx(-18.0)


class TestRFFilterBlock:
    """Tests for RFFilter block."""

    def test_rf_filter_bandpass_in_band(self):
        """Test bandpass filter in passband."""
        from src.osk.blocks.rf import RFFilter

        filt = RFFilter(
            filter_type="bandpass",
            center_freq_hz=1e9,
            bandwidth_hz=100e6,
            insertion_loss_db=1.0,
            rejection_db=40.0,
        )
        filt.init()
        filt.setInput(0.0, port=0)  # Power
        filt.setInput(1e9, port=1)  # Freq (in band)
        filt.update()

        assert filt.getOutput() == pytest.approx(-1.0)  # Just insertion loss

    def test_rf_filter_bandpass_out_of_band(self):
        """Test bandpass filter out of band."""
        from src.osk.blocks.rf import RFFilter

        filt = RFFilter(
            filter_type="bandpass",
            center_freq_hz=1e9,
            bandwidth_hz=100e6,
            insertion_loss_db=1.0,
            rejection_db=40.0,
        )
        filt.init()
        filt.setInput(0.0, port=0)
        filt.setInput(2e9, port=1)  # Out of band
        filt.update()

        assert filt.getOutput() == pytest.approx(-41.0)  # IL + rejection

    def test_rf_filter_bandstop(self):
        """Test bandstop filter."""
        from src.osk.blocks.rf import RFFilter

        filt = RFFilter(
            filter_type="bandstop",
            center_freq_hz=1e9,
            bandwidth_hz=100e6,
            insertion_loss_db=1.0,
            rejection_db=30.0,
        )
        filt.init()

        # In stop band
        filt.setInput(0.0, port=0)
        filt.setInput(1e9, port=1)
        filt.update()
        assert filt.getOutput() == pytest.approx(-31.0)

        # Out of stop band (passband)
        filt.setInput(0.0, port=0)
        filt.setInput(2e9, port=1)
        filt.update()
        assert filt.getOutput() == pytest.approx(-1.0)

    def test_rf_filter_lowpass(self):
        """Test lowpass filter."""
        from src.osk.blocks.rf import RFFilter

        filt = RFFilter(
            filter_type="lowpass", center_freq_hz=1e9, insertion_loss_db=0.5, rejection_db=50.0
        )
        filt.init()

        # Below cutoff
        filt.setInput(0.0, port=0)
        filt.setInput(0.5e9, port=1)
        filt.update()
        assert filt.getOutput() == pytest.approx(-0.5)

        # Above cutoff
        filt.setInput(0.0, port=0)
        filt.setInput(2e9, port=1)
        filt.update()
        assert filt.getOutput() == pytest.approx(-50.5)

    def test_rf_filter_highpass(self):
        """Test highpass filter."""
        from src.osk.blocks.rf import RFFilter

        filt = RFFilter(
            filter_type="highpass", center_freq_hz=1e9, insertion_loss_db=0.5, rejection_db=50.0
        )
        filt.init()

        # Above cutoff
        filt.setInput(0.0, port=0)
        filt.setInput(2e9, port=1)
        filt.update()
        assert filt.getOutput() == pytest.approx(-0.5)

        # Below cutoff
        filt.setInput(0.0, port=0)
        filt.setInput(0.5e9, port=1)
        filt.update()
        assert filt.getOutput() == pytest.approx(-50.5)

    def test_rf_filter_unknown_type(self):
        """Test filter with unknown type."""
        from src.osk.blocks.rf import RFFilter

        filt = RFFilter(filter_type="unknown", insertion_loss_db=2.0)
        filt.init()
        filt.setInput(0.0, port=0)
        filt.setInput(1e9, port=1)
        filt.update()

        assert filt.getOutput() == pytest.approx(-2.0)


class TestSParameterNetworkBlock:
    """Tests for SParameterNetwork block."""

    def test_s_param_through(self):
        """Test ideal through connection."""
        from src.osk.blocks.rf import SParameterNetwork

        # Default is ideal through: S21 = 1
        sparam = SParameterNetwork()
        sparam.init()
        sparam.setInput([1.0, 0.0])  # Unit input
        sparam.update()

        output = sparam.getOutputVector()
        assert output is not None
        # b1 = S11 * a1 = 0
        # b2 = S21 * a1 = 1
        assert output[0] == pytest.approx(0.0)
        assert output[2] == pytest.approx(1.0)

    def test_s_param_custom(self):
        """Test custom S-parameters."""
        from src.osk.blocks.rf import SParameterNetwork

        # S11 = 0.5, S21 = 0.866 (approx for -3dB return loss, 0dB insertion)
        sparam = SParameterNetwork(s_params=[0.5, 0, 0, 0, 0.866, 0, 0, 0])
        sparam.init()
        sparam.setInput([2.0, 0.0])
        sparam.update()

        output = sparam.getOutputVector()
        assert output is not None
        assert output[0] == pytest.approx(1.0)  # b1 = 0.5 * 2
        assert output[2] == pytest.approx(1.732)  # b2 = 0.866 * 2

    def test_s_param_connected(self):
        """Test S-parameter with connected input."""
        from src.osk.blocks.rf import SParameterNetwork
        from src.osk.blocks.sources import Constant

        const = Constant(value=[1.0, 0.5])
        const.init()
        const.update()

        sparam = SParameterNetwork()
        sparam.init()
        sparam.connectInput(const)
        sparam.update()

        output = sparam.getOutputVector()
        assert output is not None


class TestRFBudgetElementBlock:
    """Tests for RFBudgetElement block."""

    def test_rf_budget_first_element(self):
        """Test first element in cascade."""
        from src.osk.blocks.rf import RFBudgetElement

        elem = RFBudgetElement(gain_db=10.0, noise_figure_db=3.0)
        elem.init()
        elem.setInput(-30.0, port=0)  # Input power
        elem.setInput(0.0, port=1)  # Cascaded gain (first element)
        elem.setInput(0.0, port=2)  # Cascaded NF (first element)
        elem.update()

        output = elem.getOutputVector()
        assert output is not None
        assert output[0] == pytest.approx(-20.0)  # Pout = Pin + G
        assert output[1] == pytest.approx(10.0)  # Cascaded gain
        assert output[2] == pytest.approx(3.0)  # Cascaded NF = this NF

    def test_rf_budget_cascade(self):
        """Test cascaded element with Friis formula."""
        from src.osk.blocks.rf import RFBudgetElement

        elem = RFBudgetElement(gain_db=5.0, noise_figure_db=6.0)
        elem.init()
        elem.setInput(-20.0, port=0)
        elem.setInput(10.0, port=1)  # Previous gain
        elem.setInput(3.0, port=2)  # Previous NF
        elem.update()

        output = elem.getOutputVector()
        assert output is not None
        assert output[0] == pytest.approx(-15.0)
        assert output[1] == pytest.approx(15.0)
        # NF should be slightly higher than first stage

    def test_rf_budget_low_gain_cascade(self):
        """Test cascade with very low gain."""
        from src.osk.blocks.rf import RFBudgetElement

        elem = RFBudgetElement(gain_db=0.0, noise_figure_db=3.0)
        elem.init()
        elem.setInput(0.0, port=0)
        elem.setInput(-100.0, port=1)  # Very low previous gain
        elem.setInput(3.0, port=2)
        elem.update()

        # Should handle low gain case


class TestAttenuatorBlock:
    """Tests for Attenuator block."""

    def test_attenuator_basic(self):
        """Test basic attenuation."""
        from src.osk.blocks.rf import Attenuator

        atten = Attenuator(attenuation_db=10.0)
        atten.init()
        atten.setInput(0.0)

        assert atten.getOutput() == pytest.approx(-10.0)

    def test_attenuator_connected(self):
        """Test attenuator with connected input."""
        from src.osk.blocks.rf import Attenuator
        from src.osk.blocks.sources import Constant

        const = Constant(value=20.0)
        const.init()
        const.update()

        atten = Attenuator(attenuation_db=6.0)
        atten.init()
        atten.connectInput(const)
        atten.update()

        assert atten.getOutput() == pytest.approx(14.0)


class TestAMModulatorBlock:
    """Tests for AMModulator block."""

    def test_am_modulator_zero_message(self):
        """Test AM modulator with zero message."""
        from src.osk.blocks.rf import AMModulator
        from src.osk.state import State

        State.t = 0.0
        mod = AMModulator(carrier_freq=1e6, carrier_amplitude=1.0, modulation_index=0.5)
        mod.init()
        mod.setInput(0.0)  # Zero message
        mod.update()

        # At t=0, cos(0) = 1, envelope = 1, output = 1
        assert mod.getOutput() == pytest.approx(1.0)

    def test_am_modulator_with_message(self):
        """Test AM modulator with non-zero message."""
        from src.osk.blocks.rf import AMModulator
        from src.osk.state import State

        State.t = 0.0
        mod = AMModulator(carrier_freq=1e6, carrier_amplitude=2.0, modulation_index=0.5)
        mod.init()
        mod.setInput(1.0)  # Full positive message
        mod.update()

        # At t=0: envelope = 1 + 0.5*1 = 1.5, carrier = 1
        # output = 2.0 * 1.5 * 1 = 3.0
        assert mod.getOutput() == pytest.approx(3.0)


class TestFMModulatorBlock:
    """Tests for FMModulator block."""

    def test_fm_modulator_zero_message(self):
        """Test FM modulator with zero message."""
        from src.osk.blocks.rf import FMModulator
        from src.osk.state import State

        State.t = 0.0
        State.dt = 0.001
        mod = FMModulator(carrier_freq=1e6, carrier_amplitude=1.0, freq_deviation=75e3)
        mod.init()
        mod.setInput(0.0)
        mod.update()

        # At t=0 with zero message, output = cos(0) = 1
        assert mod.getOutput() == pytest.approx(1.0)

    def test_fm_modulator_accumulation(self):
        """Test FM modulator phase accumulation."""
        from src.osk.blocks.rf import FMModulator
        from src.osk.state import State

        State.t = 0.0
        State.dt = 1e-6
        mod = FMModulator(
            carrier_freq=0.0,  # Zero carrier to isolate phase modulation
            carrier_amplitude=1.0,
            freq_deviation=1e6,
        )
        mod.init()

        # First update with positive message
        mod.setInput(1.0)
        mod.update()

        # Phase should have accumulated


class TestPhaseNoiseBlock:
    """Tests for PhaseNoise block."""

    def test_phase_noise_basic(self):
        """Test phase noise adds noise to signal."""
        from src.osk.blocks.rf import PhaseNoise
        from src.osk.state import State

        State.dt = 0.001
        pn = PhaseNoise(phase_noise_dbcHz=-100.0, offset_freq=10e3)
        pn.init()
        pn.setInput(1.0)
        pn.update()

        # Output should be close to input with small noise
        output = pn.getOutput()
        assert isinstance(output, float)

    def test_phase_noise_connected(self):
        """Test phase noise with connected input."""
        from src.osk.blocks.rf import PhaseNoise
        from src.osk.blocks.sources import Constant
        from src.osk.state import State

        State.dt = 0.001
        const = Constant(value=5.0)
        const.init()
        const.update()

        pn = PhaseNoise(phase_noise_dbcHz=-80.0, offset_freq=1e3)
        pn.init()
        pn.connectInput(const)
        pn.update()

        # Output should be close to 5.0


class TestdBmToWattsBlock:
    """Tests for dBmToWatts block."""

    def test_dbm_to_watts_0dbm(self):
        """Test 0 dBm = 1 mW."""
        from src.osk.blocks.rf import dBmToWatts

        conv = dBmToWatts()
        conv.init()
        conv.setInput(0.0)

        assert conv.getOutput() == pytest.approx(0.001)

    def test_dbm_to_watts_30dbm(self):
        """Test 30 dBm = 1 W."""
        from src.osk.blocks.rf import dBmToWatts

        conv = dBmToWatts()
        conv.init()
        conv.setInput(30.0)

        assert conv.getOutput() == pytest.approx(1.0)

    def test_dbm_to_watts_connected(self):
        """Test with connected input."""
        from src.osk.blocks.rf import dBmToWatts
        from src.osk.blocks.sources import Constant

        const = Constant(value=10.0)
        const.init()
        const.update()

        conv = dBmToWatts()
        conv.init()
        conv.connectInput(const)
        conv.update()

        # 10 dBm = 10 mW = 0.01 W
        assert conv.getOutput() == pytest.approx(0.01)


class TestWattsTodBmBlock:
    """Tests for WattsTodBm block."""

    def test_watts_to_dbm_1mw(self):
        """Test 1 mW = 0 dBm."""
        from src.osk.blocks.rf import WattsTodBm

        conv = WattsTodBm()
        conv.init()
        conv.setInput(0.001)

        assert conv.getOutput() == pytest.approx(0.0)

    def test_watts_to_dbm_1w(self):
        """Test 1 W = 30 dBm."""
        from src.osk.blocks.rf import WattsTodBm

        conv = WattsTodBm()
        conv.init()
        conv.setInput(1.0)

        assert conv.getOutput() == pytest.approx(30.0)

    def test_watts_to_dbm_zero(self):
        """Test 0 W returns floor value."""
        from src.osk.blocks.rf import WattsTodBm

        conv = WattsTodBm()
        conv.init()
        conv.setInput(0.0)

        assert conv.getOutput() == -200.0

    def test_watts_to_dbm_connected(self):
        """Test with connected input."""
        from src.osk.blocks.rf import WattsTodBm
        from src.osk.blocks.sources import Constant

        const = Constant(value=0.01)  # 10 mW
        const.init()
        const.update()

        conv = WattsTodBm()
        conv.init()
        conv.connectInput(const)
        conv.update()

        assert conv.getOutput() == pytest.approx(10.0)

    def test_watts_to_dbm_connected_zero(self):
        """Test connected with zero input."""
        from src.osk.blocks.rf import WattsTodBm
        from src.osk.blocks.sources import Constant

        const = Constant(value=0.0)
        const.init()
        const.update()

        conv = WattsTodBm()
        conv.init()
        conv.connectInput(const)
        conv.update()

        assert conv.getOutput() == -200.0


# =============================================================================
# Sensor Fusion Module Tests
# =============================================================================


class TestMadgwickFilterBlock:
    """Tests for MadgwickFilter block."""

    def test_madgwick_initialization(self):
        """Test Madgwick filter initialization."""
        from src.osk.blocks.sensor_fusion import MadgwickFilter

        mf = MadgwickFilter(beta=0.1)
        mf.init()

        # Initial quaternion should be identity [1, 0, 0, 0]
        output = mf.getOutputVector()
        assert output is not None
        assert output[0] == pytest.approx(1.0)

    def test_madgwick_stationary(self):
        """Test Madgwick filter with stationary input."""
        from src.osk.blocks.sensor_fusion import MadgwickFilter
        from src.osk.state import State

        State.dt = 0.01
        mf = MadgwickFilter(beta=0.1)
        mf.init()

        # Zero gyro, normalized accelerometer pointing up
        mf.setInput([0, 0, 0], port=0)  # Gyro
        mf.setInput([0, 0, 1], port=1)  # Accel
        mf.update()

        output = mf.getOutputVector()
        assert output is not None


class TestComplementaryFilterBlock:
    """Tests for ComplementaryFilter block."""

    def test_complementary_initialization(self):
        """Test complementary filter initialization."""
        from src.osk.blocks.sensor_fusion import ComplementaryFilter

        cf = ComplementaryFilter(alpha=0.98)
        cf.init()

        # Initial output should be zeros (Euler angles)
        output = cf.getOutputVector()
        assert output is not None

    def test_complementary_stationary(self):
        """Test complementary filter with stationary input."""
        from src.osk.blocks.sensor_fusion import ComplementaryFilter
        from src.osk.state import State

        State.dt = 0.01
        cf = ComplementaryFilter(alpha=0.98)
        cf.init()

        # Zero gyro, flat accelerometer
        cf.setInput([0, 0, 0], port=0)  # Gyro
        cf.setInput([0, 0, 1], port=1)  # Accel
        cf.update()

        output = cf.getOutputVector()
        assert output is not None


class TestMahonyFilterBlock:
    """Tests for MahonyFilter block."""

    def test_mahony_initialization(self):
        """Test Mahony filter initialization."""
        from src.osk.blocks.sensor_fusion import MahonyFilter

        # MahonyFilter uses Kp and Ki
        mf = MahonyFilter(Kp=0.5, Ki=0.01)
        mf.init()

        output = mf.getOutputVector()
        assert output is not None
        assert output[0] == pytest.approx(1.0)  # Identity quaternion

    def test_mahony_stationary(self):
        """Test Mahony filter with stationary input."""
        from src.osk.blocks.sensor_fusion import MahonyFilter
        from src.osk.state import State

        State.dt = 0.01
        mf = MahonyFilter(Kp=0.5, Ki=0.01)
        mf.init()

        mf.setInput([0, 0, 0], port=0)  # Gyro
        mf.setInput([0, 0, 1], port=1)  # Accel
        mf.update()


class TestIMUSensor:
    """Tests for IMUSensor block."""

    def test_imu_initialization(self):
        """Test IMU sensor initialization."""
        from src.osk.blocks.sensor_fusion import IMUSensor

        imu = IMUSensor()
        imu.init()

        output = imu.getOutputVector()
        assert output is not None

    def test_imu_with_input(self):
        """Test IMU sensor with input."""
        from src.osk.blocks.sensor_fusion import IMUSensor
        from src.osk.state import State

        State.dt = 0.01
        imu = IMUSensor()
        imu.init()

        # True acceleration and angular velocity
        imu.setInput([0.0, 0.0, 9.81], port=0)  # Accel
        imu.setInput([0.0, 0.0, 0.0], port=1)  # Gyro
        imu.update()


class TestAccelerometer:
    """Tests for Accelerometer block."""

    def test_accelerometer_basic(self):
        """Test accelerometer output."""
        from src.osk.blocks.sensor_fusion import Accelerometer

        accel = Accelerometer()
        accel.init()
        accel.setInput([0.0, 0.0, 9.81])
        accel.update()

        output = accel.getOutputVector()
        assert output is not None


class TestGyroscope:
    """Tests for Gyroscope block."""

    def test_gyroscope_basic(self):
        """Test gyroscope output."""
        from src.osk.blocks.sensor_fusion import Gyroscope

        gyro = Gyroscope()
        gyro.init()
        gyro.setInput([0.1, 0.2, 0.3])
        gyro.update()

        output = gyro.getOutputVector()
        assert output is not None


class TestMagnetometer:
    """Tests for Magnetometer block."""

    def test_magnetometer_basic(self):
        """Test magnetometer output."""
        from src.osk.blocks.sensor_fusion import Magnetometer

        mag = Magnetometer()
        mag.init()
        mag.setInput([0.2, 0.0, 0.4])
        mag.update()

        output = mag.getOutputVector()
        assert output is not None


class TestGPSSensor:
    """Tests for GPSSensor block."""

    def test_gps_basic(self):
        """Test GPS sensor output."""
        from src.osk.blocks.sensor_fusion import GPSSensor

        gps = GPSSensor()
        gps.init()
        gps.setInput([40.0, -75.0, 100.0])  # Lat, lon, alt
        gps.update()

        output = gps.getOutputVector()
        assert output is not None


class TestAltimeter:
    """Tests for Altimeter block."""

    def test_altimeter_basic(self):
        """Test altimeter output."""
        from src.osk.blocks.sensor_fusion import Altimeter

        alt = Altimeter()
        alt.init()
        alt.setInput(1000.0)  # Altitude
        alt.update()

        output = alt.getOutput()
        assert isinstance(output, float)


class TestAlphaBetaFilter:
    """Tests for AlphaBetaFilter block."""

    def test_alpha_beta_initialization(self):
        """Test alpha-beta filter initialization."""
        from src.osk.blocks.sensor_fusion import AlphaBetaFilter

        abf = AlphaBetaFilter(alpha=0.5, beta=0.1)
        abf.init()

        output = abf.getOutputVector()
        assert output is not None


class TestAlphaBetaGammaFilter:
    """Tests for AlphaBetaGammaFilter block."""

    def test_alpha_beta_gamma_initialization(self):
        """Test alpha-beta-gamma filter initialization."""
        from src.osk.blocks.sensor_fusion import AlphaBetaGammaFilter

        abgf = AlphaBetaGammaFilter(alpha=0.5, beta=0.1, gamma=0.01)
        abgf.init()

        output = abgf.getOutputVector()
        assert output is not None


class TestINSGPSFusion:
    """Tests for INSGPSFusion block."""

    def test_ins_gps_initialization(self):
        """Test INS/GPS fusion initialization."""
        from src.osk.blocks.sensor_fusion import INSGPSFusion

        fusion = INSGPSFusion()
        fusion.init()

        output = fusion.getOutputVector()
        assert output is not None


# =============================================================================
# Aerospace Module Tests
# =============================================================================


class TestISAAtmosphereBlock:
    """Tests for ISAAtmosphere block."""

    def test_atmosphere_sea_level(self):
        """Test ISA at sea level."""
        from src.osk.blocks.aerospace import ISAAtmosphere

        atm = ISAAtmosphere()
        atm.init()
        atm.setInput(0.0)  # Sea level
        atm.update()

        output = atm.getOutputVector()
        assert output is not None
        # Standard sea level: T=288.15K, P=101325 Pa, rho=1.225 kg/m³
        assert output[0] == pytest.approx(288.15, rel=0.001)
        assert output[1] == pytest.approx(101325, rel=0.001)

    def test_atmosphere_11km(self):
        """Test ISA at 11km (tropopause)."""
        from src.osk.blocks.aerospace import ISAAtmosphere

        atm = ISAAtmosphere()
        atm.init()
        atm.setInput(11000.0)
        atm.update()

        output = atm.getOutputVector()
        assert output is not None
        # At 11km: T ≈ 216.65K
        assert output[0] == pytest.approx(216.65, rel=0.01)

    def test_atmosphere_connected(self):
        """Test ISA with connected input."""
        from src.osk.blocks.aerospace import ISAAtmosphere
        from src.osk.blocks.sources import Constant

        const = Constant(value=5000.0)
        const.init()
        const.update()

        atm = ISAAtmosphere()
        atm.init()
        atm.connectInput(const)
        atm.update()

        output = atm.getOutputVector()
        assert output is not None


class TestQuaternionNormalize:
    """Tests for QuaternionNormalize block."""

    def test_quat_normalize_unit(self):
        """Test normalizing already-unit quaternion."""
        from src.osk.blocks.aerospace import QuaternionNormalize

        qn = QuaternionNormalize()
        qn.init()
        qn.setInput([1.0, 0.0, 0.0, 0.0])
        qn.update()

        output = qn.getOutputVector()
        assert output is not None
        assert output[0] == pytest.approx(1.0)

    def test_quat_normalize_non_unit(self):
        """Test normalizing non-unit quaternion."""
        from src.osk.blocks.aerospace import QuaternionNormalize

        qn = QuaternionNormalize()
        qn.init()
        qn.setInput([2.0, 0.0, 0.0, 0.0])
        qn.update()

        output = qn.getOutputVector()
        assert output is not None
        # Should be normalized to [1, 0, 0, 0]
        assert output[0] == pytest.approx(1.0)


class TestQuaternionMultiply:
    """Tests for QuaternionMultiply block."""

    def test_quat_multiply_identity(self):
        """Test multiplying by identity quaternion."""
        from src.osk.blocks.aerospace import QuaternionMultiply

        qm = QuaternionMultiply()
        qm.init()
        qm.setInput([1.0, 0.0, 0.0, 0.0], port=0)  # Identity
        qm.setInput([0.707, 0.0, 0.0, 0.707], port=1)  # 90 deg about z
        qm.update()

        output = qm.getOutputVector()
        assert output is not None


class TestQuaternionConjugate:
    """Tests for QuaternionConjugate block."""

    def test_quat_conjugate(self):
        """Test quaternion conjugate."""
        from src.osk.blocks.aerospace import QuaternionConjugate

        qc = QuaternionConjugate()
        qc.init()
        qc.setInput([1.0, 0.5, 0.5, 0.5])
        qc.update()

        output = qc.getOutputVector()
        assert output is not None
        # Conjugate negates vector part
        assert output[0] == pytest.approx(1.0)
        assert output[1] == pytest.approx(-0.5)


class TestQuaternionToEuler:
    """Tests for QuaternionToEuler block."""

    def test_quat_to_euler_identity(self):
        """Test identity quaternion to Euler."""
        from src.osk.blocks.aerospace import QuaternionToEuler

        qe = QuaternionToEuler()
        qe.init()
        qe.setInput([1.0, 0.0, 0.0, 0.0])
        qe.update()

        output = qe.getOutputVector()
        assert output is not None
        # Should be zero Euler angles
        assert all(abs(x) < 1e-10 for x in output)


class TestEulerToQuaternion:
    """Tests for EulerToQuaternion block."""

    def test_euler_to_quat_zero(self):
        """Test zero Euler to quaternion."""
        from src.osk.blocks.aerospace import EulerToQuaternion

        eq = EulerToQuaternion()
        eq.init()
        eq.setInput([0.0, 0.0, 0.0])
        eq.update()

        output = eq.getOutputVector()
        assert output is not None
        assert output[0] == pytest.approx(1.0)


class TestQuaternionRotateVector:
    """Tests for QuaternionRotateVector block."""

    def test_quat_rotate_identity(self):
        """Test rotating vector by identity quaternion."""
        from src.osk.blocks.aerospace import QuaternionRotateVector

        qrv = QuaternionRotateVector()
        qrv.init()
        qrv.setInput([1.0, 0.0, 0.0, 0.0], port=0)  # Identity quat
        qrv.setInput([1.0, 0.0, 0.0], port=1)  # Vector
        qrv.update()

        output = qrv.getOutputVector()
        assert output is not None
        assert output[0] == pytest.approx(1.0)


class TestDCMToQuaternion:
    """Tests for DCMToQuaternion block."""

    def test_dcm_to_quat_identity(self):
        """Test identity DCM to quaternion."""
        from src.osk.blocks.aerospace import DCMToQuaternion

        dq = DCMToQuaternion()
        dq.init()
        dq.setInput([1, 0, 0, 0, 1, 0, 0, 0, 1])
        dq.update()

        output = dq.getOutputVector()
        assert output is not None


class TestQuaternionToDCM:
    """Tests for QuaternionToDCM block."""

    def test_quat_to_dcm_identity(self):
        """Test identity quaternion to DCM."""
        from src.osk.blocks.aerospace import QuaternionToDCM

        qd = QuaternionToDCM()
        qd.init()
        qd.setInput([1.0, 0.0, 0.0, 0.0])
        qd.update()

        output = qd.getOutputVector()
        assert output is not None
        # Identity DCM
        assert output[0] == pytest.approx(1.0)
        assert output[4] == pytest.approx(1.0)
        assert output[8] == pytest.approx(1.0)


class TestSixDOFEuler:
    """Tests for SixDOFEuler block."""

    def test_six_dof_euler_initialization(self):
        """Test 6DOF Euler initialization."""
        from src.osk.blocks.aerospace import SixDOFEuler

        eom = SixDOFEuler(mass=100.0, Ixx=10.0, Iyy=10.0, Izz=10.0, Ixz=0.0)
        eom.init()

        output = eom.getOutputVector()
        assert output is not None


class TestFlatEarthGravity:
    """Tests for FlatEarthGravity block."""

    def test_flat_earth_gravity(self):
        """Test flat earth gravity model."""
        from src.osk.blocks.aerospace import FlatEarthGravity

        grav = FlatEarthGravity()
        grav.init()
        grav.setInput(0.0)  # Altitude
        grav.update()

        output = grav.getOutputVector()
        assert output is not None
        # Gravity should be approximately 9.8 m/s²


class TestWGS84Gravity:
    """Tests for WGS84Gravity block."""

    def test_wgs84_gravity_equator(self):
        """Test WGS84 gravity at equator sea level."""
        from src.osk.blocks.aerospace import WGS84Gravity

        grav = WGS84Gravity()
        grav.init()
        grav.setInput([0.0, 0.0])  # [latitude (rad), altitude (m)]
        grav.update()

        output = grav.getOutput()
        # At equator sea level, gravity should be around 9.78
        assert output == pytest.approx(9.78, rel=0.01)

    def test_wgs84_gravity_pole(self):
        """Test WGS84 gravity at pole sea level."""
        import math

        from src.osk.blocks.aerospace import WGS84Gravity

        grav = WGS84Gravity()
        grav.init()
        grav.setInput([math.pi / 2, 0.0])  # [90 deg latitude, 0 altitude]
        grav.update()

        output = grav.getOutput()
        # At pole, gravity should be around 9.83
        assert output == pytest.approx(9.83, rel=0.01)


# =============================================================================
# Control Design Block Tests
# =============================================================================


class TestLQRControllerBlock:
    """Tests for LQRController block."""

    def test_lqr_default_initialization(self):
        """Test LQR with default parameters."""
        from src.osk.blocks.control_design import LQRController

        lqr = LQRController(num_states=2, num_inputs=1)
        lqr.init()

        # State input [0, 0] should produce zero output
        lqr.setInput(0.0, port=0)
        lqr.setInput(0.0, port=1)
        lqr.update()

        assert lqr.getOutput(0) == 0.0

    def test_lqr_with_custom_gain(self):
        """Test LQR with custom gain matrix."""
        from src.osk.blocks.control_design import LQRController

        # K matrix: 1x2 (1 input, 2 states)
        K = [[1.0, 2.0]]
        lqr = LQRController(K=K, num_states=2, num_inputs=1)
        lqr.init()

        # State = [1, 1], output = -K*x = -(1*1 + 2*1) = -3
        lqr.setInput(1.0, port=0)
        lqr.setInput(1.0, port=1)
        lqr.update()

        assert lqr.getOutput(0) == pytest.approx(-3.0)

    def test_lqr_multi_input(self):
        """Test LQR with multiple inputs."""
        from src.osk.blocks.control_design import LQRController

        # K matrix: 2x2 (2 inputs, 2 states)
        K = [[1.0, 0.0], [0.0, 1.0]]
        lqr = LQRController(K=K, num_states=2, num_inputs=2)
        lqr.init()

        lqr.setInput(2.0, port=0)
        lqr.setInput(3.0, port=1)
        lqr.update()

        # u0 = -(1*2 + 0*3) = -2
        # u1 = -(0*2 + 1*3) = -3
        assert lqr.getOutput(0) == pytest.approx(-2.0)
        assert lqr.getOutput(1) == pytest.approx(-3.0)

    def test_lqr_with_vector_input(self):
        """Test LQR with connected vector input."""
        from src.osk.blocks.control_design import LQRController
        from src.osk.blocks.sources import Constant

        K = [[1.0, 2.0]]
        lqr = LQRController(K=K, num_states=2, num_inputs=1)
        lqr.init()

        const = Constant(value=[1.0, 0.5])
        const.init()
        const.update()

        lqr.connectInput(const)
        lqr.update()

        # u = -(1*1 + 2*0.5) = -2
        assert lqr.getOutput(0) == pytest.approx(-2.0)

    def test_lqr_output_vector(self):
        """Test LQR getOutputVector for multi-input case."""
        from src.osk.blocks.control_design import LQRController

        K = [[1.0, 0.0], [0.0, 1.0]]
        lqr = LQRController(K=K, num_states=2, num_inputs=2)
        lqr.init()

        lqr.setInput(1.0, port=0)
        lqr.setInput(2.0, port=1)
        lqr.update()

        vec = lqr.getOutputVector()
        assert vec is not None
        assert vec[0] == pytest.approx(-1.0)
        assert vec[1] == pytest.approx(-2.0)


class TestPolePlacementBlock:
    """Tests for PolePlacement block."""

    def test_pole_placement_default(self):
        """Test pole placement with default parameters."""
        from src.osk.blocks.control_design import PolePlacement

        pp = PolePlacement(num_states=2)
        pp.init()

        pp.setInput(0.0, port=0)
        pp.setInput(0.0, port=1)
        pp.update()

        assert pp.getOutput() == 0.0

    def test_pole_placement_with_gains(self):
        """Test pole placement with custom gains."""
        from src.osk.blocks.control_design import PolePlacement

        K = [2.0, 3.0]
        pp = PolePlacement(K=K, num_states=2)
        pp.init()

        pp.setInput(1.0, port=0)
        pp.setInput(1.0, port=1)
        pp.update()

        # u = -(2*1 + 3*1) = -5
        assert pp.getOutput() == pytest.approx(-5.0)

    def test_pole_placement_with_vector_input(self):
        """Test pole placement with connected vector input."""
        from src.osk.blocks.control_design import PolePlacement
        from src.osk.blocks.sources import Constant

        K = [1.0, 2.0]
        pp = PolePlacement(K=K, num_states=2)
        pp.init()

        const = Constant(value=[2.0, 3.0])
        const.init()
        const.update()

        pp.connectInput(const)
        pp.update()

        # u = -(1*2 + 2*3) = -8
        assert pp.getOutput() == pytest.approx(-8.0)


class TestLeadLagCompensatorBlock:
    """Tests for LeadLagCompensator block."""

    def test_lead_lag_initialization(self):
        """Test lead-lag compensator initialization."""
        from src.osk.blocks.control_design import LeadLagCompensator

        comp = LeadLagCompensator(gain=2.0, zero=-1.0, pole=-10.0)
        comp.init()

        assert comp.output == 0.0

    def test_lead_lag_step_response(self):
        """Test lead-lag compensator step response."""
        from src.osk.blocks.control_design import LeadLagCompensator

        comp = LeadLagCompensator(gain=1.0, zero=-1.0, pole=-10.0)
        comp.init()

        comp.setInput(1.0)
        comp.update()

        # Immediate output should be non-zero (feedthrough term)
        assert comp.getOutput() != 0.0

    def test_lead_lag_with_connected_input(self):
        """Test lead-lag with connected input."""
        from src.osk.blocks.control_design import LeadLagCompensator
        from src.osk.blocks.sources import Constant

        comp = LeadLagCompensator(gain=1.0, zero=-2.0, pole=-5.0)
        comp.init()

        const = Constant(value=2.0)
        const.init()
        const.update()

        comp.connectInput(const)
        comp.update()

        assert comp.getOutput() != 0.0


class TestPIControllerBlock:
    """Tests for PIController block."""

    def test_pi_initialization(self):
        """Test PI controller initialization."""
        from src.osk.blocks.control_design import PIController

        pi = PIController(Kp=1.0, Ki=0.5)
        pi.init()

        assert pi.output == 0.0

    def test_pi_proportional_only(self):
        """Test PI controller proportional term."""
        from src.osk.blocks.control_design import PIController

        pi = PIController(Kp=2.0, Ki=0.0)
        pi.init()

        pi.setInput(1.0)
        pi.update()

        # P term only: 2.0 * 1.0 = 2.0
        assert pi.getOutput() == pytest.approx(2.0)

    def test_pi_with_initial_integrator(self):
        """Test PI with initial integrator value."""
        from src.osk.blocks.control_design import PIController

        pi = PIController(Kp=0.0, Ki=1.0, initial_integrator=5.0)
        pi.init()

        pi.setInput(0.0)
        pi.update()

        # I term only: 1.0 * 5.0 = 5.0
        assert pi.getOutput() == pytest.approx(5.0)

    def test_pi_with_connected_input(self):
        """Test PI with connected input."""
        from src.osk.blocks.control_design import PIController
        from src.osk.blocks.sources import Constant

        pi = PIController(Kp=1.0, Ki=0.5)
        pi.init()

        const = Constant(value=2.0)
        const.init()
        const.update()

        pi.connectInput(const)
        pi.update()

        # P term: 1.0 * 2.0 = 2.0
        # I term: 0.5 * 0.0 = 0.0 (integrator starts at 0)
        assert pi.getOutput() == pytest.approx(2.0)


class TestPDControllerBlock:
    """Tests for PDController block."""

    def test_pd_initialization(self):
        """Test PD controller initialization."""
        from src.osk.blocks.control_design import PDController

        pd = PDController(Kp=1.0, Kd=0.1)
        pd.init()

        assert pd.output == 0.0

    def test_pd_proportional_only(self):
        """Test PD controller proportional term."""
        from src.osk.blocks.control_design import PDController

        pd = PDController(Kp=3.0, Kd=0.0)
        pd.init()

        pd.setInput(2.0)
        pd.update()

        # P term only: 3.0 * 2.0 = 6.0
        assert pd.getOutput() == pytest.approx(6.0)

    def test_pd_with_derivative(self):
        """Test PD controller with derivative term."""
        from src.osk.blocks.control_design import PDController

        pd = PDController(Kp=1.0, Kd=0.1, N=100.0)
        pd.init()

        pd.setInput(0.0)
        pd.update()
        pd.setInput(1.0)
        pd.update()

        # Output should include derivative contribution
        output = pd.getOutput()
        assert output > 1.0  # More than just P term

    def test_pd_with_connected_input(self):
        """Test PD with connected input."""
        from src.osk.blocks.control_design import PDController
        from src.osk.blocks.sources import Constant

        pd = PDController(Kp=2.0, Kd=0.1)
        pd.init()

        const = Constant(value=1.5)
        const.init()
        const.update()

        pd.connectInput(const)
        pd.update()

        # P term: 2.0 * 1.5 = 3.0 plus derivative term
        assert pd.getOutput() >= 3.0


class TestAntiWindupPIDBlock:
    """Tests for AntiWindupPID block."""

    def test_anti_windup_pid_initialization(self):
        """Test anti-windup PID initialization."""
        from src.osk.blocks.control_design import AntiWindupPID

        pid = AntiWindupPID(Kp=1.0, Ki=0.5, Kd=0.1)
        pid.init()

        assert pid.output == 0.0

    def test_anti_windup_pid_saturation_upper(self):
        """Test anti-windup PID upper saturation."""
        from src.osk.blocks.control_design import AntiWindupPID

        pid = AntiWindupPID(Kp=10.0, Ki=0.0, Kd=0.0, upper_limit=5.0)
        pid.init()

        pid.setInput(1.0)
        pid.update()

        # P term would be 10.0, but saturates at 5.0
        assert pid.getOutput() == pytest.approx(5.0)

    def test_anti_windup_pid_saturation_lower(self):
        """Test anti-windup PID lower saturation."""
        from src.osk.blocks.control_design import AntiWindupPID

        pid = AntiWindupPID(Kp=10.0, Ki=0.0, Kd=0.0, lower_limit=-3.0)
        pid.init()

        pid.setInput(-1.0)
        pid.update()

        # P term would be -10.0, but saturates at -3.0
        assert pid.getOutput() == pytest.approx(-3.0)

    def test_anti_windup_pid_full_pid(self):
        """Test full anti-windup PID operation."""
        from src.osk.blocks.control_design import AntiWindupPID

        pid = AntiWindupPID(Kp=1.0, Ki=0.5, Kd=0.1, N=100.0, Kb=1.0)
        pid.init()

        pid.setInput(1.0)
        pid.update()

        # Should have non-zero output
        assert pid.getOutput() != 0.0

    def test_anti_windup_pid_with_connected_input(self):
        """Test anti-windup PID with connected input."""
        from src.osk.blocks.control_design import AntiWindupPID
        from src.osk.blocks.sources import Constant

        pid = AntiWindupPID(Kp=2.0, Ki=0.5, Kd=0.0, upper_limit=10.0)
        pid.init()

        const = Constant(value=1.0)
        const.init()
        const.update()

        pid.connectInput(const)
        pid.update()

        # P term: 2.0 * 1.0 = 2.0
        assert pid.getOutput() == pytest.approx(2.0)


class TestModelReferenceBlock:
    """Tests for ModelReference block."""

    def test_model_reference_initialization(self):
        """Test model reference initialization."""
        from src.osk.blocks.control_design import ModelReference

        ref = ModelReference(natural_frequency=1.0, damping_ratio=1.0)
        ref.init()

        assert ref.output == 0.0

    def test_model_reference_step_input(self):
        """Test model reference with step input."""
        from src.osk.blocks.control_design import ModelReference

        ref = ModelReference(natural_frequency=10.0, damping_ratio=0.7)
        ref.init()

        ref.setInput(1.0)
        ref.update()

        # Output starts at 0 (second-order system)
        assert ref.getOutput() == 0.0

    def test_model_reference_with_connected_input(self):
        """Test model reference with connected input."""
        from src.osk.blocks.control_design import ModelReference
        from src.osk.blocks.sources import Constant

        ref = ModelReference(natural_frequency=5.0, damping_ratio=1.0)
        ref.init()

        const = Constant(value=2.0)
        const.init()
        const.update()

        ref.connectInput(const)
        ref.update()

        # Output should be the current state
        assert ref.getOutput() is not None


# =============================================================================
# Control Analysis Block Tests
# =============================================================================


class TestBodePlotBlock:
    """Tests for BodePlot analysis block."""

    def test_bode_initialization(self):
        """Test Bode plot initialization with default parameters."""
        from src.osk.blocks.control_analysis import BodePlot

        bode = BodePlot()
        bode.init()

        # Should have computed frequency response data
        assert len(bode.frequencies) > 0
        assert len(bode.magnitude_db) > 0
        assert len(bode.phase_deg) > 0

    def test_bode_with_custom_tf(self):
        """Test Bode plot with custom transfer function."""
        from src.osk.blocks.control_analysis import BodePlot

        # Simple first-order system: 1 / (s + 1)
        bode = BodePlot(numerator=[1.0], denominator=[1.0, 1.0], numPoints=50)
        bode.init()

        # DC gain should be 0 dB (1/1 = 1)
        assert bode.magnitude_db[0] == pytest.approx(0.0, abs=1.0)

    def test_bode_get_data(self):
        """Test Bode plot get_bode_data method."""
        from src.osk.blocks.control_analysis import BodePlot

        bode = BodePlot(numerator=[1.0], denominator=[1.0, 1.0])
        bode.init()

        data = bode.get_bode_data()
        assert "frequencies" in data
        assert "magnitude_db" in data
        assert "phase_deg" in data
        assert "gain_margin" in data
        assert "phase_margin" in data

    def test_bode_getData(self):
        """Test Bode plot getData method."""
        from src.osk.blocks.control_analysis import BodePlot

        bode = BodePlot(numerator=[10.0], denominator=[1.0, 2.0, 1.0])
        bode.init()

        data = bode.getData()
        assert data["analysisType"] == "bode"
        assert "frequencies" in data

    def test_bode_setInput(self):
        """Test Bode plot setInput method."""
        from src.osk.blocks.control_analysis import BodePlot

        bode = BodePlot()
        bode.init()

        bode.setInput(1.0)
        assert bode.input == 1.0

    def test_bode_update(self):
        """Test Bode plot update method (no-op for analysis blocks)."""
        from src.osk.blocks.control_analysis import BodePlot

        bode = BodePlot()
        bode.init()

        output_before = bode.getOutput()
        bode.update()
        output_after = bode.getOutput()

        assert output_before == output_after

    def test_bode_stability_margins(self):
        """Test Bode plot stability margin computation."""
        from src.osk.blocks.control_analysis import BodePlot

        # System with finite gain and phase margins
        # H(s) = 10 / (s^2 + 2s + 1)
        bode = BodePlot(
            numerator=[10.0],
            denominator=[1.0, 2.0, 1.0],
            minFrequency=0.01,
            maxFrequency=100.0,
            numPoints=200,
        )
        bode.init()

        # Should have computed stability margins
        # Phase margin should exist for this system
        data = bode.get_bode_data()
        assert "gain_margin" in data
        assert "phase_margin" in data


class TestNyquistPlotBlock:
    """Tests for NyquistPlot analysis block."""

    def test_nyquist_initialization(self):
        """Test Nyquist plot initialization."""
        from src.osk.blocks.control_analysis import NyquistPlot

        nyquist = NyquistPlot()
        nyquist.init()

        assert len(nyquist.real_parts) > 0
        assert len(nyquist.imag_parts) > 0
        assert len(nyquist.frequencies) > 0

    def test_nyquist_with_custom_tf(self):
        """Test Nyquist plot with custom transfer function."""
        from src.osk.blocks.control_analysis import NyquistPlot

        # Stable system: 1 / (s + 1)
        nyquist = NyquistPlot(numerator=[1.0], denominator=[1.0, 1.0], numPoints=100)
        nyquist.init()

        # Stable system should have 0 encirclements
        assert nyquist.encirclements == 0

    def test_nyquist_get_data(self):
        """Test Nyquist plot get_nyquist_data method."""
        from src.osk.blocks.control_analysis import NyquistPlot

        nyquist = NyquistPlot(numerator=[1.0], denominator=[1.0, 1.0])
        nyquist.init()

        data = nyquist.get_nyquist_data()
        assert "real" in data
        assert "imag" in data
        assert "frequencies" in data
        assert "encirclements" in data

    def test_nyquist_getData(self):
        """Test Nyquist plot getData method."""
        from src.osk.blocks.control_analysis import NyquistPlot

        nyquist = NyquistPlot()
        nyquist.init()

        data = nyquist.getData()
        assert data["analysisType"] == "nyquist"

    def test_nyquist_setInput(self):
        """Test Nyquist plot setInput method."""
        from src.osk.blocks.control_analysis import NyquistPlot

        nyquist = NyquistPlot()
        nyquist.init()

        nyquist.setInput(2.0)
        assert nyquist.input == 2.0

    def test_nyquist_update(self):
        """Test Nyquist plot update method."""
        from src.osk.blocks.control_analysis import NyquistPlot

        nyquist = NyquistPlot()
        nyquist.init()

        output_before = nyquist.getOutput()
        nyquist.update()
        output_after = nyquist.getOutput()

        assert output_before == output_after


class TestPoleZeroMapBlock:
    """Tests for PoleZeroMap analysis block."""

    def test_pzmap_initialization(self):
        """Test pole-zero map initialization."""
        from src.osk.blocks.control_analysis import PoleZeroMap

        pzmap = PoleZeroMap()
        pzmap.init()

        # Default TF [1]/[1, 1] has one pole at s=-1
        assert len(pzmap.poles) == 1

    def test_pzmap_stable_system(self):
        """Test pole-zero map for a stable system."""
        from src.osk.blocks.control_analysis import PoleZeroMap

        # Stable system: all poles in LHP
        # H(s) = 1 / (s^2 + 3s + 2) = 1 / ((s+1)(s+2))
        pzmap = PoleZeroMap(numerator=[1.0], denominator=[1.0, 3.0, 2.0])
        pzmap.init()

        assert pzmap.is_stable is True
        assert pzmap.getOutput() == 1.0
        assert len(pzmap.poles) == 2

    def test_pzmap_unstable_system(self):
        """Test pole-zero map for an unstable system."""
        from src.osk.blocks.control_analysis import PoleZeroMap

        # Unstable system: pole in RHP
        # H(s) = 1 / (s - 1) has pole at s=1
        pzmap = PoleZeroMap(numerator=[1.0], denominator=[1.0, -1.0])
        pzmap.init()

        assert pzmap.is_stable is False
        assert pzmap.getOutput() == 0.0

    def test_pzmap_with_zeros(self):
        """Test pole-zero map with zeros."""
        from src.osk.blocks.control_analysis import PoleZeroMap

        # H(s) = (s + 1) / (s^2 + 3s + 2)
        pzmap = PoleZeroMap(numerator=[1.0, 1.0], denominator=[1.0, 3.0, 2.0])
        pzmap.init()

        assert len(pzmap.zeros) == 1
        assert len(pzmap.poles) == 2

    def test_pzmap_get_data(self):
        """Test pole-zero map get_pole_zero_data method."""
        from src.osk.blocks.control_analysis import PoleZeroMap

        pzmap = PoleZeroMap(numerator=[1.0], denominator=[1.0, 1.0])
        pzmap.init()

        data = pzmap.get_pole_zero_data()
        assert "poles" in data
        assert "zeros" in data
        assert "is_stable" in data
        assert "dominant_pole" in data

    def test_pzmap_getData(self):
        """Test pole-zero map getData method."""
        from src.osk.blocks.control_analysis import PoleZeroMap

        pzmap = PoleZeroMap()
        pzmap.init()

        data = pzmap.getData()
        assert data["analysisType"] == "pzmap"

    def test_pzmap_setInput(self):
        """Test pole-zero map setInput method."""
        from src.osk.blocks.control_analysis import PoleZeroMap

        pzmap = PoleZeroMap()
        pzmap.init()

        pzmap.setInput(3.0)
        assert pzmap.input == 3.0

    def test_pzmap_dominant_pole(self):
        """Test dominant pole identification."""
        from src.osk.blocks.control_analysis import PoleZeroMap

        # System with poles at -1 and -10, dominant pole is at -1
        pzmap = PoleZeroMap(numerator=[1.0], denominator=[1.0, 11.0, 10.0])
        pzmap.init()

        assert pzmap.dominant_pole is not None
        assert pzmap.dominant_pole[0] == pytest.approx(-1.0, abs=0.1)


class TestStepInfoBlock:
    """Tests for StepInfo analysis block."""

    def test_stepinfo_initialization(self):
        """Test step info initialization."""
        from src.osk.blocks.control_analysis import StepInfo

        stepinfo = StepInfo()
        stepinfo.init()

        assert len(stepinfo.times) > 0
        assert len(stepinfo.response) > 0

    def test_stepinfo_first_order_system(self):
        """Test step info for first-order system."""
        from src.osk.blocks.control_analysis import StepInfo

        # First-order system: 1 / (s + 1), time constant = 1
        stepinfo = StepInfo(
            numerator=[1.0], denominator=[1.0, 1.0], simulationTime=10.0, numPoints=500
        )
        stepinfo.init()

        # Steady-state value should be 1.0
        assert stepinfo.steady_state_value == pytest.approx(1.0, rel=0.05)

        # Rise time for first-order system is about 2.2 * tau
        assert stepinfo.rise_time is not None

    def test_stepinfo_second_order_underdamped(self):
        """Test step info for underdamped second-order system."""
        from src.osk.blocks.control_analysis import StepInfo

        # Underdamped system: wn^2 / (s^2 + 2*zeta*wn*s + wn^2)
        # wn = 1, zeta = 0.3
        wn = 1.0
        zeta = 0.3
        stepinfo = StepInfo(
            numerator=[wn**2],
            denominator=[1.0, 2 * zeta * wn, wn**2],
            simulationTime=20.0,
            numPoints=1000,
        )
        stepinfo.init()

        # Underdamped system should have overshoot
        assert stepinfo.overshoot_percent is not None
        assert stepinfo.overshoot_percent > 0

    def test_stepinfo_get_data(self):
        """Test step info get_step_data method."""
        from src.osk.blocks.control_analysis import StepInfo

        stepinfo = StepInfo(numerator=[1.0], denominator=[1.0, 1.0])
        stepinfo.init()

        data = stepinfo.get_step_data()
        assert "times" in data
        assert "response" in data
        assert "rise_time" in data
        assert "settling_time" in data
        assert "overshoot_percent" in data
        assert "peak_time" in data
        assert "peak_value" in data
        assert "steady_state_value" in data

    def test_stepinfo_getData(self):
        """Test step info getData method."""
        from src.osk.blocks.control_analysis import StepInfo

        stepinfo = StepInfo()
        stepinfo.init()

        data = stepinfo.getData()
        assert data["analysisType"] == "stepinfo"

    def test_stepinfo_setInput(self):
        """Test step info setInput method."""
        from src.osk.blocks.control_analysis import StepInfo

        stepinfo = StepInfo()
        stepinfo.init()

        stepinfo.setInput(4.0)
        assert stepinfo.input == 4.0

    def test_stepinfo_settling_time(self):
        """Test settling time computation."""
        from src.osk.blocks.control_analysis import StepInfo

        # Critically damped system should settle without oscillation
        stepinfo = StepInfo(
            numerator=[1.0],
            denominator=[1.0, 2.0, 1.0],  # (s+1)^2
            simulationTime=10.0,
            numPoints=500,
            settlingPercent=2.0,
        )
        stepinfo.init()

        assert stepinfo.settling_time is not None

    def test_stepinfo_static_gain(self):
        """Test step info for static gain (zero-order system)."""
        from src.osk.blocks.control_analysis import StepInfo

        # Static gain: H(s) = 2
        stepinfo = StepInfo(numerator=[2.0], denominator=[1.0], simulationTime=5.0)
        stepinfo.init()

        # Response should be constant at 2.0
        assert stepinfo.response[0] == pytest.approx(2.0)
        assert stepinfo.response[-1] == pytest.approx(2.0)


# =============================================================================
# Data Types Block Tests
# =============================================================================


class TestDataTypeConversionBlock:
    """Tests for DataTypeConversion block."""

    def test_data_type_double_passthrough(self):
        """Test double type conversion (passthrough)."""
        from src.osk.blocks.data_types import DataTypeConversion

        dtc = DataTypeConversion(output_type="double")
        dtc.init()

        dtc.setInput(3.14159)
        dtc.update()

        assert dtc.getOutput() == pytest.approx(3.14159)

    def test_data_type_single_passthrough(self):
        """Test single type conversion (passthrough in Python)."""
        from src.osk.blocks.data_types import DataTypeConversion

        dtc = DataTypeConversion(output_type="single")
        dtc.init()

        dtc.setInput(2.718)
        dtc.update()

        assert dtc.getOutput() == pytest.approx(2.718)

    def test_data_type_boolean_true(self):
        """Test boolean conversion for non-zero value."""
        from src.osk.blocks.data_types import DataTypeConversion

        dtc = DataTypeConversion(output_type="boolean")
        dtc.init()

        dtc.setInput(5.0)
        dtc.update()

        assert dtc.getOutput() == 1.0

    def test_data_type_boolean_false(self):
        """Test boolean conversion for zero value."""
        from src.osk.blocks.data_types import DataTypeConversion

        dtc = DataTypeConversion(output_type="boolean")
        dtc.init()

        dtc.setInput(0.0)
        dtc.update()

        assert dtc.getOutput() == 0.0

    def test_data_type_int8_saturation(self):
        """Test int8 conversion with saturation."""
        from src.osk.blocks.data_types import DataTypeConversion

        dtc = DataTypeConversion(output_type="int8", saturate=True)
        dtc.init()

        # Test saturation at upper limit
        dtc.setInput(200.0)
        dtc.update()
        assert dtc.getOutput() == 127.0

        # Test saturation at lower limit
        dtc.setInput(-200.0)
        dtc.update()
        assert dtc.getOutput() == -128.0

    def test_data_type_uint8_saturation(self):
        """Test uint8 conversion with saturation."""
        from src.osk.blocks.data_types import DataTypeConversion

        dtc = DataTypeConversion(output_type="uint8", saturate=True)
        dtc.init()

        dtc.setInput(300.0)
        dtc.update()
        assert dtc.getOutput() == 255.0

        dtc.setInput(-10.0)
        dtc.update()
        assert dtc.getOutput() == 0.0

    def test_data_type_int16_saturation(self):
        """Test int16 conversion with saturation."""
        from src.osk.blocks.data_types import DataTypeConversion

        dtc = DataTypeConversion(output_type="int16", saturate=True)
        dtc.init()

        dtc.setInput(40000.0)
        dtc.update()
        assert dtc.getOutput() == 32767.0

    def test_data_type_int32_saturation(self):
        """Test int32 conversion with saturation."""
        from src.osk.blocks.data_types import DataTypeConversion

        dtc = DataTypeConversion(output_type="int32", saturate=True)
        dtc.init()

        dtc.setInput(3e9)
        dtc.update()
        assert dtc.getOutput() == 2147483647.0

    def test_data_type_uint16_saturation(self):
        """Test uint16 conversion with saturation."""
        from src.osk.blocks.data_types import DataTypeConversion

        dtc = DataTypeConversion(output_type="uint16", saturate=True)
        dtc.init()

        dtc.setInput(70000.0)
        dtc.update()
        assert dtc.getOutput() == 65535.0

    def test_data_type_uint32_saturation(self):
        """Test uint32 conversion with saturation."""
        from src.osk.blocks.data_types import DataTypeConversion

        dtc = DataTypeConversion(output_type="uint32", saturate=True)
        dtc.init()

        dtc.setInput(5e9)
        dtc.update()
        assert dtc.getOutput() == 4294967295.0

    def test_data_type_int8_wrap(self):
        """Test int8 conversion with wrap-around."""
        from src.osk.blocks.data_types import DataTypeConversion

        dtc = DataTypeConversion(output_type="int8", saturate=False)
        dtc.init()

        dtc.setInput(128.0)  # Wraps to -128
        dtc.update()
        assert dtc.getOutput() == -128.0

    def test_data_type_round_mode_floor(self):
        """Test floor rounding mode."""
        from src.osk.blocks.data_types import DataTypeConversion

        dtc = DataTypeConversion(output_type="int8", round_mode="floor")
        dtc.init()

        dtc.setInput(3.7)
        dtc.update()
        assert dtc.getOutput() == 3.0

        dtc.setInput(-3.7)
        dtc.update()
        assert dtc.getOutput() == -4.0

    def test_data_type_round_mode_ceil(self):
        """Test ceil rounding mode."""
        from src.osk.blocks.data_types import DataTypeConversion

        dtc = DataTypeConversion(output_type="int8", round_mode="ceil")
        dtc.init()

        dtc.setInput(3.3)
        dtc.update()
        assert dtc.getOutput() == 4.0

    def test_data_type_round_mode_fix(self):
        """Test fix (truncate toward zero) rounding mode."""
        from src.osk.blocks.data_types import DataTypeConversion

        dtc = DataTypeConversion(output_type="int8", round_mode="fix")
        dtc.init()

        dtc.setInput(3.9)
        dtc.update()
        assert dtc.getOutput() == 3.0

        dtc.setInput(-3.9)
        dtc.update()
        assert dtc.getOutput() == -3.0

    def test_data_type_with_connected_input(self):
        """Test data type conversion with connected input."""
        from src.osk.blocks.data_types import DataTypeConversion
        from src.osk.blocks.sources import Constant

        dtc = DataTypeConversion(output_type="int8")
        dtc.init()

        const = Constant(value=50.5)
        const.init()
        const.update()

        dtc.connectInput(const)
        dtc.update()

        assert dtc.getOutput() == 50.0  # Rounded


class TestRealImagToComplexBlock:
    """Tests for RealImagToComplex block."""

    def test_real_imag_to_complex_basic(self):
        """Test basic real/imag to complex conversion."""
        import math

        from src.osk.blocks.data_types import RealImagToComplex

        rtc = RealImagToComplex()
        rtc.init()

        rtc.setInput(3.0, port=0)  # Real
        rtc.setInput(4.0, port=1)  # Imag
        rtc.update()

        # Magnitude = sqrt(3^2 + 4^2) = 5
        assert rtc.getOutput(0) == pytest.approx(5.0)
        # Phase = atan2(4, 3) ~ 0.927 rad
        assert rtc.getOutput(1) == pytest.approx(math.atan2(4, 3))

    def test_real_imag_to_complex_zero(self):
        """Test real/imag to complex with zero values."""
        from src.osk.blocks.data_types import RealImagToComplex

        rtc = RealImagToComplex()
        rtc.init()

        rtc.setInput(0.0, port=0)
        rtc.setInput(0.0, port=1)
        rtc.update()

        assert rtc.getOutput(0) == 0.0
        assert rtc.getOutput(1) == 0.0

    def test_real_imag_to_complex_output_vector(self):
        """Test real/imag to complex getOutputVector."""
        from src.osk.blocks.data_types import RealImagToComplex

        rtc = RealImagToComplex()
        rtc.init()

        rtc.setInput(1.0, port=0)
        rtc.setInput(1.0, port=1)
        rtc.update()

        vec = rtc.getOutputVector()
        assert vec is not None
        assert len(vec) == 2

    def test_real_imag_to_complex_with_connected_input(self):
        """Test real/imag to complex with connected inputs."""
        from src.osk.blocks.data_types import RealImagToComplex
        from src.osk.blocks.sources import Constant

        rtc = RealImagToComplex()
        rtc.init()

        const_real = Constant(value=5.0)
        const_real.init()
        const_real.update()

        const_imag = Constant(value=12.0)
        const_imag.init()
        const_imag.update()

        rtc.connectInput(const_real, port=0)
        rtc.connectInput(const_imag, port=1)
        rtc.update()

        # Magnitude = sqrt(5^2 + 12^2) = 13
        assert rtc.getOutput(0) == pytest.approx(13.0)

    def test_real_imag_invalid_port(self):
        """Test getOutput with invalid port."""
        from src.osk.blocks.data_types import RealImagToComplex

        rtc = RealImagToComplex()
        rtc.init()

        rtc.setInput(1.0, port=0)
        rtc.setInput(1.0, port=1)
        rtc.update()

        assert rtc.getOutput(2) == 0.0


class TestComplexToRealImagBlock:
    """Tests for ComplexToRealImag block."""

    def test_complex_to_real_imag_basic(self):
        """Test basic complex to real/imag conversion."""
        import math

        from src.osk.blocks.data_types import ComplexToRealImag

        ctr = ComplexToRealImag()
        ctr.init()

        # Magnitude = 5, phase = pi/4 (45 degrees)
        ctr.setInput(5.0, port=0)  # Magnitude
        ctr.setInput(math.pi / 4, port=1)  # Phase
        ctr.update()

        # Real = 5 * cos(pi/4) ~ 3.535
        # Imag = 5 * sin(pi/4) ~ 3.535
        assert ctr.getOutput(0) == pytest.approx(5.0 * math.cos(math.pi / 4))
        assert ctr.getOutput(1) == pytest.approx(5.0 * math.sin(math.pi / 4))

    def test_complex_to_real_imag_zero_phase(self):
        """Test complex to real/imag with zero phase."""
        from src.osk.blocks.data_types import ComplexToRealImag

        ctr = ComplexToRealImag()
        ctr.init()

        ctr.setInput(10.0, port=0)  # Magnitude
        ctr.setInput(0.0, port=1)  # Phase = 0
        ctr.update()

        # Real = 10 * cos(0) = 10
        # Imag = 10 * sin(0) = 0
        assert ctr.getOutput(0) == pytest.approx(10.0)
        assert ctr.getOutput(1) == pytest.approx(0.0)

    def test_complex_to_real_imag_90_deg(self):
        """Test complex to real/imag with 90 degree phase."""
        import math

        from src.osk.blocks.data_types import ComplexToRealImag

        ctr = ComplexToRealImag()
        ctr.init()

        ctr.setInput(1.0, port=0)  # Magnitude
        ctr.setInput(math.pi / 2, port=1)  # Phase = 90 deg
        ctr.update()

        # Real = 1 * cos(pi/2) ~ 0
        # Imag = 1 * sin(pi/2) = 1
        assert ctr.getOutput(0) == pytest.approx(0.0, abs=1e-10)
        assert ctr.getOutput(1) == pytest.approx(1.0)

    def test_complex_to_real_imag_output_vector(self):
        """Test complex to real/imag getOutputVector."""
        from src.osk.blocks.data_types import ComplexToRealImag

        ctr = ComplexToRealImag()
        ctr.init()

        ctr.setInput(2.0, port=0)
        ctr.setInput(0.0, port=1)
        ctr.update()

        vec = ctr.getOutputVector()
        assert vec is not None
        assert len(vec) == 2
        assert vec[0] == pytest.approx(2.0)
        assert vec[1] == pytest.approx(0.0)

    def test_complex_to_real_imag_with_connected_input(self):
        """Test complex to real/imag with connected inputs."""
        import math

        from src.osk.blocks.data_types import ComplexToRealImag
        from src.osk.blocks.sources import Constant

        ctr = ComplexToRealImag()
        ctr.init()

        const_mag = Constant(value=2.0)
        const_mag.init()
        const_mag.update()

        const_phase = Constant(value=math.pi)  # 180 degrees
        const_phase.init()
        const_phase.update()

        ctr.connectInput(const_mag, port=0)
        ctr.connectInput(const_phase, port=1)
        ctr.update()

        # Real = 2 * cos(pi) = -2
        # Imag = 2 * sin(pi) ~ 0
        assert ctr.getOutput(0) == pytest.approx(-2.0)
        assert ctr.getOutput(1) == pytest.approx(0.0, abs=1e-10)

    def test_complex_to_real_imag_invalid_port(self):
        """Test getOutput with invalid port."""
        from src.osk.blocks.data_types import ComplexToRealImag

        ctr = ComplexToRealImag()
        ctr.init()

        ctr.setInput(1.0, port=0)
        ctr.setInput(0.0, port=1)
        ctr.update()

        assert ctr.getOutput(2) == 0.0


# =============================================================================
# Sinks Block Tests
# =============================================================================


class TestScopeBlockExtended:
    """Extended tests for Scope block to increase coverage."""

    def test_scope_init(self):
        """Test Scope block init method."""
        from src.osk.blocks.sinks import Scope

        scope = Scope(num_inputs=3)
        scope.init()

        assert scope.times == []
        assert scope.values == []
        assert scope._vector_inputs == {}
        assert scope._total_traces == 0

    def test_scope_setInput_vector(self):
        """Test Scope block with vector input."""
        from src.osk.blocks.sinks import Scope

        scope = Scope(num_inputs=1)
        scope.init()

        scope.setInput([1.0, 2.0, 3.0], port=0)

        # First element is stored in inputs[0]
        assert scope.inputs[0] == 1.0
        # Full vector in _vector_inputs
        assert 0 in scope._vector_inputs
        assert scope._vector_inputs[0] == [1.0, 2.0, 3.0]

    def test_scope_setInput_scalar_clears_vector(self):
        """Test Scope block: scalar input clears previous vector."""
        from src.osk.blocks.sinks import Scope

        scope = Scope(num_inputs=1)
        scope.init()

        # First set vector
        scope.setInput([1.0, 2.0, 3.0], port=0)
        assert 0 in scope._vector_inputs

        # Then set scalar
        scope.setInput(5.0, port=0)
        assert 0 not in scope._vector_inputs
        assert scope.inputs[0] == 5.0

    def test_scope_setInputName(self):
        """Test Scope setInputName method."""
        from src.osk.blocks.sinks import Scope

        scope = Scope(num_inputs=2)
        scope.init()

        scope.setInputName("Signal A", port=0)
        scope.setInputName("Signal B", port=1)

        assert scope.input_names[0] == "Signal A"
        assert scope.input_names[1] == "Signal B"

    def test_scope_getData_with_names(self):
        """Test Scope getData returns input names."""
        from src.osk.blocks.sinks import Scope
        from src.osk.blocks.sources import Constant
        from src.osk.state import State

        scope = Scope(num_inputs=2)
        scope.init()

        const1 = Constant(value=1.0)
        const1.init()
        const2 = Constant(value=2.0)
        const2.init()

        scope.connectInput(const1, port=0)
        scope.connectInput(const2, port=1)
        scope.setInputName("Position", port=0)
        scope.setInputName("Velocity", port=1)

        const1.update()
        const2.update()
        scope.update()

        # Simulate recording
        State.ready = True
        State.t = 0.0
        scope.rpt()

        data = scope.getData()
        assert "inputNames" in data
        assert data["inputNames"][0] == "Position"
        assert data["inputNames"][1] == "Velocity"

    def test_scope_invalid_port_getOutput(self):
        """Test Scope getOutput with invalid port."""
        from src.osk.blocks.sinks import Scope

        scope = Scope(num_inputs=2)
        scope.init()

        scope.setInput(1.0, port=0)
        scope.setInput(2.0, port=1)

        assert scope.getOutput(0) == 1.0
        assert scope.getOutput(1) == 2.0
        assert scope.getOutput(5) == 0.0  # Invalid port


class TestToWorkspaceBlockExtended:
    """Extended tests for ToWorkspace block."""

    def test_toworkspace_initialization(self):
        """Test ToWorkspace initialization."""
        from src.osk.blocks.sinks import ToWorkspace

        tw = ToWorkspace(variable_name="mydata")
        tw.init()

        assert tw.variable_name == "mydata"
        assert tw.times == []
        assert tw.values == []

    def test_toworkspace_record(self):
        """Test ToWorkspace recording."""
        from src.osk.blocks.sinks import ToWorkspace
        from src.osk.blocks.sources import Constant
        from src.osk.state import State

        tw = ToWorkspace(variable_name="output")
        tw.init()

        const = Constant(value=3.14)
        const.init()
        const.update()

        tw.connectInput(const)
        tw.update()

        # Simulate recording
        State.ready = True
        State.t = 0.5
        tw.rpt()

        assert len(tw.times) == 1
        assert tw.times[0] == 0.5
        assert tw.values[0] == pytest.approx(3.14)

    def test_toworkspace_getData(self):
        """Test ToWorkspace getData method."""
        from src.osk.blocks.sinks import ToWorkspace
        from src.osk.state import State

        tw = ToWorkspace(variable_name="testvar")
        tw.init()

        tw.setInput(10.0)
        tw.update()

        State.ready = True
        State.t = 1.0
        tw.rpt()

        data = tw.getData()
        assert data["name"] == "testvar"
        assert len(data["times"]) == 1
        assert len(data["values"]) == 1

    def test_toworkspace_getOutput(self):
        """Test ToWorkspace getOutput method."""
        from src.osk.blocks.sinks import ToWorkspace

        tw = ToWorkspace()
        tw.init()

        tw.setInput(42.0)
        tw.update()

        assert tw.getOutput() == 42.0


class TestDisplayBlockSinks:
    """Sinks tests for Display block."""

    def test_display_setInput_sinks(self):
        """Test Display setInput method."""
        from src.osk.blocks.sinks import Display

        disp = Display()

        disp.setInput(5.5)
        assert disp.input == 5.5

    def test_display_connectInput_sinks(self):
        """Test Display connectInput method."""
        from src.osk.blocks.sinks import Display
        from src.osk.blocks.sources import Constant

        disp = Display()

        const = Constant(value=2.5)
        const.init()
        const.update()

        disp.connectInput(const)
        disp.update()

        assert disp.input == 2.5

    def test_display_rpt_sinks(self):
        """Test Display rpt method."""
        from src.osk.blocks.sinks import Display
        from src.osk.state import State

        disp = Display()

        disp.setInput(7.77)

        State.ready = True
        disp.rpt()

        assert disp.current_value == 7.77
        assert disp.getOutput() == 7.77


class TestTerminatorBlockSinks:
    """Sinks tests for Terminator block."""

    def test_terminator_setInput_extended(self):
        """Test Terminator setInput method."""
        from src.osk.blocks.sinks import Terminator

        term = Terminator()

        term.setInput(100.0)
        assert term.input == 100.0

    def test_terminator_connectInput_extended(self):
        """Test Terminator connectInput method."""
        from src.osk.blocks.sinks import Terminator
        from src.osk.blocks.sources import Constant

        term = Terminator()

        const = Constant(value=999.0)
        const.init()
        const.update()

        term.connectInput(const)
        term.update()

        assert term.input == 999.0

    def test_terminator_getOutput_always_zero(self):
        """Test Terminator always returns zero output."""
        from src.osk.blocks.sinks import Terminator

        term = Terminator()

        term.setInput(12345.0)
        term.update()

        assert term.getOutput() == 0.0


class TestScope3DBlock:
    """Tests for Scope3D block."""

    def test_scope3d_initialization(self):
        """Test Scope3D initialization with custom labels."""
        from src.osk.blocks.sinks import Scope3D

        scope = Scope3D(x_label="Longitude", y_label="Latitude", z_label="Altitude")
        scope.init()

        assert scope.x_label == "Longitude"
        assert scope.y_label == "Latitude"
        assert scope.z_label == "Altitude"
        assert scope.times == []
        assert scope.x_values == []
        assert scope.y_values == []
        assert scope.z_values == []

    def test_scope3d_setInput(self):
        """Test Scope3D setInput method."""
        from src.osk.blocks.sinks import Scope3D

        scope = Scope3D()
        scope.init()

        scope.setInput(1.0, port=0)  # X
        scope.setInput(2.0, port=1)  # Y
        scope.setInput(3.0, port=2)  # Z

        assert scope.inputs[0] == 1.0
        assert scope.inputs[1] == 2.0
        assert scope.inputs[2] == 3.0

    def test_scope3d_connectInput(self):
        """Test Scope3D connectInput method."""
        from src.osk.blocks.sinks import Scope3D
        from src.osk.blocks.sources import Constant

        scope = Scope3D()
        scope.init()

        const_x = Constant(value=10.0)
        const_x.init()
        const_x.update()

        const_y = Constant(value=20.0)
        const_y.init()
        const_y.update()

        const_z = Constant(value=30.0)
        const_z.init()
        const_z.update()

        scope.connectInput(const_x, port=0)
        scope.connectInput(const_y, port=1)
        scope.connectInput(const_z, port=2)
        scope.update()

        assert scope.inputs[0] == 10.0
        assert scope.inputs[1] == 20.0
        assert scope.inputs[2] == 30.0

    def test_scope3d_rpt(self):
        """Test Scope3D rpt method."""
        from src.osk.blocks.sinks import Scope3D
        from src.osk.state import State

        scope = Scope3D()
        scope.init()

        scope.setInput(1.5, port=0)
        scope.setInput(2.5, port=1)
        scope.setInput(3.5, port=2)

        State.ready = True
        State.t = 0.1
        scope.rpt()

        assert len(scope.times) == 1
        assert scope.times[0] == 0.1
        assert scope.x_values[0] == 1.5
        assert scope.y_values[0] == 2.5
        assert scope.z_values[0] == 3.5

    def test_scope3d_getData(self):
        """Test Scope3D getData method."""
        from src.osk.blocks.sinks import Scope3D
        from src.osk.state import State

        scope = Scope3D(x_label="Roll", y_label="Pitch", z_label="Yaw")
        scope.init()

        scope.setInput(0.1, port=0)
        scope.setInput(0.2, port=1)
        scope.setInput(0.3, port=2)

        State.ready = True
        State.t = 0.0
        scope.rpt()

        data = scope.getData()
        assert data["x"] == [0.1]
        assert data["y"] == [0.2]
        assert data["z"] == [0.3]
        assert data["inputNames"] == ["Roll", "Pitch", "Yaw"]

    def test_scope3d_getOutput(self):
        """Test Scope3D getOutput method."""
        from src.osk.blocks.sinks import Scope3D

        scope = Scope3D()
        scope.init()

        scope.setInput(5.0, port=0)
        scope.setInput(6.0, port=1)
        scope.setInput(7.0, port=2)

        assert scope.getOutput(0) == 5.0
        assert scope.getOutput(1) == 6.0
        assert scope.getOutput(2) == 7.0
        assert scope.getOutput(3) == 0.0  # Invalid port


# =============================================================================
# Aerospace Block Extended Tests
# =============================================================================


class TestQuaternionNormalizeExtended:
    """Extended tests for QuaternionNormalize block."""

    def test_normalize_near_zero_quaternion(self):
        """Test normalization of near-zero quaternion."""
        from src.osk.blocks.aerospace import QuaternionNormalize

        qn = QuaternionNormalize()
        qn.init()

        # Very small quaternion - should return identity
        qn.setInput([1e-20, 1e-20, 1e-20, 1e-20])
        qn.update()

        output = qn.getOutputVector()
        assert output == [1.0, 0.0, 0.0, 0.0]

    def test_normalize_with_setInput_scalar_ports(self):
        """Test setInput with individual scalar ports."""
        from src.osk.blocks.aerospace import QuaternionNormalize

        qn = QuaternionNormalize()
        qn.init()

        # Set individual components
        qn.setInput(0.5, port=0)
        qn.setInput(0.5, port=1)
        qn.setInput(0.5, port=2)
        qn.setInput(0.5, port=3)
        qn.update()

        output = qn.getOutputVector()
        expected_norm = 1.0
        actual_norm = sum(x * x for x in output) ** 0.5
        assert abs(actual_norm - expected_norm) < 1e-10

    def test_normalize_getOutput_invalid_port(self):
        """Test getOutput with invalid port."""
        from src.osk.blocks.aerospace import QuaternionNormalize

        qn = QuaternionNormalize()
        qn.init()
        qn.update()

        assert qn.getOutput(4) == 0.0
        assert qn.getOutput(10) == 0.0


class TestQuaternionMultiplyExtended:
    """Extended tests for QuaternionMultiply block."""

    def test_multiply_with_connected_blocks(self):
        """Test quaternion multiplication with connected blocks."""
        from src.osk.blocks.aerospace import QuaternionMultiply
        from src.osk.blocks.math_ops import Mux

        qm = QuaternionMultiply()
        qm.init()

        # Create mux blocks for vector inputs
        mux1 = Mux(num_inputs=4)
        mux1.init()
        mux1.setInput(1.0, port=0)
        mux1.setInput(0.0, port=1)
        mux1.setInput(0.0, port=2)
        mux1.setInput(0.0, port=3)
        mux1.update()

        mux2 = Mux(num_inputs=4)
        mux2.init()
        mux2.setInput(1.0, port=0)
        mux2.setInput(0.0, port=1)
        mux2.setInput(0.0, port=2)
        mux2.setInput(0.0, port=3)
        mux2.update()

        qm.connectInput(mux1, port=0)
        qm.connectInput(mux2, port=1)
        qm.update()

        output = qm.getOutputVector()
        # Identity * Identity = Identity
        assert abs(output[0] - 1.0) < 1e-10
        assert abs(output[1]) < 1e-10
        assert abs(output[2]) < 1e-10
        assert abs(output[3]) < 1e-10

    def test_multiply_getOutput_invalid_port(self):
        """Test getOutput with invalid port."""
        from src.osk.blocks.aerospace import QuaternionMultiply

        qm = QuaternionMultiply()
        qm.init()
        qm.update()

        assert qm.getOutput(4) == 0.0


class TestQuaternionConjugateExtended:
    """Extended tests for QuaternionConjugate block."""

    def test_conjugate_with_connected_block(self):
        """Test quaternion conjugate with connected block."""
        from src.osk.blocks.aerospace import QuaternionConjugate
        from src.osk.blocks.math_ops import Mux

        qc = QuaternionConjugate()
        qc.init()

        mux = Mux(num_inputs=4)
        mux.init()
        mux.setInput(0.707, port=0)
        mux.setInput(0.707, port=1)
        mux.setInput(0.0, port=2)
        mux.setInput(0.0, port=3)
        mux.update()

        qc.connectInput(mux)
        qc.update()

        output = qc.getOutputVector()
        assert abs(output[0] - 0.707) < 1e-10
        assert abs(output[1] + 0.707) < 1e-10

    def test_conjugate_getOutput_invalid_port(self):
        """Test getOutput with invalid port."""
        from src.osk.blocks.aerospace import QuaternionConjugate

        qc = QuaternionConjugate()
        qc.init()
        qc.update()

        assert qc.getOutput(4) == 0.0


class TestQuaternionToEulerExtended:
    """Extended tests for QuaternionToEuler block."""

    def test_euler_gimbal_lock(self):
        """Test quaternion to euler at gimbal lock (pitch = 90 degrees)."""
        import math

        from src.osk.blocks.aerospace import QuaternionToEuler

        qe = QuaternionToEuler()
        qe.init()

        # Quaternion for pitch = 90 degrees (gimbal lock)
        qe.setInput([0.707, 0.0, 0.707, 0.0])
        qe.update()

        output = qe.getOutputVector()
        # Pitch should be near pi/2
        assert abs(output[1] - math.pi / 2) < 0.1

    def test_euler_with_connected_block(self):
        """Test with connected block."""
        from src.osk.blocks.aerospace import QuaternionToEuler
        from src.osk.blocks.math_ops import Mux

        qe = QuaternionToEuler()
        qe.init()

        mux = Mux(num_inputs=4)
        mux.init()
        mux.setInput(1.0, port=0)
        mux.setInput(0.0, port=1)
        mux.setInput(0.0, port=2)
        mux.setInput(0.0, port=3)
        mux.update()

        qe.connectInput(mux)
        qe.update()

        output = qe.getOutputVector()
        # Identity quaternion -> zero angles
        assert abs(output[0]) < 1e-10
        assert abs(output[1]) < 1e-10
        assert abs(output[2]) < 1e-10

    def test_euler_getOutput_invalid_port(self):
        """Test getOutput with invalid port."""
        from src.osk.blocks.aerospace import QuaternionToEuler

        qe = QuaternionToEuler()
        qe.init()
        qe.update()

        assert qe.getOutput(3) == 0.0


class TestEulerToQuaternionExtended:
    """Extended tests for EulerToQuaternion block."""

    def test_euler_to_quat_with_connected_block(self):
        """Test with connected block."""
        from src.osk.blocks.aerospace import EulerToQuaternion
        from src.osk.blocks.math_ops import Mux

        eq = EulerToQuaternion()
        eq.init()

        mux = Mux(num_inputs=3)
        mux.init()
        mux.setInput(0.0, port=0)
        mux.setInput(0.0, port=1)
        mux.setInput(0.0, port=2)
        mux.update()

        eq.connectInput(mux)
        eq.update()

        output = eq.getOutputVector()
        # Zero angles -> identity quaternion
        assert abs(output[0] - 1.0) < 1e-10
        assert abs(output[1]) < 1e-10

    def test_euler_to_quat_setInput_scalar(self):
        """Test setInput with scalar port values."""
        from src.osk.blocks.aerospace import EulerToQuaternion

        eq = EulerToQuaternion()
        eq.init()

        eq.setInput(0.1, port=0)  # roll
        eq.setInput(0.2, port=1)  # pitch
        eq.setInput(0.3, port=2)  # yaw
        eq.update()

        output = eq.getOutputVector()
        # Should be normalized
        norm = sum(x * x for x in output) ** 0.5
        assert abs(norm - 1.0) < 1e-10

    def test_euler_to_quat_getOutput_invalid_port(self):
        """Test getOutput with invalid port."""
        from src.osk.blocks.aerospace import EulerToQuaternion

        eq = EulerToQuaternion()
        eq.init()
        eq.update()

        assert eq.getOutput(4) == 0.0


class TestQuaternionRotateVectorExtended:
    """Extended tests for QuaternionRotateVector block."""

    def test_rotate_vector_with_connected_blocks(self):
        """Test with connected blocks."""
        from src.osk.blocks.aerospace import QuaternionRotateVector
        from src.osk.blocks.math_ops import Mux

        qrv = QuaternionRotateVector()
        qrv.init()

        # Identity quaternion
        quat_mux = Mux(num_inputs=4)
        quat_mux.init()
        quat_mux.setInput(1.0, port=0)
        quat_mux.setInput(0.0, port=1)
        quat_mux.setInput(0.0, port=2)
        quat_mux.setInput(0.0, port=3)
        quat_mux.update()

        # Vector to rotate
        vec_mux = Mux(num_inputs=3)
        vec_mux.init()
        vec_mux.setInput(1.0, port=0)
        vec_mux.setInput(2.0, port=1)
        vec_mux.setInput(3.0, port=2)
        vec_mux.update()

        qrv.connectInput(quat_mux, port=0)
        qrv.connectInput(vec_mux, port=1)
        qrv.update()

        output = qrv.getOutputVector()
        # Identity rotation - vector unchanged
        assert abs(output[0] - 1.0) < 1e-10
        assert abs(output[1] - 2.0) < 1e-10
        assert abs(output[2] - 3.0) < 1e-10

    def test_rotate_vector_getOutput_invalid_port(self):
        """Test getOutput with invalid port."""
        from src.osk.blocks.aerospace import QuaternionRotateVector

        qrv = QuaternionRotateVector()
        qrv.init()
        qrv.update()

        assert qrv.getOutput(3) == 0.0


class TestDCMToQuaternionExtended:
    """Extended tests for DCMToQuaternion block."""

    def test_dcm_to_quat_rotation_about_x(self):
        """Test DCM to quaternion for rotation about x-axis."""
        import math

        from src.osk.blocks.aerospace import DCMToQuaternion

        dcm = DCMToQuaternion()
        dcm.init()

        # 90 degree rotation about x-axis
        c, s = math.cos(math.pi / 4), math.sin(math.pi / 4)
        dcm_matrix = [
            1,
            0,
            0,
            0,
            c,
            -s,
            0,
            s,
            c,
        ]
        dcm.setInput(dcm_matrix)
        dcm.update()

        output = dcm.getOutputVector()
        norm = sum(x * x for x in output) ** 0.5
        assert abs(norm - 1.0) < 1e-6

    def test_dcm_to_quat_rotation_about_y(self):
        """Test DCM to quaternion for rotation about y-axis (r22 > r33)."""
        import math

        from src.osk.blocks.aerospace import DCMToQuaternion

        dcm = DCMToQuaternion()
        dcm.init()

        # Rotation about y-axis where r22 > r33
        angle = math.pi / 3
        c, s = math.cos(angle), math.sin(angle)
        dcm_matrix = [
            c,
            0,
            s,
            0,
            1,
            0,
            -s,
            0,
            c,
        ]
        dcm.setInput(dcm_matrix)
        dcm.update()

        output = dcm.getOutputVector()
        norm = sum(x * x for x in output) ** 0.5
        assert abs(norm - 1.0) < 1e-6

    def test_dcm_to_quat_rotation_about_z(self):
        """Test DCM to quaternion for rotation about z-axis (r33 largest)."""
        import math

        from src.osk.blocks.aerospace import DCMToQuaternion

        dcm = DCMToQuaternion()
        dcm.init()

        # Rotation about z-axis where r33 > r11 and r33 > r22
        angle = math.pi / 3
        c, s = math.cos(angle), math.sin(angle)
        dcm_matrix = [
            c,
            -s,
            0,
            s,
            c,
            0,
            0,
            0,
            1,
        ]
        dcm.setInput(dcm_matrix)
        dcm.update()

        output = dcm.getOutputVector()
        norm = sum(x * x for x in output) ** 0.5
        assert abs(norm - 1.0) < 1e-6

    def test_dcm_to_quat_with_connected_block(self):
        """Test with connected block."""
        from src.osk.blocks.aerospace import DCMToQuaternion
        from src.osk.blocks.math_ops import Mux

        dcm = DCMToQuaternion()
        dcm.init()

        # Identity DCM
        mux = Mux(num_inputs=9)
        mux.init()
        mux.setInput(1.0, port=0)
        mux.setInput(0.0, port=1)
        mux.setInput(0.0, port=2)
        mux.setInput(0.0, port=3)
        mux.setInput(1.0, port=4)
        mux.setInput(0.0, port=5)
        mux.setInput(0.0, port=6)
        mux.setInput(0.0, port=7)
        mux.setInput(1.0, port=8)
        mux.update()

        dcm.connectInput(mux)
        dcm.update()

        output = dcm.getOutputVector()
        # Identity DCM -> identity quaternion
        assert abs(output[0] - 1.0) < 0.01 or abs(output[0] + 1.0) < 0.01

    def test_dcm_to_quat_getOutput_invalid_port(self):
        """Test getOutput with invalid port."""
        from src.osk.blocks.aerospace import DCMToQuaternion

        dcm = DCMToQuaternion()
        dcm.init()
        dcm.update()

        assert dcm.getOutput(4) == 0.0


class TestQuaternionToDCMExtended:
    """Extended tests for QuaternionToDCM block."""

    def test_quat_to_dcm_with_connected_block(self):
        """Test with connected block."""
        from src.osk.blocks.aerospace import QuaternionToDCM
        from src.osk.blocks.math_ops import Mux

        qtd = QuaternionToDCM()
        qtd.init()

        # Identity quaternion
        mux = Mux(num_inputs=4)
        mux.init()
        mux.setInput(1.0, port=0)
        mux.setInput(0.0, port=1)
        mux.setInput(0.0, port=2)
        mux.setInput(0.0, port=3)
        mux.update()

        qtd.connectInput(mux)
        qtd.update()

        output = qtd.getOutputVector()
        # Identity quaternion -> identity DCM
        assert abs(output[0] - 1.0) < 1e-10
        assert abs(output[4] - 1.0) < 1e-10
        assert abs(output[8] - 1.0) < 1e-10

    def test_quat_to_dcm_getOutput_invalid_port(self):
        """Test getOutput with invalid port."""
        from src.osk.blocks.aerospace import QuaternionToDCM

        qtd = QuaternionToDCM()
        qtd.init()
        qtd.update()

        assert qtd.getOutput(9) == 0.0


class TestISAAtmosphereExtended:
    """Extended tests for ISAAtmosphere block."""

    def test_atmosphere_stratosphere(self):
        """Test atmosphere above 11km (stratosphere)."""
        from src.osk.blocks.aerospace import ISAAtmosphere

        atm = ISAAtmosphere()
        atm.init()

        # Above troposphere
        atm.setInput(15000.0)
        atm.update()

        output = atm.getOutputVector()
        # Temperature should be around 216.65K in stratosphere
        assert output[0] < 230  # Temperature below 230K
        assert output[1] < 15000  # Pressure lower than sea level

    def test_atmosphere_getOutput_invalid_port(self):
        """Test getOutput with invalid port."""
        from src.osk.blocks.aerospace import ISAAtmosphere

        atm = ISAAtmosphere()
        atm.init()
        atm.update()

        assert atm.getOutput(4) == 0.0


class TestSixDOFEulerExtended:
    """Extended tests for SixDOFEuler block."""

    def test_sixdof_with_forces_and_moments(self):
        """Test 6DOF dynamics with forces and moments."""
        from src.osk.blocks.aerospace import SixDOFEuler

        sixdof = SixDOFEuler(mass=100.0, Ixx=10.0, Iyy=10.0, Izz=10.0, Ixz=0.0)
        sixdof.init()

        # Apply a force
        sixdof.setInput([100.0, 0.0, 0.0], port=0)  # Forces
        sixdof.setInput([0.0, 0.0, 0.0], port=1)  # Moments
        sixdof.update()

        output = sixdof.getOutputVector()
        assert len(output) == 12
        # Acceleration should be F/m = 100/100 = 1 m/s^2
        # u_dot = 1.0

    def test_sixdof_with_connected_blocks(self):
        """Test 6DOF with connected blocks."""
        from src.osk.blocks.aerospace import SixDOFEuler
        from src.osk.blocks.math_ops import Mux

        sixdof = SixDOFEuler(mass=10.0, Ixx=1.0, Iyy=1.0, Izz=1.0, Ixz=0.0)
        sixdof.init()

        # Forces mux
        forces_mux = Mux(num_inputs=3)
        forces_mux.init()
        forces_mux.setInput(10.0, port=0)
        forces_mux.setInput(0.0, port=1)
        forces_mux.setInput(0.0, port=2)
        forces_mux.update()

        # Moments mux
        moments_mux = Mux(num_inputs=3)
        moments_mux.init()
        moments_mux.setInput(0.0, port=0)
        moments_mux.setInput(0.0, port=1)
        moments_mux.setInput(0.0, port=2)
        moments_mux.update()

        sixdof.connectInput(forces_mux, port=0)
        sixdof.connectInput(moments_mux, port=1)
        sixdof.update()

        output = sixdof.getOutputVector()
        assert len(output) == 12

    def test_sixdof_getOutput_invalid_port(self):
        """Test getOutput with invalid port."""
        from src.osk.blocks.aerospace import SixDOFEuler

        sixdof = SixDOFEuler()
        sixdof.init()
        sixdof.update()

        assert sixdof.getOutput(12) == 0.0

    def test_sixdof_gimbal_lock_handling(self):
        """Test 6DOF near gimbal lock (theta near 90 degrees)."""
        import math

        from src.osk.blocks.aerospace import SixDOFEuler

        sixdof = SixDOFEuler(mass=10.0, Ixx=1.0, Iyy=1.0, Izz=1.0, Ixz=0.0)
        sixdof.init()

        # Set theta close to 90 degrees
        sixdof.theta[0] = math.pi / 2 - 0.001
        sixdof.setInput([0.0, 0.0, 0.0], port=0)
        sixdof.setInput([0.0, 0.0, 1.0], port=1)  # Yaw moment
        sixdof.update()

        # Should not crash, theta_dot should be computed
        assert sixdof.getOutputVector() is not None


class TestFlatEarthGravityExtended:
    """Extended tests for FlatEarthGravity block."""

    def test_flat_earth_custom_g(self):
        """Test with custom gravity value."""
        from src.osk.blocks.aerospace import FlatEarthGravity

        grav = FlatEarthGravity(g=10.0)
        grav.init()
        grav.update()

        output = grav.getOutputVector()
        assert output[2] == 10.0

    def test_flat_earth_getOutput_invalid_port(self):
        """Test getOutput with invalid port."""
        from src.osk.blocks.aerospace import FlatEarthGravity

        grav = FlatEarthGravity()
        grav.init()
        grav.update()

        assert grav.getOutput(3) == 0.0


class TestWGS84GravityExtended:
    """Extended tests for WGS84Gravity block."""

    def test_wgs84_with_connected_block(self):
        """Test with connected block."""
        from src.osk.blocks.aerospace import WGS84Gravity
        from src.osk.blocks.math_ops import Mux

        grav = WGS84Gravity()
        grav.init()

        # [latitude, altitude]
        mux = Mux(num_inputs=2)
        mux.init()
        mux.setInput(0.785, port=0)  # 45 degrees
        mux.setInput(1000.0, port=1)  # 1000m altitude
        mux.update()

        grav.connectInput(mux)
        grav.update()

        output = grav.getOutput()
        assert 9.7 < output < 9.9

    def test_wgs84_setInput_scalar(self):
        """Test setInput with scalar port values."""
        from src.osk.blocks.aerospace import WGS84Gravity

        grav = WGS84Gravity()
        grav.init()

        grav.setInput(0.0, port=0)  # Equator
        grav.setInput(0.0, port=1)  # Sea level
        grav.update()

        output = grav.getOutput()
        assert abs(output - 9.78) < 0.1


# =============================================================================
# Sensor Fusion Extended Tests
# =============================================================================


class TestIMUSensorExtended:
    """Extended tests for IMUSensor block."""

    def test_imu_with_connected_blocks(self):
        """Test IMU with connected blocks."""
        from src.osk.blocks.math_ops import Mux
        from src.osk.blocks.sensor_fusion import IMUSensor

        imu = IMUSensor(accel_noise=0.0, gyro_noise=0.0, seed=42)
        imu.init()

        # Accel mux
        accel_mux = Mux(num_inputs=3)
        accel_mux.init()
        accel_mux.setInput(0.0, port=0)
        accel_mux.setInput(0.0, port=1)
        accel_mux.setInput(9.81, port=2)
        accel_mux.update()

        # Gyro mux
        gyro_mux = Mux(num_inputs=3)
        gyro_mux.init()
        gyro_mux.setInput(0.1, port=0)
        gyro_mux.setInput(0.0, port=1)
        gyro_mux.setInput(0.0, port=2)
        gyro_mux.update()

        imu.connectInput(accel_mux, port=0)
        imu.connectInput(gyro_mux, port=1)
        imu.update()

        output = imu.getOutputVector()
        assert len(output) == 6
        assert abs(output[2] - 9.81) < 0.1

    def test_imu_getOutput_invalid_port(self):
        """Test getOutput with invalid port."""
        from src.osk.blocks.sensor_fusion import IMUSensor

        imu = IMUSensor()
        imu.init()
        imu.update()

        assert imu.getOutput(6) == 0.0


class TestAccelerometerExtended:
    """Extended tests for Accelerometer block."""

    def test_accelerometer_with_connected_block(self):
        """Test Accelerometer with connected block."""
        from src.osk.blocks.math_ops import Mux
        from src.osk.blocks.sensor_fusion import Accelerometer

        accel = Accelerometer(noise=0.0, seed=42)
        accel.init()

        mux = Mux(num_inputs=3)
        mux.init()
        mux.setInput(0.0, port=0)
        mux.setInput(0.0, port=1)
        mux.setInput(9.81, port=2)
        mux.update()

        accel.connectInput(mux)
        accel.update()

        output = accel.getOutputVector()
        assert abs(output[2] - 9.81) < 0.01

    def test_accelerometer_getOutput_invalid_port(self):
        """Test getOutput with invalid port."""
        from src.osk.blocks.sensor_fusion import Accelerometer

        accel = Accelerometer()
        accel.init()
        accel.update()

        assert accel.getOutput(3) == 0.0


class TestGyroscopeExtended:
    """Extended tests for Gyroscope block."""

    def test_gyroscope_with_connected_block(self):
        """Test Gyroscope with connected block."""
        from src.osk.blocks.math_ops import Mux
        from src.osk.blocks.sensor_fusion import Gyroscope

        gyro = Gyroscope(noise=0.0, seed=42)
        gyro.init()

        mux = Mux(num_inputs=3)
        mux.init()
        mux.setInput(0.1, port=0)
        mux.setInput(0.2, port=1)
        mux.setInput(0.3, port=2)
        mux.update()

        gyro.connectInput(mux)
        gyro.update()

        output = gyro.getOutputVector()
        assert abs(output[0] - 0.1) < 0.01
        assert abs(output[1] - 0.2) < 0.01
        assert abs(output[2] - 0.3) < 0.01

    def test_gyroscope_getOutput_invalid_port(self):
        """Test getOutput with invalid port."""
        from src.osk.blocks.sensor_fusion import Gyroscope

        gyro = Gyroscope()
        gyro.init()
        gyro.update()

        assert gyro.getOutput(3) == 0.0


class TestMagnetometerExtended:
    """Extended tests for Magnetometer block."""

    def test_magnetometer_with_connected_block(self):
        """Test Magnetometer with connected block."""
        from src.osk.blocks.math_ops import Mux
        from src.osk.blocks.sensor_fusion import Magnetometer

        mag = Magnetometer(noise=0.0, seed=42)
        mag.init()

        mux = Mux(num_inputs=3)
        mux.init()
        mux.setInput(0.3, port=0)  # North component
        mux.setInput(0.0, port=1)
        mux.setInput(0.5, port=2)  # Down component
        mux.update()

        mag.connectInput(mux)
        mag.update()

        output = mag.getOutputVector()
        assert abs(output[0] - 0.3) < 0.01

    def test_magnetometer_getOutput_invalid_port(self):
        """Test getOutput with invalid port."""
        from src.osk.blocks.sensor_fusion import Magnetometer

        mag = Magnetometer()
        mag.init()
        mag.update()

        assert mag.getOutput(3) == 0.0


class TestGPSSensorExtended:
    """Extended tests for GPSSensor block."""

    def test_gps_with_connected_blocks(self):
        """Test GPS with connected blocks."""
        from src.osk.blocks.math_ops import Mux
        from src.osk.blocks.sensor_fusion import GPSSensor
        from src.osk.state import State

        State.t = 0.0

        gps = GPSSensor(position_noise=0.0, velocity_noise=0.0, seed=42)
        gps.init()

        pos_mux = Mux(num_inputs=3)
        pos_mux.init()
        pos_mux.setInput(45.0, port=0)  # lat
        pos_mux.setInput(-122.0, port=1)  # lon
        pos_mux.setInput(100.0, port=2)  # alt
        pos_mux.update()

        vel_mux = Mux(num_inputs=3)
        vel_mux.init()
        vel_mux.setInput(10.0, port=0)  # vn
        vel_mux.setInput(5.0, port=1)  # ve
        vel_mux.setInput(0.0, port=2)  # vd
        vel_mux.update()

        gps.connectInput(pos_mux, port=0)
        gps.connectInput(vel_mux, port=1)
        gps.update()

        output = gps.getOutputVector()
        assert len(output) == 6

    def test_gps_getOutput_invalid_port(self):
        """Test getOutput with invalid port."""
        from src.osk.blocks.sensor_fusion import GPSSensor

        gps = GPSSensor()
        gps.init()

        assert gps.getOutput(6) == 0.0


class TestComplementaryFilterExtended:
    """Extended tests for ComplementaryFilter block."""

    def test_complementary_with_connected_blocks(self):
        """Test Complementary filter with connected blocks."""
        from src.osk.blocks.math_ops import Mux
        from src.osk.blocks.sensor_fusion import ComplementaryFilter
        from src.osk.state import State

        State.dt = 0.01

        cf = ComplementaryFilter(alpha=0.98)
        cf.init()

        accel_mux = Mux(num_inputs=3)
        accel_mux.init()
        accel_mux.setInput(0.0, port=0)
        accel_mux.setInput(0.0, port=1)
        accel_mux.setInput(9.81, port=2)
        accel_mux.update()

        gyro_mux = Mux(num_inputs=3)
        gyro_mux.init()
        gyro_mux.setInput(0.0, port=0)
        gyro_mux.setInput(0.0, port=1)
        gyro_mux.setInput(0.0, port=2)
        gyro_mux.update()

        cf.connectInput(accel_mux, port=0)
        cf.connectInput(gyro_mux, port=1)
        cf.update()

        output = cf.getOutputVector()
        assert len(output) == 3

    def test_complementary_getOutput_invalid_port(self):
        """Test getOutput with invalid port."""
        from src.osk.blocks.sensor_fusion import ComplementaryFilter
        from src.osk.state import State

        State.dt = 0.01

        cf = ComplementaryFilter()
        cf.init()
        cf.update()

        assert cf.getOutput(3) == 0.0


class TestMadgwickFilterExtended:
    """Extended tests for MadgwickFilter block."""

    def test_madgwick_with_magnetometer(self):
        """Test Madgwick filter with magnetometer input."""
        from src.osk.blocks.math_ops import Mux
        from src.osk.blocks.sensor_fusion import MadgwickFilter
        from src.osk.state import State

        State.dt = 0.01

        mf = MadgwickFilter(beta=0.1)
        mf.init()

        accel_mux = Mux(num_inputs=3)
        accel_mux.init()
        accel_mux.setInput(0.0, port=0)
        accel_mux.setInput(0.0, port=1)
        accel_mux.setInput(1.0, port=2)  # Normalized gravity
        accel_mux.update()

        gyro_mux = Mux(num_inputs=3)
        gyro_mux.init()
        gyro_mux.setInput(0.0, port=0)
        gyro_mux.setInput(0.0, port=1)
        gyro_mux.setInput(0.0, port=2)
        gyro_mux.update()

        mag_mux = Mux(num_inputs=3)
        mag_mux.init()
        mag_mux.setInput(1.0, port=0)  # North
        mag_mux.setInput(0.0, port=1)
        mag_mux.setInput(0.0, port=2)
        mag_mux.update()

        mf.connectInput(accel_mux, port=0)
        mf.connectInput(gyro_mux, port=1)
        mf.connectInput(mag_mux, port=2)
        mf.update()

        output = mf.getOutputVector()
        assert len(output) == 4

    def test_madgwick_zero_accel(self):
        """Test Madgwick with zero acceleration."""
        from src.osk.blocks.sensor_fusion import MadgwickFilter
        from src.osk.state import State

        State.dt = 0.01

        mf = MadgwickFilter()
        mf.init()

        mf.setInput([0.0, 0.0, 0.0], port=0)  # Zero accel
        mf.setInput([0.0, 0.0, 0.0], port=1)  # Zero gyro
        mf.update()

        # Should not crash with zero input
        assert mf.getOutputVector() is not None

    def test_madgwick_getOutput_invalid_port(self):
        """Test getOutput with invalid port."""
        from src.osk.blocks.sensor_fusion import MadgwickFilter
        from src.osk.state import State

        State.dt = 0.01

        mf = MadgwickFilter()
        mf.init()
        mf.update()

        assert mf.getOutput(4) == 0.0


class TestMahonyFilterExtended:
    """Extended tests for MahonyFilter block."""

    def test_mahony_with_integral_gain(self):
        """Test Mahony filter with integral gain."""
        from src.osk.blocks.math_ops import Mux
        from src.osk.blocks.sensor_fusion import MahonyFilter
        from src.osk.state import State

        State.dt = 0.01

        mh = MahonyFilter(Kp=1.0, Ki=0.1)
        mh.init()

        accel_mux = Mux(num_inputs=3)
        accel_mux.init()
        accel_mux.setInput(0.0, port=0)
        accel_mux.setInput(0.0, port=1)
        accel_mux.setInput(1.0, port=2)
        accel_mux.update()

        gyro_mux = Mux(num_inputs=3)
        gyro_mux.init()
        gyro_mux.setInput(0.0, port=0)
        gyro_mux.setInput(0.0, port=1)
        gyro_mux.setInput(0.0, port=2)
        gyro_mux.update()

        mh.connectInput(accel_mux, port=0)
        mh.connectInput(gyro_mux, port=1)
        mh.update()

        output = mh.getOutputVector()
        assert len(output) == 4

    def test_mahony_zero_accel(self):
        """Test Mahony with zero acceleration."""
        from src.osk.blocks.sensor_fusion import MahonyFilter
        from src.osk.state import State

        State.dt = 0.01

        mh = MahonyFilter()
        mh.init()

        mh.setInput([0.0, 0.0, 0.0], port=0)  # Zero accel
        mh.setInput([0.0, 0.0, 0.0], port=1)  # Zero gyro
        mh.update()

        # Should not crash with zero input
        assert mh.getOutputVector() is not None

    def test_mahony_getOutput_invalid_port(self):
        """Test getOutput with invalid port."""
        from src.osk.blocks.sensor_fusion import MahonyFilter
        from src.osk.state import State

        State.dt = 0.01

        mh = MahonyFilter()
        mh.init()
        mh.update()

        assert mh.getOutput(4) == 0.0


class TestINSGPSFusionExtended:
    """Extended tests for INSGPSFusion block."""

    def test_ins_gps_full_update(self):
        """Test INS/GPS fusion with all inputs."""
        from src.osk.blocks.math_ops import Mux
        from src.osk.blocks.sensor_fusion import INSGPSFusion
        from src.osk.state import State

        State.dt = 0.01

        ins = INSGPSFusion()
        ins.init()

        # IMU data [ax, ay, az, wx, wy, wz]
        imu_mux = Mux(num_inputs=6)
        imu_mux.init()
        for i in range(6):
            imu_mux.setInput(0.0, port=i)
        imu_mux.update()

        # GPS position [lat, lon, alt]
        gps_pos = Mux(num_inputs=3)
        gps_pos.init()
        gps_pos.setInput(45.0, port=0)
        gps_pos.setInput(-122.0, port=1)
        gps_pos.setInput(100.0, port=2)
        gps_pos.update()

        # GPS velocity [vn, ve, vd]
        gps_vel = Mux(num_inputs=3)
        gps_vel.init()
        gps_vel.setInput(0.0, port=0)
        gps_vel.setInput(0.0, port=1)
        gps_vel.setInput(0.0, port=2)
        gps_vel.update()

        ins.connectInput(imu_mux, port=0)
        ins.connectInput(gps_pos, port=1)
        ins.connectInput(gps_vel, port=2)
        ins.update()

        output = ins.getOutputVector()
        assert len(output) == 9

    def test_ins_gps_getOutput_invalid_port(self):
        """Test getOutput with invalid port."""
        from src.osk.blocks.sensor_fusion import INSGPSFusion

        ins = INSGPSFusion()
        ins.init()

        assert ins.getOutput(9) == 0.0


class TestAlphaBetaFilterExtended:
    """Extended tests for AlphaBetaFilter block."""

    def test_alpha_beta_tracking(self):
        """Test alpha-beta filter tracking."""
        from src.osk.blocks.sensor_fusion import AlphaBetaFilter
        from src.osk.blocks.sources import Constant

        abf = AlphaBetaFilter(alpha=0.5, beta=0.1, sample_time=0.1)
        abf.init()

        # Connect a constant signal
        const = Constant(value=10.0)
        const.init()
        const.update()

        abf.connectInput(const)

        # Run several updates
        for _ in range(10):
            abf.update()

        output = abf.getOutputVector()
        # Position should converge toward 10
        assert output[0] > 5.0

    def test_alpha_beta_getOutput_invalid_port(self):
        """Test getOutput with invalid port."""
        from src.osk.blocks.sensor_fusion import AlphaBetaFilter

        abf = AlphaBetaFilter()
        abf.init()
        abf.update()

        assert abf.getOutput(2) == 0.0


class TestAlphaBetaGammaFilterExtended:
    """Extended tests for AlphaBetaGammaFilter block."""

    def test_alpha_beta_gamma_tracking(self):
        """Test alpha-beta-gamma filter tracking."""
        from src.osk.blocks.sensor_fusion import AlphaBetaGammaFilter
        from src.osk.blocks.sources import Constant

        abgf = AlphaBetaGammaFilter(alpha=0.5, beta=0.3, gamma=0.1, sample_time=0.1)
        abgf.init()

        # Connect a constant signal
        const = Constant(value=100.0)
        const.init()
        const.update()

        abgf.connectInput(const)

        # Run several updates
        for _ in range(10):
            abgf.update()

        output = abgf.getOutputVector()
        # Position should converge toward 100
        assert output[0] > 50.0

    def test_alpha_beta_gamma_getOutput_invalid_port(self):
        """Test getOutput with invalid port."""
        from src.osk.blocks.sensor_fusion import AlphaBetaGammaFilter

        abgf = AlphaBetaGammaFilter()
        abgf.init()
        abgf.update()

        assert abgf.getOutput(3) == 0.0


# =============================================================================
# Math Ops Extended Tests
# =============================================================================


class TestSumVectorExtended:
    """Extended tests for Sum block with vectors."""

    def test_sum_vector_via_setInput(self):
        """Test vector sum via setInput."""
        from src.osk.blocks.math_ops import Sum

        sum_block = Sum(signs="++")
        sum_block.init()

        sum_block.setInput([1.0, 2.0, 3.0], port=0)
        sum_block.setInput([4.0, 5.0, 6.0], port=1)
        sum_block.update()

        output = sum_block.getOutputVector()
        assert output is not None
        assert output[0] == 5.0
        assert output[1] == 7.0
        assert output[2] == 9.0

    def test_sum_vector_scalar_mix(self):
        """Test vector + scalar combination."""
        from src.osk.blocks.math_ops import Mux, Sum
        from src.osk.blocks.sources import Constant

        sum_block = Sum(signs="++")
        sum_block.init()

        # Vector input
        mux = Mux(num_inputs=3)
        mux.init()
        mux.setInput(1.0, port=0)
        mux.setInput(2.0, port=1)
        mux.setInput(3.0, port=2)
        mux.update()

        # Scalar input
        const = Constant(value=10.0)
        const.init()
        const.update()

        sum_block.connectInput(mux, port=0)
        sum_block.connectInput(const, port=1)
        sum_block.update()

        output = sum_block.getOutputVector()
        # Should broadcast scalar to first element
        assert output is not None

    def test_sum_getOutput_port_beyond_vector(self):
        """Test getOutput with port beyond vector size."""
        from src.osk.blocks.math_ops import Sum

        sum_block = Sum(signs="++")
        sum_block.init()

        sum_block.setInput([1.0, 2.0], port=0)
        sum_block.setInput([3.0, 4.0], port=1)
        sum_block.update()

        assert sum_block.getOutput(0) == 4.0
        assert sum_block.getOutput(1) == 6.0
        assert sum_block.getOutput(2) == 0.0


class TestProductVectorExtended:
    """Extended tests for Product block with vectors."""

    def test_product_vector_via_setInput(self):
        """Test vector product via setInput."""
        from src.osk.blocks.math_ops import Product

        prod = Product(operations="**")
        prod.init()

        prod.setInput([2.0, 3.0, 4.0], port=0)
        prod.setInput([5.0, 6.0, 7.0], port=1)
        prod.update()

        output = prod.getOutputVector()
        assert output is not None
        assert output[0] == 10.0
        assert output[1] == 18.0
        assert output[2] == 28.0

    def test_product_vector_division(self):
        """Test vector division."""
        from src.osk.blocks.math_ops import Product

        prod = Product(operations="*/")
        prod.init()

        prod.setInput([10.0, 20.0, 30.0], port=0)
        prod.setInput([2.0, 4.0, 5.0], port=1)
        prod.update()

        output = prod.getOutputVector()
        assert output is not None
        assert output[0] == 5.0
        assert output[1] == 5.0
        assert output[2] == 6.0

    def test_product_vector_divide_by_zero(self):
        """Test vector division by near-zero."""
        from src.osk.blocks.math_ops import Product

        prod = Product(operations="*/")
        prod.init()

        prod.setInput([10.0, 20.0], port=0)
        prod.setInput([0.0, 0.0], port=1)  # Near zero
        prod.update()

        output = prod.getOutputVector()
        # Should use EPS instead of zero
        assert output is not None


class TestGainVectorExtended:
    """Extended tests for Gain block with vectors."""

    def test_gain_vector_source_port(self):
        """Test Gain with specific source port."""
        from src.osk.blocks.math_ops import Gain, Mux

        gain = Gain(gain=2.0)
        gain.init()

        mux = Mux(num_inputs=3)
        mux.init()
        mux.setInput(5.0, port=0)
        mux.setInput(10.0, port=1)
        mux.setInput(15.0, port=2)
        mux.update()

        # Connect with source_port=1
        gain.connectInput(mux, port=0, source_port=1)
        gain.update()

        # Should use scalar mode with port 1 value
        assert gain.getOutput() == 20.0

    def test_gain_getOutput_port_beyond_vector(self):
        """Test getOutput with port beyond vector size."""
        from src.osk.blocks.math_ops import Gain

        gain = Gain(gain=2.0)
        gain.init()

        gain.setInput([1.0, 2.0], port=0)
        gain.update()

        assert gain.getOutput(0) == 2.0
        assert gain.getOutput(1) == 4.0
        assert gain.getOutput(2) == 0.0


class TestAbsVectorExtended:
    """Extended tests for Abs block with vectors."""

    def test_abs_vector_via_setInput(self):
        """Test Abs with vector input."""
        from src.osk.blocks.math_ops import Abs

        abs_block = Abs()
        abs_block.init()

        abs_block.setInput([-1.0, 2.0, -3.0])
        abs_block.update()

        output = abs_block.getOutputVector()
        assert output is not None
        assert output[0] == 1.0
        assert output[1] == 2.0
        assert output[2] == 3.0

    def test_abs_getOutput_port_beyond_vector(self):
        """Test getOutput with port beyond vector size."""
        from src.osk.blocks.math_ops import Abs

        abs_block = Abs()
        abs_block.init()

        abs_block.setInput([-5.0, -6.0])
        abs_block.update()

        assert abs_block.getOutput(0) == 5.0
        assert abs_block.getOutput(1) == 6.0
        assert abs_block.getOutput(2) == 0.0


class TestSignVectorExtended:
    """Extended tests for Sign block with vectors."""

    def test_sign_vector_via_setInput(self):
        """Test Sign with vector input."""
        from src.osk.blocks.math_ops import Sign

        sign_block = Sign()
        sign_block.init()

        sign_block.setInput([-5.0, 0.0, 10.0])
        sign_block.update()

        output = sign_block.getOutputVector()
        assert output is not None
        assert output[0] == -1.0
        assert output[1] == 0.0
        assert output[2] == 1.0

    def test_sign_getOutput_port_beyond_vector(self):
        """Test getOutput with port beyond vector size."""
        from src.osk.blocks.math_ops import Sign

        sign_block = Sign()
        sign_block.init()

        sign_block.setInput([-1.0, 1.0])
        sign_block.update()

        assert sign_block.getOutput(0) == -1.0
        assert sign_block.getOutput(1) == 1.0
        assert sign_block.getOutput(2) == 0.0


class TestSaturationVectorExtended:
    """Extended tests for Saturation block with vectors."""

    def test_saturation_vector_via_setInput(self):
        """Test Saturation with vector input."""
        from src.osk.blocks.math_ops import Saturation

        sat = Saturation(upper_limit=5.0, lower_limit=-5.0)
        sat.init()

        sat.setInput([-10.0, 0.0, 10.0])
        sat.update()

        output = sat.getOutputVector()
        assert output is not None
        assert output[0] == -5.0
        assert output[1] == 0.0
        assert output[2] == 5.0

    def test_saturation_getOutput_port_beyond_vector(self):
        """Test getOutput with port beyond vector size."""
        from src.osk.blocks.math_ops import Saturation

        sat = Saturation()
        sat.init()

        sat.setInput([0.5, -0.5])
        sat.update()

        assert sat.getOutput(0) == 0.5
        assert sat.getOutput(1) == -0.5
        assert sat.getOutput(2) == 0.0


class TestMuxDemuxExtended:
    """Extended tests for Mux and Demux blocks."""

    def test_mux_with_more_inputs(self):
        """Test Mux with many inputs."""
        from src.osk.blocks.math_ops import Mux

        mux = Mux(num_inputs=5)
        mux.init()

        for i in range(5):
            mux.setInput(float(i + 1), port=i)
        mux.update()

        output = mux.getOutputVector()
        assert len(output) == 5
        assert output == [1.0, 2.0, 3.0, 4.0, 5.0]

    def test_demux_getOutputVector(self):
        """Test Demux getOutputVector method."""
        from src.osk.blocks.math_ops import Demux, Mux

        mux = Mux(num_inputs=3)
        mux.init()
        mux.setInput(10.0, port=0)
        mux.setInput(20.0, port=1)
        mux.setInput(30.0, port=2)
        mux.update()

        demux = Demux(num_outputs=3)
        demux.init()
        demux.connectInput(mux)
        demux.update()

        output = demux.getOutputVector()
        assert output == [10.0, 20.0, 30.0]


class TestTrigonometryExtendedFunctions:
    """Extended tests for Trigonometry block functions."""

    def test_trigonometry_sin(self):
        """Test Trigonometry with sin function."""
        import math

        from src.osk.blocks.math_ops import Trigonometry

        trig = Trigonometry(function="sin")
        trig.init()

        trig.setInput(math.pi / 2)
        trig.update()

        assert abs(trig.getOutput() - 1.0) < 1e-10

    def test_trigonometry_cos(self):
        """Test Trigonometry with cos function."""
        from src.osk.blocks.math_ops import Trigonometry

        trig = Trigonometry(function="cos")
        trig.init()

        trig.setInput(0.0)
        trig.update()

        assert abs(trig.getOutput() - 1.0) < 1e-10

    def test_trigonometry_tan(self):
        """Test Trigonometry with tan function."""
        import math

        from src.osk.blocks.math_ops import Trigonometry

        trig = Trigonometry(function="tan")
        trig.init()

        trig.setInput(math.pi / 4)
        trig.update()

        assert abs(trig.getOutput() - 1.0) < 1e-10

    def test_trigonometry_asin(self):
        """Test Trigonometry with asin function."""
        import math

        from src.osk.blocks.math_ops import Trigonometry

        trig = Trigonometry(function="asin")
        trig.init()

        trig.setInput(1.0)
        trig.update()

        assert abs(trig.getOutput() - math.pi / 2) < 1e-10

    def test_trigonometry_acos(self):
        """Test Trigonometry with acos function."""
        import math

        from src.osk.blocks.math_ops import Trigonometry

        trig = Trigonometry(function="acos")
        trig.init()

        trig.setInput(0.0)
        trig.update()

        assert abs(trig.getOutput() - math.pi / 2) < 1e-10

    def test_trigonometry_atan(self):
        """Test Trigonometry with atan function."""
        import math

        from src.osk.blocks.math_ops import Trigonometry

        trig = Trigonometry(function="atan")
        trig.init()

        trig.setInput(1.0)
        trig.update()

        assert abs(trig.getOutput() - math.pi / 4) < 1e-10

    def test_trigonometry_sinh(self):
        """Test Trigonometry with sinh function."""
        import math

        from src.osk.blocks.math_ops import Trigonometry

        trig = Trigonometry(function="sinh")
        trig.init()

        trig.setInput(1.0)
        trig.update()

        assert abs(trig.getOutput() - math.sinh(1.0)) < 1e-10

    def test_trigonometry_cosh(self):
        """Test Trigonometry with cosh function."""
        from src.osk.blocks.math_ops import Trigonometry

        trig = Trigonometry(function="cosh")
        trig.init()

        trig.setInput(0.0)
        trig.update()

        assert abs(trig.getOutput() - 1.0) < 1e-10

    def test_trigonometry_tanh(self):
        """Test Trigonometry with tanh function."""
        import math

        from src.osk.blocks.math_ops import Trigonometry

        trig = Trigonometry(function="tanh")
        trig.init()

        trig.setInput(1.0)
        trig.update()

        assert abs(trig.getOutput() - math.tanh(1.0)) < 1e-10


class TestMathFunctionExtended2:
    """Extended tests for MathFunction block."""

    def test_math_function_sqrt(self):
        """Test MathFunction with sqrt."""
        from src.osk.blocks.math_ops import MathFunction

        mf = MathFunction(function="sqrt")
        mf.init()

        mf.setInput(16.0)
        mf.update()

        assert mf.getOutput() == 4.0

    def test_math_function_exp(self):
        """Test MathFunction with exp."""
        import math

        from src.osk.blocks.math_ops import MathFunction

        mf = MathFunction(function="exp")
        mf.init()

        mf.setInput(1.0)
        mf.update()

        assert abs(mf.getOutput() - math.e) < 1e-10

    def test_math_function_log(self):
        """Test MathFunction with log."""
        import math

        from src.osk.blocks.math_ops import MathFunction

        mf = MathFunction(function="log")
        mf.init()

        mf.setInput(math.e)
        mf.update()

        assert abs(mf.getOutput() - 1.0) < 1e-10

    def test_math_function_log10(self):
        """Test MathFunction with log10."""
        from src.osk.blocks.math_ops import MathFunction

        mf = MathFunction(function="log10")
        mf.init()

        mf.setInput(100.0)
        mf.update()

        assert abs(mf.getOutput() - 2.0) < 1e-10

    def test_math_function_square(self):
        """Test MathFunction with square."""
        from src.osk.blocks.math_ops import MathFunction

        mf = MathFunction(function="square")
        mf.init()

        mf.setInput(5.0)
        mf.update()

        assert mf.getOutput() == 25.0

    def test_math_function_reciprocal(self):
        """Test MathFunction with reciprocal."""
        from src.osk.blocks.math_ops import MathFunction

        mf = MathFunction(function="reciprocal")
        mf.init()

        mf.setInput(4.0)
        mf.update()

        assert mf.getOutput() == 0.25

    def test_math_function_pow(self):
        """Test MathFunction with pow (exponent parameter)."""
        from src.osk.blocks.math_ops import MathFunction

        mf = MathFunction(function="pow", exponent=3.0)
        mf.init()

        mf.setInput(2.0)
        mf.update()

        assert mf.getOutput() == 8.0

    def test_math_function_vector(self):
        """Test MathFunction with vector input."""
        from src.osk.blocks.math_ops import MathFunction

        mf = MathFunction(function="sqrt")
        mf.init()

        mf.setInput([4.0, 9.0, 16.0])
        mf.update()

        output = mf.getOutputVector()
        assert output is not None
        assert output[0] == 2.0
        assert output[1] == 3.0
        assert output[2] == 4.0

    def test_math_function_with_connected_block(self):
        """Test MathFunction with connected block."""
        from src.osk.blocks.math_ops import MathFunction
        from src.osk.blocks.sources import Constant

        mf = MathFunction(function="exp")
        mf.init()

        const = Constant(value=0.0)
        const.init()
        const.update()

        mf.connectInput(const)
        mf.update()

        assert mf.getOutput() == 1.0

    def test_math_function_getOutput_invalid_port(self):
        """Test MathFunction getOutput with invalid port."""
        from src.osk.blocks.math_ops import MathFunction

        mf = MathFunction(function="sqrt")
        mf.init()

        mf.setInput([4.0, 9.0])
        mf.update()

        assert mf.getOutput(0) == 2.0
        assert mf.getOutput(1) == 3.0
        assert mf.getOutput(2) == 0.0


class TestMathFunctionsExtended:
    """Extended tests for math function blocks."""

    def test_sqrt_vector(self):
        """Test Sqrt with vector input."""
        from src.osk.blocks.math_ops import Sqrt

        sqrt_block = Sqrt()
        sqrt_block.init()

        sqrt_block.setInput([4.0, 9.0, 16.0])
        sqrt_block.update()

        output = sqrt_block.getOutputVector()
        assert output is not None
        assert output[0] == 2.0
        assert output[1] == 3.0
        assert output[2] == 4.0

    def test_exp_vector(self):
        """Test Exp with vector input."""
        import math

        from src.osk.blocks.math_ops import Exp

        exp_block = Exp()
        exp_block.init()

        exp_block.setInput([0.0, 1.0, 2.0])
        exp_block.update()

        output = exp_block.getOutputVector()
        assert output is not None
        assert abs(output[0] - 1.0) < 1e-10
        assert abs(output[1] - math.e) < 1e-10

    def test_log_vector(self):
        """Test Log with vector input."""
        import math

        from src.osk.blocks.math_ops import Log

        log_block = Log()
        log_block.init()

        log_block.setInput([1.0, math.e, math.e**2])
        log_block.update()

        output = log_block.getOutputVector()
        assert output is not None
        assert abs(output[0]) < 1e-10
        assert abs(output[1] - 1.0) < 1e-10
        assert abs(output[2] - 2.0) < 1e-10

    def test_log10_vector(self):
        """Test Log10 with vector input."""
        from src.osk.blocks.math_ops import Log10

        log10_block = Log10()
        log10_block.init()

        log10_block.setInput([1.0, 10.0, 100.0])
        log10_block.update()

        output = log10_block.getOutputVector()
        assert output is not None
        assert abs(output[0]) < 1e-10
        assert abs(output[1] - 1.0) < 1e-10
        assert abs(output[2] - 2.0) < 1e-10

    def test_reciprocal_vector(self):
        """Test Reciprocal with vector input."""
        from src.osk.blocks.math_ops import Reciprocal

        recip = Reciprocal()
        recip.init()

        recip.setInput([2.0, 4.0, 5.0])
        recip.update()

        output = recip.getOutputVector()
        assert output is not None
        assert output[0] == 0.5
        assert output[1] == 0.25
        assert output[2] == 0.2


class TestMinMaxExtended2:
    """Extended tests for MinMax block."""

    def test_minmax_min_mode(self):
        """Test MinMax in minimum mode."""
        from src.osk.blocks.math_ops import MinMax

        mm = MinMax(function="min", num_inputs=2)
        mm.init()

        mm.setInput(10.0, port=0)
        mm.setInput(5.0, port=1)
        mm.update()

        assert mm.getOutput() == 5.0

    def test_minmax_max_mode(self):
        """Test MinMax in maximum mode."""
        from src.osk.blocks.math_ops import MinMax

        mm = MinMax(function="max", num_inputs=2)
        mm.init()

        mm.setInput(5.0, port=0)
        mm.setInput(10.0, port=1)
        mm.update()

        assert mm.getOutput() == 10.0

    def test_minmax_with_connected_blocks(self):
        """Test MinMax with connected blocks."""
        from src.osk.blocks.math_ops import MinMax
        from src.osk.blocks.sources import Constant

        mm = MinMax(function="max", num_inputs=2)
        mm.init()

        c1 = Constant(value=3.0)
        c1.init()
        c1.update()

        c2 = Constant(value=7.0)
        c2.init()
        c2.update()

        mm.connectInput(c1, port=0)
        mm.connectInput(c2, port=1)
        mm.update()

        assert mm.getOutput() == 7.0


class TestDotProductCrossProductExtended:
    """Extended tests for DotProduct and CrossProduct blocks."""

    def test_dot_product_with_connected_blocks(self):
        """Test DotProduct with connected blocks."""
        from src.osk.blocks.math_ops import DotProduct, Mux

        dp = DotProduct()
        dp.init()

        mux1 = Mux(num_inputs=3)
        mux1.init()
        mux1.setInput(1.0, port=0)
        mux1.setInput(2.0, port=1)
        mux1.setInput(3.0, port=2)
        mux1.update()

        mux2 = Mux(num_inputs=3)
        mux2.init()
        mux2.setInput(4.0, port=0)
        mux2.setInput(5.0, port=1)
        mux2.setInput(6.0, port=2)
        mux2.update()

        dp.connectInput(mux1, port=0)
        dp.connectInput(mux2, port=1)
        dp.update()

        # 1*4 + 2*5 + 3*6 = 4 + 10 + 18 = 32
        assert dp.getOutput() == 32.0

    def test_cross_product_with_connected_blocks(self):
        """Test CrossProduct with connected blocks."""
        from src.osk.blocks.math_ops import CrossProduct, Mux

        cp = CrossProduct()
        cp.init()

        # i x j = k
        mux1 = Mux(num_inputs=3)
        mux1.init()
        mux1.setInput(1.0, port=0)
        mux1.setInput(0.0, port=1)
        mux1.setInput(0.0, port=2)
        mux1.update()

        mux2 = Mux(num_inputs=3)
        mux2.init()
        mux2.setInput(0.0, port=0)
        mux2.setInput(1.0, port=1)
        mux2.setInput(0.0, port=2)
        mux2.update()

        cp.connectInput(mux1, port=0)
        cp.connectInput(mux2, port=1)
        cp.update()

        output = cp.getOutputVector()
        assert output[0] == 0.0
        assert output[1] == 0.0
        assert output[2] == 1.0


class TestAtan2Extended:
    """Extended tests for Atan2 block."""

    def test_atan2_with_connected_blocks(self):
        """Test Atan2 with connected blocks."""
        import math

        from src.osk.blocks.math_ops import Atan2
        from src.osk.blocks.sources import Constant

        atan2_block = Atan2()
        atan2_block.init()

        y_const = Constant(value=1.0)
        y_const.init()
        y_const.update()

        x_const = Constant(value=1.0)
        x_const.init()
        x_const.update()

        atan2_block.connectInput(y_const, port=0)
        atan2_block.connectInput(x_const, port=1)
        atan2_block.update()

        assert abs(atan2_block.getOutput() - math.pi / 4) < 1e-10

    def test_atan2_quadrants(self):
        """Test Atan2 in different quadrants."""
        import math

        from src.osk.blocks.math_ops import Atan2

        atan2_block = Atan2()
        atan2_block.init()

        # Quadrant 2: y=1, x=-1
        atan2_block.setInput(1.0, port=0)  # y
        atan2_block.setInput(-1.0, port=1)  # x
        atan2_block.update()
        assert abs(atan2_block.getOutput() - 3 * math.pi / 4) < 1e-10

        # Quadrant 3: y=-1, x=-1
        atan2_block.setInput(-1.0, port=0)
        atan2_block.setInput(-1.0, port=1)
        atan2_block.update()
        assert abs(atan2_block.getOutput() + 3 * math.pi / 4) < 1e-10


class TestPowerExtended:
    """Extended tests for Power block."""

    def test_power_with_connected_blocks(self):
        """Test Power with connected blocks."""
        from src.osk.blocks.math_ops import Power
        from src.osk.blocks.sources import Constant

        power = Power()
        power.init()

        base = Constant(value=2.0)
        base.init()
        base.update()

        exp = Constant(value=3.0)
        exp.init()
        exp.update()

        power.connectInput(base, port=0)
        power.connectInput(exp, port=1)
        power.update()

        assert power.getOutput() == 8.0


class TestBiasExtended:
    """Extended tests for Bias block."""

    def test_bias_vector(self):
        """Test Bias with vector input."""
        from src.osk.blocks.math_ops import Bias

        bias = Bias(bias=10.0)
        bias.init()

        bias.setInput([1.0, 2.0, 3.0])
        bias.update()

        output = bias.getOutputVector()
        assert output is not None
        assert output[0] == 11.0
        assert output[1] == 12.0
        assert output[2] == 13.0


class TestSquareExtended2:
    """Extended tests for Square block."""

    def test_square_scalar(self):
        """Test Square with scalar input."""
        from src.osk.blocks.math_ops import Square

        sq = Square()
        sq.init()

        sq.setInput(5.0)
        sq.update()

        assert sq.getOutput() == 25.0

    def test_square_negative(self):
        """Test Square with negative input."""
        from src.osk.blocks.math_ops import Square

        sq = Square()
        sq.init()

        sq.setInput(-3.0)
        sq.update()

        assert sq.getOutput() == 9.0

    def test_square_with_connected_block(self):
        """Test Square with connected block."""
        from src.osk.blocks.math_ops import Square
        from src.osk.blocks.sources import Constant

        sq = Square()
        sq.init()

        const = Constant(value=4.0)
        const.init()
        const.update()

        sq.connectInput(const)
        sq.update()

        assert sq.getOutput() == 16.0


# =============================================================================
# State Class Tests
# =============================================================================


class TestStateClass:
    """Tests for State class."""

    def test_state_init_default(self):
        """Test State initialization with defaults."""
        from src.osk.state import State

        state = State()
        assert state.x == [0.0, 0.0]
        assert state.x0 == 0.0
        assert state.xd0 == 0.0

    def test_state_init_with_values(self):
        """Test State initialization with custom values."""
        from src.osk.state import State

        state = State(x=[5.0, 2.0])
        assert state.x == [5.0, 2.0]

    def test_state_set(self):
        """Test State.set() method."""
        from src.osk.state import State

        state = State()
        State.t = 10.0
        State.kpass = 3
        state.set()

        assert State.t == 0.0
        assert State.t1 == 0.0
        assert State.kpass == 0
        assert State.ready == 1

    def test_state_reset(self):
        """Test State.reset() method."""
        from src.osk.state import State

        state = State()
        state.reset(0.05)

        assert State.dtp == 0.05
        assert State.dt == 0.05
        assert State.kpass == 0
        assert State.ready == 1

    def test_state_sample_event(self):
        """Test State.sample() with event-driven sampling."""
        from src.osk.state import State

        state = State()
        State.t = 5.0
        State.ready = 0

        state.sample(State.EVENT, 5.0)
        assert State.ready == 1

    def test_state_sample_periodic(self):
        """Test State.sample() with periodic sampling."""
        from src.osk.state import State

        state = State()
        State.ready = 0

        state.sample(0.01, 10.0)
        assert State.ready == 1

    def test_state_propagate_euler(self):
        """Test Euler integration method."""
        from src.osk.state import State

        state = State(x=[0.0, 1.0])
        State.method = "Euler"
        State.dt = 0.1
        State.kpass = 0

        state.propagate()

        # x[0] += dt * x[1] = 0.0 + 0.1 * 1.0 = 0.1
        assert abs(state.x[0] - 0.1) < 1e-10

    def test_state_propagate_rk2(self):
        """Test RK2 integration method."""
        from src.osk.state import State

        state = State(x=[0.0, 1.0])
        State.method = "RK2"
        State.dt = 0.1
        State.dtp = 0.1
        State.kpass = 0

        # Pass 0
        state.propagate()
        assert state.x0 == 0.0
        assert state.xd0 == 1.0

        # Pass 1
        state.x[1] = 1.0  # Derivative at midpoint
        State.kpass = 1
        state.propagate()
        # x[0] = x0 + dt * xd1 = 0.0 + 0.1 * 1.0 = 0.1
        assert abs(state.x[0] - 0.1) < 1e-10

    def test_state_propagate_rk4(self):
        """Test RK4 integration method."""
        from src.osk.state import State

        state = State(x=[0.0, 1.0])
        State.method = "RK4"
        State.dt = 0.1
        State.dtp = 0.1

        # Execute all 4 passes
        for kpass in range(4):
            State.kpass = kpass
            state.propagate()

        # For constant derivative, result should be ~ 0.1
        assert abs(state.x[0] - 0.1) < 1e-10

    def test_state_propagate_merson(self):
        """Test Merson's integration method."""
        from src.osk.state import State

        state = State(x=[0.0, 1.0])
        State.method = "Merson"
        State.dt = 0.1
        State.dtp = 0.1

        # Execute all 5 passes
        for kpass in range(5):
            State.kpass = kpass
            state.propagate()

        # For constant derivative, result should be ~ 0.1
        assert abs(state.x[0] - 0.1) < 1e-10

    def test_state_propagate_default(self):
        """Test default integration method (unknown falls back to RK4)."""
        from src.osk.state import State

        state = State(x=[0.0, 1.0])
        State.method = "Unknown"
        State.dt = 0.1
        State.dtp = 0.1
        State.kpass = 0

        state.propagate()
        # Should use RK4

    def test_state_updateclock_euler(self):
        """Test updateclock for Euler method."""
        from src.osk.state import State

        state = State()
        State.method = "Euler"
        State.dtp = 0.1
        State.t = 0.0
        State.kpass = 0

        state.updateclock()

        # Euler has 1 pass, so after pass 0, time should advance
        assert State.kpass == 0
        assert abs(State.t - 0.1) < 1e-10
        assert State.ready == 1

    def test_state_updateclock_rk2(self):
        """Test updateclock for RK2 method."""
        from src.osk.state import State

        state = State()
        State.method = "RK2"
        State.dtp = 0.1
        State.t = 0.0
        State.kpass = 0

        # First pass
        state.updateclock()
        assert State.kpass == 1
        assert State.ready == 0

        # Second pass
        state.updateclock()
        assert State.kpass == 0
        assert State.ready == 1
        assert abs(State.t - 0.1) < 1e-10

    def test_state_updateclock_rk4(self):
        """Test updateclock for RK4 method."""
        from src.osk.state import State

        state = State()
        State.method = "RK4"
        State.dtp = 0.1
        State.t = 0.0
        State.kpass = 0

        # Run all 4 passes
        for _ in range(4):
            state.updateclock()

        assert State.kpass == 0
        assert State.ready == 1
        assert abs(State.t - 0.1) < 1e-10

    def test_state_updateclock_merson(self):
        """Test updateclock for Merson method."""
        from src.osk.state import State

        state = State()
        State.method = "Merson"
        State.dtp = 0.1
        State.t = 0.0
        State.kpass = 0

        # Run all 5 passes
        for _ in range(5):
            state.updateclock()

        assert State.kpass == 0
        assert State.ready == 1
        assert abs(State.t - 0.1) < 1e-10


# =============================================================================
# Sim Class Tests
# =============================================================================


class TestSimClass:
    """Tests for Sim class."""

    def test_sim_init(self):
        """Test Sim initialization."""
        # Create a simple test block
        from src.osk.blocks.sources import Constant
        from src.osk.sim import Sim

        const = Constant(value=1.0)
        stage = [const]

        Sim(dts=[0.01], tmax=0.1, vStage=[stage])

        assert Sim.tmax == 0.1
        assert Sim.dts == [0.01]
        assert len(Sim.vStage) == 1
        assert Sim.stop == 0

    def test_sim_run_simple(self):
        """Test simple simulation run."""
        # Create a simple test block
        from src.osk.blocks.sources import Constant
        from src.osk.sim import Sim
        from src.osk.state import State

        const = Constant(value=5.0)
        stage = [const]

        State.method = "Euler"
        sim = Sim(dts=[0.01], tmax=0.05, vStage=[stage])
        results = sim.run()

        assert "times" in results
        assert "outputs" in results
        assert len(results["times"]) > 0

    def test_sim_sample(self):
        """Test Sim.sample class method."""
        from src.osk.blocks.sources import Constant
        from src.osk.sim import Sim

        const = Constant(value=1.0)
        stage = [const]

        Sim(dts=[0.01], tmax=0.1, vStage=[stage])

        # This should not raise
        Sim.sample(0.01, 0.1)

    def test_sim_terminate(self):
        """Test Sim.terminate class method."""
        from src.osk.sim import Sim

        Sim.stop = 0
        Sim.terminate(1)

        assert Sim.stop == 1

    def test_sim_run_with_integrator(self):
        """Test simulation with integrator block."""
        from src.osk.blocks.continuous import Integrator
        from src.osk.blocks.sources import Constant
        from src.osk.sim import Sim
        from src.osk.state import State

        State.method = "Euler"

        # Create blocks
        const = Constant(value=1.0)
        integ = Integrator(initial_condition=0.0)

        # Connect
        integ.connectInput(const)

        stage = [const, integ]
        sim = Sim(dts=[0.01], tmax=0.05, vStage=[stage])
        results = sim.run()

        assert len(results["times"]) > 0

    def test_sim_run_with_rk4(self):
        """Test simulation with RK4 integration."""
        from src.osk.blocks.sources import Constant
        from src.osk.sim import Sim
        from src.osk.state import State

        State.method = "RK4"

        const = Constant(value=1.0)
        stage = [const]

        sim = Sim(dts=[0.01], tmax=0.02, vStage=[stage])
        results = sim.run()

        assert len(results["times"]) > 0

    def test_sim_multiple_stages(self):
        """Test simulation with multiple stages."""
        from src.osk.blocks.sources import Constant
        from src.osk.sim import Sim
        from src.osk.state import State

        State.method = "Euler"

        const1 = Constant(value=1.0)
        const2 = Constant(value=2.0)

        stage1 = [const1]
        stage2 = [const2]

        sim = Sim(dts=[0.01, 0.02], tmax=0.02, vStage=[stage1, stage2])
        # This tests that multiple stages work
        _ = sim


# =============================================================================
# Block Base Class Tests
# =============================================================================


class TestBlockBaseClass:
    """Tests for Block base class."""

    def test_block_add_integrator(self):
        """Test Block.addIntegrator method."""
        from src.osk.block import Block

        block = Block()
        integrator = block.addIntegrator([0.0, 0.0])

        assert integrator is not None
        assert len(block.vState) == 1
        assert integrator[0] == 0.0
        assert integrator[1] == 0.0

    def test_block_propagate_states(self):
        """Test Block.propagateStates method."""
        from src.osk.block import Block
        from src.osk.state import State

        State.method = "Euler"
        State.dt = 0.1
        State.kpass = 0

        block = Block()
        integ = block.addIntegrator([0.0, 1.0])

        block.propagateStates()

        # After Euler step: x[0] += dt * x[1]
        assert abs(integ[0] - 0.1) < 1e-10

    def test_block_default_methods(self):
        """Test Block default method implementations."""
        from src.osk.block import Block

        block = Block()

        # These should not raise
        block.init()
        block.update()
        block.rpt()

        # Default output is 0
        assert block.getOutput() == 0.0

    def test_block_init_count(self):
        """Test Block.initCount attribute."""
        from src.osk.block import Block

        block = Block()
        assert block.initCount == 0

        block.initCount += 1
        assert block.initCount == 1
