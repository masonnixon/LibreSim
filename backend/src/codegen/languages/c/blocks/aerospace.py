"""C templates for aerospace blocks."""

import math
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
    double quaternion[4];  // [w, x, y, z]
    double vector[3];
    double output[3];
    double input;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->quaternion[0] = 1.0; b->quaternion[1] = 0.0;
    b->quaternion[2] = 0.0; b->quaternion[3] = 0.0;
    b->vector[0] = 0.0; b->vector[1] = 0.0; b->vector[2] = 0.0;
    b->output[0] = 0.0; b->output[1] = 0.0; b->output[2] = 0.0;
    b->input = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    double w = b->quaternion[0], x = b->quaternion[1];
    double y = b->quaternion[2], z = b->quaternion[3];
    double vx = b->vector[0], vy = b->vector[1], vz = b->vector[2];

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
    double input[2];  // [latitude, altitude]
    double output;
    double a, ge;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input[0] = 0.0;
    b->input[1] = 0.0;
    b->output = 9.80665;
    b->a = 6378137.0;
    b->ge = 9.7803253359;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    double lat = b->input[0], h = b->input[1];
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
