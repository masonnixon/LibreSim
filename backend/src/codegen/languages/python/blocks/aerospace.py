"""Python templates for aerospace blocks."""

from ....models import BlockInfo


def quaternion_normalize_template(block: BlockInfo, class_name: str) -> str:
    """Generate QuaternionNormalize block code."""
    return f'''
import math

class {class_name}:
    """Quaternion Normalize block: {block.name}"""

    def __init__(self):
        self.input = [1.0, 0.0, 0.0, 0.0]  # [w, x, y, z]
        self.output = [1.0, 0.0, 0.0, 0.0]

    def init(self):
        self.output = [1.0, 0.0, 0.0, 0.0]

    def update(self, t: float):
        mag = math.sqrt(sum(q * q for q in self.input))
        if mag > 1e-15:
            self.output = [q / mag for q in self.input]
        else:
            self.output = [1.0, 0.0, 0.0, 0.0]

    def get_output(self, port: int = 0) -> float:
        if port < 4:
            return self.output[port]
        return 0.0

    def get_output_vector(self) -> list:
        return list(self.output)
'''


def quaternion_multiply_template(block: BlockInfo, class_name: str) -> str:
    """Generate QuaternionMultiply block code."""
    return f'''
class {class_name}:
    """Quaternion Multiply block: {block.name}

    q_result = q1 * q2 (Hamilton product)
    """

    def __init__(self):
        self.q1 = [1.0, 0.0, 0.0, 0.0]  # First quaternion [w, x, y, z]
        self.q2 = [1.0, 0.0, 0.0, 0.0]  # Second quaternion
        self.output = [1.0, 0.0, 0.0, 0.0]
        self.input = 0.0

    def init(self):
        self.output = [1.0, 0.0, 0.0, 0.0]

    def update(self, t: float):
        w1, x1, y1, z1 = self.q1
        w2, x2, y2, z2 = self.q2

        # Hamilton product
        self.output = [
            w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
            w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
            w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
        ]

    def get_output(self, port: int = 0) -> float:
        if port < 4:
            return self.output[port]
        return 0.0

    def get_output_vector(self) -> list:
        return list(self.output)
'''


def quaternion_conjugate_template(block: BlockInfo, class_name: str) -> str:
    """Generate QuaternionConjugate block code."""
    return f'''
class {class_name}:
    """Quaternion Conjugate block: {block.name}"""

    def __init__(self):
        self.input = [1.0, 0.0, 0.0, 0.0]  # [w, x, y, z]
        self.output = [1.0, 0.0, 0.0, 0.0]

    def init(self):
        self.output = [1.0, 0.0, 0.0, 0.0]

    def update(self, t: float):
        self.output = [self.input[0], -self.input[1], -self.input[2], -self.input[3]]

    def get_output(self, port: int = 0) -> float:
        if port < 4:
            return self.output[port]
        return 0.0

    def get_output_vector(self) -> list:
        return list(self.output)
'''


def quaternion_to_euler_template(block: BlockInfo, class_name: str) -> str:
    """Generate QuaternionToEuler block code."""
    return f'''
import math

class {class_name}:
    """Quaternion to Euler block: {block.name}

    Converts quaternion to Euler angles (ZYX rotation order).
    Output: [roll, pitch, yaw] in radians
    """

    def __init__(self):
        self.input = [1.0, 0.0, 0.0, 0.0]  # [w, x, y, z]
        self.output = [0.0, 0.0, 0.0]  # [roll, pitch, yaw]

    def init(self):
        self.output = [0.0, 0.0, 0.0]

    def update(self, t: float):
        w, x, y, z = self.input

        # Roll (x-axis rotation)
        sinr_cosp = 2.0 * (w * x + y * z)
        cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
        roll = math.atan2(sinr_cosp, cosr_cosp)

        # Pitch (y-axis rotation)
        sinp = 2.0 * (w * y - z * x)
        if abs(sinp) >= 1:
            pitch = math.copysign(math.pi / 2, sinp)
        else:
            pitch = math.asin(sinp)

        # Yaw (z-axis rotation)
        siny_cosp = 2.0 * (w * z + x * y)
        cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
        yaw = math.atan2(siny_cosp, cosy_cosp)

        self.output = [roll, pitch, yaw]

    def get_output(self, port: int = 0) -> float:
        if port < 3:
            return self.output[port]
        return 0.0

    def get_output_vector(self) -> list:
        return list(self.output)
'''


def euler_to_quaternion_template(block: BlockInfo, class_name: str) -> str:
    """Generate EulerToQuaternion block code."""
    return f'''
import math

class {class_name}:
    """Euler to Quaternion block: {block.name}

    Converts Euler angles (ZYX rotation order) to quaternion.
    Input: [roll, pitch, yaw] in radians
    Output: [w, x, y, z] quaternion
    """

    def __init__(self):
        self.input = [0.0, 0.0, 0.0]  # [roll, pitch, yaw]
        self.output = [1.0, 0.0, 0.0, 0.0]  # [w, x, y, z]

    def init(self):
        self.output = [1.0, 0.0, 0.0, 0.0]

    def update(self, t: float):
        roll, pitch, yaw = self.input

        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)

        self.output = [
            cr * cp * cy + sr * sp * sy,  # w
            sr * cp * cy - cr * sp * sy,  # x
            cr * sp * cy + sr * cp * sy,  # y
            cr * cp * sy - sr * sp * cy,  # z
        ]

    def get_output(self, port: int = 0) -> float:
        if port < 4:
            return self.output[port]
        return 0.0

    def get_output_vector(self) -> list:
        return list(self.output)
'''


def quaternion_rotate_vector_template(block: BlockInfo, class_name: str) -> str:
    """Generate QuaternionRotateVector block code."""
    return f'''
class {class_name}:
    """Quaternion Rotate Vector block: {block.name}

    Rotates a 3D vector by a quaternion: v' = q * v * q^(-1)
    """

    def __init__(self):
        self.input = [1.0, 0.0, 0.0, 0.0]  # quaternion [w, x, y, z]
        self.input1 = [0.0, 0.0, 0.0]  # vector
        self.output = [0.0, 0.0, 0.0]

    def init(self):
        self.input = [1.0, 0.0, 0.0, 0.0]
        self.input1 = [0.0, 0.0, 0.0]
        self.output = [0.0, 0.0, 0.0]

    def update(self, t: float):
        w, x, y, z = self.input
        vx, vy, vz = self.input1

        # v' = v + 2*w*(q_v x v) + 2*(q_v x (q_v x v))
        # Cross product: q_v x v
        cx1 = y * vz - z * vy
        cy1 = z * vx - x * vz
        cz1 = x * vy - y * vx

        # Cross product: q_v x (q_v x v)
        cx2 = y * cz1 - z * cy1
        cy2 = z * cx1 - x * cz1
        cz2 = x * cy1 - y * cx1

        self.output = [
            vx + 2.0 * (w * cx1 + cx2),
            vy + 2.0 * (w * cy1 + cy2),
            vz + 2.0 * (w * cz1 + cz2),
        ]

    def get_output(self, port: int = 0) -> float:
        if port < 3:
            return self.output[port]
        return 0.0

    def get_output_vector(self) -> list:
        return list(self.output)
'''


def dcm_to_quaternion_template(block: BlockInfo, class_name: str) -> str:
    """Generate DCMToQuaternion block code."""
    return f'''
import math

class {class_name}:
    """DCM to Quaternion block: {block.name}

    Converts Direction Cosine Matrix to quaternion.
    Input: 9-element vector representing 3x3 DCM (row-major)
    """

    def __init__(self):
        self.input = [1, 0, 0, 0, 1, 0, 0, 0, 1]  # Identity
        self.output = [1.0, 0.0, 0.0, 0.0]

    def init(self):
        self.output = [1.0, 0.0, 0.0, 0.0]

    def update(self, t: float):
        r11, r12, r13, r21, r22, r23, r31, r32, r33 = self.input

        trace = r11 + r22 + r33

        if trace > 0:
            s = 0.5 / math.sqrt(trace + 1.0)
            w = 0.25 / s
            x = (r32 - r23) * s
            y = (r13 - r31) * s
            z = (r21 - r12) * s
        elif r11 > r22 and r11 > r33:
            s = 2.0 * math.sqrt(1.0 + r11 - r22 - r33)
            w = (r32 - r23) / s
            x = 0.25 * s
            y = (r12 + r21) / s
            z = (r13 + r31) / s
        elif r22 > r33:
            s = 2.0 * math.sqrt(1.0 + r22 - r11 - r33)
            w = (r13 - r31) / s
            x = (r12 + r21) / s
            y = 0.25 * s
            z = (r23 + r32) / s
        else:
            s = 2.0 * math.sqrt(1.0 + r33 - r11 - r22)
            w = (r21 - r12) / s
            x = (r13 + r31) / s
            y = (r23 + r32) / s
            z = 0.25 * s

        self.output = [w, x, y, z]

    def get_output(self, port: int = 0) -> float:
        if port < 4:
            return self.output[port]
        return 0.0

    def get_output_vector(self) -> list:
        return list(self.output)
'''


def quaternion_to_dcm_template(block: BlockInfo, class_name: str) -> str:
    """Generate QuaternionToDCM block code."""
    return f'''
class {class_name}:
    """Quaternion to DCM block: {block.name}

    Converts quaternion to Direction Cosine Matrix.
    Output: 9-element vector representing 3x3 DCM (row-major)
    """

    def __init__(self):
        self.input = [1.0, 0.0, 0.0, 0.0]  # [w, x, y, z]
        self.output = [1, 0, 0, 0, 1, 0, 0, 0, 1]  # Identity

    def init(self):
        self.output = [1, 0, 0, 0, 1, 0, 0, 0, 1]

    def update(self, t: float):
        w, x, y, z = self.input

        self.output = [
            1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y),
            2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x),
            2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y),
        ]

    def get_output(self, port: int = 0) -> float:
        if port < 9:
            return self.output[port]
        return 0.0

    def get_output_vector(self) -> list:
        return list(self.output)
'''


def isa_atmosphere_template(block: BlockInfo, class_name: str) -> str:
    """Generate ISAAtmosphere block code."""
    return f'''
import math

class {class_name}:
    """ISA Atmosphere block: {block.name}

    Computes atmospheric properties based on altitude.
    Input: Altitude (meters)
    Outputs: [temperature (K), pressure (Pa), density (kg/m^3), speed of sound (m/s)]
    """

    def __init__(self):
        self.altitude = 0.0
        self.input = 0.0
        # Sea level values
        self.T0 = 288.15  # K
        self.P0 = 101325.0  # Pa
        self.rho0 = 1.225  # kg/m^3
        self.g = 9.80665  # m/s^2
        self.R = 287.05  # J/kg/K
        self.gamma = 1.4
        self.L = 0.0065  # K/m lapse rate
        self.output = [self.T0, self.P0, self.rho0, 340.3]

    def init(self):
        self.output = [self.T0, self.P0, self.rho0, 340.3]

    def update(self, t: float):
        h = max(0, self.input)

        if h <= 11000:  # Troposphere
            T = self.T0 - self.L * h
            P = self.P0 * (T / self.T0) ** (self.g / (self.R * self.L))
        else:  # Stratosphere (simplified)
            T11 = self.T0 - self.L * 11000
            P11 = self.P0 * (T11 / self.T0) ** (self.g / (self.R * self.L))
            T = T11
            P = P11 * math.exp(-self.g * (h - 11000) / (self.R * T11))

        rho = P / (self.R * T)
        a = math.sqrt(self.gamma * self.R * T)

        self.output = [T, P, rho, a]

    def get_output(self, port: int = 0) -> float:
        if port < 4:
            return self.output[port]
        return 0.0

    def get_output_vector(self) -> list:
        return list(self.output)
'''


def flat_earth_gravity_template(block: BlockInfo, class_name: str) -> str:
    """Generate FlatEarthGravity block code."""
    g = block.parameters.get("g", 9.80665)
    return f'''
class {class_name}:
    """Flat Earth Gravity block: {block.name}

    Returns constant gravitational acceleration vector [0, 0, g] in NED frame.
    """

    def __init__(self):
        self.g = {g}
        self.output = [0.0, 0.0, {g}]
        self.input = 0.0

    def init(self):
        self.output = [0.0, 0.0, self.g]

    def update(self, t: float):
        self.output = [0.0, 0.0, self.g]

    def get_output(self, port: int = 0) -> float:
        if port < 3:
            return self.output[port]
        return 0.0

    def get_output_vector(self) -> list:
        return list(self.output)
'''


def wgs84_gravity_template(block: BlockInfo, class_name: str) -> str:
    """Generate WGS84Gravity block code."""
    return f'''
import math

class {class_name}:
    """WGS84 Gravity block: {block.name}

    Computes gravity based on latitude and altitude.
    Input: [latitude (rad), altitude (m)] or scalar (latitude only)
    """

    def __init__(self):
        self.input = [0.0, 0.0]  # [latitude, altitude]
        self.output = 9.80665
        # WGS84 constants
        self.a = 6378137.0  # m
        self.ge = 9.7803253359
        self.gp = 9.8321849378

    def init(self):
        self.output = 9.80665

    def update(self, t: float):
        # Handle both scalar and vector inputs
        if isinstance(self.input, (list, tuple)):
            lat = self.input[0] if len(self.input) > 0 else 0.0
            h = self.input[1] if len(self.input) > 1 else 0.0
        else:
            lat = self.input
            h = 0.0
        sin_lat2 = math.sin(lat) ** 2

        # Somigliana formula
        g0 = self.ge * (1 + 0.00193185265241 * sin_lat2) / \\
             math.sqrt(1 - 0.00669437999014 * sin_lat2)

        # Free-air correction
        self.output = g0 * (1 - 2 * h / self.a)

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def six_dof_euler_template(block: BlockInfo, class_name: str) -> str:
    """Generate SixDOFEuler block code."""
    mass = block.parameters.get("mass", 1.0)
    ixx = block.parameters.get("Ixx", 1.0)
    iyy = block.parameters.get("Iyy", 1.0)
    izz = block.parameters.get("Izz", 1.0)
    ixz = block.parameters.get("Ixz", 0.0)
    return f'''
import math

class {class_name}:
    """6-DOF Euler block: {block.name}

    6-DOF equations of motion with Euler angle representation.
    Inputs: Forces [Fx, Fy, Fz] and Moments [Mx, My, Mz] in body frame
    Outputs: [u, v, w, p, q, r, phi, theta, psi, x, y, z]
    """

    def __init__(self):
        self.mass = {mass}
        self.Ixx = {ixx}
        self.Iyy = {iyy}
        self.Izz = {izz}
        self.Ixz = {ixz}
        self.forces = [0.0, 0.0, 0.0]
        self.moments = [0.0, 0.0, 0.0]
        self.input = 0.0

        # State variables [value, derivative]
        self.u = [0.0, 0.0]  # Forward velocity
        self.v = [0.0, 0.0]  # Lateral velocity
        self.w = [0.0, 0.0]  # Vertical velocity
        self.p = [0.0, 0.0]  # Roll rate
        self.q = [0.0, 0.0]  # Pitch rate
        self.r = [0.0, 0.0]  # Yaw rate
        self.phi = [0.0, 0.0]  # Roll angle
        self.theta = [0.0, 0.0]  # Pitch angle
        self.psi = [0.0, 0.0]  # Yaw angle
        self.xe = [0.0, 0.0]  # X position
        self.ye = [0.0, 0.0]  # Y position
        self.ze = [0.0, 0.0]  # Z position

        # RK4 intermediates
        self.xd0 = [[0.0, 0.0] for _ in range(12)]
        self.xd1 = [[0.0, 0.0] for _ in range(12)]
        self.xd2 = [[0.0, 0.0] for _ in range(12)]
        self.xd3 = [[0.0, 0.0] for _ in range(12)]

        self.output = [0.0] * 12

    def init(self):
        for state in [self.u, self.v, self.w, self.p, self.q, self.r,
                      self.phi, self.theta, self.psi, self.xe, self.ye, self.ze]:
            state[0] = 0.0
            state[1] = 0.0
        self.output = [0.0] * 12

    def update(self, t: float):
        Fx, Fy, Fz = self.forces
        L, M, N = self.moments

        u, v, w = self.u[0], self.v[0], self.w[0]
        p, q, r = self.p[0], self.q[0], self.r[0]
        phi, theta, psi = self.phi[0], self.theta[0], self.psi[0]

        # Force equations
        self.u[1] = Fx / self.mass - q * w + r * v
        self.v[1] = Fy / self.mass - r * u + p * w
        self.w[1] = Fz / self.mass - p * v + q * u

        # Moment equations
        Gamma = self.Ixx * self.Izz - self.Ixz ** 2
        c1 = ((self.Iyy - self.Izz) * self.Izz - self.Ixz ** 2) / Gamma
        c2 = ((self.Ixx - self.Iyy + self.Izz) * self.Ixz) / Gamma
        c3 = self.Izz / Gamma
        c4 = self.Ixz / Gamma
        c5 = (self.Izz - self.Ixx) / self.Iyy
        c6 = self.Ixz / self.Iyy
        c7 = 1.0 / self.Iyy
        c8 = ((self.Ixx - self.Iyy) * self.Ixx + self.Ixz ** 2) / Gamma
        c9 = self.Ixx / Gamma

        self.p[1] = c1 * p * q + c2 * q * r + c3 * L + c4 * N
        self.q[1] = c5 * p * r + c6 * (p ** 2 - r ** 2) + c7 * M
        self.r[1] = c8 * p * q - c2 * q * r + c4 * L + c9 * N

        # Kinematic equations
        cos_phi, sin_phi = math.cos(phi), math.sin(phi)
        cos_theta = math.cos(theta)
        tan_theta = math.tan(theta) if abs(cos_theta) > 1e-10 else 0.0

        self.phi[1] = p + (q * sin_phi + r * cos_phi) * tan_theta
        self.theta[1] = q * cos_phi - r * sin_phi
        if abs(cos_theta) > 1e-10:
            self.psi[1] = (q * sin_phi + r * cos_phi) / cos_theta
        else:
            self.psi[1] = 0.0

        # Navigation equations
        cos_psi, sin_psi = math.cos(psi), math.sin(psi)
        sin_theta = math.sin(theta)

        self.xe[1] = (cos_theta * cos_psi) * u + \\
                     (sin_phi * sin_theta * cos_psi - cos_phi * sin_psi) * v + \\
                     (cos_phi * sin_theta * cos_psi + sin_phi * sin_psi) * w

        self.ye[1] = (cos_theta * sin_psi) * u + \\
                     (sin_phi * sin_theta * sin_psi + cos_phi * cos_psi) * v + \\
                     (cos_phi * sin_theta * sin_psi - sin_phi * cos_psi) * w

        self.ze[1] = (-sin_theta) * u + (sin_phi * cos_theta) * v + (cos_phi * cos_theta) * w

        self.output = [
            self.u[0], self.v[0], self.w[0],
            self.p[0], self.q[0], self.r[0],
            self.phi[0], self.theta[0], self.psi[0],
            self.xe[0], self.ye[0], self.ze[0]
        ]

    def get_output(self, port: int = 0) -> float:
        if port < 12:
            return self.output[port]
        return 0.0

    def get_output_vector(self) -> list:
        return list(self.output)
'''


# Template registry for aerospace blocks
AEROSPACE_TEMPLATES = {
    "quaternion_normalize": quaternion_normalize_template,
    "quaternion_multiply": quaternion_multiply_template,
    "quaternion_conjugate": quaternion_conjugate_template,
    "quaternion_to_euler": quaternion_to_euler_template,
    "euler_to_quaternion": euler_to_quaternion_template,
    "quaternion_rotate_vector": quaternion_rotate_vector_template,
    "dcm_to_quaternion": dcm_to_quaternion_template,
    "quaternion_to_dcm": quaternion_to_dcm_template,
    "isa_atmosphere": isa_atmosphere_template,
    "flat_earth_gravity": flat_earth_gravity_template,
    "wgs84_gravity": wgs84_gravity_template,
    "six_dof_euler": six_dof_euler_template,
}
