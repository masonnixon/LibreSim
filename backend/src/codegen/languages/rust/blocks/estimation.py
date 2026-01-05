"""Rust templates for state estimation blocks (Kalman filters, observers)."""

from ....models import BlockInfo


def _format_f64(value) -> str:
    """Format a numeric value as a Rust f64 literal."""
    if isinstance(value, (int, float)):
        s = str(float(value))
        if "." not in s and "e" not in s.lower():
            return s + ".0"
        return s
    return str(value)


def kalman_filter_template(block: BlockInfo, struct_name: str) -> str:
    """Generate Kalman filter block code.

    Implements a discrete-time Kalman filter:
    Predict:
        x_pred = A * x + B * u
        P_pred = A * P * A' + Q
    Update:
        K = P_pred * C' * (C * P_pred * C' + R)^-1
        x = x_pred + K * (y - C * x_pred)
        P = (I - K * C) * P_pred
    """
    A = block.parameters.get("A", [[1.0]])
    B = block.parameters.get("B", [[0.0]])
    C = block.parameters.get("C", [[1.0]])
    Q = block.parameters.get("Q", [[0.0001]])
    R = block.parameters.get("R", [[0.01]])
    initial_state = block.parameters.get("initialState", [0.0])
    initial_P = block.parameters.get("initialP", [[1.0]])

    # Infer dimensions
    n_states = len(A)
    n_inputs = len(B[0]) if B and B[0] else 1
    n_outputs = len(C)

    # Format matrix initializations
    def format_matrix(mat, rows, cols):
        outer = []
        for i in range(rows):
            inner = []
            for j in range(cols):
                val = mat[i][j] if i < len(mat) and j < len(mat[i]) else 0.0
                inner.append(_format_f64(val))
            outer.append("[" + ", ".join(inner) + "]")
        return "[" + ", ".join(outer) + "]"

    def format_vector(vec, size):
        vals = []
        for i in range(size):
            val = vec[i] if i < len(vec) else 0.0
            vals.append(_format_f64(val))
        return "[" + ", ".join(vals) + "]"

    a_init = format_matrix(A, n_states, n_states)
    b_init = format_matrix(B, n_states, n_inputs)
    c_init = format_matrix(C, n_outputs, n_states)
    q_init = format_matrix(Q, n_states, n_states)
    r_init = format_matrix(R, n_outputs, n_outputs)
    x_init = format_vector(initial_state, n_states)
    p_init = format_matrix(initial_P, n_states, n_states)

    return f"""
/// {block.name} - Kalman Filter
#[derive(Clone)]
pub struct {struct_name} {{
    // Inputs: input (u - control), input1 (y - measurement)
    pub input: f64,   // Control input (port 0)
    pub input1: f64,  // Measurement input (port 1)

    // State estimate output
    pub x: [f64; {n_states}],

    // System matrices
    pub a: [[f64; {n_states}]; {n_states}],
    pub b: [[f64; {n_inputs}]; {n_states}],
    pub c: [[f64; {n_states}]; {n_outputs}],
    pub q: [[f64; {n_states}]; {n_states}],
    pub r: [[f64; {n_outputs}]; {n_outputs}],

    // Estimation covariance
    pub p: [[f64; {n_states}]; {n_states}],
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            input1: 0.0,
            x: {x_init},
            a: {a_init},
            b: {b_init},
            c: {c_init},
            q: {q_init},
            r: {r_init},
            p: {p_init},
        }}
    }}

    pub fn init(&mut self) {{
        self.input = 0.0;
        self.input1 = 0.0;
        self.x = {x_init};
        self.p = {p_init};
    }}

    pub fn update(&mut self, _t: f64) {{
        const N_STATES: usize = {n_states};
        const N_INPUTS: usize = {n_inputs};
        const N_OUTPUTS: usize = {n_outputs};

        // === PREDICT ===
        // x_pred = A * x + B * u
        let mut x_pred = [0.0; N_STATES];
        for i in 0..N_STATES {{
            for j in 0..N_STATES {{
                x_pred[i] += self.a[i][j] * self.x[j];
            }}
            // B * u (input is control)
            x_pred[i] += self.b[i][0] * self.input;
        }}

        // P_pred = A * P * A' + Q
        let mut temp_nn = [[0.0; N_STATES]; N_STATES];
        for i in 0..N_STATES {{
            for j in 0..N_STATES {{
                for k in 0..N_STATES {{
                    temp_nn[i][j] += self.a[i][k] * self.p[k][j];
                }}
            }}
        }}
        let mut p_pred = [[0.0; N_STATES]; N_STATES];
        for i in 0..N_STATES {{
            for j in 0..N_STATES {{
                p_pred[i][j] = self.q[i][j];
                for k in 0..N_STATES {{
                    p_pred[i][j] += temp_nn[i][k] * self.a[j][k];
                }}
            }}
        }}

        // === UPDATE ===
        // Innovation covariance: S = C * P_pred * C' + R
        let mut temp_on = [[0.0; N_STATES]; N_OUTPUTS];
        for i in 0..N_OUTPUTS {{
            for j in 0..N_STATES {{
                for k in 0..N_STATES {{
                    temp_on[i][j] += self.c[i][k] * p_pred[k][j];
                }}
            }}
        }}
        let mut s = [[0.0; N_OUTPUTS]; N_OUTPUTS];
        for i in 0..N_OUTPUTS {{
            for j in 0..N_OUTPUTS {{
                s[i][j] = self.r[i][j];
                for k in 0..N_STATES {{
                    s[i][j] += temp_on[i][k] * self.c[j][k];
                }}
            }}
        }}

        // Kalman gain: K = P_pred * C' * S^-1
        let mut k = [[0.0; N_OUTPUTS]; N_STATES];
        if N_OUTPUTS == 1 {{
            let s_inv = 1.0 / s[0][0];
            for i in 0..N_STATES {{
                let mut pc = 0.0;
                for j in 0..N_STATES {{
                    pc += p_pred[i][j] * self.c[0][j];
                }}
                k[i][0] = pc * s_inv;
            }}
        }} else if N_OUTPUTS == 2 {{
            let det = s[0][0] * s[1][1] - s[0][1] * s[1][0];
            let s_inv = [
                [ s[1][1] / det, -s[0][1] / det],
                [-s[1][0] / det,  s[0][0] / det],
            ];
            for i in 0..N_STATES {{
                for j in 0..N_OUTPUTS {{
                    for m in 0..N_STATES {{
                        for n in 0..N_OUTPUTS {{
                            k[i][j] += p_pred[i][m] * self.c[n][m] * s_inv[n][j];
                        }}
                    }}
                }}
            }}
        }}

        // Innovation: y - C * x_pred (input1 is measurement)
        let mut innovation = [0.0; N_OUTPUTS];
        for i in 0..N_OUTPUTS {{
            innovation[i] = self.input1;  // Single measurement input
            for j in 0..N_STATES {{
                innovation[i] -= self.c[i][j] * x_pred[j];
            }}
        }}

        // State update: x = x_pred + K * innovation
        for i in 0..N_STATES {{
            self.x[i] = x_pred[i];
            for j in 0..N_OUTPUTS {{
                self.x[i] += k[i][j] * innovation[j];
            }}
        }}

        // Covariance update: P = (I - K * C) * P_pred
        let mut ikc = [[0.0; N_STATES]; N_STATES];
        for i in 0..N_STATES {{
            for j in 0..N_STATES {{
                ikc[i][j] = if i == j {{ 1.0 }} else {{ 0.0 }};
                for m in 0..N_OUTPUTS {{
                    ikc[i][j] -= k[i][m] * self.c[m][j];
                }}
            }}
        }}
        let mut p_new = [[0.0; N_STATES]; N_STATES];
        for i in 0..N_STATES {{
            for j in 0..N_STATES {{
                for m in 0..N_STATES {{
                    p_new[i][j] += ikc[i][m] * p_pred[m][j];
                }}
            }}
        }}
        self.p = p_new;
    }}

    pub fn get_output(&self, port: i32) -> f64 {{
        if port >= 0 && (port as usize) < {n_states} {{
            self.x[port as usize]
        }} else {{
            0.0
        }}
    }}

    pub fn get_output_vector(&self) -> &[f64; {n_states}] {{
        &self.x
    }}
}}
"""


def luenberger_observer_template(block: BlockInfo, struct_name: str) -> str:
    """Generate Luenberger observer block code."""
    A = block.parameters.get("A", [[0.0]])
    B = block.parameters.get("B", [[1.0]])
    C = block.parameters.get("C", [[1.0]])
    L = block.parameters.get("L", [[1.0]])
    initial_state = block.parameters.get("initialState", [0.0])

    n_states = len(A)
    n_inputs = len(B[0]) if B and B[0] else 1
    n_outputs = len(C)

    def format_matrix(mat, rows, cols):
        outer = []
        for i in range(rows):
            inner = []
            for j in range(cols):
                val = mat[i][j] if i < len(mat) and j < len(mat[i]) else 0.0
                inner.append(_format_f64(val))
            outer.append("[" + ", ".join(inner) + "]")
        return "[" + ", ".join(outer) + "]"

    def format_vector(vec, size):
        vals = []
        for i in range(size):
            val = vec[i] if i < len(vec) else 0.0
            vals.append(_format_f64(val))
        return "[" + ", ".join(vals) + "]"

    a_init = format_matrix(A, n_states, n_states)
    b_init = format_matrix(B, n_states, n_inputs)
    c_init = format_matrix(C, n_outputs, n_states)
    l_init = format_matrix(L, n_states, n_outputs)
    x_init = format_vector(initial_state, n_states)

    return f"""
/// {block.name} - Luenberger Observer
#[derive(Clone)]
pub struct {struct_name} {{
    // Inputs: input (u - control), input1 (y - measurement)
    pub input: f64,   // Control input (port 0)
    pub input1: f64,  // Measurement input (port 1)

    // State estimate [value, derivative]
    pub x: [[f64; 2]; {n_states}],
    pub x0: [f64; {n_states}],
    pub xd0: [f64; {n_states}],
    pub xd1: [f64; {n_states}],
    pub xd2: [f64; {n_states}],
    pub xd3: [f64; {n_states}],

    // System matrices
    pub a: [[f64; {n_states}]; {n_states}],
    pub b: [[f64; {n_inputs}]; {n_states}],
    pub c: [[f64; {n_states}]; {n_outputs}],
    pub l: [[f64; {n_outputs}]; {n_states}],
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        let x_init: [f64; {n_states}] = {x_init};
        let mut x = [[0.0; 2]; {n_states}];
        for i in 0..{n_states} {{
            x[i][0] = x_init[i];
        }}
        Self {{
            input: 0.0,
            input1: 0.0,
            x,
            x0: [0.0; {n_states}],
            xd0: [0.0; {n_states}],
            xd1: [0.0; {n_states}],
            xd2: [0.0; {n_states}],
            xd3: [0.0; {n_states}],
            a: {a_init},
            b: {b_init},
            c: {c_init},
            l: {l_init},
        }}
    }}

    pub fn init(&mut self) {{
        self.input = 0.0;
        self.input1 = 0.0;
        let x_init: [f64; {n_states}] = {x_init};
        for i in 0..{n_states} {{
            self.x[i] = [x_init[i], 0.0];
        }}
    }}

    pub fn update(&mut self, _t: f64) {{
        const N_STATES: usize = {n_states};
        const N_INPUTS: usize = {n_inputs};
        const N_OUTPUTS: usize = {n_outputs};

        // Compute y_hat = C * x
        let mut y_hat = [0.0; N_OUTPUTS];
        for i in 0..N_OUTPUTS {{
            for j in 0..N_STATES {{
                y_hat[i] += self.c[i][j] * self.x[j][0];
            }}
        }}

        // Compute error = y - y_hat (input1 is measurement)
        let mut error = [0.0; N_OUTPUTS];
        for i in 0..N_OUTPUTS {{
            error[i] = self.input1 - y_hat[i];
        }}

        // x_dot = A*x + B*u + L*error
        for i in 0..N_STATES {{
            self.x[i][1] = 0.0;
            for j in 0..N_STATES {{
                self.x[i][1] += self.a[i][j] * self.x[j][0];
            }}
            // B*u (input is control)
            self.x[i][1] += self.b[i][0] * self.input;
            // L*error
            for j in 0..N_OUTPUTS {{
                self.x[i][1] += self.l[i][j] * error[j];
            }}
        }}
    }}

    pub fn get_output(&self, port: i32) -> f64 {{
        if port >= 0 && (port as usize) < {n_states} {{
            self.x[port as usize][0]
        }} else {{
            0.0
        }}
    }}

    pub fn propagate_states(&mut self, dt: f64, kpass: usize, method: IntegrationMethod) {{
        for i in 0..{n_states} {{
            let deriv = self.x[i][1];
            propagate_integrator(
                &mut self.x[i][0],
                &mut self.x0[i],
                &mut self.xd0[i],
                &mut self.xd1[i],
                &mut self.xd2[i],
                &mut self.xd3[i],
                deriv,
                dt, kpass, method,
            );
        }}
    }}
}}
"""


# Template registry for estimation blocks
ESTIMATION_TEMPLATES = {
    "kalman_filter": kalman_filter_template,
    "luenberger_observer": luenberger_observer_template,
}
