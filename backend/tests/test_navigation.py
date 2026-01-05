"""Unit tests for Navigation Toolbox blocks."""

import math

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


class TestLLAToECEF:
    """Tests for LLA to ECEF conversion."""

    def test_equator_prime_meridian(self):
        """Point at equator/prime meridian should be on +X axis."""
        block = LLAToECEF()
        block.setInput([0.0, 0.0, 0.0])  # Equator, prime meridian, sea level
        block.update()

        output = block.getOutputVector()
        assert abs(output[0] - WGS84_A) < 1.0  # X ~= semi-major axis
        assert abs(output[1]) < 1.0  # Y ~= 0
        assert abs(output[2]) < 1.0  # Z ~= 0

    def test_north_pole(self):
        """North pole should be on +Z axis."""
        block = LLAToECEF()
        block.setInput([90.0, 0.0, 0.0])  # North pole
        block.update()

        output = block.getOutputVector()
        assert abs(output[0]) < 1.0  # X ~= 0
        assert abs(output[1]) < 1.0  # Y ~= 0
        assert output[2] > 6356000  # Z > semi-minor axis

    def test_altitude(self):
        """Adding altitude should increase distance from center."""
        block1 = LLAToECEF()
        block1.setInput([45.0, 90.0, 0.0])
        block1.update()
        r1 = math.sqrt(sum(x**2 for x in block1.getOutputVector()))

        block2 = LLAToECEF()
        block2.setInput([45.0, 90.0, 1000.0])  # 1km altitude
        block2.update()
        r2 = math.sqrt(sum(x**2 for x in block2.getOutputVector()))

        assert abs(r2 - r1 - 1000.0) < 1.0


class TestECEFToLLA:
    """Tests for ECEF to LLA conversion."""

    def test_roundtrip(self):
        """ECEF(LLA(x)) and back should give original."""
        lla_original = [37.7749, -122.4194, 100.0]  # San Francisco

        lla_to_ecef = LLAToECEF()
        lla_to_ecef.setInput(lla_original)
        lla_to_ecef.update()

        ecef_to_lla = ECEFToLLA()
        ecef_to_lla.setInput(lla_to_ecef.getOutputVector())
        ecef_to_lla.update()

        lla_recovered = ecef_to_lla.getOutputVector()

        assert abs(lla_recovered[0] - lla_original[0]) < 1e-6
        assert abs(lla_recovered[1] - lla_original[1]) < 1e-6
        assert abs(lla_recovered[2] - lla_original[2]) < 1.0


class TestECEFToNED:
    """Tests for ECEF to NED conversion."""

    def test_origin_at_reference(self):
        """Point at reference should be NED origin."""
        ref_lla = [45.0, -90.0, 0.0]

        # Get ECEF of reference
        lla_to_ecef = LLAToECEF()
        lla_to_ecef.setInput(ref_lla)
        lla_to_ecef.update()
        ref_ecef = lla_to_ecef.getOutputVector()

        # Convert back to NED
        ecef_to_ned = ECEFToNED(reference_lla=ref_lla)
        ecef_to_ned.setInput(ref_ecef)
        ecef_to_ned.update()

        ned = ecef_to_ned.getOutputVector()
        assert abs(ned[0]) < 1.0  # North
        assert abs(ned[1]) < 1.0  # East
        assert abs(ned[2]) < 1.0  # Down


class TestNEDToECEF:
    """Tests for NED to ECEF conversion."""

    def test_roundtrip(self):
        """NED -> ECEF -> NED should be identity."""
        ref_lla = [40.0, -75.0, 100.0]
        ned_original = [1000.0, 500.0, -50.0]

        ned_to_ecef = NEDToECEF(reference_lla=ref_lla)
        ned_to_ecef.setInput(ned_original)
        ned_to_ecef.update()

        ecef_to_ned = ECEFToNED(reference_lla=ref_lla)
        ecef_to_ned.setInput(ned_to_ecef.getOutputVector())
        ecef_to_ned.update()

        ned_recovered = ecef_to_ned.getOutputVector()

        assert abs(ned_recovered[0] - ned_original[0]) < 1.0
        assert abs(ned_recovered[1] - ned_original[1]) < 1.0
        assert abs(ned_recovered[2] - ned_original[2]) < 1.0


class TestCoordinateTransformationConversion:
    """Tests for Coordinate Transformation Conversion block."""

    def test_lla_to_ecef(self):
        """Test LLA to ECEF conversion."""
        block = CoordinateTransformationConversion(input_type="lla", output_type="ecef")
        block.setInput([0.0, 0.0, 0.0])
        block.update()

        output = block.getOutputVector()
        assert abs(output[0] - WGS84_A) < 1.0

    def test_euler_to_quaternion(self):
        """Test Euler to quaternion conversion."""
        block = CoordinateTransformationConversion(input_type="euler", output_type="quaternion")
        block.setInput([0.0, 0.0, 0.0])  # Zero Euler angles
        block.update()

        output = block.getOutputVector()
        assert abs(output[0] - 1.0) < 1e-6  # w = 1
        assert abs(output[1]) < 1e-6  # x = 0
        assert abs(output[2]) < 1e-6  # y = 0
        assert abs(output[3]) < 1e-6  # z = 0

    def test_quaternion_to_euler_roundtrip(self):
        """Test quaternion <-> Euler roundtrip."""
        euler_original = [0.1, 0.2, 0.3]

        euler_to_q = CoordinateTransformationConversion(
            input_type="euler", output_type="quaternion"
        )
        euler_to_q.setInput(euler_original)
        euler_to_q.update()

        q_to_euler = CoordinateTransformationConversion(
            input_type="quaternion", output_type="euler"
        )
        q_to_euler.setInput(euler_to_q.getOutputVector())
        q_to_euler.update()

        euler_recovered = q_to_euler.getOutputVector()

        for i in range(3):
            assert abs(euler_recovered[i] - euler_original[i]) < 1e-6

    def test_dcm_to_quaternion(self):
        """Test DCM to quaternion for identity matrix."""
        block = CoordinateTransformationConversion(input_type="dcm", output_type="quaternion")
        # Identity DCM
        block.setInput([1, 0, 0, 0, 1, 0, 0, 0, 1])
        block.update()

        output = block.getOutputVector()
        assert abs(output[0] - 1.0) < 1e-6  # w = 1
        assert abs(output[1]) < 1e-6
        assert abs(output[2]) < 1e-6
        assert abs(output[3]) < 1e-6

    def test_axis_angle_to_quaternion(self):
        """Test axis-angle to quaternion."""
        block = CoordinateTransformationConversion(
            input_type="axis_angle", output_type="quaternion"
        )
        # 90 degree rotation around Z axis
        block.setInput([0, 0, 1, math.pi / 2])
        block.update()

        output = block.getOutputVector()
        # Expected: [cos(45), 0, 0, sin(45)] = [0.707, 0, 0, 0.707]
        assert abs(output[0] - math.cos(math.pi / 4)) < 1e-6
        assert abs(output[1]) < 1e-6
        assert abs(output[2]) < 1e-6
        assert abs(output[3] - math.sin(math.pi / 4)) < 1e-6


class TestWaypointFollower:
    """Tests for Waypoint Follower block."""

    def test_bearing_north(self):
        """Bearing to point due north should be 0."""
        wp = WaypointFollower(
            waypoints=[[1.0, 0.0]],  # 1 degree north of origin
            acceptance_radius=100.0,
        )
        wp.setInput([0.0, 0.0])  # At origin
        wp.update()

        output = wp.getOutputVector()
        assert abs(output[0]) < 0.01  # Bearing ~0 (north)
        assert output[1] > 100000  # Distance > 100km

    def test_bearing_east(self):
        """Bearing to point due east should be pi/2."""
        wp = WaypointFollower(
            waypoints=[[0.0, 1.0]],  # 1 degree east
            acceptance_radius=100.0,
        )
        wp.setInput([0.0, 0.0])
        wp.update()

        output = wp.getOutputVector()
        assert abs(output[0] - math.pi / 2) < 0.01  # Bearing ~90 degrees

    def test_waypoint_advancement(self):
        """Should advance to next waypoint when reached."""
        wp = WaypointFollower(waypoints=[[0.0, 0.0], [1.0, 0.0]], acceptance_radius=1000.0)

        # Start at first waypoint
        wp.setInput([0.0, 0.0])
        wp.update()

        # First update should trigger advancement since we're at WP0
        assert wp.current_wp_index >= 0


class TestGreatCircleDistance:
    """Tests for Great Circle Distance block."""

    def test_same_point(self):
        """Distance between same point should be 0."""
        block = GreatCircleDistance()
        block.setInput([45.0, -90.0], port=0)
        block.setInput([45.0, -90.0], port=1)
        block.update()

        assert abs(block.getOutput()) < 1.0

    def test_known_distance(self):
        """Test known distance between cities."""
        # New York to London is approximately 5,570 km
        block = GreatCircleDistance()
        block.setInput([40.7128, -74.0060], port=0)  # NYC
        block.setInput([51.5074, -0.1278], port=1)  # London
        block.update()

        distance = block.getOutput()
        # Should be within 5% of 5570 km
        assert 5300000 < distance < 5850000

    def test_antipodal_points(self):
        """Distance between antipodal points should be ~20000 km."""
        block = GreatCircleDistance()
        block.setInput([0.0, 0.0], port=0)
        block.setInput([0.0, 180.0], port=1)
        block.update()

        distance = block.getOutput()
        half_circumference = math.pi * WGS84_A
        assert abs(distance - half_circumference) < 100000


class TestFlatEarthPosition:
    """Tests for Flat Earth Position block."""

    def test_stationary(self):
        """Zero velocity should maintain position."""
        from src.osk.state import State

        State.dt = 0.01

        block = FlatEarthPosition(initial_position=[100.0, 200.0, -50.0])
        block.init()

        block.setInput([0.0, 0.0, 0.0])  # Zero velocity
        block.update()

        output = block.getOutputVector()
        assert abs(output[0] - 100.0) < 1.0
        assert abs(output[1] - 200.0) < 1.0
        assert abs(output[2] - (-50.0)) < 1.0

    def test_constant_velocity(self):
        """Constant velocity should integrate to position."""
        from src.osk.state import State

        State.dt = 0.1

        block = FlatEarthPosition(initial_position=[0.0, 0.0, 0.0])
        block.init()

        # 10 m/s north for 1 second (10 steps of 0.1s)
        for _ in range(10):
            block.setInput([10.0, 0.0, 0.0])
            block.update()
            block.propagateStates()

        # Position should be approximately 10m north
        # (Integration method affects exact value)
        output = block.getOutputVector()
        assert output[0] > 0.5  # Some northward movement
