"""C++ templates for aerospace blocks."""

from ....models import BlockInfo


def quaternion_normalize_template(block: BlockInfo, class_name: str) -> str:
    """Generate QuaternionNormalize block code."""
    return f"""
// {block.name} - Quaternion Normalize
#include <cmath>
#include <array>

class {class_name} {{
public:
    std::array<double, 4> input = {{1.0, 0.0, 0.0, 0.0}};  // [w, x, y, z]
    std::array<double, 4> output = {{1.0, 0.0, 0.0, 0.0}};

    void init() {{
        output = {{1.0, 0.0, 0.0, 0.0}};
    }}

    void update(double t) {{
        (void)t;
        double mag = std::sqrt(input[0]*input[0] + input[1]*input[1] +
                               input[2]*input[2] + input[3]*input[3]);
        if (mag > 1e-15) {{
            for (int i = 0; i < 4; i++) output[i] = input[i] / mag;
        }} else {{
            output = {{1.0, 0.0, 0.0, 0.0}};
        }}
    }}

    double get_output(int port = 0) const {{
        if (port >= 0 && port < 4) return output[port];
        return 0.0;
    }}

    const std::array<double, 4>& getOutputVector() const {{
        return output;
    }}
}};
"""


def quaternion_multiply_template(block: BlockInfo, class_name: str) -> str:
    """Generate QuaternionMultiply block code."""
    return f"""
// {block.name} - Quaternion Multiply (Hamilton product)
#include <array>

class {class_name} {{
public:
    std::array<double, 4> q1 = {{1.0, 0.0, 0.0, 0.0}};  // First quaternion
    std::array<double, 4> q2 = {{1.0, 0.0, 0.0, 0.0}};  // Second quaternion
    std::array<double, 4> output = {{1.0, 0.0, 0.0, 0.0}};
    double input = 0.0;

    void init() {{
        output = {{1.0, 0.0, 0.0, 0.0}};
    }}

    void update(double t) {{
        (void)t;
        double w1 = q1[0], x1 = q1[1], y1 = q1[2], z1 = q1[3];
        double w2 = q2[0], x2 = q2[1], y2 = q2[2], z2 = q2[3];

        output[0] = w1*w2 - x1*x2 - y1*y2 - z1*z2;
        output[1] = w1*x2 + x1*w2 + y1*z2 - z1*y2;
        output[2] = w1*y2 - x1*z2 + y1*w2 + z1*x2;
        output[3] = w1*z2 + x1*y2 - y1*x2 + z1*w2;
    }}

    double get_output(int port = 0) const {{
        if (port >= 0 && port < 4) return output[port];
        return 0.0;
    }}

    const std::array<double, 4>& getOutputVector() const {{
        return output;
    }}
}};
"""


def quaternion_conjugate_template(block: BlockInfo, class_name: str) -> str:
    """Generate QuaternionConjugate block code."""
    return f"""
// {block.name} - Quaternion Conjugate
#include <array>

class {class_name} {{
public:
    std::array<double, 4> input = {{1.0, 0.0, 0.0, 0.0}};  // [w, x, y, z]
    std::array<double, 4> output = {{1.0, 0.0, 0.0, 0.0}};

    void init() {{
        output = {{1.0, 0.0, 0.0, 0.0}};
    }}

    void update(double t) {{
        (void)t;
        output[0] = input[0];
        output[1] = -input[1];
        output[2] = -input[2];
        output[3] = -input[3];
    }}

    double get_output(int port = 0) const {{
        if (port >= 0 && port < 4) return output[port];
        return 0.0;
    }}

    const std::array<double, 4>& getOutputVector() const {{
        return output;
    }}
}};
"""


def quaternion_to_euler_template(block: BlockInfo, class_name: str) -> str:
    """Generate QuaternionToEuler block code."""
    return f"""
// {block.name} - Quaternion to Euler (ZYX rotation order)
#include <cmath>
#include <array>

class {class_name} {{
public:
    std::array<double, 4> input = {{1.0, 0.0, 0.0, 0.0}};  // [w, x, y, z]
    std::array<double, 3> output = {{0.0, 0.0, 0.0}};      // [roll, pitch, yaw]

    void init() {{
        output = {{0.0, 0.0, 0.0}};
    }}

    void update(double t) {{
        (void)t;
        double w = input[0], x = input[1], y = input[2], z = input[3];

        // Roll
        double sinr_cosp = 2.0 * (w * x + y * z);
        double cosr_cosp = 1.0 - 2.0 * (x * x + y * y);
        output[0] = std::atan2(sinr_cosp, cosr_cosp);

        // Pitch
        double sinp = 2.0 * (w * y - z * x);
        if (std::abs(sinp) >= 1.0) {{
            output[1] = std::copysign(M_PI / 2, sinp);
        }} else {{
            output[1] = std::asin(sinp);
        }}

        // Yaw
        double siny_cosp = 2.0 * (w * z + x * y);
        double cosy_cosp = 1.0 - 2.0 * (y * y + z * z);
        output[2] = std::atan2(siny_cosp, cosy_cosp);
    }}

    double get_output(int port = 0) const {{
        if (port >= 0 && port < 3) return output[port];
        return 0.0;
    }}

    const std::array<double, 3>& getOutputVector() const {{
        return output;
    }}
}};
"""


def euler_to_quaternion_template(block: BlockInfo, class_name: str) -> str:
    """Generate EulerToQuaternion block code."""
    return f"""
// {block.name} - Euler to Quaternion (ZYX rotation order)
#include <cmath>
#include <array>

class {class_name} {{
public:
    std::array<double, 3> input = {{0.0, 0.0, 0.0}};       // [roll, pitch, yaw]
    std::array<double, 4> output = {{1.0, 0.0, 0.0, 0.0}}; // [w, x, y, z]

    void init() {{
        output = {{1.0, 0.0, 0.0, 0.0}};
    }}

    void update(double t) {{
        (void)t;
        double roll = input[0], pitch = input[1], yaw = input[2];

        double cr = std::cos(roll * 0.5), sr = std::sin(roll * 0.5);
        double cp = std::cos(pitch * 0.5), sp = std::sin(pitch * 0.5);
        double cy = std::cos(yaw * 0.5), sy = std::sin(yaw * 0.5);

        output[0] = cr * cp * cy + sr * sp * sy;  // w
        output[1] = sr * cp * cy - cr * sp * sy;  // x
        output[2] = cr * sp * cy + sr * cp * sy;  // y
        output[3] = cr * cp * sy - sr * sp * cy;  // z
    }}

    double get_output(int port = 0) const {{
        if (port >= 0 && port < 4) return output[port];
        return 0.0;
    }}

    const std::array<double, 4>& getOutputVector() const {{
        return output;
    }}
}};
"""


def quaternion_rotate_vector_template(block: BlockInfo, class_name: str) -> str:
    """Generate QuaternionRotateVector block code."""
    return f"""
// {block.name} - Quaternion Rotate Vector
#include <array>

class {class_name} {{
public:
    // Input: quaternion (port 0) - use 'input' pointer for vector assignment
    std::array<double, 4> input = {{1.0, 0.0, 0.0, 0.0}};
    // Input: vector (port 1)
    std::array<double, 3> input1 = {{0.0, 0.0, 0.0}};
    std::array<double, 3> output = {{0.0, 0.0, 0.0}};

    void init() {{
        input = {{1.0, 0.0, 0.0, 0.0}};
        input1 = {{0.0, 0.0, 0.0}};
        output = {{0.0, 0.0, 0.0}};
    }}

    void update(double t) {{
        (void)t;
        double w = input[0], x = input[1];
        double y = input[2], z = input[3];
        double vx = input1[0], vy = input1[1], vz = input1[2];

        // q_v x v
        double cx1 = y * vz - z * vy;
        double cy1 = z * vx - x * vz;
        double cz1 = x * vy - y * vx;

        // q_v x (q_v x v)
        double cx2 = y * cz1 - z * cy1;
        double cy2 = z * cx1 - x * cz1;
        double cz2 = x * cy1 - y * cx1;

        output[0] = vx + 2.0 * (w * cx1 + cx2);
        output[1] = vy + 2.0 * (w * cy1 + cy2);
        output[2] = vz + 2.0 * (w * cz1 + cz2);
    }}

    double get_output(int port = 0) const {{
        if (port >= 0 && port < 3) return output[port];
        return 0.0;
    }}

    const std::array<double, 3>& getOutputVector() const {{
        return output;
    }}
}};
"""


def dcm_to_quaternion_template(block: BlockInfo, class_name: str) -> str:
    """Generate DCMToQuaternion block code."""
    return f"""
// {block.name} - DCM to Quaternion
#include <cmath>
#include <array>

class {class_name} {{
public:
    std::array<double, 9> input = {{1, 0, 0, 0, 1, 0, 0, 0, 1}};  // Identity DCM
    std::array<double, 4> output = {{1.0, 0.0, 0.0, 0.0}};

    void init() {{
        output = {{1.0, 0.0, 0.0, 0.0}};
    }}

    void update(double t) {{
        (void)t;
        double r11 = input[0], r12 = input[1], r13 = input[2];
        double r21 = input[3], r22 = input[4], r23 = input[5];
        double r31 = input[6], r32 = input[7], r33 = input[8];

        double trace = r11 + r22 + r33;
        double w, x, y, z, s;

        if (trace > 0) {{
            s = 0.5 / std::sqrt(trace + 1.0);
            w = 0.25 / s;
            x = (r32 - r23) * s;
            y = (r13 - r31) * s;
            z = (r21 - r12) * s;
        }} else if (r11 > r22 && r11 > r33) {{
            s = 2.0 * std::sqrt(1.0 + r11 - r22 - r33);
            w = (r32 - r23) / s;
            x = 0.25 * s;
            y = (r12 + r21) / s;
            z = (r13 + r31) / s;
        }} else if (r22 > r33) {{
            s = 2.0 * std::sqrt(1.0 + r22 - r11 - r33);
            w = (r13 - r31) / s;
            x = (r12 + r21) / s;
            y = 0.25 * s;
            z = (r23 + r32) / s;
        }} else {{
            s = 2.0 * std::sqrt(1.0 + r33 - r11 - r22);
            w = (r21 - r12) / s;
            x = (r13 + r31) / s;
            y = (r23 + r32) / s;
            z = 0.25 * s;
        }}

        output = {{w, x, y, z}};
    }}

    double get_output(int port = 0) const {{
        if (port >= 0 && port < 4) return output[port];
        return 0.0;
    }}

    const std::array<double, 4>& getOutputVector() const {{
        return output;
    }}
}};
"""


def quaternion_to_dcm_template(block: BlockInfo, class_name: str) -> str:
    """Generate QuaternionToDCM block code."""
    return f"""
// {block.name} - Quaternion to DCM
#include <array>

class {class_name} {{
public:
    std::array<double, 4> input = {{1.0, 0.0, 0.0, 0.0}};  // [w, x, y, z]
    std::array<double, 9> output = {{1, 0, 0, 0, 1, 0, 0, 0, 1}};  // Identity

    void init() {{
        output = {{1, 0, 0, 0, 1, 0, 0, 0, 1}};
    }}

    void update(double t) {{
        (void)t;
        double w = input[0], x = input[1], y = input[2], z = input[3];

        output[0] = 1 - 2*(y*y + z*z);
        output[1] = 2*(x*y - w*z);
        output[2] = 2*(x*z + w*y);
        output[3] = 2*(x*y + w*z);
        output[4] = 1 - 2*(x*x + z*z);
        output[5] = 2*(y*z - w*x);
        output[6] = 2*(x*z - w*y);
        output[7] = 2*(y*z + w*x);
        output[8] = 1 - 2*(x*x + y*y);
    }}

    double get_output(int port = 0) const {{
        if (port >= 0 && port < 9) return output[port];
        return 0.0;
    }}

    const std::array<double, 9>& getOutputVector() const {{
        return output;
    }}
}};
"""


def isa_atmosphere_template(block: BlockInfo, class_name: str) -> str:
    """Generate ISAAtmosphere block code."""
    return f"""
// {block.name} - ISA Atmosphere Model
#include <cmath>
#include <array>

class {class_name} {{
public:
    double input = 0.0;  // Altitude (m)
    std::array<double, 4> output = {{288.15, 101325.0, 1.225, 340.3}};

    // ISA constants
    static constexpr double T0 = 288.15;
    static constexpr double P0 = 101325.0;
    static constexpr double rho0 = 1.225;
    static constexpr double g = 9.80665;
    static constexpr double R = 287.05;
    static constexpr double gamma = 1.4;
    static constexpr double L = 0.0065;

    void init() {{
        output = {{T0, P0, rho0, 340.3}};
    }}

    void update(double t) {{
        (void)t;
        double h = input > 0 ? input : 0;
        double T, P;

        if (h <= 11000) {{
            T = T0 - L * h;
            P = P0 * std::pow(T / T0, g / (R * L));
        }} else {{
            double T11 = T0 - L * 11000;
            double P11 = P0 * std::pow(T11 / T0, g / (R * L));
            T = T11;
            P = P11 * std::exp(-g * (h - 11000) / (R * T11));
        }}

        double rho = P / (R * T);
        double a = std::sqrt(gamma * R * T);

        output = {{T, P, rho, a}};
    }}

    double get_output(int port = 0) const {{
        if (port >= 0 && port < 4) return output[port];
        return 0.0;
    }}

    const std::array<double, 4>& getOutputVector() const {{
        return output;
    }}
}};
"""


def flat_earth_gravity_template(block: BlockInfo, class_name: str) -> str:
    """Generate FlatEarthGravity block code."""
    g = block.parameters.get("g", 9.80665)
    return f"""
// {block.name} - Flat Earth Gravity
#include <array>

class {class_name} {{
public:
    double g_val = {g};
    std::array<double, 3> output = {{0.0, 0.0, {g}}};
    double input = 0.0;

    void init() {{
        output = {{0.0, 0.0, g_val}};
    }}

    void update(double t) {{
        (void)t;
        output = {{0.0, 0.0, g_val}};
    }}

    double get_output(int port = 0) const {{
        if (port >= 0 && port < 3) return output[port];
        return 0.0;
    }}

    const std::array<double, 3>& getOutputVector() const {{
        return output;
    }}
}};
"""


def wgs84_gravity_template(block: BlockInfo, class_name: str) -> str:
    """Generate WGS84Gravity block code."""
    return f"""
// {block.name} - WGS84 Gravity Model
#include <cmath>
#include <array>

class {class_name} {{
public:
    double input = 0.0;   // Latitude (rad) - port 0
    double input1 = 0.0;  // Altitude (m) - port 1
    double output = 9.80665;

    static constexpr double a = 6378137.0;
    static constexpr double ge = 9.7803253359;

    void init() {{
        output = 9.80665;
    }}

    void update(double t) {{
        (void)t;
        double lat = input, h = input1;
        double sin_lat2 = std::sin(lat) * std::sin(lat);

        double g0 = ge * (1 + 0.00193185265241 * sin_lat2) /
                    std::sqrt(1 - 0.00669437999014 * sin_lat2);

        output = g0 * (1 - 2 * h / a);
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output;
    }}

    double getOutputVector() const {{
        return output;
    }}
}};
"""


def six_dof_euler_template(block: BlockInfo, class_name: str) -> str:
    """Generate SixDOFEuler block code."""
    mass = block.parameters.get("mass", 1.0)
    ixx = block.parameters.get("Ixx", 1.0)
    iyy = block.parameters.get("Iyy", 1.0)
    izz = block.parameters.get("Izz", 1.0)
    ixz = block.parameters.get("Ixz", 0.0)
    return f"""
// {block.name} - 6-DOF Euler Equations of Motion
#include <cmath>
#include <array>

class {class_name} {{
public:
    double mass = {mass};
    double Ixx = {ixx}, Iyy = {iyy}, Izz = {izz}, Ixz = {ixz};

    std::array<double, 3> forces = {{0.0, 0.0, 0.0}};   // [Fx, Fy, Fz]
    std::array<double, 3> moments = {{0.0, 0.0, 0.0}};  // [L, M, N]
    double input = 0.0;

    // States [value, derivative]
    std::array<double, 2> u = {{0.0, 0.0}}, v = {{0.0, 0.0}}, w = {{0.0, 0.0}};
    std::array<double, 2> p = {{0.0, 0.0}}, q = {{0.0, 0.0}}, r = {{0.0, 0.0}};
    std::array<double, 2> phi = {{0.0, 0.0}}, theta = {{0.0, 0.0}}, psi = {{0.0, 0.0}};
    std::array<double, 2> xe = {{0.0, 0.0}}, ye = {{0.0, 0.0}}, ze = {{0.0, 0.0}};

    // RK4 intermediates
    std::array<double, 12> xd0 = {{}}, xd1 = {{}}, xd2 = {{}}, xd3 = {{}};

    std::array<double, 12> output = {{}};

    void init() {{
        u = v = w = {{0.0, 0.0}};
        p = q = r = {{0.0, 0.0}};
        phi = theta = psi = {{0.0, 0.0}};
        xe = ye = ze = {{0.0, 0.0}};
        output = {{}};
    }}

    void update(double t) {{
        (void)t;
        double Fx = forces[0], Fy = forces[1], Fz = forces[2];
        double L = moments[0], M = moments[1], N = moments[2];

        double u_ = u[0], v_ = v[0], w_ = w[0];
        double p_ = p[0], q_ = q[0], r_ = r[0];
        double phi_ = phi[0], theta_ = theta[0], psi_ = psi[0];

        // Force equations
        u[1] = Fx / mass - q_ * w_ + r_ * v_;
        v[1] = Fy / mass - r_ * u_ + p_ * w_;
        w[1] = Fz / mass - p_ * v_ + q_ * u_;

        // Moment equations
        double Gamma = Ixx * Izz - Ixz * Ixz;
        double c1 = ((Iyy - Izz) * Izz - Ixz * Ixz) / Gamma;
        double c2 = ((Ixx - Iyy + Izz) * Ixz) / Gamma;
        double c3 = Izz / Gamma;
        double c4 = Ixz / Gamma;
        double c5 = (Izz - Ixx) / Iyy;
        double c6 = Ixz / Iyy;
        double c7 = 1.0 / Iyy;
        double c8 = ((Ixx - Iyy) * Ixx + Ixz * Ixz) / Gamma;
        double c9 = Ixx / Gamma;

        p[1] = c1 * p_ * q_ + c2 * q_ * r_ + c3 * L + c4 * N;
        q[1] = c5 * p_ * r_ + c6 * (p_ * p_ - r_ * r_) + c7 * M;
        r[1] = c8 * p_ * q_ - c2 * q_ * r_ + c4 * L + c9 * N;

        // Kinematic equations
        double cos_phi = std::cos(phi_), sin_phi = std::sin(phi_);
        double cos_theta = std::cos(theta_);
        double tan_theta = std::abs(cos_theta) > 1e-10 ? std::tan(theta_) : 0.0;

        phi[1] = p_ + (q_ * sin_phi + r_ * cos_phi) * tan_theta;
        theta[1] = q_ * cos_phi - r_ * sin_phi;
        psi[1] = std::abs(cos_theta) > 1e-10 ? (q_ * sin_phi + r_ * cos_phi) / cos_theta : 0.0;

        // Navigation equations
        double cos_psi = std::cos(psi_), sin_psi = std::sin(psi_);
        double sin_theta = std::sin(theta_);

        xe[1] = (cos_theta * cos_psi) * u_ +
                (sin_phi * sin_theta * cos_psi - cos_phi * sin_psi) * v_ +
                (cos_phi * sin_theta * cos_psi + sin_phi * sin_psi) * w_;

        ye[1] = (cos_theta * sin_psi) * u_ +
                (sin_phi * sin_theta * sin_psi + cos_phi * cos_psi) * v_ +
                (cos_phi * sin_theta * sin_psi - sin_phi * cos_psi) * w_;

        ze[1] = (-sin_theta) * u_ + (sin_phi * cos_theta) * v_ + (cos_phi * cos_theta) * w_;

        output = {{u[0], v[0], w[0], p[0], q[0], r[0],
                  phi[0], theta[0], psi[0], xe[0], ye[0], ze[0]}};
    }}

    double get_output(int port = 0) const {{
        if (port >= 0 && port < 12) return output[port];
        return 0.0;
    }}

    const std::array<double, 12>& getOutputVector() const {{
        return output;
    }}
}};
"""


def lla_to_ecef_template(block: BlockInfo, class_name: str) -> str:
    """Generate LLA to ECEF conversion block code."""
    return f"""
// {block.name} - LLA to ECEF Conversion
#include <cmath>
#include <array>

class {class_name} {{
public:
    std::array<double, 3> input = {{0.0, 0.0, 0.0}};  // [lat, lon, alt] - port 0
    std::array<double, 3> output = {{0.0, 0.0, 0.0}}; // [X, Y, Z] ECEF

    // WGS84 constants
    static constexpr double a = 6378137.0;           // Semi-major axis
    static constexpr double f = 1.0 / 298.257223563; // Flattening
    static constexpr double e2 = 2*f - f*f;          // Eccentricity squared

    void init() {{
        input = {{0.0, 0.0, 0.0}};
        output = {{0.0, 0.0, 0.0}};
    }}

    void update(double t) {{
        (void)t;
        double lat = input[0], lon = input[1], alt = input[2];
        double sin_lat = std::sin(lat), cos_lat = std::cos(lat);
        double sin_lon = std::sin(lon), cos_lon = std::cos(lon);

        double N = a / std::sqrt(1.0 - e2 * sin_lat * sin_lat);

        output[0] = (N + alt) * cos_lat * cos_lon;
        output[1] = (N + alt) * cos_lat * sin_lon;
        output[2] = (N * (1.0 - e2) + alt) * sin_lat;
    }}

    double get_output(int port = 0) const {{
        if (port >= 0 && port < 3) return output[port];
        return 0.0;
    }}

    const std::array<double, 3>& getOutputVector() const {{
        return output;
    }}
}};
"""


def ecef_to_ned_template(block: BlockInfo, class_name: str) -> str:
    """Generate ECEF to NED conversion block code."""
    # Get reference point from parameters (in degrees, convert to radians)
    ref_lat_deg = block.parameters.get("referenceLat", 0.0)
    ref_lon_deg = block.parameters.get("referenceLon", 0.0)
    ref_alt = block.parameters.get("referenceAlt", 0.0)
    # Convert degrees to radians
    ref_lat_rad = ref_lat_deg * 3.14159265358979323846 / 180.0
    ref_lon_rad = ref_lon_deg * 3.14159265358979323846 / 180.0

    return f"""
// {block.name} - ECEF to NED Conversion
#include <cmath>
#include <array>

class {class_name} {{
public:
    // ECEF position vector (port 0) - 3 elements
    std::array<double, 3> input = {{0.0, 0.0, 0.0}};
    std::array<double, 3> output = {{0.0, 0.0, 0.0}};  // [N, E, D]

    // Reference point (from parameters, converted to radians)
    static constexpr double lat_ref = {ref_lat_rad};
    static constexpr double lon_ref = {ref_lon_rad};
    static constexpr double alt_ref = {ref_alt};

    // WGS84 constants
    static constexpr double a = 6378137.0;
    static constexpr double f = 1.0 / 298.257223563;
    static constexpr double e2 = 2*f - f*f;

    void init() {{
        input = {{0.0, 0.0, 0.0}};
        output = {{0.0, 0.0, 0.0}};
    }}

    void update(double t) {{
        (void)t;
        double sin_lat = std::sin(lat_ref), cos_lat = std::cos(lat_ref);
        double sin_lon = std::sin(lon_ref), cos_lon = std::cos(lon_ref);

        // Reference ECEF position
        double N_ref = a / std::sqrt(1.0 - e2 * sin_lat * sin_lat);
        double x_ref = (N_ref + alt_ref) * cos_lat * cos_lon;
        double y_ref = (N_ref + alt_ref) * cos_lat * sin_lon;
        double z_ref = (N_ref * (1.0 - e2) + alt_ref) * sin_lat;

        // Delta ECEF
        double dx = input[0] - x_ref;
        double dy = input[1] - y_ref;
        double dz = input[2] - z_ref;

        // Rotation matrix ECEF->NED
        output[0] = -sin_lat * cos_lon * dx - sin_lat * sin_lon * dy + cos_lat * dz;  // N
        output[1] = -sin_lon * dx + cos_lon * dy;  // E
        output[2] = -cos_lat * cos_lon * dx - cos_lat * sin_lon * dy - sin_lat * dz;  // D
    }}

    double get_output(int port = 0) const {{
        if (port >= 0 && port < 3) return output[port];
        return 0.0;
    }}

    const std::array<double, 3>& getOutputVector() const {{
        return output;
    }}
}};
"""


def great_circle_distance_template(block: BlockInfo, class_name: str) -> str:
    """Generate Great Circle Distance block code."""
    return f"""
// {block.name} - Great Circle Distance (Haversine)
#include <cmath>
#include <array>

class {class_name} {{
public:
    std::array<double, 2> input = {{0.0, 0.0}};   // [lat1, lon1] - point 1 (port 0)
    std::array<double, 2> input1 = {{0.0, 0.0}};  // [lat2, lon2] - point 2 (port 1)
    double output = 0.0;  // Distance (m)

    static constexpr double R = 6371000.0;  // Earth mean radius (m)

    void init() {{
        input = {{0.0, 0.0}};
        input1 = {{0.0, 0.0}};
        output = 0.0;
    }}

    void update(double t) {{
        (void)t;
        double lat1 = input[0], lon1 = input[1];
        double lat2 = input1[0], lon2 = input1[1];

        double dlat = lat2 - lat1;
        double dlon = lon2 - lon1;

        double a = std::sin(dlat / 2) * std::sin(dlat / 2) +
                   std::cos(lat1) * std::cos(lat2) *
                   std::sin(dlon / 2) * std::sin(dlon / 2);
        double c = 2 * std::atan2(std::sqrt(a), std::sqrt(1 - a));

        output = R * c;
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output;
    }}

    double getOutputVector() const {{
        return output;
    }}
}};
"""


def imu_sensor_template(block: BlockInfo, class_name: str) -> str:
    """Generate IMU sensor model block code."""
    accel_noise = block.parameters.get("accel_noise", 0.01)
    gyro_noise = block.parameters.get("gyro_noise", 0.001)
    accel_bias = block.parameters.get("accel_bias", 0.0)
    gyro_bias = block.parameters.get("gyro_bias", 0.0)
    return f"""
// {block.name} - IMU Sensor Model
#include <cmath>
#include <array>
#include <random>

class {class_name} {{
public:
    // Input: true acceleration (port 0) - 3 elements
    std::array<double, 3> input = {{0.0, 0.0, 0.0}};
    // Input: true angular rate (port 1) - 3 elements
    std::array<double, 3> input1 = {{0.0, 0.0, 0.0}};
    // Output: [ax, ay, az, gx, gy, gz] - measured with noise
    std::array<double, 6> output = {{0.0, 0.0, 0.0, 0.0, 0.0, 0.0}};

    double accel_noise = {accel_noise};
    double gyro_noise = {gyro_noise};
    double accel_bias = {accel_bias};
    double gyro_bias = {gyro_bias};

    std::mt19937 gen{{42}};
    std::normal_distribution<double> accel_dist{{0.0, accel_noise}};
    std::normal_distribution<double> gyro_dist{{0.0, gyro_noise}};

    void init() {{
        output = {{0.0, 0.0, 0.0, 0.0, 0.0, 0.0}};
    }}

    void update(double t) {{
        (void)t;
        // Add noise and bias to accelerometer
        for (int i = 0; i < 3; i++) {{
            output[i] = input[i] + accel_bias + accel_dist(gen);
        }}
        // Add noise and bias to gyroscope
        for (int i = 0; i < 3; i++) {{
            output[3 + i] = input1[i] + gyro_bias + gyro_dist(gen);
        }}
    }}

    double get_output(int port = 0) const {{
        if (port >= 0 && port < 6) return output[port];
        return 0.0;
    }}

    const std::array<double, 6>& getOutputVector() const {{
        return output;
    }}
}};
"""


def madgwick_filter_template(block: BlockInfo, class_name: str) -> str:
    """Generate Madgwick AHRS filter block code."""
    beta = block.parameters.get("beta", 0.1)
    return f"""
// {block.name} - Madgwick AHRS Filter
#include <cmath>
#include <array>

class {class_name} {{
public:
    // Input: gyroscope [gx, gy, gz] (rad/s) - port 0
    std::array<double, 3> input = {{0.0, 0.0, 0.0}};
    // Input: accelerometer [ax, ay, az] (m/s^2) - port 1
    std::array<double, 3> input1 = {{0.0, 0.0, 9.81}};
    // Output: quaternion [w, x, y, z]
    std::array<double, 4> output = {{1.0, 0.0, 0.0, 0.0}};

    double beta = {beta};  // Filter gain
    double q0 = 1.0, q1 = 0.0, q2 = 0.0, q3 = 0.0;  // Internal quaternion state
    double sample_period = 0.01;  // Default sample period

    void init() {{
        q0 = 1.0; q1 = 0.0; q2 = 0.0; q3 = 0.0;
        output = {{1.0, 0.0, 0.0, 0.0}};
    }}

    void update(double t) {{
        (void)t;
        double gx = input[0], gy = input[1], gz = input[2];
        double ax = input1[0], ay = input1[1], az = input1[2];

        // Normalize accelerometer
        double norm = std::sqrt(ax*ax + ay*ay + az*az);
        if (norm > 1e-10) {{
            ax /= norm; ay /= norm; az /= norm;
        }}

        // Gradient descent algorithm
        double f1 = 2.0*(q1*q3 - q0*q2) - ax;
        double f2 = 2.0*(q0*q1 + q2*q3) - ay;
        double f3 = 2.0*(0.5 - q1*q1 - q2*q2) - az;

        double J11 = -2.0*q2, J12 = 2.0*q3, J13 = -2.0*q0, J14 = 2.0*q1;
        double J21 = 2.0*q1, J22 = 2.0*q0, J23 = 2.0*q3, J24 = 2.0*q2;
        double J31 = 0.0, J32 = -4.0*q1, J33 = -4.0*q2, J34 = 0.0;

        double grad0 = J11*f1 + J21*f2 + J31*f3;
        double grad1 = J12*f1 + J22*f2 + J32*f3;
        double grad2 = J13*f1 + J23*f2 + J33*f3;
        double grad3 = J14*f1 + J24*f2 + J34*f3;

        norm = std::sqrt(grad0*grad0 + grad1*grad1 + grad2*grad2 + grad3*grad3);
        if (norm > 1e-10) {{
            grad0 /= norm; grad1 /= norm; grad2 /= norm; grad3 /= norm;
        }}

        // Quaternion rate from gyroscope
        double qDot0 = 0.5*(-q1*gx - q2*gy - q3*gz);
        double qDot1 = 0.5*(q0*gx + q2*gz - q3*gy);
        double qDot2 = 0.5*(q0*gy - q1*gz + q3*gx);
        double qDot3 = 0.5*(q0*gz + q1*gy - q2*gx);

        // Apply gradient descent correction
        qDot0 -= beta * grad0;
        qDot1 -= beta * grad1;
        qDot2 -= beta * grad2;
        qDot3 -= beta * grad3;

        // Integrate
        q0 += qDot0 * sample_period;
        q1 += qDot1 * sample_period;
        q2 += qDot2 * sample_period;
        q3 += qDot3 * sample_period;

        // Normalize quaternion
        norm = std::sqrt(q0*q0 + q1*q1 + q2*q2 + q3*q3);
        q0 /= norm; q1 /= norm; q2 /= norm; q3 /= norm;

        output = {{q0, q1, q2, q3}};
    }}

    double get_output(int port = 0) const {{
        if (port >= 0 && port < 4) return output[port];
        return 0.0;
    }}

    const std::array<double, 4>& getOutputVector() const {{
        return output;
    }}
}};
"""


def complementary_filter_template(block: BlockInfo, class_name: str) -> str:
    """Generate Complementary filter block code."""
    alpha = block.parameters.get("alpha", 0.98)
    return f"""
// {block.name} - Complementary Filter
#include <cmath>
#include <array>

class {class_name} {{
public:
    // Input: gyroscope [gx, gy, gz] (rad/s) - port 0
    std::array<double, 3> input = {{0.0, 0.0, 0.0}};
    // Input: accelerometer [ax, ay, az] (m/s^2) - port 1
    std::array<double, 3> input1 = {{0.0, 0.0, 9.81}};
    // Output: [roll, pitch, yaw] (rad)
    std::array<double, 3> output = {{0.0, 0.0, 0.0}};

    double alpha = {alpha};  // Filter coefficient (high = trust gyro more)
    double roll = 0.0, pitch = 0.0, yaw = 0.0;
    double sample_period = 0.01;

    void init() {{
        roll = 0.0; pitch = 0.0; yaw = 0.0;
        output = {{0.0, 0.0, 0.0}};
    }}

    void update(double t) {{
        (void)t;
        double gx = input[0], gy = input[1], gz = input[2];
        double ax = input1[0], ay = input1[1], az = input1[2];

        // Gyroscope integration
        roll += gx * sample_period;
        pitch += gy * sample_period;
        yaw += gz * sample_period;

        // Accelerometer angles
        double accel_roll = std::atan2(ay, az);
        double accel_pitch = std::atan2(-ax, std::sqrt(ay*ay + az*az));

        // Complementary filter
        roll = alpha * roll + (1.0 - alpha) * accel_roll;
        pitch = alpha * pitch + (1.0 - alpha) * accel_pitch;
        // Yaw has no accelerometer correction (needs magnetometer)

        output = {{roll, pitch, yaw}};
    }}

    double get_output(int port = 0) const {{
        if (port >= 0 && port < 3) return output[port];
        return 0.0;
    }}

    const std::array<double, 3>& getOutputVector() const {{
        return output;
    }}
}};
"""


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
    "lla_to_ecef": lla_to_ecef_template,
    "ecef_to_ned": ecef_to_ned_template,
    "great_circle_distance": great_circle_distance_template,
    "imu_sensor": imu_sensor_template,
    "madgwick_filter": madgwick_filter_template,
    "complementary_filter": complementary_filter_template,
}
