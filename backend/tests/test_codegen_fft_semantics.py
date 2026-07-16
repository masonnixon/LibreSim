"""Regression tests for generated frame window and FFT semantics."""

import json
import math
from pathlib import Path

import pytest

from src.codegen.generator import CodeGenerationConfig, CodeGenerator
from src.codegen.languages.python.blocks.dsp import fft_template, window_function_template
from src.codegen.models import BlockInfo, Language
from src.osk.blocks.dsp import FFT, WindowFunction

REPO_ROOT = Path(__file__).parents[2]
EXAMPLE_PATH = REPO_ROOT / "examples/40_dsp_fft_spectrum.json"


def _block(
    block_type: str,
    parameters: dict,
    input_width: int,
    output_width: int,
) -> BlockInfo:
    return BlockInfo(
        id=block_type,
        type=block_type,
        name=block_type.replace("_", " ").title(),
        parameters=parameters,
        input_connections=[],
        output_connections=[],
        execution_order=0,
        input_dimensions=[[input_width]],
        output_dimensions=[[output_width]],
    )


def test_python_window_and_fft_templates_match_osk() -> None:
    """Generated Python must preserve the OSK frame and interleaved DFT contract."""
    model = json.loads(EXAMPLE_PATH.read_text())
    frame = next(block for block in model["blocks"] if block["id"] == "fft_frame")[
        "parameters"
    ]["value"]

    osk_window = WindowFunction(window_type="hamming", length=64)
    osk_fft = FFT(n_points=64)
    osk_window.init()
    osk_window.setInput(frame)
    osk_window.update()
    osk_fft.init()
    osk_fft.setInput(osk_window.getOutputVector())
    osk_fft.update()

    namespace = {"math": math}
    exec(
        window_function_template(
            _block("window_function", {"windowType": "hamming", "length": 64}, 64, 64),
            "GeneratedWindow",
        ),
        namespace,
    )
    exec(
        fft_template(_block("fft", {"nPoints": 64}, 64, 128), "GeneratedFFT"),
        namespace,
    )
    generated_window = namespace["GeneratedWindow"]()
    generated_window.input = list(frame)
    generated_window.update(0.0)
    generated_fft = namespace["GeneratedFFT"]()
    generated_fft.input = generated_window.get_output_vector()
    generated_fft.update(0.0)

    assert generated_window.get_output_vector() == pytest.approx(osk_window.getOutputVector())
    assert generated_fft.get_output_vector() == pytest.approx(osk_fft.getOutputVector())
    assert generated_fft.get_output(20) == pytest.approx(-0.0006577245, abs=1e-9)
    assert generated_fft.get_output(21) == pytest.approx(-17.0500873978, abs=1e-9)
    assert generated_fft.get_output(50) == pytest.approx(0.0010693130, abs=1e-9)
    assert generated_fft.get_output(51) == pytest.approx(-8.5252600342, abs=1e-9)


@pytest.mark.parametrize("language", list(Language))
def test_fft_example_uses_real_templates_and_128_element_spectrum(language: Language) -> None:
    """Every target must emit real frame DSP blocks and the canonical spectrum schema."""
    model = json.loads(EXAMPLE_PATH.read_text())
    generator = CodeGenerator()
    config = CodeGenerationConfig(
        language=language,
        step_size=model["simulationConfig"]["stepSize"],
        stop_time=model["simulationConfig"]["stopTime"],
    )
    model_info = generator.compile_model_info(model, config)
    frequency_outputs = [
        signal
        for signal in model_info.output_signals
        if signal.sink_block_id == "scope_freq"
    ]
    assert len(frequency_outputs) == 128

    project = generator.generate(model, config)
    source = "\n".join(
        generated.content
        for generated in project.files
        if isinstance(generated.content, str)
    )
    assert "Passthrough (type: window_function)" not in source
    assert "Passthrough (type: fft)" not in source
    assert "real_sum" in source
    assert "imag_sum" in source
