"""Behavioral coverage for continuous block vector and delay edge paths."""

import pytest

from src.osk.blocks.continuous import Derivative, Integrator, TransportDelay, ZeroPole
from src.osk.context import SimContext


class ScalarSource:
    def __init__(self, value):
        self.value = value

    def getOutput(self, port=0):
        return self.value


class VectorSource(ScalarSource):
    def __init__(self, vector=None, value=0.0):
        super().__init__(value)
        self.vector = vector

    def getOutputVector(self):
        return self.vector


def test_integrator_reconfigures_vector_initial_conditions_and_limits():
    block = Integrator([2.0], limit_output=True, lower_limit=-1.0, upper_limit=1.0)
    block.setInput([3.0, -4.0, 5.0])
    block.init()
    assert [state[0] for state in block._states] == [2.0, 0.0, 0.0]

    block._states[0][:] = [2.0, 0.0]
    block._states[1][:] = [-2.0, 0.0]
    block.setInput([3.0, -4.0, 5.0])
    block.update()
    assert [state[1] for state in block._states] == [0.0, 0.0, 5.0]
    assert block.getOutput() == 1.0
    assert block.getOutput(1) == -1.0
    assert block.getOutput(9) == 0.0
    assert block.getOutputVector() == [1.0, -1.0, 0.0]


def test_integrator_external_initial_condition_and_signal_protocols():
    missing_ic = Integrator(external_ic=True)
    missing_ic.init()
    missing_ic.update()
    assert missing_ic._ic_initialized is True
    assert missing_ic.getOutput() == 0.0

    block = Integrator([0.0, 0.0], external_ic=True)
    block.init()
    block.connectInput(ScalarSource(4.0), port=1, source_port=3)
    block.connectInput(VectorSource([1.0, 2.0]), port=0)
    block.connectInput(ScalarSource(99.0), port=2)
    block.update()
    assert block.getOutputVector() == [4.0, 4.0]
    assert [state[1] for state in block._states] == [1.0, 2.0]

    scalar_vector_protocol = Integrator(external_ic=True)
    scalar_vector_protocol.init()
    scalar_vector_protocol.connectInput(VectorSource(None, 6.0), port=0)
    scalar_vector_protocol.update()
    assert scalar_vector_protocol.x[1] == 6.0

    scalar_protocol = Integrator(external_ic=True)
    scalar_protocol.init()
    scalar_protocol.connectInput(ScalarSource(7.0), port=0)
    scalar_protocol.update()
    assert scalar_protocol.x[1] == 7.0

    scalar_ic = Integrator(external_ic=True)
    scalar_ic.init()
    scalar_ic.connectInput(ScalarSource(5.0), port=1)
    scalar_ic.update()
    assert scalar_ic.getOutput() == 5.0

    empty_vector_ic = Integrator([], external_ic=True)
    empty_vector_ic.connectInput(ScalarSource(5.0), port=1)
    empty_vector_ic.update()
    assert empty_vector_ic._ic_initialized is True
    assert empty_vector_ic.getOutputVector() is None


def test_integrator_standard_scalar_and_vector_source_protocols():
    scalar = Integrator(limit_output=True, lower_limit=-1.0, upper_limit=1.0)
    scalar.init()
    scalar.connectInput(ScalarSource(3.0), source_port=2)
    scalar.update()
    assert scalar.x[1] == 3.0
    scalar.x[:] = [2.0, 3.0]
    scalar.update()
    assert scalar.x[1] == 0.0
    assert scalar.getOutput() == 1.0
    assert scalar.getOutputVector() is None

    vector = Integrator()
    vector.init()
    vector.connectInput(VectorSource([2.0, 3.0]))
    vector.update()
    assert [state[1] for state in vector._states] == [2.0, 3.0]

    vector_fallback = Integrator()
    vector_fallback.init()
    vector_fallback.connectInput(VectorSource(None, 8.0))
    vector_fallback.update()
    assert vector_fallback.x[1] == 8.0


def test_derivative_vector_lifecycle_and_source_protocols():
    derivative = Derivative(coefficient=2.0)
    derivative.setInput([3.0, 4.0])
    derivative.init()
    derivative.update()
    assert derivative.getOutputVector() == [6.0, 8.0]
    assert derivative.getOutput() == 6.0
    assert derivative.getOutput(9) == 0.0

    derivative.connectInput(VectorSource([5.0, 6.0]))
    derivative.update()
    assert derivative.getOutputVector() == [10.0, 12.0]

    scalar_fallback = Derivative(coefficient=3.0)
    scalar_fallback.connectInput(VectorSource(None, 4.0), source_port=2)
    scalar_fallback.update()
    assert scalar_fallback.getOutput() == 12.0
    assert scalar_fallback.getOutputVector() is None

    no_vector_method = Derivative(coefficient=4.0)
    no_vector_method.connectInput(ScalarSource(2.0))
    no_vector_method.update()
    assert no_vector_method.getOutput() == 8.0


def test_empty_vectors_and_short_internal_buffers_are_safe():
    empty_integrator = Integrator([])
    empty_integrator.init()
    empty_integrator.update()
    assert empty_integrator.getOutput() == 0.0
    assert empty_integrator.getOutputVector() is None

    integrator = Integrator([0.0, 0.0])
    integrator._input_vector = []
    integrator.setInput([1.0, 2.0])
    assert integrator._input_vector == []

    derivative = Derivative()
    derivative._setup_vector_mode(2)
    derivative._input_vector = []
    derivative.setInput([1.0, 2.0])
    assert derivative._input_vector == []


def test_transport_delay_empty_single_interpolated_duplicate_and_beyond_buffers():
    delay = TransportDelay(delay_time=1.0, initial_output=-1.0)
    delay.context = SimContext(t=1.0, ready=0)
    delay.update()
    assert delay.getOutput() == -1.0

    delay.time_buffer = [0.0]
    delay.buffer = [5.0]
    delay.update()
    assert delay.getOutput() == 5.0

    delay.time_buffer = [0.0, 2.0]
    delay.buffer = [0.0, 20.0]
    delay.context.t = 2.0
    delay.update()
    assert delay.getOutput() == pytest.approx(10.0)

    delay.time_buffer = [1.0, 1.0]
    delay.buffer = [7.0, 8.0]
    delay.context.t = 2.0
    delay.update()
    assert delay.getOutput() == 7.0

    delay.time_buffer = [0.0, 0.5]
    delay.buffer = [2.0, 3.0]
    delay.context.t = 3.0
    delay.update()
    assert delay.getOutput() == 3.0

    delay.connectInput(ScalarSource(9.0))
    delay.context.ready = 1
    delay.context.t = 0.5
    delay.update()
    assert delay.buffer[-1] == 9.0
    assert delay.getOutput() == -1.0


def test_zero_pole_static_gain_and_multistate_derivative():
    static = ZeroPole(zeros=[], poles=[-1.0], gain=3.0)
    static.poles = []
    static._build_state_space()
    static.connectInput(ScalarSource(2.0))
    static.update()
    assert static.getOutput() == 6.0

    dynamic = ZeroPole(zeros=[], poles=[-1.0, -2.0], gain=1.0)
    dynamic.init()
    dynamic.setInput(4.0)
    dynamic.update()
    assert dynamic.states[0][1] == 0.0
    assert dynamic.states[1][1] == 4.0
    assert dynamic.getOutput() == 0.0
