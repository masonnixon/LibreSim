"""Model-related Pydantic models."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, ConfigDict

from .block import Block, Connection
from .simulation import SimulationConfig


class ModelMetadata(BaseModel):
    """Model metadata."""
    model_config = ConfigDict(populate_by_name=True)

    name: str
    description: str = ""
    author: str = ""
    created_at: datetime = Field(default_factory=datetime.now, alias="createdAt")
    modified_at: datetime = Field(default_factory=datetime.now, alias="modifiedAt")
    version: str = "1.0.0"


class Model(BaseModel):
    """Complete model definition."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    metadata: ModelMetadata
    blocks: list[Block] = Field(default_factory=list)
    connections: list[Connection] = Field(default_factory=list)
    simulation_config: SimulationConfig = Field(
        default_factory=SimulationConfig, alias="simulationConfig"
    )


class ModelCreate(BaseModel):
    """Request model for creating a new model."""

    name: str
    description: str = ""


class ModelUpdate(BaseModel):
    """Request model for updating an existing model."""
    model_config = ConfigDict(populate_by_name=True)

    metadata: ModelMetadata | None = None
    blocks: list[Block] | None = None
    connections: list[Connection] | None = None
    simulation_config: SimulationConfig | None = Field(None, alias="simulationConfig")
