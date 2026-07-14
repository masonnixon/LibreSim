"""Regression tests for generated discrete PID semantics."""

import math

import pytest

from src.codegen.generator import CodeGenerationConfig, CodeGenerator
from src.codegen.languages.python.blocks.discrete import (
    discrete_pid_controller_template,
)
from src.codegen.models import BlockInfo, Language
from src.osk.blocks.discrete import DiscretePIDController
from src.osk.state import State

PARAMETERS = {
    "Kp": 4.0,
    "Ki": 2.0,
    "Kd": 0.5,
    "N": 50.0,
    "sampleTime": 0.1,
    "method": "trapezoidal",
}


def _block() -> BlockInfo:
    return BlockInfo(
        id="pid",
        type="discrete_pid_controller",
        name="Discrete PID",
        parameters=PARAMETERS,
        input_connections=[],
        output_connections=[],
        execution_order=1,
    )


def _model() -> dict:
    return {
        "id": "discrete-pid",
        "metadata": {"name": "Discrete PID", "description": ""},
        "blocks": [
            {
                "id": "source",
                "type": "constant",
                "name": "Error",
                "position": {"x": 0, "y": 0},
                "parameters": {"value": 1.0},
                "inputPorts": [],
                "outputPorts": [{"id": "source-out", "name": "out", "dimensions": [1]}],
            },
            {
                "id": "pid",
                "type": "discrete_pid_controller",
                "name": "Discrete PID",
                "position": {"x": 100, "y": 0},
                "parameters": PARAMETERS,
                "inputPorts": [{"id": "pid-in", "name": "error", "dimensions": [1]}],
                "outputPorts": [{"id": "pid-out", "name": "out", "dimensions": [1]}],
            },
            {
                "id": "scope",
                "type": "scope",
                "name": "Scope",
                "position": {"x": 200, "y": 0},
                "parameters": {},
                "inputPorts": [{"id": "scope-in", "name": "in", "dimensions": [1]}],
                "outputPorts": [],
            },
        ],
        "connections": [
            {
                "id": "source-pid",
                "sourceBlockId": "source",
                "sourcePortId": "source-out",
                "targetBlockId": "pid",
                "targetPortId": "pid-in",
            },
            {
                "id": "pid-scope",
                "sourceBlockId": "pid",
                "sourcePortId": "pid-out",
                "targetBlockId": "scope",
                "targetPortId": "scope-in",
            },
        ],
        "simulationConfig": {
            "solver": "rk4",
            "startTime": 0.0,
            "stopTime": 1.0,
            "stepSize": 0.01,
        },
    }


def test_python_discrete_pid_matches_osk_sample_timing():
    namespace: dict[str, object] = {}
    exec(discrete_pid_controller_template(_block(), "GeneratedPID"), namespace)
    generated = namespace["GeneratedPID"]()
    osk = DiscretePIDController(
        Kp=PARAMETERS["Kp"],
        Ki=PARAMETERS["Ki"],
        Kd=PARAMETERS["Kd"],
        N=PARAMETERS["N"],
        sample_time=PARAMETERS["sampleTime"],
        method=PARAMETERS["method"],
    )
    generated.init()
    osk.init()
    State.ready = 1

    for step in range(201):
        t = step * 0.01
        error = math.sin(0.7 * t) + 0.25
        State.t = t
        generated.input = error
        osk.setInput(error)

        generated.update(t)
        osk.update()

        assert generated.get_output() == pytest.approx(osk.getOutput())


@pytest.mark.parametrize(
    ("language", "path"),
    [
        (Language.PYTHON, "blocks.py"),
        (Language.C, "include/blocks.h"),
        (Language.CPP, "include/blocks.hpp"),
        (Language.RUST, "src/blocks.rs"),
    ],
)
def test_discrete_pid_has_a_real_template(language: Language, path: str):
    project = CodeGenerator().generate(
        _model(), CodeGenerationConfig(language=language, project_name="discrete-pid")
    )
    source = project.get_file(path)

    assert source is not None
    assert "Passthrough (type: discrete_pid_controller)" not in source.content
