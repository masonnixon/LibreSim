"""Deterministic API regressions for simulation-runner replacement."""

import asyncio
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from src.models.simulation import SimulationStatus
from src.simulation.runner import SimulationRunner


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
            ControlledRunner.created.put_nowait(self)

        async def run(self):
            self.run_entered.set()
            try:
                await self.release.wait()
                await super().run()
            finally:
                self.operation_exited.set()

        async def continue_from_step_mode(self):
            self.continue_entered.set()
            try:
                await self.release.wait()
                await super().continue_from_step_mode()
            finally:
                self.operation_exited.set()

        async def stop_and_wait(self, timeout: float = 5.0) -> bool:
            self.release.set()
            stopped = await super().stop_and_wait(timeout=timeout)
            if stopped:
                await self.operation_exited.wait()
            return stopped

    simulation_routes._runner = None
    simulation_routes._runner_lock = asyncio.Lock()
    monkeypatch.setattr(simulation_routes, "SimulationRunner", ControlledRunner)

    yield ControlledRunner

    simulation_routes._runner = None
    simulation_routes._runner_lock = asyncio.Lock()


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
    assert first_response.status_code == 200
    assert second_response.status_code == 200
    replacement_results = second.get_results()

    simulation_routes._runner = None
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
        has_live_run=True,
        stop_and_wait=AsyncMock(return_value=False),
    )
    simulation_routes._runner = refusing_runner

    response = await async_client.post(
        "/api/simulate/start",
        json=_request(sample_model, simulation_config, "rk4"),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Previous simulation did not stop"
    refusing_runner.stop_and_wait.assert_awaited_once()
