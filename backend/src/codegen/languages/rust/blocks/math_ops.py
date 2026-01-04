"""Rust block templates for math operation blocks."""

from ....models import BlockInfo


def template_sum(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Sum block."""
    signs = block.parameters.get("signs", "++")
    num_inputs = len(signs)

    # Build input fields
    input_fields = "\n    ".join([f"pub input{i}: f64," for i in range(num_inputs)])

    # Build initialization
    init_inputs = "\n            ".join([f"input{i}: 0.0," for i in range(num_inputs)])

    # Build sum expression
    sum_terms = []
    for i, sign in enumerate(signs):
        if sign == '+':
            sum_terms.append(f"self.input{i}")
        else:
            sum_terms.append(f"(-self.input{i})")
    sum_expr = " + ".join(sum_terms)

    return f"""
/// {block.name} - Sum block
#[derive(Clone, Default)]
pub struct {struct_name} {{
    {input_fields}
    pub output: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            {init_inputs}
            output: 0.0,
        }}
    }}

    pub fn init(&mut self) {{
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        self.output = {sum_expr};
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_gain(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Gain block.

    Supports both scalar and vector inputs - applies element-wise gain.
    """
    gain = block.parameters.get("gain", 1.0)

    # Check if this block expects vector input from its port dimensions
    expects_vector = False
    if hasattr(block, 'input_dimensions') and block.input_dimensions:
        dims = block.input_dimensions[0] if block.input_dimensions else [1]
        expects_vector = len(dims) > 0 and dims[0] > 1

    if expects_vector:
        # Vector version
        vec_size = block.input_dimensions[0][0] if block.input_dimensions else 3
        return f"""
/// {block.name} - Gain block (vector mode, size={vec_size})
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: [f64; {vec_size}],
    pub output: [f64; {vec_size}],
    pub gain: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: [0.0; {vec_size}],
            output: [0.0; {vec_size}],
            gain: {gain}_f64,
        }}
    }}

    pub fn init(&mut self) {{
        self.input = [0.0; {vec_size}];
        self.output = [0.0; {vec_size}];
    }}

    pub fn update(&mut self, _t: f64) {{
        for i in 0..{vec_size} {{
            self.output[i] = self.gain * self.input[i];
        }}
    }}

    pub fn get_output(&self, port: usize) -> f64 {{
        if port < {vec_size} {{ self.output[port] }} else {{ 0.0 }}
    }}

    pub fn get_output_vector(&self) -> &[f64; {vec_size}] {{
        &self.output
    }}
}}

impl Default for {struct_name} {{
    fn default() -> Self {{
        Self::new()
    }}
}}
"""
    else:
        # Scalar version
        return f"""
/// {block.name} - Gain block (scalar mode)
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub gain: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: 0.0,
            gain: {gain}_f64,
        }}
    }}

    pub fn init(&mut self) {{
        self.input = 0.0;
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        self.output = self.gain * self.input;
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_product(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Product block."""
    inputs = block.parameters.get("inputs", "**")
    num_inputs = len(inputs)

    # Build input fields
    input_fields = "\n    ".join([f"pub input{i}: f64," for i in range(num_inputs)])

    # Build initialization
    init_inputs = "\n            ".join([f"input{i}: 1.0," for i in range(num_inputs)])

    # Build product expression
    product_terms = []
    for i, op in enumerate(inputs):
        if op == '*':
            product_terms.append(f"self.input{i}")
        else:
            product_terms.append(f"(1.0 / self.input{i}.max(1e-10))")
    product_expr = " * ".join(product_terms) if product_terms else "1.0"

    return f"""
/// {block.name} - Product block
#[derive(Clone, Default)]
pub struct {struct_name} {{
    {input_fields}
    pub output: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            {init_inputs}
            output: 1.0,
        }}
    }}

    pub fn init(&mut self) {{
        self.output = 1.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        self.output = {product_expr};
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_abs(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Abs block."""
    return f"""
/// {block.name} - Absolute value
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
        self.output = self.input.abs();
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_sign(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Sign block."""
    return f"""
/// {block.name} - Sign function
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
        self.output = if self.input > 0.0 {{
            1.0
        }} else if self.input < 0.0 {{
            -1.0
        }} else {{
            0.0
        }};
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_bias(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Bias block."""
    bias = block.parameters.get("bias", 0.0)
    return f"""
/// {block.name} - Bias (adds constant)
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub bias: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: 0.0,
            bias: {bias}_f64,
        }}
    }}

    pub fn init(&mut self) {{
        self.input = 0.0;
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        self.output = self.input + self.bias;
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_saturation(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Saturation block."""
    # Support both camelCase (JSON) and snake_case parameter names
    upper = block.parameters.get("upperLimit", block.parameters.get("upper_limit", 1.0))
    lower = block.parameters.get("lowerLimit", block.parameters.get("lower_limit", -1.0))
    return f"""
/// {block.name} - Saturation (clamp)
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub upper: f64,
    pub lower: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: 0.0,
            upper: {upper}_f64,
            lower: {lower}_f64,
        }}
    }}

    pub fn init(&mut self) {{
        self.input = 0.0;
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        self.output = self.input.clamp(self.lower, self.upper);
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_dead_zone(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Dead Zone block."""
    start = block.parameters.get("start", -0.5)
    end = block.parameters.get("end", 0.5)
    return f"""
/// {block.name} - Dead Zone
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub zone_start: f64,
    pub zone_end: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: 0.0,
            zone_start: {start}_f64,
            zone_end: {end}_f64,
        }}
    }}

    pub fn init(&mut self) {{
        self.input = 0.0;
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        self.output = if self.input > self.zone_end {{
            self.input - self.zone_end
        }} else if self.input < self.zone_start {{
            self.input - self.zone_start
        }} else {{
            0.0
        }};
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_switch(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Switch block."""
    threshold = block.parameters.get("threshold", 0.0)
    return f"""
/// {block.name} - Switch
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub input0: f64,    // First input (u1)
    pub input1: f64,    // Control input (u2)
    pub input2: f64,    // Second input (u3)
    pub output: f64,
    pub threshold: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input0: 0.0,
            input1: 0.0,
            input2: 0.0,
            output: 0.0,
            threshold: {threshold}_f64,
        }}
    }}

    pub fn init(&mut self) {{
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        self.output = if self.input1 >= self.threshold {{
            self.input0
        }} else {{
            self.input2
        }};
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_math_function(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Math Function block."""
    func = block.parameters.get("function", "exp")
    func_map = {
        "exp": "self.input.exp()",
        "log": "self.input.ln()",
        "log10": "self.input.log10()",
        "sqrt": "self.input.sqrt()",
        "square": "(self.input * self.input)",
        "pow": "self.input.powi(2)",
        "reciprocal": "(1.0 / self.input.max(1e-10))",
    }
    expr = func_map.get(func, "self.input")

    return f"""
/// {block.name} - Math function ({func})
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
        self.output = {expr};
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_trigonometry(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Trigonometric Function block."""
    func = block.parameters.get("function", "sin")
    func_map = {
        "sin": "self.input.sin()",
        "cos": "self.input.cos()",
        "tan": "self.input.tan()",
        "asin": "self.input.asin()",
        "acos": "self.input.acos()",
        "atan": "self.input.atan()",
        "sinh": "self.input.sinh()",
        "cosh": "self.input.cosh()",
        "tanh": "self.input.tanh()",
    }
    expr = func_map.get(func, "self.input")

    return f"""
/// {block.name} - Trigonometric function ({func})
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
        self.output = {expr};
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_mux(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Mux block."""
    num_inputs = block.parameters.get("numInputs", 2)
    input_fields = "\n    ".join([f"pub input{i}: f64," for i in range(num_inputs)])
    input_inits = "\n            ".join([f"input{i}: 0.0," for i in range(num_inputs)])
    output_assigns = "\n        ".join([f"self.output[{i}] = self.input{i};" for i in range(num_inputs)])

    return f"""
/// {block.name} - Mux block
#[derive(Clone)]
pub struct {struct_name} {{
    {input_fields}
    pub output: [f64; {num_inputs}],
}}

impl {struct_name} {{
    pub const NUM_INPUTS: usize = {num_inputs};

    pub fn new() -> Self {{
        Self {{
            {input_inits}
            output: [0.0; {num_inputs}],
        }}
    }}

    pub fn init(&mut self) {{
        self.output = [0.0; {num_inputs}];
    }}

    pub fn update(&mut self, _t: f64) {{
        {output_assigns}
    }}

    pub fn get_output(&self, port: usize) -> f64 {{
        if port < Self::NUM_INPUTS {{
            self.output[port]
        }} else {{
            0.0
        }}
    }}

    pub fn get_output_vector(&self) -> &[f64; {num_inputs}] {{
        &self.output
    }}
}}

impl Default for {struct_name} {{
    fn default() -> Self {{
        Self::new()
    }}
}}
"""


def template_demux(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Demux block."""
    num_outputs = block.parameters.get("numOutputs", 2)

    return f"""
/// {block.name} - Demux block
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: [f64; {num_outputs}],
    outputs: [f64; {num_outputs}],
}}

impl {struct_name} {{
    pub const NUM_OUTPUTS: usize = {num_outputs};

    pub fn new() -> Self {{
        Self {{
            input: [0.0; {num_outputs}],
            outputs: [0.0; {num_outputs}],
        }}
    }}

    pub fn init(&mut self) {{
        self.outputs = [0.0; {num_outputs}];
    }}

    pub fn update(&mut self, _t: f64) {{
        for i in 0..Self::NUM_OUTPUTS {{
            self.outputs[i] = self.input[i];
        }}
    }}

    pub fn get_output(&self, port: usize) -> f64 {{
        if port < Self::NUM_OUTPUTS {{
            self.outputs[port]
        }} else {{
            0.0
        }}
    }}

    pub fn get_output_vector(&self) -> &[f64; {num_outputs}] {{
        &self.outputs
    }}
}}

impl Default for {struct_name} {{
    fn default() -> Self {{
        Self::new()
    }}
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
