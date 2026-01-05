"""Navigation Toolbox blocks for LibreSim.

These blocks implement navigation and coordinate transformation functions
similar to MATLAB Navigation Toolbox.
"""

import math

from ..block import Block

# =============================================================================
# WGS84 Ellipsoid Constants
# =============================================================================

WGS84_A = 6378137.0  # Semi-major axis (m)
WGS84_F = 1 / 298.257223563  # Flattening
WGS84_B = WGS84_A * (1 - WGS84_F)  # Semi-minor axis
WGS84_E2 = 2 * WGS84_F - WGS84_F**2  # First eccentricity squared
WGS84_EP2 = WGS84_E2 / (1 - WGS84_E2)  # Second eccentricity squared


# =============================================================================
# Coordinate Transformation Conversion Block
# =============================================================================


class CoordinateTransformationConversion(Block):
    """Convert between different coordinate representations.

    This is the key Navigation Toolbox block that converts between
    multiple coordinate/attitude representations.

    Supported conversions:
    - Geodetic (LLA) <-> ECEF
    - ECEF <-> NED/ENU (requires reference)
    - Euler angles <-> DCM
    - Euler angles <-> Quaternion
    - DCM <-> Quaternion
    - Axis-angle <-> Quaternion

    Parameters:
        input_type: Type of input coordinates
        output_type: Type of output coordinates
    """

    SUPPORTED_CONVERSIONS = {
        ("lla", "ecef"),
        ("ecef", "lla"),
        ("ecef", "ned"),
        ("ned", "ecef"),
        ("ecef", "enu"),
        ("enu", "ecef"),
        ("euler", "dcm"),
        ("dcm", "euler"),
        ("euler", "quaternion"),
        ("quaternion", "euler"),
        ("dcm", "quaternion"),
        ("quaternion", "dcm"),
        ("axis_angle", "quaternion"),
        ("quaternion", "axis_angle"),
    }

    def __init__(
        self,
        input_type: str = "lla",
        output_type: str = "ecef",
        reference_lla: list | None = None,
        euler_sequence: str = "ZYX",
    ):
        super().__init__()
        self.input_type = input_type.lower()
        self.output_type = output_type.lower()
        self.reference_lla = reference_lla if reference_lla else [0.0, 0.0, 0.0]
        self.euler_sequence = euler_sequence.upper()

        # Pre-compute reference ECEF for NED/ENU conversions
        self._ref_ecef = None
        self._ref_rotation = None
        if self.input_type in ["ned", "enu"] or self.output_type in ["ned", "enu"]:
            self._compute_reference()

        self.input = []
        self.output = []
        self.input_block = None

    def _compute_reference(self):
        """Pre-compute reference frame transformation."""
        lat, lon, alt = self.reference_lla
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)

        # Reference ECEF
        N = WGS84_A / math.sqrt(1 - WGS84_E2 * math.sin(lat_rad) ** 2)
        self._ref_ecef = [
            (N + alt) * math.cos(lat_rad) * math.cos(lon_rad),
            (N + alt) * math.cos(lat_rad) * math.sin(lon_rad),
            (N * (1 - WGS84_E2) + alt) * math.sin(lat_rad),
        ]

        # Rotation matrix from ECEF to NED
        sin_lat = math.sin(lat_rad)
        cos_lat = math.cos(lat_rad)
        sin_lon = math.sin(lon_rad)
        cos_lon = math.cos(lon_rad)

        # R_ned_ecef (rows are NED unit vectors in ECEF)
        self._ref_rotation = [
            [-sin_lat * cos_lon, -sin_lat * sin_lon, cos_lat],  # North
            [-sin_lon, cos_lon, 0],  # East
            [-cos_lat * cos_lon, -cos_lat * sin_lon, -sin_lat],  # Down
        ]

    def init(self):
        self.input = []
        self.output = []

    def setInput(self, value, port=0):
        if isinstance(value, list):
            self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            vec = self.input_block.getOutputVector()
            if vec is not None:
                self.input = vec

        if not self.input:
            return

        conversion = (self.input_type, self.output_type)

        if conversion == ("lla", "ecef"):
            self.output = self._lla_to_ecef(self.input)
        elif conversion == ("ecef", "lla"):
            self.output = self._ecef_to_lla(self.input)
        elif conversion == ("ecef", "ned"):
            self.output = self._ecef_to_ned(self.input)
        elif conversion == ("ned", "ecef"):
            self.output = self._ned_to_ecef(self.input)
        elif conversion == ("ecef", "enu"):
            self.output = self._ecef_to_enu(self.input)
        elif conversion == ("enu", "ecef"):
            self.output = self._enu_to_ecef(self.input)
        elif conversion == ("euler", "dcm"):
            self.output = self._euler_to_dcm(self.input)
        elif conversion == ("dcm", "euler"):
            self.output = self._dcm_to_euler(self.input)
        elif conversion == ("euler", "quaternion"):
            self.output = self._euler_to_quaternion(self.input)
        elif conversion == ("quaternion", "euler"):
            self.output = self._quaternion_to_euler(self.input)
        elif conversion == ("dcm", "quaternion"):
            self.output = self._dcm_to_quaternion(self.input)
        elif conversion == ("quaternion", "dcm"):
            self.output = self._quaternion_to_dcm(self.input)
        elif conversion == ("axis_angle", "quaternion"):
            self.output = self._axis_angle_to_quaternion(self.input)
        elif conversion == ("quaternion", "axis_angle"):
            self.output = self._quaternion_to_axis_angle(self.input)
        else:
            self.output = self.input  # Pass through if unsupported

    def _lla_to_ecef(self, lla: list) -> list:
        """Convert LLA (lat, lon, alt in degrees/meters) to ECEF."""
        lat = math.radians(lla[0])
        lon = math.radians(lla[1])
        alt = lla[2]

        N = WGS84_A / math.sqrt(1 - WGS84_E2 * math.sin(lat) ** 2)

        x = (N + alt) * math.cos(lat) * math.cos(lon)
        y = (N + alt) * math.cos(lat) * math.sin(lon)
        z = (N * (1 - WGS84_E2) + alt) * math.sin(lat)

        return [x, y, z]

    def _ecef_to_lla(self, ecef: list) -> list:
        """Convert ECEF to LLA using iterative method."""
        x, y, z = ecef

        lon = math.atan2(y, x)

        p = math.sqrt(x**2 + y**2)
        lat = math.atan2(z, p * (1 - WGS84_E2))  # Initial guess

        # Iterate to refine latitude
        for _ in range(10):
            N = WGS84_A / math.sqrt(1 - WGS84_E2 * math.sin(lat) ** 2)
            lat_new = math.atan2(z + WGS84_E2 * N * math.sin(lat), p)
            if abs(lat_new - lat) < 1e-12:
                break
            lat = lat_new

        N = WGS84_A / math.sqrt(1 - WGS84_E2 * math.sin(lat) ** 2)
        alt = p / math.cos(lat) - N

        return [math.degrees(lat), math.degrees(lon), alt]

    def _ecef_to_ned(self, ecef: list) -> list:
        """Convert ECEF position to NED relative to reference."""
        if self._ref_ecef is None:
            return ecef

        # Difference in ECEF
        dx = ecef[0] - self._ref_ecef[0]
        dy = ecef[1] - self._ref_ecef[1]
        dz = ecef[2] - self._ref_ecef[2]

        # Rotate to NED
        ned = [
            self._ref_rotation[0][0] * dx
            + self._ref_rotation[0][1] * dy
            + self._ref_rotation[0][2] * dz,
            self._ref_rotation[1][0] * dx
            + self._ref_rotation[1][1] * dy
            + self._ref_rotation[1][2] * dz,
            self._ref_rotation[2][0] * dx
            + self._ref_rotation[2][1] * dy
            + self._ref_rotation[2][2] * dz,
        ]

        return ned

    def _ned_to_ecef(self, ned: list) -> list:
        """Convert NED position to ECEF using reference."""
        if self._ref_ecef is None:
            return ned

        # Transpose rotation (NED to ECEF)
        R_T = [[self._ref_rotation[j][i] for j in range(3)] for i in range(3)]

        # Rotate from NED to ECEF
        dx = R_T[0][0] * ned[0] + R_T[0][1] * ned[1] + R_T[0][2] * ned[2]
        dy = R_T[1][0] * ned[0] + R_T[1][1] * ned[1] + R_T[1][2] * ned[2]
        dz = R_T[2][0] * ned[0] + R_T[2][1] * ned[1] + R_T[2][2] * ned[2]

        return [
            self._ref_ecef[0] + dx,
            self._ref_ecef[1] + dy,
            self._ref_ecef[2] + dz,
        ]

    def _ecef_to_enu(self, ecef: list) -> list:
        """Convert ECEF to ENU relative to reference."""
        ned = self._ecef_to_ned(ecef)
        return [ned[1], ned[0], -ned[2]]  # ENU = [E, N, U] = [NED[1], NED[0], -NED[2]]

    def _enu_to_ecef(self, enu: list) -> list:
        """Convert ENU to ECEF using reference."""
        ned = [enu[1], enu[0], -enu[2]]  # NED = [ENU[1], ENU[0], -ENU[2]]
        return self._ned_to_ecef(ned)

    def _euler_to_dcm(self, euler: list) -> list:
        """Convert Euler angles (ZYX) to DCM (row-major)."""
        phi, theta, psi = euler  # roll, pitch, yaw

        c1, s1 = math.cos(phi), math.sin(phi)
        c2, s2 = math.cos(theta), math.sin(theta)
        c3, s3 = math.cos(psi), math.sin(psi)

        # ZYX rotation: R = Rz(psi) * Ry(theta) * Rx(phi)
        dcm = [
            c2 * c3,
            c3 * s1 * s2 - c1 * s3,
            s1 * s3 + c1 * c3 * s2,
            c2 * s3,
            c1 * c3 + s1 * s2 * s3,
            c1 * s2 * s3 - c3 * s1,
            -s2,
            c2 * s1,
            c1 * c2,
        ]

        return dcm

    def _dcm_to_euler(self, dcm: list) -> list:
        """Convert DCM (row-major) to Euler angles (ZYX)."""
        # Extract angles from DCM
        theta = -math.asin(max(-1, min(1, dcm[6])))  # Pitch

        if abs(math.cos(theta)) > 1e-6:
            phi = math.atan2(dcm[7], dcm[8])  # Roll
            psi = math.atan2(dcm[3], dcm[0])  # Yaw
        else:
            # Gimbal lock
            phi = 0
            psi = math.atan2(-dcm[1], dcm[4])

        return [phi, theta, psi]

    def _euler_to_quaternion(self, euler: list) -> list:
        """Convert Euler angles to quaternion [w, x, y, z]."""
        phi, theta, psi = euler

        c_phi = math.cos(phi / 2)
        s_phi = math.sin(phi / 2)
        c_theta = math.cos(theta / 2)
        s_theta = math.sin(theta / 2)
        c_psi = math.cos(psi / 2)
        s_psi = math.sin(psi / 2)

        w = c_phi * c_theta * c_psi + s_phi * s_theta * s_psi
        x = s_phi * c_theta * c_psi - c_phi * s_theta * s_psi
        y = c_phi * s_theta * c_psi + s_phi * c_theta * s_psi
        z = c_phi * c_theta * s_psi - s_phi * s_theta * c_psi

        return [w, x, y, z]

    def _quaternion_to_euler(self, q: list) -> list:
        """Convert quaternion [w, x, y, z] to Euler angles."""
        w, x, y, z = q

        # Roll (x-axis rotation)
        sinr_cosp = 2 * (w * x + y * z)
        cosr_cosp = 1 - 2 * (x * x + y * y)
        phi = math.atan2(sinr_cosp, cosr_cosp)

        # Pitch (y-axis rotation)
        sinp = 2 * (w * y - z * x)
        if abs(sinp) >= 1:
            theta = math.copysign(math.pi / 2, sinp)
        else:
            theta = math.asin(sinp)

        # Yaw (z-axis rotation)
        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        psi = math.atan2(siny_cosp, cosy_cosp)

        return [phi, theta, psi]

    def _dcm_to_quaternion(self, dcm: list) -> list:
        """Convert DCM to quaternion."""
        r11, r12, r13, r21, r22, r23, r31, r32, r33 = dcm
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

        return [w, x, y, z]

    def _quaternion_to_dcm(self, q: list) -> list:
        """Convert quaternion to DCM (row-major)."""
        w, x, y, z = q

        return [
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

    def _axis_angle_to_quaternion(self, axis_angle: list) -> list:
        """Convert axis-angle [ax, ay, az, angle] to quaternion."""
        ax, ay, az, angle = axis_angle

        # Normalize axis
        mag = math.sqrt(ax * ax + ay * ay + az * az)
        if mag > 1e-10:
            ax, ay, az = ax / mag, ay / mag, az / mag
        else:
            return [1.0, 0.0, 0.0, 0.0]

        half_angle = angle / 2
        s = math.sin(half_angle)

        return [math.cos(half_angle), ax * s, ay * s, az * s]

    def _quaternion_to_axis_angle(self, q: list) -> list:
        """Convert quaternion to axis-angle [ax, ay, az, angle]."""
        w, x, y, z = q

        # Normalize
        mag = math.sqrt(w * w + x * x + y * y + z * z)
        if mag > 1e-10:
            w, x, y, z = w / mag, x / mag, y / mag, z / mag

        angle = 2 * math.acos(max(-1, min(1, w)))
        s = math.sqrt(1 - w * w)

        if s < 1e-10:
            return [1.0, 0.0, 0.0, 0.0]

        return [x / s, y / s, z / s, angle]

    def getOutput(self, port=0):
        if port < len(self.output):
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


# =============================================================================
# Individual Coordinate Transformation Blocks
# =============================================================================


class LLAToECEF(Block):
    """Convert geodetic coordinates (LLA) to ECEF.

    Input: [latitude (deg), longitude (deg), altitude (m)]
    Output: [X, Y, Z] in meters
    """

    def __init__(self):
        super().__init__()
        self.input = [0.0, 0.0, 0.0]
        self.output = [0.0, 0.0, 0.0]
        self.input_block = None

    def init(self):
        self.output = [0.0, 0.0, 0.0]

    def setInput(self, value, port=0):
        if isinstance(value, list) and len(value) >= 3:
            self.input = value[:3]

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            vec = self.input_block.getOutputVector()
            if vec is not None and len(vec) >= 3:
                self.input = vec[:3]

        lat = math.radians(self.input[0])
        lon = math.radians(self.input[1])
        alt = self.input[2]

        N = WGS84_A / math.sqrt(1 - WGS84_E2 * math.sin(lat) ** 2)

        self.output = [
            (N + alt) * math.cos(lat) * math.cos(lon),
            (N + alt) * math.cos(lat) * math.sin(lon),
            (N * (1 - WGS84_E2) + alt) * math.sin(lat),
        ]

    def getOutput(self, port=0):
        if port < 3:
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


class ECEFToLLA(Block):
    """Convert ECEF coordinates to geodetic (LLA).

    Input: [X, Y, Z] in meters
    Output: [latitude (deg), longitude (deg), altitude (m)]
    """

    def __init__(self):
        super().__init__()
        self.input = [0.0, 0.0, 0.0]
        self.output = [0.0, 0.0, 0.0]
        self.input_block = None

    def init(self):
        self.output = [0.0, 0.0, 0.0]

    def setInput(self, value, port=0):
        if isinstance(value, list) and len(value) >= 3:
            self.input = value[:3]

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            vec = self.input_block.getOutputVector()
            if vec is not None and len(vec) >= 3:
                self.input = vec[:3]

        x, y, z = self.input

        lon = math.atan2(y, x)
        p = math.sqrt(x**2 + y**2)
        lat = math.atan2(z, p * (1 - WGS84_E2))

        for _ in range(10):
            N = WGS84_A / math.sqrt(1 - WGS84_E2 * math.sin(lat) ** 2)
            lat_new = math.atan2(z + WGS84_E2 * N * math.sin(lat), p)
            if abs(lat_new - lat) < 1e-12:
                break
            lat = lat_new

        N = WGS84_A / math.sqrt(1 - WGS84_E2 * math.sin(lat) ** 2)
        if abs(math.cos(lat)) > 1e-10:
            alt = p / math.cos(lat) - N
        else:
            alt = abs(z) - WGS84_B

        self.output = [math.degrees(lat), math.degrees(lon), alt]

    def getOutput(self, port=0):
        if port < 3:
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


class ECEFToNED(Block):
    """Convert ECEF position to NED relative to reference.

    Inputs:
        - Port 0: ECEF position [X, Y, Z]
        - Port 1: Reference LLA [lat, lon, alt] (optional, use parameter if not connected)

    Output: [North, East, Down] in meters
    """

    def __init__(self, reference_lla: list | None = None):
        super().__init__()
        self.reference_lla = reference_lla if reference_lla else [0.0, 0.0, 0.0]
        self.input_ecef = [0.0, 0.0, 0.0]
        self.output = [0.0, 0.0, 0.0]
        self.input_blocks = [None, None]
        self._compute_reference()

    def _compute_reference(self):
        lat = math.radians(self.reference_lla[0])
        lon = math.radians(self.reference_lla[1])
        alt = self.reference_lla[2]

        N = WGS84_A / math.sqrt(1 - WGS84_E2 * math.sin(lat) ** 2)
        self._ref_ecef = [
            (N + alt) * math.cos(lat) * math.cos(lon),
            (N + alt) * math.cos(lat) * math.sin(lon),
            (N * (1 - WGS84_E2) + alt) * math.sin(lat),
        ]

        sin_lat = math.sin(lat)
        cos_lat = math.cos(lat)
        sin_lon = math.sin(lon)
        cos_lon = math.cos(lon)

        self._rotation = [
            [-sin_lat * cos_lon, -sin_lat * sin_lon, cos_lat],
            [-sin_lon, cos_lon, 0],
            [-cos_lat * cos_lon, -cos_lat * sin_lon, -sin_lat],
        ]

    def init(self):
        self.output = [0.0, 0.0, 0.0]

    def setInput(self, value, port=0):
        if port == 0 and isinstance(value, list) and len(value) >= 3:
            self.input_ecef = value[:3]
        elif port == 1 and isinstance(value, list) and len(value) >= 3:
            self.reference_lla = value[:3]
            self._compute_reference()

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block

    def update(self):
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                vec = block.getOutputVector()
                if vec is not None and len(vec) >= 3:
                    if i == 0:
                        self.input_ecef = vec[:3]
                    else:
                        self.reference_lla = vec[:3]
                        self._compute_reference()

        dx = self.input_ecef[0] - self._ref_ecef[0]
        dy = self.input_ecef[1] - self._ref_ecef[1]
        dz = self.input_ecef[2] - self._ref_ecef[2]

        self.output = [
            self._rotation[0][0] * dx + self._rotation[0][1] * dy + self._rotation[0][2] * dz,
            self._rotation[1][0] * dx + self._rotation[1][1] * dy + self._rotation[1][2] * dz,
            self._rotation[2][0] * dx + self._rotation[2][1] * dy + self._rotation[2][2] * dz,
        ]

    def getOutput(self, port=0):
        if port < 3:
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


class NEDToECEF(Block):
    """Convert NED position to ECEF.

    Input: [North, East, Down] in meters
    Parameter: Reference LLA
    Output: [X, Y, Z] in meters
    """

    def __init__(self, reference_lla: list | None = None):
        super().__init__()
        self.reference_lla = reference_lla if reference_lla else [0.0, 0.0, 0.0]
        self.input_ned = [0.0, 0.0, 0.0]
        self.output = [0.0, 0.0, 0.0]
        self.input_block = None
        self._compute_reference()

    def _compute_reference(self):
        lat = math.radians(self.reference_lla[0])
        lon = math.radians(self.reference_lla[1])
        alt = self.reference_lla[2]

        N = WGS84_A / math.sqrt(1 - WGS84_E2 * math.sin(lat) ** 2)
        self._ref_ecef = [
            (N + alt) * math.cos(lat) * math.cos(lon),
            (N + alt) * math.cos(lat) * math.sin(lon),
            (N * (1 - WGS84_E2) + alt) * math.sin(lat),
        ]

        sin_lat = math.sin(lat)
        cos_lat = math.cos(lat)
        sin_lon = math.sin(lon)
        cos_lon = math.cos(lon)

        # Transpose of NED rotation matrix
        self._rotation_T = [
            [-sin_lat * cos_lon, -sin_lon, -cos_lat * cos_lon],
            [-sin_lat * sin_lon, cos_lon, -cos_lat * sin_lon],
            [cos_lat, 0, -sin_lat],
        ]

    def init(self):
        self.output = [0.0, 0.0, 0.0]

    def setInput(self, value, port=0):
        if isinstance(value, list) and len(value) >= 3:
            self.input_ned = value[:3]

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            vec = self.input_block.getOutputVector()
            if vec is not None and len(vec) >= 3:
                self.input_ned = vec[:3]

        n, e, d = self.input_ned

        dx = self._rotation_T[0][0] * n + self._rotation_T[0][1] * e + self._rotation_T[0][2] * d
        dy = self._rotation_T[1][0] * n + self._rotation_T[1][1] * e + self._rotation_T[1][2] * d
        dz = self._rotation_T[2][0] * n + self._rotation_T[2][1] * e + self._rotation_T[2][2] * d

        self.output = [
            self._ref_ecef[0] + dx,
            self._ref_ecef[1] + dy,
            self._ref_ecef[2] + dz,
        ]

    def getOutput(self, port=0):
        if port < 3:
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


# =============================================================================
# Waypoint Navigation
# =============================================================================


class WaypointFollower(Block):
    """Waypoint follower for navigation.

    Computes heading and distance to next waypoint.

    Input: Current position [lat, lon] in degrees
    Parameters: List of waypoints [[lat1, lon1], [lat2, lon2], ...]
    Outputs: [heading_to_wp (rad), distance_to_wp (m), current_wp_index]
    """

    def __init__(self, waypoints: list | None = None, acceptance_radius: float = 100.0):
        super().__init__()
        self.waypoints = waypoints if waypoints else [[0.0, 0.0]]
        self.acceptance_radius = acceptance_radius
        self.current_wp_index = 0
        self.position = [0.0, 0.0]
        self.output = [0.0, 0.0, 0.0]
        self.input_block = None

    def init(self):
        self.current_wp_index = 0
        self.output = [0.0, 0.0, 0.0]

    def setInput(self, value, port=0):
        if isinstance(value, list) and len(value) >= 2:
            self.position = value[:2]

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def _compute_bearing_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> tuple:
        """Compute bearing and distance between two points."""
        lat1_r = math.radians(lat1)
        lon1_r = math.radians(lon1)
        lat2_r = math.radians(lat2)
        lon2_r = math.radians(lon2)

        dlon = lon2_r - lon1_r
        dlat = lat2_r - lat1_r

        # Haversine formula for distance
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = WGS84_A * c  # Approximate distance using semi-major axis

        # Bearing calculation
        x = math.sin(dlon) * math.cos(lat2_r)
        y = math.cos(lat1_r) * math.sin(lat2_r) - math.sin(lat1_r) * math.cos(lat2_r) * math.cos(
            dlon
        )
        bearing = math.atan2(x, y)

        return bearing, distance

    def update(self):
        if self.input_block is not None:
            vec = self.input_block.getOutputVector()
            if vec is not None and len(vec) >= 2:
                self.position = vec[:2]

        if self.current_wp_index >= len(self.waypoints):
            self.output = [0.0, 0.0, float(self.current_wp_index)]
            return

        target_wp = self.waypoints[self.current_wp_index]
        bearing, distance = self._compute_bearing_distance(
            self.position[0], self.position[1], target_wp[0], target_wp[1]
        )

        # Check if we've reached the waypoint
        if distance < self.acceptance_radius:
            if self.current_wp_index < len(self.waypoints) - 1:
                self.current_wp_index += 1
                # Recompute for new waypoint
                target_wp = self.waypoints[self.current_wp_index]
                bearing, distance = self._compute_bearing_distance(
                    self.position[0], self.position[1], target_wp[0], target_wp[1]
                )

        self.output = [bearing, distance, float(self.current_wp_index)]

    def getOutput(self, port=0):
        if port < 3:
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output


class GreatCircleDistance(Block):
    """Compute great circle distance between two points.

    Inputs:
        - Port 0: Point 1 [lat, lon] in degrees
        - Port 1: Point 2 [lat, lon] in degrees

    Output: Distance in meters
    """

    def __init__(self):
        super().__init__()
        self.point1 = [0.0, 0.0]
        self.point2 = [0.0, 0.0]
        self.output = 0.0
        self.input_blocks = [None, None]

    def init(self):
        self.output = 0.0

    def setInput(self, value, port=0):
        if isinstance(value, list) and len(value) >= 2:
            if port == 0:
                self.point1 = value[:2]
            else:
                self.point2 = value[:2]

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block

    def update(self):
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                vec = block.getOutputVector()
                if vec is not None and len(vec) >= 2:
                    if i == 0:
                        self.point1 = vec[:2]
                    else:
                        self.point2 = vec[:2]

        lat1 = math.radians(self.point1[0])
        lon1 = math.radians(self.point1[1])
        lat2 = math.radians(self.point2[0])
        lon2 = math.radians(self.point2[1])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        self.output = WGS84_A * c

    def getOutput(self, port=0):
        return self.output


class FlatEarthPosition(Block):
    """Compute position using flat Earth approximation.

    Integrates velocity to get position in NED frame.

    Input: Velocity [Vn, Ve, Vd] in m/s
    Output: Position [N, E, D] in meters
    """

    def __init__(self, initial_position: list | None = None):
        super().__init__()
        self.initial_position = initial_position if initial_position else [0.0, 0.0, 0.0]
        self.velocity = [0.0, 0.0, 0.0]
        self.output = list(self.initial_position)
        self.input_block = None

        # Integrators for position
        self.n = self.addIntegrator([self.initial_position[0], 0.0])
        self.e = self.addIntegrator([self.initial_position[1], 0.0])
        self.d = self.addIntegrator([self.initial_position[2], 0.0])

    def init(self):
        self.n[0] = self.initial_position[0]
        self.n[1] = 0.0
        self.e[0] = self.initial_position[1]
        self.e[1] = 0.0
        self.d[0] = self.initial_position[2]
        self.d[1] = 0.0
        self.output = list(self.initial_position)

    def setInput(self, value, port=0):
        if isinstance(value, list) and len(value) >= 3:
            self.velocity = value[:3]

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            vec = self.input_block.getOutputVector()
            if vec is not None and len(vec) >= 3:
                self.velocity = vec[:3]

        # Set derivatives
        self.n[1] = self.velocity[0]
        self.e[1] = self.velocity[1]
        self.d[1] = self.velocity[2]

        self.output = [self.n[0], self.e[0], self.d[0]]

    def getOutput(self, port=0):
        if port < 3:
            return self.output[port]
        return 0.0

    def getOutputVector(self):
        return self.output
