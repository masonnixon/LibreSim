"""Rust block templates for sink blocks."""

from ....models import BlockInfo


def template_scope(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Scope block."""
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
