"""Regression tests for RF simulation and generated-code semantics."""

import json
from pathlib import Path

import pytest

from src.codegen.generator import CodeGenerationConfig, CodeGenerator
from src.codegen.languages.python.blocks.rf import (
    am_modulator_template,
    rf_budget_element_template,
)
from src.codegen.models import BlockInfo, Language
from src.models.model import Model
from src.models.simulation import SimulationConfig, SolverType
from src.osk.blocks.rf import AMModulator, RFBudgetElement
from src.osk.blocks.sources import Constant
from src.simulation.compiler import ModelCompiler
from src.simulation.osk_adapter import OSKAdapter

REPO_ROOT = Path(__file__).parents[2]


def _block(block_type: str, parameters: dict, inputs: int, outputs: int = 1) -> BlockInfo:
    return BlockInfo(
        id="rf-block",
        type=block_type,
        name="RF Block",
        parameters=parameters,
        input_connections=[],
        output_connections=[],
        execution_order=0,
        input_dimensions=[[1]] * inputs,
        output_dimensions=[[1]] * outputs,
    )


def test_rf_budget_cascade_matches_friis_equation() -> None:
    """A multi-stage budget must preserve power, gain, and Friis NF independently."""
    power = -80.0
    gain = 0.0
    noise_figure = 0.0

    for element_gain, element_nf in [(15.0, 1.5), (-2.0, 2.0), (-6.0, 8.0), (20.0, 4.0)]:
        element = RFBudgetElement(gain_db=element_gain, noise_figure_db=element_nf)
        element.init()
        element.setInput(power, 0)
        element.setInput(gain, 1)
        element.setInput(noise_figure, 2)
        element.update()
        power, gain, noise_figure = element.getOutputVector()

    assert power == pytest.approx(-53.0)
    assert gain == pytest.approx(27.0)
    assert noise_figure == pytest.approx(3.007701091)


def test_am_modulator_uses_external_carrier_when_connected() -> None:
    """The optional second port must multiply the envelope by the wired carrier."""
    message = Constant(value=0.5)
    carrier = Constant(value=-0.25)
    modulator = AMModulator(modulation_index=0.8)
    message.init()
    carrier.init()
    modulator.connectInput(message, 0)
    modulator.connectInput(carrier, 1)
    modulator.init()
    message.update()
    carrier.update()
    modulator.update()

    assert modulator.getOutput() == pytest.approx(-0.35)


def test_compiler_and_adapter_route_declared_named_ports() -> None:
    """Named RF port IDs must resolve to their declared positions, not port zero."""
    model_data = json.loads((REPO_ROOT / "examples/42_rf_receiver_chain.json").read_text())
    compiled = ModelCompiler().compile(Model.model_validate(model_data))
    assert compiled.success

    lna = next(block for block in compiled.blocks if block.id == "lna")
    assert lna.input_port_ids == ["lna-power", "lna-gain", "lna-nf"]
    assert lna.output_port_ids == ["lna-pout", "lna-gainout", "lna-nfout"]

    adapter = OSKAdapter()
    adapter.initialize(
        compiled,
        SimulationConfig(solver=SolverType.EULER, stop_time=0.01, step_size=0.01),
    )
    adapter.step(0.0, 0.01)
    final_element = adapter.get_block("if_amp")
    assert final_element.getOutput(0) == pytest.approx(-53.0)
    assert final_element.getOutput(1) == pytest.approx(27.0)
    assert final_element.getOutput(2) == pytest.approx(3.007701091)


def test_python_rf_templates_execute_canonical_equations() -> None:
    """Python templates must implement RF equations rather than passthrough."""
    namespace: dict[str, object] = {}
    exec(
        rf_budget_element_template(
            _block(
                "rf_budget_element",
                {"gainDb": 5.0, "noiseFigureDb": 6.0},
                inputs=3,
                outputs=3,
            ),
            "Budget",
        ),
        namespace,
    )
    budget_type = namespace["Budget"]
    budget = budget_type()
    budget.input = -20.0
    budget.input1 = 10.0
    budget.input2 = 3.0
    budget.update(0.0)
    assert budget.get_output(0) == pytest.approx(-15.0)
    assert budget.get_output(1) == pytest.approx(15.0)

    namespace = {}
    exec(
        am_modulator_template(
            _block("am_modulator", {"modulationIndex": 0.8}, inputs=2), "AM"
        ),
        namespace,
    )
    am_type = namespace["AM"]
    am = am_type()
    am.input = 0.5
    am.input1 = -0.25
    am.update(0.0)
    assert am.get_output() == pytest.approx(-0.35)


@pytest.mark.parametrize("language", list(Language))
@pytest.mark.parametrize("example", ["42_rf_receiver_chain.json", "43_rf_am_modulation.json"])
def test_rf_examples_use_real_templates(language: Language, example: str) -> None:
    """Every target registry must emit RF implementations, never passthrough blocks."""
    model_data = json.loads((REPO_ROOT / "examples" / example).read_text())
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

    assert "Passthrough (type: rf_budget_element)" not in source
    assert "Passthrough (type: am_modulator)" not in source
    if example.startswith("42_"):
        assert "noise_figure" in source
    else:
        assert "modulation_index" in source
