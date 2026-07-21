"""Behavioral coverage for shared code-generation analysis and DSP helpers."""

import math

import pytest

from src.codegen import analysis, filter_design
from src.codegen.analysis import compute_analysis_output
from src.codegen.dsp_utils import window_coefficients
from src.codegen.filter_design import BiquadCoefficients, design_analog_filter
from src.codegen.models import BlockInfo


def block(block_id="analysis", block_type="bode_plot", parameters=None, connections=None):
    return BlockInfo(
        id=block_id,
        type=block_type,
        name=block_id,
        parameters=parameters or {},
        input_connections=connections or [],
        output_connections=[],
        execution_order=0,
    )


def test_analysis_rejects_unsupported_and_nonfinite_results(monkeypatch):
    with pytest.raises(ValueError, match="Unsupported analysis block type: gain"):
        compute_analysis_output(block(block_type="gain"), {})

    class NonFiniteAnalysis:
        def __init__(self, **parameters):
            assert parameters == {}

        def init(self):
            pass

        def getOutput(self):
            return math.inf

    monkeypatch.setitem(analysis._ANALYSIS_CLASSES, "bode_plot", NonFiniteAnalysis)
    with pytest.raises(ValueError, match="analysis.*non-finite output inf"):
        compute_analysis_output(block(), {})


def test_analysis_connection_parsing_and_transfer_function_override():
    target = block(
        parameters={"numerator": [99.0], "ignored": "value"},
        connections=[
            "malformed",
            "transfer:0@1",
            "missing:0@0",
            "gain:0@0",
            "transfer:0@0",
        ],
    )
    transfer = block(
        "transfer",
        "transfer_function",
        {"numerator": [1.0], "denominator": [1.0, 1.0]},
    )
    output = compute_analysis_output(target, {"gain": block("gain", "gain"), "transfer": transfer})
    assert math.isfinite(output)

    numerator_only = block("tf", "transfer_function", {"numerator": [2.0]})
    output = compute_analysis_output(
        block(connections=["tf:0@0"]),
        {"tf": numerator_only},
    )
    assert math.isfinite(output)


@pytest.mark.parametrize(
    ("window_type", "expected"),
    [
        ("rectangular", [1.0, 1.0, 1.0, 1.0]),
        ("hanning", [0.0, 0.75, 0.75, 0.0]),
        ("hamming", [0.08, 0.77, 0.77, 0.08]),
        ("blackman", [0.0, 0.63, 0.63, 0.0]),
        ("unknown", [1.0, 1.0, 1.0, 1.0]),
    ],
)
def test_window_coefficients_match_reference_formulas(window_type, expected):
    assert window_coefficients(window_type, 4) == pytest.approx(expected, abs=1e-12)


def test_kaiser_coefficients_are_symmetric_and_bounded():
    coefficients = window_coefficients("kaiser", 5, beta=100.0)
    assert coefficients == pytest.approx(list(reversed(coefficients)))
    assert coefficients[2] == pytest.approx(1.0)
    assert all(0.0 <= value <= 1.0 for value in coefficients)


def test_filter_design_guards_fallbacks_and_response_modes():
    assert design_analog_filter({}, 0.0) == [BiquadCoefficients(1.0, 0.0, 0.0, 0.0, 0.0)]

    fallback = design_analog_filter(
        {"design": "unknown", "response": "lowpass", "order": 1},
        0.01,
    )
    assert len(fallback) == 1
    assert fallback[0].b0 == pytest.approx(fallback[0].b1)

    # Orders above the Bessel lookup table use the radial fallback pole distribution.
    bessel = design_analog_filter(
        {"design": "bessel", "response": "highpass", "order": 6},
        0.01,
    )
    assert len(bessel) == 3
    assert bessel[0].b0 == pytest.approx(bessel[0].b2)
    assert bessel[0].b1 == pytest.approx(-2 * bessel[0].b0)

    bandpass = design_analog_filter(
        {
            "design": "butterworth",
            "response": "bandpass",
            "order": 2,
            "lowCutoff": 2.0,
            "highCutoff": 8.0,
        },
        0.01,
    )
    assert len(bandpass) == 1
    assert bandpass[0].b1 == 0.0
    assert bandpass[0].b2 == pytest.approx(-bandpass[0].b0)


def test_filter_design_defensively_falls_back_for_degenerate_poles(monkeypatch):
    cutoff = 10.0
    step_size = 0.01
    zero_denominator_pole = (2 / step_size) / (2 * math.pi * cutoff)
    monkeypatch.setattr(
        filter_design,
        "_butterworth_poles",
        lambda order: [complex(zero_denominator_pole, 0.0)],
    )
    assert design_analog_filter({"cutoffFrequency": cutoff}, step_size) == [
        BiquadCoefficients(1.0, 0.0, 0.0, 0.0, 0.0)
    ]

    monkeypatch.setattr(
        filter_design,
        "_butterworth_poles",
        lambda order: [complex(math.nan, math.nan)],
    )
    assert design_analog_filter({}, step_size) == [
        BiquadCoefficients(1.0, 0.0, 0.0, 0.0, 0.0)
    ]
