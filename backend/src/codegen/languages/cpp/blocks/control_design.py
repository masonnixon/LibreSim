"""C++ templates for control design blocks."""

from ....models import BlockInfo


def pid_controller_template(block: BlockInfo, class_name: str) -> str:
    """Generate PID controller block code."""
    kp = block.parameters.get("Kp", 1.0)
    ki = block.parameters.get("Ki", 1.0)
    kd = block.parameters.get("Kd", 0.0)
    n = block.parameters.get("N", 100.0)
    return f"""
// {block.name} - PID Controller
class {class_name} {{
public:
    double input = 0.0;
    double output = 0.0;
    double Kp = {kp};
    double Ki = {ki};
    double Kd = {kd};
    double N = {n};  // Derivative filter coefficient

    // Integrator state [value, derivative]
    double integrator[2] = {{0.0, 0.0}};
    double x0_int = 0.0;  // RK x0 storage
    double xd0_int = 0.0, xd1_int = 0.0, xd2_int = 0.0, xd3_int = 0.0;

    // Derivative filter state
    double deriv_state[2] = {{0.0, 0.0}};
    double x0_der = 0.0;  // RK x0 storage
    double xd0_der = 0.0, xd1_der = 0.0, xd2_der = 0.0, xd3_der = 0.0;

    void init() {{
        integrator[0] = integrator[1] = 0.0;
        deriv_state[0] = deriv_state[1] = 0.0;
        x0_int = 0.0;
        x0_der = 0.0;
        output = 0.0;
    }}

    void update(double t) {{
        (void)t;
        double error = input;

        // P term
        double p_term = Kp * error;

        // I term
        integrator[1] = error;
        double i_term = Ki * integrator[0];

        // D term (filtered derivative)
        deriv_state[1] = N * (error - deriv_state[0]);
        double d_term = Kd * deriv_state[1];

        output = p_term + i_term + d_term;
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output;
    }}

    void propagate_states(double dt, int kpass, const std::string& method) {{
        // Propagate integrator state
        propagate_integrator(
            integrator[0],
            x0_int, xd0_int, xd1_int, xd2_int, xd3_int,
            integrator[1],
            dt, kpass, method
        );
        // Propagate derivative filter state
        propagate_integrator(
            deriv_state[0],
            x0_der, xd0_der, xd1_der, xd2_der, xd3_der,
            deriv_state[1],
            dt, kpass, method
        );
    }}
}};
"""


def pi_controller_template(block: BlockInfo, class_name: str) -> str:
    """Generate PI controller block code."""
    kp = block.parameters.get("Kp", 1.0)
    ki = block.parameters.get("Ki", 1.0)
    initial = block.parameters.get(
        "initialIntegrator", block.parameters.get("initial_integrator", 0.0)
    )
    return f"""
// {block.name} - PI Controller
class {class_name} {{
public:
    double input = 0.0;
    double output = 0.0;
    double Kp = {kp};
    double Ki = {ki};
    double initial_integrator = {initial};

    // Integrator state [value, derivative]
    double integrator[2] = {{{initial}, 0.0}};
    double x0 = {initial};
    double xd0 = 0.0, xd1 = 0.0, xd2 = 0.0, xd3 = 0.0;

    void init() {{
        integrator[0] = initial_integrator;
        integrator[1] = 0.0;
        x0 = initial_integrator;
        output = 0.0;
    }}

    void update(double t) {{
        (void)t;
        double error = input;
        integrator[1] = error;

        double p_term = Kp * error;
        double i_term = Ki * integrator[0];

        output = p_term + i_term;
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output;
    }}

    void propagate_states(double dt, int kpass, const std::string& method) {{
        propagate_integrator(
            integrator[0], x0, xd0, xd1, xd2, xd3,
            integrator[1], dt, kpass, method
        );
    }}
}};
"""


def pd_controller_template(block: BlockInfo, class_name: str) -> str:
    """Generate PD controller block code."""
    kp = block.parameters.get("Kp", 1.0)
    kd = block.parameters.get("Kd", 1.0)
    n = block.parameters.get("N", 100.0)
    return f"""
// {block.name} - PD Controller
class {class_name} {{
public:
    double input = 0.0;
    double output = 0.0;
    double Kp = {kp};
    double Kd = {kd};
    double N = {n};  // Derivative filter coefficient

    // Derivative filter state [value, derivative]
    double deriv_state[2] = {{0.0, 0.0}};
    double x0 = 0.0;
    double xd0 = 0.0, xd1 = 0.0, xd2 = 0.0, xd3 = 0.0;

    void init() {{
        deriv_state[0] = deriv_state[1] = 0.0;
        x0 = 0.0;
        output = 0.0;
    }}

    void update(double t) {{
        (void)t;
        double error = input;

        // Filtered derivative
        deriv_state[1] = N * (error - deriv_state[0]);
        double d_term = Kd * deriv_state[1];

        output = Kp * error + d_term;
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output;
    }}

    void propagate_states(double dt, int kpass, const std::string& method) {{
        propagate_integrator(
            deriv_state[0], x0, xd0, xd1, xd2, xd3,
            deriv_state[1], dt, kpass, method
        );
    }}
}};
"""


def anti_windup_pid_template(block: BlockInfo, class_name: str) -> str:
    """Generate Anti-windup PID controller block code."""
    kp = block.parameters.get("Kp", 1.0)
    ki = block.parameters.get("Ki", 1.0)
    kd = block.parameters.get("Kd", 0.0)
    n = block.parameters.get("N", 100.0)
    # Support both camelCase (JSON) and snake_case parameter names
    upper = block.parameters.get("upperLimit", block.parameters.get("upper_limit", 1e30))
    lower = block.parameters.get("lowerLimit", block.parameters.get("lower_limit", -1e30))
    kb = block.parameters.get("Kb", 1.0)
    return f"""
// {block.name} - Anti-windup PID Controller
class {class_name} {{
public:
    double input = 0.0;
    double output = 0.0;
    double Kp = {kp};
    double Ki = {ki};
    double Kd = {kd};
    double N = {n};
    double upper_limit = {upper};
    double lower_limit = {lower};
    double Kb = {kb};  // Back-calculation gain

    // Integrator state
    double integrator[2] = {{0.0, 0.0}};
    double xd0_int = 0.0, xd1_int = 0.0, xd2_int = 0.0, xd3_int = 0.0;

    // Derivative filter state
    double deriv_state[2] = {{0.0, 0.0}};
    double xd0_der = 0.0, xd1_der = 0.0, xd2_der = 0.0, xd3_der = 0.0;

    void init() {{
        integrator[0] = integrator[1] = 0.0;
        deriv_state[0] = deriv_state[1] = 0.0;
        output = 0.0;
    }}

    void update(double t) {{
        (void)t;
        double error = input;

        // P term
        double p_term = Kp * error;

        // I term
        double i_term = Ki * integrator[0];

        // D term (filtered)
        deriv_state[1] = N * (error - deriv_state[0]);
        double d_term = Kd * deriv_state[1];

        // Unsaturated output
        double u_unsat = p_term + i_term + d_term;

        // Saturate output
        double u_sat = std::clamp(u_unsat, lower_limit, upper_limit);
        output = u_sat;

        // Back-calculation
        double saturation_error = u_sat - u_unsat;
        integrator[1] = error + Kb * saturation_error;
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output;
    }}
}};
"""


def lead_lag_compensator_template(block: BlockInfo, class_name: str) -> str:
    """Generate Lead-Lag compensator block code."""
    gain = block.parameters.get("gain", 1.0)
    zero = block.parameters.get("zero", -1.0)
    pole = block.parameters.get("pole", -10.0)
    return f"""
// {block.name} - Lead-Lag Compensator: K * (s + z) / (s + p)
class {class_name} {{
public:
    double input = 0.0;
    double output = 0.0;
    double gain = {gain};
    double zero = {zero};
    double pole = {pole};

    // State [value, derivative]
    double x[2] = {{0.0, 0.0}};
    double xd0 = 0.0, xd1 = 0.0, xd2 = 0.0, xd3 = 0.0;

    void init() {{
        x[0] = x[1] = 0.0;
        output = 0.0;
    }}

    void update(double t) {{
        (void)t;
        // State equation: x' = -p*x + u
        x[1] = -pole * x[0] + input;
        // Output: y = K*(z-p)*x + K*u
        output = gain * (zero - pole) * x[0] + gain * input;
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output;
    }}
}};
"""


def lqr_controller_template(block: BlockInfo, class_name: str) -> str:
    """Generate LQR controller block code."""
    K = block.parameters.get("K", [[1.0]])
    # Infer dimensions from K matrix if not explicitly provided
    num_inputs = block.parameters.get("num_inputs", len(K))
    num_states = block.parameters.get("num_states", len(K[0]) if K else 1)

    # Format K matrix initialization
    k_init_rows = []
    for i in range(num_inputs):
        row_vals = []
        for j in range(num_states):
            val = K[i][j] if i < len(K) and j < len(K[i]) else 0.0
            row_vals.append(str(val))
        k_init_rows.append("{" + ", ".join(row_vals) + "}")
    k_init = "{" + ", ".join(k_init_rows) + "}"

    return f"""
// {block.name} - LQR Controller: u = -K*x
#include <array>

class {class_name} {{
public:
    static constexpr int NUM_STATES = {num_states};
    static constexpr int NUM_INPUTS = {num_inputs};

    std::array<double, NUM_STATES> input = {{}};  // State vector input
    std::array<double, NUM_INPUTS> output = {{}};
    double K[NUM_INPUTS][NUM_STATES] = {k_init};

    void init() {{
        input.fill(0.0);
        output.fill(0.0);
    }}

    void update(double t) {{
        (void)t;
        // u = -K * x
        for (int i = 0; i < NUM_INPUTS; i++) {{
            double u = 0.0;
            for (int j = 0; j < NUM_STATES; j++) {{
                u -= K[i][j] * input[j];
            }}
            output[i] = u;
        }}
    }}

    double get_output(int port = 0) const {{
        if (port >= 0 && port < NUM_INPUTS) {{
            return output[port];
        }}
        return 0.0;
    }}
}};
"""


def pole_placement_template(block: BlockInfo, class_name: str) -> str:
    """Generate Pole Placement controller block code."""
    K = block.parameters.get("K", [1.0])
    # Infer dimensions from K vector if not explicitly provided
    num_states = block.parameters.get("num_states", len(K) if isinstance(K, list) else 1)

    # Format K vector initialization
    k_vals = [str(K[i]) if i < len(K) else "0.0" for i in range(num_states)]
    k_init = "{" + ", ".join(k_vals) + "}"

    return f"""
// {block.name} - Pole Placement Controller: u = -K*x
#include <array>

class {class_name} {{
public:
    static constexpr int NUM_STATES = {num_states};

    std::array<double, NUM_STATES> input = {{}};  // State vector input
    double output = 0.0;
    double K[NUM_STATES] = {k_init};

    void init() {{
        input.fill(0.0);
        output = 0.0;
    }}

    void update(double t) {{
        (void)t;
        // u = -K * x (SISO)
        double u = 0.0;
        for (int i = 0; i < NUM_STATES; i++) {{
            u -= K[i] * input[i];
        }}
        output = u;
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output;
    }}
}};
"""


def model_reference_template(block: BlockInfo, class_name: str) -> str:
    """Generate Model Reference block code."""
    wn = block.parameters.get(
        "naturalFrequency", block.parameters.get("natural_frequency", 1.0)
    )
    zeta = block.parameters.get("dampingRatio", block.parameters.get("damping_ratio", 1.0))
    return f"""
// {block.name} - Model Reference: wn^2 / (s^2 + 2*zeta*wn*s + wn^2)
class {class_name} {{
public:
    double input = 0.0;
    double output = 0.0;
    double wn = {wn};
    double zeta = {zeta};

    // States [value, derivative]
    double x1[2] = {{0.0, 0.0}};
    double x2[2] = {{0.0, 0.0}};
    double x0_1 = 0.0, x0_2 = 0.0;
    double xd0_1 = 0.0, xd1_1 = 0.0, xd2_1 = 0.0, xd3_1 = 0.0;
    double xd0_2 = 0.0, xd1_2 = 0.0, xd2_2 = 0.0, xd3_2 = 0.0;

    void init() {{
        x1[0] = x1[1] = 0.0;
        x2[0] = x2[1] = 0.0;
        x0_1 = x0_2 = 0.0;
        output = 0.0;
    }}

    void update(double t) {{
        (void)t;
        double wn2 = wn * wn;

        x1[1] = x2[0];
        x2[1] = -wn2 * x1[0] - 2.0 * zeta * wn * x2[0] + wn2 * input;

        output = x1[0];
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output;
    }}

    void propagate_states(double dt, int kpass, const std::string& method) {{
        propagate_integrator(
            x1[0], x0_1, xd0_1, xd1_1, xd2_1, xd3_1,
            x1[1], dt, kpass, method
        );
        propagate_integrator(
            x2[0], x0_2, xd0_2, xd1_2, xd2_2, xd3_2,
            x2[1], dt, kpass, method
        );
    }}
}};
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
