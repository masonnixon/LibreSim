"""Strict parsing and comparison helpers for generated simulation outputs."""

from __future__ import annotations

import csv
import math
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TextIO


class FailureCategory(StrEnum):
    """Machine-readable generated-output failure categories."""

    MISSING_OR_EMPTY_OUTPUT_SET = "missing_or_empty_output_set"
    MALFORMED_OUTPUT = "malformed_output"
    NONFINITE_OUTPUT = "nonfinite_output"
    MISSING_OUTPUTS = "missing_outputs"
    UNEXPECTED_OUTPUTS = "unexpected_outputs"
    OUTPUT_KEY_MISMATCH = "output_key_mismatch"
    NUMERICAL_MISMATCH = "numerical_mismatch"


class OutputValidationError(ValueError):
    """Raised when a generated output artifact violates the structural contract."""

    def __init__(self, category: FailureCategory, message: str):
        super().__init__(message)
        self.category = category


@dataclass(frozen=True)
class ParsedOutput:
    """A validated results CSV with one scalar series per canonical output key."""

    times: tuple[float, ...]
    series: dict[str, tuple[float, ...]]

    @property
    def final_values(self) -> dict[str, float]:
        """Return the last finite sample for every output series."""
        return {key: values[-1] for key, values in self.series.items()}


@dataclass(frozen=True)
class OutputComparison:
    """Result of comparing two canonical final-value maps."""

    matches: bool
    max_error: float = 0.0
    failure_category: FailureCategory | None = None
    missing_outputs: tuple[str, ...] = ()
    unexpected_outputs: tuple[str, ...] = ()
    mismatched_outputs: tuple[str, ...] = ()


def parse_results_csv(stream: TextIO) -> ParsedOutput:
    """Parse a generated results CSV without discarding malformed or duplicate data."""
    rows = csv.reader(stream)
    try:
        header = next(rows)
    except StopIteration as exc:
        raise OutputValidationError(
            FailureCategory.MISSING_OR_EMPTY_OUTPUT_SET,
            "Results CSV is empty",
        ) from exc

    if not header or header[0] != "time":
        raise OutputValidationError(
            FailureCategory.MALFORMED_OUTPUT,
            "Results CSV must start with a 'time' column",
        )
    if len(header) == 1:
        raise OutputValidationError(
            FailureCategory.MISSING_OR_EMPTY_OUTPUT_SET,
            "Results CSV contains no output columns",
        )
    if any(not key for key in header[1:]):
        raise OutputValidationError(
            FailureCategory.MALFORMED_OUTPUT,
            "Results CSV contains an empty output key",
        )

    duplicate_keys = sorted({key for key in header if header.count(key) > 1})
    if duplicate_keys:
        raise OutputValidationError(
            FailureCategory.MALFORMED_OUTPUT,
            f"Results CSV contains duplicate columns: {duplicate_keys}",
        )

    times: list[float] = []
    series: dict[str, list[float]] = {key: [] for key in header[1:]}
    for row_number, row in enumerate(rows, start=2):
        if len(row) != len(header):
            raise OutputValidationError(
                FailureCategory.MALFORMED_OUTPUT,
                f"Results CSV row {row_number} has {len(row)} columns; expected {len(header)}",
            )
        try:
            values = [float(value) for value in row]
        except ValueError as exc:
            raise OutputValidationError(
                FailureCategory.MALFORMED_OUTPUT,
                f"Results CSV row {row_number} contains a non-numeric value",
            ) from exc
        if not all(math.isfinite(value) for value in values):
            raise OutputValidationError(
                FailureCategory.NONFINITE_OUTPUT,
                f"Results CSV row {row_number} contains a non-finite value",
            )

        times.append(values[0])
        for key, value in zip(header[1:], values[1:], strict=True):
            series[key].append(value)

    if not times:
        raise OutputValidationError(
            FailureCategory.MISSING_OR_EMPTY_OUTPUT_SET,
            "Results CSV contains no data rows",
        )

    return ParsedOutput(
        times=tuple(times),
        series={key: tuple(values) for key, values in series.items()},
    )


def read_results_csv(path: Path) -> ParsedOutput:
    """Read and strictly parse a generated results CSV file."""
    with path.open(newline="") as stream:
        return parse_results_csv(stream)


def compare_final_values(
    expected: Mapping[str, float],
    actual: Mapping[str, float],
    *,
    tolerance: float,
) -> OutputComparison:
    """Compare finite scalar outputs by exact key identity and numerical tolerance."""
    if not expected or not actual:
        return OutputComparison(
            matches=False,
            failure_category=FailureCategory.MISSING_OR_EMPTY_OUTPUT_SET,
            missing_outputs=tuple(sorted(set(expected) - set(actual))),
            unexpected_outputs=tuple(sorted(set(actual) - set(expected))),
        )

    missing = tuple(sorted(set(expected) - set(actual)))
    unexpected = tuple(sorted(set(actual) - set(expected)))
    if missing or unexpected:
        if missing and unexpected:
            category = FailureCategory.OUTPUT_KEY_MISMATCH
        elif missing:
            category = FailureCategory.MISSING_OUTPUTS
        else:
            category = FailureCategory.UNEXPECTED_OUTPUTS
        return OutputComparison(
            matches=False,
            failure_category=category,
            missing_outputs=missing,
            unexpected_outputs=unexpected,
        )

    max_error = 0.0
    mismatched: list[str] = []
    for key in sorted(expected):
        expected_value = expected[key]
        actual_value = actual[key]
        if not math.isfinite(expected_value) or not math.isfinite(actual_value):
            return OutputComparison(
                matches=False,
                failure_category=FailureCategory.NONFINITE_OUTPUT,
                mismatched_outputs=(key,),
            )

        absolute_difference = abs(expected_value - actual_value)
        if abs(expected_value) < 1e-6 and abs(actual_value) < 1e-6:
            error = 0.0 if absolute_difference < 1e-6 else absolute_difference
        elif abs(expected_value) > 1e-10:
            error = absolute_difference / abs(expected_value)
        else:
            error = absolute_difference

        max_error = max(max_error, error)
        if error > tolerance:
            mismatched.append(key)

    if mismatched:
        return OutputComparison(
            matches=False,
            max_error=max_error,
            failure_category=FailureCategory.NUMERICAL_MISMATCH,
            mismatched_outputs=tuple(mismatched),
        )
    return OutputComparison(matches=True, max_error=max_error)
