"""Tests for OSK simulation blocks."""

import pytest

from src.osk.blocks.continuous import Integrator
from src.osk.blocks.math_ops import Gain, Sum
from src.osk.blocks.sinks import Scope
from src.osk.blocks.sources import Constant, Step
from src.osk.state import State


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
