"""FAC-9 regressions for isolation between independent simulations."""

import ast
import asyncio
import math
from collections import Counter
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Barrier

import pytest

from src.models.model import Model
from src.models.simulation import SimulationConfig, SimulationStatus, SolverType
from src.osk import Block, Sim, SimContext, State, activate_context, get_active_context
from src.osk.blocks.continuous import TransportDelay
from src.osk.blocks.discrete import UnitDelay
from src.osk.blocks.signal_processing import LowPassFilter, RateLimiter
from src.osk.blocks.sources import Clock, SineWave
from src.simulation.compiler import CompiledBlock, CompiledModel, ModelCompiler
from src.simulation.osk_adapter import BLOCK_SNAPSHOT_CODECS, BLOCK_TYPE_MAP, OSKAdapter
from src.simulation.runner import (
    SimulationOperationConflict,
    SimulationOperationToken,
    SimulationRunner,
)
from src.simulation.snapshot import SnapshotValidationError


def _driven_integrator_model() -> Model:
    """Return x' = sin(t), which distinguishes Euler from RK4."""
    return Model.model_validate(
        {
            "id": "fac9-driven-integrator",
            "metadata": {"name": "FAC-9 driven integrator"},
            "blocks": [
                {
                    "id": "sine",
                    "type": "sine_wave",
                    "name": "sin(t)",
                    "position": {"x": 0, "y": 0},
                    "parameters": {
                        "amplitude": 1.0,
                        "frequency": 1.0 / (2.0 * math.pi),
                        "phase": 0.0,
                        "bias": 0.0,
                    },
                    "outputPorts": [{"id": "sine-out", "name": "out"}],
                },
                {
                    "id": "integrator",
                    "type": "integrator",
                    "name": "Integral",
                    "position": {"x": 100, "y": 0},
                    "parameters": {"initialCondition": 0.0},
                    "inputPorts": [{"id": "integrator-in", "name": "in"}],
                    "outputPorts": [{"id": "integrator-out", "name": "out"}],
                },
                {
                    "id": "scope",
                    "type": "scope",
                    "name": "Scope",
                    "position": {"x": 200, "y": 0},
                    "parameters": {"numInputs": 1},
                    "inputPorts": [{"id": "scope-in", "name": "in"}],
                },
            ],
            "connections": [
                {
                    "id": "sine-to-integrator",
                    "sourceBlockId": "sine",
                    "sourcePortId": "sine-out",
                    "targetBlockId": "integrator",
                    "targetPortId": "integrator-in",
                },
                {
                    "id": "integrator-to-scope",
                    "sourceBlockId": "integrator",
                    "sourcePortId": "integrator-out",
                    "targetBlockId": "scope",
                    "targetPortId": "scope-in",
                },
            ],
        }
    )


def _snapshot_state_zoo_model() -> Model:
    """Return a graph exercising RNG, continuous, discrete, delay, and sink state."""
    block_types = [
        ("ramp", "ramp", {"slope": 0.75, "startTime": 0.0, "initialOutput": 0.2}, 0, 1),
        ("integrator", "integrator", {"initialCondition": 0.1}, 1, 1),
        (
            "noise",
            "white_noise",
            {"mean": 0.0, "variance": 0.25, "seed": 1234, "sampleTime": 0.0},
            0,
            1,
        ),
        ("filter", "low_pass_filter", {"cutoffFrequency": 1.3}, 1, 1),
        ("unit-delay", "unit_delay", {"initialCondition": -0.2, "sampleTime": 0.15}, 1, 1),
        (
            "transport-delay",
            "transport_delay",
            {"delayTime": 0.25, "initialOutput": -0.3},
            1,
            1,
        ),
        ("scope", "scope", {"numInputs": 2}, 2, 0),
        (
            "scope-3d",
            "scope_3d",
            {"xLabel": "X", "yLabel": "Y", "zLabel": "Z"},
            3,
            0,
        ),
    ]
    blocks = []
    for index, (block_id, block_type, parameters, inputs, outputs) in enumerate(block_types):
        blocks.append(
            {
                "id": block_id,
                "type": block_type,
                "name": block_id,
                "position": {"x": index * 100, "y": 0},
                "parameters": parameters,
                "inputPorts": [
                    {"id": f"{block_id}-in-{port}", "name": f"in{port}"}
                    for port in range(inputs)
                ],
                "outputPorts": [
                    {"id": f"{block_id}-out-{port}", "name": f"out{port}"}
                    for port in range(outputs)
                ],
            }
        )

    edges = [
        ("ramp", 0, "integrator", 0),
        ("noise", 0, "filter", 0),
        ("filter", 0, "unit-delay", 0),
        ("unit-delay", 0, "transport-delay", 0),
        ("integrator", 0, "scope", 0),
        ("transport-delay", 0, "scope", 1),
        ("integrator", 0, "scope-3d", 0),
        ("filter", 0, "scope-3d", 1),
        ("transport-delay", 0, "scope-3d", 2),
    ]
    connections = [
        {
            "id": f"edge-{index}",
            "sourceBlockId": source,
            "sourcePortId": f"{source}-out-{source_port}",
            "targetBlockId": target,
            "targetPortId": f"{target}-in-{target_port}",
        }
        for index, (source, source_port, target, target_port) in enumerate(edges)
    ]
    return Model.model_validate(
        {
            "id": "fac9-snapshot-state-zoo",
            "metadata": {"name": "FAC-9 snapshot state zoo"},
            "blocks": blocks,
            "connections": connections,
        }
    )


def _config(solver: SolverType, step_size: float) -> SimulationConfig:
    return SimulationConfig(solver=solver, step_size=step_size, stop_time=1.0)


def _adapter_value(adapter: OSKAdapter) -> float:
    return float(adapter._osk_blocks["integrator"].getOutput())


def _adapter_snapshot(
    adapter: OSKAdapter,
) -> tuple[float, float, float, float, str, int, int]:
    context = adapter.context
    return (
        context.t,
        context.t1,
        context.dt,
        context.dtp,
        context.method,
        context.kpass,
        context.ready,
    )


def _context_snapshot(
    context: SimContext,
) -> tuple[float, float, float, float, str, int, int, int, int, int, int]:
    return (
        context.t,
        context.t1,
        context.dt,
        context.dtp,
        context.method,
        context.kpass,
        context.ready,
        context.tickfirst,
        context.ticklast,
        context.stop,
        context.stop0,
    )


def _initialized_builtin(
    factory: Callable[[], Block], step_size: float
) -> tuple[Block, SimContext]:
    context = SimContext(dt=step_size, dtp=step_size)
    block = factory()
    block.bind_context(context, object())
    block.init()
    return block, context


def _advance_builtin(block: Block, context: SimContext, index: int) -> float:
    context.t = index * context.dtp
    context.t1 = context.t
    context.dt = context.dtp
    context.ready = 1
    if hasattr(block, "setInput"):
        block.setInput(1.5 + math.sin(1.7 * context.t))
    block.update()
    return float(block.getOutput())


def _builtin_reference(
    factory: Callable[[], Block], step_size: float, steps: int
) -> list[float]:
    block, context = _initialized_builtin(factory, step_size)
    return [_advance_builtin(block, context, index) for index in range(steps)]


def test_every_registered_builtin_has_an_explicit_versioned_snapshot_codec():
    assert set(BLOCK_SNAPSHOT_CODECS) == set(BLOCK_TYPE_MAP)
    assert len(BLOCK_TYPE_MAP) == 181
    assert all(codec.version >= 1 for codec in BLOCK_SNAPSHOT_CODECS.values())


def test_adapter_snapshot_is_detached_immutable_and_round_trips_complete_state():
    adapter = OSKAdapter()
    adapter.initialize(
        ModelCompiler().compile(_driven_integrator_model()),
        _config(SolverType.RK4, 0.05),
    )
    for index in range(4):
        adapter.step(index * 0.05, 0.05)

    integrator = adapter._osk_blocks["integrator"].vState[0]
    integrator.x0 = 3.25
    integrator.xd0 = 1.0
    integrator.xd1 = 2.0
    integrator.xd2 = 3.0
    integrator.xd3 = 4.0
    integrator.xd4 = 5.0
    adapter.context.tickfirst = 0
    adapter.context.ticklast = 1
    adapter.context.stop = 7
    adapter.context.stop0 = 6
    snapshot = adapter.capture_snapshot()

    with pytest.raises(AttributeError):
        snapshot.context.t = 99.0  # type: ignore[misc]
    original_payload = snapshot.blocks[1].attributes
    adapter.step(0.2, 0.05)
    assert snapshot.blocks[1].attributes == original_payload

    adapter.restore_snapshot(snapshot)
    assert adapter.capture_snapshot() == snapshot
    restored = adapter._osk_blocks["integrator"].vState[0]
    assert (restored.x0, restored.xd0, restored.xd1, restored.xd2, restored.xd3, restored.xd4) == (
        3.25,
        1.0,
        2.0,
        3.0,
        4.0,
        5.0,
    )


def test_adapter_snapshot_validation_and_commit_failure_are_non_mutating(monkeypatch):
    adapter = OSKAdapter()
    adapter.initialize(
        ModelCompiler().compile(_driven_integrator_model()),
        _config(SolverType.RK4, 0.05),
    )
    for index in range(3):
        adapter.step(index * 0.05, 0.05)
    target = adapter.capture_snapshot()
    adapter.step(0.15, 0.05)
    before = adapter.capture_snapshot()

    invalid_snapshots = [
        replace(target, schema_version=target.schema_version + 1),
        replace(target, model_fingerprint="wrong-model"),
        replace(target, config_fingerprint="wrong-config"),
        replace(target, blocks=target.blocks[:-1]),
        replace(
            target,
            blocks=(replace(target.blocks[0], block_type="clock"), *target.blocks[1:]),
        ),
        replace(target, context=replace(target.context, ready=0)),
    ]
    for invalid in invalid_snapshots:
        with pytest.raises(SnapshotValidationError):
            adapter.restore_snapshot(invalid)
        assert adapter.capture_snapshot() == before

    codec = BLOCK_SNAPSHOT_CODECS["integrator"]
    original_apply = codec.apply
    calls = 0

    def fail_once(prepared):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("injected codec failure")
        original_apply(prepared)

    monkeypatch.setattr(codec, "apply", fail_once)
    with pytest.raises(RuntimeError, match="injected codec failure"):
        adapter.restore_snapshot(target)

    assert calls == 2
    assert adapter.capture_snapshot() == before


def _checkpoint_observable(snapshot):
    return (
        snapshot.adapter,
        snapshot.current_time,
        snapshot.progress,
        snapshot.total_steps,
        snapshot.next_result_generation,
        snapshot.results,
    )


def test_runner_checkpoint_replay_covers_state_zoo_and_preserves_peer():
    config = SimulationConfig(
        solver=SolverType.RK4,
        step_size=0.1,
        stop_time=2.0,
        max_result_points=5,
    )
    runner = SimulationRunner(_snapshot_state_zoo_model(), config)
    peer = SimulationRunner(_driven_integrator_model(), config)
    assert runner.initialize_step_mode() is True
    assert peer.initialize_step_mode() is True
    assert runner.step_forward(7)["success"] is True
    assert peer.step_forward(3)["success"] is True
    checkpoint = runner.capture_snapshot()
    peer_before = peer.capture_snapshot()

    assert runner.step_forward(5)["success"] is True
    expected = runner.capture_snapshot()
    runner.restore_snapshot(checkpoint)

    assert runner.status == SimulationStatus.PAUSED
    assert runner._step_mode is True
    assert runner._active_operation is None
    assert runner._pending_handoff is None
    assert len(runner._state_history) == 1
    assert runner._state_history[0].compact
    assert all(not result.values for result in runner._state_history[0].results)
    assert runner.step_forward(5)["success"] is True
    replayed = runner.capture_snapshot()

    assert _checkpoint_observable(replayed) == _checkpoint_observable(expected)
    assert peer.capture_snapshot() == peer_before


def test_runner_checkpoint_validation_ownership_and_failed_commit_are_atomic(monkeypatch):
    config = SimulationConfig(solver=SolverType.RK4, step_size=0.1, stop_time=2.0)
    runner = SimulationRunner(_snapshot_state_zoo_model(), config)
    assert runner.initialize_step_mode() is True
    runner.step_forward(3)
    target = runner.capture_snapshot()
    runner.step_forward(2)
    before = runner.capture_snapshot()
    history_before = tuple(runner._state_history)
    checkpoints_before = {
        key: dict(generations) for key, generations in runner._result_checkpoints.items()
    }

    invalid_snapshots = [
        replace(target, schema_version=target.schema_version + 1),
        replace(target, current_time=target.current_time + 0.1),
        replace(target, progress=target.progress + 0.1),
        replace(target, adapter=replace(target.adapter, blocks=target.adapter.blocks[:-1])),
    ]
    for invalid in invalid_snapshots:
        with pytest.raises(SnapshotValidationError):
            runner.restore_snapshot(invalid)
        assert runner.capture_snapshot() == before
        assert tuple(runner._state_history) == history_before

    runner.context.kpass = 1
    runner.context.ready = 0
    with pytest.raises(SnapshotValidationError, match="committed simulation boundary"):
        runner.capture_snapshot()
    assert runner._active_operation is None
    runner.context.kpass = 0
    runner.context.ready = 1

    reservation = runner.mark_scheduled()
    with pytest.raises(SimulationOperationConflict):
        runner.capture_snapshot()
    with pytest.raises(SimulationOperationConflict):
        runner.restore_snapshot(target)
    assert runner._release_operation(reservation) is True

    other = SimulationRunner(_driven_integrator_model(), config)
    assert other.initialize_step_mode() is True
    other_before = other.capture_snapshot()
    with pytest.raises(SnapshotValidationError, match="model fingerprint"):
        other.restore_snapshot(target)
    assert other.capture_snapshot() == other_before

    codec = BLOCK_SNAPSHOT_CODECS["integrator"]
    original_apply = codec.apply
    calls = 0

    def fail_once(prepared):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("injected runner codec failure")
        original_apply(prepared)

    monkeypatch.setattr(codec, "apply", fail_once)
    with pytest.raises(RuntimeError, match="injected runner codec failure"):
        runner.restore_snapshot(target)

    assert calls >= 2
    assert runner.capture_snapshot() == before
    assert tuple(runner._state_history) == history_before
    assert runner._result_checkpoints == checkpoints_before
    assert runner._active_operation is None


def _run_adapter_isolated(solver: SolverType, step_size: float, steps: int) -> float:
    adapter = OSKAdapter()
    adapter.initialize(
        ModelCompiler().compile(_driven_integrator_model()), _config(solver, step_size)
    )
    for index in range(steps):
        adapter.step(index * step_size, step_size)
    return _adapter_value(adapter)


def _run_runner_isolated(solver: SolverType, step_size: float, steps: int) -> float:
    runner = SimulationRunner(_driven_integrator_model(), _config(solver, step_size))
    assert runner.initialize_step_mode() is True
    assert runner.step_forward(steps)["success"] is True
    return _adapter_value(runner._adapter)


def _stable_runner_results(runner: SimulationRunner) -> dict:
    results = runner.get_results()
    results["statistics"].pop("executionTime")
    return results


def test_same_runner_operation_reservation_is_atomic_across_threads():
    runner = SimulationRunner(_driven_integrator_model(), _config(SolverType.EULER, 0.01))
    barrier = Barrier(2)

    def reserve() -> SimulationOperationToken | SimulationOperationConflict:
        barrier.wait()
        try:
            return runner.mark_scheduled()
        except SimulationOperationConflict as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as executor:
        claims = list(executor.map(lambda _: reserve(), range(2)))

    tokens = [claim for claim in claims if isinstance(claim, SimulationOperationToken)]
    conflicts = [claim for claim in claims if isinstance(claim, SimulationOperationConflict)]
    assert len(tokens) == 1
    assert len(conflicts) == 1
    assert runner.has_live_run
    assert runner._release_operation(tokens[0]) is True
    assert not runner.has_live_run


def test_exact_operation_release_prevents_stale_completion_aba():
    runner = SimulationRunner(_driven_integrator_model(), _config(SolverType.EULER, 0.01))
    runner._pause_acknowledged.set()
    first = runner.mark_scheduled()
    first_finished = first.finished
    forged = SimulationOperationToken(kind="run", background=True)

    assert not runner._pause_acknowledged.is_set()
    assert runner._release_operation(forged) is False
    assert runner.has_live_run
    assert not first_finished.is_set()
    assert runner._release_operation(first) is True
    assert first_finished.is_set()

    second = runner.mark_scheduled()
    second_finished = second.finished
    assert second_finished is not first_finished
    assert not second_finished.is_set()
    assert runner._release_operation(first) is False
    assert runner.has_live_run
    assert not second_finished.is_set()
    assert runner._release_operation(second) is True
    assert second_finished.is_set()
    assert not runner.has_live_run


@pytest.mark.asyncio
async def test_scheduled_operation_token_can_only_be_adopted_once():
    runner = SimulationRunner(_driven_integrator_model(), _config(SolverType.EULER, 0.01))
    token = runner.mark_scheduled()

    outcomes = await asyncio.gather(
        runner.run(token),
        runner.run(token),
        return_exceptions=True,
    )

    assert sum(outcome is None for outcome in outcomes) == 1
    conflicts = [
        outcome for outcome in outcomes if isinstance(outcome, SimulationOperationConflict)
    ]
    assert len(conflicts) == 1
    assert token.finished.is_set()
    assert not runner.has_live_run


def _advance_decay(context: SimContext, state: State, start: float) -> None:
    context.begin_step(start, context.dtp)
    for kpass in range(context.pass_count):
        context.enter_stage(kpass)
        state.x[1] = -state.x[0]
        state.propagate()
    context.complete_step()


class _NativeProbe(Block):
    """Small native-OSK block that records compatibility-facade values."""

    def __init__(self, barrier: Barrier | None = None):
        super().__init__()
        self.x = self.addIntegrator([1.0, 0.0])
        self.barrier = barrier
        self.waited = False
        self.facade_checks: tuple[int, int, int] | None = None
        self.observed: list[tuple[float, str, float, list[float], object]] = []

    def update(self) -> None:
        if self.barrier is not None and not self.waited:
            self.waited = True
            self.barrier.wait(timeout=5)
        if self.facade_checks is None:
            Sim.stop = 7
            assigned_stop = self.context.stop
            Sim.terminate(9)
            terminated_stop = self.context.stop
            Sim.stop = 0
            original_ready = self.context.ready
            self.context.ready = 0
            Sim.sample(State.t)
            sampled_ready = self.context.ready
            self.context.ready = original_ready
            self.facade_checks = (assigned_stop, terminated_stop, sampled_ready)
        self.observed.append((State.t, State.method, Sim.tmax, Sim.dts, Sim.vStage))
        self.x[1] = -self.x[0]

    def getOutput(self, port: int = 0) -> float:
        return self.x[0]


def _native_sim(
    method: str,
    step_size: float,
    stop_time: float,
    barrier: Barrier | None = None,
) -> tuple[Sim, _NativeProbe]:
    with activate_context(SimContext(method=method)):
        block = _NativeProbe(barrier)
        sim = Sim(dts=[step_size], tmax=stop_time, vStage=[[block]])
    return sim, block


def test_explicit_contexts_alternate_every_stage_without_crosstalk():
    rk2 = SimContext(method="RK2", dt=0.1, dtp=0.1)
    merson = SimContext(method="Merson", dt=0.04, dtp=0.04)
    rk2_state = State([1.0, 0.0], context=rk2)
    merson_state = State([1.0, 0.0], context=merson)

    rk2.begin_step(0.0, rk2.dtp)
    merson.begin_step(0.0, merson.dtp)
    for kpass in range(max(rk2.pass_count, merson.pass_count)):
        if kpass < rk2.pass_count:
            rk2.enter_stage(kpass)
            rk2_state.x[1] = -rk2_state.x[0]
            rk2_state.propagate()
        if kpass < merson.pass_count:
            merson.enter_stage(kpass)
            merson_state.x[1] = -merson_state.x[0]
            merson_state.propagate()
    rk2.complete_step()
    merson.complete_step()

    isolated_rk2 = SimContext(method="RK2", dt=0.1, dtp=0.1)
    isolated_merson = SimContext(method="Merson", dt=0.04, dtp=0.04)
    expected_rk2 = State([1.0, 0.0], context=isolated_rk2)
    expected_merson = State([1.0, 0.0], context=isolated_merson)
    _advance_decay(isolated_rk2, expected_rk2, 0.0)
    _advance_decay(isolated_merson, expected_merson, 0.0)

    assert rk2_state.x == pytest.approx(expected_rk2.x)
    assert merson_state.x == pytest.approx(expected_merson.x)
    assert rk2.t == pytest.approx(0.1)
    assert merson.t == pytest.approx(0.04)


def test_state_uses_explicit_context_while_another_context_is_active():
    bound = SimContext(method="Euler", dt=0.2, dtp=0.2, kpass=0)
    active = SimContext(method="RK4", dt=0.01, dtp=0.01, kpass=3)
    state = State([0.0, 1.0], context=bound)

    with activate_context(active):
        state.propagate()

    assert state.x[0] == pytest.approx(0.2)
    assert active.t == 0.0


def test_state_facade_reads_and_writes_only_the_active_context():
    first = SimContext()
    second = SimContext()

    with activate_context(first):
        State.t = 3.0
        State.method = "Euler"
        assert State.t == 3.0
    with activate_context(second):
        assert State.t == 0.0
        assert State.method == "RK4"
        State.dt = 0.25

    assert first.t == 3.0
    assert first.method == "Euler"
    assert first.dt == 0.01
    assert second.dt == 0.25


def test_nested_activation_and_exceptions_restore_the_previous_context():
    outer = SimContext()
    inner = SimContext()

    with activate_context(outer):
        assert get_active_context() is outer
        with pytest.raises(RuntimeError, match="boom"), activate_context(inner):
            assert get_active_context() is inner
            raise RuntimeError("boom")
        assert get_active_context() is outer


@pytest.mark.asyncio
async def test_task_cancellation_restores_the_inherited_context():
    outer = SimContext()
    inner = SimContext()
    entered = asyncio.Event()
    restored: list[SimContext] = []

    async def wait_until_cancelled() -> None:
        try:
            with activate_context(inner):
                entered.set()
                await asyncio.Event().wait()
        finally:
            restored.append(get_active_context())

    with activate_context(outer):
        task = asyncio.create_task(wait_until_cancelled())
        await entered.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert get_active_context() is outer

    assert restored == [outer]


@pytest.mark.asyncio
async def test_facade_values_are_isolated_between_simultaneous_tasks():
    first = SimContext()
    second = SimContext()
    barrier = asyncio.Barrier(2)

    async def write_and_read(context: SimContext, value: float) -> float:
        with activate_context(context):
            State.t = value
            await barrier.wait()
            await asyncio.sleep(0)
            return State.t

    observed = await asyncio.gather(
        write_and_read(first, 1.25),
        write_and_read(second, 9.5),
    )

    assert observed == [1.25, 9.5]
    assert first.t == 1.25
    assert second.t == 9.5


def test_context_owner_claim_is_identity_based_and_survives_reset():
    context = SimContext()
    owner = object()
    original_id = id(context)

    context.claim_owner(owner)
    context.claim_owner(owner)
    context.reset(dtp=0.2, method="Euler")

    assert id(context) == original_id
    assert context.owner is owner
    assert context.dtp == 0.2
    assert context.method == "Euler"
    with pytest.raises(ValueError, match="already owned"):
        context.claim_owner(object())


def test_adapter_ownership_and_reset_preserve_context_identity():
    context = SimContext()
    adapter = OSKAdapter(context)
    original_id = id(adapter.context)
    compiled = ModelCompiler().compile(_driven_integrator_model())

    with pytest.raises(ValueError, match="already owned"):
        OSKAdapter(context)

    adapter.initialize(compiled, _config(SolverType.EULER, 0.1))
    adapter.initialize(compiled, _config(SolverType.RK4, 0.05))
    assert id(adapter.context) == original_id
    assert adapter.context.owner is adapter
    assert adapter.context.method == "RK4"


def test_adapter_initialization_exception_restores_the_previous_context():
    outer = SimContext()
    adapter = OSKAdapter()
    invalid = CompiledModel(
        success=True,
        message="intentionally invalid",
        blocks=[
            CompiledBlock(
                id="unknown",
                type="not_registered",
                name="Unknown",
                parameters={},
            )
        ],
        execution_order=["unknown"],
    )

    with activate_context(outer):
        with pytest.raises(ValueError, match="Unknown block type"):
            adapter.initialize(invalid, _config(SolverType.RK4, 0.1))
        assert get_active_context() is outer


def test_explicit_state_legacy_delegates_ignore_another_active_context():
    bound = SimContext(method="Euler", dt=0.1, dtp=0.1)
    ambient = SimContext(method="RK4", dt=0.01, dtp=0.01)
    state = State(context=bound)

    with activate_context(ambient):
        state.reset(0.2)
        state.updateclock()

    assert bound.t == pytest.approx(0.2)
    assert bound.dtp == pytest.approx(0.2)
    assert ambient.t == 0.0
    assert ambient.dtp == 0.01


def test_context_rejects_invalid_stage_and_preserves_unknown_method_fallback():
    context = SimContext(method="unknown", dt=0.1, dtp=0.1)
    state = State([0.0, 1.0], context=context)

    assert context.effective_method == "RK4"
    assert context.pass_count == 4
    with pytest.raises(ValueError, match="Invalid stage"):
        context.enter_stage(4)

    context.kpass = -1
    with pytest.raises(ValueError, match="Invalid current stage"):
        state.updateclock()

    context.kpass = 0
    context.enter_stage(0)
    state.propagate()
    assert state.x[0] == pytest.approx(0.05)

    context.request_stop(-2)
    assert context.stop == -2


def test_adapters_with_different_solvers_can_step_alternately_without_crosstalk():
    euler_step = 0.1
    rk4_step = 0.05
    euler_steps = 6
    rk4_steps = 9
    euler_reference = _run_adapter_isolated(SolverType.EULER, euler_step, euler_steps)
    rk4_reference = _run_adapter_isolated(SolverType.RK4, rk4_step, rk4_steps)

    euler = OSKAdapter()
    rk4 = OSKAdapter()
    compiled = ModelCompiler().compile(_driven_integrator_model())
    euler.initialize(compiled, _config(SolverType.EULER, euler_step))
    rk4.initialize(compiled, _config(SolverType.RK4, rk4_step))

    assert euler.context.method == "Euler"
    assert euler.context.dtp == pytest.approx(euler_step)
    assert rk4.context.method == "RK4"
    assert rk4.context.dtp == pytest.approx(rk4_step)

    for index in range(max(euler_steps, rk4_steps)):
        if index < euler_steps:
            euler.step(index * euler_step, euler_step)
        if index < rk4_steps:
            rk4.step(index * rk4_step, rk4_step)

    assert _adapter_value(euler) == pytest.approx(euler_reference)
    assert _adapter_value(rk4) == pytest.approx(rk4_reference)


@pytest.mark.parametrize(
    "factory",
    [
        pytest.param(
            lambda: SineWave(amplitude=2.0, frequency=0.75, phase=0.2, bias=-0.1),
            id="sine-wave",
        ),
        pytest.param(Clock, id="clock"),
        pytest.param(
            lambda: RateLimiter(rising_rate=1.25, falling_rate=-0.8),
            id="rate-limiter",
        ),
        pytest.param(lambda: LowPassFilter(cutoff_freq=1.4), id="low-pass-filter"),
        pytest.param(
            lambda: UnitDelay(initial_condition=-0.5, sample_time=0.15),
            id="unit-delay",
        ),
        pytest.param(
            lambda: TransportDelay(delay_time=0.18, initial_output=-0.5),
            id="transport-delay",
        ),
    ],
)
@pytest.mark.parametrize("chunk_size", [1, 2], ids=["ABAB", "AABB"])
def test_timing_sensitive_builtins_match_isolated_traces_when_interleaved(
    factory: Callable[[], Block], chunk_size: int
):
    cases = {"first": (0.1, 9), "second": (0.06, 13)}
    references = {
        name: _builtin_reference(factory, step_size, steps)
        for name, (step_size, steps) in cases.items()
    }
    instances = {
        name: _initialized_builtin(factory, step_size)
        for name, (step_size, _) in cases.items()
    }
    traces = {name: [] for name in cases}
    indices = {name: 0 for name in cases}

    while any(indices[name] < cases[name][1] for name in cases):
        for name, peer in (("first", "second"), ("second", "first")):
            block, context = instances[name]
            _, steps = cases[name]
            for _ in range(chunk_size):
                index = indices[name]
                if index >= steps:
                    break
                peer_before = _context_snapshot(instances[peer][1])
                traces[name].append(_advance_builtin(block, context, index))
                indices[name] += 1
                assert _context_snapshot(instances[peer][1]) == peer_before

    assert traces["first"] == pytest.approx(references["first"])
    assert traces["second"] == pytest.approx(references["second"])


@pytest.mark.parametrize("chunk_size", [1, 2], ids=["ABAB", "AABB"])
def test_adapter_schedules_preserve_complete_peer_state_and_output_traces(chunk_size: int):
    cases = {
        "euler": (SolverType.EULER, 0.1, 8),
        "rk4": (SolverType.RK4, 0.01, 80),
    }

    def initialized(solver: SolverType, step_size: float) -> OSKAdapter:
        adapter = OSKAdapter()
        adapter.initialize(
            ModelCompiler().compile(_driven_integrator_model()),
            _config(solver, step_size),
        )
        return adapter

    references: dict[str, list[float]] = {}
    for name, (solver, step_size, steps) in cases.items():
        adapter = initialized(solver, step_size)
        references[name] = [
            next(iter(adapter.step(index * step_size, step_size).values()))
            for index in range(steps)
        ]

    adapters = {
        name: initialized(solver, step_size)
        for name, (solver, step_size, _) in cases.items()
    }
    traces = {name: [] for name in cases}
    indices = {name: 0 for name in cases}
    while any(indices[name] < cases[name][2] for name in cases):
        for name, peer in (("euler", "rk4"), ("rk4", "euler")):
            _, step_size, steps = cases[name]
            for _ in range(chunk_size):
                index = indices[name]
                if index >= steps:
                    break
                peer_before = _adapter_snapshot(adapters[peer])
                outputs = adapters[name].step(index * step_size, step_size)
                traces[name].append(next(iter(outputs.values())))
                indices[name] += 1
                assert _adapter_snapshot(adapters[peer]) == peer_before

    assert traces["euler"] == pytest.approx(references["euler"])
    assert traces["rk4"] == pytest.approx(references["rk4"])


def test_stateful_run_simulation_uses_the_adapter_context():
    adapter = OSKAdapter()
    adapter.initialize(
        ModelCompiler().compile(_driven_integrator_model()),
        _config(SolverType.RK4, 0.05),
    )

    adapter.run_simulation()

    assert adapter.context.t == pytest.approx(1.0)
    assert _adapter_value(adapter) == pytest.approx(1.0 - math.cos(1.0), abs=1e-6)


def test_nonzero_start_time_is_shared_by_adapter_runner_and_reset_snapshots():
    config = SimulationConfig(
        solver=SolverType.RK4,
        start_time=2.5,
        stop_time=2.8,
        step_size=0.1,
    )
    runner = SimulationRunner(_driven_integrator_model(), config)
    context_id = id(runner.context)

    assert runner.context is runner._adapter.context
    assert runner.current_time == pytest.approx(2.5)
    assert runner.initialize_step_mode() is True
    assert runner.context.t == pytest.approx(2.5)
    assert runner.context.t1 == pytest.approx(2.5)
    assert runner._state_history[-1].adapter.context.t == pytest.approx(2.5)

    assert runner.step_forward()["success"] is True
    assert runner._results
    assert runner.initialize_step_mode() is True
    assert runner.current_time == pytest.approx(2.5)
    assert runner.progress == 0.0
    assert runner._total_steps == 0
    assert runner._results == {}
    assert len(runner._state_history) == 1
    assert runner.context.t == pytest.approx(2.5)

    assert runner.step_forward()["success"] is True
    runner._execution_time = 42.0
    runner._error_message = "stale error"
    runner._should_stop = True
    runner._is_paused = True
    runner.reset_step_mode()
    assert id(runner.context) == context_id
    assert runner.current_time == pytest.approx(2.5)
    assert runner._execution_time == 0.0
    assert runner._error_message is None
    assert runner._should_stop is False
    assert runner._is_paused is False
    assert runner.context.t == pytest.approx(2.5)
    assert runner.context.t1 == pytest.approx(2.5)
    assert runner._state_history[-1].adapter.context.t == pytest.approx(2.5)

    runner.step_forward()
    runner.reset()
    assert id(runner.context) == context_id
    assert runner.current_time == pytest.approx(2.5)
    assert runner.context.t == pytest.approx(2.5)
    assert runner.context.t1 == pytest.approx(2.5)


def test_native_adapter_run_honors_nonzero_start_time():
    adapter = OSKAdapter()
    adapter.initialize(
        ModelCompiler().compile(_driven_integrator_model()),
        SimulationConfig(
            solver=SolverType.RK4,
            start_time=0.5,
            stop_time=0.7,
            step_size=0.1,
        ),
    )

    results = adapter.run_simulation()

    assert adapter.context.t == pytest.approx(0.7)
    assert results["statistics"]["finalTime"] == pytest.approx(0.7)
    # Native Sim retains its historical final-report call at the terminal time.
    assert results["signals"][0]["times"] == pytest.approx([0.5, 0.6, 0.7, 0.7])


def test_adapter_reporting_and_state_boundaries_activate_and_restore_context(monkeypatch):
    adapter = OSKAdapter()
    outer = SimContext()
    observed: dict[str, SimContext] = {}

    def probe(name: str, result):
        def call(*args):
            observed[name] = get_active_context()
            return result

        return call

    monkeypatch.setattr(adapter, "_get_analysis_data", probe("analysis", {}))
    monkeypatch.setattr(adapter, "_get_scope_data", probe("scope", []))
    monkeypatch.setattr(adapter, "_get_state", probe("get_state", {}))
    monkeypatch.setattr(adapter, "_set_state", probe("set_state", None))

    with activate_context(outer):
        assert adapter.get_analysis_data() == {}
        assert adapter.get_scope_data() == []
        assert adapter.get_state() == {}
        adapter.set_state({})
        assert get_active_context() is outer

    assert observed == {
        "analysis": adapter.context,
        "scope": adapter.context,
        "get_state": adapter.context,
        "set_state": adapter.context,
    }

    def fail() -> dict:
        assert get_active_context() is adapter.context
        raise RuntimeError("reporting failed")

    monkeypatch.setattr(adapter, "_get_analysis_data", fail)
    with activate_context(outer):
        with pytest.raises(RuntimeError, match="reporting failed"):
            adapter.get_analysis_data()
        assert get_active_context() is outer


@pytest.mark.asyncio
async def test_continuous_runner_honors_nonzero_start_time():
    runner = SimulationRunner(
        _driven_integrator_model(),
        SimulationConfig(
            solver=SolverType.RK4,
            start_time=0.5,
            stop_time=0.7,
            step_size=0.1,
        ),
    )

    await runner.run()

    results = runner.get_results()
    assert runner.status == SimulationStatus.COMPLETED
    assert runner.current_time == pytest.approx(0.7)
    assert runner.context.t == pytest.approx(0.7)
    assert results["statistics"]["finalTime"] == pytest.approx(0.7)
    assert results["signals"][0]["times"] == pytest.approx([0.5, 0.6])


def test_runners_with_different_solvers_can_step_alternately_without_crosstalk():
    euler_step = 0.1
    rk4_step = 0.05
    euler_steps = 6
    rk4_steps = 9
    euler_reference = _run_runner_isolated(SolverType.EULER, euler_step, euler_steps)
    rk4_reference = _run_runner_isolated(SolverType.RK4, rk4_step, rk4_steps)

    euler = SimulationRunner(_driven_integrator_model(), _config(SolverType.EULER, euler_step))
    rk4 = SimulationRunner(_driven_integrator_model(), _config(SolverType.RK4, rk4_step))
    assert euler.initialize_step_mode() is True
    assert rk4.initialize_step_mode() is True

    for index in range(max(euler_steps, rk4_steps)):
        if index < euler_steps:
            assert euler.step_forward()["success"] is True
        if index < rk4_steps:
            assert rk4.step_forward()["success"] is True

    assert _adapter_value(euler._adapter) == pytest.approx(euler_reference)
    assert _adapter_value(rk4._adapter) == pytest.approx(rk4_reference)


@pytest.mark.asyncio
async def test_runners_overlap_past_cooperative_yield_and_match_isolated_results():
    class GatedRunner(SimulationRunner):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.reached_yield = asyncio.Event()
            self.release_yield = asyncio.Event()

        async def _cooperate_after_step(self) -> None:
            self.reached_yield.set()
            await self.release_yield.wait()
            await super()._cooperate_after_step()

    euler_config = SimulationConfig(
        solver=SolverType.EULER,
        step_size=0.1,
        stop_time=11.95,
    )
    rk4_config = SimulationConfig(
        solver=SolverType.RK4,
        step_size=0.01,
        stop_time=1.195,
    )
    euler = GatedRunner(_driven_integrator_model(), euler_config)
    rk4 = GatedRunner(_driven_integrator_model(), rk4_config)

    euler_task = asyncio.create_task(euler.run())
    rk4_task = asyncio.create_task(rk4.run())
    await euler.reached_yield.wait()
    await rk4.reached_yield.wait()

    assert euler.has_live_run
    assert rk4.has_live_run
    assert euler.status == SimulationStatus.RUNNING
    assert rk4.status == SimulationStatus.RUNNING
    assert euler._total_steps == 100
    assert rk4._total_steps == 100
    assert euler.context is not rk4.context
    assert euler.context.method == "Euler"
    assert rk4.context.method == "RK4"

    euler.release_yield.set()
    rk4.release_yield.set()
    await asyncio.gather(euler_task, rk4_task)

    isolated_euler = SimulationRunner(_driven_integrator_model(), euler_config)
    isolated_rk4 = SimulationRunner(_driven_integrator_model(), rk4_config)
    await isolated_euler.run()
    await isolated_rk4.run()

    assert _stable_runner_results(euler) == _stable_runner_results(isolated_euler)
    assert _stable_runner_results(rk4) == _stable_runner_results(isolated_rk4)
    assert euler.context.dtp == pytest.approx(0.1)
    assert rk4.context.dtp == pytest.approx(0.01)


@pytest.mark.asyncio
async def test_pause_acknowledges_committed_boundary_before_step_mode_handoff():
    class BoundaryGatedRunner(SimulationRunner):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.reached_boundary = asyncio.Event()
            self.release_boundary = asyncio.Event()

        async def _cooperate_after_step(self) -> None:
            self.reached_boundary.set()
            await self.release_boundary.wait()
            await super()._cooperate_after_step()

    runner = BoundaryGatedRunner(
        _driven_integrator_model(),
        SimulationConfig(
            solver=SolverType.RK4,
            step_size=0.01,
            stop_time=2.0,
        ),
    )
    run_task = asyncio.create_task(runner.run())
    await runner.reached_boundary.wait()
    assert runner._total_steps == 100
    assert runner.current_time == pytest.approx(1.0)

    pause_task = asyncio.create_task(runner.pause())
    await asyncio.sleep(0)
    assert not pause_task.done()
    runner.release_boundary.set()
    await pause_task

    boundary_time = runner.current_time
    boundary_steps = runner._total_steps
    boundary_results = _stable_runner_results(runner)
    assert boundary_time == pytest.approx(1.0)
    assert runner.status == SimulationStatus.PAUSED
    assert runner.has_live_run

    await runner.pause()
    assert runner.current_time == pytest.approx(boundary_time)
    assert runner._pause_acknowledged.is_set()
    assert await runner.enter_step_mode() is True
    await run_task

    assert not runner.has_live_run
    assert runner._active_operation is None
    assert runner._pending_handoff is None
    assert runner._step_mode is True
    assert runner.status == SimulationStatus.PAUSED
    assert runner.current_time == pytest.approx(boundary_time)
    assert runner._total_steps == boundary_steps
    assert len(runner._state_history) == 1
    assert runner._state_history[0].current_time == pytest.approx(boundary_time)
    assert _stable_runner_results(runner) == boundary_results


@pytest.mark.asyncio
async def test_cancelled_step_handoff_leaves_quiescent_paused_runner():
    class CancelGatedRunner(SimulationRunner):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.reached_boundary = asyncio.Event()
            self.release_boundary = asyncio.Event()
            self.transition_seen = asyncio.Event()
            self.release_transition = asyncio.Event()

        async def _cooperate_after_step(self) -> None:
            self.reached_boundary.set()
            await self.release_boundary.wait()
            await super()._cooperate_after_step()

        async def _wait_while_paused(self) -> None:
            await super()._wait_while_paused()
            if self._transition_requested:
                self.transition_seen.set()
                await self.release_transition.wait()

    runner = CancelGatedRunner(
        _driven_integrator_model(),
        SimulationConfig(solver=SolverType.RK4, step_size=0.01, stop_time=2.0),
    )
    run_task = asyncio.create_task(runner.run())
    await runner.reached_boundary.wait()
    pause_task = asyncio.create_task(runner.pause())
    await asyncio.sleep(0)
    runner.release_boundary.set()
    await pause_task

    enter_task = asyncio.create_task(runner.enter_step_mode())
    await runner.transition_seen.wait()
    enter_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await enter_task
    assert runner._pending_handoff is None

    runner.release_transition.set()
    await run_task

    assert runner._active_operation is None
    assert runner._pending_handoff is None
    assert runner._transition_requested is False
    assert runner._is_paused is True
    assert runner.status == SimulationStatus.PAUSED
    runner.reset()
    assert runner.status == SimulationStatus.IDLE


@pytest.mark.asyncio
async def test_resume_before_pause_boundary_resolves_pause_waiter():
    class BoundaryGatedRunner(SimulationRunner):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.reached_boundary = asyncio.Event()
            self.release_boundary = asyncio.Event()

        async def _cooperate_after_step(self) -> None:
            self.reached_boundary.set()
            await self.release_boundary.wait()
            await super()._cooperate_after_step()

    runner = BoundaryGatedRunner(
        _driven_integrator_model(),
        SimulationConfig(solver=SolverType.EULER, step_size=0.01, stop_time=1.2),
    )
    run_task = asyncio.create_task(runner.run())
    await runner.reached_boundary.wait()

    pause_task = asyncio.create_task(runner.pause())
    await asyncio.sleep(0)
    assert not pause_task.done()
    runner.resume()
    await asyncio.wait_for(pause_task, timeout=0.5)

    runner.release_boundary.set()
    await run_task
    assert runner.status == SimulationStatus.COMPLETED
    assert runner.current_time == pytest.approx(1.2)


def test_native_sim_rebinds_registered_states_from_the_provisional_context():
    block = _NativeProbe()
    provisional_context = block.context

    sim = Sim(dts=[0.1], tmax=0.2, vStage=[[block]])

    assert block.context is sim.context
    assert block.context is not provisional_context
    assert all(state.context is sim.context for state in block.vState)
    assert sim.clock is None
    assert not hasattr(sim.context, "clock")


def test_block_binding_is_idempotent_only_for_the_same_context_and_owner():
    block = _NativeProbe()
    sim = Sim(dts=[0.1], tmax=0.2, vStage=[[block]])

    block.bind_context(sim.context, sim)

    assert block.context is sim.context
    assert block._context_owner is sim
    with pytest.raises(ValueError, match="already owned"):
        block.bind_context(sim.context, object())


def test_direct_block_binding_claims_context_and_rejects_an_owner_split():
    context = SimContext()
    owner = object()
    block = _NativeProbe()

    block.bind_context(context, owner)

    assert context.owner is owner
    assert block._context_owner is owner
    assert block.context is context

    claimed_context = SimContext()
    claimed_context.claim_owner(object())
    unowned_block = _NativeProbe()
    provisional_context = unowned_block.context
    with pytest.raises(ValueError, match="already owned"):
        unowned_block.bind_context(claimed_context, owner)
    assert unowned_block._context_owner is None
    assert unowned_block.context is provisional_context


def test_native_block_cannot_be_reused_by_a_second_simulation():
    block = _NativeProbe()
    first = Sim(dts=[0.1], tmax=0.2, vStage=[[block]])

    with pytest.raises(ValueError, match="already owned"):
        Sim(dts=[0.05], tmax=0.4, vStage=[[block]])

    assert block.context is first.context
    assert block._context_owner is first


def test_native_sim_preflight_failure_does_not_partially_bind_other_blocks():
    owned = _NativeProbe()
    first = Sim(dts=[0.1], tmax=0.2, vStage=[[owned]])
    unowned = _NativeProbe()
    provisional_context = unowned.context

    with pytest.raises(ValueError, match="already owned"):
        Sim(dts=[0.05], tmax=0.4, vStage=[[unowned, owned]])

    assert owned.context is first.context
    assert owned._context_owner is first
    assert unowned.context is provisional_context
    assert unowned._context_owner is None


def test_adapter_owned_blocks_accept_only_the_adapter_context_owner_pair():
    adapter = OSKAdapter()
    adapter.initialize(
        ModelCompiler().compile(_driven_integrator_model()),
        _config(SolverType.RK4, 0.05),
    )
    blocks = list(adapter._osk_blocks.values())

    sim = Sim(
        dts=[0.05],
        tmax=1.0,
        vStage=[blocks],
        context=adapter.context,
        owner=adapter,
    )

    assert sim.context is adapter.context
    assert all(block._context_owner is adapter for block in blocks)
    with pytest.raises(ValueError, match="already owned"):
        Sim(
            dts=[0.05],
            tmax=1.0,
            vStage=[blocks],
            context=adapter.context,
            owner=object(),
        )


def test_adapter_sim_does_not_split_legacy_state_and_sim_facades():
    native, _ = _native_sim("Euler", 0.1, 0.3)
    adapter = OSKAdapter()
    adapter.initialize(
        ModelCompiler().compile(_driven_integrator_model()),
        _config(SolverType.RK4, 0.05),
    )

    adapter.run_simulation()
    State.t = 0.15
    State.ready = 0
    Sim.sample(0.15)

    assert Sim.tmax == native.tmax
    assert native.context.t == pytest.approx(0.15)
    assert native.context.ready == 1
    assert adapter.context.t == pytest.approx(1.0)


def test_first_native_sim_keeps_its_fields_after_a_second_is_constructed():
    first, first_block = _native_sim("Euler", 0.1, 0.3)
    second, _ = _native_sim("Merson", 0.05, 0.2)

    assert Sim.tmax == second.tmax
    first.run()

    assert first.context.method == "Euler"
    assert first.context.t == pytest.approx(0.3)
    assert first_block.observed
    assert all(method == "Euler" for _, method, _, _, _ in first_block.observed)
    assert all(tmax == first.tmax for _, _, tmax, _, _ in first_block.observed)
    assert all(dts is first.dts for _, _, _, dts, _ in first_block.observed)
    assert all(stages is first.vStage for _, _, _, _, stages in first_block.observed)
    assert Sim.tmax == second.tmax


def test_native_sims_run_concurrently_without_context_or_facade_crosstalk():
    barrier = Barrier(2)
    euler, euler_block = _native_sim("Euler", 0.1, 0.3, barrier)
    merson, merson_block = _native_sim("Merson", 0.05, 0.2, barrier)

    with ThreadPoolExecutor(max_workers=2) as executor:
        euler_future = executor.submit(euler.run)
        merson_future = executor.submit(merson.run)
        euler_future.result(timeout=10)
        merson_future.result(timeout=10)

    euler_reference, euler_reference_block = _native_sim("Euler", 0.1, 0.3)
    merson_reference, merson_reference_block = _native_sim("Merson", 0.05, 0.2)
    euler_reference.run()
    merson_reference.run()

    assert euler_block.getOutput() == pytest.approx(euler_reference_block.getOutput())
    assert merson_block.getOutput() == pytest.approx(merson_reference_block.getOutput())
    assert all(method == "Euler" for _, method, _, _, _ in euler_block.observed)
    assert all(method == "Merson" for _, method, _, _, _ in merson_block.observed)
    assert all(tmax == euler.tmax for _, _, tmax, _, _ in euler_block.observed)
    assert all(tmax == merson.tmax for _, _, tmax, _, _ in merson_block.observed)
    assert all(dts is euler.dts for _, _, _, dts, _ in euler_block.observed)
    assert all(dts is merson.dts for _, _, _, dts, _ in merson_block.observed)
    assert all(stages is euler.vStage for _, _, _, _, stages in euler_block.observed)
    assert all(stages is merson.vStage for _, _, _, _, stages in merson_block.observed)
    assert euler_block.facade_checks == (7, 9, 1)
    assert merson_block.facade_checks == (7, 9, 1)


def test_mutable_state_facade_inventory_does_not_grow():
    """Prevent mutable compatibility-facade access from returning to production."""
    backend_root = Path(__file__).resolve().parents[1]
    mutable_fields = {
        "t",
        "t1",
        "dt",
        "dtp",
        "ready",
        "kpass",
        "method",
        "tickfirst",
        "ticklast",
    }
    candidates = [
        *sorted((backend_root / "src/osk/blocks").glob("*.py")),
        backend_root / "src/osk/block.py",
        backend_root / "src/osk/sim.py",
        backend_root / "src/simulation/osk_adapter.py",
        backend_root / "src/simulation/runner.py",
    ]
    actual: Counter[str] = Counter()
    for path in candidates:
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "State"
                and node.attr in mutable_fields
            ):
                actual[path.relative_to(backend_root).as_posix()] += 1

    assert actual == Counter()
