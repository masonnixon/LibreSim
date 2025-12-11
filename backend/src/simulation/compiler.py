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
        self, blocks: List[Block], input_connections: Dict[str, List[str]],
        for_algebraic_loop_detection: bool = False
    ) -> Dict[str, Set[str]]:
        """Build graph of block dependencies (block -> set of blocks it depends on).

        Args:
            blocks: List of blocks
            input_connections: Map of block_id -> list of input connections
            for_algebraic_loop_detection: If True, excludes dependencies through
                state-holding blocks (integrators, etc.) since they break algebraic loops.

        Returns:
            Dictionary mapping block_id -> set of block_ids it depends on
        """
        dependencies: Dict[str, Set[str]] = {b.id: set() for b in blocks}
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

    def _flatten_subsystems(
        self, blocks: List[Block], connections: List[Connection]
    ) -> tuple[List[Block], List[Connection]]:
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
        flattened_blocks: List[Block] = []
        flattened_connections: List[Connection] = list(connections)

        # Track subsystem input/output mappings for connection rewiring
        # subsystem_id -> port_index -> internal_block_id
        subsystem_inport_map: Dict[str, Dict[int, str]] = {}
        subsystem_outport_map: Dict[str, Dict[int, str]] = {}

        for block in blocks:
            if block.type != "subsystem" or not block.children:
                # Not a subsystem or no children, keep as-is
                flattened_blocks.append(block)
                continue

            # This is a subsystem with children - flatten it
            subsystem_id = block.id
            subsystem_inport_map[subsystem_id] = {}
            subsystem_outport_map[subsystem_id] = {}

            # Add child blocks with prefixed IDs
            for child in block.children:
                # Create a new block with prefixed ID
                prefixed_id = f"{subsystem_id}__{child.id}"
                child_copy = Block(
                    id=prefixed_id,
                    type=child.type,
                    name=f"{block.name}/{child.name}",
                    position=child.position,
                    parameters=child.parameters,
                    input_ports=child.input_ports,
                    output_ports=child.output_ports,
                )
                flattened_blocks.append(child_copy)

                # Track inport/outport mappings
                if child.type == "inport":
                    port_num = child.parameters.get("portNumber", 1)
                    if isinstance(port_num, (int, float)):
                        subsystem_inport_map[subsystem_id][int(port_num) - 1] = prefixed_id
                elif child.type == "outport":
                    port_num = child.parameters.get("portNumber", 1)
                    if isinstance(port_num, (int, float)):
                        subsystem_outport_map[subsystem_id][int(port_num) - 1] = prefixed_id

            # Add child connections with prefixed IDs
            if block.child_connections:
                for conn in block.child_connections:
                    prefixed_conn = Connection(
                        id=f"{subsystem_id}__{conn.id}",
                        source_block_id=f"{subsystem_id}__{conn.source_block_id}",
                        source_port_id=conn.source_port_id,
                        target_block_id=f"{subsystem_id}__{conn.target_block_id}",
                        target_port_id=conn.target_port_id,
                    )
                    flattened_connections.append(prefixed_conn)

        # Now rewire connections that went to/from subsystems
        rewired_connections: List[Connection] = []
        for conn in flattened_connections:
            source_id = conn.source_block_id
            target_id = conn.target_block_id
            new_source_id = source_id
            new_target_id = target_id
            new_source_port = conn.source_port_id
            new_target_port = conn.target_port_id

            # Check if source is a subsystem - rewire to outport
            if source_id in subsystem_outport_map:
                # Parse port index from port ID (e.g., "block-out-0" -> 0)
                try:
                    port_idx = int(conn.source_port_id.split("-")[-1])
                    if port_idx in subsystem_outport_map[source_id]:
                        outport_id = subsystem_outport_map[source_id][port_idx]
                        new_source_id = outport_id
                        # Outport has a single input, so we connect from its output
                        new_source_port = f"{outport_id}-out-0"
                except (ValueError, IndexError):
                    pass

            # Check if target is a subsystem - rewire to inport
            if target_id in subsystem_inport_map:
                try:
                    port_idx = int(conn.target_port_id.split("-")[-1])
                    if port_idx in subsystem_inport_map[target_id]:
                        inport_id = subsystem_inport_map[target_id][port_idx]
                        new_target_id = inport_id
                        # Inport takes input on port 0
                        new_target_port = f"{inport_id}-in-0"
                except (ValueError, IndexError):
                    pass

            # Skip connections that still reference subsystem blocks (they're removed)
            if new_source_id in subsystem_inport_map or new_target_id in subsystem_outport_map:
                continue

            rewired_connections.append(Connection(
                id=conn.id,
                source_block_id=new_source_id,
                source_port_id=new_source_port,
                target_block_id=new_target_id,
                target_port_id=new_target_port,
            ))

        return flattened_blocks, rewired_connections
