"""Regression tests for numerical integration order and stage timing."""

import math

import pytest

from src.osk.block import Block
from src.osk.sim import Sim
from src.osk.state import State


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


def _kernel_decay_error(method: str, step_size: float) -> float:
    State.method = method
    block = DecayBlock()
    Sim(dts=[step_size], tmax=1.0, vStage=[[block]]).run()
    return abs(block.getOutput() - math.exp(-1.0))


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
