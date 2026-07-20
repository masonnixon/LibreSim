"""Regression coverage for runner state and result contracts."""

import asyncio
from dataclasses import replace
from unittest.mock import AsyncMock, Mock

import pytest
from pydantic import ValidationError

from src.models.block import Block
from src.models.model import Model, ModelMetadata
from src.models.simulation import SimulationConfig, SimulationStatus
from src.simulation.compiler import CompiledModel
from src.simulation.runner import (
    SimulationOperationConflict,
    SimulationOperationToken,
    SimulationRunner,
)
from src.simulation.snapshot import (
    ResultSeriesSnapshot,
    SnapshotValidationError,
)


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


@pytest.mark.parametrize("step_size", [0.0, -0.1])
def test_simulation_config_rejects_nonpositive_step_sizes(step_size: float) -> None:
    with pytest.raises(ValidationError, match="greater than 0"):
        SimulationConfig(stepSize=step_size)


def test_stop_and_background_reservations_release_pause_waiters() -> None:
    runner = SimulationRunner(constant_model(), SimulationConfig())
    stop_waiter = asyncio.Event()
    runner._pause_waiter = stop_waiter
    runner.stop()

    assert stop_waiter.is_set()
    assert runner._pause_waiter is None
    assert runner._should_stop is True
    assert runner._resume_gate.is_set()

    scheduled_waiter = asyncio.Event()
    runner._pause_waiter = scheduled_waiter
    token = runner.mark_scheduled(reset_stop=True)

    assert scheduled_waiter.is_set()
    assert runner._pause_waiter is None
    assert runner._should_stop is False
    assert runner.has_live_run is True
    assert runner.release_unadopted_operation(token) is True


def test_continue_reservation_and_token_validation_contracts() -> None:
    runner = SimulationRunner(constant_model(), SimulationConfig())
    assert runner.can_continue_from_step_mode is False
    runner._step_mode = True
    runner._compiled = CompiledModel(success=True, message="ready")
    waiter = asyncio.Event()
    runner._pause_waiter = waiter

    token = runner.schedule_continue()

    assert waiter.is_set()
    assert runner._pause_waiter is None
    assert runner.can_continue_from_step_mode is True
    assert runner.has_live_run is True
    with pytest.raises(SimulationOperationConflict, match="Invalid or stale"):
        runner._claim_operation("continue", SimulationOperationToken("continue"))
    assert runner.release_unadopted_operation(token) is True


@pytest.mark.asyncio
async def test_stop_and_wait_reports_timeout_for_an_unfinished_background_run() -> None:
    runner = SimulationRunner(constant_model(), SimulationConfig())
    token = runner.mark_scheduled()

    assert await runner.stop_and_wait(timeout=0) is False
    assert runner.release_unadopted_operation(token) is True


@pytest.mark.asyncio
async def test_idle_pause_reuses_waiter_and_resume_without_waiter() -> None:
    runner = SimulationRunner(constant_model(), SimulationConfig())
    waiter = asyncio.Event()
    runner._pause_waiter = waiter

    await runner.pause()

    assert waiter.is_set()
    assert runner.status == SimulationStatus.PAUSED
    runner._pause_waiter = None
    runner.resume()
    assert runner.status == SimulationStatus.RUNNING
    assert runner._resume_gate.is_set()


def test_reset_handles_uncompiled_and_compiled_runners() -> None:
    runner = SimulationRunner(
        constant_model(),
        SimulationConfig(startTime=2.0, stopTime=3.0, stepSize=0.1),
    )
    runner._status = SimulationStatus.ERROR
    runner._current_time = 2.5
    runner._error_message = "old error"
    runner._adapter.initialize = Mock()

    runner.reset()

    assert runner.status == SimulationStatus.IDLE
    assert runner.current_time == 2.0
    assert runner.error_message is None
    runner._adapter.initialize.assert_not_called()

    runner._compiled = CompiledModel(success=True, message="compiled")
    runner.reset()
    runner._adapter.initialize.assert_called_once_with(runner._compiled, runner.config)


def test_step_backward_stops_at_the_initial_checkpoint() -> None:
    runner = SimulationRunner(
        constant_model(),
        SimulationConfig(stopTime=1.0, stepSize=0.1),
    )
    assert runner.initialize_step_mode() is True
    assert runner.step_forward(2)["stepsExecuted"] == 2

    result = runner.step_backward(10)

    assert result["success"] is True
    assert result["stepsExecuted"] == 2
    assert result["historySize"] == 1
    assert result["currentTime"] == 0.0


@pytest.mark.asyncio
async def test_run_preserves_compiler_message_when_no_detailed_errors_exist() -> None:
    runner = SimulationRunner(constant_model(), SimulationConfig())
    runner._compiler.compile = Mock(
        return_value=CompiledModel(success=False, message="compiler rejected graph")
    )

    await runner.run()

    assert runner.status == SimulationStatus.ERROR
    assert runner.error_message == "compiler rejected graph"
    assert runner._active_operation is None


@pytest.mark.asyncio
async def test_continue_records_adapter_errors_and_releases_ownership() -> None:
    runner = SimulationRunner(
        constant_model(),
        SimulationConfig(stopTime=1.0, stepSize=0.1),
    )
    assert runner.initialize_step_mode() is True
    runner._adapter.step = Mock(side_effect=RuntimeError("step sentinel"))
    token = runner.schedule_continue()

    await runner.continue_from_step_mode(token)

    assert runner.status == SimulationStatus.ERROR
    assert runner.error_message == "step sentinel"
    assert token.finished.is_set()
    assert runner._active_operation is None


@pytest.mark.asyncio
async def test_continue_honors_a_transition_requested_at_pause_boundary() -> None:
    runner = SimulationRunner(
        constant_model(),
        SimulationConfig(stopTime=1.0, stepSize=0.1),
    )
    assert runner.initialize_step_mode() is True

    async def request_transition() -> None:
        runner._transition_requested = True

    runner._wait_while_paused = AsyncMock(side_effect=request_transition)
    runner._adapter.step = Mock()
    token = runner.schedule_continue()

    await runner.continue_from_step_mode(token)

    runner._adapter.step.assert_not_called()
    assert runner.status == SimulationStatus.PAUSED
    assert token.finished.is_set()


def initialized_runner() -> SimulationRunner:
    runner = SimulationRunner(
        constant_model(),
        SimulationConfig(stopTime=1.0, stepSize=0.1),
    )
    assert runner.initialize_step_mode() is True
    return runner


def test_snapshot_capture_rejects_runner_adapter_time_mismatch() -> None:
    runner = initialized_runner()
    runner._current_time += runner.config.step_size

    with pytest.raises(SnapshotValidationError, match="times are inconsistent"):
        runner.capture_snapshot()


def test_public_snapshot_restore_rejects_invalid_snapshot_kinds() -> None:
    runner = initialized_runner()

    with pytest.raises(SnapshotValidationError, match="detached snapshot"):
        runner.restore_snapshot(runner._state_history[-1])
    with pytest.raises(SnapshotValidationError, match="Unsupported runner snapshot"):
        runner.restore_snapshot(object())  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda snapshot: replace(
                snapshot,
                adapter=replace(snapshot.adapter, compact=True),
            ),
            "snapshot modes disagree",
        ),
        (
            lambda snapshot: replace(snapshot, next_result_generation=-1),
            "Invalid next result generation",
        ),
    ],
)
def test_snapshot_restore_rejects_invalid_runner_metadata(mutation, message: str) -> None:
    runner = initialized_runner()
    snapshot = mutation(runner.capture_snapshot())

    with pytest.raises(SnapshotValidationError, match=message):
        runner.restore_snapshot(snapshot)


def _result_ref(**changes) -> ResultSeriesSnapshot:
    return replace(
        ResultSeriesSnapshot(
            key="signal",
            generation=0,
            length=0,
            decimation=1,
        ),
        **changes,
    )


@pytest.mark.parametrize(
    ("results", "next_generation", "message"),
    [
        ((_result_ref(), _result_ref()), 1, "Duplicate result key 'signal'"),
        ((_result_ref(generation=-1),), 1, "Invalid result metadata"),
        ((_result_ref(length=-1),), 1, "Invalid result metadata"),
        ((_result_ref(decimation=0),), 1, "Invalid result metadata"),
        (
            (_result_ref(length=1),),
            1,
            "Detached result length does not match",
        ),
        ((_result_ref(),), 0, "Next result generation is not monotonic"),
    ],
)
def test_snapshot_restore_rejects_invalid_result_metadata(
    results: tuple[ResultSeriesSnapshot, ...],
    next_generation: int,
    message: str,
) -> None:
    runner = initialized_runner()
    snapshot = replace(
        runner.capture_snapshot(),
        results=results,
        next_result_generation=next_generation,
    )

    with pytest.raises(SnapshotValidationError, match=message):
        runner.restore_snapshot(snapshot)


def test_compact_snapshot_restore_requires_an_existing_result_generation() -> None:
    runner = initialized_runner()
    compact = replace(
        runner._state_history[-1],
        results=(_result_ref(key="ghost", generation=7),),
        next_result_generation=8,
    )

    with pytest.raises(SnapshotValidationError, match="Missing result generation"):
        runner._prepare_snapshot_restore(compact)


def test_compact_snapshot_restore_rejects_length_beyond_generation() -> None:
    runner = initialized_runner()
    runner._result_generations["ghost"] = 7
    runner._results["ghost"] = []
    compact = replace(
        runner._state_history[-1],
        results=(_result_ref(key="ghost", generation=7, length=1),),
        next_result_generation=8,
    )

    with pytest.raises(SnapshotValidationError, match="length exceeds generation"):
        runner._prepare_snapshot_restore(compact)


def test_snapshot_preparation_rejects_unsupported_objects() -> None:
    runner = initialized_runner()

    with pytest.raises(SnapshotValidationError, match="Unsupported runner snapshot"):
        runner._prepare_snapshot_restore(object())  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_enter_step_mode_initializes_a_fresh_runner() -> None:
    runner = SimulationRunner(constant_model(), SimulationConfig())

    assert await runner.enter_step_mode() is True
    assert runner._compiled is not None
    assert runner.status == SimulationStatus.PAUSED
    assert runner._active_operation is None


@pytest.mark.asyncio
async def test_enter_step_mode_rejects_existing_handoff_and_foreground_owner() -> None:
    runner = SimulationRunner(constant_model(), SimulationConfig())
    background = runner.mark_scheduled()
    runner._is_paused = True
    runner._pause_acknowledged.set()
    runner._pending_handoff = SimulationOperationToken("step-enter")

    with pytest.raises(SimulationOperationConflict, match="handoff"):
        await runner.enter_step_mode()

    runner._pending_handoff = None
    assert runner.release_unadopted_operation(background) is True
    foreground = runner._reserve_operation("reset")
    with pytest.raises(SimulationOperationConflict, match="busy with reset"):
        await runner.enter_step_mode()
    assert runner._release_operation(foreground) is True


@pytest.mark.asyncio
async def test_enter_step_mode_cancellation_cleans_up_foreground_ownership() -> None:
    runner = SimulationRunner(constant_model(), SimulationConfig())
    runner._enter_step_mode_owned = Mock(side_effect=asyncio.CancelledError)

    with pytest.raises(asyncio.CancelledError):
        await runner.enter_step_mode()

    assert runner._active_operation is None
    assert runner._transition_requested is False
    assert runner._is_paused is True
    assert runner._resume_gate.is_set() is False
    assert runner.status == SimulationStatus.PAUSED


@pytest.mark.asyncio
async def test_enter_step_mode_records_checkpoint_failure() -> None:
    runner = initialized_runner()
    runner._step_mode = False
    runner._save_state = Mock(side_effect=RuntimeError("save failed"))

    assert await runner.enter_step_mode() is False
    assert runner.status == SimulationStatus.ERROR
    assert runner.error_message == "save failed"
    assert runner._active_operation is None


def test_initialize_step_mode_records_adapter_failure() -> None:
    runner = SimulationRunner(constant_model(), SimulationConfig())
    runner._adapter.initialize = Mock(side_effect=RuntimeError("init failed"))

    assert runner.initialize_step_mode() is False
    assert runner.status == SimulationStatus.ERROR
    assert runner.error_message == "init failed"
    assert runner._active_operation is None


def test_step_forward_reports_compilation_failure_without_detailed_errors() -> None:
    runner = SimulationRunner(constant_model(), SimulationConfig())
    runner._compiler.compile = Mock(
        return_value=CompiledModel(success=False, message="bad graph")
    )

    assert runner.step_forward() == {"success": False, "error": "bad graph"}


def test_reset_step_mode_is_a_noop_before_initialization() -> None:
    runner = SimulationRunner(constant_model(), SimulationConfig())
    runner._adapter.initialize = Mock()

    runner.reset_step_mode()

    runner._adapter.initialize.assert_not_called()
    assert runner.status == SimulationStatus.IDLE


@pytest.mark.asyncio
async def test_continue_releases_a_pending_pause_waiter_after_failure() -> None:
    runner = initialized_runner()
    waiter = asyncio.Event()
    runner._pause_waiter = waiter
    runner._adapter.step = Mock(side_effect=RuntimeError("step failed"))
    token = runner.schedule_continue()
    runner._pause_waiter = waiter

    await runner.continue_from_step_mode(token)

    assert waiter.is_set()
    assert runner.status == SimulationStatus.ERROR


@pytest.mark.asyncio
async def test_run_records_adapter_initialization_failure() -> None:
    runner = SimulationRunner(constant_model(), SimulationConfig())
    runner._adapter.initialize = Mock(side_effect=RuntimeError("run init failed"))

    await runner.run()

    assert runner.status == SimulationStatus.ERROR
    assert runner.error_message == "run init failed"
    assert runner._active_operation is None


@pytest.mark.asyncio
async def test_run_preserves_paused_status_when_already_in_step_mode() -> None:
    runner = initialized_runner()

    await runner.run()

    assert runner.status == SimulationStatus.PAUSED
    assert runner._step_mode is True


@pytest.mark.asyncio
async def test_pause_wait_helper_handles_waiters_and_stop_boundaries() -> None:
    runner = SimulationRunner(constant_model(), SimulationConfig())
    waiter = asyncio.Event()
    runner._pause_waiter = waiter
    runner._is_paused = True
    runner._resume_gate.clear()
    task = asyncio.create_task(runner._wait_while_paused())
    await asyncio.sleep(0)

    assert waiter.is_set()
    assert runner._pause_acknowledged.is_set()
    runner.resume()
    await task
    assert runner.status == SimulationStatus.RUNNING

    runner._is_paused = True
    runner._should_stop = True
    await runner._wait_while_paused()
    assert runner.status == SimulationStatus.RUNNING

    runner._should_stop = False
    runner._is_paused = True
    runner._pause_waiter = None
    runner._resume_gate.clear()
    task = asyncio.create_task(runner._wait_while_paused())
    await asyncio.sleep(0)
    runner.resume()
    await task
    assert runner.status == SimulationStatus.RUNNING
