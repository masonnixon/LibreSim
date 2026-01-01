"""Sensor Fusion and Tracking Toolbox blocks for LibreSim.

These blocks implement sensor models and fusion algorithms similar to
MATLAB Sensor Fusion and Tracking Toolbox.
"""

import math
import random
from typing import Optional

from ..block import Block


# =============================================================================
# IMU Sensor Model
# =============================================================================


class IMUSensor(Block):
    """Inertial Measurement Unit (IMU) sensor model.

    Models accelerometer and gyroscope with noise and bias.

    Inputs:
        - Port 0: True acceleration [ax, ay, az] (m/s^2)
        - Port 1: True angular velocity [wx, wy, wz] (rad/s)

    Outputs:
        - Ports 0-2: Measured acceleration [ax, ay, az]
        - Ports 3-5: Measured angular velocity [wx, wy, wz]

    Parameters:
        - accel_noise: Accelerometer noise std dev (m/s^2)
        - gyro_noise: Gyroscope noise std dev (rad/s)
        - accel_bias: Accelerometer bias [bx, by, bz]
        - gyro_bias: Gyroscope bias [bx, by, bz]
        - accel_scale_error: Scale factor error (fraction)
        - gyro_scale_error: Scale factor error (fraction)
    """

    def __init__(self, accel_noise: float = 0.01, gyro_noise: float = 0.001,
                 accel_bias: Optional[list] = None, gyro_bias: Optional[list] = None,
                 accel_scale_error: float = 0.0, gyro_scale_error: float = 0.0,
                 seed: Optional[int] = None):
        super().__init__()
        self.accel_noise = accel_noise
        self.gyro_noise = gyro_noise
        self.accel_bias = accel_bias if accel_bias else [0.0, 0.0, 0.0]
        self.gyro_bias = gyro_bias if gyro_bias else [0.0, 0.0, 0.0]
        self.accel_scale_error = accel_scale_error
        self.gyro_scale_error = gyro_scale_error

        self.true_accel = [0.0, 0.0, 0.0]
        self.true_gyro = [0.0, 0.0, 0.0]
        self.output = [0.0] * 6
        self.input_blocks = [None, None]

        self._random = random.Random(seed)

    def init(self):
        self.output = [0.0] * 6

    def setInput(self, value, port=0):
        if isinstance(value, list) and len(value) >= 3:
            if port == 0:
                self.true_accel = value[:3]
            else:
                self.true_gyro = value[:3]

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block

    def update(self):
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                vec = block.getOutputVector()
                if vec is not None and len(vec) >= 3:
                    if i == 0:
                        self.true_accel = vec[:3]
                    else:
                        self.true_gyro = vec[:3]

        # Apply sensor model to accelerometer
        meas_accel = []
        for i in range(3):
            val = self.true_accel[i] * (1 + self.accel_scale_error)
            val += self.accel_bias[i]
            val += self._random.gauss(0, self.accel_noise)
            meas_accel.append(val)

        # Apply sensor model to gyroscope
        meas_gyro = []
        for i in range(3):
            val = self.true_gyro[i] * (1 + self.gyro_scale_error)
            val += self.gyro_bias[i]
            val += self._random.gauss(0, self.gyro_noise)
            meas_gyro.append(val)

        self.output = meas_accel + meas_gyro

    def getOutput(self, port=0):
        if port < len(self.output):
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


class Accelerometer(Block):
    """Accelerometer sensor model.

    Input: True acceleration [ax, ay, az] (m/s^2)
    Output: Measured acceleration with noise and bias
    """

    def __init__(self, noise: float = 0.01, bias: Optional[list] = None,
                 scale_error: float = 0.0, seed: Optional[int] = None):
        super().__init__()
        self.noise = noise
        self.bias = bias if bias else [0.0, 0.0, 0.0]
        self.scale_error = scale_error
        self.true_accel = [0.0, 0.0, 0.0]
        self.output = [0.0, 0.0, 0.0]
        self.input_block = None
        self._random = random.Random(seed)

    def init(self):
        self.output = [0.0, 0.0, 0.0]

    def setInput(self, value, port=0):
        if isinstance(value, list) and len(value) >= 3:
            self.true_accel = value[:3]

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            vec = self.input_block.getOutputVector()
            if vec is not None and len(vec) >= 3:
                self.true_accel = vec[:3]

        self.output = []
        for i in range(3):
            val = self.true_accel[i] * (1 + self.scale_error)
            val += self.bias[i]
            val += self._random.gauss(0, self.noise)
            self.output.append(val)

    def getOutput(self, port=0):
        if port < 3:
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


class Gyroscope(Block):
    """Gyroscope sensor model.

    Input: True angular velocity [wx, wy, wz] (rad/s)
    Output: Measured angular velocity with noise and bias
    """

    def __init__(self, noise: float = 0.001, bias: Optional[list] = None,
                 scale_error: float = 0.0, seed: Optional[int] = None):
        super().__init__()
        self.noise = noise
        self.bias = bias if bias else [0.0, 0.0, 0.0]
        self.scale_error = scale_error
        self.true_gyro = [0.0, 0.0, 0.0]
        self.output = [0.0, 0.0, 0.0]
        self.input_block = None
        self._random = random.Random(seed)

    def init(self):
        self.output = [0.0, 0.0, 0.0]

    def setInput(self, value, port=0):
        if isinstance(value, list) and len(value) >= 3:
            self.true_gyro = value[:3]

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            vec = self.input_block.getOutputVector()
            if vec is not None and len(vec) >= 3:
                self.true_gyro = vec[:3]

        self.output = []
        for i in range(3):
            val = self.true_gyro[i] * (1 + self.scale_error)
            val += self.bias[i]
            val += self._random.gauss(0, self.noise)
            self.output.append(val)

    def getOutput(self, port=0):
        if port < 3:
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


class Magnetometer(Block):
    """Magnetometer sensor model.

    Input: True magnetic field [mx, my, mz] (Gauss or Tesla)
    Output: Measured magnetic field with noise and bias
    """

    def __init__(self, noise: float = 0.001, bias: Optional[list] = None,
                 scale_error: float = 0.0, seed: Optional[int] = None):
        super().__init__()
        self.noise = noise
        self.bias = bias if bias else [0.0, 0.0, 0.0]
        self.scale_error = scale_error
        self.true_mag = [0.0, 0.0, 0.0]
        self.output = [0.0, 0.0, 0.0]
        self.input_block = None
        self._random = random.Random(seed)

    def init(self):
        self.output = [0.0, 0.0, 0.0]

    def setInput(self, value, port=0):
        if isinstance(value, list) and len(value) >= 3:
            self.true_mag = value[:3]

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            vec = self.input_block.getOutputVector()
            if vec is not None and len(vec) >= 3:
                self.true_mag = vec[:3]

        self.output = []
        for i in range(3):
            val = self.true_mag[i] * (1 + self.scale_error)
            val += self.bias[i]
            val += self._random.gauss(0, self.noise)
            self.output.append(val)

    def getOutput(self, port=0):
        if port < 3:
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


# =============================================================================
# GPS Sensor Model
# =============================================================================


class GPSSensor(Block):
    """GPS receiver sensor model.

    Models position and velocity measurements with noise.

    Inputs:
        - Port 0: True position [lat, lon, alt] (degrees, meters)
        - Port 1: True velocity [vn, ve, vd] (m/s)

    Outputs:
        - Ports 0-2: Measured position [lat, lon, alt]
        - Ports 3-5: Measured velocity [vn, ve, vd]

    Parameters:
        - position_noise: Position noise std dev (meters)
        - velocity_noise: Velocity noise std dev (m/s)
        - update_rate: GPS update rate (Hz)
    """

    def __init__(self, position_noise: float = 5.0, velocity_noise: float = 0.1,
                 update_rate: float = 1.0, seed: Optional[int] = None):
        super().__init__()
        self.position_noise = position_noise
        self.velocity_noise = velocity_noise
        self.update_rate = update_rate
        self.update_period = 1.0 / update_rate

        self.true_position = [0.0, 0.0, 0.0]
        self.true_velocity = [0.0, 0.0, 0.0]
        self.output = [0.0] * 6
        self.last_update_time = -1.0
        self.input_blocks = [None, None]

        self._random = random.Random(seed)

        # Approximate meters per degree at equator
        self._m_per_deg_lat = 111320.0
        self._m_per_deg_lon = 111320.0

    def init(self):
        self.output = [0.0] * 6
        self.last_update_time = -1.0

    def setInput(self, value, port=0):
        if isinstance(value, list) and len(value) >= 3:
            if port == 0:
                self.true_position = value[:3]
            else:
                self.true_velocity = value[:3]

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block

    def update(self):
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                vec = block.getOutputVector()
                if vec is not None and len(vec) >= 3:
                    if i == 0:
                        self.true_position = vec[:3]
                    else:
                        self.true_velocity = vec[:3]

        from ..state import State
        t = State.t

        # Only update at GPS rate
        if t - self.last_update_time >= self.update_period:
            self.last_update_time = t

            # Position noise in degrees
            lat_noise = self._random.gauss(0, self.position_noise / self._m_per_deg_lat)
            lon_noise = self._random.gauss(0, self.position_noise / self._m_per_deg_lon)
            alt_noise = self._random.gauss(0, self.position_noise)

            # Velocity noise
            vn_noise = self._random.gauss(0, self.velocity_noise)
            ve_noise = self._random.gauss(0, self.velocity_noise)
            vd_noise = self._random.gauss(0, self.velocity_noise)

            self.output = [
                self.true_position[0] + lat_noise,
                self.true_position[1] + lon_noise,
                self.true_position[2] + alt_noise,
                self.true_velocity[0] + vn_noise,
                self.true_velocity[1] + ve_noise,
                self.true_velocity[2] + vd_noise,
            ]

    def getOutput(self, port=0):
        if port < len(self.output):
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


class Altimeter(Block):
    """Barometric altimeter sensor model.

    Input: True altitude (m)
    Output: Measured altitude with noise
    """

    def __init__(self, noise: float = 1.0, bias: float = 0.0,
                 seed: Optional[int] = None):
        super().__init__()
        self.noise = noise
        self.bias = bias
        self.true_altitude = 0.0
        self.output = 0.0
        self.input_block = None
        self._random = random.Random(seed)

    def init(self):
        self.output = 0.0

    def setInput(self, value, port=0):
        self.true_altitude = float(value)

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.true_altitude = self.input_block.getOutput()

        self.output = self.true_altitude + self.bias + self._random.gauss(0, self.noise)

    def getOutput(self, port=0):
        return self.output


# =============================================================================
# Attitude Estimation Filters
# =============================================================================


class ComplementaryFilter(Block):
    """Complementary filter for attitude estimation.

    Fuses accelerometer and gyroscope data to estimate attitude.
    Uses high-pass filter on gyro and low-pass filter on accelerometer.

    Inputs:
        - Port 0: Accelerometer [ax, ay, az]
        - Port 1: Gyroscope [wx, wy, wz] (rad/s)

    Output: Euler angles [roll, pitch, yaw] (rad)

    Parameters:
        - alpha: Filter coefficient (0-1), higher = more gyro weight
    """

    def __init__(self, alpha: float = 0.98):
        super().__init__()
        self.alpha = alpha
        self.accel = [0.0, 0.0, 0.0]
        self.gyro = [0.0, 0.0, 0.0]
        self.euler = [0.0, 0.0, 0.0]  # [roll, pitch, yaw]
        self.output = [0.0, 0.0, 0.0]
        self.input_blocks = [None, None]

    def init(self):
        self.euler = [0.0, 0.0, 0.0]
        self.output = [0.0, 0.0, 0.0]

    def setInput(self, value, port=0):
        if isinstance(value, list) and len(value) >= 3:
            if port == 0:
                self.accel = value[:3]
            else:
                self.gyro = value[:3]

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block

    def update(self):
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                vec = block.getOutputVector()
                if vec is not None and len(vec) >= 3:
                    if i == 0:
                        self.accel = vec[:3]
                    else:
                        self.gyro = vec[:3]

        from ..state import State
        dt = State.dt

        # Estimate angles from accelerometer
        ax, ay, az = self.accel
        accel_roll = math.atan2(ay, math.sqrt(ax * ax + az * az))
        accel_pitch = math.atan2(-ax, math.sqrt(ay * ay + az * az))

        # Integrate gyroscope
        p, q, r = self.gyro
        roll_rate = p + math.sin(self.euler[0]) * math.tan(self.euler[1]) * q + \
                    math.cos(self.euler[0]) * math.tan(self.euler[1]) * r
        pitch_rate = math.cos(self.euler[0]) * q - math.sin(self.euler[0]) * r

        if abs(math.cos(self.euler[1])) > 1e-6:
            yaw_rate = math.sin(self.euler[0]) / math.cos(self.euler[1]) * q + \
                       math.cos(self.euler[0]) / math.cos(self.euler[1]) * r
        else:
            yaw_rate = 0.0

        gyro_roll = self.euler[0] + roll_rate * dt
        gyro_pitch = self.euler[1] + pitch_rate * dt
        gyro_yaw = self.euler[2] + yaw_rate * dt

        # Complementary filter
        self.euler[0] = self.alpha * gyro_roll + (1 - self.alpha) * accel_roll
        self.euler[1] = self.alpha * gyro_pitch + (1 - self.alpha) * accel_pitch
        self.euler[2] = gyro_yaw  # Yaw only from gyro (no magnetometer)

        self.output = list(self.euler)

    def getOutput(self, port=0):
        if port < 3:
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


class MadgwickFilter(Block):
    """Madgwick AHRS (Attitude and Heading Reference System) filter.

    Gradient descent based sensor fusion for attitude estimation.

    Inputs:
        - Port 0: Accelerometer [ax, ay, az]
        - Port 1: Gyroscope [wx, wy, wz] (rad/s)
        - Port 2: Magnetometer [mx, my, mz] (optional)

    Output: Quaternion [w, x, y, z]

    Parameters:
        - beta: Filter gain (typically 0.01 to 0.5)
    """

    def __init__(self, beta: float = 0.1):
        super().__init__()
        self.beta = beta
        self.accel = [0.0, 0.0, 0.0]
        self.gyro = [0.0, 0.0, 0.0]
        self.mag = [0.0, 0.0, 0.0]
        self.q = [1.0, 0.0, 0.0, 0.0]  # [w, x, y, z]
        self.output = [1.0, 0.0, 0.0, 0.0]
        self.input_blocks = [None, None, None]
        self.use_mag = False

    def init(self):
        self.q = [1.0, 0.0, 0.0, 0.0]
        self.output = [1.0, 0.0, 0.0, 0.0]

    def setInput(self, value, port=0):
        if isinstance(value, list) and len(value) >= 3:
            if port == 0:
                self.accel = value[:3]
            elif port == 1:
                self.gyro = value[:3]
            else:
                self.mag = value[:3]
                self.use_mag = True

    def connectInput(self, block, port=0, source_port=0):
        if port < 3:
            self.input_blocks[port] = block
            if port == 2:
                self.use_mag = True

    def update(self):
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                vec = block.getOutputVector()
                if vec is not None and len(vec) >= 3:
                    if i == 0:
                        self.accel = vec[:3]
                    elif i == 1:
                        self.gyro = vec[:3]
                    else:
                        self.mag = vec[:3]

        from ..state import State
        dt = State.dt

        q = self.q
        gx, gy, gz = self.gyro
        ax, ay, az = self.accel

        # Normalize accelerometer
        norm = math.sqrt(ax * ax + ay * ay + az * az)
        if norm > 1e-10:
            ax, ay, az = ax / norm, ay / norm, az / norm
        else:
            ax, ay, az = 0.0, 0.0, 0.0

        # Gradient descent corrective step (accelerometer only)
        q0, q1, q2, q3 = q

        # Auxiliary variables
        _2q0 = 2.0 * q0
        _2q1 = 2.0 * q1
        _2q2 = 2.0 * q2
        _2q3 = 2.0 * q3
        _4q0 = 4.0 * q0
        _4q1 = 4.0 * q1
        _4q2 = 4.0 * q2
        _8q1 = 8.0 * q1
        _8q2 = 8.0 * q2
        q0q0 = q0 * q0
        q1q1 = q1 * q1
        q2q2 = q2 * q2
        q3q3 = q3 * q3

        # Gradient (objective function derivative)
        s0 = _4q0 * q2q2 + _2q2 * ax + _4q0 * q1q1 - _2q1 * ay
        s1 = _4q1 * q3q3 - _2q3 * ax + 4.0 * q0q0 * q1 - _2q0 * ay - _4q1 + _8q1 * q1q1 + _8q1 * q2q2 + _4q1 * az
        s2 = 4.0 * q0q0 * q2 + _2q0 * ax + _4q2 * q3q3 - _2q3 * ay - _4q2 + _8q2 * q1q1 + _8q2 * q2q2 + _4q2 * az
        s3 = 4.0 * q1q1 * q3 - _2q1 * ax + 4.0 * q2q2 * q3 - _2q2 * ay

        # Normalize gradient
        norm = math.sqrt(s0 * s0 + s1 * s1 + s2 * s2 + s3 * s3)
        if norm > 1e-10:
            s0, s1, s2, s3 = s0 / norm, s1 / norm, s2 / norm, s3 / norm

        # Rate of change of quaternion from gyroscope
        qDot0 = 0.5 * (-q1 * gx - q2 * gy - q3 * gz)
        qDot1 = 0.5 * (q0 * gx + q2 * gz - q3 * gy)
        qDot2 = 0.5 * (q0 * gy - q1 * gz + q3 * gx)
        qDot3 = 0.5 * (q0 * gz + q1 * gy - q2 * gx)

        # Apply feedback
        qDot0 -= self.beta * s0
        qDot1 -= self.beta * s1
        qDot2 -= self.beta * s2
        qDot3 -= self.beta * s3

        # Integrate
        q0 += qDot0 * dt
        q1 += qDot1 * dt
        q2 += qDot2 * dt
        q3 += qDot3 * dt

        # Normalize quaternion
        norm = math.sqrt(q0 * q0 + q1 * q1 + q2 * q2 + q3 * q3)
        if norm > 1e-10:
            self.q = [q0 / norm, q1 / norm, q2 / norm, q3 / norm]

        self.output = list(self.q)

    def getOutput(self, port=0):
        if port < 4:
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


class MahonyFilter(Block):
    """Mahony AHRS filter.

    Proportional-Integral filter for attitude estimation.

    Inputs:
        - Port 0: Accelerometer [ax, ay, az]
        - Port 1: Gyroscope [wx, wy, wz] (rad/s)

    Output: Quaternion [w, x, y, z]

    Parameters:
        - Kp: Proportional gain
        - Ki: Integral gain
    """

    def __init__(self, Kp: float = 1.0, Ki: float = 0.0):
        super().__init__()
        self.Kp = Kp
        self.Ki = Ki
        self.accel = [0.0, 0.0, 0.0]
        self.gyro = [0.0, 0.0, 0.0]
        self.q = [1.0, 0.0, 0.0, 0.0]
        self.integral_error = [0.0, 0.0, 0.0]
        self.output = [1.0, 0.0, 0.0, 0.0]
        self.input_blocks = [None, None]

    def init(self):
        self.q = [1.0, 0.0, 0.0, 0.0]
        self.integral_error = [0.0, 0.0, 0.0]
        self.output = [1.0, 0.0, 0.0, 0.0]

    def setInput(self, value, port=0):
        if isinstance(value, list) and len(value) >= 3:
            if port == 0:
                self.accel = value[:3]
            else:
                self.gyro = value[:3]

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block

    def update(self):
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                vec = block.getOutputVector()
                if vec is not None and len(vec) >= 3:
                    if i == 0:
                        self.accel = vec[:3]
                    else:
                        self.gyro = vec[:3]

        from ..state import State
        dt = State.dt

        q0, q1, q2, q3 = self.q
        gx, gy, gz = self.gyro
        ax, ay, az = self.accel

        # Normalize accelerometer
        norm = math.sqrt(ax * ax + ay * ay + az * az)
        if norm > 1e-10:
            ax, ay, az = ax / norm, ay / norm, az / norm
        else:
            # Skip correction if no valid accelerometer data
            ax, ay, az = 0.0, 0.0, 0.0

        # Estimated gravity direction
        vx = 2.0 * (q1 * q3 - q0 * q2)
        vy = 2.0 * (q0 * q1 + q2 * q3)
        vz = q0 * q0 - q1 * q1 - q2 * q2 + q3 * q3

        # Error is cross product between estimated and measured
        ex = ay * vz - az * vy
        ey = az * vx - ax * vz
        ez = ax * vy - ay * vx

        # Apply integral feedback
        if self.Ki > 0:
            self.integral_error[0] += ex * dt
            self.integral_error[1] += ey * dt
            self.integral_error[2] += ez * dt
            gx += self.Ki * self.integral_error[0]
            gy += self.Ki * self.integral_error[1]
            gz += self.Ki * self.integral_error[2]

        # Apply proportional feedback
        gx += self.Kp * ex
        gy += self.Kp * ey
        gz += self.Kp * ez

        # Integrate quaternion rate
        qDot0 = 0.5 * (-q1 * gx - q2 * gy - q3 * gz)
        qDot1 = 0.5 * (q0 * gx + q2 * gz - q3 * gy)
        qDot2 = 0.5 * (q0 * gy - q1 * gz + q3 * gx)
        qDot3 = 0.5 * (q0 * gz + q1 * gy - q2 * gx)

        q0 += qDot0 * dt
        q1 += qDot1 * dt
        q2 += qDot2 * dt
        q3 += qDot3 * dt

        # Normalize
        norm = math.sqrt(q0 * q0 + q1 * q1 + q2 * q2 + q3 * q3)
        if norm > 1e-10:
            self.q = [q0 / norm, q1 / norm, q2 / norm, q3 / norm]

        self.output = list(self.q)

    def getOutput(self, port=0):
        if port < 4:
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


# =============================================================================
# INS/GPS Fusion
# =============================================================================


class INSGPSFusion(Block):
    """Loosely coupled INS/GPS fusion using Extended Kalman Filter.

    Fuses IMU data with GPS measurements for navigation.

    Inputs:
        - Port 0: IMU data [ax, ay, az, wx, wy, wz]
        - Port 1: GPS position [lat, lon, alt]
        - Port 2: GPS velocity [vn, ve, vd]

    Outputs:
        - Position [lat, lon, alt]
        - Velocity [vn, ve, vd]
        - Attitude (Euler) [roll, pitch, yaw]

    This is a simplified implementation.
    """

    def __init__(self, initial_position: Optional[list] = None,
                 initial_velocity: Optional[list] = None,
                 initial_attitude: Optional[list] = None):
        super().__init__()
        self.position = initial_position if initial_position else [0.0, 0.0, 0.0]
        self.velocity = initial_velocity if initial_velocity else [0.0, 0.0, 0.0]
        self.attitude = initial_attitude if initial_attitude else [0.0, 0.0, 0.0]

        self.imu_data = [0.0] * 6
        self.gps_position = [0.0, 0.0, 0.0]
        self.gps_velocity = [0.0, 0.0, 0.0]
        self.gps_valid = False

        self.output = self.position + self.velocity + self.attitude
        self.input_blocks = [None, None, None]

        # Process and measurement noise
        self.Q_position = 0.01
        self.Q_velocity = 0.1
        self.R_gps_position = 5.0
        self.R_gps_velocity = 0.1

        # Simple EKF state covariance
        self.P = [10.0] * 9  # Diagonal elements only

    def init(self):
        self.output = self.position + self.velocity + self.attitude

    def setInput(self, value, port=0):
        if isinstance(value, list):
            if port == 0 and len(value) >= 6:
                self.imu_data = value[:6]
            elif port == 1 and len(value) >= 3:
                self.gps_position = value[:3]
                self.gps_valid = True
            elif port == 2 and len(value) >= 3:
                self.gps_velocity = value[:3]

    def connectInput(self, block, port=0, source_port=0):
        if port < 3:
            self.input_blocks[port] = block

    def update(self):
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                vec = block.getOutputVector()
                if vec is not None:
                    if i == 0 and len(vec) >= 6:
                        self.imu_data = vec[:6]
                    elif i == 1 and len(vec) >= 3:
                        self.gps_position = vec[:3]
                        self.gps_valid = True
                    elif i == 2 and len(vec) >= 3:
                        self.gps_velocity = vec[:3]

        from ..state import State
        dt = State.dt

        ax, ay, az, wx, wy, wz = self.imu_data
        roll, pitch, yaw = self.attitude

        # Simple attitude integration
        roll += wx * dt
        pitch += wy * dt
        yaw += wz * dt

        # Rotate acceleration to NED frame (simplified)
        cr, sr = math.cos(roll), math.sin(roll)
        cp, sp = math.cos(pitch), math.sin(pitch)
        cy, sy = math.cos(yaw), math.sin(yaw)

        # Simplified rotation (not full DCM)
        an = ax * cp * cy + ay * (sr * sp * cy - cr * sy) + az * (cr * sp * cy + sr * sy)
        ae = ax * cp * sy + ay * (sr * sp * sy + cr * cy) + az * (cr * sp * sy - sr * cy)
        ad = -ax * sp + ay * sr * cp + az * cr * cp

        # Subtract gravity
        ad += 9.80665

        # Velocity integration
        self.velocity[0] += an * dt
        self.velocity[1] += ae * dt
        self.velocity[2] += ad * dt

        # Position integration (simplified, degrees)
        m_per_deg = 111320.0
        self.position[0] += self.velocity[0] * dt / m_per_deg
        self.position[1] += self.velocity[1] * dt / (m_per_deg * max(0.1, math.cos(math.radians(self.position[0]))))
        self.position[2] -= self.velocity[2] * dt

        # GPS correction (simple Kalman-like update)
        if self.gps_valid:
            alpha_pos = 0.1
            alpha_vel = 0.2

            self.position[0] += alpha_pos * (self.gps_position[0] - self.position[0])
            self.position[1] += alpha_pos * (self.gps_position[1] - self.position[1])
            self.position[2] += alpha_pos * (self.gps_position[2] - self.position[2])

            self.velocity[0] += alpha_vel * (self.gps_velocity[0] - self.velocity[0])
            self.velocity[1] += alpha_vel * (self.gps_velocity[1] - self.velocity[1])
            self.velocity[2] += alpha_vel * (self.gps_velocity[2] - self.velocity[2])

            self.gps_valid = False

        self.attitude = [roll, pitch, yaw]
        self.output = self.position + self.velocity + self.attitude

    def getOutput(self, port=0):
        if port < len(self.output):
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


# =============================================================================
# Tracking Filters
# =============================================================================


class AlphaBetaFilter(Block):
    """Alpha-Beta tracking filter.

    Simple tracking filter for position and velocity estimation.

    Input: Measured position
    Outputs: [estimated_position, estimated_velocity]

    Parameters:
        - alpha: Position gain
        - beta: Velocity gain
    """

    def __init__(self, alpha: float = 0.5, beta: float = 0.1, sample_time: float = 0.1):
        super().__init__()
        self.alpha = alpha
        self.beta = beta
        self.sample_time = sample_time
        self.position = 0.0
        self.velocity = 0.0
        self.output = [0.0, 0.0]
        self.input_block = None

    def init(self):
        self.position = 0.0
        self.velocity = 0.0
        self.output = [0.0, 0.0]

    def setInput(self, value, port=0):
        pass  # Will be processed in update

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            measurement = self.input_block.getOutput()
        else:
            measurement = 0.0

        # Predict
        predicted_position = self.position + self.velocity * self.sample_time

        # Update
        residual = measurement - predicted_position
        self.position = predicted_position + self.alpha * residual
        self.velocity = self.velocity + (self.beta / self.sample_time) * residual

        self.output = [self.position, self.velocity]

    def getOutput(self, port=0):
        if port < 2:
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


class AlphaBetaGammaFilter(Block):
    """Alpha-Beta-Gamma tracking filter.

    Extended tracking filter including acceleration estimation.

    Input: Measured position
    Outputs: [position, velocity, acceleration]

    Parameters:
        - alpha: Position gain
        - beta: Velocity gain
        - gamma: Acceleration gain
    """

    def __init__(self, alpha: float = 0.5, beta: float = 0.3, gamma: float = 0.1,
                 sample_time: float = 0.1):
        super().__init__()
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.sample_time = sample_time
        self.position = 0.0
        self.velocity = 0.0
        self.acceleration = 0.0
        self.output = [0.0, 0.0, 0.0]
        self.input_block = None

    def init(self):
        self.position = 0.0
        self.velocity = 0.0
        self.acceleration = 0.0
        self.output = [0.0, 0.0, 0.0]

    def setInput(self, value, port=0):
        pass

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            measurement = self.input_block.getOutput()
        else:
            measurement = 0.0

        dt = self.sample_time
        dt2 = dt * dt

        # Predict
        predicted_position = self.position + self.velocity * dt + 0.5 * self.acceleration * dt2
        predicted_velocity = self.velocity + self.acceleration * dt

        # Update
        residual = measurement - predicted_position
        self.position = predicted_position + self.alpha * residual
        self.velocity = predicted_velocity + (self.beta / dt) * residual
        self.acceleration = self.acceleration + (2.0 * self.gamma / dt2) * residual

        self.output = [self.position, self.velocity, self.acceleration]

    def getOutput(self, port=0):
        if port < 3:
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output
