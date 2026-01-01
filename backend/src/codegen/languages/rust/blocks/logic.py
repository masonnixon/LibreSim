"""Rust templates for logic blocks."""

from ....models import BlockInfo


def template_compare_to_zero(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for CompareToZero block."""
    operator = block.parameters.get("operator", "==")
    op_map = {
        "==": "==",
        "!=": "!=",
        ">": ">",
        ">=": ">=",
        "<": "<",
        "<=": "<=",
    }
    rust_op = op_map.get(operator, "==")

    return f"""
/// {block.name} - Compare to Zero ({operator})
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: 0.0,
        }}
    }}

    pub fn init(&mut self) {{
        self.input = 0.0;
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        self.output = if self.input {rust_op} 0.0 {{ 1.0 }} else {{ 0.0 }};
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_compare_to_constant(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for CompareToConstant block."""
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
    rust_op = op_map.get(operator, "==")

    return f"""
/// {block.name} - Compare to Constant ({operator} {constant})
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub constant: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: 0.0,
            constant: {constant}_f64,
        }}
    }}

    pub fn init(&mut self) {{
        self.input = 0.0;
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        self.output = if self.input {rust_op} self.constant {{ 1.0 }} else {{ 0.0 }};
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_relational_operator(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for RelationalOperator block."""
    operator = block.parameters.get("operator", "==")
    op_map = {
        "==": "==",
        "!=": "!=",
        ">": ">",
        ">=": ">=",
        "<": "<",
        "<=": "<=",
    }
    rust_op = op_map.get(operator, "==")

    return f"""
/// {block.name} - Relational Operator ({operator})
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub input: f64,   // First input
    pub input1: f64,  // Second input
    pub output: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            input1: 0.0,
            output: 0.0,
        }}
    }}

    pub fn init(&mut self) {{
        self.input = 0.0;
        self.input1 = 0.0;
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        self.output = if self.input {rust_op} self.input1 {{ 1.0 }} else {{ 0.0 }};
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_logical_operator(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for LogicalOperator block."""
    operator = block.parameters.get("operator", "AND")
    num_inputs = block.parameters.get("numInputs", 2)

    input_decls = "\n    ".join([f"pub input{i}: f64," for i in range(num_inputs)])
    input_inits = "\n            ".join([f"input{i}: 0.0," for i in range(num_inputs)])
    input_resets = "\n        ".join([f"self.input{i} = 0.0;" for i in range(num_inputs)])

    # Build operation based on operator
    if operator == "AND":
        bool_checks = " && ".join([f"(self.input{i} != 0.0)" for i in range(num_inputs)])
        op_code = f"self.output = if {bool_checks} {{ 1.0 }} else {{ 0.0 }};"
    elif operator == "OR":
        bool_checks = " || ".join([f"(self.input{i} != 0.0)" for i in range(num_inputs)])
        op_code = f"self.output = if {bool_checks} {{ 1.0 }} else {{ 0.0 }};"
    elif operator == "NAND":
        bool_checks = " && ".join([f"(self.input{i} != 0.0)" for i in range(num_inputs)])
        op_code = f"self.output = if {bool_checks} {{ 0.0 }} else {{ 1.0 }};"
    elif operator == "NOR":
        bool_checks = " || ".join([f"(self.input{i} != 0.0)" for i in range(num_inputs)])
        op_code = f"self.output = if {bool_checks} {{ 0.0 }} else {{ 1.0 }};"
    elif operator == "XOR":
        xor_code = "(self.input0 != 0.0)"
        for i in range(1, num_inputs):
            xor_code = f"(({xor_code}) != (self.input{i} != 0.0))"
        op_code = f"self.output = if {xor_code} {{ 1.0 }} else {{ 0.0 }};"
    elif operator == "NOT":
        op_code = "self.output = if self.input0 != 0.0 { 0.0 } else { 1.0 };"
    else:
        op_code = "self.output = 0.0;"

    return f"""
/// {block.name} - Logical Operator ({operator})
#[derive(Clone, Default)]
pub struct {struct_name} {{
    {input_decls}
    pub output: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            {input_inits}
            output: 0.0,
        }}
    }}

    pub fn init(&mut self) {{
        {input_resets}
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        {op_code}
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_bit_operator(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for BitOperator block."""
    operator = block.parameters.get("operator", "AND")

    op_map = {
        "AND": "(self.input as i64) & (self.input1 as i64)",
        "OR": "(self.input as i64) | (self.input1 as i64)",
        "XOR": "(self.input as i64) ^ (self.input1 as i64)",
        "NOT": "!(self.input as i64)",
        "SHIFT_LEFT": "(self.input as i64) << (self.input1 as i64)",
        "SHIFT_RIGHT": "(self.input as i64) >> (self.input1 as i64)",
    }
    op_expr = op_map.get(operator, "0")

    return f"""
/// {block.name} - Bit Operator ({operator})
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub input: f64,   // First input
    pub input1: f64,  // Second input
    pub output: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            input1: 0.0,
            output: 0.0,
        }}
    }}

    pub fn init(&mut self) {{
        self.input = 0.0;
        self.input1 = 0.0;
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        self.output = ({op_expr}) as f64;
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


LOGIC_TEMPLATES = {
    "compare_to_zero": template_compare_to_zero,
    "compare_to_constant": template_compare_to_constant,
    "relational_operator": template_relational_operator,
    "logical_operator": template_logical_operator,
    "bit_operator": template_bit_operator,
}
