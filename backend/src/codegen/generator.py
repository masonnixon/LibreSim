"""Main code generator orchestrator."""

from dataclasses import dataclass, field
from typing import Any, Literal

from src.simulation.compiler import ModelCompiler
from src.models.model import Model
from .models import (
    Language,
    IntegrationMethod,
    GeneratedProject,
    CompiledModelInfo,
    BlockInfo,
)


# Block types that require numerical integration (have state/derivative interface)
# These blocks implement the integrator interface with state, derivative, x0, xd0, etc.
INTEGRATOR_BLOCKS = {
    "integrator",
    "limited_integrator",
    "transfer_function",
    "state_space",
    "second_order",
}

# Block types that hold state but use their own internal update mechanism
# These blocks don't need external integration - they update their own state
STATE_HOLDING_BLOCKS = {
    "integrator",
    "limited_integrator",
    "derivative",
    "transfer_function",
    "state_space",
    "zero_pole",
    "second_order",
    "discrete_integrator",
    "discrete_transfer_function",
    "discrete_state_space",
    "discrete_filter",
    "unit_delay",
    "memory",
    "transport_delay",
    "variable_transport_delay",
    "pid_controller",
    "discrete_pid_controller",
    "moving_average",
    "low_pass_filter",
    "high_pass_filter",
    "band_pass_filter",
    "rate_limiter",
    "backlash",
    "kalman_filter",
    "extended_kalman_filter",
    "luenberger_observer",
    "complementary_filter",
    "madgwick_filter",
    "mahony_filter",
    "alpha_beta_filter",
    "alpha_beta_gamma_filter",
    "ins_gps_fusion",
    "fir_filter",
    "iir_filter",
}

# Source blocks (no inputs, generate signals)
SOURCE_BLOCKS = {
    "constant",
    "step",
    "ramp",
    "sine_wave",
    "pulse",
    "clock",
    "white_noise",
    "from_workspace",
    "ground",
    "imu_sensor",
    "accelerometer",
    "gyroscope",
    "magnetometer",
    "gps_sensor",
    "altimeter",
}

# Sink blocks (consume signals, produce outputs)
SINK_BLOCKS = {
    "scope",
    "to_workspace",
    "display",
    "terminator",
    "xy_graph",
}


@dataclass
class CodeGenerationConfig:
    """Configuration for code generation."""
    language: Language = Language.PYTHON
    integration_method: IntegrationMethod = IntegrationMethod.RK4
    step_size: float = 0.01
    stop_time: float = 10.0
    start_time: float = 0.0
    project_name: str = "simulation"
    include_csv_output: bool = True
    include_main: bool = True
    optimization_level: int = 0  # 0-3 for C/C++/Rust


class CodeGenerator:
    """Main orchestrator for code generation."""

    def __init__(self):
        self._compiler = ModelCompiler()
        self._generators: dict[Language, "LanguageGenerator"] = {}
        self._register_generators()

    def _register_generators(self) -> None:
        """Register language-specific generators."""
        # Import here to avoid circular imports
        from .languages.python.generator import PythonCodeGenerator
        from .languages.c.generator import CCodeGenerator
        from .languages.cpp.generator import CppCodeGenerator
        from .languages.rust.generator import RustCodeGenerator

        self._generators[Language.PYTHON] = PythonCodeGenerator()
        self._generators[Language.C] = CCodeGenerator()
        self._generators[Language.CPP] = CppCodeGenerator()
        self._generators[Language.RUST] = RustCodeGenerator()

    def generate(
        self,
        model: dict[str, Any],
        config: CodeGenerationConfig,
    ) -> GeneratedProject:
        """Generate code from a model.

        Args:
            model: The model dictionary (from JSON/API)
            config: Code generation configuration

        Returns:
            GeneratedProject containing all generated files
        """
        # Step 1: Convert dict to Model object if needed and compile
        if isinstance(model, dict):
            model_obj = Model.model_validate(model)
        else:
            model_obj = model
        compiled = self._compiler.compile(model_obj)
        if not compiled.success:
            raise CodeGenerationError(f"Model compilation failed: {compiled.message}")

        # Step 2: Extract information for code generation
        model_info = self._extract_model_info(compiled, model, config)

        # Step 3: Get language-specific generator
        generator = self._generators.get(config.language)
        if generator is None:
            raise CodeGenerationError(f"Unsupported language: {config.language}")

        # Step 4: Generate the project
        return generator.generate(model_info, config)

    def _extract_model_info(
        self,
        compiled: Any,  # CompiledModel from compiler
        model: dict[str, Any],
        config: CodeGenerationConfig,
    ) -> CompiledModelInfo:
        """Extract code generation info from compiled model."""
        blocks: list[BlockInfo] = []
        integrator_blocks: list[str] = []
        source_blocks: list[str] = []
        sink_blocks: list[str] = []

        # Build a map of block ID to block data from original model
        block_map = {b["id"]: b for b in model.get("blocks", [])}

        for i, block_id in enumerate(compiled.execution_order):
            # Find the compiled block
            compiled_block = None
            for cb in compiled.blocks:
                if cb.id == block_id:
                    compiled_block = cb
                    break

            if compiled_block is None:
                continue

            # Get original block data for parameters
            original_block = block_map.get(block_id, {})

            block_info = BlockInfo(
                id=block_id,
                type=compiled_block.type,
                name=compiled_block.name,
                parameters=original_block.get("parameters", {}),
                input_connections=compiled_block.input_connections,
                output_connections=compiled_block.output_connections,
                execution_order=i,
            )
            blocks.append(block_info)

            # Categorize blocks
            # Only blocks with the integrator interface go in integrator_blocks
            if compiled_block.type in INTEGRATOR_BLOCKS:
                integrator_blocks.append(block_id)
            if compiled_block.type in SOURCE_BLOCKS:
                source_blocks.append(block_id)
            if compiled_block.type in SINK_BLOCKS:
                sink_blocks.append(block_id)

        # Get simulation config
        sim_config = model.get("simulationConfig", {})

        return CompiledModelInfo(
            blocks=blocks,
            execution_order=compiled.execution_order,
            integrator_blocks=integrator_blocks,
            source_blocks=source_blocks,
            sink_blocks=sink_blocks,
            step_size=config.step_size or sim_config.get("stepSize", 0.01),
            stop_time=config.stop_time or sim_config.get("stopTime", 10.0),
            start_time=config.start_time or sim_config.get("startTime", 0.0),
        )

    def get_supported_blocks(self) -> list[str]:
        """Get list of block types supported for code generation."""
        from src.simulation.osk_adapter import BLOCK_TYPE_MAP
        return list(BLOCK_TYPE_MAP.keys())

    def get_supported_languages(self) -> list[str]:
        """Get list of supported languages."""
        return [lang.value for lang in Language]

    def get_supported_methods(self) -> list[str]:
        """Get list of supported integration methods."""
        return [method.value for method in IntegrationMethod]


class CodeGenerationError(Exception):
    """Error during code generation."""
    pass


# Base class for language generators (imported by language modules)
class LanguageGenerator:
    """Abstract base class for language-specific code generators."""

    def generate(
        self,
        model_info: CompiledModelInfo,
        config: CodeGenerationConfig,
    ) -> GeneratedProject:
        """Generate a project for the target language.

        Args:
            model_info: Compiled model information
            config: Code generation configuration

        Returns:
            GeneratedProject with all files
        """
        raise NotImplementedError("Subclasses must implement generate()")

    def get_block_template(self, block_type: str) -> str:
        """Get the code template for a block type."""
        raise NotImplementedError("Subclasses must implement get_block_template()")
