"""Model management API routes."""

from fastapi import APIRouter, HTTPException
from typing import Dict

from ...models.model import Model, ModelCreate, ModelUpdate
from ...services.model_service import ModelService

router = APIRouter()
model_service = ModelService()


@router.get("")
async def list_models() -> list[Model]:
    """List all models."""
    return model_service.list_models()


@router.post("")
async def create_model(model: ModelCreate) -> Model:
    """Create a new model."""
    return model_service.create_model(model)


@router.get("/{model_id}")
async def get_model(model_id: str) -> Model:
    """Get a model by ID."""
    model = model_service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.put("/{model_id}")
async def update_model(model_id: str, model: ModelUpdate) -> Model:
    """Update an existing model."""
    updated = model_service.update_model(model_id, model)
    if not updated:
        raise HTTPException(status_code=404, detail="Model not found")
    return updated


@router.delete("/{model_id}")
async def delete_model(model_id: str) -> Dict[str, str]:
    """Delete a model."""
    success = model_service.delete_model(model_id)
    if not success:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"message": "Model deleted"}


@router.post("/{model_id}/validate")
async def validate_model(model_id: str) -> Dict[str, any]:
    """Validate a model for simulation."""
    model = model_service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    validation = model_service.validate_model(model)
    return validation


@router.post("/{model_id}/compile")
async def compile_model(model_id: str) -> Dict[str, any]:
    """Compile a model for simulation."""
    model = model_service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    result = model_service.compile_model(model)
    return result
