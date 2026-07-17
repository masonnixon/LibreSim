"""Deterministic API regressions for simulation-runner replacement."""

import asyncio
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from httpx import ASGITransport, AsyncClient

from src.models.simulation import SimulationStatus
from src.simulation.runner import SimulationOperationToken, SimulationRunner
from src.simulation.session_registry import (
    SessionCapacityExceeded,
    SessionRecord,
    SessionRegistry,
)


@pytest.fixture
def controlled_runner(monkeypatch):
    """Gate real runner coroutines with events while preserving their simulation behavior."""
    from src.api.routes import simulation as simulation_routes

    class ControlledRunner(SimulationRunner):
        created: asyncio.Queue["ControlledRunner"] = asyncio.Queue()

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.run_entered = asyncio.Event()
            self.continue_entered = asyncio.Event()
            self.release = asyncio.Event()
            self.operation_exited = asyncio.Event()
            self.stop_entered = asyncio.Event()
            self.allow_stop = asyncio.Event()
            self.allow_stop.set()
            ControlledRunner.created.put_nowait(self)

        async def run(self, token: SimulationOperationToken | None = None):
            self.run_entered.set()
            try:
                await self.release.wait()
                await super().run(token)
            finally:
                self.operation_exited.set()

        async def continue_from_step_mode(
            self,
            token: SimulationOperationToken | None = None,
        ):
            self.continue_entered.set()
            try:
                await self.release.wait()
                await super().continue_from_step_mode(token)
            finally:
                self.operation_exited.set()

        async def stop_and_wait(self, timeout: float = 5.0) -> bool:
            self.stop_entered.set()
            await self.allow_stop.wait()
            self.release.set()
            stopped = await super().stop_and_wait(timeout=timeout)
            if stopped:
                await self.operation_exited.wait()
            return stopped

    simulation_routes._registry = SessionRegistry()
    monkeypatch.setattr(simulation_routes, "SimulationRunner", ControlledRunner)

    yield ControlledRunner

    simulation_routes._registry = SessionRegistry()


@pytest.fixture
async def async_client():
    from src.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client


def _request(sample_model: dict, simulation_config: dict, solver: str) -> dict:
    config = deepcopy(simulation_config)
    config.update({"solver": solver, "stopTime": 1.0, "stepSize": 0.01})
    return {"model": sample_model, "config": config}


def _stable_results(results: dict) -> dict:
    """Ignore wall-clock runtime when comparing isolated and replacement executions."""
    normalized = deepcopy(results)
    normalized["statistics"].pop("executionTime", None)
    return normalized


@pytest.mark.asyncio
async def test_second_start_waits_for_first_and_matches_isolated_run(
    async_client: AsyncClient,
    controlled_runner,
    sample_model,
    simulation_config,
):
    from src.api.routes import simulation as simulation_routes

    first_request = asyncio.create_task(
        async_client.post(
            "/api/simulate/start",
            json=_request(sample_model, simulation_config, "euler"),
        )
    )
    first = await controlled_runner.created.get()
    await first.run_entered.wait()

    second_request = asyncio.create_task(
        async_client.post(
            "/api/simulate/start",
            json=_request(sample_model, simulation_config, "rk4"),
        )
    )
    second = await controlled_runner.created.get()
    await second.run_entered.wait()

    assert first.operation_exited.is_set()
    assert not first.has_live_run
    assert simulation_routes.get_runner() is second
    assert second.has_live_run

    second.release.set()
    first_response, second_response = await asyncio.gather(first_request, second_request)
    await second.operation_exited.wait()
    assert first_response.status_code == 200
    assert second_response.status_code == 200
    replacement_results = second.get_results()

    simulation_routes._registry = SessionRegistry()
    isolated_request = asyncio.create_task(
        async_client.post(
            "/api/simulate/start",
            json=_request(sample_model, simulation_config, "rk4"),
        )
    )
    isolated = await controlled_runner.created.get()
    await isolated.run_entered.wait()
    isolated.release.set()
    isolated_response = await isolated_request
    await isolated.operation_exited.wait()

    assert isolated_response.status_code == 200
    assert _stable_results(replacement_results) == _stable_results(isolated.get_results())


@pytest.mark.asyncio
async def test_idle_but_scheduled_runner_is_stopped_before_replacement(
    async_client: AsyncClient,
    controlled_runner,
    sample_model,
    simulation_config,
):
    first_request = asyncio.create_task(
        async_client.post(
            "/api/simulate/start",
            json=_request(sample_model, simulation_config, "euler"),
        )
    )
    first = await controlled_runner.created.get()
    await first.run_entered.wait()
    first._status = SimulationStatus.IDLE

    second_request = asyncio.create_task(
        async_client.post(
            "/api/simulate/start",
            json=_request(sample_model, simulation_config, "rk4"),
        )
    )
    second = await controlled_runner.created.get()
    await second.run_entered.wait()

    assert first.operation_exited.is_set()
    assert not first.has_live_run
    assert second.has_live_run

    second.release.set()
    responses = await asyncio.gather(first_request, second_request)
    assert [response.status_code for response in responses] == [200, 200]


@pytest.mark.asyncio
async def test_start_and_step_init_are_serialized(
    async_client: AsyncClient,
    controlled_runner,
    sample_model,
    simulation_config,
):
    from src.api.routes import simulation as simulation_routes

    start_request = asyncio.create_task(
        async_client.post(
            "/api/simulate/start",
            json=_request(sample_model, simulation_config, "euler"),
        )
    )
    running = await controlled_runner.created.get()
    await running.run_entered.wait()

    step_response = await async_client.post(
        "/api/simulate/step/init",
        json=_request(sample_model, simulation_config, "rk4"),
    )
    step_runner = await controlled_runner.created.get()
    start_response = await start_request

    assert start_response.status_code == 200
    assert step_response.status_code == 200
    assert running.operation_exited.is_set()
    assert not running.has_live_run
    assert simulation_routes.get_runner() is step_runner
    assert step_runner.status == SimulationStatus.PAUSED


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("path", "payload"),
    [
        ("/api/simulate/reset", None),
        ("/api/simulate/step/forward", {"numSteps": 1}),
    ],
)
async def test_live_run_rejects_same_runner_mutations(
    async_client: AsyncClient,
    controlled_runner,
    sample_model,
    simulation_config,
    path: str,
    payload: dict | None,
):
    start_request = asyncio.create_task(
        async_client.post(
            "/api/simulate/start",
            json=_request(sample_model, simulation_config, "euler"),
        )
    )
    running = await controlled_runner.created.get()
    await running.run_entered.wait()
    time_before = running.current_time

    response = await async_client.post(path, json=payload)

    assert response.status_code == 409
    assert response.json()["detail"] == "Simulation is already running"
    assert running.current_time == time_before
    assert running.has_live_run
    assert not running.operation_exited.is_set()

    running.release.set()
    assert (await start_request).status_code == 200


@pytest.mark.asyncio
async def test_unpaused_live_run_rejects_step_mode_entry(
    async_client: AsyncClient,
    controlled_runner,
    sample_model,
    simulation_config,
):
    start_request = asyncio.create_task(
        async_client.post(
            "/api/simulate/start",
            json=_request(sample_model, simulation_config, "euler"),
        )
    )
    running = await controlled_runner.created.get()
    await running.run_entered.wait()

    response = await async_client.post("/api/simulate/step/enter")

    assert response.status_code == 409
    assert response.json()["detail"] == "Simulation is already running"
    assert running.has_live_run

    running.release.set()
    assert (await start_request).status_code == 200


@pytest.mark.asyncio
async def test_step_continue_is_tracked_until_replacement_stops_it(
    async_client: AsyncClient,
    controlled_runner,
    sample_model,
    simulation_config,
):
    from src.api.routes import simulation as simulation_routes

    init_response = await async_client.post(
        "/api/simulate/step/init",
        json=_request(sample_model, simulation_config, "euler"),
    )
    continuing = await controlled_runner.created.get()
    assert init_response.status_code == 200

    continue_request = asyncio.create_task(async_client.post("/api/simulate/step/continue"))
    await continuing.continue_entered.wait()
    assert continuing.has_live_run

    replacement_request = asyncio.create_task(
        async_client.post(
            "/api/simulate/start",
            json=_request(sample_model, simulation_config, "rk4"),
        )
    )
    replacement = await controlled_runner.created.get()
    await replacement.run_entered.wait()

    assert continuing.operation_exited.is_set()
    assert not continuing.has_live_run
    assert simulation_routes.get_runner() is replacement
    assert replacement.has_live_run

    replacement.release.set()
    continue_response, replacement_response = await asyncio.gather(
        continue_request, replacement_request
    )
    assert continue_response.status_code == 200
    assert replacement_response.status_code == 200


@pytest.mark.asyncio
async def test_second_step_continue_is_rejected_while_first_is_live(
    async_client: AsyncClient,
    controlled_runner,
    sample_model,
    simulation_config,
):
    init_response = await async_client.post(
        "/api/simulate/step/init",
        json=_request(sample_model, simulation_config, "euler"),
    )
    continuing = await controlled_runner.created.get()
    assert init_response.status_code == 200

    first_continue = asyncio.create_task(async_client.post("/api/simulate/step/continue"))
    await continuing.continue_entered.wait()

    second_continue = await async_client.post("/api/simulate/step/continue")
    assert second_continue.status_code == 409
    assert second_continue.json()["detail"] == "Simulation is already running"

    continuing.release.set()
    assert (await first_continue).status_code == 200


@pytest.mark.asyncio
async def test_step_continue_is_reserved_before_background_task_starts(
    async_client: AsyncClient,
    controlled_runner,
    sample_model,
    simulation_config,
):
    from src.api.routes import simulation as simulation_routes

    init_response = await async_client.post(
        "/api/simulate/step/init",
        json=_request(sample_model, simulation_config, "euler"),
    )
    runner = await controlled_runner.created.get()
    assert init_response.status_code == 200

    response = await async_client.post("/api/simulate/step/continue")
    assert response.status_code == 200
    assert runner.has_live_run
    record = simulation_routes._registry.get_record(runner.session_id)
    assert record is not None
    assert record.task is not None
    assert record.operation_token is runner._active_operation

    conflict = await async_client.post("/api/simulate/step/continue")
    assert conflict.status_code == 409

    runner.release.set()
    await record.task
    assert not runner.has_live_run


@pytest.mark.asyncio
async def test_step_continue_rejects_runner_outside_step_mode(
    async_client: AsyncClient,
    controlled_runner,
    sample_model,
    simulation_config,
):
    init_response = await async_client.post(
        "/api/simulate/step/init",
        json=_request(sample_model, simulation_config, "euler"),
    )
    runner = await controlled_runner.created.get()
    assert init_response.status_code == 200

    runner._step_mode = False
    response = await async_client.post("/api/simulate/step/continue")

    assert response.status_code == 400
    assert response.json()["detail"] == "Simulation is not in step mode"


@pytest.mark.asyncio
async def test_start_preserves_replacement_timeout_conflict(
    async_client: AsyncClient,
    controlled_runner,
    sample_model,
    simulation_config,
):
    from src.api.routes import simulation as simulation_routes

    refusing_runner = SimpleNamespace(
        session_id="refusing",
        stop=Mock(),
        has_live_run=True,
        stop_and_wait=AsyncMock(return_value=False),
    )
    record = SessionRecord(runner=refusing_runner, sequence=1)
    simulation_routes._registry._sessions[refusing_runner.session_id] = record
    simulation_routes._registry._current_session_id = refusing_runner.session_id

    response = await async_client.post(
        "/api/simulate/start",
        json=_request(sample_model, simulation_config, "rk4"),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Previous simulation did not stop"
    refusing_runner.stop.assert_called_once()
    refusing_runner.stop_and_wait.assert_awaited_once()


@pytest.mark.asyncio
async def test_retained_sessions_are_independently_addressable(
    async_client: AsyncClient,
    controlled_runner,
    sample_model,
    simulation_config,
):
    first_response = await async_client.post(
        "/api/simulate/start",
        json={
            **_request(sample_model, simulation_config, "euler"),
            "replaceCurrent": False,
        },
    )
    first = await controlled_runner.created.get()
    await first.run_entered.wait()

    second_response = await async_client.post(
        "/api/simulate/start",
        json={
            **_request(sample_model, simulation_config, "rk4"),
            "replaceCurrent": False,
        },
    )
    second = await controlled_runner.created.get()
    await second.run_entered.wait()

    first_id = first_response.json()["sessionId"]
    second_id = second_response.json()["sessionId"]
    assert first_id != second_id
    assert first_id == first.session_id
    assert second_id == second.session_id

    current_status = await async_client.get("/api/simulate/status")
    first_status = await async_client.get(
        "/api/simulate/status", params={"sessionId": first_id}
    )
    first_results = await async_client.get(
        "/api/simulate/results", params={"sessionId": first_id}
    )
    assert current_status.json()["sessionId"] == second_id
    assert first_status.json()["sessionId"] == first_id
    assert first_results.json()["sessionId"] == first_id

    stop_first = await async_client.post(
        "/api/simulate/stop", params={"sessionId": first_id}
    )
    assert stop_first.status_code == 200
    assert stop_first.json()["sessionId"] == first_id
    assert first._should_stop is True
    assert second._should_stop is False
    assert second.has_live_run

    first.release.set()
    second.release.set()
    await asyncio.gather(first.operation_exited.wait(), second.operation_exited.wait())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("get", "/api/simulate/status", None),
        ("get", "/api/simulate/results", None),
        ("post", "/api/simulate/stop", None),
        ("post", "/api/simulate/reset", None),
        ("post", "/api/simulate/pause", None),
        ("post", "/api/simulate/resume", None),
        ("post", "/api/simulate/step/enter", None),
        ("post", "/api/simulate/step/forward", {"numSteps": 1}),
        ("post", "/api/simulate/step/backward", {"numSteps": 1}),
        ("post", "/api/simulate/step/reset", None),
        ("post", "/api/simulate/step/continue", None),
        ("delete", "/api/simulate/sessions/missing", None),
    ],
)
async def test_unknown_explicit_session_returns_404(
    async_client: AsyncClient,
    method: str,
    path: str,
    payload: dict | None,
):
    kwargs: dict = {}
    if not path.endswith("/missing"):
        kwargs["params"] = {"sessionId": "missing"}
    if payload is not None:
        kwargs["json"] = payload
    response = await async_client.request(method, path, **kwargs)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_default_replacement_removes_only_current_retained_session(
    async_client: AsyncClient,
    controlled_runner,
    sample_model,
    simulation_config,
):
    retained_response = await async_client.post(
        "/api/simulate/start",
        json={
            **_request(sample_model, simulation_config, "euler"),
            "replaceCurrent": False,
        },
    )
    retained = await controlled_runner.created.get()
    await retained.run_entered.wait()

    current_response = await async_client.post(
        "/api/simulate/start",
        json={
            **_request(sample_model, simulation_config, "rk4"),
            "replaceCurrent": False,
        },
    )
    replaced = await controlled_runner.created.get()
    await replaced.run_entered.wait()

    replacement_response = await async_client.post(
        "/api/simulate/start",
        json=_request(sample_model, simulation_config, "euler"),
    )
    replacement = await controlled_runner.created.get()
    await replacement.run_entered.wait()

    retained_id = retained_response.json()["sessionId"]
    replaced_id = current_response.json()["sessionId"]
    replacement_id = replacement_response.json()["sessionId"]
    assert (await async_client.get(
        "/api/simulate/status", params={"sessionId": retained_id}
    )).status_code == 200
    assert (await async_client.get(
        "/api/simulate/status", params={"sessionId": replaced_id}
    )).status_code == 404
    assert (await async_client.get("/api/simulate/status")).json()["sessionId"] == replacement_id
    assert retained.has_live_run
    assert not replaced.has_live_run

    retained.release.set()
    replacement.release.set()
    await asyncio.gather(retained.operation_exited.wait(), replacement.operation_exited.wait())


@pytest.mark.asyncio
async def test_replacement_wait_does_not_block_coexistence_installation(
    async_client: AsyncClient,
    controlled_runner,
    sample_model,
    simulation_config,
):
    first_response = await async_client.post(
        "/api/simulate/start",
        json={
            **_request(sample_model, simulation_config, "euler"),
            "replaceCurrent": False,
        },
    )
    first = await controlled_runner.created.get()
    await first.run_entered.wait()
    first.allow_stop.clear()

    replacement_request = asyncio.create_task(
        async_client.post(
            "/api/simulate/start",
            json=_request(sample_model, simulation_config, "rk4"),
        )
    )
    replacement = await controlled_runner.created.get()
    await first.stop_entered.wait()

    coexist_response = await async_client.post(
        "/api/simulate/start",
        json={
            **_request(sample_model, simulation_config, "euler"),
            "replaceCurrent": False,
        },
    )
    coexist = await controlled_runner.created.get()
    await coexist.run_entered.wait()
    assert coexist_response.status_code == 200

    first.allow_stop.set()
    replacement_response = await replacement_request
    await replacement.run_entered.wait()
    assert replacement_response.status_code == 200
    assert (await async_client.get(
        "/api/simulate/status",
        params={"sessionId": first_response.json()["sessionId"]},
    )).status_code == 404
    assert (await async_client.get(
        "/api/simulate/status",
        params={"sessionId": coexist_response.json()["sessionId"]},
    )).status_code == 200
    assert (await async_client.get("/api/simulate/status")).json()["sessionId"] == replacement.session_id

    coexist.release.set()
    replacement.release.set()
    await asyncio.gather(coexist.operation_exited.wait(), replacement.operation_exited.wait())


@pytest.mark.asyncio
async def test_deletion_tombstone_rejects_targeting_and_promotes_latest_peer(
    async_client: AsyncClient,
    controlled_runner,
    sample_model,
    simulation_config,
):
    first_response = await async_client.post(
        "/api/simulate/start",
        json={
            **_request(sample_model, simulation_config, "euler"),
            "replaceCurrent": False,
        },
    )
    first = await controlled_runner.created.get()
    await first.run_entered.wait()
    second_response = await async_client.post(
        "/api/simulate/start",
        json={
            **_request(sample_model, simulation_config, "rk4"),
            "replaceCurrent": False,
        },
    )
    second = await controlled_runner.created.get()
    await second.run_entered.wait()
    second.allow_stop.clear()

    second_id = second_response.json()["sessionId"]
    deletion = asyncio.create_task(
        async_client.delete(f"/api/simulate/sessions/{second_id}")
    )
    await second.stop_entered.wait()
    tombstoned = await async_client.get(
        "/api/simulate/status", params={"sessionId": second_id}
    )
    assert tombstoned.status_code == 409

    second.allow_stop.set()
    deleted = await deletion
    assert deleted.status_code == 200
    assert (await async_client.get(
        "/api/simulate/status", params={"sessionId": second_id}
    )).status_code == 404
    assert (await async_client.get("/api/simulate/status")).json()["sessionId"] == first_response.json()["sessionId"]
    assert first.has_live_run

    first.release.set()
    await first.operation_exited.wait()


@pytest.mark.asyncio
async def test_capacity_never_evicts_live_sessions_and_prunes_oldest_terminal(
    async_client: AsyncClient,
    controlled_runner,
    sample_model,
    simulation_config,
):
    from src.api.routes import simulation as simulation_routes

    simulation_routes._registry = SessionRegistry(max_sessions=2)
    responses = []
    runners = []
    for solver in ("euler", "rk4"):
        responses.append(
            await async_client.post(
                "/api/simulate/start",
                json={
                    **_request(sample_model, simulation_config, solver),
                    "replaceCurrent": False,
                },
            )
        )
        runners.append(await controlled_runner.created.get())
        await runners[-1].run_entered.wait()

    rejected = await async_client.post(
        "/api/simulate/start",
        json={
            **_request(sample_model, simulation_config, "euler"),
            "replaceCurrent": False,
        },
    )
    rejected_runner = await controlled_runner.created.get()
    assert rejected.status_code == 429
    assert not rejected_runner.has_live_run
    assert all(runner.has_live_run for runner in runners)
    assert simulation_routes._registry.session_count == 2

    runners[0].release.set()
    await runners[0].operation_exited.wait()
    admitted = await async_client.post(
        "/api/simulate/start",
        json={
            **_request(sample_model, simulation_config, "euler"),
            "replaceCurrent": False,
        },
    )
    admitted_runner = await controlled_runner.created.get()
    await admitted_runner.run_entered.wait()
    assert admitted.status_code == 200
    assert simulation_routes._registry.session_count == 2
    assert (await async_client.get(
        "/api/simulate/status",
        params={"sessionId": responses[0].json()["sessionId"]},
    )).status_code == 404
    assert runners[1].has_live_run

    runners[1].release.set()
    admitted_runner.release.set()
    await asyncio.gather(
        runners[1].operation_exited.wait(),
        admitted_runner.operation_exited.wait(),
    )


@pytest.mark.asyncio
async def test_cancelled_owned_task_releases_unadopted_runner_token(
    controlled_runner,
    sample_model,
    simulation_config,
):
    from src.models.model import Model
    from src.models.simulation import SimulationConfig

    registry = SessionRegistry()
    runner = controlled_runner(Model(**sample_model), SimulationConfig(**simulation_config))
    entered = asyncio.Event()

    async def operation(token: SimulationOperationToken) -> None:
        entered.set()
        await runner.run(token)

    record = await registry.install(
        runner,
        replace_current=False,
        run_operation=operation,
    )
    assert record.task is not None
    assert not entered.is_set()
    record.task.cancel()
    await asyncio.gather(record.task, return_exceptions=True)
    assert not entered.is_set()
    assert not runner.has_live_run
    assert record.operation_token is not None
    assert record.operation_token.finished.is_set()


@pytest.mark.asyncio
async def test_targeted_step_continuation_conflicts_only_with_same_session(
    async_client: AsyncClient,
    controlled_runner,
    sample_model,
    simulation_config,
):
    first_response = await async_client.post(
        "/api/simulate/step/init",
        json={
            **_request(sample_model, simulation_config, "euler"),
            "replaceCurrent": False,
        },
    )
    first = await controlled_runner.created.get()
    second_response = await async_client.post(
        "/api/simulate/step/init",
        json={
            **_request(sample_model, simulation_config, "rk4"),
            "replaceCurrent": False,
        },
    )
    second = await controlled_runner.created.get()
    first_id = first_response.json()["sessionId"]
    second_id = second_response.json()["sessionId"]

    first_step = await async_client.post(
        "/api/simulate/step/forward",
        params={"sessionId": first_id},
        json={"numSteps": 1},
    )
    assert first_step.status_code == 200
    assert first_step.json()["sessionId"] == first_id
    assert first.current_time > first.config.start_time
    assert second.current_time == second.config.start_time

    continued = await async_client.post(
        "/api/simulate/step/continue", params={"sessionId": first_id}
    )
    assert continued.status_code == 200
    await first.continue_entered.wait()
    conflict = await async_client.post(
        "/api/simulate/reset", params={"sessionId": first_id}
    )
    peer_step = await async_client.post(
        "/api/simulate/step/forward",
        params={"sessionId": second_id},
        json={"numSteps": 1},
    )
    assert conflict.status_code == 409
    assert peer_step.status_code == 200
    assert peer_step.json()["sessionId"] == second_id

    first.release.set()
    await first.operation_exited.wait()


@pytest.mark.asyncio
async def test_failed_step_initialization_remains_current_and_addressable(
    async_client: AsyncClient,
    controlled_runner,
    monkeypatch,
    sample_model,
    simulation_config,
):
    def fail_initialization(runner: SimulationRunner) -> bool:
        runner._status = SimulationStatus.ERROR
        runner._error_message = "deliberate initialization failure"
        return False

    monkeypatch.setattr(controlled_runner, "initialize_step_mode", fail_initialization)
    response = await async_client.post(
        "/api/simulate/step/init",
        json={
            **_request(sample_model, simulation_config, "euler"),
            "replaceCurrent": False,
        },
    )
    runner = await controlled_runner.created.get()
    assert response.status_code == 500

    targeted = await async_client.get(
        "/api/simulate/status", params={"sessionId": runner.session_id}
    )
    current = await async_client.get("/api/simulate/status")
    assert targeted.status_code == 200
    assert targeted.json()["status"] == "error"
    assert targeted.json()["sessionId"] == runner.session_id
    assert current.json()["sessionId"] == runner.session_id


@pytest.mark.asyncio
async def test_concurrent_capacity_creations_share_one_atomic_prune_slot(
    controlled_runner,
    sample_model,
    simulation_config,
):
    from src.models.model import Model
    from src.models.simulation import SimulationConfig

    model = Model(**sample_model)
    config = SimulationConfig(**simulation_config)
    registry = SessionRegistry(max_sessions=2)
    terminal = controlled_runner(model, config)
    await registry.install(terminal, replace_current=False)
    live = controlled_runner(model, config)
    live_record = await registry.install(
        live,
        replace_current=False,
        run_operation=live.run,
    )
    await live.run_entered.wait()

    candidates = [controlled_runner(model, config), controlled_runner(model, config)]
    results = await asyncio.gather(
        *(
            registry.install(
                candidate,
                replace_current=False,
                run_operation=candidate.run,
            )
            for candidate in candidates
        ),
        return_exceptions=True,
    )
    admitted = [result for result in results if isinstance(result, SessionRecord)]
    rejected = [
        result for result in results if isinstance(result, SessionCapacityExceeded)
    ]
    assert len(admitted) == 1
    assert len(rejected) == 1
    assert registry.session_count == 2
    assert registry.get_record(terminal.session_id) is None
    assert registry.get_record(live.session_id) is live_record

    admitted_runner = admitted[0].runner
    await admitted_runner.run_entered.wait()
    live.release.set()
    admitted_runner.release.set()
    assert live_record.task is not None
    assert admitted[0].task is not None
    await asyncio.gather(live_record.task, admitted[0].task)
