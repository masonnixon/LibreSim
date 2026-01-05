"""Base class for language-specific code generators."""

from abc import ABC, abstractmethod
from typing import Any

from ..models import (
    BlockInfo,
    CompiledModelInfo,
    GeneratedProject,
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
        # Map common Unicode superscript/subscript to ASCII equivalents
        unicode_replacements = {
            "²": "2",
            "³": "3",
            "¹": "1",
            "⁴": "4",
            "⁵": "5",
            "⁶": "6",
            "⁷": "7",
            "⁸": "8",
            "⁹": "9",
            "⁰": "0",
            "₀": "0",
            "₁": "1",
            "₂": "2",
            "₃": "3",
            "₄": "4",
            "₅": "5",
            "₆": "6",
            "₇": "7",
            "₈": "8",
            "₉": "9",
            "°": "deg",
            "π": "pi",
            "α": "alpha",
            "β": "beta",
            "γ": "gamma",
            "δ": "delta",
            "Δ": "Delta",
            "θ": "theta",
            "Θ": "Theta",
            "ω": "omega",
            "Ω": "Omega",
            "φ": "phi",
            "Φ": "Phi",
            "ψ": "psi",
            "Ψ": "Psi",
            "μ": "mu",
            "σ": "sigma",
            "τ": "tau",
            "ρ": "rho",
            "λ": "lambda",
            "ε": "epsilon",
        }

        # Replace Unicode characters first
        for unicode_char, replacement in unicode_replacements.items():
            name = name.replace(unicode_char, replacement)

        # Replace non-ASCII alphanumeric with underscore
        # Only allow ASCII letters (a-z, A-Z), digits (0-9), and underscores
        result = ""
        for char in name:
            if (
                (char >= "a" and char <= "z")
                or (char >= "A" and char <= "Z")
                or (char >= "0" and char <= "9")
                or char == "_"
            ):
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
        # Always use block ID to ensure uniqueness (names can be duplicated)
        # Sanitize the ID to make it a valid identifier
        sanitized_id = self.sanitize_identifier(block.id)
        return f"block_{sanitized_id}"

    def parse_connection(self, conn_str: str) -> tuple[str, int, int | None]:
        """Parse a connection string.

        Args:
            conn_str: Connection string like "source_id:port@target_port"

        Returns:
            Tuple of (block_id, source_port, target_port or None)
        """
        import re

        def extract_port_number(port_str: str) -> int:
            """Extract port number from strings like 'in0', 'out', '0', etc.

            Port naming convention:
            - 0-indexed: 'in0', 'in1', 'out0', 'out1' -> returns 0, 1, 0, 1
            - 1-indexed: 'in1', 'in2', 'out1', 'out2' -> returns 0, 1, 0, 1

            The convention is: if the first port is numbered 0, use 0-indexed.
            If the first port is numbered 1, use 1-indexed (subtract 1).
            """
            if port_str.isdigit():
                return int(port_str)
            # Try to extract number from end of string (e.g., "in0" -> 0, "out1" -> 1)
            match = re.search(r"(\d+)$", port_str)
            if match:
                port_num = int(match.group(1))
                # If port_num is 0, it's 0-indexed; otherwise assume 1-indexed
                return port_num if port_num == 0 else port_num - 1
            return 0

        # Format: "source_id:source_port@target_port" for inputs
        # Format: "target_id:target_port" for outputs
        if "@" in conn_str:
            # Input connection
            parts = conn_str.split("@")
            target_port = extract_port_number(parts[1])
            source_parts = parts[0].rsplit(":", 1)
            source_id = source_parts[0]
            source_port = extract_port_number(source_parts[1]) if len(source_parts) > 1 else 0
            return (source_id, source_port, target_port)
        else:
            # Output connection
            parts = conn_str.rsplit(":", 1)
            target_id = parts[0]
            target_port = extract_port_number(parts[1]) if len(parts) > 1 else 0
            return (target_id, target_port, None)
