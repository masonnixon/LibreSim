"""Rust templates for aerospace blocks."""

from ....models import BlockInfo


def quaternion_normalize_template(block: BlockInfo, struct_name: str) -> str:
    """Generate QuaternionNormalize block code."""
    return f"""
/// {block.name} - Quaternion Normalize
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: [f64; 4],   // [w, x, y, z]
    pub output: [f64; 4],
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: [1.0, 0.0, 0.0, 0.0],
            output: [1.0, 0.0, 0.0, 0.0],
        }}
    }}

    pub fn init(&mut self) {{
        self.output = [1.0, 0.0, 0.0, 0.0];
    }}

    pub fn update(&mut self, _t: f64) {{
        let mag = (self.input[0].powi(2) + self.input[1].powi(2) +
                   self.input[2].powi(2) + self.input[3].powi(2)).sqrt();
        if mag > 1e-15 {{
            for i in 0..4 {{
                self.output[i] = self.input[i] / mag;
            }}
        }} else {{
            self.output = [1.0, 0.0, 0.0, 0.0];
        }}
    }}

    pub fn get_output(&self, port: i32) -> f64 {{
        if port >= 0 && port < 4 {{
            self.output[port as usize]
        }} else {{
            0.0
        }}
    }}

    pub fn get_output_vector(&self) -> &[f64; 4] {{
        &self.output
    }}
}}
"""


def quaternion_multiply_template(block: BlockInfo, struct_name: str) -> str:
    """Generate QuaternionMultiply block code."""
    return f"""
/// {block.name} - Quaternion Multiply (Hamilton product)
#[derive(Clone)]
pub struct {struct_name} {{
    pub q1: [f64; 4],      // First quaternion [w, x, y, z]
    pub q2: [f64; 4],      // Second quaternion
    pub output: [f64; 4],
    pub input: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            q1: [1.0, 0.0, 0.0, 0.0],
            q2: [1.0, 0.0, 0.0, 0.0],
            output: [1.0, 0.0, 0.0, 0.0],
            input: 0.0,
        }}
    }}

    pub fn init(&mut self) {{
        self.output = [1.0, 0.0, 0.0, 0.0];
    }}

    pub fn update(&mut self, _t: f64) {{
        let (w1, x1, y1, z1) = (self.q1[0], self.q1[1], self.q1[2], self.q1[3]);
        let (w2, x2, y2, z2) = (self.q2[0], self.q2[1], self.q2[2], self.q2[3]);

        self.output[0] = w1*w2 - x1*x2 - y1*y2 - z1*z2;
        self.output[1] = w1*x2 + x1*w2 + y1*z2 - z1*y2;
        self.output[2] = w1*y2 - x1*z2 + y1*w2 + z1*x2;
        self.output[3] = w1*z2 + x1*y2 - y1*x2 + z1*w2;
    }}

    pub fn get_output(&self, port: i32) -> f64 {{
        if port >= 0 && port < 4 {{
            self.output[port as usize]
        }} else {{
            0.0
        }}
    }}

    pub fn get_output_vector(&self) -> &[f64; 4] {{
        &self.output
    }}
}}
"""


def quaternion_conjugate_template(block: BlockInfo, struct_name: str) -> str:
    """Generate QuaternionConjugate block code."""
    return f"""
/// {block.name} - Quaternion Conjugate
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: [f64; 4],   // [w, x, y, z]
    pub output: [f64; 4],
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: [1.0, 0.0, 0.0, 0.0],
            output: [1.0, 0.0, 0.0, 0.0],
        }}
    }}

    pub fn init(&mut self) {{
        self.output = [1.0, 0.0, 0.0, 0.0];
    }}

    pub fn update(&mut self, _t: f64) {{
        self.output[0] = self.input[0];
        self.output[1] = -self.input[1];
        self.output[2] = -self.input[2];
        self.output[3] = -self.input[3];
    }}

    pub fn get_output(&self, port: i32) -> f64 {{
        if port >= 0 && port < 4 {{
            self.output[port as usize]
        }} else {{
            0.0
        }}
    }}

    pub fn get_output_vector(&self) -> &[f64; 4] {{
        &self.output
    }}
}}
"""


def quaternion_to_euler_template(block: BlockInfo, struct_name: str) -> str:
    """Generate QuaternionToEuler block code."""
    return f"""
/// {block.name} - Quaternion to Euler (ZYX rotation order)
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: [f64; 4],   // [w, x, y, z]
    pub output: [f64; 3],  // [roll, pitch, yaw]
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: [1.0, 0.0, 0.0, 0.0],
            output: [0.0, 0.0, 0.0],
        }}
    }}

    pub fn init(&mut self) {{
        self.output = [0.0, 0.0, 0.0];
    }}

    pub fn update(&mut self, _t: f64) {{
        let (w, x, y, z) = (self.input[0], self.input[1], self.input[2], self.input[3]);

        // Roll
        let sinr_cosp = 2.0 * (w * x + y * z);
        let cosr_cosp = 1.0 - 2.0 * (x * x + y * y);
        self.output[0] = sinr_cosp.atan2(cosr_cosp);

        // Pitch
        let sinp = 2.0 * (w * y - z * x);
        if sinp.abs() >= 1.0 {{
            self.output[1] = std::f64::consts::FRAC_PI_2.copysign(sinp);
        }} else {{
            self.output[1] = sinp.asin();
        }}

        // Yaw
        let siny_cosp = 2.0 * (w * z + x * y);
        let cosy_cosp = 1.0 - 2.0 * (y * y + z * z);
        self.output[2] = siny_cosp.atan2(cosy_cosp);
    }}

    pub fn get_output(&self, port: i32) -> f64 {{
        if port >= 0 && port < 3 {{
            self.output[port as usize]
        }} else {{
            0.0
        }}
    }}

    pub fn get_output_vector(&self) -> &[f64; 3] {{
        &self.output
    }}
}}
"""


def euler_to_quaternion_template(block: BlockInfo, struct_name: str) -> str:
    """Generate EulerToQuaternion block code."""
    return f"""
/// {block.name} - Euler to Quaternion (ZYX rotation order)
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: [f64; 3],   // [roll, pitch, yaw]
    pub output: [f64; 4],  // [w, x, y, z]
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: [0.0, 0.0, 0.0],
            output: [1.0, 0.0, 0.0, 0.0],
        }}
    }}

    pub fn init(&mut self) {{
        self.output = [1.0, 0.0, 0.0, 0.0];
    }}

    pub fn update(&mut self, _t: f64) {{
        let (roll, pitch, yaw) = (self.input[0], self.input[1], self.input[2]);

        let (cr, sr) = ((roll * 0.5).cos(), (roll * 0.5).sin());
        let (cp, sp) = ((pitch * 0.5).cos(), (pitch * 0.5).sin());
        let (cy, sy) = ((yaw * 0.5).cos(), (yaw * 0.5).sin());

        self.output[0] = cr * cp * cy + sr * sp * sy;  // w
        self.output[1] = sr * cp * cy - cr * sp * sy;  // x
        self.output[2] = cr * sp * cy + sr * cp * sy;  // y
        self.output[3] = cr * cp * sy - sr * sp * cy;  // z
    }}

    pub fn get_output(&self, port: i32) -> f64 {{
        if port >= 0 && port < 4 {{
            self.output[port as usize]
        }} else {{
            0.0
        }}
    }}

    pub fn get_output_vector(&self) -> &[f64; 4] {{
        &self.output
    }}
}}
"""


def quaternion_rotate_vector_template(block: BlockInfo, struct_name: str) -> str:
    """Generate QuaternionRotateVector block code."""
    return f"""
/// {block.name} - Quaternion Rotate Vector
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: [f64; 4],   // Quaternion [w, x, y, z] (port 0)
    pub input1: [f64; 3],  // Vector (port 1)
    pub output: [f64; 3],
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: [1.0, 0.0, 0.0, 0.0],
            input1: [0.0, 0.0, 0.0],
            output: [0.0, 0.0, 0.0],
        }}
    }}

    pub fn init(&mut self) {{
        self.input = [1.0, 0.0, 0.0, 0.0];
        self.input1 = [0.0, 0.0, 0.0];
        self.output = [0.0, 0.0, 0.0];
    }}

    pub fn update(&mut self, _t: f64) {{
        let (w, x, y, z) = (self.input[0], self.input[1],
                           self.input[2], self.input[3]);
        let (vx, vy, vz) = (self.input1[0], self.input1[1], self.input1[2]);

        // q_v x v
        let cx1 = y * vz - z * vy;
        let cy1 = z * vx - x * vz;
        let cz1 = x * vy - y * vx;

        // q_v x (q_v x v)
        let cx2 = y * cz1 - z * cy1;
        let cy2 = z * cx1 - x * cz1;
        let cz2 = x * cy1 - y * cx1;

        self.output[0] = vx + 2.0 * (w * cx1 + cx2);
        self.output[1] = vy + 2.0 * (w * cy1 + cy2);
        self.output[2] = vz + 2.0 * (w * cz1 + cz2);
    }}

    pub fn get_output(&self, port: i32) -> f64 {{
        if port >= 0 && port < 3 {{
            self.output[port as usize]
        }} else {{
            0.0
        }}
    }}

    pub fn get_output_vector(&self) -> &[f64; 3] {{
        &self.output
    }}
}}
"""


def dcm_to_quaternion_template(block: BlockInfo, struct_name: str) -> str:
    """Generate DCMToQuaternion block code."""
    return f"""
/// {block.name} - DCM to Quaternion
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: [f64; 9],   // 3x3 DCM row-major
    pub output: [f64; 4],  // [w, x, y, z]
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],  // Identity
            output: [1.0, 0.0, 0.0, 0.0],
        }}
    }}

    pub fn init(&mut self) {{
        self.output = [1.0, 0.0, 0.0, 0.0];
    }}

    pub fn update(&mut self, _t: f64) {{
        let (r11, r12, r13) = (self.input[0], self.input[1], self.input[2]);
        let (r21, r22, r23) = (self.input[3], self.input[4], self.input[5]);
        let (r31, r32, r33) = (self.input[6], self.input[7], self.input[8]);

        let trace = r11 + r22 + r33;
        let (w, x, y, z);

        if trace > 0.0 {{
            let s = 0.5 / (trace + 1.0).sqrt();
            w = 0.25 / s;
            x = (r32 - r23) * s;
            y = (r13 - r31) * s;
            z = (r21 - r12) * s;
        }} else if r11 > r22 && r11 > r33 {{
            let s = 2.0 * (1.0 + r11 - r22 - r33).sqrt();
            w = (r32 - r23) / s;
            x = 0.25 * s;
            y = (r12 + r21) / s;
            z = (r13 + r31) / s;
        }} else if r22 > r33 {{
            let s = 2.0 * (1.0 + r22 - r11 - r33).sqrt();
            w = (r13 - r31) / s;
            x = (r12 + r21) / s;
            y = 0.25 * s;
            z = (r23 + r32) / s;
        }} else {{
            let s = 2.0 * (1.0 + r33 - r11 - r22).sqrt();
            w = (r21 - r12) / s;
            x = (r13 + r31) / s;
            y = (r23 + r32) / s;
            z = 0.25 * s;
        }}

        self.output = [w, x, y, z];
    }}

    pub fn get_output(&self, port: i32) -> f64 {{
        if port >= 0 && port < 4 {{
            self.output[port as usize]
        }} else {{
            0.0
        }}
    }}

    pub fn get_output_vector(&self) -> &[f64; 4] {{
        &self.output
    }}
}}
"""


def quaternion_to_dcm_template(block: BlockInfo, struct_name: str) -> str:
    """Generate QuaternionToDCM block code."""
    return f"""
/// {block.name} - Quaternion to DCM
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: [f64; 4],   // [w, x, y, z]
    pub output: [f64; 9],  // 3x3 DCM row-major
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: [1.0, 0.0, 0.0, 0.0],
            output: [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],  // Identity
        }}
    }}

    pub fn init(&mut self) {{
        self.output = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0];
    }}

    pub fn update(&mut self, _t: f64) {{
        let (w, x, y, z) = (self.input[0], self.input[1], self.input[2], self.input[3]);

        self.output[0] = 1.0 - 2.0*(y*y + z*z);
        self.output[1] = 2.0*(x*y - w*z);
        self.output[2] = 2.0*(x*z + w*y);
        self.output[3] = 2.0*(x*y + w*z);
        self.output[4] = 1.0 - 2.0*(x*x + z*z);
        self.output[5] = 2.0*(y*z - w*x);
        self.output[6] = 2.0*(x*z - w*y);
        self.output[7] = 2.0*(y*z + w*x);
        self.output[8] = 1.0 - 2.0*(x*x + y*y);
    }}

    pub fn get_output(&self, port: i32) -> f64 {{
        if port >= 0 && port < 9 {{
            self.output[port as usize]
        }} else {{
            0.0
        }}
    }}

    pub fn get_output_vector(&self) -> &[f64; 9] {{
        &self.output
    }}
}}
"""


def isa_atmosphere_template(block: BlockInfo, struct_name: str) -> str:
    """Generate ISAAtmosphere block code."""
    return f"""
/// {block.name} - ISA Atmosphere Model
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: f64,        // Altitude (m)
    pub output: [f64; 4],  // [T, P, rho, a]
}}

impl {struct_name} {{
    const T0: f64 = 288.15;
    const P0: f64 = 101325.0;
    const RHO0: f64 = 1.225;
    const G: f64 = 9.80665;
    const R: f64 = 287.05;
    const GAMMA: f64 = 1.4;
    const L: f64 = 0.0065;

    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: [Self::T0, Self::P0, Self::RHO0, 340.3],
        }}
    }}

    pub fn init(&mut self) {{
        self.output = [Self::T0, Self::P0, Self::RHO0, 340.3];
    }}

    pub fn update(&mut self, _t: f64) {{
        let h = self.input.max(0.0);
        let (t, p);

        if h <= 11000.0 {{
            t = Self::T0 - Self::L * h;
            p = Self::P0 * (t / Self::T0).powf(Self::G / (Self::R * Self::L));
        }} else {{
            let t11 = Self::T0 - Self::L * 11000.0;
            let p11 = Self::P0 * (t11 / Self::T0).powf(Self::G / (Self::R * Self::L));
            t = t11;
            p = p11 * (-Self::G * (h - 11000.0) / (Self::R * t11)).exp();
        }}

        let rho = p / (Self::R * t);
        let a = (Self::GAMMA * Self::R * t).sqrt();

        self.output = [t, p, rho, a];
    }}

    pub fn get_output(&self, port: i32) -> f64 {{
        if port >= 0 && port < 4 {{
            self.output[port as usize]
        }} else {{
            0.0
        }}
    }}

    pub fn get_output_vector(&self) -> &[f64; 4] {{
        &self.output
    }}
}}
"""


def flat_earth_gravity_template(block: BlockInfo, struct_name: str) -> str:
    """Generate FlatEarthGravity block code."""
    g = block.parameters.get("g", 9.80665)
    return f"""
/// {block.name} - Flat Earth Gravity
#[derive(Clone)]
pub struct {struct_name} {{
    pub g: f64,
    pub output: [f64; 3],
    pub input: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            g: {g},
            output: [0.0, 0.0, {g}],
            input: 0.0,
        }}
    }}

    pub fn init(&mut self) {{
        self.output = [0.0, 0.0, self.g];
    }}

    pub fn update(&mut self, _t: f64) {{
        self.output = [0.0, 0.0, self.g];
    }}

    pub fn get_output(&self, port: i32) -> f64 {{
        if port >= 0 && port < 3 {{
            self.output[port as usize]
        }} else {{
            0.0
        }}
    }}

    pub fn get_output_vector(&self) -> &[f64; 3] {{
        &self.output
    }}
}}
"""


def wgs84_gravity_template(block: BlockInfo, struct_name: str) -> str:
    """Generate WGS84Gravity block code."""
    return f"""
/// {block.name} - WGS84 Gravity Model
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: f64,   // Latitude (rad) - port 0
    pub input1: f64,  // Altitude (m) - port 1
    pub output: f64,
}}

impl {struct_name} {{
    const A: f64 = 6378137.0;
    const GE: f64 = 9.7803253359;

    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            input1: 0.0,
            output: 9.80665,
        }}
    }}

    pub fn init(&mut self) {{
        self.output = 9.80665;
    }}

    pub fn update(&mut self, _t: f64) {{
        let lat = self.input;
        let h = self.input1;
        let sin_lat2 = lat.sin().powi(2);

        let g0 = Self::GE * (1.0 + 0.00193185265241 * sin_lat2) /
                 (1.0 - 0.00669437999014 * sin_lat2).sqrt();

        self.output = g0 * (1.0 - 2.0 * h / Self::A);
    }}

    pub fn get_output(&self, _port: i32) -> f64 {{
        self.output
    }}
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
/// {block.name} - 6-DOF Euler Equations of Motion
#[derive(Clone)]
pub struct {struct_name} {{
    pub mass: f64,
    pub ixx: f64,
    pub iyy: f64,
    pub izz: f64,
    pub ixz: f64,

    pub forces: [f64; 3],   // [Fx, Fy, Fz]
    pub moments: [f64; 3],  // [L, M, N]
    pub input: f64,

    // States [value, derivative]
    pub u: [f64; 2],
    pub v: [f64; 2],
    pub w: [f64; 2],
    pub p: [f64; 2],
    pub q: [f64; 2],
    pub r: [f64; 2],
    pub phi: [f64; 2],
    pub theta: [f64; 2],
    pub psi: [f64; 2],
    pub xe: [f64; 2],
    pub ye: [f64; 2],
    pub ze: [f64; 2],

    // RK4 intermediates
    pub xd0: [f64; 12],
    pub xd1: [f64; 12],
    pub xd2: [f64; 12],
    pub xd3: [f64; 12],

    pub output: [f64; 12],
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            mass: {mass},
            ixx: {ixx},
            iyy: {iyy},
            izz: {izz},
            ixz: {ixz},
            forces: [0.0; 3],
            moments: [0.0; 3],
            input: 0.0,
            u: [0.0; 2], v: [0.0; 2], w: [0.0; 2],
            p: [0.0; 2], q: [0.0; 2], r: [0.0; 2],
            phi: [0.0; 2], theta: [0.0; 2], psi: [0.0; 2],
            xe: [0.0; 2], ye: [0.0; 2], ze: [0.0; 2],
            xd0: [0.0; 12], xd1: [0.0; 12], xd2: [0.0; 12], xd3: [0.0; 12],
            output: [0.0; 12],
        }}
    }}

    pub fn init(&mut self) {{
        self.u = [0.0; 2]; self.v = [0.0; 2]; self.w = [0.0; 2];
        self.p = [0.0; 2]; self.q = [0.0; 2]; self.r = [0.0; 2];
        self.phi = [0.0; 2]; self.theta = [0.0; 2]; self.psi = [0.0; 2];
        self.xe = [0.0; 2]; self.ye = [0.0; 2]; self.ze = [0.0; 2];
        self.output = [0.0; 12];
    }}

    pub fn update(&mut self, _t: f64) {{
        let (fx, fy, fz) = (self.forces[0], self.forces[1], self.forces[2]);
        let (l, m, n) = (self.moments[0], self.moments[1], self.moments[2]);

        let (u_, v_, w_) = (self.u[0], self.v[0], self.w[0]);
        let (p_, q_, r_) = (self.p[0], self.q[0], self.r[0]);
        let (phi_, theta_, psi_) = (self.phi[0], self.theta[0], self.psi[0]);

        // Force equations
        self.u[1] = fx / self.mass - q_ * w_ + r_ * v_;
        self.v[1] = fy / self.mass - r_ * u_ + p_ * w_;
        self.w[1] = fz / self.mass - p_ * v_ + q_ * u_;

        // Moment equations
        let gamma = self.ixx * self.izz - self.ixz * self.ixz;
        let c1 = ((self.iyy - self.izz) * self.izz - self.ixz * self.ixz) / gamma;
        let c2 = ((self.ixx - self.iyy + self.izz) * self.ixz) / gamma;
        let c3 = self.izz / gamma;
        let c4 = self.ixz / gamma;
        let c5 = (self.izz - self.ixx) / self.iyy;
        let c6 = self.ixz / self.iyy;
        let c7 = 1.0 / self.iyy;
        let c8 = ((self.ixx - self.iyy) * self.ixx + self.ixz * self.ixz) / gamma;
        let c9 = self.ixx / gamma;

        self.p[1] = c1 * p_ * q_ + c2 * q_ * r_ + c3 * l + c4 * n;
        self.q[1] = c5 * p_ * r_ + c6 * (p_ * p_ - r_ * r_) + c7 * m;
        self.r[1] = c8 * p_ * q_ - c2 * q_ * r_ + c4 * l + c9 * n;

        // Kinematic equations
        let (cos_phi, sin_phi) = (phi_.cos(), phi_.sin());
        let cos_theta = theta_.cos();
        let tan_theta = if cos_theta.abs() > 1e-10 {{ theta_.tan() }} else {{ 0.0 }};

        self.phi[1] = p_ + (q_ * sin_phi + r_ * cos_phi) * tan_theta;
        self.theta[1] = q_ * cos_phi - r_ * sin_phi;
        self.psi[1] = if cos_theta.abs() > 1e-10 {{
            (q_ * sin_phi + r_ * cos_phi) / cos_theta
        }} else {{
            0.0
        }};

        // Navigation equations
        let (cos_psi, sin_psi) = (psi_.cos(), psi_.sin());
        let sin_theta = theta_.sin();

        self.xe[1] = (cos_theta * cos_psi) * u_ +
                     (sin_phi * sin_theta * cos_psi - cos_phi * sin_psi) * v_ +
                     (cos_phi * sin_theta * cos_psi + sin_phi * sin_psi) * w_;

        self.ye[1] = (cos_theta * sin_psi) * u_ +
                     (sin_phi * sin_theta * sin_psi + cos_phi * cos_psi) * v_ +
                     (cos_phi * sin_theta * sin_psi - sin_phi * cos_psi) * w_;

        self.ze[1] = (-sin_theta) * u_ + (sin_phi * cos_theta) * v_ + (cos_phi * cos_theta) * w_;

        self.output = [
            self.u[0], self.v[0], self.w[0],
            self.p[0], self.q[0], self.r[0],
            self.phi[0], self.theta[0], self.psi[0],
            self.xe[0], self.ye[0], self.ze[0],
        ];
    }}

    pub fn get_output(&self, port: i32) -> f64 {{
        if port >= 0 && port < 12 {{
            self.output[port as usize]
        }} else {{
            0.0
        }}
    }}

    pub fn get_output_vector(&self) -> &[f64; 12] {{
        &self.output
    }}
}}
"""


def lla_to_ecef_template(block: BlockInfo, struct_name: str) -> str:
    """Generate LLA to ECEF conversion block code."""
    return f"""
/// {block.name} - LLA to ECEF Conversion
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: [f64; 3],   // [lat, lon, alt] - port 0
    pub output: [f64; 3],  // [X, Y, Z] ECEF
}}

impl {struct_name} {{
    const A: f64 = 6378137.0;           // Semi-major axis
    const F: f64 = 1.0 / 298.257223563; // Flattening
    const E2: f64 = 2.0 * Self::F - Self::F * Self::F;  // Eccentricity squared

    pub fn new() -> Self {{
        Self {{
            input: [0.0, 0.0, 0.0],
            output: [0.0, 0.0, 0.0],
        }}
    }}

    pub fn init(&mut self) {{
        self.input = [0.0, 0.0, 0.0];
        self.output = [0.0, 0.0, 0.0];
    }}

    pub fn update(&mut self, _t: f64) {{
        let (lat, lon, alt) = (self.input[0], self.input[1], self.input[2]);
        let (sin_lat, cos_lat) = (lat.sin(), lat.cos());
        let (sin_lon, cos_lon) = (lon.sin(), lon.cos());

        let n = Self::A / (1.0 - Self::E2 * sin_lat * sin_lat).sqrt();

        self.output[0] = (n + alt) * cos_lat * cos_lon;
        self.output[1] = (n + alt) * cos_lat * sin_lon;
        self.output[2] = (n * (1.0 - Self::E2) + alt) * sin_lat;
    }}

    pub fn get_output(&self, port: i32) -> f64 {{
        if port >= 0 && port < 3 {{
            self.output[port as usize]
        }} else {{
            0.0
        }}
    }}

    pub fn get_output_vector(&self) -> &[f64; 3] {{
        &self.output
    }}
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
/// {block.name} - ECEF to NED Conversion
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: [f64; 3],  // ECEF position vector - port 0
    pub output: [f64; 3], // [N, E, D]
}}

impl {struct_name} {{
    const A: f64 = 6378137.0;
    const F: f64 = 1.0 / 298.257223563;
    const E2: f64 = 2.0 * Self::F - Self::F * Self::F;
    const LAT_REF: f64 = {ref_lat_rad}_f64;
    const LON_REF: f64 = {ref_lon_rad}_f64;
    const ALT_REF: f64 = {ref_alt}_f64;

    pub fn new() -> Self {{
        Self {{
            input: [0.0, 0.0, 0.0],
            output: [0.0, 0.0, 0.0],
        }}
    }}

    pub fn init(&mut self) {{
        self.input = [0.0, 0.0, 0.0];
        self.output = [0.0, 0.0, 0.0];
    }}

    pub fn update(&mut self, _t: f64) {{
        let (lat_ref, lon_ref, alt_ref) = (Self::LAT_REF, Self::LON_REF, Self::ALT_REF);
        let (sin_lat, cos_lat) = (lat_ref.sin(), lat_ref.cos());
        let (sin_lon, cos_lon) = (lon_ref.sin(), lon_ref.cos());

        // Reference ECEF position
        let n_ref = Self::A / (1.0 - Self::E2 * sin_lat * sin_lat).sqrt();
        let x_ref = (n_ref + alt_ref) * cos_lat * cos_lon;
        let y_ref = (n_ref + alt_ref) * cos_lat * sin_lon;
        let z_ref = (n_ref * (1.0 - Self::E2) + alt_ref) * sin_lat;

        // Delta ECEF
        let dx = self.input[0] - x_ref;
        let dy = self.input[1] - y_ref;
        let dz = self.input[2] - z_ref;

        // Rotation matrix ECEF->NED
        self.output[0] = -sin_lat * cos_lon * dx - sin_lat * sin_lon * dy + cos_lat * dz;  // N
        self.output[1] = -sin_lon * dx + cos_lon * dy;  // E
        self.output[2] = -cos_lat * cos_lon * dx - cos_lat * sin_lon * dy - sin_lat * dz;  // D
    }}

    pub fn get_output(&self, port: i32) -> f64 {{
        if port >= 0 && port < 3 {{
            self.output[port as usize]
        }} else {{
            0.0
        }}
    }}

    pub fn get_output_vector(&self) -> &[f64; 3] {{
        &self.output
    }}
}}
"""


def great_circle_distance_template(block: BlockInfo, struct_name: str) -> str:
    """Generate Great Circle Distance block code."""
    return f"""
/// {block.name} - Great Circle Distance (Haversine)
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: [f64; 2],   // [lat1, lon1] - point 1 (port 0)
    pub input1: [f64; 2],  // [lat2, lon2] - point 2 (port 1)
    pub output: f64,  // Distance (m)
}}

impl {struct_name} {{
    const R: f64 = 6371000.0;  // Earth mean radius (m)

    pub fn new() -> Self {{
        Self {{
            input: [0.0, 0.0],
            input1: [0.0, 0.0],
            output: 0.0,
        }}
    }}

    pub fn init(&mut self) {{
        self.input = [0.0, 0.0];
        self.input1 = [0.0, 0.0];
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        let (lat1, lon1) = (self.input[0], self.input[1]);
        let (lat2, lon2) = (self.input1[0], self.input1[1]);

        let dlat = lat2 - lat1;
        let dlon = lon2 - lon1;

        let a = (dlat / 2.0).sin().powi(2) +
                lat1.cos() * lat2.cos() * (dlon / 2.0).sin().powi(2);
        let c = 2.0 * a.sqrt().atan2((1.0 - a).sqrt());

        self.output = Self::R * c;
    }}

    pub fn get_output(&self, _port: i32) -> f64 {{
        self.output
    }}
}}
"""


def imu_sensor_template(block: BlockInfo, struct_name: str) -> str:
    """Generate IMU sensor model block code."""
    accel_noise = block.parameters.get("accel_noise", 0.01)
    gyro_noise = block.parameters.get("gyro_noise", 0.001)
    accel_bias = block.parameters.get("accel_bias", 0.0)
    gyro_bias = block.parameters.get("gyro_bias", 0.0)
    return f"""
/// {block.name} - IMU Sensor Model
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: [f64; 3],   // True acceleration (port 0)
    pub input1: [f64; 3],  // True angular rate (port 1)
    pub output: [f64; 6],  // [ax, ay, az, gx, gy, gz]
    pub accel_noise: f64,
    pub gyro_noise: f64,
    pub accel_bias: f64,
    pub gyro_bias: f64,
    seed: u64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: [0.0, 0.0, 0.0],
            input1: [0.0, 0.0, 0.0],
            output: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            accel_noise: {accel_noise},
            gyro_noise: {gyro_noise},
            accel_bias: {accel_bias},
            gyro_bias: {gyro_bias},
            seed: 42,
        }}
    }}

    fn randn(&mut self) -> f64 {{
        // Simple LCG for noise
        self.seed = self.seed.wrapping_mul(6364136223846793005).wrapping_add(1);
        let u1 = (self.seed as f64) / (u64::MAX as f64);
        self.seed = self.seed.wrapping_mul(6364136223846793005).wrapping_add(1);
        let u2 = (self.seed as f64) / (u64::MAX as f64);
        (-2.0 * u1.ln()).sqrt() * (2.0 * std::f64::consts::PI * u2).cos()
    }}

    pub fn init(&mut self) {{
        self.output = [0.0; 6];
    }}

    pub fn update(&mut self, _t: f64) {{
        for i in 0..3 {{
            self.output[i] = self.input[i] + self.accel_bias + self.accel_noise * self.randn();
        }}
        for i in 0..3 {{
            self.output[3 + i] = self.input1[i] + self.gyro_bias + self.gyro_noise * self.randn();
        }}
    }}

    pub fn get_output(&self, port: i32) -> f64 {{
        if port >= 0 && port < 6 {{
            self.output[port as usize]
        }} else {{
            0.0
        }}
    }}

    pub fn get_output_vector(&self) -> &[f64; 6] {{
        &self.output
    }}
}}
"""


def madgwick_filter_template(block: BlockInfo, struct_name: str) -> str:
    """Generate Madgwick AHRS filter block code."""
    beta = block.parameters.get("beta", 0.1)
    return f"""
/// {block.name} - Madgwick AHRS Filter
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: [f64; 3],   // Gyroscope [gx, gy, gz] (rad/s) - port 0
    pub input1: [f64; 3],  // Accelerometer [ax, ay, az] (m/s^2) - port 1
    pub output: [f64; 4],  // Quaternion [w, x, y, z]
    pub beta: f64,
    q0: f64, q1: f64, q2: f64, q3: f64,
    sample_period: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: [0.0, 0.0, 0.0],
            input1: [0.0, 0.0, 9.81],
            output: [1.0, 0.0, 0.0, 0.0],
            beta: {beta},
            q0: 1.0, q1: 0.0, q2: 0.0, q3: 0.0,
            sample_period: 0.01,
        }}
    }}

    pub fn init(&mut self) {{
        self.q0 = 1.0; self.q1 = 0.0; self.q2 = 0.0; self.q3 = 0.0;
        self.output = [1.0, 0.0, 0.0, 0.0];
    }}

    pub fn update(&mut self, _t: f64) {{
        let (gx, gy, gz) = (self.input[0], self.input[1], self.input[2]);
        let (mut ax, mut ay, mut az) = (self.input1[0], self.input1[1], self.input1[2]);

        let mut norm = (ax*ax + ay*ay + az*az).sqrt();
        if norm > 1e-10 {{
            ax /= norm; ay /= norm; az /= norm;
        }}

        let f1 = 2.0*(self.q1*self.q3 - self.q0*self.q2) - ax;
        let f2 = 2.0*(self.q0*self.q1 + self.q2*self.q3) - ay;
        let f3 = 2.0*(0.5 - self.q1*self.q1 - self.q2*self.q2) - az;

        let (j11, j12, j13, j14) = (-2.0*self.q2, 2.0*self.q3, -2.0*self.q0, 2.0*self.q1);
        let (j21, j22, j23, j24) = (2.0*self.q1, 2.0*self.q0, 2.0*self.q3, 2.0*self.q2);
        let (j32, j33) = (-4.0*self.q1, -4.0*self.q2);

        let mut grad0 = j11*f1 + j21*f2;
        let mut grad1 = j12*f1 + j22*f2 + j32*f3;
        let mut grad2 = j13*f1 + j23*f2 + j33*f3;
        let mut grad3 = j14*f1 + j24*f2;

        norm = (grad0*grad0 + grad1*grad1 + grad2*grad2 + grad3*grad3).sqrt();
        if norm > 1e-10 {{
            grad0 /= norm; grad1 /= norm; grad2 /= norm; grad3 /= norm;
        }}

        let q_dot0 = 0.5*(-self.q1*gx - self.q2*gy - self.q3*gz) - self.beta * grad0;
        let q_dot1 = 0.5*(self.q0*gx + self.q2*gz - self.q3*gy) - self.beta * grad1;
        let q_dot2 = 0.5*(self.q0*gy - self.q1*gz + self.q3*gx) - self.beta * grad2;
        let q_dot3 = 0.5*(self.q0*gz + self.q1*gy - self.q2*gx) - self.beta * grad3;

        self.q0 += q_dot0 * self.sample_period;
        self.q1 += q_dot1 * self.sample_period;
        self.q2 += q_dot2 * self.sample_period;
        self.q3 += q_dot3 * self.sample_period;

        norm = (self.q0*self.q0 + self.q1*self.q1 + self.q2*self.q2 + self.q3*self.q3).sqrt();
        self.q0 /= norm; self.q1 /= norm; self.q2 /= norm; self.q3 /= norm;

        self.output = [self.q0, self.q1, self.q2, self.q3];
    }}

    pub fn get_output(&self, port: i32) -> f64 {{
        if port >= 0 && port < 4 {{
            self.output[port as usize]
        }} else {{
            0.0
        }}
    }}

    pub fn get_output_vector(&self) -> &[f64; 4] {{
        &self.output
    }}
}}
"""


def complementary_filter_template(block: BlockInfo, struct_name: str) -> str:
    """Generate Complementary filter block code."""
    alpha = block.parameters.get("alpha", 0.98)
    return f"""
/// {block.name} - Complementary Filter
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: [f64; 3],   // Gyroscope [gx, gy, gz] (rad/s) - port 0
    pub input1: [f64; 3],  // Accelerometer [ax, ay, az] (m/s^2) - port 1
    pub output: [f64; 3],  // [roll, pitch, yaw] (rad)
    pub alpha: f64,
    roll: f64, pitch: f64, yaw: f64,
    sample_period: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: [0.0, 0.0, 0.0],
            input1: [0.0, 0.0, 9.81],
            output: [0.0, 0.0, 0.0],
            alpha: {alpha},
            roll: 0.0, pitch: 0.0, yaw: 0.0,
            sample_period: 0.01,
        }}
    }}

    pub fn init(&mut self) {{
        self.roll = 0.0; self.pitch = 0.0; self.yaw = 0.0;
        self.output = [0.0, 0.0, 0.0];
    }}

    pub fn update(&mut self, _t: f64) {{
        let (gx, gy, gz) = (self.input[0], self.input[1], self.input[2]);
        let (ax, ay, az) = (self.input1[0], self.input1[1], self.input1[2]);

        self.roll += gx * self.sample_period;
        self.pitch += gy * self.sample_period;
        self.yaw += gz * self.sample_period;

        let accel_roll = ay.atan2(az);
        let accel_pitch = (-ax).atan2((ay*ay + az*az).sqrt());

        self.roll = self.alpha * self.roll + (1.0 - self.alpha) * accel_roll;
        self.pitch = self.alpha * self.pitch + (1.0 - self.alpha) * accel_pitch;

        self.output = [self.roll, self.pitch, self.yaw];
    }}

    pub fn get_output(&self, port: i32) -> f64 {{
        if port >= 0 && port < 3 {{
            self.output[port as usize]
        }} else {{
            0.0
        }}
    }}

    pub fn get_output_vector(&self) -> &[f64; 3] {{
        &self.output
    }}
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
