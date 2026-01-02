"""Rust block templates for sink blocks."""

from ....models import BlockInfo


def template_scope(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Scope block."""
    num_inputs = block.parameters.get("numInputs", 1)

    if num_inputs > 1:
        # Generate input fields: input (port 0), input1 (port 1), input2 (port 2), etc.
        input_fields = ["pub input: f64,"]
        for i in range(1, num_inputs):
            input_fields.append(f"pub input{i}: f64,")
        input_fields_str = "\n    ".join(input_fields)

        # Generate new() defaults
        new_defaults = ["input: 0.0,"]
        for i in range(1, num_inputs):
            new_defaults.append(f"input{i}: 0.0,")
        new_defaults.append(f"outputs: [0.0; {num_inputs}],")
        new_defaults_str = "\n            ".join(new_defaults)

        # Generate init code
        init_lines = ["self.input = 0.0;"]
        for i in range(1, num_inputs):
            init_lines.append(f"self.input{i} = 0.0;")
        init_lines.append(f"self.outputs = [0.0; {num_inputs}];")
        init_str = "\n        ".join(init_lines)

        # Generate update code
        update_lines = ["self.outputs[0] = self.input;"]
        for i in range(1, num_inputs):
            update_lines.append(f"self.outputs[{i}] = self.input{i};")
        update_str = "\n        ".join(update_lines)

        # Generate get_output match arms
        match_arms = ["0 => self.outputs[0],"]
        for i in range(1, num_inputs):
            match_arms.append(f"{i} => self.outputs[{i}],")
        match_arms.append("_ => 0.0,")
        match_str = "\n            ".join(match_arms)

        return f"""
/// {block.name} - Scope (data recording, {num_inputs} inputs)
#[derive(Clone)]
pub struct {struct_name} {{
    {input_fields_str}
    outputs: [f64; {num_inputs}],
}}

impl Default for {struct_name} {{
    fn default() -> Self {{
        Self::new()
    }}
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            {new_defaults_str}
        }}
    }}

    pub fn init(&mut self) {{
        {init_str}
    }}

    pub fn update(&mut self, _t: f64) {{
        {update_str}
    }}

    pub fn get_output(&self, port: usize) -> f64 {{
        match port {{
            {match_str}
        }}
    }}
}}
"""
    else:
        return f"""
/// {block.name} - Scope (data recording)
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
        self.output = self.input;
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_display(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Display block."""
    return f"""
/// {block.name} - Display
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
        self.output = self.input;
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_terminator(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Terminator block."""
    return f"""
/// {block.name} - Terminator (absorbs signal)
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub input: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{ input: 0.0 }}
    }}

    pub fn init(&mut self) {{
        self.input = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        // Terminator does nothing
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.input
    }}
}}
"""


def template_to_workspace(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for ToWorkspace block."""
    return f"""
/// {block.name} - ToWorkspace (data logging)
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
        self.output = self.input;
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_xy_graph(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for XY Graph block."""
    return f"""
/// {block.name} - XY Graph
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub input: f64,   // X input
    pub input1: f64,  // Y input
    output: f64,
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
        self.output = self.input;
    }}

    pub fn get_output(&self, port: usize) -> f64 {{
        match port {{
            0 => self.input,
            1 => self.input1,
            _ => self.input,
        }}
    }}
}}
"""


SINK_TEMPLATES = {
    "scope": template_scope,
    "display": template_display,
    "terminator": template_terminator,
    "to_workspace": template_to_workspace,
    "xy_graph": template_xy_graph,
}
