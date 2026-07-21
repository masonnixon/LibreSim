"""Behavioral edge coverage for the remaining small OSK block modules."""

import pytest

from src.osk.blocks.control_design import LQRController, PolePlacement
from src.osk.blocks.data_types import ComplexToRealImag, DataTypeConversion, RealImagToComplex
from src.osk.blocks.logic import LogicalOperator, RelationalOperator
from src.osk.blocks.sinks import Scope, Scope3D, ToWorkspace
from src.osk.blocks.subsystems import Inport, Outport, Subsystem
from src.osk.context import SimContext
from src.osk.state import State


class ScalarSource:
    def __init__(self, value=0.0):
        self.value = value

    def getOutput(self, port=0):
        return self.value + port


class VectorSource(ScalarSource):
    def __init__(self, vector):
        super().__init__(vector[0] if vector else 0.0)
        self.vector = vector

    def getOutputVector(self):
        return self.vector


def test_state_feedback_scalar_sources_invalid_ports_and_outputs():
    default = LQRController()
    assert (default.num_inputs, default.num_states, default.K) == (1, 1, [[1.0]])

    source = VectorSource(None)
    lqr = LQRController(K=[[2.0]], num_states=1, num_inputs=1)
    lqr.setInput(9.0, 1)
    lqr.connectInput(source)
    lqr.update()
    assert lqr.getOutput() == 0.0
    assert lqr.getOutput(2) == 0.0

    placement = PolePlacement(K=[3.0])
    placement.setInput(9.0, 1)
    placement.connectInput(source)
    placement.update()
    assert placement.getOutput() == 0.0


def test_data_type_fallback_rounding_unknown_type_and_invalid_ports():
    conversion = DataTypeConversion(output_type="unknown", round_mode="unknown")
    assert conversion._round_value(1.6) == 2
    conversion.setInput(3.5)
    conversion.update()
    assert conversion.getOutput() == 3.5

    for block in [RealImagToComplex(), ComplexToRealImag()]:
        block.setInput(9.0, 2)
        block.connectInput(ScalarSource(9.0), 2)
        block.update()
        assert block.getOutputVector() == [0.0, 0.0]


def test_logic_scalar_protocols_and_vector_fallback_elements():
    relation = RelationalOperator(operator=">")
    relation.connectInput(ScalarSource(3.0), 0, source_port=1)
    relation.connectInput(VectorSource(None), 1, source_port=0)
    relation.update()
    assert relation.getOutput() == 1.0

    logical = LogicalOperator(operator="AND", num_inputs=2)
    logical.connectInput(ScalarSource(1.0), 0)
    logical.connectInput(VectorSource(None), 1)
    logical.update()
    assert logical.getOutput() == 0.0

    logical.input_blocks = [None, None]
    logical.setInput([1.0, 0.0], 0)
    logical.setInput(1.0, 1)
    logical.update()
    assert logical.getOutputVector() == [1.0, 0.0]


def test_scope_vector_to_scalar_transition_recording_and_stage_guard():
    source = VectorSource([1.0, 2.0])
    scope = Scope(num_inputs=1)
    scope.context = SimContext(t=1.0, ready=1)
    scope.connectInput(source, 0)
    scope.update()
    scope.update()  # Cached vector names must remain stable.
    scope.rpt()
    assert scope.getData()["values"] == [[1.0], [2.0]]

    source.vector = None
    source.value = 3.0
    scope.update()
    assert scope._vector_inputs == {}
    scope.context.ready = 0
    scope.rpt()
    assert scope.times == [1.0]

    workspace = ToWorkspace()
    workspace.context = SimContext(ready=0)
    workspace.rpt()
    assert workspace.getData()["values"] == []


def test_subsystem_scalar_vector_protocols_invalid_ports_and_outputs():
    scalar = ScalarSource(2.0)
    vector = VectorSource([3.0, 4.0])

    inport = Inport()
    inport.connectInput(vector)
    inport.update()
    assert inport.getOutputVector() == [3.0, 4.0]
    vector.vector = None
    inport.update()
    assert inport.getOutputVector() is None
    inport.connectInput(scalar, source_port=1)
    inport.update()
    assert inport.getOutput() == 3.0

    outport = Outport()
    outport.connectInput(scalar, source_port=1)
    outport.update()
    assert outport.getOutput() == 3.0

    subsystem = Subsystem(num_inputs=1, num_outputs=1)
    subsystem.setInput(9.0, 2)
    subsystem.connectInput(scalar, 2)
    subsystem.setOutportBlock(1, scalar)
    subsystem.update()
    assert subsystem.getOutput(2) == 0.0
    assert subsystem.getOutputVector() is None

    subsystem.setOutportBlock(1, VectorSource(None))
    subsystem.update()
    assert subsystem.getOutputVector() is None
    subsystem.setOutportBlock(1, VectorSource([5.0, 6.0]))
    subsystem.update()
    assert subsystem.getOutputVector() == [5.0, 6.0]


def test_scope3d_invalid_ports_connections_and_stage_guard():
    scope = Scope3D()
    scope.context = SimContext(t=2.0, ready=0)
    scope.setInput(9.0, 3)
    scope.connectInput(ScalarSource(1.0), 0, source_port=2)
    scope.connectInput(ScalarSource(9.0), 3)
    scope.update()
    scope.rpt()
    assert scope.inputs == [3.0, 0.0, 0.0]
    assert scope.getData()["times"] == []


@pytest.mark.parametrize(
    ("method", "last_pass"), [("Euler", 1), ("RK2", 2), ("RK4", 4), ("Merson", 5)]
)
def test_state_propagators_ignore_out_of_range_integration_passes(method, last_pass):
    context = SimContext(dt=0.1, method=method, kpass=last_pass)
    state = State([2.0, 3.0], context=context)
    state.propagate()
    assert state.x == [2.0, 3.0]
