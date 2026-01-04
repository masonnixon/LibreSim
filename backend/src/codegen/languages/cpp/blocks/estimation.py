"""C++ templates for state estimation blocks (Kalman filters, observers)."""

from ....models import BlockInfo


def kalman_filter_template(block: BlockInfo, class_name: str) -> str:
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
    n_states = len(A)  # Number of states
    n_inputs = len(B[0]) if B and B[0] else 1  # Number of control inputs
    n_outputs = len(C)  # Number of measurements

    # Format matrix initializations
    def format_matrix(mat, rows, cols, name):
        lines = []
        for i in range(rows):
            for j in range(cols):
                val = mat[i][j] if i < len(mat) and j < len(mat[i]) else 0.0
                lines.append(f"        {name}[{i}][{j}] = {val};")
        return "\n".join(lines)

    def format_vector(vec, size, name):
        lines = []
        for i in range(size):
            val = vec[i] if i < len(vec) else 0.0
            lines.append(f"        {name}[{i}] = {val};")
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
#include <array>

class {class_name} {{
public:
    static constexpr int N_STATES = {n_states};
    static constexpr int N_INPUTS = {n_inputs};
    static constexpr int N_OUTPUTS = {n_outputs};

    // Inputs: input (u - control), input1 (y - measurement)
    double input = 0.0;   // Control input (port 0)
    double input1 = 0.0;  // Measurement input (port 1)

    // State estimate output
    std::array<double, N_STATES> x = {{}};

    // System matrices
    double A[N_STATES][N_STATES];
    double B[N_STATES][N_INPUTS];
    double C[N_OUTPUTS][N_STATES];
    double Q[N_STATES][N_STATES];
    double R[N_OUTPUTS][N_OUTPUTS];

    // Estimation covariance
    double P[N_STATES][N_STATES];

    // Working matrices
    double x_pred[N_STATES];
    double P_pred[N_STATES][N_STATES];
    double K[N_STATES][N_OUTPUTS];
    double temp_nn[N_STATES][N_STATES];
    double temp_on[N_OUTPUTS][N_STATES];
    double temp_oo[N_OUTPUTS][N_OUTPUTS];

    void init() {{
        input = 0.0;
        input1 = 0.0;
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

    void update(double t) {{
        (void)t;

        // === PREDICT ===
        // x_pred = A * x + B * u
        for (int i = 0; i < N_STATES; i++) {{
            x_pred[i] = 0.0;
            for (int j = 0; j < N_STATES; j++) {{
                x_pred[i] += A[i][j] * x[j];
            }}
            // B * u (input is the control signal)
            x_pred[i] += B[i][0] * input;
        }}

        // P_pred = A * P * A' + Q
        // First: temp = A * P
        for (int i = 0; i < N_STATES; i++) {{
            for (int j = 0; j < N_STATES; j++) {{
                temp_nn[i][j] = 0.0;
                for (int k = 0; k < N_STATES; k++) {{
                    temp_nn[i][j] += A[i][k] * P[k][j];
                }}
            }}
        }}
        // Then: P_pred = temp * A' + Q
        for (int i = 0; i < N_STATES; i++) {{
            for (int j = 0; j < N_STATES; j++) {{
                P_pred[i][j] = Q[i][j];
                for (int k = 0; k < N_STATES; k++) {{
                    P_pred[i][j] += temp_nn[i][k] * A[j][k];  // A' means A[j][k]
                }}
            }}
        }}

        // === UPDATE ===
        // Innovation covariance: S = C * P_pred * C' + R
        // First: temp_on = C * P_pred
        for (int i = 0; i < N_OUTPUTS; i++) {{
            for (int j = 0; j < N_STATES; j++) {{
                temp_on[i][j] = 0.0;
                for (int k = 0; k < N_STATES; k++) {{
                    temp_on[i][j] += C[i][k] * P_pred[k][j];
                }}
            }}
        }}
        // S = temp_on * C' + R
        for (int i = 0; i < N_OUTPUTS; i++) {{
            for (int j = 0; j < N_OUTPUTS; j++) {{
                temp_oo[i][j] = R[i][j];
                for (int k = 0; k < N_STATES; k++) {{
                    temp_oo[i][j] += temp_on[i][k] * C[j][k];
                }}
            }}
        }}

        // Kalman gain: K = P_pred * C' * S^-1
        // For simplicity, handle 1x1 and 2x2 S matrices
        if (N_OUTPUTS == 1) {{
            double s_inv = 1.0 / temp_oo[0][0];
            for (int i = 0; i < N_STATES; i++) {{
                double pc = 0.0;
                for (int k = 0; k < N_STATES; k++) {{
                    pc += P_pred[i][k] * C[0][k];
                }}
                K[i][0] = pc * s_inv;
            }}
        }} else {{
            // General matrix inverse for small matrices
            // For 2x2: inv = [d -b; -c a] / det
            if (N_OUTPUTS == 2) {{
                double det = temp_oo[0][0] * temp_oo[1][1] - temp_oo[0][1] * temp_oo[1][0];
                double s_inv[2][2] = {{
                    {{ temp_oo[1][1] / det, -temp_oo[0][1] / det}},
                    {{-temp_oo[1][0] / det,  temp_oo[0][0] / det}}
                }};
                // K = P_pred * C' * S_inv
                for (int i = 0; i < N_STATES; i++) {{
                    for (int j = 0; j < N_OUTPUTS; j++) {{
                        K[i][j] = 0.0;
                        for (int m = 0; m < N_STATES; m++) {{
                            for (int n = 0; n < N_OUTPUTS; n++) {{
                                K[i][j] += P_pred[i][m] * C[n][m] * s_inv[n][j];
                            }}
                        }}
                    }}
                }}
            }}
        }}

        // Innovation: y - C * x_pred (input1 is the measurement)
        double innovation[N_OUTPUTS];
        for (int i = 0; i < N_OUTPUTS; i++) {{
            innovation[i] = input1;  // Single measurement input
            for (int j = 0; j < N_STATES; j++) {{
                innovation[i] -= C[i][j] * x_pred[j];
            }}
        }}

        // State update: x = x_pred + K * innovation
        for (int i = 0; i < N_STATES; i++) {{
            x[i] = x_pred[i];
            for (int j = 0; j < N_OUTPUTS; j++) {{
                x[i] += K[i][j] * innovation[j];
            }}
        }}

        // Covariance update: P = (I - K * C) * P_pred
        // temp_nn = K * C
        for (int i = 0; i < N_STATES; i++) {{
            for (int j = 0; j < N_STATES; j++) {{
                temp_nn[i][j] = (i == j) ? 1.0 : 0.0;  // Start with identity
                for (int k = 0; k < N_OUTPUTS; k++) {{
                    temp_nn[i][j] -= K[i][k] * C[k][j];
                }}
            }}
        }}
        // P = temp_nn * P_pred
        double P_new[N_STATES][N_STATES];
        for (int i = 0; i < N_STATES; i++) {{
            for (int j = 0; j < N_STATES; j++) {{
                P_new[i][j] = 0.0;
                for (int k = 0; k < N_STATES; k++) {{
                    P_new[i][j] += temp_nn[i][k] * P_pred[k][j];
                }}
            }}
        }}
        for (int i = 0; i < N_STATES; i++) {{
            for (int j = 0; j < N_STATES; j++) {{
                P[i][j] = P_new[i][j];
            }}
        }}
    }}

    double get_output(int port) const {{
        if (port >= 0 && port < N_STATES) {{
            return x[port];
        }}
        return 0.0;
    }}

    const std::array<double, N_STATES>& getOutputVector() const {{
        return x;
    }}
}};
"""


def luenberger_observer_template(block: BlockInfo, class_name: str) -> str:
    """Generate Luenberger observer block code.

    Implements: x_dot = A*x + B*u + L*(y - C*x)
    """
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
                lines.append(f"        {name}[{i}][{j}] = {val};")
        return "\n".join(lines)

    def format_vector(vec, size, name):
        lines = []
        for i in range(size):
            val = vec[i] if i < len(vec) else 0.0
            lines.append(f"        {name}[{i}] = {val};")
        return "\n".join(lines)

    a_init = format_matrix(A, n_states, n_states, "A")
    b_init = format_matrix(B, n_states, n_inputs, "B")
    c_init = format_matrix(C, n_outputs, n_states, "C")
    l_init = format_matrix(L, n_states, n_outputs, "L")
    x_init = format_vector(initial_state, n_states, "x[0]")

    return f"""
// {block.name} - Luenberger Observer
#include <array>

class {class_name} {{
public:
    static constexpr int N_STATES = {n_states};
    static constexpr int N_INPUTS = {n_inputs};
    static constexpr int N_OUTPUTS = {n_outputs};

    // Inputs: input (u - control), input1 (y - measurement)
    double input = 0.0;   // Control input (port 0)
    double input1 = 0.0;  // Measurement input (port 1)

    // State estimate [value, derivative] for each state
    double x[N_STATES][2] = {{{{0.0}}}};
    std::array<double, N_STATES> x_out = {{}};  // Output array for getOutputVector
    double x0[N_STATES] = {{0.0}};
    double xd0[N_STATES] = {{0.0}}, xd1[N_STATES] = {{0.0}};
    double xd2[N_STATES] = {{0.0}}, xd3[N_STATES] = {{0.0}};

    // System matrices
    double A[N_STATES][N_STATES];
    double B[N_STATES][N_INPUTS];
    double C[N_OUTPUTS][N_STATES];
    double L[N_STATES][N_OUTPUTS];

    void init() {{
        input = 0.0;
        input1 = 0.0;
{a_init}
{b_init}
{c_init}
{l_init}
{x_init}
    }}

    void update(double t) {{
        (void)t;

        // Compute y_hat = C * x
        double y_hat[N_OUTPUTS] = {{0.0}};
        for (int i = 0; i < N_OUTPUTS; i++) {{
            for (int j = 0; j < N_STATES; j++) {{
                y_hat[i] += C[i][j] * x[j][0];
            }}
        }}

        // Compute error = y - y_hat (input1 is measurement)
        double error[N_OUTPUTS];
        for (int i = 0; i < N_OUTPUTS; i++) {{
            error[i] = input1 - y_hat[i];
        }}

        // x_dot = A*x + B*u + L*error
        for (int i = 0; i < N_STATES; i++) {{
            x[i][1] = 0.0;
            // A*x
            for (int j = 0; j < N_STATES; j++) {{
                x[i][1] += A[i][j] * x[j][0];
            }}
            // B*u (input is control)
            x[i][1] += B[i][0] * input;
            // L*error
            for (int j = 0; j < N_OUTPUTS; j++) {{
                x[i][1] += L[i][j] * error[j];
            }}
        }}
    }}

    double get_output(int port) const {{
        if (port >= 0 && port < N_STATES) {{
            return x[port][0];
        }}
        return 0.0;
    }}

    const std::array<double, N_STATES>& getOutputVector() {{
        for (int i = 0; i < N_STATES; i++) {{
            x_out[i] = x[i][0];
        }}
        return x_out;
    }}

    void propagate_states(double dt, int kpass, const std::string& method) {{
        for (int i = 0; i < N_STATES; i++) {{
            propagate_integrator(
                x[i][0],
                x0[i], xd0[i], xd1[i], xd2[i], xd3[i],
                x[i][1],
                dt, kpass, method
            );
        }}
    }}
}};
"""


# Template registry for estimation blocks
ESTIMATION_TEMPLATES = {
    "kalman_filter": kalman_filter_template,
    "luenberger_observer": luenberger_observer_template,
}
