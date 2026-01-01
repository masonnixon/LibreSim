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
class {class_name} : public Block {{
public:
    {input_decls}

    void init() override {{
        output_ = 0.0;
    }}

    void update(double t) override {{
        (void)t;
        output_ = {sum_expr};
    }}

    double getOutput(int port = 0) const override {{
        (void)port;
        return output_;
    }}

private:
    double output_ = 0.0;
}};
"""


def template_gain(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Gain block."""
    gain = block.parameters.get("gain", 1.0)
    return f"""
// {block.name} - Gain block
class {class_name} : public Block {{
public:
    double input = 0.0;
    double gain = {gain};

    void init() override {{
        output_ = 0.0;
    }}

    void update(double t) override {{
        (void)t;
        output_ = gain * input;
    }}

    double getOutput(int port = 0) const override {{
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
class {class_name} : public Block {{
public:
    {input_decls}

    void init() override {{
        output_ = 1.0;
    }}

    void update(double t) override {{
        (void)t;
        output_ = {product_expr};
    }}

    double getOutput(int port = 0) const override {{
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
class {class_name} : public Block {{
public:
    double input = 0.0;

    void init() override {{
        output_ = 0.0;
    }}

    void update(double t) override {{
        (void)t;
        output_ = std::fabs(input);
    }}

    double getOutput(int port = 0) const override {{
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
class {class_name} : public Block {{
public:
    double input = 0.0;

    void init() override {{
        output_ = 0.0;
    }}

    void update(double t) override {{
        (void)t;
        if (input > 0) output_ = 1.0;
        else if (input < 0) output_ = -1.0;
        else output_ = 0.0;
    }}

    double getOutput(int port = 0) const override {{
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
class {class_name} : public Block {{
public:
    double input = 0.0;
    double bias = {bias};

    void init() override {{
        output_ = 0.0;
    }}

    void update(double t) override {{
        (void)t;
        output_ = input + bias;
    }}

    double getOutput(int port = 0) const override {{
        (void)port;
        return output_;
    }}

private:
    double output_ = 0.0;
}};
"""


def template_saturation(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Saturation block."""
    upper = block.parameters.get("upper_limit", 1.0)
    lower = block.parameters.get("lower_limit", -1.0)
    return f"""
// {block.name} - Saturation (clamp)
class {class_name} : public Block {{
public:
    double input = 0.0;
    double upper = {upper};
    double lower = {lower};

    void init() override {{
        output_ = 0.0;
    }}

    void update(double t) override {{
        (void)t;
        output_ = std::clamp(input, lower, upper);
    }}

    double getOutput(int port = 0) const override {{
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
class {class_name} : public Block {{
public:
    double input = 0.0;
    double zone_start = {start};
    double zone_end = {end};

    void init() override {{
        output_ = 0.0;
    }}

    void update(double t) override {{
        (void)t;
        if (input > zone_end) output_ = input - zone_end;
        else if (input < zone_start) output_ = input - zone_start;
        else output_ = 0.0;
    }}

    double getOutput(int port = 0) const override {{
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
class {class_name} : public Block {{
public:
    double input0 = 0.0;  // First input (u1)
    double input1 = 0.0;  // Control input (u2)
    double input2 = 0.0;  // Second input (u3)
    double threshold = {threshold};

    void init() override {{
        output_ = 0.0;
    }}

    void update(double t) override {{
        (void)t;
        output_ = (input1 >= threshold) ? input0 : input2;
    }}

    double getOutput(int port = 0) const override {{
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
class {class_name} : public Block {{
public:
    double input = 0.0;

    void init() override {{
        output_ = 0.0;
    }}

    void update(double t) override {{
        (void)t;
        output_ = {expr};
    }}

    double getOutput(int port = 0) const override {{
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
class {class_name} : public Block {{
public:
    double input = 0.0;

    void init() override {{
        output_ = 0.0;
    }}

    void update(double t) override {{
        (void)t;
        output_ = {expr};
    }}

    double getOutput(int port = 0) const override {{
        (void)port;
        return output_;
    }}

private:
    double output_ = 0.0;
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
}
