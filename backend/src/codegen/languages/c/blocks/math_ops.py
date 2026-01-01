"""C block templates for math operation blocks."""

from ....models import BlockInfo


def template_sum(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Sum block."""
    signs = block.parameters.get("signs", "++")
    num_inputs = len(signs)
    input_decls = "\n    ".join([f"double input{i};" for i in range(num_inputs)])
    sum_terms = []
    for i, sign in enumerate(signs):
        if sign == '+':
            sum_terms.append(f"b->input{i}")
        else:
            sum_terms.append(f"(-b->input{i})")
    sum_expr = " + ".join(sum_terms)

    return f"""
// {block.name} - Sum block
typedef struct {{
    {input_decls}
    double output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    {"".join([f"b->input{i} = 0.0; " for i in range(num_inputs)])}
    b->output = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    b->output = {sum_expr};
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_gain(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Gain block."""
    gain = block.parameters.get("gain", 1.0)
    return f"""
// {block.name} - Gain block
typedef struct {{
    double input;
    double output;
    double gain;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
    b->gain = {gain};
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    b->output = b->gain * b->input;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_product(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Product block."""
    inputs = block.parameters.get("inputs", "**")
    num_inputs = len(inputs)
    input_decls = "\n    ".join([f"double input{i};" for i in range(num_inputs)])
    init_inputs = "".join([f"b->input{i} = 1.0; " for i in range(num_inputs)])

    # Build product expression
    product_terms = []
    for i, op in enumerate(inputs):
        if op == '*':
            product_terms.append(f"b->input{i}")
        else:  # divide
            product_terms.append(f"(1.0 / (b->input{i} != 0 ? b->input{i} : 1e-10))")

    product_expr = " * ".join(product_terms) if product_terms else "1.0"

    return f"""
// {block.name} - Product block
typedef struct {{
    {input_decls}
    double output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    {init_inputs}
    b->output = 1.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    b->output = {product_expr};
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_abs(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Abs block."""
    return f"""
// {block.name} - Absolute value
typedef struct {{
    double input;
    double output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    b->output = fabs(b->input);
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_sign(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Sign block."""
    return f"""
// {block.name} - Sign function
typedef struct {{
    double input;
    double output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    if (b->input > 0) b->output = 1.0;
    else if (b->input < 0) b->output = -1.0;
    else b->output = 0.0;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_bias(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Bias block."""
    bias = block.parameters.get("bias", 0.0)
    return f"""
// {block.name} - Bias (adds constant)
typedef struct {{
    double input;
    double output;
    double bias;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
    b->bias = {bias};
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    b->output = b->input + b->bias;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_saturation(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Saturation block."""
    upper = block.parameters.get("upper_limit", 1.0)
    lower = block.parameters.get("lower_limit", -1.0)
    return f"""
// {block.name} - Saturation (clamp)
typedef struct {{
    double input;
    double output;
    double upper;
    double lower;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
    b->upper = {upper};
    b->lower = {lower};
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    if (b->input > b->upper) b->output = b->upper;
    else if (b->input < b->lower) b->output = b->lower;
    else b->output = b->input;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_dead_zone(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Dead Zone block."""
    start = block.parameters.get("start", -0.5)
    end = block.parameters.get("end", 0.5)
    return f"""
// {block.name} - Dead Zone
typedef struct {{
    double input;
    double output;
    double zone_start;
    double zone_end;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
    b->zone_start = {start};
    b->zone_end = {end};
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    if (b->input > b->zone_end) b->output = b->input - b->zone_end;
    else if (b->input < b->zone_start) b->output = b->input - b->zone_start;
    else b->output = 0.0;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_switch(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Switch block."""
    threshold = block.parameters.get("threshold", 0.0)
    return f"""
// {block.name} - Switch
typedef struct {{
    double input0;    // First input (u1)
    double input1;    // Control input (u2)
    double input2;    // Second input (u3)
    double output;
    double threshold;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input0 = 0.0;
    b->input1 = 0.0;
    b->input2 = 0.0;
    b->output = 0.0;
    b->threshold = {threshold};
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    b->output = (b->input1 >= b->threshold) ? b->input0 : b->input2;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_math_function(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Math Function block."""
    func = block.parameters.get("function", "exp")
    func_map = {
        "exp": "exp(b->input)",
        "log": "log(b->input)",
        "log10": "log10(b->input)",
        "sqrt": "sqrt(b->input)",
        "square": "(b->input * b->input)",
        "pow": "pow(b->input, 2.0)",
        "reciprocal": "(1.0 / (b->input != 0 ? b->input : 1e-10))",
    }
    expr = func_map.get(func, "b->input")

    return f"""
// {block.name} - Math function ({func})
typedef struct {{
    double input;
    double output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    b->output = {expr};
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_trigonometry(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Trigonometric Function block."""
    func = block.parameters.get("function", "sin")
    func_map = {
        "sin": "sin(b->input)",
        "cos": "cos(b->input)",
        "tan": "tan(b->input)",
        "asin": "asin(b->input)",
        "acos": "acos(b->input)",
        "atan": "atan(b->input)",
        "sinh": "sinh(b->input)",
        "cosh": "cosh(b->input)",
        "tanh": "tanh(b->input)",
    }
    expr = func_map.get(func, "b->input")

    return f"""
// {block.name} - Trigonometric function ({func})
typedef struct {{
    double input;
    double output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    b->output = {expr};
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_mux(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Mux block."""
    num_inputs = block.parameters.get("numInputs", 2)
    input_decls = "\n    ".join([f"double input{i};" for i in range(num_inputs)])
    input_inits = "\n    ".join([f"b->input{i} = 0.0;" for i in range(num_inputs)])
    output_assigns = "\n    ".join([f"b->output[{i}] = b->input{i};" for i in range(num_inputs)])

    return f"""
// {block.name} - Mux block
typedef struct {{
    {input_decls}
    double output[{num_inputs}];
    int num_inputs;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    {input_inits}
    for (int i = 0; i < {num_inputs}; i++) b->output[i] = 0.0;
    b->num_inputs = {num_inputs};
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    {output_assigns}
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    if (port >= 0 && port < b->num_inputs) return b->output[port];
    return 0.0;
}}
"""


def template_demux(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Demux block."""
    num_outputs = block.parameters.get("numOutputs", 2)

    return f"""
// {block.name} - Demux block
typedef struct {{
    double input[{num_outputs}];
    double outputs[{num_outputs}];
    int num_outputs;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    for (int i = 0; i < {num_outputs}; i++) {{
        b->input[i] = 0.0;
        b->outputs[i] = 0.0;
    }}
    b->num_outputs = {num_outputs};
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    for (int i = 0; i < b->num_outputs; i++) {{
        b->outputs[i] = b->input[i];
    }}
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    if (port >= 0 && port < b->num_outputs) return b->outputs[port];
    return 0.0;
}}
"""


MATH_TEMPLATES = {
    "sum": template_sum,
    "gain": template_gain,
    "product": template_product,
    "abs": template_abs,
    "sign": template_sign,
    "bias": template_bias,
    "saturation": template_saturation,
    "dead_zone": template_dead_zone,
    "switch": template_switch,
    "math_function": template_math_function,
    "trigonometry": template_trigonometry,
    "mux": template_mux,
    "demux": template_demux,
}
