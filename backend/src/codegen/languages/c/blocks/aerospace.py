"""C templates for aerospace blocks."""

from ....models import BlockInfo


def quaternion_normalize_template(block: BlockInfo, struct_name: str) -> str:
    """Generate QuaternionNormalize block code."""
    return f"""
// {block.name} - Quaternion Normalize
#include <math.h>

typedef struct {{
    double input[4];   // [w, x, y, z]
    double output[4];
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input[0] = 1.0; b->input[1] = 0.0; b->input[2] = 0.0; b->input[3] = 0.0;
    b->output[0] = 1.0; b->output[1] = 0.0; b->output[2] = 0.0; b->output[3] = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    double mag = sqrt(b->input[0]*b->input[0] + b->input[1]*b->input[1] +
                      b->input[2]*b->input[2] + b->input[3]*b->input[3]);
    if (mag > 1e-15) {{
        for (int i = 0; i < 4; i++) b->output[i] = b->input[i] / mag;
    }} else {{
        b->output[0] = 1.0; b->output[1] = 0.0; b->output[2] = 0.0; b->output[3] = 0.0;
    }}
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    if (port >= 0 && port < 4) return b->output[port];
    return 0.0;
}}

static inline double* {struct_name}_get_output_vector({struct_name}* b) {{
    return b->output;
}}
"""


def quaternion_multiply_template(block: BlockInfo, struct_name: str) -> str:
    """Generate QuaternionMultiply block code."""
    return f"""
// {block.name} - Quaternion Multiply (Hamilton product)
typedef struct {{
    double q1[4];      // First quaternion [w, x, y, z]
    double q2[4];      // Second quaternion
    double output[4];
    double input;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->q1[0] = 1.0; b->q1[1] = 0.0; b->q1[2] = 0.0; b->q1[3] = 0.0;
    b->q2[0] = 1.0; b->q2[1] = 0.0; b->q2[2] = 0.0; b->q2[3] = 0.0;
    b->output[0] = 1.0; b->output[1] = 0.0; b->output[2] = 0.0; b->output[3] = 0.0;
    b->input = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    double w1 = b->q1[0], x1 = b->q1[1], y1 = b->q1[2], z1 = b->q1[3];
    double w2 = b->q2[0], x2 = b->q2[1], y2 = b->q2[2], z2 = b->q2[3];

    b->output[0] = w1*w2 - x1*x2 - y1*y2 - z1*z2;
    b->output[1] = w1*x2 + x1*w2 + y1*z2 - z1*y2;
    b->output[2] = w1*y2 - x1*z2 + y1*w2 + z1*x2;
    b->output[3] = w1*z2 + x1*y2 - y1*x2 + z1*w2;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    if (port >= 0 && port < 4) return b->output[port];
    return 0.0;
}}

static inline double* {struct_name}_get_output_vector({struct_name}* b) {{
    return b->output;
}}
"""


def quaternion_conjugate_template(block: BlockInfo, struct_name: str) -> str:
    """Generate QuaternionConjugate block code."""
    return f"""
// {block.name} - Quaternion Conjugate
typedef struct {{
    double input[4];   // [w, x, y, z]
    double output[4];
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input[0] = 1.0; b->input[1] = 0.0; b->input[2] = 0.0; b->input[3] = 0.0;
    b->output[0] = 1.0; b->output[1] = 0.0; b->output[2] = 0.0; b->output[3] = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    b->output[0] = b->input[0];
    b->output[1] = -b->input[1];
    b->output[2] = -b->input[2];
    b->output[3] = -b->input[3];
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    if (port >= 0 && port < 4) return b->output[port];
    return 0.0;
}}

static inline double* {struct_name}_get_output_vector({struct_name}* b) {{
    return b->output;
}}
"""


def quaternion_to_euler_template(block: BlockInfo, struct_name: str) -> str:
    """Generate QuaternionToEuler block code."""
    return f"""
// {block.name} - Quaternion to Euler (ZYX rotation order)
#include <math.h>

typedef struct {{
    double input[4];   // [w, x, y, z]
    double output[3];  // [roll, pitch, yaw]
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input[0] = 1.0; b->input[1] = 0.0; b->input[2] = 0.0; b->input[3] = 0.0;
    b->output[0] = 0.0; b->output[1] = 0.0; b->output[2] = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    double w = b->input[0], x = b->input[1], y = b->input[2], z = b->input[3];

    // Roll
    double sinr_cosp = 2.0 * (w * x + y * z);
    double cosr_cosp = 1.0 - 2.0 * (x * x + y * y);
    b->output[0] = atan2(sinr_cosp, cosr_cosp);

    // Pitch
    double sinp = 2.0 * (w * y - z * x);
    if (fabs(sinp) >= 1.0) {{
        b->output[1] = copysign(M_PI / 2, sinp);
    }} else {{
        b->output[1] = asin(sinp);
    }}

    // Yaw
    double siny_cosp = 2.0 * (w * z + x * y);
    double cosy_cosp = 1.0 - 2.0 * (y * y + z * z);
    b->output[2] = atan2(siny_cosp, cosy_cosp);
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    if (port >= 0 && port < 3) return b->output[port];
    return 0.0;
}}

static inline double* {struct_name}_get_output_vector({struct_name}* b) {{
    return b->output;
}}
"""


def euler_to_quaternion_template(block: BlockInfo, struct_name: str) -> str:
    """Generate EulerToQuaternion block code."""
    return f"""
// {block.name} - Euler to Quaternion (ZYX rotation order)
#include <math.h>

typedef struct {{
    double input[3];   // [roll, pitch, yaw]
    double output[4];  // [w, x, y, z]
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input[0] = 0.0; b->input[1] = 0.0; b->input[2] = 0.0;
    b->output[0] = 1.0; b->output[1] = 0.0; b->output[2] = 0.0; b->output[3] = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    double roll = b->input[0], pitch = b->input[1], yaw = b->input[2];

    double cr = cos(roll * 0.5), sr = sin(roll * 0.5);
    double cp = cos(pitch * 0.5), sp = sin(pitch * 0.5);
    double cy = cos(yaw * 0.5), sy = sin(yaw * 0.5);

    b->output[0] = cr * cp * cy + sr * sp * sy;  // w
    b->output[1] = sr * cp * cy - cr * sp * sy;  // x
    b->output[2] = cr * sp * cy + sr * cp * sy;  // y
    b->output[3] = cr * cp * sy - sr * sp * cy;  // z
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    if (port >= 0 && port < 4) return b->output[port];
    return 0.0;
}}

static inline double* {struct_name}_get_output_vector({struct_name}* b) {{
    return b->output;
}}
"""


def quaternion_rotate_vector_template(block: BlockInfo, struct_name: str) -> str:
    """Generate QuaternionRotateVector block code."""
    return f"""
// {block.name} - Quaternion Rotate Vector
typedef struct {{
    double input[4];   // Quaternion [w, x, y, z] (port 0)
    double input1[3];  // Vector (port 1)
    double output[3];
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input[0] = 1.0; b->input[1] = 0.0;
    b->input[2] = 0.0; b->input[3] = 0.0;
    b->input1[0] = 0.0; b->input1[1] = 0.0; b->input1[2] = 0.0;
    b->output[0] = 0.0; b->output[1] = 0.0; b->output[2] = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    double w = b->input[0], x = b->input[1];
    double y = b->input[2], z = b->input[3];
    double vx = b->input1[0], vy = b->input1[1], vz = b->input1[2];

    // q_v x v
    double cx1 = y * vz - z * vy;
    double cy1 = z * vx - x * vz;
    double cz1 = x * vy - y * vx;

    // q_v x (q_v x v)
    double cx2 = y * cz1 - z * cy1;
    double cy2 = z * cx1 - x * cz1;
    double cz2 = x * cy1 - y * cx1;

    b->output[0] = vx + 2.0 * (w * cx1 + cx2);
    b->output[1] = vy + 2.0 * (w * cy1 + cy2);
    b->output[2] = vz + 2.0 * (w * cz1 + cz2);
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    if (port >= 0 && port < 3) return b->output[port];
    return 0.0;
}}

static inline double* {struct_name}_get_output_vector({struct_name}* b) {{
    return b->output;
}}
"""


def dcm_to_quaternion_template(block: BlockInfo, struct_name: str) -> str:
    """Generate DCMToQuaternion block code."""
    return f"""
// {block.name} - DCM to Quaternion
#include <math.h>

typedef struct {{
    double input[9];   // 3x3 DCM row-major
    double output[4];  // [w, x, y, z]
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    // Identity DCM
    b->input[0] = 1; b->input[1] = 0; b->input[2] = 0;
    b->input[3] = 0; b->input[4] = 1; b->input[5] = 0;
    b->input[6] = 0; b->input[7] = 0; b->input[8] = 1;
    b->output[0] = 1.0; b->output[1] = 0.0; b->output[2] = 0.0; b->output[3] = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    double r11 = b->input[0], r12 = b->input[1], r13 = b->input[2];
    double r21 = b->input[3], r22 = b->input[4], r23 = b->input[5];
    double r31 = b->input[6], r32 = b->input[7], r33 = b->input[8];

    double trace = r11 + r22 + r33;
    double w, x, y, z, s;

    if (trace > 0) {{
        s = 0.5 / sqrt(trace + 1.0);
        w = 0.25 / s;
        x = (r32 - r23) * s;
        y = (r13 - r31) * s;
        z = (r21 - r12) * s;
    }} else if (r11 > r22 && r11 > r33) {{
        s = 2.0 * sqrt(1.0 + r11 - r22 - r33);
        w = (r32 - r23) / s;
        x = 0.25 * s;
        y = (r12 + r21) / s;
        z = (r13 + r31) / s;
    }} else if (r22 > r33) {{
        s = 2.0 * sqrt(1.0 + r22 - r11 - r33);
        w = (r13 - r31) / s;
        x = (r12 + r21) / s;
        y = 0.25 * s;
        z = (r23 + r32) / s;
    }} else {{
        s = 2.0 * sqrt(1.0 + r33 - r11 - r22);
        w = (r21 - r12) / s;
        x = (r13 + r31) / s;
        y = (r23 + r32) / s;
        z = 0.25 * s;
    }}

    b->output[0] = w; b->output[1] = x; b->output[2] = y; b->output[3] = z;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    if (port >= 0 && port < 4) return b->output[port];
    return 0.0;
}}

static inline double* {struct_name}_get_output_vector({struct_name}* b) {{
    return b->output;
}}
"""


def quaternion_to_dcm_template(block: BlockInfo, struct_name: str) -> str:
    """Generate QuaternionToDCM block code."""
    return f"""
// {block.name} - Quaternion to DCM
typedef struct {{
    double input[4];   // [w, x, y, z]
    double output[9];  // 3x3 DCM row-major
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input[0] = 1.0; b->input[1] = 0.0; b->input[2] = 0.0; b->input[3] = 0.0;
    // Identity DCM
    b->output[0] = 1; b->output[1] = 0; b->output[2] = 0;
    b->output[3] = 0; b->output[4] = 1; b->output[5] = 0;
    b->output[6] = 0; b->output[7] = 0; b->output[8] = 1;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    double w = b->input[0], x = b->input[1], y = b->input[2], z = b->input[3];

    b->output[0] = 1 - 2*(y*y + z*z);
    b->output[1] = 2*(x*y - w*z);
    b->output[2] = 2*(x*z + w*y);
    b->output[3] = 2*(x*y + w*z);
    b->output[4] = 1 - 2*(x*x + z*z);
    b->output[5] = 2*(y*z - w*x);
    b->output[6] = 2*(x*z - w*y);
    b->output[7] = 2*(y*z + w*x);
    b->output[8] = 1 - 2*(x*x + y*y);
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    if (port >= 0 && port < 9) return b->output[port];
    return 0.0;
}}

static inline double* {struct_name}_get_output_vector({struct_name}* b) {{
    return b->output;
}}
"""


def isa_atmosphere_template(block: BlockInfo, struct_name: str) -> str:
    """Generate ISAAtmosphere block code."""
    return f"""
// {block.name} - ISA Atmosphere Model
#include <math.h>

typedef struct {{
    double input;      // Altitude (m)
    double output[4];  // [T, P, rho, a]
    // ISA constants
    double T0, P0, rho0, g, R, gamma, L;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->T0 = 288.15;
    b->P0 = 101325.0;
    b->rho0 = 1.225;
    b->g = 9.80665;
    b->R = 287.05;
    b->gamma = 1.4;
    b->L = 0.0065;
    b->output[0] = b->T0;
    b->output[1] = b->P0;
    b->output[2] = b->rho0;
    b->output[3] = 340.3;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    double h = b->input > 0 ? b->input : 0;
    double T, P;

    if (h <= 11000) {{
        T = b->T0 - b->L * h;
        P = b->P0 * pow(T / b->T0, b->g / (b->R * b->L));
    }} else {{
        double T11 = b->T0 - b->L * 11000;
        double P11 = b->P0 * pow(T11 / b->T0, b->g / (b->R * b->L));
        T = T11;
        P = P11 * exp(-b->g * (h - 11000) / (b->R * T11));
    }}

    double rho = P / (b->R * T);
    double a = sqrt(b->gamma * b->R * T);

    b->output[0] = T;
    b->output[1] = P;
    b->output[2] = rho;
    b->output[3] = a;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    if (port >= 0 && port < 4) return b->output[port];
    return 0.0;
}}

static inline double* {struct_name}_get_output_vector({struct_name}* b) {{
    return b->output;
}}
"""


def flat_earth_gravity_template(block: BlockInfo, struct_name: str) -> str:
    """Generate FlatEarthGravity block code."""
    g = block.parameters.get("g", 9.80665)
    return f"""
// {block.name} - Flat Earth Gravity
typedef struct {{
    double g;
    double output[3];
    double input;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->g = {g};
    b->output[0] = 0.0;
    b->output[1] = 0.0;
    b->output[2] = {g};
    b->input = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    b->output[0] = 0.0;
    b->output[1] = 0.0;
    b->output[2] = b->g;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    if (port >= 0 && port < 3) return b->output[port];
    return 0.0;
}}

static inline double* {struct_name}_get_output_vector({struct_name}* b) {{
    return b->output;
}}
"""


def wgs84_gravity_template(block: BlockInfo, struct_name: str) -> str:
    """Generate WGS84Gravity block code."""
    return f"""
// {block.name} - WGS84 Gravity Model
#include <math.h>

typedef struct {{
    double input;   // Latitude (rad) - port 0
    double input1;  // Altitude (m) - port 1
    double output;
    double a, ge;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->input1 = 0.0;
    b->output = 9.80665;
    b->a = 6378137.0;
    b->ge = 9.7803253359;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    double lat = b->input, h = b->input1;
    double sin_lat2 = sin(lat) * sin(lat);

    double g0 = b->ge * (1 + 0.00193185265241 * sin_lat2) /
                sqrt(1 - 0.00669437999014 * sin_lat2);

    b->output = g0 * (1 - 2 * h / b->a);
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}

double {struct_name}_get_output_vector({struct_name}* b) {{
    return b->output;
}}
"""


def six_dof_euler_template(block: BlockInfo, struct_name: str) -> str:
    """Generate SixDOFEuler block code."""
    mass = block.parameters.get("mass", 1.0)
    ixx = block.parameters.get("Ixx", 1.0)
    iyy = block.parameters.get("Iyy", 1.0)
    izz = block.parameters.get("Izz", 1.0)
    ixz = block.parameters.get("Ixz", 0.0)
    return f"""
// {block.name} - 6-DOF Euler Equations of Motion
#include <math.h>

typedef struct {{
    double mass, Ixx, Iyy, Izz, Ixz;
    double forces[3];   // [Fx, Fy, Fz]
    double moments[3];  // [L, M, N]
    double input;

    // States [value, derivative]
    double u[2], v[2], w[2];      // Velocities
    double p[2], q[2], r[2];      // Angular rates
    double phi[2], theta[2], psi[2];  // Euler angles
    double xe[2], ye[2], ze[2];   // Position

    // RK4 intermediates
    double xd0[12], xd1[12], xd2[12], xd3[12];

    double output[12];
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->mass = {mass};
    b->Ixx = {ixx}; b->Iyy = {iyy}; b->Izz = {izz}; b->Ixz = {ixz};
    for (int i = 0; i < 3; i++) {{ b->forces[i] = 0.0; b->moments[i] = 0.0; }}
    b->u[0] = b->u[1] = 0.0; b->v[0] = b->v[1] = 0.0; b->w[0] = b->w[1] = 0.0;
    b->p[0] = b->p[1] = 0.0; b->q[0] = b->q[1] = 0.0; b->r[0] = b->r[1] = 0.0;
    b->phi[0] = b->phi[1] = 0.0; b->theta[0] = b->theta[1] = 0.0; b->psi[0] = b->psi[1] = 0.0;
    b->xe[0] = b->xe[1] = 0.0; b->ye[0] = b->ye[1] = 0.0; b->ze[0] = b->ze[1] = 0.0;
    for (int i = 0; i < 12; i++) {{
        b->output[i] = 0.0;
        b->xd0[i] = b->xd1[i] = b->xd2[i] = b->xd3[i] = 0.0;
    }}
    b->input = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    double Fx = b->forces[0], Fy = b->forces[1], Fz = b->forces[2];
    double L = b->moments[0], M = b->moments[1], N = b->moments[2];

    double u = b->u[0], v = b->v[0], w = b->w[0];
    double p = b->p[0], q = b->q[0], r = b->r[0];
    double phi = b->phi[0], theta = b->theta[0], psi = b->psi[0];

    // Force equations
    b->u[1] = Fx / b->mass - q * w + r * v;
    b->v[1] = Fy / b->mass - r * u + p * w;
    b->w[1] = Fz / b->mass - p * v + q * u;

    // Moment equations
    double Gamma = b->Ixx * b->Izz - b->Ixz * b->Ixz;
    double c1 = ((b->Iyy - b->Izz) * b->Izz - b->Ixz * b->Ixz) / Gamma;
    double c2 = ((b->Ixx - b->Iyy + b->Izz) * b->Ixz) / Gamma;
    double c3 = b->Izz / Gamma;
    double c4 = b->Ixz / Gamma;
    double c5 = (b->Izz - b->Ixx) / b->Iyy;
    double c6 = b->Ixz / b->Iyy;
    double c7 = 1.0 / b->Iyy;
    double c8 = ((b->Ixx - b->Iyy) * b->Ixx + b->Ixz * b->Ixz) / Gamma;
    double c9 = b->Ixx / Gamma;

    b->p[1] = c1 * p * q + c2 * q * r + c3 * L + c4 * N;
    b->q[1] = c5 * p * r + c6 * (p * p - r * r) + c7 * M;
    b->r[1] = c8 * p * q - c2 * q * r + c4 * L + c9 * N;

    // Kinematic equations
    double cos_phi = cos(phi), sin_phi = sin(phi);
    double cos_theta = cos(theta);
    double tan_theta = fabs(cos_theta) > 1e-10 ? tan(theta) : 0.0;

    b->phi[1] = p + (q * sin_phi + r * cos_phi) * tan_theta;
    b->theta[1] = q * cos_phi - r * sin_phi;
    b->psi[1] = fabs(cos_theta) > 1e-10 ? (q * sin_phi + r * cos_phi) / cos_theta : 0.0;

    // Navigation equations
    double cos_psi = cos(psi), sin_psi = sin(psi);
    double sin_theta = sin(theta);

    b->xe[1] = (cos_theta * cos_psi) * u +
               (sin_phi * sin_theta * cos_psi - cos_phi * sin_psi) * v +
               (cos_phi * sin_theta * cos_psi + sin_phi * sin_psi) * w;

    b->ye[1] = (cos_theta * sin_psi) * u +
               (sin_phi * sin_theta * sin_psi + cos_phi * cos_psi) * v +
               (cos_phi * sin_theta * sin_psi - sin_phi * cos_psi) * w;

    b->ze[1] = (-sin_theta) * u + (sin_phi * cos_theta) * v + (cos_phi * cos_theta) * w;

    // Update output
    b->output[0] = b->u[0]; b->output[1] = b->v[0]; b->output[2] = b->w[0];
    b->output[3] = b->p[0]; b->output[4] = b->q[0]; b->output[5] = b->r[0];
    b->output[6] = b->phi[0]; b->output[7] = b->theta[0]; b->output[8] = b->psi[0];
    b->output[9] = b->xe[0]; b->output[10] = b->ye[0]; b->output[11] = b->ze[0];
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    if (port >= 0 && port < 12) return b->output[port];
    return 0.0;
}}

static inline double* {struct_name}_get_output_vector({struct_name}* b) {{
    return b->output;
}}
"""


def lla_to_ecef_template(block: BlockInfo, struct_name: str) -> str:
    """Generate LLA to ECEF conversion block code."""
    return f"""
// {block.name} - LLA to ECEF Conversion
#include <math.h>

#define {struct_name.upper()}_A 6378137.0
#define {struct_name.upper()}_F (1.0 / 298.257223563)
#define {struct_name.upper()}_E2 (2*{struct_name.upper()}_F - {struct_name.upper()}_F*{struct_name.upper()}_F)

typedef struct {{
    double input[3];   // [lat, lon, alt] - port 0
    double output[3];  // [X, Y, Z] ECEF
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input[0] = 0.0;
    b->input[1] = 0.0;
    b->input[2] = 0.0;
    b->output[0] = 0.0;
    b->output[1] = 0.0;
    b->output[2] = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    double lat = b->input[0] * M_PI / 180.0;
    double lon = b->input[1] * M_PI / 180.0;
    double alt = b->input[2];
    double sin_lat = sin(lat), cos_lat = cos(lat);
    double sin_lon = sin(lon), cos_lon = cos(lon);

    double N = {struct_name.upper()}_A / sqrt(1.0 - {struct_name.upper()}_E2 * sin_lat * sin_lat);

    b->output[0] = (N + alt) * cos_lat * cos_lon;
    b->output[1] = (N + alt) * cos_lat * sin_lon;
    b->output[2] = (N * (1.0 - {struct_name.upper()}_E2) + alt) * sin_lat;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    if (port >= 0 && port < 3) return b->output[port];
    return 0.0;
}}

static inline double* {struct_name}_get_output_vector({struct_name}* b) {{
    return b->output;
}}
"""


def ecef_to_ned_template(block: BlockInfo, struct_name: str) -> str:
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
#include <math.h>

#define {struct_name.upper()}_A 6378137.0
#define {struct_name.upper()}_F (1.0 / 298.257223563)
#define {struct_name.upper()}_E2 (2*{struct_name.upper()}_F - {struct_name.upper()}_F*{struct_name.upper()}_F)
#define {struct_name.upper()}_LAT_REF {ref_lat_rad}
#define {struct_name.upper()}_LON_REF {ref_lon_rad}
#define {struct_name.upper()}_ALT_REF {ref_alt}

typedef struct {{
    double input[3];  // ECEF position vector - port 0
    double output[3]; // [N, E, D]
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input[0] = 0.0; b->input[1] = 0.0; b->input[2] = 0.0;
    b->output[0] = 0.0; b->output[1] = 0.0; b->output[2] = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    double lat_ref = {struct_name.upper()}_LAT_REF;
    double lon_ref = {struct_name.upper()}_LON_REF;
    double alt_ref = {struct_name.upper()}_ALT_REF;
    double sin_lat = sin(lat_ref), cos_lat = cos(lat_ref);
    double sin_lon = sin(lon_ref), cos_lon = cos(lon_ref);

    // Reference ECEF position
    double N_ref = {struct_name.upper()}_A / sqrt(1.0 - {struct_name.upper()}_E2 * sin_lat * sin_lat);
    double x_ref = (N_ref + alt_ref) * cos_lat * cos_lon;
    double y_ref = (N_ref + alt_ref) * cos_lat * sin_lon;
    double z_ref = (N_ref * (1.0 - {struct_name.upper()}_E2) + alt_ref) * sin_lat;

    // Delta ECEF
    double dx = b->input[0] - x_ref;
    double dy = b->input[1] - y_ref;
    double dz = b->input[2] - z_ref;

    // Rotation matrix ECEF->NED
    b->output[0] = -sin_lat * cos_lon * dx - sin_lat * sin_lon * dy + cos_lat * dz;  // N
    b->output[1] = -sin_lon * dx + cos_lon * dy;  // E
    b->output[2] = -cos_lat * cos_lon * dx - cos_lat * sin_lon * dy - sin_lat * dz;  // D
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    if (port >= 0 && port < 3) return b->output[port];
    return 0.0;
}}

static inline double* {struct_name}_get_output_vector({struct_name}* b) {{
    return b->output;
}}
"""


def great_circle_distance_template(block: BlockInfo, struct_name: str) -> str:
    """Generate Great Circle Distance block code."""
    return f"""
// {block.name} - Great Circle Distance (Haversine)
#include <math.h>

#define {struct_name.upper()}_R 6378137.0

typedef struct {{
    double input[2];   // [lat1, lon1] - point 1 (port 0)
    double input1[2];  // [lat2, lon2] - point 2 (port 1)
    double output;  // Distance (m)
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input[0] = 0.0;
    b->input[1] = 0.0;
    b->input1[0] = 0.0;
    b->input1[1] = 0.0;
    b->output = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    double lat1 = b->input[0] * M_PI / 180.0;
    double lon1 = b->input[1] * M_PI / 180.0;
    double lat2 = b->input1[0] * M_PI / 180.0;
    double lon2 = b->input1[1] * M_PI / 180.0;

    double dlat = lat2 - lat1;
    double dlon = lon2 - lon1;

    double a = sin(dlat / 2) * sin(dlat / 2) +
               cos(lat1) * cos(lat2) *
               sin(dlon / 2) * sin(dlon / 2);
    double c = 2 * atan2(sqrt(a), sqrt(1 - a));

    b->output = {struct_name.upper()}_R * c;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}

double {struct_name}_get_output_vector({struct_name}* b) {{
    return b->output;
}}
"""


def imu_sensor_template(block: BlockInfo, struct_name: str) -> str:
    """Generate IMU sensor model block code."""
    accel_noise = block.parameters.get("accel_noise", 0.01)
    gyro_noise = block.parameters.get("gyro_noise", 0.001)
    accel_bias = block.parameters.get("accel_bias", 0.0)
    gyro_bias = block.parameters.get("gyro_bias", 0.0)
    return f"""
// {block.name} - IMU Sensor Model
#include <math.h>
#include <stdlib.h>

typedef struct {{
    double input[3];   // True acceleration (port 0)
    double input1[3];  // True angular rate (port 1)
    double output[6];  // [ax, ay, az, gx, gy, gz]
    double accel_noise, gyro_noise, accel_bias, gyro_bias;
}} {struct_name};

static double {struct_name}_randn(void) {{
    // Box-Muller transform for Gaussian noise
    double u1 = ((double)rand() + 1.0) / ((double)RAND_MAX + 2.0);
    double u2 = ((double)rand() + 1.0) / ((double)RAND_MAX + 2.0);
    return sqrt(-2.0 * log(u1)) * cos(2.0 * M_PI * u2);
}}

void {struct_name}_init({struct_name}* b) {{
    for (int i = 0; i < 3; i++) {{ b->input[i] = 0.0; b->input1[i] = 0.0; }}
    for (int i = 0; i < 6; i++) b->output[i] = 0.0;
    b->accel_noise = {accel_noise};
    b->gyro_noise = {gyro_noise};
    b->accel_bias = {accel_bias};
    b->gyro_bias = {gyro_bias};
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    for (int i = 0; i < 3; i++) {{
        b->output[i] = b->input[i] + b->accel_bias + b->accel_noise * {struct_name}_randn();
    }}
    for (int i = 0; i < 3; i++) {{
        b->output[3 + i] = b->input1[i] + b->gyro_bias + b->gyro_noise * {struct_name}_randn();
    }}
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    if (port >= 0 && port < 6) return b->output[port];
    return 0.0;
}}

static inline double* {struct_name}_get_output_vector({struct_name}* b) {{
    return b->output;
}}
"""


def madgwick_filter_template(block: BlockInfo, struct_name: str) -> str:
    """Generate Madgwick AHRS filter block code."""
    beta = block.parameters.get("beta", 0.1)
    return f"""
// {block.name} - Madgwick AHRS Filter
#include <math.h>

typedef struct {{
    double input[3];   // Gyroscope [gx, gy, gz] (rad/s) - port 0
    double input1[3];  // Accelerometer [ax, ay, az] (m/s^2) - port 1
    double output[4];  // Quaternion [w, x, y, z]
    double beta;
    double q0, q1, q2, q3;  // Internal quaternion state
    double sample_period;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    for (int i = 0; i < 3; i++) {{ b->input[i] = 0.0; }}
    b->input1[0] = 0.0; b->input1[1] = 0.0; b->input1[2] = 9.81;
    b->output[0] = 1.0; b->output[1] = 0.0; b->output[2] = 0.0; b->output[3] = 0.0;
    b->beta = {beta};
    b->q0 = 1.0; b->q1 = 0.0; b->q2 = 0.0; b->q3 = 0.0;
    b->sample_period = 0.01;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    double gx = b->input[0], gy = b->input[1], gz = b->input[2];
    double ax = b->input1[0], ay = b->input1[1], az = b->input1[2];

    double norm = sqrt(ax*ax + ay*ay + az*az);
    if (norm > 1e-10) {{ ax /= norm; ay /= norm; az /= norm; }}

    double f1 = 2.0*(b->q1*b->q3 - b->q0*b->q2) - ax;
    double f2 = 2.0*(b->q0*b->q1 + b->q2*b->q3) - ay;
    double f3 = 2.0*(0.5 - b->q1*b->q1 - b->q2*b->q2) - az;

    double J11 = -2.0*b->q2, J12 = 2.0*b->q3, J13 = -2.0*b->q0, J14 = 2.0*b->q1;
    double J21 = 2.0*b->q1, J22 = 2.0*b->q0, J23 = 2.0*b->q3, J24 = 2.0*b->q2;
    double J32 = -4.0*b->q1, J33 = -4.0*b->q2;

    double grad0 = J11*f1 + J21*f2;
    double grad1 = J12*f1 + J22*f2 + J32*f3;
    double grad2 = J13*f1 + J23*f2 + J33*f3;
    double grad3 = J14*f1 + J24*f2;

    norm = sqrt(grad0*grad0 + grad1*grad1 + grad2*grad2 + grad3*grad3);
    if (norm > 1e-10) {{ grad0 /= norm; grad1 /= norm; grad2 /= norm; grad3 /= norm; }}

    double qDot0 = 0.5*(-b->q1*gx - b->q2*gy - b->q3*gz) - b->beta * grad0;
    double qDot1 = 0.5*(b->q0*gx + b->q2*gz - b->q3*gy) - b->beta * grad1;
    double qDot2 = 0.5*(b->q0*gy - b->q1*gz + b->q3*gx) - b->beta * grad2;
    double qDot3 = 0.5*(b->q0*gz + b->q1*gy - b->q2*gx) - b->beta * grad3;

    b->q0 += qDot0 * b->sample_period;
    b->q1 += qDot1 * b->sample_period;
    b->q2 += qDot2 * b->sample_period;
    b->q3 += qDot3 * b->sample_period;

    norm = sqrt(b->q0*b->q0 + b->q1*b->q1 + b->q2*b->q2 + b->q3*b->q3);
    b->q0 /= norm; b->q1 /= norm; b->q2 /= norm; b->q3 /= norm;

    b->output[0] = b->q0; b->output[1] = b->q1; b->output[2] = b->q2; b->output[3] = b->q3;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    if (port >= 0 && port < 4) return b->output[port];
    return 0.0;
}}

static inline double* {struct_name}_get_output_vector({struct_name}* b) {{
    return b->output;
}}
"""


def complementary_filter_template(block: BlockInfo, struct_name: str) -> str:
    """Generate Complementary filter block code."""
    alpha = block.parameters.get("alpha", 0.98)
    return f"""
// {block.name} - Complementary Filter
#include <math.h>

typedef struct {{
    double input[3];   // Gyroscope [gx, gy, gz] (rad/s) - port 0
    double input1[3];  // Accelerometer [ax, ay, az] (m/s^2) - port 1
    double output[3];  // [roll, pitch, yaw] (rad)
    double alpha;
    double roll, pitch, yaw;
    double sample_period;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    for (int i = 0; i < 3; i++) {{ b->input[i] = 0.0; b->output[i] = 0.0; }}
    b->input1[0] = 0.0; b->input1[1] = 0.0; b->input1[2] = 9.81;
    b->alpha = {alpha};
    b->roll = 0.0; b->pitch = 0.0; b->yaw = 0.0;
    b->sample_period = 0.01;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    double gx = b->input[0], gy = b->input[1], gz = b->input[2];
    double ax = b->input1[0], ay = b->input1[1], az = b->input1[2];

    b->roll += gx * b->sample_period;
    b->pitch += gy * b->sample_period;
    b->yaw += gz * b->sample_period;

    double accel_roll = atan2(ay, az);
    double accel_pitch = atan2(-ax, sqrt(ay*ay + az*az));

    b->roll = b->alpha * b->roll + (1.0 - b->alpha) * accel_roll;
    b->pitch = b->alpha * b->pitch + (1.0 - b->alpha) * accel_pitch;

    b->output[0] = b->roll; b->output[1] = b->pitch; b->output[2] = b->yaw;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    if (port >= 0 && port < 3) return b->output[port];
    return 0.0;
}}

static inline double* {struct_name}_get_output_vector({struct_name}* b) {{
    return b->output;
}}
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
