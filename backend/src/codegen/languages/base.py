"""Base class for language-specific code generators."""

from abc import ABC, abstractmethod
from typing import Any

from ..models import (
    GeneratedProject,
    CompiledModelInfo,
    BlockInfo,
    IntegrationMethod,
)


class LanguageGenerator(ABC):
    """Abstract base class for language-specific code generators."""

    @abstractmethod
    def generate(
        self,
        model_info: CompiledModelInfo,
        config: Any,  # CodeGenerationConfig
    ) -> GeneratedProject:
        """Generate a project for the target language.

        Args:
            model_info: Compiled model information
            config: Code generation configuration

        Returns:
            GeneratedProject with all files
        """
        pass

    @abstractmethod
    def generate_block_code(self, block: BlockInfo) -> str:
        """Generate code for a single block.

        Args:
            block: Block information

        Returns:
            Generated code string
        """
        pass

    @abstractmethod
    def generate_integration_code(self, method: IntegrationMethod) -> str:
        """Generate integration method code.

        Args:
            method: Integration method

        Returns:
            Generated code string
        """
        pass

    @abstractmethod
    def generate_main_code(
        self,
        model_info: CompiledModelInfo,
        config: Any,
    ) -> str:
        """Generate main/entry point code.

        Args:
            model_info: Compiled model information
            config: Code generation configuration

        Returns:
            Generated code string
        """
        pass

    def sanitize_identifier(self, name: str) -> str:
        """Convert a name to a valid identifier.

        Args:
            name: Original name

        Returns:
            Valid identifier string
        """
        # Replace non-alphanumeric with underscore
        result = ""
        for char in name:
            if char.isalnum():
                result += char
            else:
                result += "_"

        # Ensure starts with letter or underscore
        if result and result[0].isdigit():
            result = "_" + result

        return result or "_unnamed"

    def get_block_var_name(self, block: BlockInfo) -> str:
        """Get variable name for a block.

        Args:
            block: Block information

        Returns:
            Variable name string
        """
        # Use sanitized name or ID
        name = self.sanitize_identifier(block.name or block.id)
        return f"block_{name}"

    def parse_connection(self, conn_str: str) -> tuple[str, int, int | None]:
        """Parse a connection string.

        Args:
            conn_str: Connection string like "source_id:port@target_port"

        Returns:
            Tuple of (block_id, source_port, target_port or None)
        """
        # Format: "source_id:source_port@target_port" for inputs
        # Format: "target_id:target_port" for outputs
        if "@" in conn_str:
            # Input connection
            parts = conn_str.split("@")
            target_port = int(parts[1]) if parts[1].isdigit() else 0
            source_parts = parts[0].rsplit(":", 1)
            source_id = source_parts[0]
            source_port = int(source_parts[1]) if len(source_parts) > 1 and source_parts[1].isdigit() else 0
            return (source_id, source_port, target_port)
        else:
            # Output connection
            parts = conn_str.rsplit(":", 1)
            target_id = parts[0]
            target_port = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
            return (target_id, target_port, None)
