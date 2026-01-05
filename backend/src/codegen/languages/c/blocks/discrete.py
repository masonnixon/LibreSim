"""C templates for discrete blocks."""

from ....models import BlockInfo


def unit_delay_template(block: BlockInfo, struct_name: str) -> str:
    """Generate UnitDelay block code."""
    initial_condition = block.parameters.get("initialCondition", 0.0)
    sample_time = block.parameters.get("sampleTime", 0.1)

    return f"""
typedef struct {{
    double initial_condition;
    double sample_time;
    double input;
    double output;
    double prev_value;
    double last_sample_time;
}} {struct_name};

void {struct_name}_init({struct_name}* self) {{
    self->initial_condition = {initial_condition};
    self->sample_time = {sample_time};
    self->input = 0.0;
    self->output = self->initial_condition;
    self->prev_value = self->initial_condition;
    self->last_sample_time = -1e308;
}}

void {struct_name}_update({struct_name}* self, double t) {{
    if (t - self->last_sample_time >= self->sample_time - 1e-10) {{
        self->output = self->prev_value;
        self->prev_value = self->input;
        self->last_sample_time = t;
    }}
}}

double {struct_name}_get_output({struct_name}* self, int port) {{
    return self->output;
}}
"""


def zero_order_hold_template(block: BlockInfo, struct_name: str) -> str:
    """Generate ZeroOrderHold block code."""
    sample_time = block.parameters.get("sampleTime", 0.1)

    return f"""
typedef struct {{
    double sample_time;
    double input;
    double output;
    double held_value;
    double last_sample_time;
}} {struct_name};

void {struct_name}_init({struct_name}* self) {{
    self->sample_time = {sample_time};
    self->input = 0.0;
    self->output = 0.0;
    self->held_value = 0.0;
    self->last_sample_time = -1e308;
}}

void {struct_name}_update({struct_name}* self, double t) {{
    if (t - self->last_sample_time >= self->sample_time - 1e-10) {{
        self->held_value = self->input;
        self->last_sample_time = t;
    }}
    self->output = self->held_value;
}}

double {struct_name}_get_output({struct_name}* self, int port) {{
    return self->output;
}}
"""


def first_order_hold_template(block: BlockInfo, struct_name: str) -> str:
    """Generate FirstOrderHold block code."""
    sample_time = block.parameters.get("sampleTime", 0.1)

    return f"""
typedef struct {{
    double sample_time;
    double input;
    double output;
    double prev_value;
    double curr_value;
    double last_sample_time;
    double slope;
}} {struct_name};

void {struct_name}_init({struct_name}* self) {{
    self->sample_time = {sample_time};
    self->input = 0.0;
    self->output = 0.0;
    self->prev_value = 0.0;
    self->curr_value = 0.0;
    self->last_sample_time = -1e308;
    self->slope = 0.0;
}}

void {struct_name}_update({struct_name}* self, double t) {{
    if (t - self->last_sample_time >= self->sample_time - 1e-10) {{
        self->prev_value = self->curr_value;
        self->curr_value = self->input;
        self->slope = (self->curr_value - self->prev_value) / self->sample_time;
        self->last_sample_time = t;
    }}
    // Linear interpolation
    double dt = t - self->last_sample_time;
    self->output = self->curr_value + self->slope * dt;
}}

double {struct_name}_get_output({struct_name}* self, int port) {{
    return self->output;
}}
"""


def discrete_integrator_template(block: BlockInfo, struct_name: str) -> str:
    """Generate DiscreteIntegrator block code."""
    initial_condition = block.parameters.get("initialCondition", 0.0)
    sample_time = block.parameters.get("sampleTime", 0.1)
    method = block.parameters.get("method", "forward")

    # Map method to integer: 0=forward, 1=backward, 2=trapezoidal
    method_map = {"forward": 0, "backward": 1, "trapezoidal": 2}
    method_int = method_map.get(method, 0)

    return f"""
typedef struct {{
    double initial_condition;
    double sample_time;
    int method;  // 0=forward, 1=backward, 2=trapezoidal
    double input;
    double output;
    double prev_input;
    double state;
    double last_sample_time;
}} {struct_name};

void {struct_name}_init({struct_name}* self) {{
    self->initial_condition = {initial_condition};
    self->sample_time = {sample_time};
    self->method = {method_int};
    self->input = 0.0;
    self->output = self->initial_condition;
    self->prev_input = 0.0;
    self->state = self->initial_condition;
    self->last_sample_time = -1e308;
}}

void {struct_name}_update({struct_name}* self, double t) {{
    if (t - self->last_sample_time >= self->sample_time - 1e-10) {{
        switch (self->method) {{
            case 0:  // forward
                self->state += self->sample_time * self->prev_input;
                break;
            case 1:  // backward
                self->state += self->sample_time * self->input;
                break;
            case 2:  // trapezoidal
                self->state += self->sample_time / 2.0 * (self->input + self->prev_input);
                break;
        }}
        self->prev_input = self->input;
        self->last_sample_time = t;
    }}
    self->output = self->state;
}}

double {struct_name}_get_output({struct_name}* self, int port) {{
    return self->output;
}}
"""


def discrete_derivative_template(block: BlockInfo, struct_name: str) -> str:
    """Generate DiscreteDerivative block code."""
    sample_time = block.parameters.get("sampleTime", 0.1)

    return f"""
typedef struct {{
    double sample_time;
    double input;
    double output;
    double prev_input;
    double last_sample_time;
}} {struct_name};

void {struct_name}_init({struct_name}* self) {{
    self->sample_time = {sample_time};
    self->input = 0.0;
    self->output = 0.0;
    self->prev_input = 0.0;
    self->last_sample_time = -1e308;
}}

void {struct_name}_update({struct_name}* self, double t) {{
    if (t - self->last_sample_time >= self->sample_time - 1e-10) {{
        self->output = (self->input - self->prev_input) / self->sample_time;
        self->prev_input = self->input;
        self->last_sample_time = t;
    }}
}}

double {struct_name}_get_output({struct_name}* self, int port) {{
    return self->output;
}}
"""


def discrete_transfer_function_template(block: BlockInfo, struct_name: str) -> str:
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

    # Format arrays for C
    num_str = ", ".join(str(n) for n in numerator)
    den_str = ", ".join(str(d) for d in denominator)

    return f"""
#define {struct_name}_ORDER {order}
#define {struct_name}_NUM_LEN {num_len}
#define {struct_name}_DEN_LEN {den_len}

typedef struct {{
    double numerator[{num_len}];
    double denominator[{den_len}];
    double sample_time;
    int order;
    double input;
    double output;
    double input_history[{order + 1}];
    double output_history[{order + 1}];
    double last_sample_time;
}} {struct_name};

void {struct_name}_init({struct_name}* self) {{
    double num[] = {{{num_str}}};
    double den[] = {{{den_str}}};
    for (int i = 0; i < {num_len}; i++) self->numerator[i] = num[i];
    for (int i = 0; i < {den_len}; i++) self->denominator[i] = den[i];
    self->sample_time = {sample_time};
    self->order = {order};
    self->input = 0.0;
    self->output = 0.0;
    for (int i = 0; i < {order + 1}; i++) {{
        self->input_history[i] = 0.0;
        self->output_history[i] = 0.0;
    }}
    self->last_sample_time = -1e308;
}}

void {struct_name}_update({struct_name}* self, double t) {{
    if (t - self->last_sample_time >= self->sample_time - 1e-10) {{
        // Shift histories
        for (int i = self->order; i > 0; i--) {{
            self->input_history[i] = self->input_history[i - 1];
            self->output_history[i] = self->output_history[i - 1];
        }}
        self->input_history[0] = self->input;

        // Compute new output: sum(b[i]*u[k-i]) - sum(a[i]*y[k-i])
        double a0 = self->denominator[0];
        double new_output = 0.0;

        for (int i = 0; i < {num_len}; i++) {{
            if (i < {order + 1}) {{
                new_output += (self->numerator[i] / a0) * self->input_history[i];
            }}
        }}

        for (int i = 1; i < {den_len}; i++) {{
            if (i < {order + 1}) {{
                new_output -= (self->denominator[i] / a0) * self->output_history[i];
            }}
        }}

        self->output_history[0] = new_output;
        self->output = new_output;
        self->last_sample_time = t;
    }}
}}

double {struct_name}_get_output({struct_name}* self, int port) {{
    return self->output;
}}
"""


def memory_template(block: BlockInfo, struct_name: str) -> str:
    """Generate Memory block code."""
    initial_condition = block.parameters.get("initialCondition", 0.0)

    return f"""
typedef struct {{
    double initial_condition;
    double input;
    double output;
    double prev_value;
    int first_step;
}} {struct_name};

void {struct_name}_init({struct_name}* self) {{
    self->initial_condition = {initial_condition};
    self->input = 0.0;
    self->output = self->initial_condition;
    self->prev_value = self->initial_condition;
    self->first_step = 1;
}}

void {struct_name}_update({struct_name}* self, double t) {{
    if (self->first_step) {{
        self->output = self->initial_condition;
        self->first_step = 0;
    }} else {{
        self->output = self->prev_value;
    }}
    self->prev_value = self->input;
}}

double {struct_name}_get_output({struct_name}* self, int port) {{
    return self->output;
}}
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
