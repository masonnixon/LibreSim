"""Tests for the shared canonical generated-output schema."""

from copy import deepcopy

import pytest

from src.codegen.generator import CodeGenerationConfig, CodeGenerationError, CodeGenerator
from src.codegen.models import Language
from src.codegen.validation import canonicalize_headless_results


def _model(*, dimensions: list[int] | None = None) -> dict:
    dimensions = dimensions or [1]
    value: float | list[float] = 1.0
    if dimensions[0] > 1:
        value = [float(index + 1) for index in range(dimensions[0])]
    return {
        "id": "output-schema",
        "metadata": {"name": "Output schema", "description": ""},
        "blocks": [
            {
                "id": "source/a",
                "type": "constant",
                "name": "Duplicate name",
                "position": {"x": 0, "y": 0},
                "parameters": {"value": value},
                "inputPorts": [],
                "outputPorts": [
                    {"id": "source/a-out", "name": "out", "dimensions": dimensions}
                ],
            },
            {
                "id": "source-b",
                "type": "constant",
                "name": "Duplicate name",
                "position": {"x": 0, "y": 100},
                "parameters": {"value": 2.0},
                "inputPorts": [],
                "outputPorts": [
                    {"id": "source-b-out", "name": "out", "dimensions": [1]}
                ],
            },
            {
                "id": "sink|scope",
                "type": "scope",
                "name": "Mutable display name",
                "position": {"x": 200, "y": 0},
                "parameters": {"numInputs": 3},
                "inputPorts": [
                    {"id": "sink-in-0", "name": "in0", "dimensions": dimensions},
                    {"id": "sink-in-1", "name": "in1", "dimensions": [1]},
                    {"id": "sink-in-2", "name": "unconnected", "dimensions": [1]},
                ],
                "outputPorts": [],
            },
        ],
        # Deliberately shuffled: schema order follows target input ports.
        "connections": [
            {
                "id": "second",
                "sourceBlockId": "source-b",
                "sourcePortId": "source-b-out",
                "targetBlockId": "sink|scope",
                "targetPortId": "sink-in-1",
            },
            {
                "id": "first",
                "sourceBlockId": "source/a",
                "sourcePortId": "source/a-out",
                "targetBlockId": "sink|scope",
                "targetPortId": "sink-in-0",
            },
        ],
        "simulationConfig": {"startTime": 0.0, "stopTime": 1.0, "stepSize": 0.1},
    }


def test_output_schema_is_stable_ordered_and_display_name_independent():
    generator = CodeGenerator()
    config = CodeGenerationConfig()
    model = _model()

    first = generator.compile_model_info(model, config).output_signals
    renamed = deepcopy(model)
    renamed["blocks"][0]["name"] = "A different name"
    renamed["blocks"][2]["name"] = "Another scope name"
    second = generator.compile_model_info(renamed, config).output_signals

    assert [signal.canonical_key for signal in first] == [
        "sink=sink%7Cscope|in=0|source=source%2Fa|out=0|element=scalar",
        "sink=sink%7Cscope|in=1|source=source-b|out=0|element=scalar",
    ]
    assert [signal.canonical_key for signal in second] == [
        signal.canonical_key for signal in first
    ]
    assert all(signal.sink_input_port != 2 for signal in first)


@pytest.mark.parametrize(
    ("language", "main_path", "access_prefix"),
    [
        (Language.PYTHON, "simulation.py", "model.block_source_a.get_output("),
        (Language.C, "src/main.c", "Block_source_a_get_output(&model.block_source_a, "),
        (Language.CPP, "src/main.cpp", "model.block_source_a.get_output("),
        (Language.RUST, "src/main.rs", "model.block_source_a.get_output("),
    ],
)
def test_vector_columns_are_shared_across_generators(language, main_path, access_prefix):
    project = CodeGenerator().generate(
        _model(dimensions=[3]),
        CodeGenerationConfig(language=language),
    )
    main_file = project.get_file(main_path)

    assert main_file is not None
    for index in range(3):
        key = f"sink=sink%7Cscope|in=0|source=source%2Fa|out=0|element={index}"
        assert key in main_file.content
        assert f"{access_prefix}{index}" in main_file.content


def test_headless_results_are_canonicalized_by_sink_and_trace_order():
    schema = CodeGenerator().compile_model_info(
        _model(dimensions=[3]), CodeGenerationConfig()
    ).output_signals
    results = {
        "signals": [
            {
                "blockId": "sink|scope",
                "times": [0.0, 1.0],
                "values": [
                    [1.0, 2.0],
                    [3.0, 4.0],
                    [5.0, 6.0],
                    [7.0, 8.0],
                ],
            }
        ]
    }

    parsed = canonicalize_headless_results(results, schema)

    assert parsed.final_values == {
        signal.canonical_key: value
        for signal, value in zip(schema, (2.0, 4.0, 6.0, 8.0), strict=True)
    }


def test_rank_two_outputs_fail_explicitly():
    with pytest.raises(CodeGenerationError, match="rank-1"):
        CodeGenerator().compile_model_info(_model(dimensions=[2, 2]), CodeGenerationConfig())
