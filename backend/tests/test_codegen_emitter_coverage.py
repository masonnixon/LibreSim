"""Contract tests that keep every language emitter callable and named."""

import importlib
import inspect
from dataclasses import replace

import pytest

from src.codegen.models import BlockInfo

EMITTER_MODULES = [
    f"src.codegen.languages.{language}.blocks.{family}"
    for language in ("c", "cpp", "python", "rust")
    for family in (
        "aerospace",
        "continuous",
        "control_analysis",
        "control_design",
        "discrete",
        "dsp",
        "estimation",
        "logic",
        "math_ops",
        "nonlinear",
        "rf",
        "sensor_fusion",
        "signal_processing",
        "sinks",
        "sources",
    )
]


def _emitter_functions():
    emitters = []
    for module_name in EMITTER_MODULES:
        module = importlib.import_module(module_name)
        for name, function in inspect.getmembers(module, inspect.isfunction):
            if function.__module__ != module_name or name.startswith("_"):
                continue
            parameters = list(inspect.signature(function).parameters.values())
            if len(parameters) >= 2 and parameters[0].name == "block":
                emitters.append(pytest.param(function, id=f"{module_name.split('.')[-3]}-{name}"))
    return emitters


@pytest.fixture
def representative_block():
    """Supply valid scalar defaults plus matrices used by specialized emitters."""
    return BlockInfo(
        id="block-1",
        type="representative",
        name="Representative",
        parameters={
            "value": 1.25,
            "initial_value": 0.0,
            "final_value": 1.0,
            "step_time": 0.5,
            "slope": 2.0,
            "start_time": 0.0,
            "amplitude": 1.0,
            "frequency": 2.0,
            "phase": 0.0,
            "bias": 0.0,
            "period": 1.0,
            "pulse_width": 50.0,
            "seed": 42,
            "sample_time": 0.01,
            "noise_power": 0.1,
            "bandwidth": 10.0,
            "initial_condition": 0.0,
            "numerator": [1.0, 0.5],
            "denominator": [1.0, 0.25],
            "A": [[0.0]],
            "B": [[1.0]],
            "C": [[1.0]],
            "D": [[0.0]],
            "wn": 2.0,
            "zeta": 0.7,
            "delay": 0.1,
            "gain": 2.0,
            "kp": 1.0,
            "ki": 0.5,
            "kd": 0.25,
            "lower_limit": -10.0,
            "upper_limit": 10.0,
            "anti_windup_gain": 1.0,
            "zero": 1.0,
            "pole": 2.0,
            "K": [[1.0]],
            "L": [[1.0]],
            "reference_gain": 1.0,
            "operation": "AND",
            "operator": ">",
            "threshold": 0.0,
            "n_points": 4,
            "window_type": "hamming",
            "length": 4,
            "beta": 5.0,
            "coefficients": [0.5, 0.5],
            "factor": 2,
            "window_size": 3,
            "direction": "both",
            "alpha": 0.5,
            "gamma": 0.1,
            "process_noise": 0.01,
            "measurement_noise": 0.1,
            "initial_covariance": 1.0,
            "carrier_frequency": 1000.0,
            "modulation_index": 0.5,
            "noise_figure": 2.0,
            "input_power": 0.0,
            "temperature": 290.0,
            "euler_sequence": "ZYX",
            "reference_lla": [0.0, 0.0, 0.0],
            "waypoints": [[0.0, 0.0], [1.0, 1.0]],
            "acceptance_radius": 10.0,
        },
        input_connections=["source:0@0", "source:0@1", "source:0@2"],
        output_connections=["sink:0"],
        execution_order=0,
        input_dimensions=[[1], [1], [1]],
        output_dimensions=[[1]],
        step_size=0.01,
        analysis_output=1.0,
    )


@pytest.mark.parametrize("emitter", _emitter_functions())
def test_emitter_returns_named_nonempty_source(emitter, representative_block):
    source = emitter(representative_block, "GeneratedBlock")
    assert isinstance(source, str)
    assert len(source) > 30
    assert "GeneratedBlock" in source


@pytest.mark.parametrize("emitter", _emitter_functions())
def test_emitter_parameter_defaults_return_named_source(emitter, representative_block):
    default_block = replace(
        representative_block,
        parameters={},
        input_connections=[],
        output_connections=[],
        input_dimensions=[],
        output_dimensions=[],
        analysis_output=None,
    )
    if emitter.__name__ == "control_analysis_template":
        with pytest.raises(ValueError, match="block-1.*not precomputed"):
            emitter(default_block, "DefaultBlock")
        return
    source = emitter(default_block, "DefaultBlock")
    assert isinstance(source, str)
    assert len(source) > 30
    assert "DefaultBlock" in source


@pytest.mark.parametrize("emitter", _emitter_functions())
def test_emitter_edge_variants_return_named_source(emitter, representative_block):
    """Exercise the documented shape and enum alternatives shared by emitters."""
    name = emitter.__name__
    variants = []

    if "logical_operator" in name:
        for operator in ("OR", "NAND", "NOR", "XOR", "NOT", "unsupported"):
            variants.append({"operator": operator, "numInputs": 3})
    elif "transfer_function" in name:
        variants.append({"numerator": 1.0, "denominator": 0.0})
    elif "state_space" in name:
        variants.extend(
            [
                {"A": [], "B": [], "C": [], "D": []},
                {"A": [1.0], "B": [1.0], "C": [1.0], "D": [0.0]},
            ]
        )
    elif name in {"template_sum", "sum_template"}:
        variants.append({"signs": "+-"})
    elif name in {"template_product", "product_template"}:
        variants.append({"inputs": "*/"})
    elif "fir_filter" in name:
        variants.append({"coefficients": 2.0})
    elif "iir_filter" in name:
        variants.append({"numerator": 1.0, "denominator": 2.0})
    elif "zero_crossing_detector" in name:
        variants.extend([{"direction": "rising"}, {"direction": "falling"}])
    elif "band_limited_white_noise" in name:
        variants.append({"sampleTime": 0.0, "noisePower": 0.1})
    elif "constant" in name:
        variants.append({"value": [1.0, 2.0]})
    elif "scope" in name:
        variants.append({"numInputs": 3})

    blocks = [replace(representative_block, parameters=params) for params in variants]
    if "gain" in name:
        blocks.append(replace(representative_block, input_dimensions=[[3]]))

    if not blocks:
        blocks = [representative_block]

    for block in blocks:
        source = emitter(block, "VariantBlock")
        assert isinstance(source, str)
        assert len(source) > 30
        assert "VariantBlock" in source
