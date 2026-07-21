"""Focused edge coverage for code-generation orchestration and language backends."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from src.codegen.generator import CodeGenerationConfig, CodeGenerationError, CodeGenerator
from src.codegen.languages.c.blocks.continuous import template_state_space as c_state_space
from src.codegen.languages.c.generator import CCodeGenerator
from src.codegen.languages.cpp.generator import CppCodeGenerator
from src.codegen.languages.python.blocks.aerospace import ecef_to_ned_template
from src.codegen.languages.python.generator import PythonCodeGenerator
from src.codegen.languages.rust.blocks.control_design import (
    _format_f64 as format_control_f64,
)
from src.codegen.languages.rust.blocks.control_design import (
    lqr_controller_template,
    pole_placement_template,
)
from src.codegen.languages.rust.blocks.estimation import _format_f64 as format_estimation_f64
from src.codegen.languages.rust.generator import RustCodeGenerator
from src.codegen.models import BlockInfo, CompiledModelInfo, GeneratedProject, Language


def _block(block_id: str, block_type: str = "unsupported", **changes) -> BlockInfo:
    values = {
        "id": block_id,
        "type": block_type,
        "name": block_id,
        "parameters": {},
        "input_connections": [],
        "output_connections": [],
        "execution_order": 0,
    }
    values.update(changes)
    return BlockInfo(**values)


def _info(blocks=(), **changes) -> CompiledModelInfo:
    values = {
        "blocks": list(blocks),
        "execution_order": [block.id for block in blocks],
        "integrator_blocks": [],
        "source_blocks": [],
        "sink_blocks": [],
        "step_size": 0.01,
        "stop_time": 1.0,
    }
    values.update(changes)
    return CompiledModelInfo(**values)


def _edge_model_info() -> CompiledModelInfo:
    vector = _block("vector", "mux", output_dimensions=[[3]])
    scalar = _block("scalar", "constant", parameters={"value": 1.0})
    vector_target = _block(
        "vector_target", "demux", input_connections=["vector:0@0"], input_dimensions=[]
    )
    multi = _block("multi", "sum", input_connections=["scalar:0@2"])
    high_port = _block("high", input_connections=["scalar:0@2"])
    ordinary = _block("ordinary", input_connections=["scalar:0@0", "missing:0@0"])
    ready = _block("ready", ready_only=True)
    rate = _block("rate", "rate_limiter")
    integrator = _block("integrator", "integrator")
    custom = _block("custom", "transfer_function", custom_state_propagation=True)
    blocks = [
        vector,
        scalar,
        vector_target,
        multi,
        high_port,
        ordinary,
        ready,
        rate,
        integrator,
        custom,
    ]
    return _info(
        blocks,
        execution_order=["missing", *(block.id for block in blocks)],
        integrator_blocks=["missing", "integrator"],
        sink_blocks=["missing", "ordinary"],
    )


@pytest.mark.parametrize(
    "generator",
    [CCodeGenerator(), CppCodeGenerator(), PythonCodeGenerator(), RustCodeGenerator()],
)
def test_language_generator_edge_model_paths(generator):
    info = _edge_model_info()
    config = CodeGenerationConfig(
        language=Language.PYTHON,
        project_name="1-edge-project",
        include_main=False,
        include_csv_output=False,
    )
    project = generator.generate(info, config)
    assert project.files
    if hasattr(generator, "_generate_integrator_propagation"):
        assert "No integrators" not in generator._generate_integrator_propagation(info)

    empty = _info()
    main = generator.generate_main_code(empty, replace(config, include_csv_output=True))
    assert "time" in main
    assert generator.generate_integration_code(config.integration_method)


@pytest.mark.parametrize("generator", [CCodeGenerator(), CppCodeGenerator(), RustCodeGenerator()])
def test_compiled_generator_passthrough_and_vector_defaults(generator):
    unsupported = _block("unknown", input_connections=["source:0@2"])
    code = generator.generate_block_code(unsupported)
    assert "input2" in code

    mux = _block("mux", "mux")
    demux = _block("demux", "demux")
    assert generator._is_vector_output(mux)
    assert generator._expects_vector_input(demux)

    vector = _block("vector", "mux", output_dimensions=[[]])
    target = _block("target", "demux", input_connections=["vector:0@0"])
    wiring = generator._generate_connection_code(_info([vector, target]))
    assert "vector" in wiring
    dimensionless = _block("dimensionless", "mux")
    dimensionless_target = _block(
        "dimensionless_target", "demux", input_connections=["dimensionless:0@0"]
    )
    dimensionless_info = _info([dimensionless, dimensionless_target])
    assert "dimensionless" in generator._generate_connection_code(dimensionless_info)
    assert generator._generate_per_block_wiring(dimensionless_info)
    assert generator._generate_per_block_wiring(_info([vector, target]))

    neutral = _block("neutral")
    assert "No integrators" in generator._generate_integrator_propagation(
        _info([neutral], integrator_blocks=[neutral.id])
    )
    assert "input2" not in generator.generate_block_code(_block("single"))
    assert "input2" not in generator.generate_block_code(
        _block("portless", input_connections=["source:0"])
    )

    config = CodeGenerationConfig(include_csv_output=False)
    assert "Results written" not in generator.generate_main_code(_info(), config)
    if isinstance(generator, (CCodeGenerator, CppCodeGenerator)):
        assert "return 0.0" in generator._generate_simulation_source(_info(), config)
    else:
        assert "0.0" in generator._generate_lib(_info(), config)


def test_python_generator_syntax_and_passthrough_edges():
    generator = PythonCodeGenerator()
    project = GeneratedProject("bad", Language.PYTHON)
    project.add_file("bad.py", "def broken(:\n")
    with pytest.raises(SyntaxError, match="Syntax error in generated bad.py"):
        generator._validate_python_code(project)

    scalar = _block("scalar")
    vector_input = _block("vin", input_dimensions=[[3]])
    vector_output = _block("vout", output_dimensions=[[2]])
    assert "Passthrough block:" in generator.generate_block_code(scalar)
    assert "* 3" in generator._generate_passthrough_block(vector_input)
    assert "* 2" in generator._generate_passthrough_block(vector_output)
    assert "Block_constant" in generator.generate_block_code(_block("constant", "constant"))
    assert generator._is_vector_output(_block("mux", "mux"))
    assert generator._expects_vector_input(_block("demux", "demux"))


def test_language_base_connection_default_port():
    generator = CCodeGenerator()
    assert generator.parse_connection("source:out@input") == ("source", 0, 0)


def test_orchestrator_rejects_unsupported_generator(monkeypatch):
    generator = CodeGenerator()
    monkeypatch.setattr(generator, "compile_model_info", lambda model, config: _info())
    config = CodeGenerationConfig()
    config.language = "unsupported"  # type: ignore[assignment]
    with pytest.raises(CodeGenerationError, match="Unsupported language"):
        generator.generate({}, config)


def test_compile_model_info_accepts_model_object_and_analysis_failure(monkeypatch):
    generator = CodeGenerator()

    class ModelLike:
        def get(self, key, default=None):
            return default

    model = ModelLike()
    compiled = SimpleNamespace(success=True, execution_order=[], blocks=[])
    monkeypatch.setattr(generator._compiler, "compile", lambda candidate: compiled)
    assert generator.compile_model_info(model, CodeGenerationConfig()).blocks == []

    analysis = _block("analysis", "bode_plot")
    monkeypatch.setattr(
        "src.codegen.generator.compute_analysis_output",
        lambda block, blocks: (_ for _ in ()).throw(ValueError("bad analysis")),
    )
    with pytest.raises(CodeGenerationError, match="Failed to precompute analysis"):
        generator._extract_model_info(
            SimpleNamespace(execution_order=["missing", "analysis"], blocks=[analysis]),
            {"blocks": [{"id": "analysis"}]},
            CodeGenerationConfig(),
        )


def test_output_schema_rejects_malformed_missing_and_unsupported_shapes():
    generator = CodeGenerator()
    source = _block("source", output_dimensions=[[1]])

    def extract(sink):
        return generator._extract_output_signals([source, sink], ["missing", sink.id])

    analysis = _block("analysis", "bode_plot", output_dimensions=[[2]])
    with pytest.raises(CodeGenerationError, match="one scalar output"):
        generator._extract_output_signals([analysis], [analysis.id])

    for connection, message in [
        ("malformed", "Malformed"),
        ("source:x@y", "Non-numeric"),
        ("missing:0@0", "missing source"),
    ]:
        sink = _block("sink", "scope", input_connections=[connection])
        with pytest.raises(CodeGenerationError, match=message):
            extract(sink)

    bad_shape = _block("bad", output_dimensions=[[1, 1]])
    sink = _block("sink", "scope", input_connections=["bad:0@0"])
    with pytest.raises(CodeGenerationError, match="Unsupported output shape"):
        generator._extract_output_signals([bad_shape, sink], [sink.id])

    multi = _block("multi", output_dimensions=[[3], [1]])
    sink = _block("sink", "scope", input_connections=["multi:0@0"])
    with pytest.raises(CodeGenerationError, match="vector-valued multi-output"):
        generator._extract_output_signals([multi, sink], [sink.id])

    sink = _block("sink", "scope", input_connections=["source:0@0", "source:0@0"])
    with pytest.raises(CodeGenerationError, match="Duplicate canonical output key"):
        extract(sink)


def test_output_schema_dimension_fallback_and_port_id_fallbacks():
    generator = CodeGenerator()
    source = _block("source")
    sink = _block("sink", "scope", input_connections=["source:4@1"], input_dimensions=[[1], [2]])
    outputs = generator._extract_output_signals([source, sink], [sink.id])
    assert len(outputs) == 2
    scalar_sink = _block("scalar_sink", "scope", input_connections=["source:9@9"])
    assert generator._extract_output_signals([source, scalar_sink], [scalar_sink.id])[
        0
    ].dimensions == (1,)

    block_map = {
        "source": {"outputPorts": [{"id": "out"}]},
        "target": {"inputPorts": [{"id": "in"}]},
    }
    assert generator._resolve_port_ids_in_connection("plain", block_map["target"], block_map) == (
        "plain"
    )
    assert (
        generator._resolve_port_ids_in_connection("source:out3@in2", block_map["target"], block_map)
        == "source:2@1"
    )
    assert (
        generator._resolve_port_ids_in_connection("source:out0@in0", block_map["target"], block_map)
        == "source:0@0"
    )
    assert (
        generator._resolve_port_ids_in_connection("source:out@in", block_map["target"], block_map)
        == "source:0@0"
    )
    unmatched_map = {
        "source": {"outputPorts": [{"id": "different"}]},
        "target": {"inputPorts": [{"id": "different"}]},
    }
    assert (
        generator._resolve_port_ids_in_connection(
            "source:out@in", unmatched_map["target"], unmatched_map
        )
        == "source:0@0"
    )
    assert generator.get_supported_blocks()


def test_remaining_block_template_helper_edges():
    sparse = _block(
        "state",
        parameters={"A": [[1.0], []], "B": [[]], "C": [[], [1.0]], "D": [[]]},
    )
    assert "double A" in c_state_space(sparse, "SparseState")
    assert "1.0" in ecef_to_ned_template(
        _block("ecef", parameters={"referenceLla": [1.0, 2.0, 3.0]}), "ECEF"
    )

    assert format_control_f64("gain") == "gain"
    assert format_estimation_f64("gain") == "gain"
    assert format_estimation_f64(1e20) == "1e+20"
    assert ".0_f64" in lqr_controller_template(
        _block("lqr", parameters={"K": [[1]], "num_inputs": 1, "num_states": 1}), "LQR"
    )
    assert ".0_f64" in pole_placement_template(
        _block("pole", parameters={"K": [1], "num_states": 1}), "Pole"
    )
