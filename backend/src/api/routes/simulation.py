"""Simulation control API routes."""

import traceback
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any

from ...models.model import Model
from ...models.simulation import SimulationConfig, SimulationStatus
from ...simulation.runner import SimulationRunner

router = APIRouter()

# Global simulation runner instance (single-user for now)
_runner: SimulationRunner | None = None


def get_runner() -> SimulationRunner | None:
    """Get the current simulation runner."""
    global _runner
    return _runner


@router.post("/start")
async def start_simulation(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks,
) -> Dict[str, str]:
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
        _runner = SimulationRunner(model, config)
        session_id = _runner.session_id

        # Run simulation in background
        background_tasks.add_task(_runner.run)

        return {"sessionId": session_id}
    except Exception as e:
        print(f"Runner creation error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create simulation: {str(e)}")


@router.post("/stop")
async def stop_simulation() -> Dict[str, str]:
    """Stop the current simulation."""
    global _runner

    if _runner is None:
        raise HTTPException(status_code=400, detail="No simulation running")

    _runner.stop()
    return {"message": "Simulation stopped"}


@router.post("/pause")
async def pause_simulation() -> Dict[str, str]:
    """Pause the current simulation."""
    global _runner

    if _runner is None:
        raise HTTPException(status_code=400, detail="No simulation running")

    _runner.pause()
    return {"message": "Simulation paused"}


@router.post("/resume")
async def resume_simulation() -> Dict[str, str]:
    """Resume a paused simulation."""
    global _runner

    if _runner is None:
        raise HTTPException(status_code=400, detail="No simulation running")

    _runner.resume()
    return {"message": "Simulation resumed"}


@router.get("/status")
async def get_simulation_status() -> Dict[str, Any]:
    """Get current simulation status."""
    global _runner

    if _runner is None:
        return {"status": "idle", "progress": 0}

    return {
        "status": _runner.status.value,
        "progress": _runner.progress,
        "currentTime": _runner.current_time,
    }


@router.get("/results")
async def get_simulation_results() -> Dict[str, Any]:
    """Get simulation results."""
    global _runner

    if _runner is None:
        raise HTTPException(status_code=400, detail="No simulation available")

    return _runner.get_results()


@router.post("/debug")
async def debug_simulation(request: Dict[str, Any]) -> Dict[str, Any]:
    """Debug endpoint to test model parsing."""
    model_data = request.get("model")
    config_data = request.get("config", {})

    result = {
        "model_received": model_data is not None,
        "config_received": config_data is not None,
    }

    if model_data:
        result["model_keys"] = list(model_data.keys()) if isinstance(model_data, dict) else "not a dict"
        result["blocks_count"] = len(model_data.get("blocks", [])) if isinstance(model_data, dict) else 0

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
            runner = SimulationRunner(model, config)
            result["runner_created"] = True
        except Exception as e:
            result["runner_created"] = False
            result["runner_error"] = str(e)
            traceback.print_exc()

    return result
