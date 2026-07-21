"""Focused edge coverage for the final parser and validation layers."""

import pytest

from src.codegen.models import OutputSignalInfo
from src.codegen.validation import (
    FailureCategory,
    OutputValidationError,
    canonicalize_headless_results,
    compare_final_values,
    read_results_csv,
)
from src.models.block import Block, Port, Position
from src.models.model import Model, ModelMetadata
from src.models.simulation import SimulationConfig
from src.parsers.mdl_parser import MDLParser
from src.services.model_service import ModelService


def _signal(key: str = "sink=scope", sink: str = "scope") -> OutputSignalInfo:
    return OutputSignalInfo(key, sink, 0, "source", 0, (1,), (0,), 0)


def test_read_results_csv_and_validation_edges(tmp_path):
    results = tmp_path / "results.csv"
    results.write_text("time,sink=scope\n0,1\n")
    assert read_results_csv(results).final_values == {"sink=scope": 1.0}

    signal = _signal()
    malformed_cases = [
        ({"signals": 1}, FailureCategory.MALFORMED_OUTPUT),
        ({"signals": [1]}, FailureCategory.MALFORMED_OUTPUT),
        ({"signals": [{"blockId": "scope", "times": 1}]}, FailureCategory.MALFORMED_OUTPUT),
        (
            {"signals": [{"blockId": "scope", "times": ["bad"], "values": [1]}]},
            FailureCategory.MALFORMED_OUTPUT,
        ),
        (
            {
                "signals": [
                    {"blockId": "scope", "times": [0], "values": [1]},
                    {"blockId": "scope", "times": [0], "values": [1]},
                ]
            },
            FailureCategory.MALFORMED_OUTPUT,
        ),
        (
            {"signals": [{"blockId": "scope", "times": [0], "values": object()}]},
            FailureCategory.MALFORMED_OUTPUT,
        ),
        (
            {"signals": [{"blockId": "scope", "times": [0], "values": ["bad"]}]},
            FailureCategory.MALFORMED_OUTPUT,
        ),
        (
            {"signals": [{"blockId": "scope", "times": [0, 1], "values": [1]}]},
            FailureCategory.OUTPUT_SHAPE_MISMATCH,
        ),
        (
            {"signals": [{"blockId": "scope", "times": [], "values": []}]},
            FailureCategory.MISSING_OR_EMPTY_OUTPUT_SET,
        ),
        (
            {"signals": [{"blockId": "scope", "times": [0], "values": [float("inf")]}]},
            FailureCategory.NONFINITE_OUTPUT,
        ),
        ({"analyses": 1}, FailureCategory.MALFORMED_OUTPUT),
    ]
    for payload, category in malformed_cases:
        with pytest.raises(OutputValidationError) as exc_info:
            canonicalize_headless_results(payload, [signal])
        assert exc_info.value.category == category


def test_headless_shape_time_grid_and_analysis_edges():
    first = _signal("sink=one", "one")
    second = _signal("sink=two", "two")
    with pytest.raises(OutputValidationError, match="produced 3 traces"):
        canonicalize_headless_results(
            {"signals": [{"blockId": "one", "times": [0], "is3D": True}]}, [first]
        )
    with pytest.raises(OutputValidationError, match="different time grid"):
        canonicalize_headless_results(
            {
                "signals": [
                    {"blockId": "one", "times": [0], "values": [1]},
                    {"blockId": "two", "times": [1], "values": [2]},
                ]
            },
            [first, second],
        )

    analysis = _signal("analysis=analysis|out=0|element=scalar", "analysis")
    analysis2 = OutputSignalInfo(
        "analysis=analysis|out=1|element=scalar", "analysis", 0, "analysis", 1, (1,), (0,), 0
    )
    cases = [
        ([analysis, analysis2], {"analyses": {"analysis": {"output": 1}}}, "exactly one"),
        ([analysis], {}, "no declared scalar"),
        ([analysis], {"analyses": {"analysis": {"output": "bad"}}}, "non-numeric scalar"),
        ([analysis], {"analyses": {"analysis": {"output": float("nan")}}}, "non-finite"),
        (
            [analysis],
            {"analyses": {"analysis": {"output": 1}}, "statistics": {"finalTime": "bad"}},
            "non-numeric final time",
        ),
    ]
    for schema, payload, message in cases:
        with pytest.raises(OutputValidationError, match=message):
            canonicalize_headless_results(payload, schema)

    parsed = canonicalize_headless_results(
        {"analyses": {"analysis": {"output": 2}}, "statistics": []}, [analysis]
    )
    assert parsed.times == (0.0,)
    assert parsed.final_values[analysis.canonical_key] == 2.0

    combined = canonicalize_headless_results(
        {
            "signals": [
                {"blockId": "unknown", "times": [0], "values": [9]},
                {"blockId": "one", "times": [0], "values": [1]},
            ],
            "analyses": {"analysis": {"output": 2}},
        },
        [first, analysis],
    )
    assert combined.final_values == {"sink=one": 1.0, analysis.canonical_key: 2.0}
    assert canonicalize_headless_results({}, [first]).series == {}


def test_compare_final_value_edge_categories():
    assert compare_final_values({"a": 1}, {"b": 1}, tolerance=0).failure_category == (
        FailureCategory.OUTPUT_KEY_MISMATCH
    )
    assert compare_final_values({"a": 1}, {"a": 1, "b": 2}, tolerance=0).failure_category == (
        FailureCategory.UNEXPECTED_OUTPUTS
    )
    assert compare_final_values({"a": 0.0}, {"a": 2e-6}, tolerance=0).max_error == 2e-6
    assert compare_final_values({"a": 0.0}, {"a": 0.0}, tolerance=0).matches


def test_mdl_lexer_unterminated_and_repeated_blocks():
    parser = MDLParser()
    parser._content = "A { } A { } A { }"
    parser._pos = 0
    assert len(parser._parse_block()["A"]) == 3

    parser._content = "Key"
    parser._pos = 0
    assert parser._parse_block() == {}

    parser._content = '"unterminated'
    parser._pos = 0
    assert parser._parse_quoted_string() == "unterminated"
    parser._content = "[1, 2"
    parser._pos = 0
    assert parser._parse_array() == "[1, 2"


def test_mdl_conversion_edge_cases():
    parser = MDLParser()
    assert parser._parse_position("bad, position").x == 100.0
    assert parser._convert_product_inputs("") == "**"
    assert parser._convert_product_inputs("3") == "***"
    assert parser._convert_product_inputs("*|/") == "*/"
    assert parser._convert_product_inputs("invalid") == "invalid"
    assert parser._convert_value("[1,bad]") == "[1,bad]"

    assert parser._extract_parameters({"Inputs": "3"}, "product") == {"operations": "***"}
    assert parser._extract_parameters({"ExternalReset": "rising"}, "integrator") == {
        "externalIC": True
    }
    assert parser._extract_parameters({"ExternalReset": 0}, "integrator") == {"externalIC": False}

    inputs, _ = parser._create_ports("product", "p", {"operations": "***/"})
    assert len(inputs) == 4
    inputs, _ = parser._create_ports("integrator", "i", {"externalIC": True})
    assert [port.name for port in inputs] == ["in", "x0"]


def test_mdl_unknown_blocks_invalid_connections_and_solver_fallback():
    parser = MDLParser()
    assert parser._parse_blocks({"Block": [{"BlockType": "Unknown"}]}) == []

    source = parser._convert_block({"BlockType": "Constant", "Name": "source"}, 0)
    sink = parser._convert_block({"BlockType": "Scope", "Name": "sink"}, 1)
    assert source is not None and sink is not None
    block_map = {"source": source, "sink": sink}
    assert (
        parser._convert_connection(
            {"SrcBlock": "source", "SrcPort": 2, "DstBlock": "sink", "DstPort": 1}, block_map
        )
        is None
    )
    assert (
        parser._convert_connection(
            {"SrcBlock": "source", "SrcPort": 1, "DstBlock": "sink", "DstPort": 2}, block_map
        )
        is None
    )

    config = parser._parse_simulation_config({"FixedStep": "auto", "MaxStep": "bad"})
    assert config.step_size == 0.01


def test_model_validation_allows_terminal_and_source_exception_ports():
    source = Block(
        id="source",
        type="constant",
        name="source",
        position=Position(x=0, y=0),
        parameters={},
        inputPorts=[Port(id="in", name="in")],
        outputPorts=[],
    )
    sink = Block(
        id="sink",
        type="scope",
        name="sink",
        position=Position(x=0, y=0),
        parameters={},
        inputPorts=[],
        outputPorts=[Port(id="out", name="out")],
    )
    model = Model(
        id="model",
        metadata=ModelMetadata(name="model"),
        blocks=[source, sink],
        connections=[],
        simulationConfig=SimulationConfig(),
    )
    assert ModelService().validate_model(model) == {"valid": True, "errors": [], "warnings": []}
