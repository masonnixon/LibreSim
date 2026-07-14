"""Data models for code generation."""

import zipfile
from dataclasses import dataclass, field
from enum import StrEnum
from io import BytesIO
from typing import Any


class Language(StrEnum):
    """Supported target languages."""

    PYTHON = "python"
    C = "c"
    CPP = "cpp"
    RUST = "rust"


class IntegrationMethod(StrEnum):
    """Numerical integration methods."""

    EULER = "euler"
    RK2 = "rk2"
    RK4 = "rk4"
    MERSON = "merson"


@dataclass
class GeneratedFile:
    """A single generated file."""

    path: str  # Relative path within project
    content: str
    is_binary: bool = False


@dataclass
class GeneratedProject:
    """A complete generated project."""

    name: str
    language: Language
    files: list[GeneratedFile] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_file(self, path: str, content: str, is_binary: bool = False) -> None:
        """Add a file to the project."""
        self.files.append(GeneratedFile(path=path, content=content, is_binary=is_binary))

    def to_zip(self) -> BytesIO:
        """Create a byte-reproducible ZIP archive of the project."""
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in self.files:
                # Prefix with project name
                full_path = f"{self.name}/{file.path}"
                info = zipfile.ZipInfo(full_path, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                data = file.content.encode("utf-8") if file.is_binary else file.content
                zf.writestr(info, data)
        buffer.seek(0)
        return buffer

    def get_file(self, path: str) -> GeneratedFile | None:
        """Get a file by path."""
        for file in self.files:
            if file.path == path:
                return file
        return None


@dataclass
class BlockTemplate:
    """Template for generating code for a specific block type."""

    block_type: str
    # Structure/class definition
    struct_definition: str
    # Initialization code
    init_code: str
    # Update/step function code
    update_code: str
    # Output retrieval code
    output_code: str
    # Required imports/includes
    dependencies: list[str] = field(default_factory=list)
    # Number of state variables (for integrators)
    num_states: int = 0
    # Whether this block has internal state
    has_state: bool = False


@dataclass
class SignalInfo:
    """Information about a signal in the model."""

    source_block_id: str
    source_port: int
    dimensions: list[int]  # [1] = scalar, [3] = 3-vector, etc.
    dtype: str = "double"


@dataclass(frozen=True)
class OutputSignalInfo:
    """Canonical metadata for one scalar column in generated output."""

    canonical_key: str
    sink_block_id: str
    sink_input_port: int
    source_block_id: str
    source_output_port: int
    dimensions: tuple[int, ...]
    element_index: tuple[int, ...]
    flat_index: int


@dataclass
class BlockInfo:
    """Compiled information about a block for code generation."""

    id: str
    type: str
    name: str
    parameters: dict[str, Any]
    input_connections: list[str]  # ["source_id:port@target_port", ...]
    output_connections: list[str]  # ["target_id:port", ...]
    execution_order: int
    # Port dimensions for vector signal handling
    # Each entry is dimensions list e.g. [1] for scalar, [3] for 3-vector, [4] for quaternion
    input_dimensions: list[list[int]] = field(default_factory=list)
    output_dimensions: list[list[int]] = field(default_factory=list)
    # Resolved signal types
    input_signals: list[SignalInfo] = field(default_factory=list)
    output_signals: list[SignalInfo] = field(default_factory=list)
    # True when OSK mutates this block only during its major/ready update phase.
    ready_only: bool = False
    # True when the generated template owns and propagates one or more RK states.
    custom_state_propagation: bool = False
    # Nominal simulation step used by internally-discrete block templates.
    step_size: float = 0.01


@dataclass
class CompiledModelInfo:
    """Information extracted from compiled model for code generation."""

    blocks: list[BlockInfo]
    execution_order: list[str]
    integrator_blocks: list[str]  # Block IDs that have state
    source_blocks: list[str]  # Input/source block IDs
    sink_blocks: list[str]  # Output/sink block IDs
    step_size: float
    stop_time: float
    start_time: float = 0.0
    output_signals: list[OutputSignalInfo] = field(default_factory=list)
