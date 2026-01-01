"""Rust block templates."""

from typing import Callable, Optional
from ....models import BlockInfo

# Import all block template modules
from .sources import SOURCE_TEMPLATES
from .sinks import SINK_TEMPLATES
from .math_ops import MATH_TEMPLATES
from .continuous import CONTINUOUS_TEMPLATES
from .discrete import DISCRETE_TEMPLATES
from .logic import LOGIC_TEMPLATES
from .signal_processing import SIGNAL_PROCESSING_TEMPLATES
from .nonlinear import NONLINEAR_TEMPLATES
from .control_design import CONTROL_DESIGN_TEMPLATES
from .aerospace import AEROSPACE_TEMPLATES

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
}


def get_block_template(block_type: str) -> Optional[Callable[[BlockInfo, str], str]]:
    """Get the template function for a block type.

    Args:
        block_type: Block type string

    Returns:
        Template function or None if not found
    """
    return BLOCK_TEMPLATES.get(block_type)


__all__ = ["BLOCK_TEMPLATES", "get_block_template"]
