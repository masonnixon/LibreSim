"""Simulation control API routes."""

import asyncio
import traceback
from typing import Any, NoReturn

from fastapi import APIRouter, BackgroundTasks, HTTPException

from ...models.model import Model
from ...models.simulation import SimulationConfig
from ...simulation.runner import (
    SimulationOperationConflict,
    SimulationOperationToken,
    SimulationRunner,
)

router = APIRouter()

print("Simulation router loaded successfully")


@router.get("/test")
async def test_endpoint() -> dict[str, str]:
    """Simple test endpoint."""
    return {"status": "ok", "message": "Simulation API is working"}


# Global simulation runner instance (single-user for now)
_runner: SimulationRunner | None = None
_runner_lock = asyncio.Lock()


async def _install_runner(
    runner: SimulationRunner,
    *,
    scheduled: bool,
) -> SimulationOperationToken | None:
    """Stop any live run and atomically install its replacement."""
    global _runner

    async with _runner_lock:
        if _runner is not None and _runner.has_live_run:
            if not await _runner.stop_and_wait():
                raise HTTPException(status_code=409, detail="Previous simulation did not stop")
        token = runner.mark_scheduled() if scheduled else None
        _runner = runner
        return token


def _raise_operation_conflict(exc: SimulationOperationConflict) -> NoReturn:
    """Translate runner-local ownership conflicts into stable API responses."""
    raise HTTPException(status_code=409, detail="Simulation is already running") from exc


def get_runner() -> SimulationRunner | None:
    """Get the current simulation runner."""
    global _runner
    return _runner


@router.post("/start")
async def start_simulation(
    request: dict[str, Any],
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    """Start a simulation."""
    global _runner

    model_data = request.get("model")
    config_data = request.get("config", {})

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
        token = await _install_runner(runner, scheduled=True)
        assert token is not None
        session_id = runner.session_id

        # Run simulation in background
        background_tasks.add_task(runner.run, token)

        return {"sessionId": session_id}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Runner creation error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create simulation: {str(e)}")


@router.post("/stop")
async def stop_simulation() -> dict[str, str]:
    """Stop the current simulation."""
    global _runner

    if _runner is None:
        raise HTTPException(status_code=400, detail="No simulation running")

    _runner.stop()
    return {"message": "Simulation stopped"}


@router.post("/reset")
async def reset_simulation() -> dict[str, Any]:
    """Reset the simulation to initial state, ready to run again.

    This can be called after a simulation completes, pauses, or in step mode.
    It resets all state to initial values while preserving the compiled model.
    """
    global _runner

    if _runner is None:
        raise HTTPException(status_code=400, detail="No simulation available")

    runner = _runner
    try:
        runner.reset()
    except SimulationOperationConflict as exc:
        _raise_operation_conflict(exc)
    return {
        "success": True,
        "message": "Simulation reset",
        "currentTime": runner.current_time,
        "progress": runner.progress,
        "status": runner.status.value,
    }


@router.post("/pause")
async def pause_simulation() -> dict[str, str]:
    """Pause the current simulation."""
    global _runner

    if _runner is None:
        raise HTTPException(status_code=400, detail="No simulation running")

    runner = _runner
    await runner.pause()
    return {"message": "Simulation paused"}


@router.post("/resume")
async def resume_simulation() -> dict[str, str]:
    """Resume a paused simulation."""
    global _runner

    if _runner is None:
        raise HTTPException(status_code=400, detail="No simulation running")

    _runner.resume()
    return {"message": "Simulation resumed"}


@router.get("/status")
async def get_simulation_status() -> dict[str, Any]:
    """Get current simulation status."""
    global _runner

    if _runner is None:
        return {"status": "idle", "progress": 0}

    result = {
        "status": _runner.status.value,
        "progress": _runner.progress,
        "currentTime": _runner.current_time,
    }

    # Include error message if there is one
    if _runner.error_message:
        result["error"] = _runner.error_message

    return result


@router.get("/results")
async def get_simulation_results() -> dict[str, Any]:
    """Get simulation results."""
    global _runner

    if _runner is None:
        raise HTTPException(status_code=400, detail="No simulation available")

    return _runner.get_results()


@router.post("/step/init")
async def init_step_mode(request: dict[str, Any]) -> dict[str, Any]:
    """Initialize step mode simulation (compile model, ready for stepping)."""
    global _runner

    model_data = request.get("model")
    config_data = request.get("config", {})

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
        await _install_runner(runner, scheduled=False)
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
async def enter_step_mode() -> dict[str, Any]:
    """Enter step mode from a paused continuous simulation.

    This preserves the current simulation state and time position,
    unlike /step/init which reinitializes from the start.
    """
    global _runner

    if _runner is None:
        raise HTTPException(status_code=400, detail="No simulation running. Use /step/init first.")

    try:
        runner = _runner
        success = await runner.enter_step_mode()

        if not success:
            raise HTTPException(
                status_code=500, detail=runner.error_message or "Failed to enter step mode"
            )

        return {
            "success": True,
            "currentTime": runner.current_time,
            "progress": runner.progress,
            "status": runner.status.value,
            "historySize": 1,
        }
    except SimulationOperationConflict as exc:
        _raise_operation_conflict(exc)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Enter step mode error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to enter step mode: {str(e)}")


@router.post("/step/forward")
async def step_forward(request: dict[str, Any] | None = None) -> dict[str, Any]:
    """Execute one or more simulation steps forward."""
    global _runner

    if _runner is None:
        raise HTTPException(
            status_code=400, detail="No simulation initialized. Call /step/init first."
        )

    num_steps = 1
    if request:
        num_steps = request.get("numSteps", 1)

    runner = _runner
    try:
        result = runner.step_forward(num_steps)
    except SimulationOperationConflict as exc:
        _raise_operation_conflict(exc)
    result["status"] = runner.status.value

    return result


@router.post("/step/backward")
async def step_backward(request: dict[str, Any] | None = None) -> dict[str, Any]:
    """Step backward by restoring previous state."""
    global _runner

    if _runner is None:
        raise HTTPException(
            status_code=400, detail="No simulation initialized. Call /step/init first."
        )

    num_steps = 1
    if request:
        num_steps = request.get("numSteps", 1)

    runner = _runner
    try:
        result = runner.step_backward(num_steps)
    except SimulationOperationConflict as exc:
        _raise_operation_conflict(exc)
    result["status"] = runner.status.value

    return result


@router.post("/step/reset")
async def reset_step_mode() -> dict[str, Any]:
    """Reset step mode simulation to start time."""
    global _runner

    if _runner is None:
        raise HTTPException(status_code=400, detail="No simulation initialized")

    runner = _runner
    try:
        runner.reset_step_mode()
    except SimulationOperationConflict as exc:
        _raise_operation_conflict(exc)

    return {
        "success": True,
        "currentTime": runner.current_time,
        "status": runner.status.value,
    }


@router.post("/step/continue")
async def continue_from_step(background_tasks: BackgroundTasks) -> dict[str, Any]:
    """Continue running simulation from current step mode position."""
    global _runner

    if _runner is None:
        raise HTTPException(status_code=400, detail="No simulation initialized")
    runner = _runner
    try:
        token = runner.schedule_continue()
    except SimulationOperationConflict as exc:
        _raise_operation_conflict(exc)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    background_tasks.add_task(runner.continue_from_step_mode, token)

    return {
        "success": True,
        "currentTime": runner.current_time,
        "status": "running",
    }


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
