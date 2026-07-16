"""Semantic parity tests for generated terminal control-analysis blocks."""

import asyncio
import json
from pathlib import Path

import pytest

from src.codegen.generator import CodeGenerationConfig, CodeGenerator
from src.codegen.models import Language
from src.codegen.validation import canonicalize_headless_results
from src.models.model import Model
from src.models.simulation import SimulationConfig
from src.simulation.runner import SimulationRunner

REPO_ROOT = Path(__file__).parents[2]

EXAMPLE_OUTPUTS = {
    "07a_bode_plot_analysis": [("bode1", 17.994407014304343)],
    "07b_nyquist_plot_analysis": [("nyquist1", -1.0)],
    "07c_pole_zero_map": [
        ("pz_stable", 1.0),
        ("pz_marginal", 0.0),
        ("pz_unstable", 0.0),
    ],
    "07d_step_response_info": [
        ("step_overdamped", 14.06),
        ("step_critical", 5.835),
        ("step_underdamped", 11.32),
    ],
}


def _load_example(name: str) -> dict:
    return json.loads((REPO_ROOT / "examples" / f"{name}.json").read_text())


def _config(model: dict, *, language: Language = Language.PYTHON) -> CodeGenerationConfig:
    simulation = model["simulationConfig"]
    return CodeGenerationConfig(
        language=language,
        project_name=model["id"],
        step_size=simulation["stepSize"],
        stop_time=simulation["stopTime"],
        start_time=simulation["startTime"],
    )


@pytest.mark.parametrize(("example", "expected"), EXAMPLE_OUTPUTS.items())
def test_analysis_examples_precompute_declared_scalar_outputs(example, expected):
    model = _load_example(example)
    info = CodeGenerator().compile_model_info(model, _config(model))
    analysis_blocks = [block for block in info.blocks if block.analysis_output is not None]

    assert [block.id for block in analysis_blocks] == [block_id for block_id, _ in expected]
    assert [block.analysis_output for block in analysis_blocks] == pytest.approx(
        [value for _, value in expected]
    )
    assert [signal.canonical_key for signal in info.output_signals] == [
        f"analysis={block_id}|out=0|element=scalar" for block_id, _ in expected
    ]
    assert all(signal.source_block_id == signal.sink_block_id for signal in info.output_signals)


def test_connected_transfer_function_coefficients_override_analysis_parameters():
    model = _load_example("07a_bode_plot_analysis")
    model["blocks"][1]["parameters"].update(
        {"numerator": [999.0], "denominator": [1.0]}
    )

    info = CodeGenerator().compile_model_info(model, _config(model))

    assert info.output_signals[0].canonical_key == "analysis=bode1|out=0|element=scalar"
    assert info.blocks[1].analysis_output == pytest.approx(17.994407014304343)


@pytest.mark.parametrize("language", list(Language))
@pytest.mark.parametrize(("example", "expected"), EXAMPLE_OUTPUTS.items())
def test_all_targets_emit_analysis_templates_and_output_columns(language, example, expected):
    model = _load_example(example)
    project = CodeGenerator().generate(model, _config(model, language=language))
    generated_text = "\n".join(
        file.content for file in project.files if not file.is_binary
    )

    assert "Passthrough (type:" not in generated_text
    assert "precomputed control analysis" in generated_text.lower()
    for block_id, value in expected:
        assert f"analysis={block_id}|out=0|element=scalar" in generated_text
        assert repr(value) in generated_text


@pytest.mark.parametrize(("example", "expected"), EXAMPLE_OUTPUTS.items())
def test_headless_analysis_payload_matches_canonical_output_schema(example, expected):
    model_data = _load_example(example)
    simulation = model_data["simulationConfig"]
    runner = SimulationRunner(
        Model.model_validate(model_data),
        SimulationConfig(
            step_size=simulation["stepSize"],
            stop_time=simulation["stopTime"],
        ),
    )
    asyncio.run(runner.run())
    results = runner.get_results()
    info = CodeGenerator().compile_model_info(model_data, _config(model_data))

    parsed = canonicalize_headless_results(results, info.output_signals)

    assert parsed.final_values == pytest.approx(
        {
            f"analysis={block_id}|out=0|element=scalar": value
            for block_id, value in expected
        }
    )
    assert {
        block_id: results["analyses"][block_id]["output"] for block_id, _ in expected
    } == pytest.approx(dict(expected))
