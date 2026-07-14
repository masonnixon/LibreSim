"""Regression tests for generated recursive filter semantics."""

import json
import math
from pathlib import Path

import pytest

from src.codegen.filter_design import design_analog_filter
from src.codegen.generator import STATE_HOLDING_BLOCKS, CodeGenerationConfig, CodeGenerator
from src.codegen.languages.c.blocks.signal_processing import (
    SIGNAL_PROCESSING_TEMPLATES as C_TEMPLATES,
)
from src.codegen.languages.cpp.blocks.signal_processing import (
    SIGNAL_PROCESSING_TEMPLATES as CPP_TEMPLATES,
)
from src.codegen.languages.python.blocks.signal_processing import (
    SIGNAL_PROCESSING_TEMPLATES as PYTHON_TEMPLATES,
)
from src.codegen.languages.rust.blocks.signal_processing import (
    SIGNAL_PROCESSING_TEMPLATES as RUST_TEMPLATES,
)
from src.codegen.models import BlockInfo, Language
from src.osk.blocks.signal_processing import AnalogFilter
from src.simulation.compiler import ModelCompiler


def _block(block_type: str, parameters: dict, step_size: float = 0.001) -> BlockInfo:
    return BlockInfo(
        id="filter",
        type=block_type,
        name="Filter",
        parameters=parameters,
        input_connections=[],
        output_connections=[],
        execution_order=0,
        step_size=step_size,
    )


@pytest.mark.parametrize(
    "parameters",
    [
        {"design": "butterworth", "response": "lowpass", "order": 1, "cutoffFrequency": 3.0},
        {"design": "butterworth", "response": "lowpass", "order": 4, "cutoffFrequency": 3.0},
        {"design": "bessel", "response": "lowpass", "order": 2, "cutoffFrequency": 3.0},
        {
            "design": "chebyshev1",
            "response": "highpass",
            "order": 3,
            "cutoffFrequency": 5.0,
            "passbandRipple": 0.5,
        },
        {
            "design": "chebyshev2",
            "response": "bandpass",
            "order": 2,
            "lowCutoff": 2.0,
            "highCutoff": 8.0,
            "stopbandAtten": 30.0,
        },
    ],
)
def test_analog_filter_coefficients_match_osk(parameters: dict) -> None:
    """The shared codegen design helper must reproduce OSK's section coefficients."""
    keyword_parameters = {
        "design": parameters.get("design", "butterworth"),
        "response": parameters.get("response", "lowpass"),
        "order": parameters.get("order", 2),
        "cutoff_freq": parameters.get("cutoffFrequency", 10.0),
        "low_cutoff": parameters.get("lowCutoff", 1.0),
        "high_cutoff": parameters.get("highCutoff", 10.0),
        "passband_ripple": parameters.get("passbandRipple", 1.0),
        "stopband_atten": parameters.get("stopbandAtten", 40.0),
    }
    reference = AnalogFilter(**keyword_parameters)
    reference._design_filter(0.001)
    generated = design_analog_filter(parameters, 0.001)

    assert len(generated) == len(reference._biquads)
    for actual, expected in zip(generated, reference._biquads, strict=True):
        assert (actual.b0, actual.b1, actual.b2, actual.a1, actual.a2) == pytest.approx(
            (expected["b0"], expected["b1"], expected["b2"], expected["a1"], expected["a2"]),
            rel=1e-15,
            abs=1e-15,
        )


def test_low_pass_templates_use_model_step_size() -> None:
    """LPF alpha must derive from the simulation step, as it does in OSK."""
    block = _block("low_pass_filter", {"cutoffFrequency": 3.0})
    expected_alpha = 0.001 / (1.0 / (2.0 * math.pi * 3.0) + 0.001)

    python_code = PYTHON_TEMPLATES["low_pass_filter"](block, "Filter")
    assert "self.sample_time = 0.001" in python_code
    for registry in (C_TEMPLATES, CPP_TEMPLATES, RUST_TEMPLATES):
        code = registry["low_pass_filter"](block, "Filter")
        assert repr(expected_alpha) in code


def test_compiled_filter_blocks_receive_configured_step_size() -> None:
    """The language-independent contract must carry the configured simulation step."""
    example_path = Path(__file__).parents[2] / "examples" / "05b_lowpass_filter.json"
    model = json.loads(example_path.read_text())
    config = CodeGenerationConfig(language=Language.PYTHON, step_size=0.001)

    model_info = CodeGenerator().compile_model_info(model, config)
    filter_blocks = [
        block for block in model_info.blocks if block.type in {"low_pass_filter", "analog_filter"}
    ]

    assert len(filter_blocks) == 5
    assert all(block.step_size == 0.001 for block in filter_blocks)


def test_all_languages_generate_analog_filter_cascades() -> None:
    """Analog filters must never fall back to the silent passthrough template."""
    block = _block(
        "analog_filter",
        {"design": "butterworth", "response": "lowpass", "order": 2, "cutoffFrequency": 3.0},
    )
    expected_b0 = repr(design_analog_filter(block.parameters, block.step_size)[0].b0)

    for registry in (PYTHON_TEMPLATES, C_TEMPLATES, CPP_TEMPLATES, RUST_TEMPLATES):
        code = registry["analog_filter"](block, "Filter")
        assert "Cascaded Analog Filter" in code or "Cascaded analog filter" in code
        assert expected_b0 in code
        assert "Passthrough" not in code


def test_analog_filter_breaks_algebraic_loops() -> None:
    """The compiler must recognize the state held by the generated cascade."""
    assert "analog_filter" in STATE_HOLDING_BLOCKS
    assert "analog_filter" in ModelCompiler.STATE_HOLDING_BLOCKS
