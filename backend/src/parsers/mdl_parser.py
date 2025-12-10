"""MDL Parser - Imports Simulink .mdl model files.

The MDL format is a text-based format used by older versions of Simulink.
It contains hierarchical block/system definitions with parameters.

Example MDL structure:
    Model {
      Name "mymodel"
      System {
        Name "mymodel"
        Block {
          BlockType Gain
          Name "Gain1"
          Position [100, 100, 130, 130]
          Gain "2"
        }
        Line {
          SrcBlock "Step"
          SrcPort 1
          DstBlock "Gain1"
          DstPort 1
        }
      }
    }
"""

import re
import uuid
from typing import Dict, List, Any, Tuple
from datetime import datetime

from ..models.model import Model, ModelMetadata
from ..models.block import Block, Connection, Port, Position
from ..models.simulation import SimulationConfig


class MDLParser:
    """Parser for Simulink MDL files."""

    # Mapping from Simulink block types to LibreSim types
    BLOCK_TYPE_MAP = {
        "Constant": "constant",
        "Step": "step",
        "Ramp": "ramp",
        "Sin": "sine_wave",
        "Clock": "clock",
        "Scope": "scope",
        "Display": "display",
        "ToWorkspace": "to_workspace",
        "Terminator": "terminator",
        "Integrator": "integrator",
        "Derivative": "derivative",
        "TransferFcn": "transfer_function",
        "StateSpace": "state_space",
        "PID Controller": "pid_controller",
        "Gain": "gain",
        "Sum": "sum",
        "Product": "product",
        "Abs": "abs",
        "Saturate": "saturation",
        "Saturation": "saturation",
        "UnitDelay": "unit_delay",
        "ZeroOrderHold": "zero_order_hold",
        "Mux": "mux",
        "Demux": "demux",
        "Switch": "switch",
        "Goto": "goto",
        "From": "from",
    }

    def __init__(self):
        self._content = ""
        self._pos = 0
        self._blocks: List[Dict[str, Any]] = []
        self._lines: List[Dict[str, Any]] = []

    def parse(self, content: str, filename: str = "imported.mdl") -> Model:
        """Parse an MDL file and return a LibreSim Model.

        Args:
            content: The MDL file content as a string
            filename: Original filename for metadata

        Returns:
            A LibreSim Model object
        """
        self._content = content
        self._pos = 0
        self._blocks = []
        self._lines = []

        # Parse the MDL structure
        model_data = self._parse_block()

        # Extract model name
        model_name = self._get_value(model_data, "Name", filename.replace(".mdl", ""))

        # Find the main system
        system_data = self._find_system(model_data)

        # Parse blocks from the system
        blocks = self._parse_blocks(system_data)

        # Parse connections (lines) from the system
        connections = self._parse_connections(system_data, blocks)

        # Create simulation config from model parameters
        sim_config = self._parse_simulation_config(model_data)

        # Create the Model object
        model = Model(
            id=str(uuid.uuid4()),
            metadata=ModelMetadata(
                name=model_name,
                description=f"Imported from {filename}",
                author="MDL Import",
                createdAt=datetime.now(),
                modifiedAt=datetime.now(),
            ),
            blocks=blocks,
            connections=connections,
            simulationConfig=sim_config,
        )

        return model

    def _parse_block(self) -> Dict[str, Any]:
        """Parse a block (hierarchical key-value structure)."""
        result: Dict[str, Any] = {}

        self._skip_whitespace()

        while self._pos < len(self._content):
            self._skip_whitespace()

            if self._pos >= len(self._content):
                break

            char = self._content[self._pos]

            # End of current block
            if char == "}":
                self._pos += 1
                break

            # Parse key
            key = self._parse_key()
            if not key:
                self._pos += 1
                continue

            self._skip_whitespace()

            if self._pos >= len(self._content):
                break

            # Check if value is a nested block or a simple value
            if self._content[self._pos] == "{":
                self._pos += 1
                value = self._parse_block()

                # Handle multiple blocks with same key (e.g., multiple Block entries)
                if key in result:
                    if isinstance(result[key], list):
                        result[key].append(value)
                    else:
                        result[key] = [result[key], value]
                else:
                    result[key] = value
            else:
                value = self._parse_value()
                result[key] = value

        return result

    def _parse_key(self) -> str:
        """Parse a key (identifier)."""
        self._skip_whitespace()
        start = self._pos

        while self._pos < len(self._content):
            char = self._content[self._pos]
            if char.isalnum() or char == "_":
                self._pos += 1
            else:
                break

        return self._content[start : self._pos]

    def _parse_value(self) -> str:
        """Parse a value (string, number, or quoted string)."""
        self._skip_whitespace()

        if self._pos >= len(self._content):
            return ""

        # Quoted string
        if self._content[self._pos] == '"':
            return self._parse_quoted_string()

        # Array/matrix value
        if self._content[self._pos] == "[":
            return self._parse_array()

        # Unquoted value (until newline or whitespace)
        start = self._pos
        while self._pos < len(self._content):
            char = self._content[self._pos]
            if char in "\n\r\t " or char == "}":
                break
            self._pos += 1

        return self._content[start : self._pos].strip()

    def _parse_quoted_string(self) -> str:
        """Parse a quoted string."""
        self._pos += 1  # Skip opening quote
        start = self._pos
        escaped = False

        while self._pos < len(self._content):
            char = self._content[self._pos]
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                result = self._content[start : self._pos]
                self._pos += 1  # Skip closing quote
                return result
            self._pos += 1

        return self._content[start : self._pos]

    def _parse_array(self) -> str:
        """Parse an array/matrix value [...]."""
        start = self._pos
        depth = 0

        while self._pos < len(self._content):
            char = self._content[self._pos]
            if char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
                if depth == 0:
                    self._pos += 1
                    return self._content[start : self._pos]
            self._pos += 1

        return self._content[start : self._pos]

    def _skip_whitespace(self):
        """Skip whitespace and comments."""
        while self._pos < len(self._content):
            char = self._content[self._pos]
            if char in " \t\n\r":
                self._pos += 1
            elif char == "#":
                # Skip comment line
                while self._pos < len(self._content) and self._content[self._pos] != "\n":
                    self._pos += 1
            else:
                break

    def _get_value(self, data: Dict, key: str, default: str = "") -> str:
        """Get a value from parsed data, with default."""
        return data.get(key, default)

    def _find_system(self, model_data: Dict) -> Dict:
        """Find the main System block in the model."""
        system = model_data.get("System", {})
        if isinstance(system, list):
            return system[0] if system else {}
        return system

    def _parse_blocks(self, system_data: Dict) -> List[Block]:
        """Parse all blocks from the system."""
        blocks = []
        block_data = system_data.get("Block", [])

        if isinstance(block_data, dict):
            block_data = [block_data]

        for i, bd in enumerate(block_data):
            block = self._convert_block(bd, i)
            if block:
                blocks.append(block)

        return blocks

    def _convert_block(self, block_data: Dict, index: int) -> Block | None:
        """Convert an MDL block to a LibreSim Block."""
        block_type_mdl = block_data.get("BlockType", "")
        block_type = self.BLOCK_TYPE_MAP.get(block_type_mdl)

        if not block_type:
            # Unknown block type, skip
            return None

        name = block_data.get("Name", f"Block{index}")
        block_id = str(uuid.uuid4())

        # Parse position
        position = self._parse_position(block_data.get("Position", "[0, 0, 100, 50]"))

        # Parse parameters
        parameters = self._extract_parameters(block_data, block_type)

        # Create ports based on block type
        input_ports, output_ports = self._create_ports(block_type, block_id, parameters)

        return Block(
            id=block_id,
            type=block_type,
            name=name,
            position=position,
            parameters=parameters,
            inputPorts=input_ports,
            outputPorts=output_ports,
        )

    def _parse_position(self, pos_str: str) -> Position:
        """Parse position from MDL format [left, top, right, bottom]."""
        # Remove brackets and split
        pos_str = pos_str.strip("[]")
        parts = [p.strip() for p in pos_str.split(",")]

        if len(parts) >= 2:
            try:
                x = float(parts[0])
                y = float(parts[1])
                return Position(x=x, y=y)
            except ValueError:
                pass

        return Position(x=100.0, y=100.0)

    def _extract_parameters(self, block_data: Dict, block_type: str) -> Dict[str, Any]:
        """Extract block parameters from MDL data."""
        params: Dict[str, Any] = {}

        # Map MDL parameter names to LibreSim parameter names
        param_map = {
            "constant": {"Value": "value"},
            "step": {
                "Time": "stepTime",
                "Before": "initialValue",
                "After": "finalValue",
            },
            "sine_wave": {
                "Amplitude": "amplitude",
                "Frequency": "frequency",
                "Phase": "phase",
                "Bias": "bias",
            },
            "gain": {"Gain": "gain"},
            "sum": {"Inputs": "signs"},
            "integrator": {"InitialCondition": "initialCondition"},
            "transfer_function": {
                "Numerator": "numerator",
                "Denominator": "denominator",
            },
            "saturation": {
                "UpperLimit": "upperLimit",
                "LowerLimit": "lowerLimit",
            },
        }

        type_params = param_map.get(block_type, {})

        for mdl_name, lib_name in type_params.items():
            if mdl_name in block_data:
                value = block_data[mdl_name]
                # Try to convert to appropriate type
                params[lib_name] = self._convert_value(value)

        return params

    def _convert_value(self, value: str) -> Any:
        """Convert a string value to appropriate Python type."""
        if not value:
            return value

        # Try float
        try:
            return float(value)
        except ValueError:
            pass

        # Try parsing as array
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1]
            parts = [p.strip() for p in inner.split(",")]
            try:
                return [float(p) for p in parts if p]
            except ValueError:
                pass

        return value

    def _create_ports(
        self, block_type: str, block_id: str, parameters: Dict
    ) -> Tuple[List[Port], List[Port]]:
        """Create input and output ports based on block type."""
        input_ports = []
        output_ports = []

        # Define port configurations for each block type
        port_configs = {
            "constant": ([], [{"name": "out"}]),
            "step": ([], [{"name": "out"}]),
            "ramp": ([], [{"name": "out"}]),
            "sine_wave": ([], [{"name": "out"}]),
            "clock": ([], [{"name": "out"}]),
            "scope": ([{"name": "in"}], []),
            "display": ([{"name": "in"}], []),
            "to_workspace": ([{"name": "in"}], []),
            "terminator": ([{"name": "in"}], []),
            "integrator": ([{"name": "in"}], [{"name": "out"}]),
            "derivative": ([{"name": "in"}], [{"name": "out"}]),
            "transfer_function": ([{"name": "in"}], [{"name": "out"}]),
            "state_space": ([{"name": "in"}], [{"name": "out"}]),
            "pid_controller": ([{"name": "in"}], [{"name": "out"}]),
            "gain": ([{"name": "in"}], [{"name": "out"}]),
            "sum": ([{"name": "in1"}, {"name": "in2"}], [{"name": "out"}]),
            "product": ([{"name": "in1"}, {"name": "in2"}], [{"name": "out"}]),
            "abs": ([{"name": "in"}], [{"name": "out"}]),
            "saturation": ([{"name": "in"}], [{"name": "out"}]),
            "unit_delay": ([{"name": "in"}], [{"name": "out"}]),
            "zero_order_hold": ([{"name": "in"}], [{"name": "out"}]),
            "mux": ([{"name": "in1"}, {"name": "in2"}], [{"name": "out"}]),
            "demux": ([{"name": "in"}], [{"name": "out1"}, {"name": "out2"}]),
            "switch": (
                [{"name": "in1"}, {"name": "control"}, {"name": "in2"}],
                [{"name": "out"}],
            ),
        }

        in_config, out_config = port_configs.get(block_type, ([], []))

        for i, pc in enumerate(in_config):
            input_ports.append(
                Port(
                    id=f"{block_id}-in-{i}",
                    name=pc["name"],
                    dataType="double",
                    dimensions=[1],
                )
            )

        for i, pc in enumerate(out_config):
            output_ports.append(
                Port(
                    id=f"{block_id}-out-{i}",
                    name=pc["name"],
                    dataType="double",
                    dimensions=[1],
                )
            )

        return input_ports, output_ports

    def _parse_connections(
        self, system_data: Dict, blocks: List[Block]
    ) -> List[Connection]:
        """Parse connections (Lines) from the system."""
        connections = []
        line_data = system_data.get("Line", [])

        if isinstance(line_data, dict):
            line_data = [line_data]

        # Create block name to block mapping
        block_map = {b.name: b for b in blocks}

        for ld in line_data:
            conn = self._convert_connection(ld, block_map)
            if conn:
                connections.append(conn)

        return connections

    def _convert_connection(
        self, line_data: Dict, block_map: Dict[str, Block]
    ) -> Connection | None:
        """Convert an MDL Line to a LibreSim Connection."""
        src_block_name = line_data.get("SrcBlock", "")
        src_port = int(line_data.get("SrcPort", 1)) - 1  # MDL uses 1-based indexing
        dst_block_name = line_data.get("DstBlock", "")
        dst_port = int(line_data.get("DstPort", 1)) - 1

        src_block = block_map.get(src_block_name)
        dst_block = block_map.get(dst_block_name)

        if not src_block or not dst_block:
            return None

        # Get port IDs
        if src_port >= len(src_block.output_ports):
            return None
        if dst_port >= len(dst_block.input_ports):
            return None

        src_port_id = src_block.output_ports[src_port].id
        dst_port_id = dst_block.input_ports[dst_port].id

        return Connection(
            id=str(uuid.uuid4()),
            sourceBlockId=src_block.id,
            sourcePortId=src_port_id,
            targetBlockId=dst_block.id,
            targetPortId=dst_port_id,
        )

    def _parse_simulation_config(self, model_data: Dict) -> SimulationConfig:
        """Extract simulation configuration from model data."""
        start_time = float(model_data.get("StartTime", 0))
        stop_time = float(model_data.get("StopTime", 10))

        solver_map = {
            "ode45": "rk4",
            "ode23": "rk4",
            "ode4": "rk4",
            "ode1": "euler",
            "FixedStepDiscrete": "euler",
        }
        mdl_solver = model_data.get("Solver", "ode45")
        solver = solver_map.get(mdl_solver, "rk4")

        return SimulationConfig(
            solver=solver,
            startTime=start_time,
            stopTime=stop_time,
            stepSize=float(model_data.get("FixedStep", 0.01)),
        )
