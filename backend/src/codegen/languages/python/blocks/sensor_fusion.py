"""Python templates for sensor-fusion tracking blocks."""

from ....models import BlockInfo


def imu_sensor_template(block: BlockInfo, class_name: str) -> str:
    """Generate an OSK-compatible six-axis IMU model."""
    accel_noise = block.parameters.get("accelNoise", block.parameters.get("accel_noise", 0.01))
    gyro_noise = block.parameters.get("gyroNoise", block.parameters.get("gyro_noise", 0.001))
    accel_bias = block.parameters.get("accelBias", block.parameters.get("accel_bias", [0.0] * 3))
    gyro_bias = block.parameters.get("gyroBias", block.parameters.get("gyro_bias", [0.0] * 3))
    accel_scale = block.parameters.get(
        "accelScaleError", block.parameters.get("accel_scale_error", 0.0)
    )
    gyro_scale = block.parameters.get(
        "gyroScaleError", block.parameters.get("gyro_scale_error", 0.0)
    )
    seed = block.parameters.get("seed", None)
    return f'''
import random

class {class_name}:
    """Six-axis IMU model: {block.name}"""

    def __init__(self):
        self.input = [0.0, 0.0, 0.0]
        self.input1 = [0.0, 0.0, 0.0]
        self.output = [0.0] * 6
        self.accel_noise = {accel_noise}
        self.gyro_noise = {gyro_noise}
        self.accel_bias = {accel_bias!r}
        self.gyro_bias = {gyro_bias!r}
        self.accel_scale_error = {accel_scale}
        self.gyro_scale_error = {gyro_scale}
        self._random = random.Random({seed!r})

    def init(self):
        self.output = [0.0] * 6

    def update(self, t: float):
        measured_accel = []
        for i in range(3):
            value = self.input[i] * (1.0 + self.accel_scale_error)
            value += self.accel_bias[i]
            value += self._random.gauss(0.0, self.accel_noise)
            measured_accel.append(value)
        measured_gyro = []
        for i in range(3):
            value = self.input1[i] * (1.0 + self.gyro_scale_error)
            value += self.gyro_bias[i]
            value += self._random.gauss(0.0, self.gyro_noise)
            measured_gyro.append(value)
        self.output = measured_accel + measured_gyro

    def get_output(self, port: int = 0) -> float:
        return self.output[port] if 0 <= port < 6 else 0.0

    def get_output_vector(self) -> list:
        return list(self.output)
'''


def madgwick_filter_template(block: BlockInfo, class_name: str) -> str:
    """Generate the OSK accelerometer/gyroscope Madgwick equations."""
    beta = block.parameters.get("beta", 0.1)
    return f'''
class {class_name}:
    """Madgwick AHRS filter: {block.name}"""

    def __init__(self):
        self.beta = {beta}
        self.input = [0.0, 0.0, 0.0]
        self.input1 = [0.0, 0.0, 0.0]
        self.q = [1.0, 0.0, 0.0, 0.0]
        self.output = list(self.q)

    def init(self):
        self.q = [1.0, 0.0, 0.0, 0.0]
        self.output = list(self.q)

    def update(self, t: float, dt: float):
        ax, ay, az = self.input
        gx, gy, gz = self.input1
        norm = math.sqrt(ax * ax + ay * ay + az * az)
        if norm > 1e-10:
            ax, ay, az = ax / norm, ay / norm, az / norm
        else:
            ax, ay, az = 0.0, 0.0, 0.0

        q0, q1, q2, q3 = self.q
        _2q0, _2q1, _2q2, _2q3 = 2*q0, 2*q1, 2*q2, 2*q3
        _4q0, _4q1, _4q2 = 4*q0, 4*q1, 4*q2
        _8q1, _8q2 = 8*q1, 8*q2
        q0q0, q1q1, q2q2, q3q3 = q0*q0, q1*q1, q2*q2, q3*q3
        s0 = _4q0*q2q2 + _2q2*ax + _4q0*q1q1 - _2q1*ay
        s1 = (_4q1*q3q3 - _2q3*ax + 4*q0q0*q1 - _2q0*ay - _4q1
              + _8q1*q1q1 + _8q1*q2q2 + _4q1*az)
        s2 = (4*q0q0*q2 + _2q0*ax + _4q2*q3q3 - _2q3*ay - _4q2
              + _8q2*q1q1 + _8q2*q2q2 + _4q2*az)
        s3 = 4*q1q1*q3 - _2q1*ax + 4*q2q2*q3 - _2q2*ay
        norm = math.sqrt(s0*s0 + s1*s1 + s2*s2 + s3*s3)
        if norm > 1e-10:
            s0, s1, s2, s3 = s0/norm, s1/norm, s2/norm, s3/norm

        qdot0 = 0.5*(-q1*gx - q2*gy - q3*gz) - self.beta*s0
        qdot1 = 0.5*(q0*gx + q2*gz - q3*gy) - self.beta*s1
        qdot2 = 0.5*(q0*gy - q1*gz + q3*gx) - self.beta*s2
        qdot3 = 0.5*(q0*gz + q1*gy - q2*gx) - self.beta*s3
        q0 += qdot0 * dt
        q1 += qdot1 * dt
        q2 += qdot2 * dt
        q3 += qdot3 * dt
        norm = math.sqrt(q0*q0 + q1*q1 + q2*q2 + q3*q3)
        if norm > 1e-10:
            self.q = [q0/norm, q1/norm, q2/norm, q3/norm]
        self.output = list(self.q)

    def get_output(self, port: int = 0) -> float:
        return self.output[port] if 0 <= port < 4 else 0.0

    def get_output_vector(self) -> list:
        return list(self.output)
'''


def complementary_filter_template(block: BlockInfo, class_name: str) -> str:
    """Generate the OSK complementary attitude-filter equations."""
    alpha = block.parameters.get("alpha", 0.98)
    return f'''
class {class_name}:
    """Complementary attitude filter: {block.name}"""

    def __init__(self):
        self.alpha = {alpha}
        self.input = [0.0, 0.0, 0.0]
        self.input1 = [0.0, 0.0, 0.0]
        self.euler = [0.0, 0.0, 0.0]
        self.output = list(self.euler)

    def init(self):
        self.euler = [0.0, 0.0, 0.0]
        self.output = list(self.euler)

    def update(self, t: float, dt: float):
        ax, ay, az = self.input
        p, q, r = self.input1
        roll, pitch, yaw = self.euler
        accel_roll = math.atan2(ay, math.sqrt(ax*ax + az*az))
        accel_pitch = math.atan2(-ax, math.sqrt(ay*ay + az*az))
        roll_rate = p + math.sin(roll)*math.tan(pitch)*q + math.cos(roll)*math.tan(pitch)*r
        pitch_rate = math.cos(roll)*q - math.sin(roll)*r
        if abs(math.cos(pitch)) > 1e-6:
            yaw_rate = math.sin(roll)/math.cos(pitch)*q + math.cos(roll)/math.cos(pitch)*r
        else:
            yaw_rate = 0.0
        self.euler[0] = self.alpha*(roll + roll_rate*dt) + (1-self.alpha)*accel_roll
        self.euler[1] = self.alpha*(pitch + pitch_rate*dt) + (1-self.alpha)*accel_pitch
        self.euler[2] = yaw + yaw_rate*dt
        self.output = list(self.euler)

    def get_output(self, port: int = 0) -> float:
        return self.output[port] if 0 <= port < 3 else 0.0

    def get_output_vector(self) -> list:
        return list(self.output)
'''


def alpha_beta_filter_template(block: BlockInfo, class_name: str) -> str:
    """Generate an alpha-beta position and velocity tracking filter."""
    alpha = block.parameters.get("alpha", 0.5)
    beta = block.parameters.get("beta", 0.1)
    sample_time = block.parameters.get("sampleTime", 0.1)
    return f'''
class {class_name}:
    """Alpha-beta tracking filter: {block.name}"""

    def __init__(self):
        self.alpha = {alpha}
        self.beta = {beta}
        self.sample_time = {sample_time}
        self.input = 0.0
        self.position = 0.0
        self.velocity = 0.0
        self.output = [0.0, 0.0]

    def init(self):
        self.position = 0.0
        self.velocity = 0.0
        self.output = [0.0, 0.0]

    def update(self, t: float):
        predicted_position = self.position + self.velocity * self.sample_time
        residual = self.input - predicted_position
        self.position = predicted_position + self.alpha * residual
        self.velocity += (self.beta / self.sample_time) * residual
        self.output = [self.position, self.velocity]

    def get_output(self, port: int = 0) -> float:
        if 0 <= port < 2:
            return self.output[port]
        return 0.0
'''


def alpha_beta_gamma_filter_template(block: BlockInfo, class_name: str) -> str:
    """Generate an alpha-beta-gamma position, velocity, and acceleration filter."""
    alpha = block.parameters.get("alpha", 0.5)
    beta = block.parameters.get("beta", 0.3)
    gamma = block.parameters.get("gamma", 0.1)
    sample_time = block.parameters.get("sampleTime", 0.1)
    return f'''
class {class_name}:
    """Alpha-beta-gamma tracking filter: {block.name}"""

    def __init__(self):
        self.alpha = {alpha}
        self.beta = {beta}
        self.gamma = {gamma}
        self.sample_time = {sample_time}
        self.input = 0.0
        self.position = 0.0
        self.velocity = 0.0
        self.acceleration = 0.0
        self.output = [0.0, 0.0, 0.0]

    def init(self):
        self.position = 0.0
        self.velocity = 0.0
        self.acceleration = 0.0
        self.output = [0.0, 0.0, 0.0]

    def update(self, t: float):
        dt = self.sample_time
        predicted_position = (
            self.position + self.velocity * dt + 0.5 * self.acceleration * dt * dt
        )
        predicted_velocity = self.velocity + self.acceleration * dt
        residual = self.input - predicted_position
        self.position = predicted_position + self.alpha * residual
        self.velocity = predicted_velocity + (self.beta / dt) * residual
        self.acceleration += (2.0 * self.gamma / (dt * dt)) * residual
        self.output = [self.position, self.velocity, self.acceleration]

    def get_output(self, port: int = 0) -> float:
        if 0 <= port < 3:
            return self.output[port]
        return 0.0
'''


SENSOR_FUSION_TEMPLATES = {
    "imu_sensor": imu_sensor_template,
    "madgwick_filter": madgwick_filter_template,
    "complementary_filter": complementary_filter_template,
    "alpha_beta_filter": alpha_beta_filter_template,
    "alpha_beta_gamma_filter": alpha_beta_gamma_filter_template,
}
