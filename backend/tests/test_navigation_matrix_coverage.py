"""Behavioral coverage for matrix and navigation block protocol branches."""

import math

import pytest

from src.osk.blocks.matrix_ops import (
    Assignment,
    Concatenate,
    MatrixInverse,
    MatrixMultiply,
    MatrixSum,
    MatrixTranspose,
    Selector,
    VectorNorm,
)
from src.osk.blocks.navigation import (
    WGS84_A,
    CoordinateTransformationConversion,
    ECEFToLLA,
    ECEFToNED,
    FlatEarthPosition,
    GreatCircleDistance,
    LLAToECEF,
    NEDToECEF,
    WaypointFollower,
)


class Source:
    def __init__(self, vector=None, scalar=0.0):
        self.vector = vector
        self.scalar = scalar

    def getOutputVector(self):
        return self.vector

    def getOutput(self, port=0):
        return self.scalar


def test_matrix_multiply_protocols_and_shapes():
    block = MatrixMultiply()
    block.init()
    assert block.getOutput() == 0.0
    block.setInput(123.0, 2)
    block.connectInput(Source([1.0, 2.0]), 0)
    block.connectInput(Source([3.0, 4.0]), 1)
    block.connectInput(Source([99.0]), 2)  # Invalid ports are ignored.
    block.update()
    assert block.getOutput() == pytest.approx(11.0)
    assert block.getOutput(2) == 0.0
    assert block.getOutputVector() is None

    block.connectInput(Source(None, 6.0), 0)
    block.connectInput(Source(None, 7.0), 1)
    block.update()
    assert block.getOutput() == pytest.approx(42.0)

    block.setInput([2.0, 3.0], 0)
    block.setInput([4.0], 1)
    block.input_blocks = [None, None]
    block.update()
    assert block.getOutput() == pytest.approx(8.0)

    block.setInput([], 0)
    block.setInput([], 1)
    block.update()
    assert block.getOutput() == 0.0


def test_matrix_transpose_and_inverse_protocols():
    transpose = MatrixTranspose()
    transpose.init()
    transpose.setInput(7.0)
    transpose.update()
    assert transpose.output == [7.0]
    transpose.connectInput(Source([1.0, 2.0]))
    transpose.update()
    assert transpose.getOutputVector() == [1.0, 2.0]
    assert transpose.getOutput(3) == 0.0
    transpose.connectInput(Source(None, 5.0))
    transpose.update()
    assert transpose.getOutput() == 5.0
    assert transpose.getOutputVector() is None

    inverse = MatrixInverse()
    inverse.init()
    inverse.connectInput(Source([4.0, 7.0, 2.0, 6.0]))
    inverse.update()
    assert inverse.getOutputVector() == pytest.approx([0.6, -0.7, -0.2, 0.4])
    assert inverse.getOutput(8) == 0.0
    inverse.setInput([1.0, 2.0, 2.0, 4.0])
    inverse.input_block = None
    inverse.update()
    assert all(math.isinf(value) for value in inverse.output)
    inverse.connectInput(Source(None, 0.0))
    inverse.update()
    assert math.isinf(inverse.getOutput())
    assert inverse.getOutputVector() is None
    inverse.setInput([1.0, 2.0, 3.0])
    inverse.input_block = None
    inverse.update()
    assert inverse.output == [1.0, 2.0, 3.0]


def test_selector_assignment_and_concatenate_protocols():
    selector = Selector(indices=[1, -1, 4], output_size=3)
    selector.init()
    selector.connectInput(Source([10.0, 20.0]))
    selector.update()
    assert selector.getOutputVector() == [20.0, 0.0, 0.0]
    assert selector.getOutput(4) == 0.0
    selector.connectInput(Source(None, 3.0))
    selector.update()
    assert selector.output == [0.0, 0.0, 0.0]

    assignment = Assignment(indices=[0, 2, 9])
    assignment.init()
    assignment.connectInput(Source([1.0, 2.0, 3.0]), 0)
    assignment.connectInput(Source([8.0, 7.0]), 1)
    assignment.connectInput(Source([99.0]), 2)
    assignment.update()
    assert assignment.getOutputVector() == [8.0, 2.0, 7.0]
    assert assignment.getOutput() == 8.0
    assert assignment.getOutput(9) == 0.0
    assignment.connectInput(Source(None, 4.0), 0)
    assignment.connectInput(Source(None, 5.0), 1)
    assignment.setInput(99.0, 2)
    assignment.update()
    assert assignment.output == [5.0]
    assert assignment.getOutputVector() is None

    concatenate = Concatenate(num_inputs=2)
    concatenate.init()
    assert concatenate.getNumOutputs() == 1
    concatenate.connectInput(Source([1.0, 2.0]), 0)
    concatenate.connectInput(Source(None, 3.0), 1)
    concatenate.connectInput(Source([99.0]), 2)
    concatenate.update()
    assert concatenate.getOutputVector() == [1.0, 2.0, 3.0]
    assert concatenate.getOutput() == 1.0
    assert concatenate.getNumOutputs() == 3
    assert concatenate.getOutput(4) == 0.0
    concatenate.setInput([99.0], 2)


def test_matrix_sum_and_all_vector_norm_modes():
    matrix_sum = MatrixSum()
    matrix_sum.connectInput(Source([1.0, 2.0, 3.0]))
    matrix_sum.update()
    assert matrix_sum.getOutput() == 6.0
    matrix_sum.connectInput(Source(None, 9.0))
    matrix_sum.update()
    assert matrix_sum.getOutput() == 9.0

    expected = {"1": 7.0, "2": 5.0, "inf": 4.0, "other": 5.0}
    for mode, result in expected.items():
        norm = VectorNorm(mode)
        norm.connectInput(Source([3.0, -4.0]))
        norm.update()
        assert norm.getOutput() == pytest.approx(result)

    empty = VectorNorm("inf")
    empty.setInput([])
    empty.update()
    assert empty.getOutput() == 0.0
    empty.connectInput(Source(None, -6.0))
    empty.update()
    assert empty.getOutput() == 6.0


@pytest.mark.parametrize(
    ("dcm", "expected"),
    [
        ([1, 0, 0, 0, -1, 0, 0, 0, -1], [0, 1, 0, 0]),
        ([-1, 0, 0, 0, 1, 0, 0, 0, -1], [0, 0, 1, 0]),
        ([-1, 0, 0, 0, -1, 0, 0, 0, 1], [0, 0, 0, 1]),
    ],
)
def test_dcm_to_quaternion_negative_trace_branches(dcm, expected):
    block = CoordinateTransformationConversion("dcm", "quaternion")
    block.setInput(dcm)
    block.update()
    assert block.getOutputVector() == pytest.approx(expected)


def test_coordinate_conversion_guard_clamp_iteration_and_fallbacks():
    block = CoordinateTransformationConversion("lla", "ecef")
    block.update()
    assert block.getOutputVector() == []
    block.connectInput(Source([0.0, 0.0, 0.0]))
    block.update()
    assert block.output == pytest.approx([WGS84_A, 0.0, 0.0])

    clamp = CoordinateTransformationConversion("quaternion", "euler")
    clamp.setInput([math.sqrt(0.5), 0.0, math.sqrt(0.5), 0.0])
    clamp.update()
    assert clamp.output[1] == pytest.approx(math.pi / 2)

    # A non-axis-aligned point needs at least one refinement iteration.
    roundtrip = CoordinateTransformationConversion("ecef", "lla")
    ecef = block._lla_to_ecef([37.0, -122.0, 125.0])
    roundtrip.setInput(ecef)
    roundtrip.update()
    assert roundtrip.output == pytest.approx([37.0, -122.0, 125.0], abs=1e-6)

    fallback = CoordinateTransformationConversion("lla", "ecef")
    assert fallback._ecef_to_ned([1.0, 2.0, 3.0]) == [1.0, 2.0, 3.0]
    assert fallback._ned_to_ecef([4.0, 5.0, 6.0]) == [4.0, 5.0, 6.0]
    assert fallback._quaternion_to_axis_angle([0.0, 0.0, 0.0, 0.0]) == [
        0.0,
        0.0,
        0.0,
        math.pi,
    ]

    non_finite = roundtrip._ecef_to_lla([math.nan, 0.0, 0.0])
    assert all(math.isnan(value) for value in non_finite)


def test_navigation_source_protocols_invalid_ports_and_polar_altitude():
    lla = LLAToECEF()
    lla.connectInput(Source([0.0, 0.0, 10.0]))
    lla.update()
    assert lla.getOutputVector()[0] == pytest.approx(WGS84_A + 10.0)
    assert lla.getOutput(3) == 0.0

    ecef = ECEFToLLA()
    ecef.connectInput(Source(lla.getOutputVector()))
    ecef.update()
    assert ecef.getOutputVector() == pytest.approx([0.0, 0.0, 10.0], abs=1e-6)
    assert ecef.getOutput(3) == 0.0
    ecef.setInput([0.0, 0.0, 6356752.314245])
    ecef.input_block = None
    ecef.update()
    assert ecef.output == pytest.approx([90.0, 0.0, 0.0], abs=1e-3)
    ecef.setInput([math.nan, 0.0, 0.0])
    ecef.update()
    assert len(ecef.output) == 3
    assert any(math.isnan(value) for value in ecef.output)

    ref = [40.0, -75.0, 100.0]
    to_ecef = NEDToECEF(ref)
    to_ecef.connectInput(Source([100.0, 20.0, -5.0]))
    to_ecef.update()
    assert to_ecef.getOutput() == pytest.approx(to_ecef.output[0])
    assert to_ecef.getOutput(3) == 0.0

    to_ned = ECEFToNED(ref)
    to_ned.connectInput(Source(to_ecef.output), 0)
    to_ned.connectInput(Source(ref), 1)
    to_ned.connectInput(Source([99.0]), 2)
    to_ned.update()
    assert to_ned.getOutputVector() == pytest.approx([100.0, 20.0, -5.0], abs=1e-6)
    assert to_ned.getOutput() == pytest.approx(100.0)
    assert to_ned.getOutput(3) == 0.0


def test_waypoint_distance_and_flat_earth_source_protocols():
    follower = WaypointFollower([[0.0, 0.0], [0.0, 1.0]], acceptance_radius=1.0)
    follower.connectInput(Source([0.0, 0.0]))
    follower.update()
    assert follower.current_wp_index == 1
    assert follower.output[0] == pytest.approx(math.pi / 2)
    assert follower.getOutput() == pytest.approx(math.pi / 2)
    assert follower.getOutput(3) == 0.0
    follower.current_wp_index = len(follower.waypoints)
    follower.update()
    assert follower.output == [0.0, 0.0, 2.0]
    final_waypoint = WaypointFollower([[0.0, 0.0]], acceptance_radius=1.0)
    final_waypoint.update()
    assert final_waypoint.output == [0.0, 0.0, 0.0]

    distance = GreatCircleDistance()
    distance.connectInput(Source([0.0, 0.0]), 0)
    distance.connectInput(Source([0.0, 1.0]), 1)
    distance.connectInput(Source([99.0]), 2)
    distance.update()
    assert distance.getOutput() == pytest.approx(math.radians(1) * WGS84_A)

    position = FlatEarthPosition([1.0, 2.0, 3.0])
    position.init()
    position.connectInput(Source([4.0, 5.0, 6.0]))
    position.update()
    assert [position.n[1], position.e[1], position.d[1]] == [4.0, 5.0, 6.0]
    assert position.getOutputVector() == [1.0, 2.0, 3.0]
    assert position.getOutput() == 1.0
    assert position.getOutput(3) == 0.0


def test_navigation_invalid_input_shapes_leave_existing_values_unchanged():
    conversion = CoordinateTransformationConversion("lla", "ecef")
    conversion.setInput(123.0)
    conversion.connectInput(Source(None))
    conversion.update()
    assert conversion.output == []

    lla = LLAToECEF()
    lla.setInput([1.0])
    lla.connectInput(Source([2.0]))
    lla.update()
    assert lla.input == [0.0, 0.0, 0.0]

    ecef = ECEFToLLA()
    ecef.setInput([1.0])
    ecef.connectInput(Source([2.0]))
    ecef.update()
    assert ecef.input == [0.0, 0.0, 0.0]

    to_ned = ECEFToNED()
    to_ned.setInput([1.0], 0)
    to_ned.setInput([1.0], 1)
    to_ned.setInput([1.0, 2.0, 3.0], 2)
    to_ned.connectInput(Source([1.0]), 0)
    to_ned.update()
    assert to_ned.input_ecef == [0.0, 0.0, 0.0]

    to_ecef = NEDToECEF()
    to_ecef.setInput([1.0])
    to_ecef.connectInput(Source([1.0]))
    to_ecef.update()
    assert to_ecef.input_ned == [0.0, 0.0, 0.0]

    follower = WaypointFollower([[1.0, 0.0]])
    follower.setInput([1.0])
    follower.connectInput(Source([1.0]))
    follower.update()
    assert follower.position == [0.0, 0.0]

    distance = GreatCircleDistance()
    distance.setInput([1.0])
    distance.connectInput(Source([1.0]), 0)
    distance.update()
    assert distance.getOutput() == 0.0

    position = FlatEarthPosition()
    position.setInput([1.0])
    position.connectInput(Source([1.0]))
    position.update()
    assert position.velocity == [0.0, 0.0, 0.0]
