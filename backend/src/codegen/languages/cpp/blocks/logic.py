"""C++ templates for logic blocks."""

from ....models import BlockInfo


def template_compare_to_zero(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for CompareToZero block."""
    operator = block.parameters.get("operator", "==")
    op_map = {
        "==": "==",
        "!=": "!=",
        ">": ">",
        ">=": ">=",
        "<": "<",
        "<=": "<=",
    }
    cpp_op = op_map.get(operator, "==")

    return f"""
// {block.name} - Compare to Zero ({operator})
class {class_name} {{
public:
    double input = 0.0;
    double output = 0.0;

    void init() {{
        input = 0.0;
        output = 0.0;
    }}

    void update(double t) {{
        (void)t;
        output = (input {cpp_op} 0.0) ? 1.0 : 0.0;
    }}

    double get_output(int port) const {{
        (void)port;
        return output;
    }}
}};
"""


def template_compare_to_constant(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for CompareToConstant block."""
    operator = block.parameters.get("operator", "==")
    constant = block.parameters.get("constant", 0.0)
    op_map = {
        "==": "==",
        "!=": "!=",
        ">": ">",
        ">=": ">=",
        "<": "<",
        "<=": "<=",
    }
    cpp_op = op_map.get(operator, "==")

    return f"""
// {block.name} - Compare to Constant ({operator} {constant})
class {class_name} {{
public:
    double input = 0.0;
    double output = 0.0;
    double constant = {constant};

    void init() {{
        input = 0.0;
        output = 0.0;
    }}

    void update(double t) {{
        (void)t;
        output = (input {cpp_op} constant) ? 1.0 : 0.0;
    }}

    double get_output(int port) const {{
        (void)port;
        return output;
    }}
}};
"""


def template_relational_operator(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for RelationalOperator block."""
    operator = block.parameters.get("operator", "==")
    op_map = {
        "==": "==",
        "!=": "!=",
        ">": ">",
        ">=": ">=",
        "<": "<",
        "<=": "<=",
    }
    cpp_op = op_map.get(operator, "==")

    return f"""
// {block.name} - Relational Operator ({operator})
class {class_name} {{
public:
    double input = 0.0;   // First input
    double input1 = 0.0;  // Second input
    double output = 0.0;

    void init() {{
        input = 0.0;
        input1 = 0.0;
        output = 0.0;
    }}

    void update(double t) {{
        (void)t;
        output = (input {cpp_op} input1) ? 1.0 : 0.0;
    }}

    double get_output(int port) const {{
        (void)port;
        return output;
    }}
}};
"""


def template_logical_operator(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for LogicalOperator block."""
    operator = block.parameters.get("operator", "AND")
    num_inputs = block.parameters.get("numInputs", 2)

    input_decls = "\n    ".join([f"double input{i} = 0.0;" for i in range(num_inputs)])
    input_inits = "\n        ".join([f"input{i} = 0.0;" for i in range(num_inputs)])

    # Build operation based on operator
    if operator == "AND":
        bool_checks = " && ".join([f"(input{i} != 0)" for i in range(num_inputs)])
        op_code = f"output = ({bool_checks}) ? 1.0 : 0.0;"
    elif operator == "OR":
        bool_checks = " || ".join([f"(input{i} != 0)" for i in range(num_inputs)])
        op_code = f"output = ({bool_checks}) ? 1.0 : 0.0;"
    elif operator == "NAND":
        bool_checks = " && ".join([f"(input{i} != 0)" for i in range(num_inputs)])
        op_code = f"output = ({bool_checks}) ? 0.0 : 1.0;"
    elif operator == "NOR":
        bool_checks = " || ".join([f"(input{i} != 0)" for i in range(num_inputs)])
        op_code = f"output = ({bool_checks}) ? 0.0 : 1.0;"
    elif operator == "XOR":
        xor_code = "(input0 != 0)"
        for i in range(1, num_inputs):
            xor_code = f"(({xor_code}) != (input{i} != 0))"
        op_code = f"output = {xor_code} ? 1.0 : 0.0;"
    elif operator == "NOT":
        op_code = "output = (input0 != 0) ? 0.0 : 1.0;"
    else:
        op_code = "output = 0.0;"

    return f"""
// {block.name} - Logical Operator ({operator})
class {class_name} {{
public:
    {input_decls}
    double output = 0.0;

    void init() {{
        {input_inits}
        output = 0.0;
    }}

    void update(double t) {{
        (void)t;
        {op_code}
    }}

    double get_output(int port) const {{
        (void)port;
        return output;
    }}
}};
"""


def template_bit_operator(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for BitOperator block."""
    operator = block.parameters.get("operator", "AND")

    op_map = {
        "AND": "static_cast<int>(input) & static_cast<int>(input1)",
        "OR": "static_cast<int>(input) | static_cast<int>(input1)",
        "XOR": "static_cast<int>(input) ^ static_cast<int>(input1)",
        "NOT": "~static_cast<int>(input)",
        "SHIFT_LEFT": "static_cast<int>(input) << static_cast<int>(input1)",
        "SHIFT_RIGHT": "static_cast<int>(input) >> static_cast<int>(input1)",
    }
    op_expr = op_map.get(operator, "0")

    return f"""
// {block.name} - Bit Operator ({operator})
class {class_name} {{
public:
    double input = 0.0;   // First input
    double input1 = 0.0;  // Second input
    double output = 0.0;

    void init() {{
        input = 0.0;
        input1 = 0.0;
        output = 0.0;
    }}

    void update(double t) {{
        (void)t;
        output = static_cast<double>({op_expr});
    }}

    double get_output(int port) const {{
        (void)port;
        return output;
    }}
}};
"""


LOGIC_TEMPLATES = {
    "compare_to_zero": template_compare_to_zero,
    "compare_to_constant": template_compare_to_constant,
    "relational_operator": template_relational_operator,
    "logical_operator": template_logical_operator,
    "bit_operator": template_bit_operator,
}
