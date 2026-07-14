"""Regression tests for generated alpha-beta tracking filters."""

import json
from pathlib import Path

import pytest

from src.codegen.generator import CodeGenerationConfig, CodeGenerator
from src.codegen.languages.python.blocks.sensor_fusion import (
    alpha_beta_filter_template,
    alpha_beta_gamma_filter_template,
)
from src.codegen.models import BlockInfo, Language
from src.osk.blocks.sensor_fusion import AlphaBetaFilter, AlphaBetaGammaFilter
from src.osk.blocks.sources import Constant

REPO_ROOT = Path(__file__).parents[2]


def _block(block_type: str, parameters: dict, outputs: int) -> BlockInfo:
    return BlockInfo(
        id="tracking-filter",
        type=block_type,
        name="Tracking Filter",
        parameters=parameters,
        input_connections=[],
        output_connections=[],
        execution_order=0,
        input_dimensions=[[1]],
        output_dimensions=[[1]] * outputs,
    )


@pytest.mark.parametrize(
    ("osk_type", "template", "parameters", "expected"),
    [
        (
            AlphaBetaFilter,
            alpha_beta_filter_template,
            {"alpha": 0.5, "beta": 0.1, "sampleTime": 0.1},
            [5.0, 10.0],
        ),
        (
            AlphaBetaGammaFilter,
            alpha_beta_gamma_filter_template,
            {"alpha": 0.9, "beta": 0.5, "gamma": 0.1, "sampleTime": 0.1},
            [9.0, 50.0, 200.0],
        ),
    ],
)
def test_python_tracking_templates_match_osk_one_step(
    osk_type, template, parameters: dict, expected: list[float]
) -> None:
    """Generated tracking state updates must match the OSK equations."""
    measurement = Constant(value=10.0)
    osk_filter = osk_type(
        **{
            ("sample_time" if key == "sampleTime" else key): value
            for key, value in parameters.items()
        }
    )
    measurement.init()
    osk_filter.connectInput(measurement)
    osk_filter.init()
    measurement.update()
    osk_filter.update()

    namespace: dict[str, object] = {}
    exec(
        template(
            _block(
                "alpha_beta_gamma_filter" if len(expected) == 3 else "alpha_beta_filter",
                parameters,
                outputs=len(expected),
            ),
            "TrackingFilter",
        ),
        namespace,
    )
    generated_type = namespace["TrackingFilter"]
    generated = generated_type()
    generated.input = 10.0
    generated.update(0.0)

    for port, value in enumerate(expected):
        assert osk_filter.getOutput(port) == pytest.approx(value)
        assert generated.get_output(port) == pytest.approx(value)


@pytest.mark.parametrize("language", list(Language))
def test_tracking_example_uses_real_templates(language: Language) -> None:
    """Every target must emit stateful tracking filters rather than passthrough."""
    model_data = json.loads((REPO_ROOT / "examples/46_sensor_fusion_tracking.json").read_text())
    project = CodeGenerator().generate(
        model_data,
        CodeGenerationConfig(
            language=language,
            step_size=model_data["simulationConfig"]["stepSize"],
            stop_time=model_data["simulationConfig"]["stopTime"],
        ),
    )
    source = "\n".join(
        generated.content
        for generated in project.files
        if isinstance(generated.content, str)
    )

    assert "Passthrough (type: alpha_beta_filter)" not in source
    assert "Passthrough (type: alpha_beta_gamma_filter)" not in source
    assert "predicted_position" in source
    assert "velocity" in source
