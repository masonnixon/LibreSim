"""Python templates for terminal control-analysis blocks."""

from ....analysis import ANALYSIS_BLOCK_TYPES
from ....models import BlockInfo


def control_analysis_template(block: BlockInfo, class_name: str) -> str:
    """Generate a constant scalar computed from the canonical OSK analysis."""
    if block.analysis_output is None:
        raise ValueError(f"Analysis block '{block.id}' was not precomputed")
    output = repr(block.analysis_output)
    return f'''
class {class_name}:
    """Precomputed control analysis: {block.name}"""

    def __init__(self):
        self.input = 0.0
        self.output = {output}

    def init(self):
        self.output = {output}

    def update(self, t: float):
        pass

    def get_output(self, port: int = 0) -> float:
        return self.output if port == 0 else 0.0
'''


CONTROL_ANALYSIS_TEMPLATES = {
    block_type: control_analysis_template for block_type in ANALYSIS_BLOCK_TYPES
}
