"""Behavioral coverage for aerospace and nonlinear block edge paths."""

import math

import pytest

from src.osk.blocks.aerospace import (
    DCMToQuaternion,
    EulerToQuaternion,
    FlatEarthGravity,
    ISAAtmosphere,
    QuaternionConjugate,
    QuaternionMultiply,
    QuaternionNormalize,
    QuaternionRotateVector,
    QuaternionToDCM,
    QuaternionToEuler,
    SixDOFEuler,
    WGS84Gravity,
)
from src.osk.blocks.nonlinear import (
    HitCrossing,
    Hysteresis,
    LookupTable1D,
    LookupTable2D,
    Quantizer,
    SlewRateLimiter,
    Stiction,
    VariableTransportDelay,
    WrapToRange,
)
from src.osk.context import SimContext


class Source:
    def __init__(self, scalar=0.0, vector=None):
        self.scalar = scalar
        self.vector = vector

    def getOutput(self, port=0):
        return self.scalar

    def getOutputVector(self):
        return self.vector


def test_quaternion_blocks_source_protocols_scalar_ports_and_invalid_outputs():
    normalize = QuaternionNormalize()
    normalize.connectInput(Source(vector=[0.0, 0.0, 0.0, 0.0]))
    normalize.update()
    assert normalize.getOutputVector() == [1.0, 0.0, 0.0, 0.0]
    assert normalize.getOutput() == 1.0
    assert normalize.getOutput(4) == 0.0
    normalize.setInput(2.0, 1)
    normalize.setInput(9.0, 4)
    assert normalize.input == [0.0, 2.0, 0.0, 0.0]
    normalize.connectInput(Source(vector=[1.0]))
    normalize.update()
    assert normalize.getOutputVector() == [0.0, 1.0, 0.0, 0.0]

    multiply = QuaternionMultiply()
    multiply.connectInput(Source(vector=[0.0, 1.0, 0.0, 0.0]), 0)
    multiply.connectInput(Source(vector=[0.0, 0.0, 1.0, 0.0]), 1)
    multiply.connectInput(Source(vector=[1.0, 0.0, 0.0, 0.0]), 2)
    multiply.update()
    assert multiply.getOutputVector() == [0.0, 0.0, 0.0, 1.0]
    assert multiply.getOutput() == 0.0
    assert multiply.getOutput(4) == 0.0

    conjugate = QuaternionConjugate()
    conjugate.connectInput(Source(vector=[1.0, 2.0, 3.0, 4.0]))
    conjugate.update()
    assert conjugate.getOutputVector() == [1.0, -2.0, -3.0, -4.0]
    assert conjugate.getOutput() == 1.0
    assert conjugate.getOutput(4) == 0.0


def test_quaternion_euler_clamp_sources_and_rotation_ports():
    to_euler = QuaternionToEuler()
    to_euler.connectInput(Source(vector=[math.sqrt(0.5), 0.0, math.sqrt(0.5), 0.0]))
    to_euler.update()
    assert to_euler.getOutput(1) == pytest.approx(math.pi / 2)
    assert to_euler.getOutput(3) == 0.0

    to_quaternion = EulerToQuaternion()
    to_quaternion.setInput(math.pi / 2, 2)
    to_quaternion.setInput(9.0, 3)
    to_quaternion.connectInput(Source(vector=[0.0, 0.0, math.pi]))
    to_quaternion.update()
    assert to_quaternion.getOutputVector() == pytest.approx([0.0, 0.0, 0.0, 1.0], abs=1e-12)
    assert to_quaternion.getOutput() == pytest.approx(0.0, abs=1e-12)
    assert to_quaternion.getOutput(4) == 0.0

    rotate = QuaternionRotateVector()
    rotate.setInput([1.0], 0)
    rotate.connectInput(Source(vector=[1.0, 0.0, 0.0, 0.0]), 0)
    rotate.connectInput(Source(vector=[1.0, 2.0, 3.0]), 1)
    rotate.connectInput(Source(vector=[9.0]), 2)
    rotate.update()
    assert rotate.getOutputVector() == [1.0, 2.0, 3.0]
    assert rotate.getOutput() == 1.0
    assert rotate.getOutput(3) == 0.0


@pytest.mark.parametrize(
    ("dcm", "expected"),
    [
        ([1, 0, 0, 0, -1, 0, 0, 0, -1], [0, 1, 0, 0]),
        ([-1, 0, 0, 0, 1, 0, 0, 0, -1], [0, 0, 1, 0]),
        ([-1, 0, 0, 0, -1, 0, 0, 0, 1], [0, 0, 0, 1]),
    ],
)
def test_dcm_negative_trace_branches(dcm, expected):
    block = DCMToQuaternion()
    block.connectInput(Source(vector=dcm))
    block.update()
    assert block.getOutputVector() == pytest.approx(expected)
    assert block.getOutput() == pytest.approx(expected[0])
    assert block.getOutput(4) == 0.0


def test_atmosphere_dcm_gravity_and_six_dof_connected_sources():
    to_dcm = QuaternionToDCM()
    to_dcm.connectInput(Source(vector=[1.0, 0.0, 0.0, 0.0]))
    to_dcm.update()
    assert to_dcm.getOutput() == 1.0
    assert to_dcm.getOutput(9) == 0.0

    atmosphere = ISAAtmosphere()
    atmosphere.connectInput(Source(scalar=12000.0))
    atmosphere.update()
    assert atmosphere.getOutput() == pytest.approx(216.65)
    assert atmosphere.getOutput(4) == 0.0

    six_dof = SixDOFEuler()
    six_dof.init()
    six_dof.connectInput(Source(vector=[1.0, 2.0, 3.0]), 0)
    six_dof.connectInput(Source(vector=[4.0, 5.0, 6.0]), 1)
    six_dof.connectInput(Source(vector=[9.0]), 2)
    six_dof.theta[0] = math.pi / 2
    six_dof.update()
    assert [six_dof.u[1], six_dof.v[1], six_dof.w[1]] == [1.0, 2.0, 3.0]
    assert six_dof.psi[1] == 0.0
    assert six_dof.getOutput() == 0.0
    assert six_dof.getOutput(12) == 0.0

    flat = FlatEarthGravity(9.8)
    flat.connectInput(Source(vector=[1.0, 2.0, 3.0]))
    flat.update()
    assert flat.getOutputVector() == [0.0, 0.0, 9.8]
    assert flat.getOutput() == 0.0

    gravity = WGS84Gravity()
    gravity.setInput(math.pi / 2, 0)
    gravity.setInput(100.0, 1)
    gravity.setInput(9.0, 2)
    gravity.connectInput(Source(vector=[0.0, 0.0]))
    gravity.update()
    assert gravity.getOutput() == pytest.approx(gravity.ge)


def test_aerospace_invalid_shapes_leave_inputs_unchanged():
    multiply = QuaternionMultiply()
    multiply.setInput(1.0)
    multiply.connectInput(Source(vector=[1.0]), 0)
    multiply.connectInput(Source(vector=None), 1)
    multiply.update()
    assert multiply.getOutputVector() == [1.0, 0.0, 0.0, 0.0]

    for block, original in [
        (QuaternionConjugate(), [1.0, 0.0, 0.0, 0.0]),
        (QuaternionToEuler(), [1.0, 0.0, 0.0, 0.0]),
        (QuaternionToDCM(), [1.0, 0.0, 0.0, 0.0]),
    ]:
        block.setInput(1.0)
        block.connectInput(Source(vector=[1.0]))
        block.update()
        assert block.input == original

    to_quaternion = EulerToQuaternion()
    to_quaternion.connectInput(Source(vector=[1.0]))
    to_quaternion.update()
    assert to_quaternion.input == [0.0, 0.0, 0.0]

    rotate = QuaternionRotateVector()
    rotate.setInput(1.0)
    rotate.connectInput(Source(vector=None), 0)
    rotate.connectInput(Source(vector=[1.0]), 1)
    rotate.update()
    assert rotate.getOutputVector() == [0.0, 0.0, 0.0]

    dcm = DCMToQuaternion()
    dcm.setInput([1.0])
    dcm.connectInput(Source(vector=[1.0]))
    dcm.update()
    assert dcm.getOutputVector() == [1.0, 0.0, 0.0, 0.0]

    six_dof = SixDOFEuler()
    six_dof.setInput(1.0, 0)
    six_dof.setInput([1.0], 1)
    six_dof.setInput([1.0, 2.0, 3.0], 2)
    six_dof.connectInput(Source(vector=[1.0]), 0)
    six_dof.connectInput(Source(vector=None), 1)
    six_dof.update()
    assert six_dof.forces == [0.0, 0.0, 0.0]
    assert six_dof.moments == [0.0, 0.0, 0.0]

    gravity = WGS84Gravity()
    gravity.connectInput(Source(vector=[1.0]))
    gravity.update()
    assert gravity.input == [0.0, 0.0]


def test_lookup_tables_degenerate_boundaries_and_connected_inputs():
    assert LookupTable1D([], [])._interpolate(1.0) == 0.0
    assert LookupTable1D([1.0], [4.0])._interpolate(9.0) == 4.0
    duplicate = LookupTable1D([0.0, 0.0, 1.0], [2.0, 3.0, 4.0])
    assert duplicate._interpolate(0.0) == 2.0
    duplicate_upper = LookupTable1D([0.0, 1.0, 1.0], [2.0, 3.0, 4.0])
    assert duplicate_upper._interpolate(1.0) == 4.0
    duplicate.connectInput(Source(scalar=0.5))
    duplicate.update()
    assert duplicate.getOutput() == pytest.approx(3.5)

    empty = LookupTable2D([], [], [])
    assert empty._interpolate(0.0, 0.0) == 0.0
    assert LookupTable2D([0.0], [], [])._interpolate(0.0, 0.0) == 0.0
    table = LookupTable2D([0.0, 1.0], [0.0, 1.0], [[0.0, 1.0], [2.0, 3.0]])
    assert table._interpolate(2.0, 2.0) == 3.0
    table.connectInput(Source(scalar=0.5), 0)
    table.connectInput(Source(scalar=0.5), 1)
    table.connectInput(Source(scalar=99.0), 2)
    table.setInput(99.0, 2)
    table.update()
    assert table.getOutput() == pytest.approx(1.5)
    malformed = LookupTable2D([0.0, 1.0], [0.0, 1.0], [[]])
    assert malformed._interpolate(0.5, 0.5) == 0.0


def test_variable_delay_empty_duplicate_interpolated_and_beyond_buffers():
    delay = VariableTransportDelay(max_delay=2.0)
    delay.context = SimContext(t=1.0, ready=0)
    delay.setInput(5.0, 0)
    delay.setInput(0.0, 1)
    delay.setInput(9.0, 2)
    delay.connectInput(Source(), 2)
    delay.update()
    assert delay.getOutput() == 5.0

    delay.buffer = [(0.0, 1.0), (0.0, 2.0)]
    delay.inputs[1] = 1.0
    delay.update()
    assert delay.getOutput() == 1.0

    delay.buffer = [(0.0, 0.0), (2.0, 20.0)]
    delay.inputs[1] = 0.0
    delay.context.t = 1.0
    delay.update()
    assert delay.getOutput() == pytest.approx(10.0)

    delay.buffer = [(0.0, 2.0), (0.5, 3.0)]
    delay.context.t = 3.0
    delay.update()
    assert delay.getOutput() == 3.0


def test_nonlinear_connected_protocols_and_state_transitions():
    quantizer = Quantizer(0.5)
    quantizer.init()
    assert quantizer.getOutput() == 0.0

    wrapped = WrapToRange(lower=1.0, upper=1.0)
    wrapped.connectInput(Source(scalar=9.0), source_port=2)
    wrapped.update()
    assert wrapped.getOutput() == 1.0

    crossing = HitCrossing(threshold=1.0, direction="either")
    crossing.connectInput(Source(scalar=2.0), source_port=2)
    crossing.update()
    assert crossing.getOutput() == 1.0

    hysteresis = Hysteresis(upper_threshold=1.0, lower_threshold=-1.0)
    source = Source(scalar=2.0)
    hysteresis.connectInput(source, source_port=2)
    hysteresis.update()
    assert hysteresis.getOutput() == 1.0
    source.scalar = -2.0
    hysteresis.update()
    assert hysteresis.getOutput() == 0.0

    stiction = Stiction(breakaway_force=1.0, velocity_threshold=0.1)
    force = Source(scalar=2.0)
    velocity = Source(scalar=1.0)
    stiction.connectInput(force, 0)
    stiction.connectInput(velocity, 1)
    stiction.connectInput(Source(), 2)
    stiction.setInput(9.0, 2)
    stiction.update()
    assert stiction.getOutput() == 2.0
    stiction.update()
    assert stiction.is_stuck is False
    force.scalar = 0.0
    velocity.scalar = 0.0
    stiction.update()
    assert stiction.is_stuck is True

    limiter = SlewRateLimiter(rising_rate=2.0, falling_rate=-3.0, sample_time=0.5)
    limiter.connectInput(Source(scalar=5.0), source_port=2)
    limiter.update()
    assert limiter.getOutput() == 1.0
