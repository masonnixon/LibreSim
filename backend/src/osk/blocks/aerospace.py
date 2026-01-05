"""Aerospace Blockset blocks for LibreSim.

These blocks implement aerospace-specific functions similar to
MATLAB Aerospace Blockset.
"""

import math

from ..block import Block

# =============================================================================
# Quaternion Operations
# =============================================================================


class QuaternionNormalize(Block):
    """Normalize a quaternion to unit length.

    Input: [q0, q1, q2, q3] (scalar-first convention)
    Output: Normalized quaternion
    """

    def __init__(self):
        super().__init__()
        self.input = [1.0, 0.0, 0.0, 0.0]
        self.output = [1.0, 0.0, 0.0, 0.0]
        self.input_block = None

    def init(self):
        self.output = [1.0, 0.0, 0.0, 0.0]

    def setInput(self, value, port=0):
        if isinstance(value, list) and len(value) >= 4:
            self.input = value[:4]
        elif port < 4:
            self.input[port] = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            vec = self.input_block.getOutputVector()
            if vec is not None and len(vec) >= 4:
                self.input = vec[:4]

        # Compute magnitude
        mag = math.sqrt(sum(q * q for q in self.input))
        if mag > 1e-15:
            self.output = [q / mag for q in self.input]
        else:
            self.output = [1.0, 0.0, 0.0, 0.0]

    def getOutput(self, port=0):
        if port < 4:
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


class QuaternionMultiply(Block):
    """Multiply two quaternions.

    q_result = q1 * q2 (Hamilton product)
    Scalar-first convention: q = [q0, q1, q2, q3] = [w, x, y, z]
    """

    def __init__(self):
        super().__init__()
        self.q1 = [1.0, 0.0, 0.0, 0.0]
        self.q2 = [1.0, 0.0, 0.0, 0.0]
        self.output = [1.0, 0.0, 0.0, 0.0]
        self.input_blocks = [None, None]

    def init(self):
        self.output = [1.0, 0.0, 0.0, 0.0]

    def setInput(self, value, port=0):
        if isinstance(value, list) and len(value) >= 4:
            if port == 0:
                self.q1 = value[:4]
            else:
                self.q2 = value[:4]

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block

    def update(self):
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                vec = block.getOutputVector()
                if vec is not None and len(vec) >= 4:
                    if i == 0:
                        self.q1 = vec[:4]
                    else:
                        self.q2 = vec[:4]

        w1, x1, y1, z1 = self.q1
        w2, x2, y2, z2 = self.q2

        # Hamilton product
        self.output = [
            w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
            w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
            w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
        ]

    def getOutput(self, port=0):
        if port < 4:
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


class QuaternionConjugate(Block):
    """Compute quaternion conjugate (inverse for unit quaternions).

    Input: [q0, q1, q2, q3]
    Output: [q0, -q1, -q2, -q3]
    """

    def __init__(self):
        super().__init__()
        self.input = [1.0, 0.0, 0.0, 0.0]
        self.output = [1.0, 0.0, 0.0, 0.0]
        self.input_block = None

    def init(self):
        self.output = [1.0, 0.0, 0.0, 0.0]

    def setInput(self, value, port=0):
        if isinstance(value, list) and len(value) >= 4:
            self.input = value[:4]

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            vec = self.input_block.getOutputVector()
            if vec is not None and len(vec) >= 4:
                self.input = vec[:4]

        self.output = [self.input[0], -self.input[1], -self.input[2], -self.input[3]]

    def getOutput(self, port=0):
        if port < 4:
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


class QuaternionToEuler(Block):
    """Convert quaternion to Euler angles (ZYX rotation order).

    Input: [q0, q1, q2, q3] (scalar-first)
    Output: [roll, pitch, yaw] in radians
    """

    def __init__(self):
        super().__init__()
        self.input = [1.0, 0.0, 0.0, 0.0]
        self.output = [0.0, 0.0, 0.0]  # [roll, pitch, yaw]
        self.input_block = None

    def init(self):
        self.output = [0.0, 0.0, 0.0]

    def setInput(self, value, port=0):
        if isinstance(value, list) and len(value) >= 4:
            self.input = value[:4]

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            vec = self.input_block.getOutputVector()
            if vec is not None and len(vec) >= 4:
                self.input = vec[:4]

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

    def getOutput(self, port=0):
        if port < 3:
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


class EulerToQuaternion(Block):
    """Convert Euler angles to quaternion (ZYX rotation order).

    Input: [roll, pitch, yaw] in radians
    Output: [q0, q1, q2, q3] (scalar-first)
    """

    def __init__(self):
        super().__init__()
        self.input = [0.0, 0.0, 0.0]  # [roll, pitch, yaw]
        self.output = [1.0, 0.0, 0.0, 0.0]
        self.input_block = None

    def init(self):
        self.output = [1.0, 0.0, 0.0, 0.0]

    def setInput(self, value, port=0):
        if isinstance(value, list) and len(value) >= 3:
            self.input = value[:3]
        elif port < 3:
            self.input[port] = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            vec = self.input_block.getOutputVector()
            if vec is not None and len(vec) >= 3:
                self.input = vec[:3]

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

    def getOutput(self, port=0):
        if port < 4:
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


class QuaternionRotateVector(Block):
    """Rotate a 3D vector by a quaternion.

    v' = q * v * q^(-1)
    """

    def __init__(self):
        super().__init__()
        self.quaternion = [1.0, 0.0, 0.0, 0.0]
        self.vector = [0.0, 0.0, 0.0]
        self.output = [0.0, 0.0, 0.0]
        self.input_blocks = [None, None]

    def init(self):
        self.output = [0.0, 0.0, 0.0]

    def setInput(self, value, port=0):
        if isinstance(value, list):
            if port == 0 and len(value) >= 4:
                self.quaternion = value[:4]
            elif port == 1 and len(value) >= 3:
                self.vector = value[:3]

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block

    def update(self):
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                vec = block.getOutputVector()
                if vec is not None:
                    if i == 0 and len(vec) >= 4:
                        self.quaternion = vec[:4]
                    elif i == 1 and len(vec) >= 3:
                        self.vector = vec[:3]

        w, x, y, z = self.quaternion
        vx, vy, vz = self.vector

        # Rotation using quaternion rotation formula
        # v' = q * v * q^(-1) = v + 2*w*(q_v x v) + 2*(q_v x (q_v x v))
        # where q_v = [x, y, z]

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

    def getOutput(self, port=0):
        if port < 3:
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


# =============================================================================
# Coordinate Transformations
# =============================================================================


class DCMToQuaternion(Block):
    """Convert Direction Cosine Matrix to quaternion.

    Input: 9-element vector representing 3x3 DCM (row-major)
    Output: [q0, q1, q2, q3] quaternion
    """

    def __init__(self):
        super().__init__()
        self.input = [1, 0, 0, 0, 1, 0, 0, 0, 1]  # Identity
        self.output = [1.0, 0.0, 0.0, 0.0]
        self.input_block = None

    def init(self):
        self.output = [1.0, 0.0, 0.0, 0.0]

    def setInput(self, value, port=0):
        if isinstance(value, list) and len(value) >= 9:
            self.input = value[:9]

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            vec = self.input_block.getOutputVector()
            if vec is not None and len(vec) >= 9:
                self.input = vec[:9]

        # DCM elements (row-major)
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

    def getOutput(self, port=0):
        if port < 4:
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


class QuaternionToDCM(Block):
    """Convert quaternion to Direction Cosine Matrix.

    Input: [q0, q1, q2, q3] quaternion
    Output: 9-element vector representing 3x3 DCM (row-major)
    """

    def __init__(self):
        super().__init__()
        self.input = [1.0, 0.0, 0.0, 0.0]
        self.output = [1, 0, 0, 0, 1, 0, 0, 0, 1]  # Identity
        self.input_block = None

    def init(self):
        self.output = [1, 0, 0, 0, 1, 0, 0, 0, 1]

    def setInput(self, value, port=0):
        if isinstance(value, list) and len(value) >= 4:
            self.input = value[:4]

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            vec = self.input_block.getOutputVector()
            if vec is not None and len(vec) >= 4:
                self.input = vec[:4]

        w, x, y, z = self.input

        # DCM elements
        self.output = [
            1 - 2 * (y * y + z * z),
            2 * (x * y - w * z),
            2 * (x * z + w * y),
            2 * (x * y + w * z),
            1 - 2 * (x * x + z * z),
            2 * (y * z - w * x),
            2 * (x * z - w * y),
            2 * (y * z + w * x),
            1 - 2 * (x * x + y * y),
        ]

    def getOutput(self, port=0):
        if port < 9:
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


# =============================================================================
# Atmosphere Models
# =============================================================================


class ISAAtmosphere(Block):
    """International Standard Atmosphere model.

    Computes atmospheric properties based on altitude.
    Input: Altitude (meters)
    Outputs: [temperature (K), pressure (Pa), density (kg/m^3), speed of sound (m/s)]
    """

    def __init__(self):
        super().__init__()
        self.altitude = 0.0
        self.output = [288.15, 101325.0, 1.225, 340.3]  # Sea level values
        self.input_block = None

        # ISA constants
        self.T0 = 288.15  # Sea level temperature (K)
        self.P0 = 101325.0  # Sea level pressure (Pa)
        self.rho0 = 1.225  # Sea level density (kg/m^3)
        self.g = 9.80665  # Gravity (m/s^2)
        self.R = 287.05  # Gas constant (J/kg/K)
        self.gamma = 1.4  # Specific heat ratio
        self.L = 0.0065  # Temperature lapse rate (K/m) for troposphere

    def init(self):
        self.output = [self.T0, self.P0, self.rho0, 340.3]

    def setInput(self, value, port=0):
        self.altitude = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.altitude = self.input_block.getOutput()

        h = max(0, self.altitude)

        if h <= 11000:  # Troposphere
            T = self.T0 - self.L * h
            P = self.P0 * (T / self.T0) ** (self.g / (self.R * self.L))
        else:  # Simplified stratosphere (isothermal at -56.5°C)
            T11 = self.T0 - self.L * 11000
            P11 = self.P0 * (T11 / self.T0) ** (self.g / (self.R * self.L))
            T = T11
            P = P11 * math.exp(-self.g * (h - 11000) / (self.R * T11))

        rho = P / (self.R * T)
        a = math.sqrt(self.gamma * self.R * T)

        self.output = [T, P, rho, a]

    def getOutput(self, port=0):
        if port < 4:
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


# =============================================================================
# 6-DOF Motion
# =============================================================================


class SixDOFEuler(Block):
    """6-DOF equations of motion with Euler angle representation.

    Computes rigid body dynamics with 6 degrees of freedom.
    Inputs: [Fx, Fy, Fz, Mx, My, Mz] - Forces and moments in body frame
    Parameters: mass, Ixx, Iyy, Izz, Ixz (moments of inertia)
    Outputs: [u, v, w, p, q, r, phi, theta, psi, x, y, z] - velocities, attitudes, positions
    """

    def __init__(self, mass=1.0, Ixx=1.0, Iyy=1.0, Izz=1.0, Ixz=0.0):
        super().__init__()
        self.mass = mass
        self.Ixx = Ixx
        self.Iyy = Iyy
        self.Izz = Izz
        self.Ixz = Ixz

        self.forces = [0.0, 0.0, 0.0]  # Fx, Fy, Fz
        self.moments = [0.0, 0.0, 0.0]  # Mx, My, Mz
        self.output = [0.0] * 12

        self.input_blocks = [None, None]

        # State variables: [u, v, w, p, q, r, phi, theta, psi, x, y, z]
        self.u = self.addIntegrator([0.0, 0.0])  # Forward velocity
        self.v = self.addIntegrator([0.0, 0.0])  # Lateral velocity
        self.w = self.addIntegrator([0.0, 0.0])  # Vertical velocity
        self.p = self.addIntegrator([0.0, 0.0])  # Roll rate
        self.q = self.addIntegrator([0.0, 0.0])  # Pitch rate
        self.r = self.addIntegrator([0.0, 0.0])  # Yaw rate
        self.phi = self.addIntegrator([0.0, 0.0])  # Roll angle
        self.theta = self.addIntegrator([0.0, 0.0])  # Pitch angle
        self.psi = self.addIntegrator([0.0, 0.0])  # Yaw angle
        self.xe = self.addIntegrator([0.0, 0.0])  # X position (Earth frame)
        self.ye = self.addIntegrator([0.0, 0.0])  # Y position (Earth frame)
        self.ze = self.addIntegrator([0.0, 0.0])  # Z position (Earth frame)

    def init(self):
        for state in [
            self.u,
            self.v,
            self.w,
            self.p,
            self.q,
            self.r,
            self.phi,
            self.theta,
            self.psi,
            self.xe,
            self.ye,
            self.ze,
        ]:
            state[0] = 0.0
            state[1] = 0.0
        self.output = [0.0] * 12

    def setInput(self, value, port=0):
        if port == 0 and isinstance(value, list) and len(value) >= 3:
            self.forces = value[:3]
        elif port == 1 and isinstance(value, list) and len(value) >= 3:
            self.moments = value[:3]

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block

    def update(self):
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                vec = block.getOutputVector()
                if vec is not None and len(vec) >= 3:
                    if i == 0:
                        self.forces = vec[:3]
                    else:
                        self.moments = vec[:3]

        Fx, Fy, Fz = self.forces
        L, M, N = self.moments  # Roll, Pitch, Yaw moments

        # Current states
        u, v, w = self.u[0], self.v[0], self.w[0]
        p, q, r = self.p[0], self.q[0], self.r[0]
        phi, theta, psi = self.phi[0], self.theta[0], self.psi[0]

        # Force equations (body frame)
        self.u[1] = Fx / self.mass - q * w + r * v
        self.v[1] = Fy / self.mass - r * u + p * w
        self.w[1] = Fz / self.mass - p * v + q * u

        # Moment equations (simplified, assuming Ixy = Iyz = 0)
        Gamma = self.Ixx * self.Izz - self.Ixz**2
        c1 = ((self.Iyy - self.Izz) * self.Izz - self.Ixz**2) / Gamma
        c2 = ((self.Ixx - self.Iyy + self.Izz) * self.Ixz) / Gamma
        c3 = self.Izz / Gamma
        c4 = self.Ixz / Gamma
        c5 = (self.Izz - self.Ixx) / self.Iyy
        c6 = self.Ixz / self.Iyy
        c7 = 1.0 / self.Iyy
        c8 = ((self.Ixx - self.Iyy) * self.Ixx + self.Ixz**2) / Gamma
        c9 = self.Ixx / Gamma

        self.p[1] = c1 * p * q + c2 * q * r + c3 * L + c4 * N
        self.q[1] = c5 * p * r + c6 * (p**2 - r**2) + c7 * M
        self.r[1] = c8 * p * q - c2 * q * r + c4 * L + c9 * N

        # Kinematic equations (Euler angles)
        cos_phi, sin_phi = math.cos(phi), math.sin(phi)
        cos_theta = math.cos(theta)
        tan_theta = math.tan(theta) if abs(cos_theta) > 1e-10 else 0.0

        self.phi[1] = p + (q * sin_phi + r * cos_phi) * tan_theta
        self.theta[1] = q * cos_phi - r * sin_phi
        if abs(cos_theta) > 1e-10:
            self.psi[1] = (q * sin_phi + r * cos_phi) / cos_theta
        else:
            self.psi[1] = 0.0

        # Navigation equations (body to Earth frame)
        cos_psi, sin_psi = math.cos(psi), math.sin(psi)
        sin_theta = math.sin(theta)

        self.xe[1] = (
            (cos_theta * cos_psi) * u
            + (sin_phi * sin_theta * cos_psi - cos_phi * sin_psi) * v
            + (cos_phi * sin_theta * cos_psi + sin_phi * sin_psi) * w
        )

        self.ye[1] = (
            (cos_theta * sin_psi) * u
            + (sin_phi * sin_theta * sin_psi + cos_phi * cos_psi) * v
            + (cos_phi * sin_theta * sin_psi - sin_phi * cos_psi) * w
        )

        self.ze[1] = (-sin_theta) * u + (sin_phi * cos_theta) * v + (cos_phi * cos_theta) * w

        # Update output
        self.output = [
            self.u[0],
            self.v[0],
            self.w[0],
            self.p[0],
            self.q[0],
            self.r[0],
            self.phi[0],
            self.theta[0],
            self.psi[0],
            self.xe[0],
            self.ye[0],
            self.ze[0],
        ]

    def getOutput(self, port=0):
        if port < 12:
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


# =============================================================================
# Gravity Models
# =============================================================================


class FlatEarthGravity(Block):
    """Flat Earth gravity model.

    Returns constant gravitational acceleration.
    Input: Position (optional)
    Output: [0, 0, g] gravity vector in NED frame
    """

    def __init__(self, g=9.80665):
        super().__init__()
        self.g = g
        self.output = [0.0, 0.0, g]
        self.input_block = None

    def init(self):
        self.output = [0.0, 0.0, self.g]

    def setInput(self, value, port=0):
        pass  # Gravity doesn't depend on position in flat Earth model

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        self.output = [0.0, 0.0, self.g]

    def getOutput(self, port=0):
        if port < 3:
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


class WGS84Gravity(Block):
    """WGS84 gravity model.

    Computes gravity based on latitude and altitude.
    Input: [latitude (rad), altitude (m)]
    Output: Gravitational acceleration (m/s^2)
    """

    def __init__(self):
        super().__init__()
        self.input = [0.0, 0.0]  # [latitude, altitude]
        self.output = 9.80665
        self.input_block = None

        # WGS84 constants
        self.a = 6378137.0  # Semi-major axis (m)
        self.f = 1 / 298.257223563  # Flattening
        self.ge = 9.7803253359  # Gravity at equator
        self.gp = 9.8321849378  # Gravity at poles

    def init(self):
        self.output = 9.80665

    def setInput(self, value, port=0):
        if isinstance(value, list) and len(value) >= 2:
            self.input = value[:2]
        elif port < 2:
            self.input[port] = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            vec = self.input_block.getOutputVector()
            if vec is not None and len(vec) >= 2:
                self.input = vec[:2]

        lat, h = self.input
        sin_lat2 = math.sin(lat) ** 2

        # Gravity at sea level (Somigliana formula)
        g0 = (
            self.ge * (1 + 0.00193185265241 * sin_lat2) / math.sqrt(1 - 0.00669437999014 * sin_lat2)
        )

        # Free-air correction for altitude
        self.output = g0 * (1 - 2 * h / self.a)

    def getOutput(self, port=0):
        return self.output
