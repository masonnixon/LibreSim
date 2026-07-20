"""Regression coverage for runner state and result contracts."""

from unittest.mock import Mock

from src.models.block import Block
from src.models.model import Model, ModelMetadata
from src.models.simulation import SimulationConfig, SimulationStatus
from src.simulation.compiler import CompiledModel
from src.simulation.runner import SimulationRunner


def constant_model() -> Model:
    return Model(
        id="constant-model",
        metadata=ModelMetadata(name="Constant"),
        blocks=[
            Block(
                id="constant",
                type="constant",
                name="Constant",
                position={"x": 0, "y": 0},
                parameters={"value": 1.0},
                inputPorts=[],
                outputPorts=[{"id": "constant-out-0", "name": "out"}],
            )
        ],
        connections=[],
    )


def test_failed_step_compilation_remains_failed_when_retried() -> None:
    runner = SimulationRunner(constant_model(), SimulationConfig())
    failure = CompiledModel(
        success=False,
        message="invalid graph",
        errors=["missing input", "invalid edge"],
    )
    runner._compiler.compile = Mock(return_value=failure)
    runner._adapter.initialize = Mock()

    assert runner.initialize_step_mode() is False
    assert runner.initialize_step_mode() is False
    assert runner.status == SimulationStatus.ERROR
    assert runner.error_message == "missing input; invalid edge"
    runner._compiler.compile.assert_called_once_with(runner.model)
    runner._adapter.initialize.assert_not_called()


def test_zero_duration_snapshot_round_trip_is_valid() -> None:
    config = SimulationConfig(startTime=2.0, stopTime=2.0, stepSize=0.1)
    runner = SimulationRunner(constant_model(), config)
    assert runner.initialize_step_mode() is True
    snapshot = runner.capture_snapshot()

    runner.restore_snapshot(snapshot)

    assert runner.current_time == 2.0
    assert runner.progress == 0.0
    assert runner.status == SimulationStatus.PAUSED


def test_result_grouping_preserves_colons_in_signal_names() -> None:
    runner = SimulationRunner(constant_model(), SimulationConfig())
    runner._results = {"scope:0:Plant:velocity": [(0.0, 4.0), (0.1, 5.0)]}
    runner._result_decimation = {"scope:0:Plant:velocity": 1}
    runner._adapter.get_scope_data = Mock(return_value=[])
    runner._adapter.get_analysis_data = Mock(return_value={})

    results = runner.get_results()

    assert results["signals"] == [
        {
            "blockId": "scope",
            "portId": "out",
            "name": "Plant:velocity",
            "times": [0.0, 0.1],
            "values": [4.0, 5.0],
        }
    ]
