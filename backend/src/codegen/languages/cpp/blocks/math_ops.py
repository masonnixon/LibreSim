"""C++ block templates for math operation blocks."""

from ....models import BlockInfo


def template_sum(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Sum block."""
    signs = block.parameters.get("signs", "++")
    num_inputs = len(signs)
    input_decls = "\n    ".join([f"double input{i} = 0.0;" for i in range(num_inputs)])
    sum_terms = []
    for i, sign in enumerate(signs):
        if sign == '+':
            sum_terms.append(f"input{i}")
        else:
            sum_terms.append(f"(-input{i})")
    sum_expr = " + ".join(sum_terms)

    return f"""
// {block.name} - Sum block
class {class_name} {{
public:
    {input_decls}

    void init() {{
        output_ = 0.0;
    }}

    void update(double t) {{
        (void)t;
        output_ = {sum_expr};
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output_;
    }}

private:
    double output_ = 0.0;
}};
"""


def template_gain(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Gain block.

    Supports both scalar and vector inputs - applies element-wise gain.
    Uses std::variant to handle both types dynamically.
    """
    gain = block.parameters.get("gain", 1.0)

    # Check if this block expects vector input from its port dimensions
    expects_vector = False
    if hasattr(block, 'input_dimensions') and block.input_dimensions:
        dims = block.input_dimensions[0] if block.input_dimensions else [1]
        expects_vector = len(dims) > 0 and dims[0] > 1

    if expects_vector:
        # Vector version - determine size from input dimensions
        vec_size = block.input_dimensions[0][0] if block.input_dimensions else 3
        return f"""
// {block.name} - Gain block (vector mode, size={vec_size})
class {class_name} {{
public:
    std::array<double, {vec_size}> input = {{}};
    double gain = {gain};

    void init() {{
        output_.fill(0.0);
    }}

    void update(double t) {{
        (void)t;
        for (int i = 0; i < {vec_size}; i++) {{
            output_[i] = gain * input[i];
        }}
    }}

    double get_output(int port = 0) const {{
        if (port >= 0 && port < {vec_size}) return output_[port];
        return 0.0;
    }}

    const std::array<double, {vec_size}>& getOutputVector() const {{
        return output_;
    }}

private:
    std::array<double, {vec_size}> output_ = {{}};
}};
"""
    else:
        # Scalar version
        return f"""
// {block.name} - Gain block (scalar mode)
class {class_name} {{
public:
    double input = 0.0;
    double gain = {gain};

    void init() {{
        output_ = 0.0;
    }}

    void update(double t) {{
        (void)t;
        output_ = gain * input;
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output_;
    }}

private:
    double output_ = 0.0;
}};
"""


def template_product(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Product block."""
    inputs = block.parameters.get("inputs", "**")
    num_inputs = len(inputs)
    input_decls = "\n    ".join([f"double input{i} = 1.0;" for i in range(num_inputs)])

    # Build product expression
    product_terms = []
    for i, op in enumerate(inputs):
        if op == '*':
            product_terms.append(f"input{i}")
        else:  # divide
            product_terms.append(f"(1.0 / (input{i} != 0 ? input{i} : 1e-10))")

    product_expr = " * ".join(product_terms) if product_terms else "1.0"

    return f"""
// {block.name} - Product block
class {class_name} {{
public:
    {input_decls}

    void init() {{
        output_ = 1.0;
    }}

    void update(double t) {{
        (void)t;
        output_ = {product_expr};
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output_;
    }}

private:
    double output_ = 1.0;
}};
"""


def template_abs(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Abs block."""
    return f"""
// {block.name} - Absolute value
class {class_name} {{
public:
    double input = 0.0;

    void init() {{
        output_ = 0.0;
    }}

    void update(double t) {{
        (void)t;
        output_ = std::fabs(input);
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output_;
    }}

private:
    double output_ = 0.0;
}};
"""


def template_sign(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Sign block."""
    return f"""
// {block.name} - Sign function
class {class_name} {{
public:
    double input = 0.0;

    void init() {{
        output_ = 0.0;
    }}

    void update(double t) {{
        (void)t;
        if (input > 0) output_ = 1.0;
        else if (input < 0) output_ = -1.0;
        else output_ = 0.0;
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output_;
    }}

private:
    double output_ = 0.0;
}};
"""


def template_bias(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Bias block."""
    bias = block.parameters.get("bias", 0.0)
    return f"""
// {block.name} - Bias (adds constant)
class {class_name} {{
public:
    double input = 0.0;
    double bias = {bias};

    void init() {{
        output_ = 0.0;
    }}

    void update(double t) {{
        (void)t;
        output_ = input + bias;
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output_;
    }}

private:
    double output_ = 0.0;
}};
"""


def template_saturation(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Saturation block."""
    # Support both camelCase (JSON) and snake_case parameter names
    upper = block.parameters.get("upperLimit", block.parameters.get("upper_limit", 1.0))
    lower = block.parameters.get("lowerLimit", block.parameters.get("lower_limit", -1.0))
    return f"""
// {block.name} - Saturation (clamp)
class {class_name} {{
public:
    double input = 0.0;
    double upper = {upper};
    double lower = {lower};

    void init() {{
        output_ = 0.0;
    }}

    void update(double t) {{
        (void)t;
        output_ = std::clamp(input, lower, upper);
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output_;
    }}

private:
    double output_ = 0.0;
}};
"""


def template_dead_zone(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Dead Zone block."""
    start = block.parameters.get("start", -0.5)
    end = block.parameters.get("end", 0.5)
    return f"""
// {block.name} - Dead Zone
class {class_name} {{
public:
    double input = 0.0;
    double zone_start = {start};
    double zone_end = {end};

    void init() {{
        output_ = 0.0;
    }}

    void update(double t) {{
        (void)t;
        if (input > zone_end) output_ = input - zone_end;
        else if (input < zone_start) output_ = input - zone_start;
        else output_ = 0.0;
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output_;
    }}

private:
    double output_ = 0.0;
}};
"""


def template_switch(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Switch block."""
    threshold = block.parameters.get("threshold", 0.0)
    return f"""
// {block.name} - Switch
class {class_name} {{
public:
    double input0 = 0.0;  // First input (u1)
    double input1 = 0.0;  // Control input (u2)
    double input2 = 0.0;  // Second input (u3)
    double threshold = {threshold};

    void init() {{
        output_ = 0.0;
    }}

    void update(double t) {{
        (void)t;
        output_ = (input1 >= threshold) ? input0 : input2;
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output_;
    }}

private:
    double output_ = 0.0;
}};
"""


def template_math_function(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Math Function block."""
    func = block.parameters.get("function", "exp")
    func_map = {
        "exp": "std::exp(input)",
        "log": "std::log(input)",
        "log10": "std::log10(input)",
        "sqrt": "std::sqrt(input)",
        "square": "(input * input)",
        "pow": "std::pow(input, 2.0)",
        "reciprocal": "(1.0 / (input != 0 ? input : 1e-10))",
    }
    expr = func_map.get(func, "input")

    return f"""
// {block.name} - Math function ({func})
class {class_name} {{
public:
    double input = 0.0;

    void init() {{
        output_ = 0.0;
    }}

    void update(double t) {{
        (void)t;
        output_ = {expr};
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output_;
    }}

private:
    double output_ = 0.0;
}};
"""


def template_trigonometry(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Trigonometric Function block."""
    func = block.parameters.get("function", "sin")
    func_map = {
        "sin": "std::sin(input)",
        "cos": "std::cos(input)",
        "tan": "std::tan(input)",
        "asin": "std::asin(input)",
        "acos": "std::acos(input)",
        "atan": "std::atan(input)",
        "sinh": "std::sinh(input)",
        "cosh": "std::cosh(input)",
        "tanh": "std::tanh(input)",
    }
    expr = func_map.get(func, "input")

    return f"""
// {block.name} - Trigonometric function ({func})
class {class_name} {{
public:
    double input = 0.0;

    void init() {{
        output_ = 0.0;
    }}

    void update(double t) {{
        (void)t;
        output_ = {expr};
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output_;
    }}

private:
    double output_ = 0.0;
}};
"""


def template_mux(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Mux block."""
    num_inputs = block.parameters.get("numInputs", 2)
    input_decls = "\n    ".join([f"double input{i} = 0.0;" for i in range(num_inputs)])
    output_assigns = "\n        ".join([f"output_[{i}] = input{i};" for i in range(num_inputs)])

    return f"""
// {block.name} - Mux block
class {class_name} {{
public:
    {input_decls}
    static constexpr int NUM_INPUTS = {num_inputs};

    void init() {{
        output_.fill(0.0);
    }}

    void update(double t) {{
        (void)t;
        {output_assigns}
    }}

    double get_output(int port = 0) const {{
        if (port >= 0 && port < NUM_INPUTS) return output_[port];
        return 0.0;
    }}

    const std::array<double, NUM_INPUTS>& getOutputVector() const {{
        return output_;
    }}

private:
    std::array<double, {num_inputs}> output_ = {{}};
}};
"""


def template_demux(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Demux block."""
    num_outputs = block.parameters.get("numOutputs", 2)
    output_widths = block.parameters.get("outputWidths", None)

    # If outputWidths not specified, assume uniform scalar outputs
    if output_widths is None:
        output_widths = [1] * num_outputs

    total_width = sum(output_widths)

    # Generate output array declarations
    output_decls = []
    for i, width in enumerate(output_widths):
        if width == 1:
            output_decls.append(f"    double output{i} = 0.0;")
        else:
            output_decls.append(f"    std::array<double, {width}> output{i} = {{}};")

    output_decls_str = "\n".join(output_decls)

    # Generate init code
    init_lines = []
    for i, width in enumerate(output_widths):
        if width == 1:
            init_lines.append(f"        output{i} = 0.0;")
        else:
            init_lines.append(f"        output{i}.fill(0.0);")

    init_str = "\n".join(init_lines)

    # Generate update code
    update_lines = []
    offset = 0
    for i, width in enumerate(output_widths):
        if width == 1:
            update_lines.append(f"        output{i} = input[{offset}];")
        else:
            for j in range(width):
                update_lines.append(f"        output{i}[{j}] = input[{offset + j}];")
        offset += width

    update_str = "\n".join(update_lines)

    # Generate get_output that returns scalars based on port
    get_output_lines = ["        int offset = 0;"]
    for i, width in enumerate(output_widths):
        if width == 1:
            get_output_lines.append(f"        if (port == {i}) return output{i};")
        else:
            get_output_lines.append(f"        if (port >= {i} && port < {i + width}) return output{i}[port - {i}];")

    get_output_str = "\n".join(get_output_lines)

    # Generate getOutputVector methods for vector outputs only
    vector_methods = []
    for i, width in enumerate(output_widths):
        if width > 1:
            suffix = "" if i == 0 else str(i)
            vector_methods.append(f"""    const std::array<double, {width}>& getOutputVector{suffix}() const {{
        return output{i};
    }}""")

    vector_methods_str = "\n\n".join(vector_methods) if vector_methods else ""

    return f"""
// {block.name} - Demux block
class {class_name} {{
public:
    std::array<double, {total_width}> input = {{}};  // Total input size: {total_width}
    static constexpr int NUM_OUTPUTS = {num_outputs};

{output_decls_str}

    void init() {{
        input.fill(0.0);
{init_str}
    }}

    void update(double t) {{
        (void)t;
{update_str}
    }}

    double get_output(int port = 0) const {{
        // Return element based on port index
        if (port >= 0 && port < {total_width}) return input[port];
        return 0.0;
    }}

{vector_methods_str}
}};
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
