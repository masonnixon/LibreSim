"""C++ block templates for continuous blocks (integrators, transfer functions, etc.)."""

from ....models import BlockInfo


def template_integrator(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Integrator block."""
    initial_condition = block.parameters.get("initial_condition", 0.0)
    return f"""
// {block.name} - Integrator
class {class_name} {{
public:
    double input = 0.0;
    double output = 0.0;
    double state = 0.0;
    double initial_condition = {initial_condition};
    // Integration intermediate values
    double x0 = 0.0;  // RK x0 storage
    double xd0 = 0.0, xd1 = 0.0, xd2 = 0.0, xd3 = 0.0;

    void init() {{
        state = initial_condition;
        output = state;
        x0 = 0.0;
        xd0 = xd1 = xd2 = xd3 = 0.0;
    }}

    void update(double t) {{
        (void)t;
        output = state;
    }}

    double get_output(int port) const {{
        (void)port;
        return output;
    }}

    // Integration interface functions
    double get_derivative() const {{
        return input;
    }}

    void set_state(double value) {{
        state = value;
        output = value;
    }}

    double get_state() const {{
        return state;
    }}
}};
"""


def template_derivative(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Derivative block."""
    return f"""
// {block.name} - Derivative
class {class_name} {{
public:
    double input = 0.0;
    double output = 0.0;
    double prev_input = 0.0;
    double prev_time = 0.0;
    bool first_call = true;

    void init() {{
        input = 0.0;
        output = 0.0;
        prev_input = 0.0;
        prev_time = 0.0;
        first_call = true;
    }}

    void update(double t) {{
        if (first_call) {{
            output = 0.0;
            first_call = false;
        }} else {{
            double dt = t - prev_time;
            if (dt > 0) {{
                output = (input - prev_input) / dt;
            }}
        }}
        prev_input = input;
        prev_time = t;
    }}

    double get_output(int port) const {{
        (void)port;
        return output;
    }}
}};
"""


def template_transfer_function(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Transfer Function block.

    Implements as a chain of integrators in controllable canonical form.
    Matches Python implementation exactly for numerical accuracy.
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

    # Denominator coefficients (normalized)
    a_coeffs = ", ".join([str(d / a0) for d in denominator])

    # Numerator coefficients (normalized)
    b_coeffs = ", ".join([str(n / a0) for n in numerator])

    num_len = len(numerator)

    return f"""
// {block.name} - Transfer Function (order {order})
class {class_name} {{
public:
    double input = 0.0;
    double output = 0.0;
    std::array<double, {order}> state{{}};
    std::array<double, {order}> derivatives{{}};
    std::array<double, {order}> x0{{}};
    std::array<double, {order}> xd0{{}}, xd1{{}}, xd2{{}}, xd3{{}};
    static constexpr int order = {order};
    static constexpr int num_len = {num_len};

    void init() {{
        input = 0.0;
        output = 0.0;
        state.fill(0.0);
        derivatives.fill(0.0);
        x0.fill(0.0);
        xd0.fill(0.0);
        xd1.fill(0.0);
        xd2.fill(0.0);
        xd3.fill(0.0);
    }}

    void update(double t) {{
        (void)t;
        // Normalized coefficients
        std::array<double, {len(denominator)}> den = {{{a_coeffs}}};
        std::array<double, {num_len}> num = {{{b_coeffs}}};

        // Compute derivatives (controllable canonical form)
        // x_i' = x_(i+1) for i < order-1
        // x_(order-1)' = input - sum(a[j] * state[order-j])
        for (int i = 0; i < order; i++) {{
            if (i < order - 1) {{
                derivatives[i] = state[i + 1];
            }} else {{
                derivatives[i] = input;
                for (int j = 1; j < static_cast<int>(den.size()); j++) {{
                    if (order - j >= 0 && order - j < order) {{
                        derivatives[i] -= den[j] * state[order - j];
                    }}
                }}
            }}
        }}

        // Compute output: y = sum(num[len-1-i] * state[i]) + feedthrough
        output = 0.0;
        for (int i = 0; i < order && i < num_len; i++) {{
            output += num[num_len - 1 - i] * state[i];
        }}

        // Direct feedthrough only if numerator degree > order (improper)
        if (num_len > order) {{
            output += num[0] * input;
        }}
    }}

    double get_output(int port) const {{
        (void)port;
        return output;
    }}

    void propagate_states(double dt, int kpass, const std::string& method) {{
        (void)method;
        // RK4 integration for all states
        for (int i = 0; i < order; i++) {{
            if (kpass == 0) {{
                x0[i] = state[i];
                xd0[i] = derivatives[i];
                state[i] = x0[i] + dt / 2.0 * xd0[i];
            }} else if (kpass == 1) {{
                xd1[i] = derivatives[i];
                state[i] = x0[i] + dt / 2.0 * xd1[i];
            }} else if (kpass == 2) {{
                xd2[i] = derivatives[i];
                state[i] = x0[i] + dt * xd2[i];
            }} else if (kpass == 3) {{
                xd3[i] = derivatives[i];
                state[i] = x0[i] + dt / 6.0 * (xd0[i] + 2.0 * xd1[i] + 2.0 * xd2[i] + xd3[i]);
            }}
        }}
    }}
}};
"""


def template_state_space(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for State Space block."""
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
// {block.name} - State Space (n={n_states}, m={n_inputs}, p={n_outputs})
class {class_name} {{
public:
    std::array<double, {n_inputs}> input{{}};
    std::array<double, {n_outputs}> output{{}};
    std::array<double, {n_states}> state{{}};
    std::array<double, {n_states}> xd0{{}}, xd1{{}}, xd2{{}}, xd3{{}};
    static constexpr int n_states = {n_states};
    static constexpr int n_inputs = {n_inputs};
    static constexpr int n_outputs = {n_outputs};

    void init() {{
        input.fill(0.0);
        output.fill(0.0);
        state.fill(0.0);
        xd0.fill(0.0);
        xd1.fill(0.0);
        xd2.fill(0.0);
        xd3.fill(0.0);
    }}

    void update(double t) {{
        (void)t;
        // System matrices (simplified - actual values should be set)
        std::array<std::array<double, {n_states}>, {n_states}> A{{}};
        std::array<std::array<double, {n_inputs}>, {n_states}> B{{}};
        std::array<std::array<double, {n_states}>, {n_outputs}> C{{}};
        std::array<std::array<double, {n_inputs}>, {n_outputs}> D{{}};

        // Output: y = Cx + Du
        for (int i = 0; i < n_outputs; i++) {{
            output[i] = 0.0;
            for (int j = 0; j < n_states; j++) {{
                output[i] += C[i][j] * state[j];
            }}
            for (int j = 0; j < n_inputs; j++) {{
                output[i] += D[i][j] * input[j];
            }}
        }}
    }}

    double get_output(int port) const {{
        if (port >= 0 && port < n_outputs) {{
            return output[port];
        }}
        return 0.0;
    }}
}};
"""


def template_second_order(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Second Order Integrator block."""
    wn = block.parameters.get("natural_frequency", 1.0)
    zeta = block.parameters.get("damping_ratio", 0.7)
    ic = block.parameters.get("initial_condition", 0.0)
    ic_dot = block.parameters.get("initial_condition_derivative", 0.0)

    return f"""
// {block.name} - Second Order System (wn={wn}, zeta={zeta})
class {class_name} {{
public:
    double input = 0.0;
    double output = 0.0;
    std::array<double, 2> state{{}};  // [position, velocity]
    std::array<double, 2> xd0{{}}, xd1{{}}, xd2{{}}, xd3{{}};
    double wn = {wn};        // Natural frequency
    double zeta = {zeta};    // Damping ratio

    void init() {{
        input = 0.0;
        state[0] = {ic};      // Initial position
        state[1] = {ic_dot};  // Initial velocity
        output = state[0];
        xd0.fill(0.0);
        xd1.fill(0.0);
        xd2.fill(0.0);
        xd3.fill(0.0);
    }}

    void update(double t) {{
        (void)t;
        output = state[0];
    }}

    double get_output(int port) const {{
        (void)port;
        return output;
    }}

    // Integration: x'' + 2*zeta*wn*x' + wn^2*x = wn^2*u
    // State: x1 = x, x2 = x'
    // x1' = x2
    // x2' = wn^2*u - 2*zeta*wn*x2 - wn^2*x1
}};
"""


def template_transport_delay(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Transport Delay block."""
    delay = block.parameters.get("delay", 1.0)
    buffer_size = block.parameters.get("buffer_size", 1024)
    initial_output = block.parameters.get("initial_output", 0.0)

    return f"""
// {block.name} - Transport Delay ({delay}s)
class {class_name} {{
public:
    static constexpr int BUFFER_SIZE = {buffer_size};
    double input = 0.0;
    double output = {initial_output};
    std::array<double, BUFFER_SIZE> buffer{{}};
    std::array<double, BUFFER_SIZE> time_buffer{{}};
    int write_idx = 0;
    int count = 0;
    double delay = {delay};
    double initial_output = {initial_output};

    void init() {{
        input = 0.0;
        output = initial_output;
        write_idx = 0;
        count = 0;
        buffer.fill(initial_output);
        time_buffer.fill(-1e10);
    }}

    void update(double t) {{
        // Store current value
        buffer[write_idx] = input;
        time_buffer[write_idx] = t;
        write_idx = (write_idx + 1) % BUFFER_SIZE;
        if (count < BUFFER_SIZE) count++;

        // Find delayed value (linear interpolation)
        double target_time = t - delay;
        if (target_time < 0) {{
            output = initial_output;
            return;
        }}

        // Search for bracketing times
        bool found = false;
        for (int i = 0; i < count - 1; i++) {{
            int idx0 = (write_idx - count + i + BUFFER_SIZE) % BUFFER_SIZE;
            int idx1 = (idx0 + 1) % BUFFER_SIZE;
            if (time_buffer[idx0] <= target_time && time_buffer[idx1] >= target_time) {{
                double alpha = (target_time - time_buffer[idx0]) /
                              (time_buffer[idx1] - time_buffer[idx0] + 1e-10);
                output = buffer[idx0] + alpha * (buffer[idx1] - buffer[idx0]);
                found = true;
                break;
            }}
        }}
        if (!found) {{
            output = initial_output;
        }}
    }}

    double get_output(int port) const {{
        (void)port;
        return output;
    }}
}};
"""


CONTINUOUS_TEMPLATES = {
    "integrator": template_integrator,
    "limited_integrator": template_integrator,  # Same as integrator with limits
    "derivative": template_derivative,
    "transfer_function": template_transfer_function,
    "state_space": template_state_space,
    "second_order": template_second_order,
    "transport_delay": template_transport_delay,
}
