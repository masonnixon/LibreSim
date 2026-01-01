"""C templates for logic blocks."""

from ....models import BlockInfo


def template_compare_to_zero(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for CompareToZero block."""
    operator = block.parameters.get("operator", "==")
    # Map operator to C comparison
    op_map = {
        "==": "==",
        "!=": "!=",
        ">": ">",
        ">=": ">=",
        "<": "<",
        "<=": "<=",
    }
    c_op = op_map.get(operator, "==")

    return f"""
// {block.name} - Compare to Zero ({operator})
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
    b->output = (b->input {c_op} 0.0) ? 1.0 : 0.0;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_compare_to_constant(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for CompareToConstant block."""
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
    c_op = op_map.get(operator, "==")

    return f"""
// {block.name} - Compare to Constant ({operator} {constant})
typedef struct {{
    double input;
    double output;
    double constant;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
    b->constant = {constant};
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    b->output = (b->input {c_op} b->constant) ? 1.0 : 0.0;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_relational_operator(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for RelationalOperator block."""
    operator = block.parameters.get("operator", "==")
    op_map = {
        "==": "==",
        "!=": "!=",
        ">": ">",
        ">=": ">=",
        "<": "<",
        "<=": "<=",
    }
    c_op = op_map.get(operator, "==")

    return f"""
// {block.name} - Relational Operator ({operator})
typedef struct {{
    double input;   // First input
    double input1;  // Second input
    double output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->input1 = 0.0;
    b->output = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    b->output = (b->input {c_op} b->input1) ? 1.0 : 0.0;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_logical_operator(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for LogicalOperator block."""
    operator = block.parameters.get("operator", "AND")
    num_inputs = block.parameters.get("numInputs", 2)

    input_decls = "\n    ".join([f"double input{i};" for i in range(num_inputs)])
    input_inits = "\n    ".join([f"b->input{i} = 0.0;" for i in range(num_inputs)])

    # Build operation based on operator
    if operator == "AND":
        bool_checks = " && ".join([f"(b->input{i} != 0)" for i in range(num_inputs)])
        op_code = f"b->output = ({bool_checks}) ? 1.0 : 0.0;"
    elif operator == "OR":
        bool_checks = " || ".join([f"(b->input{i} != 0)" for i in range(num_inputs)])
        op_code = f"b->output = ({bool_checks}) ? 1.0 : 0.0;"
    elif operator == "NAND":
        bool_checks = " && ".join([f"(b->input{i} != 0)" for i in range(num_inputs)])
        op_code = f"b->output = ({bool_checks}) ? 0.0 : 1.0;"
    elif operator == "NOR":
        bool_checks = " || ".join([f"(b->input{i} != 0)" for i in range(num_inputs)])
        op_code = f"b->output = ({bool_checks}) ? 0.0 : 1.0;"
    elif operator == "XOR":
        xor_code = "(b->input0 != 0)"
        for i in range(1, num_inputs):
            xor_code = f"(({xor_code}) != (b->input{i} != 0))"
        op_code = f"b->output = {xor_code} ? 1.0 : 0.0;"
    elif operator == "NOT":
        op_code = "b->output = (b->input0 != 0) ? 0.0 : 1.0;"
    else:
        op_code = "b->output = 0.0;"

    return f"""
// {block.name} - Logical Operator ({operator})
typedef struct {{
    {input_decls}
    double output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    {input_inits}
    b->output = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    {op_code}
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_bit_operator(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for BitOperator block."""
    operator = block.parameters.get("operator", "AND")

    op_map = {
        "AND": "(int)b->input & (int)b->input1",
        "OR": "(int)b->input | (int)b->input1",
        "XOR": "(int)b->input ^ (int)b->input1",
        "NOT": "~(int)b->input",
        "SHIFT_LEFT": "(int)b->input << (int)b->input1",
        "SHIFT_RIGHT": "(int)b->input >> (int)b->input1",
    }
    op_expr = op_map.get(operator, "0")

    return f"""
// {block.name} - Bit Operator ({operator})
typedef struct {{
    double input;   // First input
    double input1;  // Second input
    double output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->input1 = 0.0;
    b->output = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    b->output = (double)({op_expr});
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


LOGIC_TEMPLATES = {
    "compare_to_zero": template_compare_to_zero,
    "compare_to_constant": template_compare_to_constant,
    "relational_operator": template_relational_operator,
    "logical_operator": template_logical_operator,
    "bit_operator": template_bit_operator,
}
