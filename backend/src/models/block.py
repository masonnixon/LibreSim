"""Block-related Pydantic models."""

from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field, ConfigDict


class BlockCategory(str, Enum):
    """Block category types."""

    SOURCES = "sources"
    SINKS = "sinks"
    CONTINUOUS = "continuous"
    DISCRETE = "discrete"
    MATH = "math"
    ROUTING = "routing"
    SUBSYSTEMS = "subsystems"


class DataType(str, Enum):
    """Signal data types."""

    DOUBLE = "double"
    SINGLE = "single"
    INT32 = "int32"
    BOOLEAN = "boolean"
    BUS = "bus"


class Port(BaseModel):
    """Port definition for a block."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    data_type: DataType = Field(default=DataType.DOUBLE, alias="dataType")
    dimensions: list[int] = Field(default=[1])


class ParameterType(str, Enum):
    """Parameter types."""

    NUMBER = "number"
    STRING = "string"
    BOOLEAN = "boolean"
    SELECT = "select"
    ARRAY = "array"


class ParameterOption(BaseModel):
    """Option for select-type parameters."""

    value: str
    label: str


class Parameter(BaseModel):
    """Block parameter definition."""

    name: str
    type: ParameterType
    default: Any
    label: str
    description: str | None = None
    options: list[ParameterOption] | None = None
    min: float | None = None
    max: float | None = None
    step: float | None = None


class BlockDefinition(BaseModel):
    """Definition of a block type."""

    type: str
    category: BlockCategory
    name: str
    description: str
    inputs: list[Port]
    outputs: list[Port]
    parameters: list[Parameter]
    icon: str | None = None


class Position(BaseModel):
    """2D position."""

    x: float
    y: float


class Block(BaseModel):
    """Instance of a block in a model."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    type: str
    name: str
    position: Position
    parameters: dict[str, Any] = Field(default_factory=dict)
    input_ports: list[Port] = Field(default_factory=list, alias="inputPorts")
    output_ports: list[Port] = Field(default_factory=list, alias="outputPorts")
    # For Subsystem blocks only
    children: list["Block"] | None = Field(default=None)
    child_connections: list["Connection"] | None = Field(default=None, alias="childConnections")
    is_expanded: bool | None = Field(default=None, alias="isExpanded")


class Connection(BaseModel):
    """Connection between blocks."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    source_block_id: str = Field(alias="sourceBlockId")
    source_port_id: str = Field(alias="sourcePortId")
    target_block_id: str = Field(alias="targetBlockId")
    target_port_id: str = Field(alias="targetPortId")


# Rebuild models to resolve forward references
Block.model_rebuild()
