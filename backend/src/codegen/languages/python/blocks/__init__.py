"""Python block templates."""

from collections.abc import Callable

from ....models import BlockInfo
from .aerospace import AEROSPACE_TEMPLATES
from .continuous import CONTINUOUS_TEMPLATES
from .control_design import CONTROL_DESIGN_TEMPLATES
from .discrete import DISCRETE_TEMPLATES
from .dsp import DSP_TEMPLATES
from .estimation import ESTIMATION_TEMPLATES
from .logic import LOGIC_TEMPLATES
from .math_ops import MATH_TEMPLATES
from .nonlinear import NONLINEAR_TEMPLATES
from .signal_processing import SIGNAL_PROCESSING_TEMPLATES
from .sinks import SINK_TEMPLATES

# Import all block template modules
from .sources import SOURCE_TEMPLATES

# Combine all templates
BLOCK_TEMPLATES: dict[str, Callable[[BlockInfo, str], str]] = {
    **SOURCE_TEMPLATES,
    **SINK_TEMPLATES,
    **MATH_TEMPLATES,
    **CONTINUOUS_TEMPLATES,
    **DISCRETE_TEMPLATES,
    **LOGIC_TEMPLATES,
    **SIGNAL_PROCESSING_TEMPLATES,
    **NONLINEAR_TEMPLATES,
    **CONTROL_DESIGN_TEMPLATES,
    **AEROSPACE_TEMPLATES,
    **DSP_TEMPLATES,
    **ESTIMATION_TEMPLATES,
}


def get_block_template(block_type: str) -> Callable[[BlockInfo, str], str] | None:
    """Get the template function for a block type.

    Args:
        block_type: Block type string

    Returns:
        Template function or None if not found
    """
    return BLOCK_TEMPLATES.get(block_type)


__all__ = ["BLOCK_TEMPLATES", "get_block_template"]
