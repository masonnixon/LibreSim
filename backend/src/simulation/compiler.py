"""Model compiler - converts visual model to OSK representation."""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Set

from ..models.model import Model
from ..models.block import Block, Connection


@dataclass
class CompiledBlock:
    """Compiled block ready for simulation."""

    id: str
    type: str
    name: str
    parameters: Dict[str, Any]
    input_connections: List[str] = field(default_factory=list)  # ["block_id:port_id", ...]
    output_connections: List[str] = field(default_factory=list)
    execution_order: int = 0


@dataclass
class CompiledModel:
    """Compiled model ready for OSK execution."""

    success: bool
    message: str
    blocks: List[CompiledBlock] = field(default_factory=list)
    execution_order: List[str] = field(default_factory=list)  # Block IDs in execution order
    errors: List[str] = field(default_factory=list)


class ModelCompiler:
    """Compiles LibreSim visual models to OSK-executable format."""

    def compile(self, model: Model) -> CompiledModel:
        """Compile a model for simulation.

        Steps:
        1. Build connectivity graph
        2. Detect algebraic loops
        3. Topological sort for execution order
        4. Create compiled blocks
        """
        if not model.blocks:
            return CompiledModel(
                success=False,
                message="Model has no blocks",
                errors=["Model has no blocks"],
            )

        try:
            # Build connection maps
            block_map = {b.id: b for b in model.blocks}
            input_connections = self._build_input_map(model.connections)
            output_connections = self._build_output_map(model.connections)

            # Build dependency graph
            dependencies = self._build_dependency_graph(model.blocks, input_connections)

            # Check for algebraic loops
            loop = self._detect_algebraic_loops(dependencies)
            if loop:
                return CompiledModel(
                    success=False,
                    message="Algebraic loop detected",
                    errors=[f"Algebraic loop involving blocks: {', '.join(loop)}"],
                )

            # Topological sort
            execution_order = self._topological_sort(model.blocks, dependencies)

            # Create compiled blocks
            compiled_blocks = []
            for order, block_id in enumerate(execution_order):
                block = block_map[block_id]
                compiled = CompiledBlock(
                    id=block.id,
                    type=block.type,
                    name=block.name,
                    parameters=block.parameters,
                    input_connections=input_connections.get(block.id, []),
                    output_connections=output_connections.get(block.id, []),
                    execution_order=order,
                )
                compiled_blocks.append(compiled)

            return CompiledModel(
                success=True,
                message="Model compiled successfully",
                blocks=compiled_blocks,
                execution_order=execution_order,
            )

        except Exception as e:
            return CompiledModel(
                success=False,
                message=f"Compilation error: {str(e)}",
                errors=[str(e)],
            )

    def _build_input_map(
        self, connections: List[Connection]
    ) -> Dict[str, List[str]]:
        """Build map of block ID -> list of input connections."""
        result: Dict[str, List[str]] = {}
        for conn in connections:
            if conn.target_block_id not in result:
                result[conn.target_block_id] = []
            result[conn.target_block_id].append(
                f"{conn.source_block_id}:{conn.source_port_id}"
            )
        return result

    def _build_output_map(
        self, connections: List[Connection]
    ) -> Dict[str, List[str]]:
        """Build map of block ID -> list of output connections."""
        result: Dict[str, List[str]] = {}
        for conn in connections:
            if conn.source_block_id not in result:
                result[conn.source_block_id] = []
            result[conn.source_block_id].append(
                f"{conn.target_block_id}:{conn.target_port_id}"
            )
        return result

    def _build_dependency_graph(
        self, blocks: List[Block], input_connections: Dict[str, List[str]]
    ) -> Dict[str, Set[str]]:
        """Build graph of block dependencies (block -> set of blocks it depends on)."""
        dependencies: Dict[str, Set[str]] = {b.id: set() for b in blocks}

        for block in blocks:
            if block.id in input_connections:
                for conn in input_connections[block.id]:
                    source_block_id = conn.split(":")[0]
                    dependencies[block.id].add(source_block_id)

        return dependencies

    def _detect_algebraic_loops(
        self, dependencies: Dict[str, Set[str]]
    ) -> List[str] | None:
        """Detect algebraic loops using DFS. Returns loop if found, None otherwise."""
        WHITE, GRAY, BLACK = 0, 1, 2
        color: Dict[str, int] = {node: WHITE for node in dependencies}
        path: List[str] = []

        def dfs(node: str) -> List[str] | None:
            color[node] = GRAY
            path.append(node)

            for neighbor in dependencies.get(node, set()):
                if color[neighbor] == GRAY:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:]
                elif color[neighbor] == WHITE:
                    result = dfs(neighbor)
                    if result:
                        return result

            path.pop()
            color[node] = BLACK
            return None

        for node in dependencies:
            if color[node] == WHITE:
                result = dfs(node)
                if result:
                    return result

        return None

    def _topological_sort(
        self, blocks: List[Block], dependencies: Dict[str, Set[str]]
    ) -> List[str]:
        """Sort blocks in execution order using Kahn's algorithm."""
        # Calculate in-degrees
        in_degree: Dict[str, int] = {b.id: 0 for b in blocks}
        for block_id, deps in dependencies.items():
            in_degree[block_id] = len(deps)

        # Start with nodes that have no dependencies
        queue = [b.id for b in blocks if in_degree[b.id] == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            # Find blocks that depend on this one
            for block_id, deps in dependencies.items():
                if node in deps:
                    in_degree[block_id] -= 1
                    if in_degree[block_id] == 0:
                        queue.append(block_id)

        return result
