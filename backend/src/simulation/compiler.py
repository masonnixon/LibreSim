"""Model compiler - converts visual model to OSK representation."""

from dataclasses import dataclass, field
from typing import Any

from ..models.block import Block, Connection
from ..models.model import Model


@dataclass
class CompiledBlock:
    """Compiled block ready for simulation."""

    id: str
    type: str
    name: str
    parameters: dict[str, Any]
    input_connections: list[str] = field(default_factory=list)  # ["block_id:port_id", ...]
    output_connections: list[str] = field(default_factory=list)
    execution_order: int = 0
    output_dimensions: list[list[int]] = field(default_factory=list)


@dataclass
class CompiledModel:
    """Compiled model ready for OSK execution."""

    success: bool
    message: str
    blocks: list[CompiledBlock] = field(default_factory=list)
    execution_order: list[str] = field(default_factory=list)  # Block IDs in execution order
    errors: list[str] = field(default_factory=list)


class ModelCompiler:
    """Compiles LibreSim visual models to OSK-executable format."""

    def compile(self, model: Model) -> CompiledModel:
        """Compile a model for simulation.

        Steps:
        1. Flatten subsystems
        2. Build connectivity graph
        3. Detect algebraic loops
        4. Topological sort for execution order
        5. Create compiled blocks
        """
        if not model.blocks:
            return CompiledModel(
                success=False,
                message="Model has no blocks",
                errors=["Model has no blocks"],
            )

        try:
            # Flatten subsystems first
            flattened_blocks, flattened_connections = self._flatten_subsystems(
                model.blocks, model.connections
            )

            # Build connection maps
            block_map = {b.id: b for b in flattened_blocks}
            input_connections = self._build_input_map(flattened_connections)
            output_connections = self._build_output_map(flattened_connections)

            # Build dependency graph for algebraic loop detection
            # (excludes state-holding blocks which break algebraic loops)
            algebraic_dependencies = self._build_dependency_graph(
                flattened_blocks, input_connections, for_algebraic_loop_detection=True
            )

            # Check for algebraic loops
            loop = self._detect_algebraic_loops(algebraic_dependencies)
            if loop:
                return CompiledModel(
                    success=False,
                    message="Algebraic loop detected",
                    errors=[f"Algebraic loop involving blocks: {', '.join(loop)}"],
                )

            # Build dependency graph for execution order
            # We break cycles at state-holding blocks since they output based on previous state
            # This is the same as algebraic loop detection graph
            execution_dependencies = self._build_dependency_graph(
                flattened_blocks, input_connections, for_algebraic_loop_detection=True
            )

            # Topological sort for execution order
            execution_order = self._topological_sort(flattened_blocks, execution_dependencies)

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
                    output_dimensions=[port.dimensions for port in block.output_ports],
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

    def _build_input_map(self, connections: list[Connection]) -> dict[str, list[str]]:
        """Build map of block ID -> list of input connections.

        Each connection is formatted as "source_block_id:source_port_id@target_port_id"
        to preserve information about which target port the connection goes to.
        """
        result: dict[str, list[str]] = {}
        for conn in connections:
            if conn.target_block_id not in result:
                result[conn.target_block_id] = []
            result[conn.target_block_id].append(
                f"{conn.source_block_id}:{conn.source_port_id}@{conn.target_port_id}"
            )
        return result

    def _build_output_map(self, connections: list[Connection]) -> dict[str, list[str]]:
        """Build map of block ID -> list of output connections."""
        result: dict[str, list[str]] = {}
        for conn in connections:
            if conn.source_block_id not in result:
                result[conn.source_block_id] = []
            result[conn.source_block_id].append(f"{conn.target_block_id}:{conn.target_port_id}")
        return result

    # Blocks that have internal state and thus "break" algebraic loops
    # These blocks introduce a delay between input and output
    STATE_HOLDING_BLOCKS = {
        "integrator",
        "discrete_integrator",
        "unit_delay",
        "transfer_function",
        "discrete_transfer_function",
        "state_space",
        "derivative",  # Has internal state for filtering
        "discrete_derivative",
        "pid_controller",  # Has integrator and derivative states
        "zero_order_hold",
        "variable_transport_delay",
        "luenberger_observer",
        "kalman_filter",
        "extended_kalman_filter",
        "moving_average",
        "low_pass_filter",
        "high_pass_filter",
        "band_pass_filter",
        "rate_limiter",
        "backlash",
    }

    def _build_dependency_graph(
        self,
        blocks: list[Block],
        input_connections: dict[str, list[str]],
        for_algebraic_loop_detection: bool = False,
    ) -> dict[str, set[str]]:
        """Build graph of block dependencies (block -> set of blocks it depends on).

        Args:
            blocks: List of blocks
            input_connections: Map of block_id -> list of input connections
            for_algebraic_loop_detection: If True, excludes dependencies through
                state-holding blocks (integrators, etc.) since they break algebraic loops.

        Returns:
            Dictionary mapping block_id -> set of block_ids it depends on
        """
        dependencies: dict[str, set[str]] = {b.id: set() for b in blocks}
        block_types = {b.id: b.type for b in blocks}

        for block in blocks:
            if block.id in input_connections:
                for conn in input_connections[block.id]:
                    source_block_id = conn.split(":")[0]

                    # For algebraic loop detection, skip if source is state-holding
                    # (state-holding blocks output based on previous state, not current input)
                    if for_algebraic_loop_detection:
                        source_type = block_types.get(source_block_id, "")
                        if source_type in self.STATE_HOLDING_BLOCKS:
                            continue

                    dependencies[block.id].add(source_block_id)

        return dependencies

    def _detect_algebraic_loops(self, dependencies: dict[str, set[str]]) -> list[str] | None:
        """Detect algebraic loops using DFS. Returns loop if found, None otherwise."""
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {node: WHITE for node in dependencies}
        path: list[str] = []

        def dfs(node: str) -> list[str] | None:
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
        self, blocks: list[Block], dependencies: dict[str, set[str]]
    ) -> list[str]:
        """Sort blocks in execution order using Kahn's algorithm."""
        # Calculate in-degrees
        in_degree: dict[str, int] = {b.id: 0 for b in blocks}
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

    def _flatten_subsystems(
        self, blocks: list[Block], connections: list[Connection]
    ) -> tuple[list[Block], list[Connection]]:
        """Flatten subsystems by extracting child blocks and rewiring connections.

        For each subsystem block:
        1. Extract child blocks (adding prefix to IDs to avoid conflicts)
        2. Replace connections to subsystem inputs with connections to internal Inport outputs
        3. Replace connections from subsystem outputs with connections from internal Outport inputs

        Args:
            blocks: List of blocks (may contain subsystems)
            connections: List of connections

        Returns:
            Tuple of (flattened_blocks, flattened_connections)
        """
        def port_index(port_id: str) -> int | None:
            try:
                return int(port_id.rsplit("-", 1)[-1])
            except (ValueError, IndexError):
                return None

        def prefixed_port_id(port_id: str, block_id: str, prefixed_id: str) -> str:
            if prefixed_id == block_id:
                return port_id
            if port_id.startswith(f"{block_id}-"):
                return f"{prefixed_id}{port_id[len(block_id):]}"
            return f"{prefixed_id}__{port_id}"

        def flatten_level(
            level_blocks: list[Block],
            level_connections: list[Connection],
            prefix: str = "",
            name_prefix: str = "",
        ) -> tuple[list[Block], list[Connection]]:
            flattened_blocks: list[Block] = []
            flattened_connections: list[Connection] = []
            subsystem_inport_map: dict[str, dict[int, str]] = {}
            subsystem_outport_map: dict[str, dict[int, str]] = {}
            flattened_subsystems: set[str] = set()

            for block in level_blocks:
                if block.type != "subsystem" or not block.children:
                    prefixed_id = f"{prefix}{block.id}"
                    flattened_blocks.append(
                        Block(
                            id=prefixed_id,
                            type=block.type,
                            name=f"{name_prefix}/{block.name}" if name_prefix else block.name,
                            position=block.position,
                            parameters=block.parameters,
                            input_ports=[
                                port.model_copy(
                                    update={
                                        "id": prefixed_port_id(port.id, block.id, prefixed_id)
                                    }
                                )
                                for port in block.input_ports
                            ],
                            output_ports=[
                                port.model_copy(
                                    update={
                                        "id": prefixed_port_id(port.id, block.id, prefixed_id)
                                    }
                                )
                                for port in block.output_ports
                            ],
                            children=block.children,
                            child_connections=block.child_connections,
                            is_expanded=block.is_expanded,
                        )
                    )
                    continue

                flattened_subsystems.add(block.id)
                child_prefix = f"{prefix}{block.id}__"
                subsystem_inport_map[block.id] = {}
                subsystem_outport_map[block.id] = {}

                # A subsystem boundary is defined only by its direct children.
                # Descendant inports/outports belong to nested subsystem boundaries.
                for child in block.children:
                    port_num = child.parameters.get("portNumber", 1)
                    if not isinstance(port_num, (int, float)):
                        continue
                    if child.type == "inport":
                        subsystem_inport_map[block.id][int(port_num) - 1] = (
                            f"{child_prefix}{child.id}"
                        )
                    elif child.type == "outport":
                        subsystem_outport_map[block.id][int(port_num) - 1] = (
                            f"{child_prefix}{child.id}"
                        )

                child_name_prefix = (
                    f"{name_prefix}/{block.name}" if name_prefix else block.name
                )
                child_blocks, child_connections = flatten_level(
                    block.children,
                    block.child_connections or [],
                    child_prefix,
                    child_name_prefix,
                )
                flattened_blocks.extend(child_blocks)
                flattened_connections.extend(child_connections)

            for conn in level_connections:
                source_id = conn.source_block_id
                target_id = conn.target_block_id
                source_idx = port_index(conn.source_port_id)
                target_idx = port_index(conn.target_port_id)

                if source_id in flattened_subsystems:
                    if source_idx is None:
                        continue
                    new_source_id = subsystem_outport_map[source_id].get(source_idx)
                    if new_source_id is None:
                        continue
                    new_source_port = f"{new_source_id}-out-0"
                else:
                    new_source_id = f"{prefix}{source_id}"
                    new_source_port = prefixed_port_id(
                        conn.source_port_id, source_id, new_source_id
                    )

                if target_id in flattened_subsystems:
                    if target_idx is None:
                        continue
                    new_target_id = subsystem_inport_map[target_id].get(target_idx)
                    if new_target_id is None:
                        continue
                    new_target_port = f"{new_target_id}-in-0"
                else:
                    new_target_id = f"{prefix}{target_id}"
                    new_target_port = prefixed_port_id(
                        conn.target_port_id, target_id, new_target_id
                    )

                flattened_connections.append(
                    Connection(
                        id=f"{prefix}{conn.id}",
                        source_block_id=new_source_id,
                        source_port_id=new_source_port,
                        target_block_id=new_target_id,
                        target_port_id=new_target_port,
                    )
                )

            return flattened_blocks, flattened_connections

        return flatten_level(blocks, connections)
