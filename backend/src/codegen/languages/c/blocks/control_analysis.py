"""C templates for terminal control-analysis blocks."""

from ....analysis import ANALYSIS_BLOCK_TYPES
from ....models import BlockInfo


def control_analysis_template(block: BlockInfo, struct_name: str) -> str:
    """Generate a constant scalar computed from the canonical OSK analysis."""
    if block.analysis_output is None:
        raise ValueError(f"Analysis block '{block.id}' was not precomputed")
    output = repr(block.analysis_output)
    return f"""
// {block.name} - precomputed control analysis
typedef struct {{
    double input;
    double output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = {output};
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)b;
    (void)t;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    return port == 0 ? b->output : 0.0;
}}
"""


CONTROL_ANALYSIS_TEMPLATES = {
    block_type: control_analysis_template for block_type in ANALYSIS_BLOCK_TYPES
}
