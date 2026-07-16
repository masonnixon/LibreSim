"""Rust templates for terminal control-analysis blocks."""

from ....analysis import ANALYSIS_BLOCK_TYPES
from ....models import BlockInfo


def control_analysis_template(block: BlockInfo, struct_name: str) -> str:
    """Generate a constant scalar computed from the canonical OSK analysis."""
    if block.analysis_output is None:
        raise ValueError(f"Analysis block '{block.id}' was not precomputed")
    output = repr(block.analysis_output)
    return f"""
// {block.name} - precomputed control analysis
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{ Self {{ input: 0.0, output: {output}_f64 }} }}
    pub fn init(&mut self) {{ self.output = {output}_f64; }}
    pub fn update(&mut self, _t: f64) {{}}
    pub fn get_output(&self, port: usize) -> f64 {{
        if port == 0 {{ self.output }} else {{ 0.0 }}
    }}
}}

impl Default for {struct_name} {{
    fn default() -> Self {{ Self::new() }}
}}
"""


CONTROL_ANALYSIS_TEMPLATES = {
    block_type: control_analysis_template for block_type in ANALYSIS_BLOCK_TYPES
}
