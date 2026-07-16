"""Shared compile-time evaluation for control-analysis code generation."""

import math
from collections.abc import Mapping

from ..osk.blocks.control_analysis import BodePlot, NyquistPlot, PoleZeroMap, StepInfo
from .models import BlockInfo

ANALYSIS_BLOCK_TYPES = frozenset(
    {"bode_plot", "nyquist_plot", "pole_zero_map", "step_info"}
)

_ANALYSIS_CLASSES = {
    "bode_plot": BodePlot,
    "nyquist_plot": NyquistPlot,
    "pole_zero_map": PoleZeroMap,
    "step_info": StepInfo,
}

_ANALYSIS_PARAMETERS = {
    "bode_plot": {
        "numerator",
        "denominator",
        "minFrequency",
        "maxFrequency",
        "numPoints",
    },
    "nyquist_plot": {
        "numerator",
        "denominator",
        "minFrequency",
        "maxFrequency",
        "numPoints",
    },
    "pole_zero_map": {"numerator", "denominator"},
    "step_info": {
        "numerator",
        "denominator",
        "simulationTime",
        "numPoints",
        "settlingPercent",
    },
}


def compute_analysis_output(
    block: BlockInfo,
    blocks_by_id: Mapping[str, BlockInfo],
) -> float:
    """Evaluate one analysis block exactly as OSK does during ``init()``."""
    if block.type not in ANALYSIS_BLOCK_TYPES:
        raise ValueError(f"Unsupported analysis block type: {block.type}")

    parameters = dict(block.parameters)
    for connection in block.input_connections:
        source_and_port, target_separator, target_port = connection.partition("@")
        source_id, source_separator, _source_port = source_and_port.rpartition(":")
        if not target_separator or not source_separator or target_port != "0":
            continue
        source = blocks_by_id.get(source_id)
        if source is not None and source.type == "transfer_function":
            for name in ("numerator", "denominator"):
                if name in source.parameters:
                    parameters[name] = source.parameters[name]
            break

    allowed = _ANALYSIS_PARAMETERS[block.type]
    constructor_parameters = {key: value for key, value in parameters.items() if key in allowed}
    analysis = _ANALYSIS_CLASSES[block.type](**constructor_parameters)
    analysis.init()
    output = float(analysis.getOutput())
    if not math.isfinite(output):
        raise ValueError(f"Analysis block '{block.id}' produced non-finite output {output!r}")
    return output
