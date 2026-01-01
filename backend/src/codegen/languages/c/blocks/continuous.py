"""C block templates for continuous blocks (integrators, transfer functions, etc.)."""

from ....models import BlockInfo


def template_integrator(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Integrator block."""
    initial_condition = block.parameters.get("initial_condition", 0.0)
    return f"""
// {block.name} - Integrator
typedef struct {{
    double input;
    double output;
    double state;
    double initial_condition;
    // Integration intermediate values
    double xd0, xd1, xd2, xd3;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->initial_condition = {initial_condition};
    b->state = b->initial_condition;
    b->output = b->state;
    b->xd0 = 0.0;
    b->xd1 = 0.0;
    b->xd2 = 0.0;
    b->xd3 = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    b->output = b->state;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}

// Integration interface functions
double {struct_name}_get_derivative({struct_name}* b) {{
    return b->input;
}}

void {struct_name}_set_state({struct_name}* b, double value) {{
    b->state = value;
    b->output = value;
}}

double {struct_name}_get_state({struct_name}* b) {{
    return b->state;
}}
"""


def template_derivative(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Derivative block."""
    return f"""
// {block.name} - Derivative
typedef struct {{
    double input;
    double output;
    double prev_input;
    double prev_time;
    int first_call;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
    b->prev_input = 0.0;
    b->prev_time = 0.0;
    b->first_call = 1;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    if (b->first_call) {{
        b->output = 0.0;
        b->first_call = 0;
    }} else {{
        double dt = t - b->prev_time;
        if (dt > 0) {{
            b->output = (b->input - b->prev_input) / dt;
        }}
    }}
    b->prev_input = b->input;
    b->prev_time = t;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_transfer_function(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Transfer Function block.

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

    # State array declaration
    state_decl = f"double state[{order}];"
    xd_decl = f"double xd0[{order}], xd1[{order}], xd2[{order}], xd3[{order}];"

    # Initialize state array
    state_init = "\n    ".join([f"b->state[{i}] = 0.0;" for i in range(order)])

    # Denominator coefficients (normalized)
    a_coeffs = ", ".join([str(d / a0) for d in denominator])

    # Numerator coefficients
    b_coeffs = ", ".join([str(n / a0) for n in numerator])

    return f"""
// {block.name} - Transfer Function (order {order})
typedef struct {{
    double input;
    double output;
    {state_decl}
    {xd_decl}
    int order;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
    b->order = {order};
    {state_init}
    for (int i = 0; i < {order}; i++) {{
        b->xd0[i] = 0.0;
        b->xd1[i] = 0.0;
        b->xd2[i] = 0.0;
        b->xd3[i] = 0.0;
    }}
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    // Compute output from state (controllable canonical form)
    double a[] = {{{a_coeffs}}};
    double bcoef[] = {{{b_coeffs}}};

    // State space output
    b->output = 0.0;
    int nb = sizeof(bcoef) / sizeof(bcoef[0]);
    int na = sizeof(a) / sizeof(a[0]);

    // Direct feedthrough term
    if (nb > 0 && na > 0) {{
        b->output = bcoef[0] * b->input;
    }}

    // State contribution
    for (int i = 0; i < b->order && i < nb - 1; i++) {{
        if (i + 1 < nb) {{
            b->output += bcoef[i + 1] * b->state[i];
        }}
    }}
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_state_space(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for State Space block."""
    # Get matrices with defaults
    A = block.parameters.get("A", [[0.0]])
    B = block.parameters.get("B", [[1.0]])
    C = block.parameters.get("C", [[1.0]])
    D = block.parameters.get("D", [[0.0]])
    x0 = block.parameters.get("x0", [0.0])

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

    # Format matrices as C arrays
    def format_matrix(mat, name, rows, cols):
        lines = []
        for i in range(rows):
            row_vals = []
            for j in range(cols):
                val = mat[i][j] if i < len(mat) and j < len(mat[i]) else 0.0
                row_vals.append(str(val))
            lines.append(f"    {{ {', '.join(row_vals)} }}")
        return f"double {name}[{rows}][{cols}] = {{\n" + ",\n".join(lines) + "\n    };"

    return f"""
// {block.name} - State Space (n={n_states}, m={n_inputs}, p={n_outputs})
typedef struct {{
    double input[{n_inputs}];
    double output[{n_outputs}];
    double state[{n_states}];
    double xd0[{n_states}], xd1[{n_states}], xd2[{n_states}], xd3[{n_states}];
    int n_states;
    int n_inputs;
    int n_outputs;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->n_states = {n_states};
    b->n_inputs = {n_inputs};
    b->n_outputs = {n_outputs};
    for (int i = 0; i < {n_states}; i++) {{
        b->state[i] = 0.0;
        b->xd0[i] = 0.0;
        b->xd1[i] = 0.0;
        b->xd2[i] = 0.0;
        b->xd3[i] = 0.0;
    }}
    for (int i = 0; i < {n_inputs}; i++) b->input[i] = 0.0;
    for (int i = 0; i < {n_outputs}; i++) b->output[i] = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    // System matrices
    double A[{n_states}][{n_states}];
    double B[{n_states}][{n_inputs}];
    double C[{n_outputs}][{n_states}];
    double D[{n_outputs}][{n_inputs}];

    // Initialize matrices (simplified - actual values should be set)
    for (int i = 0; i < {n_states}; i++)
        for (int j = 0; j < {n_states}; j++) A[i][j] = 0.0;
    for (int i = 0; i < {n_states}; i++)
        for (int j = 0; j < {n_inputs}; j++) B[i][j] = 0.0;
    for (int i = 0; i < {n_outputs}; i++)
        for (int j = 0; j < {n_states}; j++) C[i][j] = 0.0;
    for (int i = 0; i < {n_outputs}; i++)
        for (int j = 0; j < {n_inputs}; j++) D[i][j] = 0.0;

    // Output: y = Cx + Du
    for (int i = 0; i < b->n_outputs; i++) {{
        b->output[i] = 0.0;
        for (int j = 0; j < b->n_states; j++) {{
            b->output[i] += C[i][j] * b->state[j];
        }}
        for (int j = 0; j < b->n_inputs; j++) {{
            b->output[i] += D[i][j] * b->input[j];
        }}
    }}
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    if (port >= 0 && port < b->n_outputs) {{
        return b->output[port];
    }}
    return 0.0;
}}
"""


def template_second_order(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Second Order Integrator block."""
    wn = block.parameters.get("natural_frequency", 1.0)
    zeta = block.parameters.get("damping_ratio", 0.7)
    ic = block.parameters.get("initial_condition", 0.0)
    ic_dot = block.parameters.get("initial_condition_derivative", 0.0)

    return f"""
// {block.name} - Second Order System (wn={wn}, zeta={zeta})
typedef struct {{
    double input;
    double output;
    double state[2];  // [position, velocity]
    double xd0[2], xd1[2], xd2[2], xd3[2];
    double wn;        // Natural frequency
    double zeta;      // Damping ratio
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->wn = {wn};
    b->zeta = {zeta};
    b->state[0] = {ic};      // Initial position
    b->state[1] = {ic_dot};  // Initial velocity
    b->output = b->state[0];
    for (int i = 0; i < 2; i++) {{
        b->xd0[i] = 0.0;
        b->xd1[i] = 0.0;
        b->xd2[i] = 0.0;
        b->xd3[i] = 0.0;
    }}
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    b->output = b->state[0];
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}

// Integration: x'' + 2*zeta*wn*x' + wn^2*x = wn^2*u
// State: x1 = x, x2 = x'
// x1' = x2
// x2' = wn^2*u - 2*zeta*wn*x2 - wn^2*x1
"""


def template_transport_delay(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Transport Delay block."""
    delay = block.parameters.get("delay", 1.0)
    buffer_size = block.parameters.get("buffer_size", 1024)
    initial_output = block.parameters.get("initial_output", 0.0)

    return f"""
// {block.name} - Transport Delay ({delay}s)
#define {struct_name.upper()}_BUFFER_SIZE {buffer_size}

typedef struct {{
    double input;
    double output;
    double buffer[{struct_name.upper()}_BUFFER_SIZE];
    double time_buffer[{struct_name.upper()}_BUFFER_SIZE];
    int write_idx;
    int count;
    double delay;
    double initial_output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = {initial_output};
    b->delay = {delay};
    b->initial_output = {initial_output};
    b->write_idx = 0;
    b->count = 0;
    for (int i = 0; i < {struct_name.upper()}_BUFFER_SIZE; i++) {{
        b->buffer[i] = {initial_output};
        b->time_buffer[i] = -1e10;
    }}
}}

void {struct_name}_update({struct_name}* b, double t) {{
    // Store current value
    b->buffer[b->write_idx] = b->input;
    b->time_buffer[b->write_idx] = t;
    b->write_idx = (b->write_idx + 1) % {struct_name.upper()}_BUFFER_SIZE;
    if (b->count < {struct_name.upper()}_BUFFER_SIZE) b->count++;

    // Find delayed value (linear interpolation)
    double target_time = t - b->delay;
    if (target_time < 0) {{
        b->output = b->initial_output;
        return;
    }}

    // Search for bracketing times
    int found = 0;
    for (int i = 0; i < b->count - 1; i++) {{
        int idx0 = (b->write_idx - b->count + i + {struct_name.upper()}_BUFFER_SIZE) % {struct_name.upper()}_BUFFER_SIZE;
        int idx1 = (idx0 + 1) % {struct_name.upper()}_BUFFER_SIZE;
        if (b->time_buffer[idx0] <= target_time && b->time_buffer[idx1] >= target_time) {{
            double alpha = (target_time - b->time_buffer[idx0]) /
                          (b->time_buffer[idx1] - b->time_buffer[idx0] + 1e-10);
            b->output = b->buffer[idx0] + alpha * (b->buffer[idx1] - b->buffer[idx0]);
            found = 1;
            break;
        }}
    }}
    if (!found) {{
        b->output = b->initial_output;
    }}
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
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
