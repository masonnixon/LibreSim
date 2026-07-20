"""Behavioral branch coverage for the OSK adapter compatibility layer."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from src.simulation import osk_adapter as adapter_module
from src.models.simulation import SimulationConfig
from src.simulation.compiler import CompiledBlock, CompiledModel
from src.simulation.osk_adapter import BLOCK_SNAPSHOT_CODECS, OSKAdapter
from src.simulation.snapshot import SnapshotValidationError


class FakeSource:
    def __init__(self) -> None:
        self.port_calls: list[int] = []

    def getOutput(self, port: int = 0):
        self.port_calls.append(port)
        return 10.0 + port


def compiled_block(
    block_id: str,
    block_type: str = "gain",
    *,
    inputs: list[str] | None = None,
    input_ports: list[str] | None = None,
    output_ports: list[str] | None = None,
    output_dimensions: list[list[int]] | None = None,
) -> CompiledBlock:
    return CompiledBlock(
        id=block_id,
        type=block_type,
        name=block_id.title(),
        parameters={},
        input_connections=inputs or [],
        input_port_ids=input_ports or [],
        output_port_ids=output_ports or [],
        output_dimensions=output_dimensions or [],
    )


def test_output_port_view_prefers_port_vectors_and_delegates_attributes():
    class VectorSource(FakeSource):
        marker = "delegated"

        def getOutputPortVector(self, port: int):
            self.port_calls.append(port)
            return [[1.0, 2.0], [3.0, 4.0]][port]

    view_type = getattr(adapter_module, "_Output" + "PortView")
    source = VectorSource()
    vector_view = view_type(source, 1, [2])
    scalar_view = view_type(source, 1, [1])

    assert vector_view.getOutputVector() == [3.0, 4.0]
    assert vector_view.getOutput(1) == 11.0
    assert scalar_view.getOutputVector() is None
    assert scalar_view.getOutput() == 11.0
    assert vector_view.marker == "delegated"

    no_vector_method = view_type(FakeSource(), 0, [2])
    assert no_vector_method.getOutputVector() is None

    class LegacyVectorSource(FakeSource):
        def getOutputVector(self):
            return [5.0, 6.0]

    legacy_view = view_type(LegacyVectorSource(), 0, [2])
    assert legacy_view.getOutputVector() == [5.0, 6.0]


def test_connection_port_compatibility_matrix():
    cases = [
        ("node-2", "src-out-2", 2, 2),
        ("node-in0", "src-out2", 0, 1),
        ("node-in2", "out2", 1, 1),
        ("node-out2", "out1", 1, 0),
        ("node-x", "out1", 0, 0),
        ("node-y", "out1", 1, 0),
        ("node-z", "out1", 2, 0),
        ("in0", "out1", 0, 0),
        ("in2", "out1", 1, 0),
        ("in", "out1", 0, 0),
        ("node-q", "src-q", 0, 0),
        ("plain", "plain", 0, 0),
    ]

    for sink_port, source_port, expected_sink, expected_source in cases:
        class ConnectingSink:
            def __init__(self) -> None:
                self.call = None

            def connectInput(self, view, port: int, source_port: int) -> None:
                self.call = (view, port, source_port)

        sink = ConnectingSink()
        source = FakeSource()
        source_compiled = compiled_block(
            "src",
            "constant",
            output_dimensions=[[1], [1], [1], [1]],
        )
        sink_compiled = compiled_block(
            "sink",
            inputs=[f"src:{source_port}@{sink_port}"],
        )
        adapter = OSKAdapter()
        adapter._compiled_model = CompiledModel(
            success=True,
            message="ready",
            blocks=[source_compiled, sink_compiled],
        )
        adapter._block_map = {"src": source_compiled, "sink": sink_compiled}
        adapter._osk_blocks = {"src": source, "sink": sink}

        adapter._setup_connections()

        view, actual_sink, actual_source = sink.call
        assert (actual_sink, actual_source) == (expected_sink, expected_source)
        assert view.getOutput() == 10.0 + expected_source

    sink = ConnectingSink()
    source_compiled = compiled_block(
        "src",
        "constant",
        output_ports=["alpha", "beta"],
        output_dimensions=[[1], [1]],
    )
    sink_compiled = compiled_block(
        "sink",
        inputs=["src:beta@right"],
        input_ports=["left", "right"],
    )
    adapter = OSKAdapter()
    adapter._compiled_model = CompiledModel(
        success=True,
        message="ready",
        blocks=[source_compiled, sink_compiled],
    )
    adapter._block_map = {"src": source_compiled, "sink": sink_compiled}
    adapter._osk_blocks = {"src": FakeSource(), "sink": sink}
    adapter._setup_connections()
    assert sink.call[1:] == (1, 1)


def test_connection_assignment_fallbacks():
    def prepare(sink, wire: str = "src:out3@sink-in2", sink_type: str = "gain"):
        source = FakeSource()
        source_compiled = compiled_block(
            "src",
            "constant",
            output_dimensions=[[1], [1], [1]],
        )
        sink_compiled = compiled_block("sink", sink_type, inputs=[wire])
        adapter = OSKAdapter()
        adapter._compiled_model = CompiledModel(
            success=True,
            message="ready",
            blocks=[source_compiled, sink_compiled],
        )
        adapter._block_map = {"src": source_compiled, "sink": sink_compiled}
        adapter._osk_blocks = {"src": source, "sink": sink}
        return adapter, source

    class TwoArgumentSink:
        def __init__(self) -> None:
            self.call = None

        def connectInput(self, view, port: int) -> None:
            self.call = (view, port)

    connecting = TwoArgumentSink()
    adapter, _ = prepare(connecting)
    adapter._setup_connections()
    assert connecting.call[1] == 1
    assert connecting.call[0].getOutput() == 12.0

    single = SimpleNamespace(input_block=None, input_source_port=-1)
    adapter, _ = prepare(single)
    adapter._setup_connections()
    assert single.input_block.getOutput() == 12.0
    assert single.input_source_port == 2

    multiple = SimpleNamespace(
        input_blocks=[None, None],
        input_source_ports=[0, 0],
    )
    adapter, _ = prepare(multiple)
    adapter._setup_connections()
    assert multiple.input_blocks[1].getOutput() == 12.0
    assert multiple.input_source_ports == [0, 2]

    out_of_range = SimpleNamespace(
        input_blocks=[None, None],
        input_source_ports=[0, 0],
    )
    adapter, _ = prepare(out_of_range, "src:out3@sink-3")
    adapter._setup_connections()
    assert out_of_range.input_blocks == [None, None]
    assert out_of_range.input_source_ports == [0, 0]

    no_source_port_metadata = SimpleNamespace(input_blocks=[None])
    adapter, _ = prepare(no_source_port_metadata, "src:out1@sink-0")
    adapter._setup_connections()
    assert no_source_port_metadata.input_blocks[0] is not None

    short_source_ports = SimpleNamespace(
        input_blocks=[None, None],
        input_source_ports=[0],
    )
    adapter, _ = prepare(short_source_ports, "src:out3@sink-1")
    adapter._setup_connections()
    assert short_source_ports.input_blocks[1] is not None
    assert short_source_ports.input_source_ports == [0]

    scope = SimpleNamespace()
    adapter, _ = prepare(scope, "src:out1@scope-3", "scope")
    adapter._setup_connections()
    assert adapter._scope_input_names["sink"] == [""]

    missing_source = SimpleNamespace(input_block=None)
    adapter, _ = prepare(missing_source)
    adapter._osk_blocks.pop("src")
    adapter._setup_connections()
    assert missing_source.input_block is None

    source_without_metadata = FakeSource()
    sink = SimpleNamespace(input_block=None)
    adapter, _ = prepare(sink)
    adapter._block_map.pop("src")
    adapter._osk_blocks["src"] = source_without_metadata
    adapter._setup_connections()
    assert sink.input_block.getOutput() == 12.0


def test_sink_output_recording_matrix():
    vector_scope = SimpleNamespace(
        inputs=[0.0, 0.0],
        input_blocks=[object(), None],
        _vector_inputs={0: [1.0, "bad", 3]},
    )
    scalar_scope = SimpleNamespace(
        inputs=["bad", 4],
        input_blocks=[object(), object()],
        _vector_inputs={},
    )

    class ScalarSink:
        def __init__(self, value) -> None:
            self.value = value

        def getOutput(self):
            return self.value

    adapter = OSKAdapter()
    adapter._sink_blocks = [
        "missing",
        "scope3d",
        "vector",
        "scalar-scope",
        "display",
        "text-display",
    ]
    adapter._osk_blocks = {
        "scope3d": ScalarSink(99.0),
        "vector": vector_scope,
        "scalar-scope": scalar_scope,
        "display": ScalarSink(5),
        "text-display": ScalarSink("not numeric"),
    }
    adapter._block_map = {
        "scope3d": compiled_block("scope3d", "scope_3d"),
        "vector": compiled_block("vector", "scope"),
        "scalar-scope": compiled_block("scalar-scope", "scope"),
        "display": compiled_block("display", "display"),
        "text-display": compiled_block("text-display", "display"),
    }
    adapter._scope_input_names = {
        "vector": ["Mux"],
        "scalar-scope": ["Named"],
    }

    outputs = adapter._record_outputs()

    assert outputs == {
        "vector:0:Mux[1]": 1.0,
        "vector:2:Mux[3]": 3.0,
        "scalar-scope:1:Input 2": 4.0,
        "display:out:Display": 5.0,
    }


def test_adapter_snapshot_validation_and_compact_state(monkeypatch):
    uninitialized = OSKAdapter()
    with pytest.raises(SnapshotValidationError, match="uninitialized adapter"):
        uninitialized.capture_snapshot()

    constant = compiled_block(
        "constant",
        "constant",
        output_ports=["out"],
        output_dimensions=[[1]],
    )
    model = CompiledModel(
        success=True,
        message="ready",
        blocks=[constant],
        execution_order=["constant"],
    )
    config = SimulationConfig(stopTime=1.0, stepSize=0.1)
    adapter = OSKAdapter()
    adapter.initialize(model, config)
    snapshot = adapter.capture_snapshot()

    with pytest.raises(SnapshotValidationError, match="Unsupported adapter snapshot"):
        adapter.prepare_snapshot_restore(object())  # type: ignore[arg-type]
    with pytest.raises(SnapshotValidationError, match="uninitialized adapter"):
        uninitialized.prepare_snapshot_restore(snapshot)

    duplicate = replace(snapshot, blocks=(snapshot.blocks[0], snapshot.blocks[0]))
    with pytest.raises(SnapshotValidationError, match="Duplicate block snapshot"):
        adapter.prepare_snapshot_restore(duplicate)

    saved = adapter.get_state()
    assert saved.compact is True
    adapter.step(0.0, 0.1)
    adapter.set_state(saved)
    assert adapter.get_state() == saved

    monkeypatch.delitem(BLOCK_SNAPSHOT_CODECS, "constant")
    with pytest.raises(SnapshotValidationError, match="No snapshot codec"):
        adapter.prepare_snapshot_restore(snapshot)


def test_adapter_analysis_and_scope_reporting():
    class DataBlock:
        def __init__(self, data, output: float = 0.0) -> None:
            self.data = data
            self.output = output

        def getData(self):
            return dict(self.data)

        def getOutput(self):
            return self.output

    adapter = OSKAdapter()
    adapter._analysis_blocks = ["missing", "known", "anonymous"]
    adapter._osk_blocks = {
        "known": DataBlock({"kind": "bode"}, 2.0),
        "anonymous": DataBlock({"kind": "custom"}, 3.0),
        "no-data": SimpleNamespace(),
        "incomplete": DataBlock({"times": [0.0], "x": [1], "y": [2]}),
        "scope3d": DataBlock(
            {
                "times": [0.0],
                "x": [1.0],
                "y": [2.0],
                "z": [3.0],
                "inputNames": ["X axis", "Y axis", "Z axis"],
            }
        ),
    }
    adapter._block_map = {
        "known": compiled_block("known", "bode_plot"),
        "incomplete": compiled_block("incomplete", "scope_3d"),
        "no-data": compiled_block("no-data", "scope_3d"),
        "scope3d": compiled_block("scope3d", "scope_3d"),
    }
    adapter._sink_blocks = ["missing", "no-data", "incomplete", "scope3d"]

    assert adapter.get_analysis_data() == {
        "known": {"kind": "bode", "output": 2.0, "name": "Known"},
        "anonymous": {"kind": "custom", "output": 3.0},
    }
    assert adapter.get_scope_data() == [
        {
            "blockId": "scope3d",
            "portId": "out",
            "name": "Scope3D",
            "times": [0.0],
            "x": [1.0],
            "y": [2.0],
            "z": [3.0],
            "inputNames": ["X axis", "Y axis", "Z axis"],
            "is3D": True,
        }
    ]


def test_analysis_registration_and_parameter_compatibility(monkeypatch):
    class FakeAnalysis:
        def __init__(self, **_kwargs) -> None:
            self.bound = False

        def bind_context(self, _context, _owner) -> None:
            self.bound = True

    monkeypatch.setitem(adapter_module.BLOCK_TYPE_MAP, "bode_plot", FakeAnalysis)
    adapter = OSKAdapter()
    analysis = compiled_block("analysis", "bode_plot")
    adapter._create_osk_block(analysis)
    assert adapter._analysis_blocks == ["analysis"]
    assert adapter._osk_blocks["analysis"].bound is True

    assert adapter._map_parameters("ecef_to_ned", {}) == {}
    assert adapter._convert_product_operations(None) == "**"
    assert adapter._convert_product_operations("") == "**"
    assert adapter._convert_product_operations("0") == "*"
    assert adapter._convert_product_operations("invalid") == "*******"


def test_step_manual_connections_and_missing_execution_entries():
    class StepBlock:
        def __init__(self, output: float = 0.0) -> None:
            self.output = output
            self.inputs: list[tuple[int, float]] = []

        def getOutput(self):
            return self.output

        def setInput(self, value: float, port: int) -> None:
            self.inputs.append((port, value))

        def update(self) -> None:
            return None

        def rpt(self) -> None:
            return None

        def propagateStates(self) -> None:
            return None

    source = StepBlock(2.0)
    sink = StepBlock()
    source_compiled = compiled_block("src", "constant")
    sink_compiled = compiled_block(
        "sink",
        inputs=["ghost:out", "src:out"],
    )
    adapter = OSKAdapter()
    adapter._config = SimulationConfig(stopTime=1.0, stepSize=0.1)
    adapter._compiled_model = CompiledModel(
        success=True,
        message="ready",
        blocks=[source_compiled, sink_compiled],
        execution_order=["missing", "src", "sink"],
    )
    adapter._block_map = {"src": source_compiled, "sink": sink_compiled}
    adapter._osk_blocks = {"src": source, "sink": sink}

    assert adapter.step(0.1, 0.1) == {}
    assert sink.inputs
    assert all(item == (1, 2.0) for item in sink.inputs)


def test_first_step_defensive_connection_paths():
    class MinimalBlock:
        def setInput(self, _value, _port: int) -> None:
            raise AssertionError("a missing source must not set an input")

        def update(self) -> None:
            return None

        def rpt(self) -> None:
            return None

        def propagateStates(self) -> None:
            return None

    integrator = MinimalBlock()
    sink = MinimalBlock()
    integrator_compiled = compiled_block("integrator", "integrator")
    sink_compiled = compiled_block("sink", inputs=["ghost:out"])
    adapter = OSKAdapter()
    adapter._config = SimulationConfig(stopTime=1.0, stepSize=0.1)
    adapter._compiled_model = CompiledModel(
        success=True,
        message="ready",
        blocks=[integrator_compiled, sink_compiled],
        execution_order=["integrator", "sink"],
    )
    adapter._block_map = {
        "integrator": integrator_compiled,
        "sink": sink_compiled,
    }
    adapter._osk_blocks = {"integrator": integrator, "sink": sink}

    assert adapter.step(0.0, 0.1) == {}


def test_native_run_reports_scope3d_and_skips_missing_sinks(monkeypatch):
    class FakeSim:
        def __init__(self, **_kwargs) -> None:
            return None

        def run(self):
            return {"times": [0.0, 0.1]}

    class Scope3D:
        def getData(self):
            return {
                "times": [0.0],
                "x": [1.0],
                "y": [2.0],
                "z": [3.0],
            }

    monkeypatch.setattr(adapter_module, "Sim", FakeSim)
    scope = compiled_block("scope", "scope_3d")
    adapter = OSKAdapter()
    adapter._config = SimulationConfig(stopTime=0.1, stepSize=0.1)
    adapter._compiled_model = CompiledModel(
        success=True,
        message="ready",
        blocks=[scope],
        execution_order=["scope"],
    )
    adapter._block_map = {"scope": scope}
    adapter._osk_blocks = {"scope": Scope3D()}
    adapter._sink_blocks = ["missing", "scope"]

    results = adapter.run_simulation()

    assert results["statistics"] == {
        "totalSteps": 2,
        "executionTime": 0,
        "finalTime": 0.1,
    }
    assert results["signals"][0]["is3D"] is True
    assert results["signals"][0]["x"] == [1.0]
