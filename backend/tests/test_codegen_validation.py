"""Tests for the strict generated-output validation contract."""

from io import StringIO

import pytest

from src.codegen.models import OutputSignalInfo
from src.codegen.validation import (
    FailureCategory,
    OutputValidationError,
    canonicalize_headless_results,
    compare_final_values,
    parse_results_csv,
)

ANALYSIS_SCHEMA = [
    OutputSignalInfo(
        canonical_key="analysis=analysis-1|out=0|element=scalar",
        sink_block_id="analysis-1",
        sink_input_port=0,
        source_block_id="analysis-1",
        source_output_port=0,
        dimensions=(1,),
        element_index=(0,),
        flat_index=0,
    )
]


def test_parse_results_csv_preserves_named_series():
    parsed = parse_results_csv(StringIO("time,b,a\n0,2,1\n1,4,3\n"))

    assert parsed.times == (0.0, 1.0)
    assert parsed.series == {"b": (2.0, 4.0), "a": (1.0, 3.0)}
    assert parsed.final_values == {"b": 4.0, "a": 3.0}


@pytest.mark.parametrize(
    ("contents", "category"),
    [
        ("", FailureCategory.MISSING_OR_EMPTY_OUTPUT_SET),
        ("time\n0\n", FailureCategory.MISSING_OR_EMPTY_OUTPUT_SET),
        ("time,value\n", FailureCategory.MISSING_OR_EMPTY_OUTPUT_SET),
        ("clock,value\n0,1\n", FailureCategory.MALFORMED_OUTPUT),
        ("time,,value\n0,1,2\n", FailureCategory.MALFORMED_OUTPUT),
        ("time,value,value\n0,1,2\n", FailureCategory.MALFORMED_OUTPUT),
        ("time,value\n0,1,2\n", FailureCategory.MALFORMED_OUTPUT),
        ("time,value\n0,nope\n", FailureCategory.MALFORMED_OUTPUT),
        ("time,value\n0,nan\n", FailureCategory.NONFINITE_OUTPUT),
    ],
)
def test_parse_results_csv_rejects_invalid_artifacts(contents: str, category: FailureCategory):
    with pytest.raises(OutputValidationError) as exc_info:
        parse_results_csv(StringIO(contents))

    assert exc_info.value.category == category


def test_compare_final_values_is_order_independent_but_key_strict():
    result = compare_final_values(
        {"first": 1.0, "second": 2.0},
        {"second": 2.0, "first": 1.0},
        tolerance=1e-6,
    )

    assert result.matches
    assert result.failure_category is None


def test_canonicalize_headless_analysis_uses_declared_scalar_output():
    parsed = canonicalize_headless_results(
        {
            "signals": [],
            "analyses": {"analysis-1": {"output": 2.5, "richData": [1, 2, 3]}},
            "statistics": {"finalTime": 4.0},
        },
        ANALYSIS_SCHEMA,
    )

    assert parsed.times == (4.0,)
    assert parsed.final_values == {"analysis=analysis-1|out=0|element=scalar": 2.5}


@pytest.mark.parametrize(
    ("analyses", "category"),
    [
        ({}, FailureCategory.MISSING_OR_EMPTY_OUTPUT_SET),
        ({"analysis-1": {}}, FailureCategory.MISSING_OR_EMPTY_OUTPUT_SET),
        ({"analysis-1": {"output": "nope"}}, FailureCategory.MALFORMED_OUTPUT),
        ({"analysis-1": {"output": float("nan")}}, FailureCategory.NONFINITE_OUTPUT),
    ],
)
def test_canonicalize_headless_analysis_rejects_invalid_outputs(analyses, category):
    with pytest.raises(OutputValidationError) as exc_info:
        canonicalize_headless_results(
            {"signals": [], "analyses": analyses, "statistics": {"finalTime": 1.0}},
            ANALYSIS_SCHEMA,
        )

    assert exc_info.value.category == category


@pytest.mark.parametrize(
    ("expected", "actual", "category", "missing", "unexpected"),
    [
        ({}, {}, FailureCategory.MISSING_OR_EMPTY_OUTPUT_SET, (), ()),
        ({"a": 1.0}, {}, FailureCategory.MISSING_OR_EMPTY_OUTPUT_SET, ("a",), ()),
        ({"a": 1.0, "b": 2.0}, {"a": 1.0}, FailureCategory.MISSING_OUTPUTS, ("b",), ()),
        ({"a": 1.0}, {"a": 1.0, "b": 2.0}, FailureCategory.UNEXPECTED_OUTPUTS, (), ("b",)),
        (
            {"a": 1.0},
            {"b": 1.0},
            FailureCategory.OUTPUT_KEY_MISMATCH,
            ("a",),
            ("b",),
        ),
    ],
)
def test_compare_final_values_rejects_output_set_mismatches(
    expected: dict[str, float],
    actual: dict[str, float],
    category: FailureCategory,
    missing: tuple[str, ...],
    unexpected: tuple[str, ...],
):
    result = compare_final_values(expected, actual, tolerance=1e-6)

    assert not result.matches
    assert result.failure_category == category
    assert result.missing_outputs == missing
    assert result.unexpected_outputs == unexpected


def test_compare_final_values_reports_named_numerical_mismatches():
    result = compare_final_values({"a": 10.0, "b": 2.0}, {"a": 12.0, "b": 2.0}, tolerance=0.01)

    assert not result.matches
    assert result.failure_category == FailureCategory.NUMERICAL_MISMATCH
    assert result.mismatched_outputs == ("a",)
    assert result.max_error == pytest.approx(0.2)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_compare_final_values_rejects_nonfinite_values(value: float):
    result = compare_final_values({"a": 1.0}, {"a": value}, tolerance=0.01)

    assert not result.matches
    assert result.failure_category == FailureCategory.NONFINITE_OUTPUT
    assert result.mismatched_outputs == ("a",)
