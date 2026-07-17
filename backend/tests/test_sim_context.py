"""FAC-9 regressions for isolation between independent simulations."""

import ast
import asyncio
import math
from collections import Counter
from pathlib import Path

import pytest

from src.models.model import Model
from src.models.simulation import SimulationConfig, SolverType
from src.osk import SimContext, State, activate_context, get_active_context
from src.simulation.compiler import CompiledBlock, CompiledModel, ModelCompiler
from src.simulation.osk_adapter import OSKAdapter
from src.simulation.runner import SimulationRunner


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


def _config(solver: SolverType, step_size: float) -> SimulationConfig:
    return SimulationConfig(solver=solver, step_size=step_size, stop_time=1.0)


def _adapter_value(adapter: OSKAdapter) -> float:
    return float(adapter._osk_blocks["integrator"].getOutput())


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


def _advance_decay(context: SimContext, state: State, start: float) -> None:
    context.begin_step(start, context.dtp)
    for kpass in range(context.pass_count):
        context.enter_stage(kpass)
        state.x[1] = -state.x[0]
        state.propagate()
    context.complete_step()


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


def test_stateful_run_simulation_uses_the_adapter_context():
    adapter = OSKAdapter()
    adapter.initialize(
        ModelCompiler().compile(_driven_integrator_model()),
        _config(SolverType.RK4, 0.05),
    )

    adapter.run_simulation()

    assert adapter.context.t == pytest.approx(1.0)
    assert _adapter_value(adapter) == pytest.approx(1.0 - math.cos(1.0), abs=1e-6)


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


def test_mutable_state_facade_inventory_does_not_grow():
    """Freeze the temporary built-in compatibility surface for later migration."""
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

    assert actual == Counter(
        {
            "src/osk/block.py": 1,
            "src/osk/blocks/continuous.py": 2,
            "src/osk/blocks/discrete.py": 26,
            "src/osk/blocks/nonlinear.py": 3,
            "src/osk/blocks/observers.py": 4,
            "src/osk/blocks/rf.py": 4,
            "src/osk/blocks/sensor_fusion.py": 5,
            "src/osk/blocks/signal_processing.py": 21,
            "src/osk/blocks/sinks.py": 7,
            "src/osk/blocks/sources.py": 26,
            "src/osk/sim.py": 9,
        }
    )
