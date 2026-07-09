"""Regression tests for numerical integration order and stage timing."""

import math

import pytest

from src.models.model import Model
from src.models.simulation import SimulationConfig, SolverType
from src.osk.block import Block
from src.osk.blocks.continuous import TransportDelay
from src.osk.blocks.discrete import UnitDelay
from src.osk.sim import Sim
from src.osk.state import State
from src.simulation.compiler import ModelCompiler
from src.simulation.osk_adapter import OSKAdapter


@pytest.fixture(autouse=True)
def restore_global_state_timing():
    attributes = ("t", "t1", "dt", "dtp", "ready", "kpass", "method")
    previous = {attribute: getattr(State, attribute) for attribute in attributes}
    yield
    for attribute, value in previous.items():
        setattr(State, attribute, value)


class DecayBlock(Block):
    """Autonomous decay system x' = -x."""

    def __init__(self, x0: float = 1.0):
        super().__init__()
        self.s = State([x0, 0.0])

    def update(self):
        self.s.x[1] = -self.s.x[0]

    def propagateStates(self):
        self.s.propagate()

    def getOutput(self, port=0):
        return self.s.x[0]


class DrivenBlock(DecayBlock):
    """Driven system x' = sin(t)."""

    def __init__(self):
        super().__init__(x0=0.0)

    def update(self):
        self.s.x[1] = math.sin(State.t)


def _kernel_decay_error(method: str, step_size: float) -> float:
    State.method = method
    block = DecayBlock()
    Sim(dts=[step_size], tmax=1.0, vStage=[[block]]).run()
    return abs(block.getOutput() - math.exp(-1.0))


def _kernel_driven_error(method: str, step_size: float) -> float:
    State.method = method
    block = DrivenBlock()
    Sim(dts=[step_size], tmax=1.0, vStage=[[block]]).run()
    return abs(block.getOutput() - (1.0 - math.cos(1.0)))


def _adapter_driven_error(step_size: float) -> float:
    model = Model.model_validate(
        {
            "id": "driven-convergence",
            "metadata": {"name": "Driven convergence"},
            "blocks": [
                {
                    "id": "sine",
                    "type": "sine_wave",
                    "name": "sin(t)",
                    "position": {"x": 0, "y": 0},
                    "parameters": {
                        "amplitude": 1.0,
                        "frequency": 1.0 / (2.0 * math.pi),
                        "phase": 0.0,
                        "bias": 0.0,
                    },
                    "outputPorts": [{"id": "sine-out", "name": "out"}],
                },
                {
                    "id": "integrator",
                    "type": "integrator",
                    "name": "Integral",
                    "position": {"x": 100, "y": 0},
                    "parameters": {"initialCondition": 0.0},
                    "inputPorts": [{"id": "integrator-in", "name": "in"}],
                    "outputPorts": [{"id": "integrator-out", "name": "out"}],
                },
                {
                    "id": "scope",
                    "type": "scope",
                    "name": "Scope",
                    "position": {"x": 200, "y": 0},
                    "parameters": {"numInputs": 1},
                    "inputPorts": [{"id": "scope-in", "name": "in"}],
                },
            ],
            "connections": [
                {
                    "id": "sine-to-integrator",
                    "sourceBlockId": "sine",
                    "sourcePortId": "sine-out",
                    "targetBlockId": "integrator",
                    "targetPortId": "integrator-in",
                },
                {
                    "id": "integrator-to-scope",
                    "sourceBlockId": "integrator",
                    "sourcePortId": "integrator-out",
                    "targetBlockId": "scope",
                    "targetPortId": "scope-in",
                },
            ],
        }
    )
    compiled = ModelCompiler().compile(model)
    adapter = OSKAdapter()
    adapter.initialize(
        compiled,
        SimulationConfig(solver=SolverType.RK4, step_size=step_size, stop_time=1.0),
    )

    for step in range(round(1.0 / step_size)):
        adapter.step(step * step_size, step_size)

    value = adapter._osk_blocks["integrator"].getOutput()
    return abs(value - (1.0 - math.cos(1.0)))


@pytest.mark.parametrize(
    ("method", "minimum_ratio"),
    [
        ("Euler", 1.7),
        ("RK2", 3.2),
        ("RK4", 12.0),
        ("Merson", 12.0),
    ],
)
def test_kernel_autonomous_convergence_order(method: str, minimum_ratio: float):
    coarse_error = _kernel_decay_error(method, 0.1)
    fine_error = _kernel_decay_error(method, 0.05)

    assert coarse_error / fine_error > minimum_ratio


def test_kernel_rk4_driven_convergence_order():
    coarse_error = _kernel_driven_error("RK4", 0.1)
    fine_error = _kernel_driven_error("RK4", 0.05)

    assert coarse_error / fine_error > 12.0


def test_adapter_rk4_driven_convergence_order():
    coarse_error = _adapter_driven_error(0.1)
    fine_error = _adapter_driven_error(0.05)

    assert coarse_error / fine_error > 12.0


def test_discrete_block_does_not_sample_intermediate_stage_time():
    delay = UnitDelay(initial_condition=0.0, sample_time=0.1)
    delay.init()
    State.t = 0.0
    State.ready = 1
    delay.setInput(1.0)
    delay.update()

    State.t = 0.1
    State.ready = 0
    delay.setInput(2.0)
    delay.update()

    assert delay.prev_value == 1.0
    assert delay.last_sample_time == 0.0


def test_transport_delay_buffers_only_major_step_samples():
    delay = TransportDelay(delay_time=0.1)
    delay.init()
    State.t = 0.0
    State.ready = 1
    delay.setInput(1.0)
    delay.update()

    State.t = 0.05
    State.ready = 0
    delay.setInput(2.0)
    delay.update()

    assert delay.time_buffer == [0.0]
    assert delay.buffer == [1.0]
