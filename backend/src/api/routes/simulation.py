"""Simulation control API routes."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any

from ...models.simulation import SimulationConfig, SimulationStatus
from ...simulation.runner import SimulationRunner
from ...services.model_service import ModelService

router = APIRouter()
model_service = ModelService()

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

    model_id = request.get("modelId")
    config_data = request.get("config", {})

    if not model_id:
        raise HTTPException(status_code=400, detail="modelId is required")

    model = model_service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    # Validate model first
    validation = model_service.validate_model(model)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["errors"])

    # Create simulation config
    config = SimulationConfig(**config_data)

    # Create and start runner
    _runner = SimulationRunner(model, config)
    session_id = _runner.session_id

    # Run simulation in background
    background_tasks.add_task(_runner.run)

    return {"sessionId": session_id}


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
