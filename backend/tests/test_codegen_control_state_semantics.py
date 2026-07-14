"""Regression tests for generated continuous-state control blocks."""

from collections.abc import Callable

import pytest

from src.codegen.generator import CodeGenerationConfig, CodeGenerator
from src.codegen.languages.python.blocks.control_design import (
    model_reference_template,
    pd_controller_template,
    pi_controller_template,
)
from src.codegen.models import BlockInfo, Language
from src.osk.blocks.control_design import ModelReference, PDController, PIController
from src.osk.state import State


def _block(block_type: str, parameters: dict) -> BlockInfo:
    return BlockInfo(
        id="control",
        type=block_type,
        name="Control",
        parameters=parameters,
        input_connections=[],
        output_connections=[],
        execution_order=1,
    )


def _model(block_type: str, parameters: dict) -> dict:
    return {
        "id": f"{block_type}-state",
        "metadata": {"name": "Control state", "description": ""},
        "blocks": [
            {
                "id": "source",
                "type": "constant",
                "name": "Source",
                "position": {"x": 0, "y": 0},
                "parameters": {"value": 1.0},
                "inputPorts": [],
                "outputPorts": [{"id": "source-out", "name": "out", "dimensions": [1]}],
            },
            {
                "id": "control",
                "type": block_type,
                "name": "Control",
                "position": {"x": 100, "y": 0},
                "parameters": parameters,
                "inputPorts": [{"id": "control-in", "name": "in", "dimensions": [1]}],
                "outputPorts": [
                    {"id": "control-out", "name": "out", "dimensions": [1]}
                ],
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
                "id": "source-control",
                "sourceBlockId": "source",
                "sourcePortId": "source-out",
                "targetBlockId": "control",
                "targetPortId": "control-in",
            },
            {
                "id": "control-scope",
                "sourceBlockId": "control",
                "sourcePortId": "control-out",
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


@pytest.mark.parametrize(
    ("template", "parameters", "osk_factory"),
    [
        (pi_controller_template, {"Kp": 2.0, "Ki": 1.0}, lambda: PIController(2.0, 1.0)),
        (
            pd_controller_template,
            {"Kp": 5.0, "Kd": 1.0, "N": 10.0},
            lambda: PDController(5.0, 1.0, 10.0),
        ),
        (
            model_reference_template,
            {"naturalFrequency": 2.0, "dampingRatio": 0.8},
            lambda: ModelReference(2.0, 0.8),
        ),
    ],
)
def test_python_control_state_propagation_matches_osk(
    monkeypatch: pytest.MonkeyPatch,
    template: Callable[[BlockInfo, str], str],
    parameters: dict,
    osk_factory: Callable[[], object],
):
    namespace: dict[str, object] = {}
    block_type = {
        pi_controller_template: "pi_controller",
        pd_controller_template: "pd_controller",
        model_reference_template: "model_reference",
    }[template]
    exec(template(_block(block_type, parameters), "GeneratedControl"), namespace)
    generated = namespace["GeneratedControl"]()
    osk = osk_factory()
    generated.init()
    osk.init()
    monkeypatch.setattr(State, "method", "RK4")
    monkeypatch.setattr(State, "dt", 0.01)
    monkeypatch.setattr(State, "t", 0.0)
    monkeypatch.setattr(State, "ready", 1)
    monkeypatch.setattr(State, "kpass", 0)

    for step in range(50):
        State.t = step * State.dt
        State.ready = 1
        generated.input = 1.0
        osk.setInput(1.0)
        generated.update(State.t)
        osk.update()
        assert generated.get_output() == pytest.approx(osk.getOutput())

        for kpass in range(4):
            State.ready = 0
            State.kpass = kpass
            generated.input = 1.0
            osk.setInput(1.0)
            generated.update(State.t)
            osk.update()
            generated.propagate_states(State.dt, kpass)
            osk.propagateStates()


@pytest.mark.parametrize(
    "block_type",
    ["pi_controller", "pd_controller", "model_reference"],
)
def test_control_blocks_are_classified_for_custom_state_propagation(block_type: str):
    parameters = (
        {"naturalFrequency": 2.0, "dampingRatio": 0.8}
        if block_type == "model_reference"
        else {"Kp": 2.0, "Ki": 1.0, "Kd": 0.5, "N": 10.0}
    )
    info = CodeGenerator().compile_model_info(
        _model(block_type, parameters), CodeGenerationConfig()
    )

    control = next(block for block in info.blocks if block.id == "control")
    assert control.custom_state_propagation


@pytest.mark.parametrize(
    ("language", "path", "call"),
    [
        (Language.PYTHON, "simulation.py", "self._multi_state_blocks = [self.block_control]"),
        (
            Language.C,
            "src/simulation.c",
            "Block_control_propagate_states(&model->block_control, dt, kpass, method)",
        ),
        (
            Language.CPP,
            "src/simulation.cpp",
            "block_control.propagate_states(dt, kpass, method)",
        ),
        (
            Language.RUST,
            "src/lib.rs",
            "self.block_control.propagate_states(dt, kpass, method)",
        ),
    ],
)
def test_model_reference_emits_propagation_and_camel_case_parameters(
    language: Language, path: str, call: str
):
    project = CodeGenerator().generate(
        _model("model_reference", {"naturalFrequency": 2.0, "dampingRatio": 0.8}),
        CodeGenerationConfig(language=language),
    )
    model_source = project.get_file(path)

    assert model_source is not None
    assert call in model_source.content

    block_path = {
        Language.PYTHON: "blocks.py",
        Language.C: "include/blocks.h",
        Language.CPP: "include/blocks.hpp",
        Language.RUST: "src/blocks.rs",
    }[language]
    block_source = project.get_file(block_path)
    assert block_source is not None
    assert "2.0" in block_source.content
    assert "0.8" in block_source.content
