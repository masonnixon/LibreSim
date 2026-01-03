"""Rust templates for control design blocks."""

from ....models import BlockInfo


def _format_f64(value) -> str:
    """Format a numeric value as a Rust f64 literal."""
    if isinstance(value, (int, float)):
        return f"{float(value)}"
    return str(value)


def pid_controller_template(block: BlockInfo, struct_name: str) -> str:
    """Generate PID controller block code."""
    kp = block.parameters.get("Kp", 1.0)
    ki = block.parameters.get("Ki", 1.0)
    kd = block.parameters.get("Kd", 0.0)
    n = block.parameters.get("N", 100.0)
    return f"""
/// {block.name} - PID Controller
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub kp: f64,
    pub ki: f64,
    pub kd: f64,
    pub n: f64,  // Derivative filter coefficient
    // Integrator state [value, derivative]
    pub integrator: [f64; 2],
    pub x0_int: f64,  // RK x0 storage for integrator
    pub xd0_int: f64,
    pub xd1_int: f64,
    pub xd2_int: f64,
    pub xd3_int: f64,
    // Derivative filter state
    pub deriv_state: [f64; 2],
    pub x0_der: f64,  // RK x0 storage for derivative filter
    pub xd0_der: f64,
    pub xd1_der: f64,
    pub xd2_der: f64,
    pub xd3_der: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: 0.0,
            kp: {_format_f64(kp)},
            ki: {_format_f64(ki)},
            kd: {_format_f64(kd)},
            n: {_format_f64(n)},
            integrator: [0.0, 0.0],
            x0_int: 0.0,
            xd0_int: 0.0,
            xd1_int: 0.0,
            xd2_int: 0.0,
            xd3_int: 0.0,
            deriv_state: [0.0, 0.0],
            x0_der: 0.0,
            xd0_der: 0.0,
            xd1_der: 0.0,
            xd2_der: 0.0,
            xd3_der: 0.0,
        }}
    }}

    pub fn init(&mut self) {{
        self.integrator = [0.0, 0.0];
        self.deriv_state = [0.0, 0.0];
        self.x0_int = 0.0;
        self.x0_der = 0.0;
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        let error = self.input;

        // P term
        let p_term = self.kp * error;

        // I term
        self.integrator[1] = error;
        let i_term = self.ki * self.integrator[0];

        // D term (filtered derivative)
        self.deriv_state[1] = self.n * (error - self.deriv_state[0]);
        let d_term = self.kd * self.deriv_state[1];

        self.output = p_term + i_term + d_term;
    }}

    pub fn get_output(&self, _port: i32) -> f64 {{
        self.output
    }}

    pub fn propagate_states(&mut self, dt: f64, kpass: usize, method: IntegrationMethod) {{
        // Capture derivatives first to avoid borrow conflicts
        let int_deriv = self.integrator[1];
        let der_deriv = self.deriv_state[1];

        // Propagate integrator state
        propagate_integrator(
            &mut self.integrator[0],
            &mut self.x0_int,
            &mut self.xd0_int,
            &mut self.xd1_int,
            &mut self.xd2_int,
            &mut self.xd3_int,
            int_deriv,
            dt, kpass, method,
        );
        // Propagate derivative filter state
        propagate_integrator(
            &mut self.deriv_state[0],
            &mut self.x0_der,
            &mut self.xd0_der,
            &mut self.xd1_der,
            &mut self.xd2_der,
            &mut self.xd3_der,
            der_deriv,
            dt, kpass, method,
        );
    }}
}}
"""


def pi_controller_template(block: BlockInfo, struct_name: str) -> str:
    """Generate PI controller block code."""
    kp = block.parameters.get("Kp", 1.0)
    ki = block.parameters.get("Ki", 1.0)
    initial = block.parameters.get("initial_integrator", 0.0)
    return f"""
/// {block.name} - PI Controller
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub kp: f64,
    pub ki: f64,
    pub initial_integrator: f64,
    // Integrator state [value, derivative]
    pub integrator: [f64; 2],
    pub xd0: f64,
    pub xd1: f64,
    pub xd2: f64,
    pub xd3: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: 0.0,
            kp: {_format_f64(kp)},
            ki: {_format_f64(ki)},
            initial_integrator: {_format_f64(initial)},
            integrator: [{_format_f64(initial)}, 0.0],
            xd0: 0.0,
            xd1: 0.0,
            xd2: 0.0,
            xd3: 0.0,
        }}
    }}

    pub fn init(&mut self) {{
        self.integrator = [self.initial_integrator, 0.0];
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        let error = self.input;
        self.integrator[1] = error;

        let p_term = self.kp * error;
        let i_term = self.ki * self.integrator[0];

        self.output = p_term + i_term;
    }}

    pub fn get_output(&self, _port: i32) -> f64 {{
        self.output
    }}
}}
"""


def pd_controller_template(block: BlockInfo, struct_name: str) -> str:
    """Generate PD controller block code."""
    kp = block.parameters.get("Kp", 1.0)
    kd = block.parameters.get("Kd", 1.0)
    n = block.parameters.get("N", 100.0)
    return f"""
/// {block.name} - PD Controller
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub kp: f64,
    pub kd: f64,
    pub n: f64,  // Derivative filter coefficient
    // Derivative filter state [value, derivative]
    pub deriv_state: [f64; 2],
    pub xd0: f64,
    pub xd1: f64,
    pub xd2: f64,
    pub xd3: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: 0.0,
            kp: {_format_f64(kp)},
            kd: {_format_f64(kd)},
            n: {_format_f64(n)},
            deriv_state: [0.0, 0.0],
            xd0: 0.0,
            xd1: 0.0,
            xd2: 0.0,
            xd3: 0.0,
        }}
    }}

    pub fn init(&mut self) {{
        self.deriv_state = [0.0, 0.0];
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        let error = self.input;

        // Filtered derivative
        self.deriv_state[1] = self.n * (error - self.deriv_state[0]);
        let d_term = self.kd * self.deriv_state[1];

        self.output = self.kp * error + d_term;
    }}

    pub fn get_output(&self, _port: i32) -> f64 {{
        self.output
    }}
}}
"""


def anti_windup_pid_template(block: BlockInfo, struct_name: str) -> str:
    """Generate Anti-windup PID controller block code."""
    kp = block.parameters.get("Kp", 1.0)
    ki = block.parameters.get("Ki", 1.0)
    kd = block.parameters.get("Kd", 0.0)
    n = block.parameters.get("N", 100.0)
    upper = block.parameters.get("upper_limit", None)
    lower = block.parameters.get("lower_limit", None)
    kb = block.parameters.get("Kb", 1.0)

    # Format limits - use f64::INFINITY if not specified
    upper_str = _format_f64(upper) if upper is not None else "f64::INFINITY"
    lower_str = _format_f64(lower) if lower is not None else "f64::NEG_INFINITY"

    return f"""
/// {block.name} - Anti-windup PID Controller
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub kp: f64,
    pub ki: f64,
    pub kd: f64,
    pub n: f64,
    pub upper_limit: f64,
    pub lower_limit: f64,
    pub kb: f64,  // Back-calculation gain
    // Integrator state
    pub integrator: [f64; 2],
    pub xd0_int: f64,
    pub xd1_int: f64,
    pub xd2_int: f64,
    pub xd3_int: f64,
    // Derivative filter state
    pub deriv_state: [f64; 2],
    pub xd0_der: f64,
    pub xd1_der: f64,
    pub xd2_der: f64,
    pub xd3_der: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: 0.0,
            kp: {_format_f64(kp)},
            ki: {_format_f64(ki)},
            kd: {_format_f64(kd)},
            n: {_format_f64(n)},
            upper_limit: {upper_str},
            lower_limit: {lower_str},
            kb: {_format_f64(kb)},
            integrator: [0.0, 0.0],
            xd0_int: 0.0,
            xd1_int: 0.0,
            xd2_int: 0.0,
            xd3_int: 0.0,
            deriv_state: [0.0, 0.0],
            xd0_der: 0.0,
            xd1_der: 0.0,
            xd2_der: 0.0,
            xd3_der: 0.0,
        }}
    }}

    pub fn init(&mut self) {{
        self.integrator = [0.0, 0.0];
        self.deriv_state = [0.0, 0.0];
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        let error = self.input;

        // P term
        let p_term = self.kp * error;

        // I term
        let i_term = self.ki * self.integrator[0];

        // D term (filtered)
        self.deriv_state[1] = self.n * (error - self.deriv_state[0]);
        let d_term = self.kd * self.deriv_state[1];

        // Unsaturated output
        let u_unsat = p_term + i_term + d_term;

        // Saturate output
        let u_sat = u_unsat.clamp(self.lower_limit, self.upper_limit);
        self.output = u_sat;

        // Back-calculation
        let saturation_error = u_sat - u_unsat;
        self.integrator[1] = error + self.kb * saturation_error;
    }}

    pub fn get_output(&self, _port: i32) -> f64 {{
        self.output
    }}
}}
"""


def lead_lag_compensator_template(block: BlockInfo, struct_name: str) -> str:
    """Generate Lead-Lag compensator block code."""
    gain = block.parameters.get("gain", 1.0)
    zero = block.parameters.get("zero", -1.0)
    pole = block.parameters.get("pole", -10.0)
    return f"""
/// {block.name} - Lead-Lag Compensator: K * (s + z) / (s + p)
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub gain: f64,
    pub zero: f64,
    pub pole: f64,
    // State [value, derivative]
    pub x: [f64; 2],
    pub xd0: f64,
    pub xd1: f64,
    pub xd2: f64,
    pub xd3: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: 0.0,
            gain: {_format_f64(gain)},
            zero: {_format_f64(zero)},
            pole: {_format_f64(pole)},
            x: [0.0, 0.0],
            xd0: 0.0,
            xd1: 0.0,
            xd2: 0.0,
            xd3: 0.0,
        }}
    }}

    pub fn init(&mut self) {{
        self.x = [0.0, 0.0];
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        // State equation: x' = -p*x + u
        self.x[1] = -self.pole * self.x[0] + self.input;
        // Output: y = K*(z-p)*x + K*u
        self.output = self.gain * (self.zero - self.pole) * self.x[0] + self.gain * self.input;
    }}

    pub fn get_output(&self, _port: i32) -> f64 {{
        self.output
    }}
}}
"""


def lqr_controller_template(block: BlockInfo, struct_name: str) -> str:
    """Generate LQR controller block code."""
    K = block.parameters.get("K", [[1.0]])
    num_states = block.parameters.get("num_states", 1)
    num_inputs = block.parameters.get("num_inputs", 1)

    # Helper to format values as Rust f64 literals
    def to_rust_float(val):
        s = str(val)
        if '.' not in s and 'e' not in s.lower():
            return s + ".0_f64"
        return s + "_f64"

    # Format K matrix initialization
    k_rows = []
    for i in range(num_inputs):
        row_vals = []
        for j in range(num_states):
            val = K[i][j] if i < len(K) and j < len(K[i]) else 0.0
            row_vals.append(to_rust_float(val))
        k_rows.append("[" + ", ".join(row_vals) + "]")
    k_init = "[" + ", ".join(k_rows) + "]"

    return f"""
/// {block.name} - LQR Controller: u = -K*x
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: [f64; {num_inputs}],
    pub state: [f64; {num_states}],
    pub k: [[f64; {num_states}]; {num_inputs}],
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: [0.0; {num_inputs}],
            state: [0.0; {num_states}],
            k: {k_init},
        }}
    }}

    pub fn init(&mut self) {{
        self.state = [0.0; {num_states}];
        self.output = [0.0; {num_inputs}];
    }}

    pub fn update(&mut self, _t: f64) {{
        // u = -K * x
        for i in 0..{num_inputs} {{
            let mut u = 0.0;
            for j in 0..{num_states} {{
                u -= self.k[i][j] * self.state[j];
            }}
            self.output[i] = u;
        }}
    }}

    pub fn get_output(&self, port: i32) -> f64 {{
        if port >= 0 && (port as usize) < {num_inputs} {{
            self.output[port as usize]
        }} else {{
            0.0
        }}
    }}
}}
"""


def pole_placement_template(block: BlockInfo, struct_name: str) -> str:
    """Generate Pole Placement controller block code."""
    K = block.parameters.get("K", [1.0])
    num_states = block.parameters.get("num_states", 1)

    # Format K vector initialization with _f64 suffix for Rust
    def to_rust_float(val):
        s = str(val)
        if '.' not in s and 'e' not in s.lower():
            return s + ".0_f64"
        return s + "_f64"
    k_vals = [to_rust_float(K[i]) if i < len(K) else "0.0_f64" for i in range(num_states)]
    k_init = "[" + ", ".join(k_vals) + "]"

    return f"""
/// {block.name} - Pole Placement Controller: u = -K*x
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub state: [f64; {num_states}],
    pub k: [f64; {num_states}],
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: 0.0,
            state: [0.0; {num_states}],
            k: {k_init},
        }}
    }}

    pub fn init(&mut self) {{
        self.state = [0.0; {num_states}];
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        // u = -K * x (SISO)
        let mut u = 0.0;
        for i in 0..{num_states} {{
            u -= self.k[i] * self.state[i];
        }}
        self.output = u;
    }}

    pub fn get_output(&self, _port: i32) -> f64 {{
        self.output
    }}
}}
"""


def model_reference_template(block: BlockInfo, struct_name: str) -> str:
    """Generate Model Reference block code."""
    wn = block.parameters.get("natural_frequency", 1.0)
    zeta = block.parameters.get("damping_ratio", 1.0)
    return f"""
/// {block.name} - Model Reference: wn^2 / (s^2 + 2*zeta*wn*s + wn^2)
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub wn: f64,
    pub zeta: f64,
    // States [value, derivative]
    pub x1: [f64; 2],
    pub x2: [f64; 2],
    pub xd0_1: f64,
    pub xd1_1: f64,
    pub xd2_1: f64,
    pub xd3_1: f64,
    pub xd0_2: f64,
    pub xd1_2: f64,
    pub xd2_2: f64,
    pub xd3_2: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: 0.0,
            wn: {_format_f64(wn)},
            zeta: {_format_f64(zeta)},
            x1: [0.0, 0.0],
            x2: [0.0, 0.0],
            xd0_1: 0.0,
            xd1_1: 0.0,
            xd2_1: 0.0,
            xd3_1: 0.0,
            xd0_2: 0.0,
            xd1_2: 0.0,
            xd2_2: 0.0,
            xd3_2: 0.0,
        }}
    }}

    pub fn init(&mut self) {{
        self.x1 = [0.0, 0.0];
        self.x2 = [0.0, 0.0];
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        let wn2 = self.wn * self.wn;

        self.x1[1] = self.x2[0];
        self.x2[1] = -wn2 * self.x1[0] - 2.0 * self.zeta * self.wn * self.x2[0] + wn2 * self.input;

        self.output = self.x1[0];
    }}

    pub fn get_output(&self, _port: i32) -> f64 {{
        self.output
    }}
}}
"""


# Template registry for control design blocks
CONTROL_DESIGN_TEMPLATES = {
    "pid_controller": pid_controller_template,
    "pi_controller": pi_controller_template,
    "pd_controller": pd_controller_template,
    "anti_windup_pid": anti_windup_pid_template,
    "lead_lag_compensator": lead_lag_compensator_template,
    "lqr_controller": lqr_controller_template,
    "pole_placement": pole_placement_template,
    "model_reference": model_reference_template,
}
