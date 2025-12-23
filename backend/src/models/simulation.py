"""Simulation-related Pydantic models."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class SolverType(str, Enum):
    """Available ODE solvers."""

    EULER = "euler"
    RK4 = "rk4"
    MERSON = "merson"


class SimulationConfig(BaseModel):
    """Simulation configuration."""
    model_config = ConfigDict(populate_by_name=True)

    solver: SolverType = SolverType.RK4
    start_time: float = Field(default=0.0, alias="startTime")
    stop_time: float = Field(default=10.0, alias="stopTime")
    step_size: float = Field(default=0.01, alias="stepSize")
    max_step: float | None = Field(default=None, alias="maxStep")
    min_step: float | None = Field(default=None, alias="minStep")
    relative_tolerance: float = Field(default=1e-3, alias="relativeTolerance")
    absolute_tolerance: float = Field(default=1e-6, alias="absoluteTolerance")


class SimulationStatus(str, Enum):
    """Simulation execution status."""

    IDLE = "idle"
    COMPILING = "compiling"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


class SignalData(BaseModel):
    """Time series data for a signal."""
    model_config = ConfigDict(populate_by_name=True)

    block_id: str = Field(alias="blockId")
    port_id: str = Field(alias="portId")
    name: str
    times: list[float]
    values: list[float]


class SimulationStatistics(BaseModel):
    """Simulation execution statistics."""
    model_config = ConfigDict(populate_by_name=True)

    total_steps: int = Field(alias="totalSteps")
    execution_time: float = Field(alias="executionTime")
    final_time: float = Field(alias="finalTime")


class SimulationResults(BaseModel):
    """Complete simulation results."""

    signals: list[SignalData]
    statistics: SimulationStatistics
