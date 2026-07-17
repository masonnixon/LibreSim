"""Simulation control API routes."""

import traceback
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, NoReturn

from fastapi import APIRouter, HTTPException, Query

from ...config import settings
from ...models.model import Model
from ...models.simulation import SimulationConfig
from ...simulation.runner import (
    SimulationOperationConflict,
    SimulationOperationToken,
    SimulationRunner,
)
from ...simulation.session_registry import (
    SessionCapacityExceeded,
    SessionNotFound,
    SessionRecord,
    SessionRegistry,
    SessionStopFailed,
    SessionUnavailable,
)

router = APIRouter()

print("Simulation router loaded successfully")


@router.get("/test")
async def test_endpoint() -> dict[str, str]:
    """Simple test endpoint."""
    return {"status": "ok", "message": "Simulation API is working"}


# Process-local simulation sessions. Multi-worker deployments require sticky routing.
_registry = SessionRegistry(settings.max_retained_simulation_sessions)


async def _install_runner(
    runner: SimulationRunner,
    *,
    scheduled: bool,
    replace_current: bool = True,
) -> SimulationOperationToken | None:
    """Install one runner with legacy replacement behavior by default."""
    try:
        record = await _registry.install(
            runner,
            replace_current=replace_current,
            run_operation=runner.run if scheduled else None,
        )
    except SessionStopFailed as exc:
        raise HTTPException(status_code=409, detail="Previous simulation did not stop") from exc
    except SessionCapacityExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    return record.operation_token


def _raise_operation_conflict(exc: SimulationOperationConflict) -> NoReturn:
    """Translate runner-local ownership conflicts into stable API responses."""
    raise HTTPException(status_code=409, detail="Simulation is already running") from exc


def get_runner() -> SimulationRunner | None:
    """Get the current simulation runner."""
    return _registry.current_runner


async def shutdown_sessions() -> None:
    """Quiesce all process-local sessions during application shutdown."""
    await _registry.shutdown()


def _replace_current(request: dict[str, Any]) -> bool:
    value = request.get("replaceCurrent", True)
    if not isinstance(value, bool):
        raise HTTPException(status_code=400, detail="replaceCurrent must be a boolean")
    return value


@asynccontextmanager
async def _lease_record(session_id: str | None) -> AsyncIterator[SessionRecord | None]:
    try:
        async with _registry.lease(session_id) as record:
            yield record
    except SessionNotFound as exc:
        raise HTTPException(status_code=404, detail="Simulation session not found") from exc
    except SessionUnavailable as exc:
        raise HTTPException(status_code=409, detail="Simulation session is being removed") from exc


def _with_session(result: dict[str, Any], runner: SimulationRunner) -> dict[str, Any]:
    return {**result, "sessionId": runner.session_id}


@router.post("/start")
async def start_simulation(
    request: dict[str, Any],
) -> dict[str, str]:
    """Start a simulation."""
    model_data = request.get("model")
    config_data = request.get("config", {})
    replace_current = _replace_current(request)

    if not model_data:
        raise HTTPException(status_code=400, detail="model is required")

    try:
        # Parse the model from request body
        model = Model(**model_data)
    except Exception as e:
        print(f"Model parsing error: {e}")
        print(f"Model data: {model_data}")
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Invalid model data: {str(e)}")

    # Basic validation
    if not model.blocks:
        raise HTTPException(status_code=400, detail="Model has no blocks")

    try:
        # Create simulation config
        config = SimulationConfig(**config_data)
    except Exception as e:
        print(f"Config parsing error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Invalid config data: {str(e)}")

    try:
        # Create and start runner
        runner = SimulationRunner(model, config)
        token = await _install_runner(
            runner,
            scheduled=True,
            replace_current=replace_current,
        )
        assert token is not None
        session_id = runner.session_id

        return {"sessionId": session_id}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Runner creation error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create simulation: {str(e)}")


@router.post("/stop")
async def stop_simulation(
    session_id: str | None = Query(default=None, alias="sessionId"),
) -> dict[str, str]:
    """Stop the current simulation."""
    async with _lease_record(session_id) as record:
        if record is None:
            raise HTTPException(status_code=400, detail="No simulation running")
        record.runner.stop()
        return {
            "message": "Simulation stopped",
            "sessionId": record.runner.session_id,
        }


@router.post("/reset")
async def reset_simulation(
    session_id: str | None = Query(default=None, alias="sessionId"),
) -> dict[str, Any]:
    """Reset the simulation to initial state, ready to run again.

    This can be called after a simulation completes, pauses, or in step mode.
    It resets all state to initial values while preserving the compiled model.
    """
    async with _lease_record(session_id) as record:
        if record is None:
            raise HTTPException(status_code=400, detail="No simulation available")
        runner = record.runner
        try:
            runner.reset()
        except SimulationOperationConflict as exc:
            _raise_operation_conflict(exc)
        return _with_session(
            {
                "success": True,
                "message": "Simulation reset",
                "currentTime": runner.current_time,
                "progress": runner.progress,
                "status": runner.status.value,
            },
            runner,
        )


@router.post("/pause")
async def pause_simulation(
    session_id: str | None = Query(default=None, alias="sessionId"),
) -> dict[str, str]:
    """Pause the current simulation."""
    async with _lease_record(session_id) as record:
        if record is None:
            raise HTTPException(status_code=400, detail="No simulation running")
        await record.runner.pause()
        return {
            "message": "Simulation paused",
            "sessionId": record.runner.session_id,
        }


@router.post("/resume")
async def resume_simulation(
    session_id: str | None = Query(default=None, alias="sessionId"),
) -> dict[str, str]:
    """Resume a paused simulation."""
    async with _lease_record(session_id) as record:
        if record is None:
            raise HTTPException(status_code=400, detail="No simulation running")
        record.runner.resume()
        return {
            "message": "Simulation resumed",
            "sessionId": record.runner.session_id,
        }


@router.get("/status")
async def get_simulation_status(
    session_id: str | None = Query(default=None, alias="sessionId"),
) -> dict[str, Any]:
    """Get current simulation status."""
    async with _lease_record(session_id) as record:
        if record is None:
            return {"status": "idle", "progress": 0}
        runner = record.runner
        result = {
            "status": runner.status.value,
            "progress": runner.progress,
            "currentTime": runner.current_time,
            "sessionId": runner.session_id,
        }
        if runner.error_message:
            result["error"] = runner.error_message
        return result


@router.get("/results")
async def get_simulation_results(
    session_id: str | None = Query(default=None, alias="sessionId"),
) -> dict[str, Any]:
    """Get simulation results."""
    async with _lease_record(session_id) as record:
        if record is None:
            raise HTTPException(status_code=400, detail="No simulation available")
        return _with_session(record.runner.get_results(), record.runner)


@router.post("/step/init")
async def init_step_mode(request: dict[str, Any]) -> dict[str, Any]:
    """Initialize step mode simulation (compile model, ready for stepping)."""
    model_data = request.get("model")
    config_data = request.get("config", {})
    replace_current = _replace_current(request)

    if not model_data:
        raise HTTPException(status_code=400, detail="model is required")

    try:
        model = Model(**model_data)
    except Exception as e:
        print(f"Model parsing error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Invalid model data: {str(e)}")

    try:
        config = SimulationConfig(**config_data)
    except Exception as e:
        print(f"Config parsing error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Invalid config data: {str(e)}")

    try:
        runner = SimulationRunner(model, config)
        await _install_runner(
            runner,
            scheduled=False,
            replace_current=replace_current,
        )
        success = runner.initialize_step_mode()

        if not success:
            raise HTTPException(
                status_code=500, detail=runner.error_message or "Failed to initialize step mode"
            )

        return {
            "success": True,
            "sessionId": runner.session_id,
            "currentTime": runner.current_time,
            "status": runner.status.value,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Step mode init error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to initialize step mode: {str(e)}")


@router.post("/step/enter")
async def enter_step_mode(
    session_id: str | None = Query(default=None, alias="sessionId"),
) -> dict[str, Any]:
    """Enter step mode from a paused continuous simulation.

    This preserves the current simulation state and time position,
    unlike /step/init which reinitializes from the start.
    """
    async with _lease_record(session_id) as record:
        if record is None:
            raise HTTPException(
                status_code=400,
                detail="No simulation running. Use /step/init first.",
            )
        try:
            runner = record.runner
            success = await runner.enter_step_mode()

            if not success:
                raise HTTPException(
                    status_code=500,
                    detail=runner.error_message or "Failed to enter step mode",
                )

            return _with_session(
                {
                    "success": True,
                    "currentTime": runner.current_time,
                    "progress": runner.progress,
                    "status": runner.status.value,
                    "historySize": 1,
                },
                runner,
            )
        except SimulationOperationConflict as exc:
            _raise_operation_conflict(exc)
        except HTTPException:
            raise
        except Exception as e:
            print(f"Enter step mode error: {e}")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Failed to enter step mode: {str(e)}")


@router.post("/step/forward")
async def step_forward(
    request: dict[str, Any] | None = None,
    session_id: str | None = Query(default=None, alias="sessionId"),
) -> dict[str, Any]:
    """Execute one or more simulation steps forward."""
    return await _step_forward(request, session_id)


async def _step_forward(
    request: dict[str, Any] | None,
    session_id: str | None,
) -> dict[str, Any]:
    async with _lease_record(session_id) as record:
        if record is None:
            raise HTTPException(
                status_code=400,
                detail="No simulation initialized. Call /step/init first.",
            )
        num_steps = request.get("numSteps", 1) if request else 1
        runner = record.runner
        try:
            result = runner.step_forward(num_steps)
        except SimulationOperationConflict as exc:
            _raise_operation_conflict(exc)
        result["status"] = runner.status.value
        return _with_session(result, runner)


@router.post("/step/backward")
async def step_backward(
    request: dict[str, Any] | None = None,
    session_id: str | None = Query(default=None, alias="sessionId"),
) -> dict[str, Any]:
    """Step backward by restoring previous state."""
    async with _lease_record(session_id) as record:
        if record is None:
            raise HTTPException(
                status_code=400,
                detail="No simulation initialized. Call /step/init first.",
            )
        num_steps = request.get("numSteps", 1) if request else 1
        runner = record.runner
        try:
            result = runner.step_backward(num_steps)
        except SimulationOperationConflict as exc:
            _raise_operation_conflict(exc)
        result["status"] = runner.status.value
        return _with_session(result, runner)


@router.post("/step/reset")
async def reset_step_mode(
    session_id: str | None = Query(default=None, alias="sessionId"),
) -> dict[str, Any]:
    """Reset step mode simulation to start time."""
    async with _lease_record(session_id) as record:
        if record is None:
            raise HTTPException(status_code=400, detail="No simulation initialized")
        runner = record.runner
        try:
            runner.reset_step_mode()
        except SimulationOperationConflict as exc:
            _raise_operation_conflict(exc)

        return _with_session(
            {
                "success": True,
                "currentTime": runner.current_time,
                "status": runner.status.value,
            },
            runner,
        )


@router.post("/step/continue")
async def continue_from_step(
    session_id: str | None = Query(default=None, alias="sessionId"),
) -> dict[str, Any]:
    """Continue running simulation from current step mode position."""
    async with _lease_record(session_id) as record:
        if record is None:
            raise HTTPException(status_code=400, detail="No simulation initialized")
        runner = record.runner
        try:
            token = runner.schedule_continue()
            await _registry.schedule(record, token, runner.continue_from_step_mode)
        except SimulationOperationConflict as exc:
            _raise_operation_conflict(exc)
        except SessionUnavailable as exc:
            raise HTTPException(
                status_code=409,
                detail="Simulation session is being removed",
            ) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return _with_session(
            {
                "success": True,
                "currentTime": runner.current_time,
                "status": "running",
            },
            runner,
        )


@router.delete("/sessions/{session_id}")
async def delete_simulation_session(session_id: str) -> dict[str, str]:
    """Stop and discard one retained simulation session."""
    try:
        await _registry.delete(session_id)
    except SessionNotFound as exc:
        raise HTTPException(status_code=404, detail="Simulation session not found") from exc
    except SessionUnavailable as exc:
        raise HTTPException(status_code=409, detail="Simulation session is being removed") from exc
    except SessionStopFailed as exc:
        raise HTTPException(status_code=409, detail="Simulation did not stop") from exc
    return {"message": "Simulation session deleted", "sessionId": session_id}


@router.post("/debug")
async def debug_simulation(request: dict[str, Any]) -> dict[str, Any]:
    """Debug endpoint to test model parsing."""
    model_data = request.get("model")
    config_data = request.get("config", {})

    result: dict[str, Any] = {
        "model_received": model_data is not None,
        "config_received": config_data is not None,
    }

    if model_data:
        result["model_keys"] = (
            list(model_data.keys()) if isinstance(model_data, dict) else "not a dict"
        )
        result["blocks_count"] = (
            len(model_data.get("blocks", [])) if isinstance(model_data, dict) else 0
        )

        # Try to parse model
        try:
            model = Model(**model_data)
            result["model_parsed"] = True
            result["model_block_count"] = len(model.blocks)
        except Exception as e:
            result["model_parsed"] = False
            result["model_error"] = str(e)
            traceback.print_exc()

    if config_data:
        try:
            config = SimulationConfig(**config_data)
            result["config_parsed"] = True
        except Exception as e:
            result["config_parsed"] = False
            result["config_error"] = str(e)
            traceback.print_exc()

    # Try to create runner
    if result.get("model_parsed") and result.get("config_parsed"):
        try:
            SimulationRunner(model, config)
            result["runner_created"] = True
        except Exception as e:
            result["runner_created"] = False
            result["runner_error"] = str(e)
            traceback.print_exc()

    return result
