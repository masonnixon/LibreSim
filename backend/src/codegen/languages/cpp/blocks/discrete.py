"""C++ templates for discrete blocks."""

from ....models import BlockInfo


def unit_delay_template(block: BlockInfo, class_name: str) -> str:
    """Generate UnitDelay block code."""
    initial_condition = block.parameters.get("initialCondition", 0.0)
    sample_time = block.parameters.get("sampleTime", 0.1)

    return f"""
class {class_name} {{
public:
    double initial_condition = {initial_condition};
    double sample_time = {sample_time};
    double input = 0.0;
    double output = {initial_condition};
    double prev_value = {initial_condition};
    double last_sample_time = -std::numeric_limits<double>::infinity();

    void init() {{
        output = initial_condition;
        prev_value = initial_condition;
        last_sample_time = -std::numeric_limits<double>::infinity();
    }}

    void update(double t) {{
        if (t - last_sample_time >= sample_time - 1e-10) {{
            output = prev_value;
            prev_value = input;
            last_sample_time = t;
        }}
    }}

    double get_output(int port = 0) const {{
        return output;
    }}
}};
"""


def zero_order_hold_template(block: BlockInfo, class_name: str) -> str:
    """Generate ZeroOrderHold block code."""
    sample_time = block.parameters.get("sampleTime", 0.1)

    return f"""
class {class_name} {{
public:
    double sample_time = {sample_time};
    double input = 0.0;
    double output = 0.0;
    double held_value = 0.0;
    double last_sample_time = -std::numeric_limits<double>::infinity();

    void init() {{
        held_value = 0.0;
        output = 0.0;
        last_sample_time = -std::numeric_limits<double>::infinity();
    }}

    void update(double t) {{
        if (t - last_sample_time >= sample_time - 1e-10) {{
            held_value = input;
            last_sample_time = t;
        }}
        output = held_value;
    }}

    double get_output(int port = 0) const {{
        return output;
    }}
}};
"""


def first_order_hold_template(block: BlockInfo, class_name: str) -> str:
    """Generate FirstOrderHold block code."""
    sample_time = block.parameters.get("sampleTime", 0.1)

    return f"""
class {class_name} {{
public:
    double sample_time = {sample_time};
    double input = 0.0;
    double output = 0.0;
    double prev_value = 0.0;
    double curr_value = 0.0;
    double last_sample_time = -std::numeric_limits<double>::infinity();
    double slope = 0.0;

    void init() {{
        prev_value = 0.0;
        curr_value = 0.0;
        slope = 0.0;
        output = 0.0;
        last_sample_time = -std::numeric_limits<double>::infinity();
    }}

    void update(double t) {{
        if (t - last_sample_time >= sample_time - 1e-10) {{
            prev_value = curr_value;
            curr_value = input;
            slope = (curr_value - prev_value) / sample_time;
            last_sample_time = t;
        }}
        // Linear interpolation
        double dt = t - last_sample_time;
        output = curr_value + slope * dt;
    }}

    double get_output(int port = 0) const {{
        return output;
    }}
}};
"""


def discrete_integrator_template(block: BlockInfo, class_name: str) -> str:
    """Generate DiscreteIntegrator block code."""
    initial_condition = block.parameters.get("initialCondition", 0.0)
    sample_time = block.parameters.get("sampleTime", 0.1)
    method = block.parameters.get("method", "forward")

    # Map method to enum
    method_map = {"forward": "Forward", "backward": "Backward", "trapezoidal": "Trapezoidal"}
    method_enum = method_map.get(method, "Forward")

    return f"""
class {class_name} {{
public:
    enum class Method {{ Forward, Backward, Trapezoidal }};

    double initial_condition = {initial_condition};
    double sample_time = {sample_time};
    Method method = Method::{method_enum};
    double input = 0.0;
    double output = {initial_condition};
    double prev_input = 0.0;
    double state = {initial_condition};
    double last_sample_time = -std::numeric_limits<double>::infinity();

    void init() {{
        state = initial_condition;
        output = initial_condition;
        prev_input = 0.0;
        last_sample_time = -std::numeric_limits<double>::infinity();
    }}

    void update(double t) {{
        if (t - last_sample_time >= sample_time - 1e-10) {{
            switch (method) {{
                case Method::Forward:
                    state += sample_time * prev_input;
                    break;
                case Method::Backward:
                    state += sample_time * input;
                    break;
                case Method::Trapezoidal:
                    state += sample_time / 2.0 * (input + prev_input);
                    break;
            }}
            prev_input = input;
            last_sample_time = t;
        }}
        output = state;
    }}

    double get_output(int port = 0) const {{
        return output;
    }}
}};
"""


def discrete_derivative_template(block: BlockInfo, class_name: str) -> str:
    """Generate DiscreteDerivative block code."""
    sample_time = block.parameters.get("sampleTime", 0.1)

    return f"""
class {class_name} {{
public:
    double sample_time = {sample_time};
    double input = 0.0;
    double output = 0.0;
    double prev_input = 0.0;
    double last_sample_time = -std::numeric_limits<double>::infinity();

    void init() {{
        prev_input = 0.0;
        output = 0.0;
        last_sample_time = -std::numeric_limits<double>::infinity();
    }}

    void update(double t) {{
        if (t - last_sample_time >= sample_time - 1e-10) {{
            output = (input - prev_input) / sample_time;
            prev_input = input;
            last_sample_time = t;
        }}
    }}

    double get_output(int port = 0) const {{
        return output;
    }}
}};
"""


def discrete_transfer_function_template(block: BlockInfo, class_name: str) -> str:
    """Generate DiscreteTransferFunction block code."""
    numerator = block.parameters.get("numerator", [1.0])
    denominator = block.parameters.get("denominator", [1.0, -0.5])
    sample_time = block.parameters.get("sampleTime", 0.1)

    if not isinstance(numerator, list):
        numerator = [numerator]
    if not isinstance(denominator, list):
        denominator = [denominator]

    order = max(len(numerator), len(denominator)) - 1
    num_len = len(numerator)
    den_len = len(denominator)

    # Format arrays for C++
    num_str = ", ".join(str(n) for n in numerator)
    den_str = ", ".join(str(d) for d in denominator)

    return f"""
class {class_name} {{
public:
    static constexpr int ORDER = {order};
    std::array<double, {num_len}> numerator = {{{{{num_str}}}}};
    std::array<double, {den_len}> denominator = {{{{{den_str}}}}};
    double sample_time = {sample_time};
    double input = 0.0;
    double output = 0.0;
    std::array<double, {order + 1}> input_history = {{}};
    std::array<double, {order + 1}> output_history = {{}};
    double last_sample_time = -std::numeric_limits<double>::infinity();

    void init() {{
        input_history.fill(0.0);
        output_history.fill(0.0);
        output = 0.0;
        last_sample_time = -std::numeric_limits<double>::infinity();
    }}

    void update(double t) {{
        if (t - last_sample_time >= sample_time - 1e-10) {{
            // Shift histories
            for (int i = ORDER; i > 0; i--) {{
                input_history[i] = input_history[i - 1];
                output_history[i] = output_history[i - 1];
            }}
            input_history[0] = input;

            // Compute new output
            double a0 = denominator[0];
            double new_output = 0.0;

            for (size_t i = 0; i < numerator.size() && i < input_history.size(); i++) {{
                new_output += (numerator[i] / a0) * input_history[i];
            }}

            for (size_t i = 1; i < denominator.size() && i < output_history.size(); i++) {{
                new_output -= (denominator[i] / a0) * output_history[i];
            }}

            output_history[0] = new_output;
            output = new_output;
            last_sample_time = t;
        }}
    }}

    double get_output(int port = 0) const {{
        return output;
    }}
}};
"""


def memory_template(block: BlockInfo, class_name: str) -> str:
    """Generate Memory block code."""
    initial_condition = block.parameters.get("initialCondition", 0.0)

    return f"""
class {class_name} {{
public:
    double initial_condition = {initial_condition};
    double input = 0.0;
    double output = {initial_condition};
    double prev_value = {initial_condition};
    bool first_step = true;

    void init() {{
        prev_value = initial_condition;
        output = initial_condition;
        first_step = true;
    }}

    void update(double t) {{
        if (first_step) {{
            output = initial_condition;
            first_step = false;
        }} else {{
            output = prev_value;
        }}
        prev_value = input;
    }}

    double get_output(int port = 0) const {{
        return output;
    }}
}};
"""


# Template registry for discrete blocks
DISCRETE_TEMPLATES = {
    "unit_delay": unit_delay_template,
    "zero_order_hold": zero_order_hold_template,
    "first_order_hold": first_order_hold_template,
    "discrete_integrator": discrete_integrator_template,
    "discrete_derivative": discrete_derivative_template,
    "discrete_transfer_function": discrete_transfer_function_template,
    "memory": memory_template,
}
