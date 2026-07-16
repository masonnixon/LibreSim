"""C++ templates for terminal control-analysis blocks."""

from ....analysis import ANALYSIS_BLOCK_TYPES
from ....models import BlockInfo


def control_analysis_template(block: BlockInfo, class_name: str) -> str:
    """Generate a constant scalar computed from the canonical OSK analysis."""
    if block.analysis_output is None:
        raise ValueError(f"Analysis block '{block.id}' was not precomputed")
    output = repr(block.analysis_output)
    return f"""
// {block.name} - precomputed control analysis
class {class_name} {{
public:
    double input = 0.0;
    double output = {output};

    void init() {{ output = {output}; }}
    void update(double t) {{ (void)t; }}
    double get_output(int port = 0) const {{ return port == 0 ? output : 0.0; }}
}};
"""


CONTROL_ANALYSIS_TEMPLATES = {
    block_type: control_analysis_template for block_type in ANALYSIS_BLOCK_TYPES
}
