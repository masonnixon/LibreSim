"""Rust block templates for continuous blocks (integrators, transfer functions, etc.)."""

from ....models import BlockInfo


def template_integrator(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Integrator block."""
    initial_condition = block.parameters.get("initial_condition", 0.0)
    return f"""
/// {block.name} - Integrator
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub state: f64,
    pub initial_condition: f64,
    // Integration intermediate values
    pub xd0: f64,
    pub xd1: f64,
    pub xd2: f64,
    pub xd3: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            initial_condition: {initial_condition}_f64,
            state: {initial_condition}_f64,
            output: {initial_condition}_f64,
            xd0: 0.0,
            xd1: 0.0,
            xd2: 0.0,
            xd3: 0.0,
        }}
    }}

    pub fn init(&mut self) {{
        self.state = self.initial_condition;
        self.output = self.state;
        self.xd0 = 0.0;
        self.xd1 = 0.0;
        self.xd2 = 0.0;
        self.xd3 = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        self.output = self.state;
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}

    // Integration interface functions
    pub fn get_derivative(&self) -> f64 {{
        self.input
    }}

    pub fn set_state(&mut self, value: f64) {{
        self.state = value;
        self.output = value;
    }}

    pub fn get_state(&self) -> f64 {{
        self.state
    }}
}}
"""


def template_derivative(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Derivative block."""
    return f"""
/// {block.name} - Derivative
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub prev_input: f64,
    pub prev_time: f64,
    pub first_call: bool,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: 0.0,
            prev_input: 0.0,
            prev_time: 0.0,
            first_call: true,
        }}
    }}

    pub fn init(&mut self) {{
        self.input = 0.0;
        self.output = 0.0;
        self.prev_input = 0.0;
        self.prev_time = 0.0;
        self.first_call = true;
    }}

    pub fn update(&mut self, t: f64) {{
        if self.first_call {{
            self.output = 0.0;
            self.first_call = false;
        }} else {{
            let dt = t - self.prev_time;
            if dt > 0.0 {{
                self.output = (self.input - self.prev_input) / dt;
            }}
        }}
        self.prev_input = self.input;
        self.prev_time = t;
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_transfer_function(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Transfer Function block.

    Implements as a chain of integrators in controllable canonical form.
    """
    numerator = block.parameters.get("numerator", [1.0])
    denominator = block.parameters.get("denominator", [1.0, 1.0])

    if not isinstance(numerator, list):
        numerator = [numerator]
    if not isinstance(denominator, list):
        denominator = [denominator]

    order = len(denominator) - 1
    if order < 1:
        order = 1

    # Normalize coefficients
    a0 = denominator[0] if denominator else 1.0
    if a0 == 0:
        a0 = 1.0

    # Coefficients as strings
    a_coeffs = ", ".join([f"{d / a0}_f64" for d in denominator])
    b_coeffs = ", ".join([f"{n / a0}_f64" for n in numerator])

    return f"""
/// {block.name} - Transfer Function (order {order})
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub state: [f64; {order}],
    pub xd0: [f64; {order}],
    pub xd1: [f64; {order}],
    pub xd2: [f64; {order}],
    pub xd3: [f64; {order}],
}}

impl Default for {struct_name} {{
    fn default() -> Self {{
        Self::new()
    }}
}}

impl {struct_name} {{
    pub const ORDER: usize = {order};

    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: 0.0,
            state: [0.0; {order}],
            xd0: [0.0; {order}],
            xd1: [0.0; {order}],
            xd2: [0.0; {order}],
            xd3: [0.0; {order}],
        }}
    }}

    pub fn init(&mut self) {{
        self.input = 0.0;
        self.output = 0.0;
        self.state = [0.0; {order}];
        self.xd0 = [0.0; {order}];
        self.xd1 = [0.0; {order}];
        self.xd2 = [0.0; {order}];
        self.xd3 = [0.0; {order}];
    }}

    pub fn update(&mut self, _t: f64) {{
        // Compute output from state (controllable canonical form)
        let a: [f64; {len(denominator)}] = [{a_coeffs}];
        let bcoef: [f64; {len(numerator)}] = [{b_coeffs}];

        // State space output
        self.output = 0.0;

        // Direct feedthrough term
        if !bcoef.is_empty() && !a.is_empty() {{
            self.output = bcoef[0] * self.input;
        }}

        // State contribution
        for i in 0..Self::ORDER.min(bcoef.len().saturating_sub(1)) {{
            if i + 1 < bcoef.len() {{
                self.output += bcoef[i + 1] * self.state[i];
            }}
        }}
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_state_space(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for State Space block."""
    # Get matrices with defaults
    A = block.parameters.get("A", [[0.0]])
    B = block.parameters.get("B", [[1.0]])
    C = block.parameters.get("C", [[1.0]])
    D = block.parameters.get("D", [[0.0]])

    # Ensure matrices are 2D
    if not isinstance(A, list) or not A:
        A = [[0.0]]
    if not isinstance(A[0], list):
        A = [[A[0]]]
    if not isinstance(B, list) or not B:
        B = [[1.0]]
    if not isinstance(B[0], list):
        B = [[B[0]]]
    if not isinstance(C, list) or not C:
        C = [[1.0]]
    if not isinstance(C[0], list):
        C = [[C[0]]]
    if not isinstance(D, list) or not D:
        D = [[0.0]]
    if not isinstance(D[0], list):
        D = [[D[0]]]

    n_states = len(A)
    n_inputs = len(B[0]) if B else 1
    n_outputs = len(C) if C else 1

    return f"""
/// {block.name} - State Space (n={n_states}, m={n_inputs}, p={n_outputs})
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: [f64; {n_inputs}],
    pub output: [f64; {n_outputs}],
    pub state: [f64; {n_states}],
    pub xd0: [f64; {n_states}],
    pub xd1: [f64; {n_states}],
    pub xd2: [f64; {n_states}],
    pub xd3: [f64; {n_states}],
}}

impl Default for {struct_name} {{
    fn default() -> Self {{
        Self::new()
    }}
}}

impl {struct_name} {{
    pub const N_STATES: usize = {n_states};
    pub const N_INPUTS: usize = {n_inputs};
    pub const N_OUTPUTS: usize = {n_outputs};

    pub fn new() -> Self {{
        Self {{
            input: [0.0; {n_inputs}],
            output: [0.0; {n_outputs}],
            state: [0.0; {n_states}],
            xd0: [0.0; {n_states}],
            xd1: [0.0; {n_states}],
            xd2: [0.0; {n_states}],
            xd3: [0.0; {n_states}],
        }}
    }}

    pub fn init(&mut self) {{
        self.input = [0.0; {n_inputs}];
        self.output = [0.0; {n_outputs}];
        self.state = [0.0; {n_states}];
        self.xd0 = [0.0; {n_states}];
        self.xd1 = [0.0; {n_states}];
        self.xd2 = [0.0; {n_states}];
        self.xd3 = [0.0; {n_states}];
    }}

    pub fn update(&mut self, _t: f64) {{
        // System matrices (simplified - actual values should be set)
        let c: [[f64; {n_states}]; {n_outputs}] = [[0.0; {n_states}]; {n_outputs}];
        let d: [[f64; {n_inputs}]; {n_outputs}] = [[0.0; {n_inputs}]; {n_outputs}];

        // Output: y = Cx + Du
        for i in 0..Self::N_OUTPUTS {{
            self.output[i] = 0.0;
            for j in 0..Self::N_STATES {{
                self.output[i] += c[i][j] * self.state[j];
            }}
            for j in 0..Self::N_INPUTS {{
                self.output[i] += d[i][j] * self.input[j];
            }}
        }}
    }}

    pub fn get_output(&self, port: usize) -> f64 {{
        if port < Self::N_OUTPUTS {{
            self.output[port]
        }} else {{
            0.0
        }}
    }}
}}
"""


def template_second_order(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Second Order Integrator block."""
    wn = block.parameters.get("natural_frequency", 1.0)
    zeta = block.parameters.get("damping_ratio", 0.7)
    ic = block.parameters.get("initial_condition", 0.0)
    ic_dot = block.parameters.get("initial_condition_derivative", 0.0)

    return f"""
/// {block.name} - Second Order System (wn={wn}, zeta={zeta})
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub state: [f64; 2],  // [position, velocity]
    pub xd0: [f64; 2],
    pub xd1: [f64; 2],
    pub xd2: [f64; 2],
    pub xd3: [f64; 2],
    pub wn: f64,        // Natural frequency
    pub zeta: f64,      // Damping ratio
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            wn: {wn}_f64,
            zeta: {zeta}_f64,
            state: [{ic}_f64, {ic_dot}_f64],
            output: {ic}_f64,
            xd0: [0.0; 2],
            xd1: [0.0; 2],
            xd2: [0.0; 2],
            xd3: [0.0; 2],
        }}
    }}

    pub fn init(&mut self) {{
        self.state = [{ic}_f64, {ic_dot}_f64];
        self.output = self.state[0];
        self.xd0 = [0.0; 2];
        self.xd1 = [0.0; 2];
        self.xd2 = [0.0; 2];
        self.xd3 = [0.0; 2];
    }}

    pub fn update(&mut self, _t: f64) {{
        self.output = self.state[0];
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}

    // Integration: x'' + 2*zeta*wn*x' + wn^2*x = wn^2*u
    // State: x1 = x, x2 = x'
    // x1' = x2
    // x2' = wn^2*u - 2*zeta*wn*x2 - wn^2*x1
}}
"""


def template_transport_delay(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Transport Delay block."""
    delay = block.parameters.get("delay", 1.0)
    buffer_size = block.parameters.get("buffer_size", 1024)
    initial_output = block.parameters.get("initial_output", 0.0)

    return f"""
/// {block.name} - Transport Delay ({delay}s)
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub buffer: Vec<f64>,
    pub time_buffer: Vec<f64>,
    pub write_idx: usize,
    pub count: usize,
    pub delay: f64,
    pub initial_output: f64,
}}

impl Default for {struct_name} {{
    fn default() -> Self {{
        Self::new()
    }}
}}

impl {struct_name} {{
    pub const BUFFER_SIZE: usize = {buffer_size};

    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: {initial_output}_f64,
            buffer: vec![{initial_output}_f64; Self::BUFFER_SIZE],
            time_buffer: vec![-1e10; Self::BUFFER_SIZE],
            write_idx: 0,
            count: 0,
            delay: {delay}_f64,
            initial_output: {initial_output}_f64,
        }}
    }}

    pub fn init(&mut self) {{
        self.input = 0.0;
        self.output = self.initial_output;
        self.write_idx = 0;
        self.count = 0;
        self.buffer.fill(self.initial_output);
        self.time_buffer.fill(-1e10);
    }}

    pub fn update(&mut self, t: f64) {{
        // Store current value
        self.buffer[self.write_idx] = self.input;
        self.time_buffer[self.write_idx] = t;
        self.write_idx = (self.write_idx + 1) % Self::BUFFER_SIZE;
        if self.count < Self::BUFFER_SIZE {{
            self.count += 1;
        }}

        // Find delayed value (linear interpolation)
        let target_time = t - self.delay;
        if target_time < 0.0 {{
            self.output = self.initial_output;
            return;
        }}

        // Search for bracketing times
        let mut found = false;
        for i in 0..self.count.saturating_sub(1) {{
            let idx0 = (self.write_idx + Self::BUFFER_SIZE - self.count + i) % Self::BUFFER_SIZE;
            let idx1 = (idx0 + 1) % Self::BUFFER_SIZE;
            if self.time_buffer[idx0] <= target_time && self.time_buffer[idx1] >= target_time {{
                let alpha = (target_time - self.time_buffer[idx0]) /
                           (self.time_buffer[idx1] - self.time_buffer[idx0] + 1e-10);
                self.output = self.buffer[idx0] + alpha * (self.buffer[idx1] - self.buffer[idx0]);
                found = true;
                break;
            }}
        }}
        if !found {{
            self.output = self.initial_output;
        }}
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


CONTINUOUS_TEMPLATES = {
    "integrator": template_integrator,
    "derivative": template_derivative,
    "transfer_function": template_transfer_function,
    "state_space": template_state_space,
    "second_order": template_second_order,
    "transport_delay": template_transport_delay,
}
