"""Unit tests for Sensor Fusion Toolbox blocks."""

import math
import pytest

from src.osk.blocks.sensor_fusion import (
    IMUSensor, Accelerometer, Gyroscope, Magnetometer,
    GPSSensor, Altimeter, ComplementaryFilter, MadgwickFilter,
    MahonyFilter, INSGPSFusion, AlphaBetaFilter, AlphaBetaGammaFilter
)


class TestIMUSensor:
    """Tests for IMU Sensor block."""

    def test_zero_noise(self):
        """IMU with zero noise should output true values."""
        imu = IMUSensor(
            accel_noise=0.0,
            gyro_noise=0.0,
            accel_bias=[0.0, 0.0, 0.0],
            gyro_bias=[0.0, 0.0, 0.0]
        )

        true_accel = [1.0, 2.0, 3.0]
        true_gyro = [0.1, 0.2, 0.3]

        imu.setInput(true_accel, port=0)
        imu.setInput(true_gyro, port=1)
        imu.update()

        output = imu.getOutputVector()
        for i in range(3):
            assert abs(output[i] - true_accel[i]) < 1e-6
            assert abs(output[i+3] - true_gyro[i]) < 1e-6

    def test_bias_applied(self):
        """IMU should add bias to measurements."""
        bias = [0.1, 0.2, 0.3]
        imu = IMUSensor(
            accel_noise=0.0,
            gyro_noise=0.0,
            accel_bias=bias,
            gyro_bias=[0.0, 0.0, 0.0]
        )

        imu.setInput([0.0, 0.0, 0.0], port=0)
        imu.setInput([0.0, 0.0, 0.0], port=1)
        imu.update()

        output = imu.getOutputVector()
        for i in range(3):
            assert abs(output[i] - bias[i]) < 1e-6

    def test_noise_statistics(self):
        """IMU noise should have correct statistics."""
        imu = IMUSensor(
            accel_noise=1.0,
            gyro_noise=0.0,
            accel_bias=[0.0, 0.0, 0.0],
            gyro_bias=[0.0, 0.0, 0.0],
            seed=42
        )

        samples = []
        for _ in range(1000):
            imu.setInput([0.0, 0.0, 0.0], port=0)
            imu.setInput([0.0, 0.0, 0.0], port=1)
            imu.update()
            samples.append(imu.getOutput(0))

        mean = sum(samples) / len(samples)
        variance = sum((x - mean)**2 for x in samples) / len(samples)

        assert abs(mean) < 0.1  # Mean should be near 0
        assert 0.5 < variance < 1.5  # Variance should be near 1


class TestAccelerometer:
    """Tests for Accelerometer block."""

    def test_basic_measurement(self):
        """Accelerometer should output input with noise."""
        accel = Accelerometer(noise=0.0, bias=[0.0, 0.0, 0.0])

        accel.setInput([9.8, 0.0, 0.0])
        accel.update()

        output = accel.getOutputVector()
        assert abs(output[0] - 9.8) < 1e-6
        assert abs(output[1]) < 1e-6
        assert abs(output[2]) < 1e-6


class TestGyroscope:
    """Tests for Gyroscope block."""

    def test_basic_measurement(self):
        """Gyroscope should output input with noise."""
        gyro = Gyroscope(noise=0.0, bias=[0.0, 0.0, 0.0])

        gyro.setInput([0.1, 0.2, 0.3])
        gyro.update()

        output = gyro.getOutputVector()
        assert abs(output[0] - 0.1) < 1e-6
        assert abs(output[1] - 0.2) < 1e-6
        assert abs(output[2] - 0.3) < 1e-6


class TestMagnetometer:
    """Tests for Magnetometer block."""

    def test_basic_measurement(self):
        """Magnetometer should output input with noise."""
        mag = Magnetometer(noise=0.0, bias=[0.0, 0.0, 0.0])

        mag.setInput([0.5, 0.0, 0.3])
        mag.update()

        output = mag.getOutputVector()
        assert abs(output[0] - 0.5) < 1e-6
        assert abs(output[1]) < 1e-6
        assert abs(output[2] - 0.3) < 1e-6


class TestGPSSensor:
    """Tests for GPS Sensor block."""

    def test_zero_noise(self):
        """GPS with zero noise should output true values."""
        from src.osk.state import State
        State.t = 0.0

        gps = GPSSensor(
            position_noise=0.0,
            velocity_noise=0.0,
            update_rate=10.0,
            seed=42
        )
        gps.init()

        true_pos = [37.0, -122.0, 100.0]
        true_vel = [10.0, 5.0, -1.0]

        gps.setInput(true_pos, port=0)
        gps.setInput(true_vel, port=1)
        gps.update()

        output = gps.getOutputVector()
        for i in range(3):
            assert abs(output[i] - true_pos[i]) < 1e-6
            assert abs(output[i+3] - true_vel[i]) < 1e-6


class TestAltimeter:
    """Tests for Altimeter block."""

    def test_zero_noise(self):
        """Altimeter with zero noise should output true altitude."""
        alt = Altimeter(noise=0.0, bias=0.0)

        alt.setInput(1000.0)
        alt.update()

        assert abs(alt.getOutput() - 1000.0) < 1e-6

    def test_bias(self):
        """Altimeter should add bias to measurement."""
        alt = Altimeter(noise=0.0, bias=50.0)

        alt.setInput(1000.0)
        alt.update()

        assert abs(alt.getOutput() - 1050.0) < 1e-6


class TestComplementaryFilter:
    """Tests for Complementary Filter block."""

    def test_level_attitude(self):
        """Filter should estimate level attitude when level."""
        from src.osk.state import State
        State.dt = 0.01

        cf = ComplementaryFilter(alpha=0.98)
        cf.init()

        # Level accelerometer (gravity in -Z)
        accel = [0.0, 0.0, 9.8]
        gyro = [0.0, 0.0, 0.0]

        for _ in range(100):
            cf.setInput(accel, port=0)
            cf.setInput(gyro, port=1)
            cf.update()

        output = cf.getOutputVector()
        # Roll and pitch should be near zero
        assert abs(output[0]) < 0.1
        assert abs(output[1]) < 0.1

    def test_gyro_integration(self):
        """Filter should integrate gyro for yaw."""
        from src.osk.state import State
        State.dt = 0.01

        cf = ComplementaryFilter(alpha=0.98)
        cf.init()

        # Level attitude, yaw rate of 1 rad/s
        accel = [0.0, 0.0, 9.8]
        gyro = [0.0, 0.0, 1.0]

        for _ in range(100):  # 1 second
            cf.setInput(accel, port=0)
            cf.setInput(gyro, port=1)
            cf.update()

        output = cf.getOutputVector()
        # Yaw should be approximately 1 radian
        assert abs(output[2] - 1.0) < 0.1


class TestMadgwickFilter:
    """Tests for Madgwick Filter block."""

    def test_initial_quaternion(self):
        """Initial quaternion should be identity."""
        mf = MadgwickFilter(beta=0.1)
        mf.init()

        output = mf.getOutputVector()
        assert abs(output[0] - 1.0) < 1e-6
        assert abs(output[1]) < 1e-6
        assert abs(output[2]) < 1e-6
        assert abs(output[3]) < 1e-6

    def test_quaternion_normalization(self):
        """Output quaternion should always be normalized."""
        from src.osk.state import State
        State.dt = 0.01

        mf = MadgwickFilter(beta=0.1)
        mf.init()

        # Random inputs
        accel = [0.5, 0.3, 9.5]
        gyro = [0.1, 0.2, 0.3]

        for _ in range(100):
            mf.setInput(accel, port=0)
            mf.setInput(gyro, port=1)
            mf.update()

        output = mf.getOutputVector()
        norm = math.sqrt(sum(x**2 for x in output))
        assert abs(norm - 1.0) < 1e-6


class TestMahonyFilter:
    """Tests for Mahony Filter block."""

    def test_initial_quaternion(self):
        """Initial quaternion should be identity."""
        mh = MahonyFilter(Kp=1.0, Ki=0.0)
        mh.init()

        output = mh.getOutputVector()
        assert abs(output[0] - 1.0) < 1e-6

    def test_level_convergence(self):
        """Filter should converge to level attitude."""
        from src.osk.state import State
        State.dt = 0.01

        mh = MahonyFilter(Kp=2.0, Ki=0.0)
        mh.init()

        # Level accelerometer
        accel = [0.0, 0.0, 9.8]
        gyro = [0.0, 0.0, 0.0]

        for _ in range(200):
            mh.setInput(accel, port=0)
            mh.setInput(gyro, port=1)
            mh.update()

        output = mh.getOutputVector()
        # Should be near identity quaternion
        assert output[0] > 0.99


class TestINSGPSFusion:
    """Tests for INS/GPS Fusion block."""

    def test_initialization(self):
        """Fusion should initialize with given values."""
        fusion = INSGPSFusion(
            initial_position=[37.0, -122.0, 100.0],
            initial_velocity=[0.0, 0.0, 0.0],
            initial_attitude=[0.0, 0.0, 0.0]
        )
        fusion.init()

        output = fusion.getOutputVector()
        assert abs(output[0] - 37.0) < 0.01
        assert abs(output[1] - (-122.0)) < 0.01
        assert abs(output[2] - 100.0) < 1.0

    def test_gps_correction(self):
        """GPS measurements should correct drift."""
        from src.osk.state import State
        State.dt = 0.1

        fusion = INSGPSFusion(
            initial_position=[0.0, 0.0, 0.0],
            initial_velocity=[0.0, 0.0, 0.0],
            initial_attitude=[0.0, 0.0, 0.0]
        )
        fusion.init()

        # Provide GPS update
        imu_data = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]  # Zero IMU
        gps_pos = [1.0, 2.0, 100.0]
        gps_vel = [10.0, 5.0, 0.0]

        for _ in range(10):
            fusion.setInput(imu_data, port=0)
            fusion.setInput(gps_pos, port=1)
            fusion.setInput(gps_vel, port=2)
            fusion.update()

        output = fusion.getOutputVector()
        # Position should move toward GPS
        assert abs(output[0]) > 0.01  # Some movement toward GPS lat


class TestAlphaBetaFilter:
    """Tests for Alpha-Beta Filter block."""

    def test_constant_position(self):
        """Filter should track constant position."""
        abf = AlphaBetaFilter(alpha=0.5, beta=0.1, sample_time=0.1)
        abf.init()

        class ConstantBlock:
            def getOutput(self):
                return 10.0

        abf.input_block = ConstantBlock()

        for _ in range(20):
            abf.update()

        output = abf.getOutputVector()
        assert abs(output[0] - 10.0) < 0.5  # Position estimate
        assert abs(output[1]) < 0.5          # Velocity should be ~0

    def test_constant_velocity(self):
        """Filter should track constant velocity motion."""
        abf = AlphaBetaFilter(alpha=0.8, beta=0.5, sample_time=0.1)
        abf.init()

        position = 0.0

        class MovingBlock:
            def __init__(self):
                self.pos = 0.0

            def getOutput(self):
                self.pos += 1.0  # Velocity of 10 per second
                return self.pos

        abf.input_block = MovingBlock()

        for _ in range(50):
            abf.update()

        output = abf.getOutputVector()
        # Velocity estimate should be positive
        assert output[1] > 0


class TestAlphaBetaGammaFilter:
    """Tests for Alpha-Beta-Gamma Filter block."""

    def test_constant_acceleration(self):
        """Filter should estimate acceleration."""
        abgf = AlphaBetaGammaFilter(
            alpha=0.9,
            beta=0.5,
            gamma=0.1,
            sample_time=0.1
        )
        abgf.init()

        t = 0.0
        accel = 1.0  # 1 m/s^2

        class AcceleratingBlock:
            def __init__(self):
                self.t = 0.0

            def getOutput(self):
                pos = 0.5 * 1.0 * self.t**2  # s = 0.5*a*t^2
                self.t += 0.1
                return pos

        abgf.input_block = AcceleratingBlock()

        for _ in range(100):
            abgf.update()

        output = abgf.getOutputVector()
        # Acceleration estimate should be positive
        assert output[2] > 0
