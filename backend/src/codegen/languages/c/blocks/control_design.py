"""C templates for control design blocks."""

from ....models import BlockInfo


def pid_controller_template(block: BlockInfo, struct_name: str) -> str:
    """Generate PID controller block code."""
    kp = block.parameters.get("Kp", 1.0)
    ki = block.parameters.get("Ki", 1.0)
    kd = block.parameters.get("Kd", 0.0)
    n = block.parameters.get("N", 100.0)
    return f"""
// {block.name} - PID Controller
typedef struct {{
    double input;
    double output;
    double Kp, Ki, Kd, N;
    // Integrator state [value, derivative]
    double integrator[2];
    double xd0_int, xd1_int, xd2_int, xd3_int;
    // Derivative filter state
    double deriv_state[2];
    double xd0_der, xd1_der, xd2_der, xd3_der;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
    b->Kp = {kp};
    b->Ki = {ki};
    b->Kd = {kd};
    b->N = {n};
    b->integrator[0] = 0.0;
    b->integrator[1] = 0.0;
    b->deriv_state[0] = 0.0;
    b->deriv_state[1] = 0.0;
    b->xd0_int = b->xd1_int = b->xd2_int = b->xd3_int = 0.0;
    b->xd0_der = b->xd1_der = b->xd2_der = b->xd3_der = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    double error = b->input;

    // P term
    double p_term = b->Kp * error;

    // I term
    b->integrator[1] = error;
    double i_term = b->Ki * b->integrator[0];

    // D term (filtered derivative)
    b->deriv_state[1] = b->N * (error - b->deriv_state[0]);
    double d_term = b->Kd * b->deriv_state[1];

    b->output = p_term + i_term + d_term;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}

void {struct_name}_propagate_states({struct_name}* b, double dt, int kpass, const char* method) {{
    // Propagate integrator state
    propagate_integrator(
        &b->integrator[0],
        &b->xd0_int, &b->xd1_int, &b->xd2_int, &b->xd3_int,
        b->integrator[1],
        dt, kpass, method
    );
    // Propagate derivative filter state
    propagate_integrator(
        &b->deriv_state[0],
        &b->xd0_der, &b->xd1_der, &b->xd2_der, &b->xd3_der,
        b->deriv_state[1],
        dt, kpass, method
    );
}}
"""


def pi_controller_template(block: BlockInfo, struct_name: str) -> str:
    """Generate PI controller block code."""
    kp = block.parameters.get("Kp", 1.0)
    ki = block.parameters.get("Ki", 1.0)
    initial = block.parameters.get("initial_integrator", 0.0)
    return f"""
// {block.name} - PI Controller
typedef struct {{
    double input;
    double output;
    double Kp, Ki;
    double initial_integrator;
    // Integrator state [value, derivative]
    double integrator[2];
    double xd0, xd1, xd2, xd3;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
    b->Kp = {kp};
    b->Ki = {ki};
    b->initial_integrator = {initial};
    b->integrator[0] = {initial};
    b->integrator[1] = 0.0;
    b->xd0 = b->xd1 = b->xd2 = b->xd3 = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    double error = b->input;
    b->integrator[1] = error;

    double p_term = b->Kp * error;
    double i_term = b->Ki * b->integrator[0];

    b->output = p_term + i_term;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def pd_controller_template(block: BlockInfo, struct_name: str) -> str:
    """Generate PD controller block code."""
    kp = block.parameters.get("Kp", 1.0)
    kd = block.parameters.get("Kd", 1.0)
    n = block.parameters.get("N", 100.0)
    return f"""
// {block.name} - PD Controller
typedef struct {{
    double input;
    double output;
    double Kp, Kd, N;
    // Derivative filter state [value, derivative]
    double deriv_state[2];
    double xd0, xd1, xd2, xd3;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
    b->Kp = {kp};
    b->Kd = {kd};
    b->N = {n};
    b->deriv_state[0] = 0.0;
    b->deriv_state[1] = 0.0;
    b->xd0 = b->xd1 = b->xd2 = b->xd3 = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    double error = b->input;

    // Filtered derivative
    b->deriv_state[1] = b->N * (error - b->deriv_state[0]);
    double d_term = b->Kd * b->deriv_state[1];

    b->output = b->Kp * error + d_term;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def anti_windup_pid_template(block: BlockInfo, struct_name: str) -> str:
    """Generate Anti-windup PID controller block code."""
    kp = block.parameters.get("Kp", 1.0)
    ki = block.parameters.get("Ki", 1.0)
    kd = block.parameters.get("Kd", 0.0)
    n = block.parameters.get("N", 100.0)
    upper = block.parameters.get("upper_limit", 1e30)
    lower = block.parameters.get("lower_limit", -1e30)
    kb = block.parameters.get("Kb", 1.0)
    return f"""
// {block.name} - Anti-windup PID Controller
typedef struct {{
    double input;
    double output;
    double Kp, Ki, Kd, N;
    double upper_limit, lower_limit;
    double Kb;  // Back-calculation gain
    // Integrator state
    double integrator[2];
    double xd0_int, xd1_int, xd2_int, xd3_int;
    // Derivative filter state
    double deriv_state[2];
    double xd0_der, xd1_der, xd2_der, xd3_der;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
    b->Kp = {kp};
    b->Ki = {ki};
    b->Kd = {kd};
    b->N = {n};
    b->upper_limit = {upper};
    b->lower_limit = {lower};
    b->Kb = {kb};
    b->integrator[0] = b->integrator[1] = 0.0;
    b->deriv_state[0] = b->deriv_state[1] = 0.0;
    b->xd0_int = b->xd1_int = b->xd2_int = b->xd3_int = 0.0;
    b->xd0_der = b->xd1_der = b->xd2_der = b->xd3_der = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    double error = b->input;

    // P term
    double p_term = b->Kp * error;

    // I term
    double i_term = b->Ki * b->integrator[0];

    // D term (filtered)
    b->deriv_state[1] = b->N * (error - b->deriv_state[0]);
    double d_term = b->Kd * b->deriv_state[1];

    // Unsaturated output
    double u_unsat = p_term + i_term + d_term;

    // Saturate output
    double u_sat = u_unsat;
    if (u_sat > b->upper_limit) u_sat = b->upper_limit;
    if (u_sat < b->lower_limit) u_sat = b->lower_limit;
    b->output = u_sat;

    // Back-calculation
    double saturation_error = u_sat - u_unsat;
    b->integrator[1] = error + b->Kb * saturation_error;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def lead_lag_compensator_template(block: BlockInfo, struct_name: str) -> str:
    """Generate Lead-Lag compensator block code."""
    gain = block.parameters.get("gain", 1.0)
    zero = block.parameters.get("zero", -1.0)
    pole = block.parameters.get("pole", -10.0)
    return f"""
// {block.name} - Lead-Lag Compensator: K * (s + z) / (s + p)
typedef struct {{
    double input;
    double output;
    double gain;
    double zero;
    double pole;
    // State [value, derivative]
    double x[2];
    double xd0, xd1, xd2, xd3;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
    b->gain = {gain};
    b->zero = {zero};
    b->pole = {pole};
    b->x[0] = 0.0;
    b->x[1] = 0.0;
    b->xd0 = b->xd1 = b->xd2 = b->xd3 = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    // State equation: x' = -p*x + u
    b->x[1] = -b->pole * b->x[0] + b->input;
    // Output: y = K*(z-p)*x + K*u
    b->output = b->gain * (b->zero - b->pole) * b->x[0] + b->gain * b->input;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def lqr_controller_template(block: BlockInfo, struct_name: str) -> str:
    """Generate LQR controller block code."""
    K = block.parameters.get("K", [[1.0]])
    num_states = block.parameters.get("num_states", 1)
    num_inputs = block.parameters.get("num_inputs", 1)

    # Format K matrix initialization
    k_init = ""
    for i in range(num_inputs):
        for j in range(num_states):
            val = K[i][j] if i < len(K) and j < len(K[i]) else 0.0
            k_init += f"    b->K[{i}][{j}] = {val};\n"

    return f"""
// {block.name} - LQR Controller: u = -K*x
#define {struct_name.upper()}_NUM_STATES {num_states}
#define {struct_name.upper()}_NUM_INPUTS {num_inputs}

typedef struct {{
    double input;
    double output[{struct_name.upper()}_NUM_INPUTS];
    double state[{struct_name.upper()}_NUM_STATES];
    double K[{struct_name.upper()}_NUM_INPUTS][{struct_name.upper()}_NUM_STATES];
    int num_states;
    int num_inputs;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->num_states = {num_states};
    b->num_inputs = {num_inputs};
    for (int i = 0; i < {num_states}; i++) b->state[i] = 0.0;
    for (int i = 0; i < {num_inputs}; i++) b->output[i] = 0.0;
{k_init}}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    // u = -K * x
    for (int i = 0; i < b->num_inputs; i++) {{
        double u = 0.0;
        for (int j = 0; j < b->num_states; j++) {{
            u -= b->K[i][j] * b->state[j];
        }}
        b->output[i] = u;
    }}
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    if (port >= 0 && port < b->num_inputs) {{
        return b->output[port];
    }}
    return 0.0;
}}
"""


def pole_placement_template(block: BlockInfo, struct_name: str) -> str:
    """Generate Pole Placement controller block code."""
    K = block.parameters.get("K", [1.0])
    num_states = block.parameters.get("num_states", 1)

    # Format K vector initialization
    k_init = ""
    for i in range(num_states):
        val = K[i] if i < len(K) else 0.0
        k_init += f"    b->K[{i}] = {val};\n"

    return f"""
// {block.name} - Pole Placement Controller: u = -K*x
#define {struct_name.upper()}_NUM_STATES {num_states}

typedef struct {{
    double input;
    double output;
    double state[{struct_name.upper()}_NUM_STATES];
    double K[{struct_name.upper()}_NUM_STATES];
    int num_states;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
    b->num_states = {num_states};
    for (int i = 0; i < {num_states}; i++) b->state[i] = 0.0;
{k_init}}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    // u = -K * x (SISO)
    double u = 0.0;
    for (int i = 0; i < b->num_states; i++) {{
        u -= b->K[i] * b->state[i];
    }}
    b->output = u;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def model_reference_template(block: BlockInfo, struct_name: str) -> str:
    """Generate Model Reference block code."""
    wn = block.parameters.get("natural_frequency", 1.0)
    zeta = block.parameters.get("damping_ratio", 1.0)
    return f"""
// {block.name} - Model Reference: wn^2 / (s^2 + 2*zeta*wn*s + wn^2)
typedef struct {{
    double input;
    double output;
    double wn;
    double zeta;
    // States [value, derivative]
    double x1[2];
    double x2[2];
    double xd0_1, xd1_1, xd2_1, xd3_1;
    double xd0_2, xd1_2, xd2_2, xd3_2;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
    b->wn = {wn};
    b->zeta = {zeta};
    b->x1[0] = b->x1[1] = 0.0;
    b->x2[0] = b->x2[1] = 0.0;
    b->xd0_1 = b->xd1_1 = b->xd2_1 = b->xd3_1 = 0.0;
    b->xd0_2 = b->xd1_2 = b->xd2_2 = b->xd3_2 = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    double wn = b->wn;
    double wn2 = wn * wn;

    b->x1[1] = b->x2[0];
    b->x2[1] = -wn2 * b->x1[0] - 2.0 * b->zeta * wn * b->x2[0] + wn2 * b->input;

    b->output = b->x1[0];
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
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
