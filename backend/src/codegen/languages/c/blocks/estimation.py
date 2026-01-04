"""C templates for state estimation blocks (Kalman filters, observers)."""

from ....models import BlockInfo


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
    def format_matrix(mat, rows, cols, name):
        lines = []
        for i in range(rows):
            for j in range(cols):
                val = mat[i][j] if i < len(mat) and j < len(mat[i]) else 0.0
                lines.append(f"    b->{name}[{i}][{j}] = {val};")
        return "\n".join(lines)

    def format_vector(vec, size, name):
        lines = []
        for i in range(size):
            val = vec[i] if i < len(vec) else 0.0
            lines.append(f"    b->{name}[{i}] = {val};")
        return "\n".join(lines)

    a_init = format_matrix(A, n_states, n_states, "A")
    b_init = format_matrix(B, n_states, n_inputs, "B")
    c_init = format_matrix(C, n_outputs, n_states, "C")
    q_init = format_matrix(Q, n_states, n_states, "Q")
    r_init = format_matrix(R, n_outputs, n_outputs, "R")
    x_init = format_vector(initial_state, n_states, "x")
    p_init = format_matrix(initial_P, n_states, n_states, "P")

    return f"""
// {block.name} - Kalman Filter
#define {struct_name.upper()}_N_STATES {n_states}
#define {struct_name.upper()}_N_INPUTS {n_inputs}
#define {struct_name.upper()}_N_OUTPUTS {n_outputs}

typedef struct {{
    // Inputs: input (u - control), input1 (y - measurement)
    double input;   // Control input (port 0)
    double input1;  // Measurement input (port 1)

    // State estimate output
    double x[{struct_name.upper()}_N_STATES];

    // System matrices
    double A[{struct_name.upper()}_N_STATES][{struct_name.upper()}_N_STATES];
    double B[{struct_name.upper()}_N_STATES][{struct_name.upper()}_N_INPUTS];
    double C[{struct_name.upper()}_N_OUTPUTS][{struct_name.upper()}_N_STATES];
    double Q[{struct_name.upper()}_N_STATES][{struct_name.upper()}_N_STATES];
    double R[{struct_name.upper()}_N_OUTPUTS][{struct_name.upper()}_N_OUTPUTS];

    // Estimation covariance
    double P[{struct_name.upper()}_N_STATES][{struct_name.upper()}_N_STATES];

    // Working matrices
    double x_pred[{struct_name.upper()}_N_STATES];
    double P_pred[{struct_name.upper()}_N_STATES][{struct_name.upper()}_N_STATES];
    double K[{struct_name.upper()}_N_STATES][{struct_name.upper()}_N_OUTPUTS];
    double temp_nn[{struct_name.upper()}_N_STATES][{struct_name.upper()}_N_STATES];
    double temp_on[{struct_name.upper()}_N_OUTPUTS][{struct_name.upper()}_N_STATES];
    double temp_oo[{struct_name.upper()}_N_OUTPUTS][{struct_name.upper()}_N_OUTPUTS];
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->input1 = 0.0;

    // Initialize system matrices
{a_init}
{b_init}
{c_init}
{q_init}
{r_init}
    // Initialize state estimate
{x_init}
    // Initialize covariance
{p_init}
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;

    // === PREDICT ===
    // x_pred = A * x + B * u
    for (int i = 0; i < {struct_name.upper()}_N_STATES; i++) {{
        b->x_pred[i] = 0.0;
        for (int j = 0; j < {struct_name.upper()}_N_STATES; j++) {{
            b->x_pred[i] += b->A[i][j] * b->x[j];
        }}
        // B * u (input is control)
        b->x_pred[i] += b->B[i][0] * b->input;
    }}

    // P_pred = A * P * A' + Q
    // First: temp = A * P
    for (int i = 0; i < {struct_name.upper()}_N_STATES; i++) {{
        for (int j = 0; j < {struct_name.upper()}_N_STATES; j++) {{
            b->temp_nn[i][j] = 0.0;
            for (int k = 0; k < {struct_name.upper()}_N_STATES; k++) {{
                b->temp_nn[i][j] += b->A[i][k] * b->P[k][j];
            }}
        }}
    }}
    // Then: P_pred = temp * A' + Q
    for (int i = 0; i < {struct_name.upper()}_N_STATES; i++) {{
        for (int j = 0; j < {struct_name.upper()}_N_STATES; j++) {{
            b->P_pred[i][j] = b->Q[i][j];
            for (int k = 0; k < {struct_name.upper()}_N_STATES; k++) {{
                b->P_pred[i][j] += b->temp_nn[i][k] * b->A[j][k];
            }}
        }}
    }}

    // === UPDATE ===
    // Innovation covariance: S = C * P_pred * C' + R
    for (int i = 0; i < {struct_name.upper()}_N_OUTPUTS; i++) {{
        for (int j = 0; j < {struct_name.upper()}_N_STATES; j++) {{
            b->temp_on[i][j] = 0.0;
            for (int k = 0; k < {struct_name.upper()}_N_STATES; k++) {{
                b->temp_on[i][j] += b->C[i][k] * b->P_pred[k][j];
            }}
        }}
    }}
    for (int i = 0; i < {struct_name.upper()}_N_OUTPUTS; i++) {{
        for (int j = 0; j < {struct_name.upper()}_N_OUTPUTS; j++) {{
            b->temp_oo[i][j] = b->R[i][j];
            for (int k = 0; k < {struct_name.upper()}_N_STATES; k++) {{
                b->temp_oo[i][j] += b->temp_on[i][k] * b->C[j][k];
            }}
        }}
    }}

    // Kalman gain: K = P_pred * C' * S^-1
    if ({struct_name.upper()}_N_OUTPUTS == 1) {{
        double s_inv = 1.0 / b->temp_oo[0][0];
        for (int i = 0; i < {struct_name.upper()}_N_STATES; i++) {{
            double pc = 0.0;
            for (int k = 0; k < {struct_name.upper()}_N_STATES; k++) {{
                pc += b->P_pred[i][k] * b->C[0][k];
            }}
            b->K[i][0] = pc * s_inv;
        }}
    }} else if ({struct_name.upper()}_N_OUTPUTS == 2) {{
        double det = b->temp_oo[0][0] * b->temp_oo[1][1] - b->temp_oo[0][1] * b->temp_oo[1][0];
        double s_inv[2][2] = {{
            {{ b->temp_oo[1][1] / det, -b->temp_oo[0][1] / det}},
            {{-b->temp_oo[1][0] / det,  b->temp_oo[0][0] / det}}
        }};
        for (int i = 0; i < {struct_name.upper()}_N_STATES; i++) {{
            for (int j = 0; j < {struct_name.upper()}_N_OUTPUTS; j++) {{
                b->K[i][j] = 0.0;
                for (int m = 0; m < {struct_name.upper()}_N_STATES; m++) {{
                    for (int n = 0; n < {struct_name.upper()}_N_OUTPUTS; n++) {{
                        b->K[i][j] += b->P_pred[i][m] * b->C[n][m] * s_inv[n][j];
                    }}
                }}
            }}
        }}
    }}

    // Innovation: y - C * x_pred (input1 is measurement)
    double innovation[{struct_name.upper()}_N_OUTPUTS];
    for (int i = 0; i < {struct_name.upper()}_N_OUTPUTS; i++) {{
        innovation[i] = b->input1;  // Single measurement input
        for (int j = 0; j < {struct_name.upper()}_N_STATES; j++) {{
            innovation[i] -= b->C[i][j] * b->x_pred[j];
        }}
    }}

    // State update: x = x_pred + K * innovation
    for (int i = 0; i < {struct_name.upper()}_N_STATES; i++) {{
        b->x[i] = b->x_pred[i];
        for (int j = 0; j < {struct_name.upper()}_N_OUTPUTS; j++) {{
            b->x[i] += b->K[i][j] * innovation[j];
        }}
    }}

    // Covariance update: P = (I - K * C) * P_pred
    for (int i = 0; i < {struct_name.upper()}_N_STATES; i++) {{
        for (int j = 0; j < {struct_name.upper()}_N_STATES; j++) {{
            b->temp_nn[i][j] = (i == j) ? 1.0 : 0.0;
            for (int k = 0; k < {struct_name.upper()}_N_OUTPUTS; k++) {{
                b->temp_nn[i][j] -= b->K[i][k] * b->C[k][j];
            }}
        }}
    }}
    double P_new[{struct_name.upper()}_N_STATES][{struct_name.upper()}_N_STATES];
    for (int i = 0; i < {struct_name.upper()}_N_STATES; i++) {{
        for (int j = 0; j < {struct_name.upper()}_N_STATES; j++) {{
            P_new[i][j] = 0.0;
            for (int k = 0; k < {struct_name.upper()}_N_STATES; k++) {{
                P_new[i][j] += b->temp_nn[i][k] * b->P_pred[k][j];
            }}
        }}
    }}
    for (int i = 0; i < {struct_name.upper()}_N_STATES; i++) {{
        for (int j = 0; j < {struct_name.upper()}_N_STATES; j++) {{
            b->P[i][j] = P_new[i][j];
        }}
    }}
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    if (port >= 0 && port < {struct_name.upper()}_N_STATES) {{
        return b->x[port];
    }}
    return 0.0;
}}

static inline double* {struct_name}_get_output_vector({struct_name}* b) {{
    return b->x;
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

    def format_matrix(mat, rows, cols, name):
        lines = []
        for i in range(rows):
            for j in range(cols):
                val = mat[i][j] if i < len(mat) and j < len(mat[i]) else 0.0
                lines.append(f"    b->{name}[{i}][{j}] = {val};")
        return "\n".join(lines)

    def format_vector(vec, size, name):
        lines = []
        for i in range(size):
            val = vec[i] if i < len(vec) else 0.0
            lines.append(f"    b->{name}[{i}] = {val};")
        return "\n".join(lines)

    a_init = format_matrix(A, n_states, n_states, "A")
    b_init = format_matrix(B, n_states, n_inputs, "B")
    c_init = format_matrix(C, n_outputs, n_states, "C")
    l_init = format_matrix(L, n_states, n_outputs, "L")
    x_init = format_vector(initial_state, n_states, "x[0]")

    return f"""
// {block.name} - Luenberger Observer
#define {struct_name.upper()}_N_STATES {n_states}
#define {struct_name.upper()}_N_INPUTS {n_inputs}
#define {struct_name.upper()}_N_OUTPUTS {n_outputs}

typedef struct {{
    // Inputs: input (u - control), input1 (y - measurement)
    double input;   // Control input (port 0)
    double input1;  // Measurement input (port 1)

    // State estimate [value, derivative]
    double x[{struct_name.upper()}_N_STATES][2];
    double x0[{struct_name.upper()}_N_STATES];
    double xd0[{struct_name.upper()}_N_STATES], xd1[{struct_name.upper()}_N_STATES];
    double xd2[{struct_name.upper()}_N_STATES], xd3[{struct_name.upper()}_N_STATES];

    // System matrices
    double A[{struct_name.upper()}_N_STATES][{struct_name.upper()}_N_STATES];
    double B[{struct_name.upper()}_N_STATES][{struct_name.upper()}_N_INPUTS];
    double C[{struct_name.upper()}_N_OUTPUTS][{struct_name.upper()}_N_STATES];
    double L[{struct_name.upper()}_N_STATES][{struct_name.upper()}_N_OUTPUTS];
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->input1 = 0.0;
{a_init}
{b_init}
{c_init}
{l_init}
{x_init}
    for (int i = 0; i < {struct_name.upper()}_N_STATES; i++) {{
        b->x[i][1] = 0.0;
        b->x0[i] = 0.0;
        b->xd0[i] = b->xd1[i] = b->xd2[i] = b->xd3[i] = 0.0;
    }}
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;

    // Compute y_hat = C * x
    double y_hat[{struct_name.upper()}_N_OUTPUTS];
    for (int i = 0; i < {struct_name.upper()}_N_OUTPUTS; i++) {{
        y_hat[i] = 0.0;
        for (int j = 0; j < {struct_name.upper()}_N_STATES; j++) {{
            y_hat[i] += b->C[i][j] * b->x[j][0];
        }}
    }}

    // Compute error = y - y_hat (input1 is measurement)
    double error[{struct_name.upper()}_N_OUTPUTS];
    for (int i = 0; i < {struct_name.upper()}_N_OUTPUTS; i++) {{
        error[i] = b->input1 - y_hat[i];
    }}

    // x_dot = A*x + B*u + L*error
    for (int i = 0; i < {struct_name.upper()}_N_STATES; i++) {{
        b->x[i][1] = 0.0;
        for (int j = 0; j < {struct_name.upper()}_N_STATES; j++) {{
            b->x[i][1] += b->A[i][j] * b->x[j][0];
        }}
        // B*u (input is control)
        b->x[i][1] += b->B[i][0] * b->input;
        // L*error
        for (int j = 0; j < {struct_name.upper()}_N_OUTPUTS; j++) {{
            b->x[i][1] += b->L[i][j] * error[j];
        }}
    }}
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    if (port >= 0 && port < {struct_name.upper()}_N_STATES) {{
        return b->x[port][0];
    }}
    return 0.0;
}}

void {struct_name}_propagate_states({struct_name}* b, double dt, int kpass, const char* method) {{
    for (int i = 0; i < {struct_name.upper()}_N_STATES; i++) {{
        propagate_integrator(
            &b->x[i][0],
            &b->x0[i], &b->xd0[i], &b->xd1[i], &b->xd2[i], &b->xd3[i],
            b->x[i][1],
            dt, kpass, method
        );
    }}
}}
"""


# Template registry for estimation blocks
ESTIMATION_TEMPLATES = {
    "kalman_filter": kalman_filter_template,
    "luenberger_observer": luenberger_observer_template,
}
