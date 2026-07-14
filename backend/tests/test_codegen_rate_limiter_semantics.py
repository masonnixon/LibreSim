"""Regression coverage for generated rate-limiter semantics."""

from collections.abc import Callable

import pytest

from src.codegen.generator import CodeGenerationConfig, CodeGenerator
from src.codegen.languages.c.blocks.signal_processing import (
    template_rate_limiter as c_rate_limiter_template,
)
from src.codegen.languages.cpp.blocks.signal_processing import (
    template_rate_limiter as cpp_rate_limiter_template,
)
from src.codegen.languages.python.blocks.signal_processing import rate_limiter_template
from src.codegen.languages.rust.blocks.signal_processing import (
    template_rate_limiter as rust_rate_limiter_template,
)
from src.codegen.models import BlockInfo, Language
from src.osk.blocks.signal_processing import RateLimiter
from src.osk.state import State


def _block() -> BlockInfo:
    return BlockInfo(
        id="rate",
        type="rate_limiter",
        name="Rate limiter",
        parameters={"risingLimit": 7.0, "fallingLimit": -3.0},
        input_connections=[],
        output_connections=[],
        execution_order=1,
    )


def _model() -> dict:
    return {
        "id": "rate-limiter-semantics",
        "metadata": {"name": "Rate limiter semantics", "description": ""},
        "blocks": [
            {
                "id": "source",
                "type": "constant",
                "name": "Source",
                "position": {"x": 0, "y": 0},
                "parameters": {"value": 2.0},
                "inputPorts": [],
                "outputPorts": [{"id": "source-out", "name": "out", "dimensions": [1]}],
            },
            {
                "id": "rate",
                "type": "rate_limiter",
                "name": "Rate limiter",
                "position": {"x": 100, "y": 0},
                "parameters": {"risingLimit": 7.0, "fallingLimit": -3.0},
                "inputPorts": [{"id": "rate-in", "name": "in", "dimensions": [1]}],
                "outputPorts": [{"id": "rate-out", "name": "out", "dimensions": [1]}],
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
                "id": "source-rate",
                "sourceBlockId": "source",
                "sourcePortId": "source-out",
                "targetBlockId": "rate",
                "targetPortId": "rate-in",
            },
            {
                "id": "rate-scope",
                "sourceBlockId": "rate",
                "sourcePortId": "rate-out",
                "targetBlockId": "scope",
                "targetPortId": "scope-in",
            },
        ],
        "simulationConfig": {
            "solver": "rk4",
            "startTime": 0.0,
            "stopTime": 1.0,
            "stepSize": 0.02,
        },
    }


def _noise_model() -> dict:
    model = _model()
    source = model["blocks"][0]
    source.update(
        {
            "id": "noise",
            "type": "white_noise",
            "name": "Noise",
            "parameters": {"mean": 0.0, "variance": 1.0, "seed": 42},
            "outputPorts": [{"id": "noise-out", "name": "out", "dimensions": [1]}],
        }
    )
    model["connections"][0].update(
        {"sourceBlockId": "noise", "sourcePortId": "noise-out"}
    )
    return model


@pytest.mark.parametrize(
    ("template", "class_name", "signature"),
    [
        (rate_limiter_template, "RateLimiter", "def update(self, t: float, dt: float)"),
        (c_rate_limiter_template, "RateLimiter", "double t, double dt"),
        (cpp_rate_limiter_template, "RateLimiter", "void update(double t, double dt)"),
        (rust_rate_limiter_template, "RateLimiter", "_t: f64, dt: f64"),
    ],
)
def test_rate_limiter_templates_use_model_parameters_and_runtime_dt(
    template: Callable[[BlockInfo, str], str], class_name: str, signature: str
):
    code = template(_block(), class_name)

    assert signature in code
    assert "7.0" in code
    assert "-3.0" in code
    assert "first_step" not in code
    assert "sample_time" not in code


def test_python_rate_limiter_matches_osk_updates(monkeypatch: pytest.MonkeyPatch):
    namespace: dict[str, object] = {}
    exec(rate_limiter_template(_block(), "GeneratedRateLimiter"), namespace)
    generated = namespace["GeneratedRateLimiter"]()
    osk = RateLimiter(rising_limit=7.0, falling_limit=-3.0)
    generated.init()
    osk.init()
    monkeypatch.setattr(State, "dt", 0.02)

    for index, value in enumerate((2.0, 2.0, -2.0, -2.0)):
        generated.input = value
        osk.setInput(value)
        generated.update(index * State.dt, State.dt)
        osk.update()
        assert generated.get_output() == pytest.approx(osk.getOutput())


@pytest.mark.parametrize(
    ("language", "path", "call"),
    [
        (Language.PYTHON, "simulation.py", "self.block_rate.update(t, dt)"),
        (Language.C, "src/simulation.c", "Block_rate_update(&model->block_rate, t, dt)"),
        (Language.CPP, "src/simulation.cpp", "block_rate.update(t, dt)"),
        (Language.RUST, "src/lib.rs", "self.block_rate.update(t, dt)"),
    ],
)
def test_models_pass_runtime_dt_to_rate_limiter(language: Language, path: str, call: str):
    project = CodeGenerator().generate(_model(), CodeGenerationConfig(language=language))
    source = project.get_file(path)

    assert source is not None
    assert call in source.content


def test_ready_only_blocks_are_classified_from_shared_metadata():
    model_info = CodeGenerator().compile_model_info(_noise_model(), CodeGenerationConfig())

    blocks = {block.id: block for block in model_info.blocks}
    assert blocks["noise"].ready_only
    assert not blocks["rate"].ready_only


@pytest.mark.parametrize(
    ("language", "main_path", "model_path", "ready_call", "stage_call", "gate"),
    [
        (
            Language.PYTHON,
            "simulation.py",
            "simulation.py",
            "model.step(t, dt, 0, True)",
            "model.step(t + stage_offsets[kpass] * dt, dt, kpass, False)",
            "if ready:\n            self.block_noise.update(t)",
        ),
        (
            Language.C,
            "src/main.c",
            "src/simulation.c",
            "model_step(&model, t, dt, 0, 1)",
            "model_step(&model, t + stage_offsets[kpass] * dt, dt, kpass, 0)",
            "if (ready) { Block_noise_update(&model->block_noise, t); }",
        ),
        (
            Language.CPP,
            "src/main.cpp",
            "src/simulation.cpp",
            "model.step(t, dt, 0, true)",
            "model.step(t + stage_offsets[kpass] * dt, dt, kpass, false)",
            "if (ready) { block_noise.update(t); }",
        ),
        (
            Language.RUST,
            "src/main.rs",
            "src/lib.rs",
            "model.step(t, dt, 0, true)",
            "model.step(t + stage_offsets[kpass] * dt, dt, kpass, false)",
            "if ready { self.block_noise.update(t); }",
        ),
    ],
)
def test_generated_schedulers_separate_ready_and_integration_phases(
    language: Language,
    main_path: str,
    model_path: str,
    ready_call: str,
    stage_call: str,
    gate: str,
):
    project = CodeGenerator().generate(_noise_model(), CodeGenerationConfig(language=language))
    main = project.get_file(main_path)
    generated_model = project.get_file(model_path)

    assert main is not None
    assert generated_model is not None
    assert ready_call in main.content
    assert stage_call in main.content
    assert gate in generated_model.content
