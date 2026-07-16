"""Regression tests for generated IMU and AHRS semantics."""

import json
import math
from pathlib import Path

import pytest

from src.codegen.generator import CodeGenerationConfig, CodeGenerator
from src.codegen.languages.python.blocks.sensor_fusion import (
    complementary_filter_template,
    imu_sensor_template,
    madgwick_filter_template,
)
from src.codegen.models import BlockInfo, Language
from src.osk.blocks.math_ops import Demux
from src.osk.blocks.sensor_fusion import ComplementaryFilter, IMUSensor, MadgwickFilter
from src.osk.state import State
from src.simulation.osk_adapter import _OutputPortView

REPO_ROOT = Path(__file__).parents[2]
EXAMPLE_PATH = REPO_ROOT / "examples/45_sensor_fusion_ahrs.json"


def _block(block_type: str, parameters: dict, inputs: list[int], output: int) -> BlockInfo:
    return BlockInfo(
        id=block_type,
        type=block_type,
        name=block_type.replace("_", " ").title(),
        parameters=parameters,
        input_connections=[],
        output_connections=[],
        execution_order=0,
        input_dimensions=[[width] for width in inputs],
        output_dimensions=[[output]],
        step_size=0.01,
    )


def _generated_type(template, block: BlockInfo, name: str):
    namespace = {"math": math}
    exec(template(block, name), namespace)
    return namespace[name]


def test_osk_demux_preserves_declared_vector_output_ports() -> None:
    demux = Demux(num_outputs=2, output_widths=[3, 3])
    demux.init()
    demux.setInput([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    demux.update()

    assert demux.getOutput(0) == 1.0
    assert demux.getOutput(1) == 4.0
    assert demux.getOutputVector() == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    assert demux.getOutputPortVector(0) == [1.0, 2.0, 3.0]
    assert demux.getOutputPortVector(1) == [4.0, 5.0, 6.0]
    assert _OutputPortView(demux, 1, [3]).getOutputVector() == [4.0, 5.0, 6.0]


def test_python_imu_template_matches_seeded_osk_samples() -> None:
    parameters = {
        "accelNoise": 0.1,
        "gyroNoise": 0.01,
        "accelBias": [0.02, -0.01, 0.03],
        "gyroBias": [0.001, -0.002, 0.001],
        "accelScaleError": 0.02,
        "gyroScaleError": -0.01,
        "seed": 42,
    }
    true_accel = [0.0, 0.0, 9.81]
    true_gyro = [0.1, 0.05, 0.02]
    osk = IMUSensor(
        accel_noise=0.1,
        gyro_noise=0.01,
        accel_bias=parameters["accelBias"],
        gyro_bias=parameters["gyroBias"],
        accel_scale_error=0.02,
        gyro_scale_error=-0.01,
        seed=42,
    )
    osk.init()
    osk.setInput(true_accel, 0)
    osk.setInput(true_gyro, 1)
    osk.update()

    generated_type = _generated_type(
        imu_sensor_template,
        _block("imu_sensor", parameters, [3, 3], 6),
        "GeneratedIMU",
    )
    generated = generated_type()
    generated.init()
    generated.input = true_accel
    generated.input1 = true_gyro
    generated.update(0.0)
    assert generated.get_output_vector() == pytest.approx(osk.getOutputVector())


@pytest.mark.parametrize(
    ("osk_type", "template", "parameters", "output_width"),
    [
        (MadgwickFilter, madgwick_filter_template, {"beta": 0.1}, 4),
        (ComplementaryFilter, complementary_filter_template, {"alpha": 0.98}, 3),
    ],
)
def test_python_ahrs_templates_match_osk_one_step(
    osk_type, template, parameters: dict, output_width: int
) -> None:
    State.dt = 0.01
    accel = [0.02, -0.01, 9.84]
    gyro = [0.101, 0.048, 0.021]
    osk = osk_type(**parameters)
    osk.init()
    osk.setInput(accel, 0)
    osk.setInput(gyro, 1)
    osk.update()

    generated_type = _generated_type(
        template,
        _block(osk_type.__name__, parameters, [3, 3], output_width),
        "GeneratedFilter",
    )
    generated = generated_type()
    generated.init()
    generated.input = accel
    generated.input1 = gyro
    generated.update(0.0, State.dt)
    assert generated.get_output_vector() == pytest.approx(osk.getOutputVector())


@pytest.mark.parametrize("language", list(Language))
def test_ahrs_example_has_port_specific_demux_wiring(language: Language) -> None:
    model = json.loads(EXAMPLE_PATH.read_text())
    project = CodeGenerator().generate(
        model,
        CodeGenerationConfig(
            language=language,
            step_size=model["simulationConfig"]["stepSize"],
            stop_time=model["simulationConfig"]["stopTime"],
        ),
    )
    source = "\n".join(file.content for file in project.files if isinstance(file.content, str))
    assert "get_output_vector1" in source or "getOutputVector1" in source
    assert "Simple LCG for noise" not in source
    assert "normal_distribution" not in source
    if language is Language.PYTHON:
        assert "Passthrough block (vector): IMU Sensor" not in source
        assert "Passthrough block (vector): Madgwick AHRS" not in source
        assert "Passthrough block (vector): Complementary Filter" not in source
