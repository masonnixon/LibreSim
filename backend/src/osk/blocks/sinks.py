"""Sink blocks for OSK-based simulation."""

from ..block import Block
from ..state import State


class Scope(Block):
    """Scope block - records signal over time.

    Supports multiple inputs and tracks the source block name for each input
    to enable legend display in the visualization. Also handles vector inputs
    from Mux blocks, expanding them into separate traces.

    Only records and displays data for inputs that are actually connected.
    """

    def __init__(self, num_inputs=1, **kwargs):
        # Accept **kwargs to ignore extra params like sampleTime from frontend
        super().__init__()
        # Ensure num_inputs is an integer (may come as float from JSON)
        self.num_inputs = int(num_inputs)
        self.inputs = [0.0] * self.num_inputs
        self.input_blocks = [None] * self.num_inputs
        self.input_source_ports = [
            0
        ] * self.num_inputs  # Track which output port to read from source
        self.input_names = [f"Input {i + 1}" for i in range(self.num_inputs)]
        self.times = []
        self.values = []  # Will be built dynamically based on connected inputs
        # Track vector inputs (expanded from Mux blocks)
        self._vector_inputs = {}  # port -> list of values
        self._vector_names = {}  # port -> list of names
        self._total_traces = 0

    def init(self):
        self.times = []
        self.values = []
        self._vector_inputs = {}
        self._vector_names = {}
        self._total_traces = 0

    def setInput(self, value, port=0):
        if port < self.num_inputs:
            if isinstance(value, (list, tuple)):
                self._vector_inputs[port] = list(value)
                self.inputs[port] = value[0] if value else 0.0
            else:
                self.inputs[port] = value
                if port in self._vector_inputs:
                    del self._vector_inputs[port]

    def connectInput(self, block, port=0, source_port=0):
        """Connect an input block.

        Args:
            block: The source block to connect
            port: Which input port on this Scope to connect to
            source_port: Which output port on the source block to read from
        """
        if port < self.num_inputs:
            self.input_blocks[port] = block
            self.input_source_ports[port] = source_port

    def setInputName(self, name, port=0):
        """Set a display name for an input (used for legend)."""
        if port < self.num_inputs:
            self.input_names[port] = name

    def update(self):
        # Get inputs from connected blocks
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                # Get the source port index for this input
                source_port = self.input_source_ports[i] if i < len(self.input_source_ports) else 0

                # Check if source is a multi-output block (like Demux) where each port is scalar
                # Demux has getOutputVector() that returns all outputs, but each port is scalar
                # Note: Selector is NOT included here because it genuinely outputs a vector
                # when multiple indices are selected (single output port with vector value)
                is_multi_output_block = block.__class__.__name__ == "Demux"

                # Check if source has vector output (Mux, Outport with vector, etc.)
                # BUT skip vector handling for multi-output blocks - their outputs are scalars
                vec = None
                if hasattr(block, "getOutputVector") and not is_multi_output_block:
                    vec = block.getOutputVector()

                if vec is not None and len(vec) > 1:
                    # Vector signal detected
                    self._vector_inputs[i] = vec
                    self.inputs[i] = vec[0] if vec else 0.0
                    # Generate indexed names for vector elements
                    if i not in self._vector_names or len(self._vector_names[i]) != len(vec):
                        base_name = (
                            self.input_names[i] if i < len(self.input_names) else f"Input {i + 1}"
                        )
                        self._vector_names[i] = [f"{base_name}[{j + 1}]" for j in range(len(vec))]
                else:
                    # Scalar signal - use source_port to get correct output from multi-output blocks
                    self.inputs[i] = block.getOutput(source_port)
                    if i in self._vector_inputs:
                        del self._vector_inputs[i]
                        del self._vector_names[i]

    def rpt(self):
        # Record data when ready - only for connected inputs
        if State.ready:
            self.times.append(State.t)

            # Calculate total number of traces needed (only connected inputs)
            total_traces = 0
            for i in range(self.num_inputs):
                if self.input_blocks[i] is not None:  # Only count connected inputs
                    if i in self._vector_inputs:
                        total_traces += len(self._vector_inputs[i])
                    else:
                        total_traces += 1

            # Initialize values array if needed
            if len(self.values) != total_traces:
                self.values = [[] for _ in range(total_traces)]

            # Record values, expanding vectors - only for connected inputs
            trace_idx = 0
            for i in range(self.num_inputs):
                if self.input_blocks[i] is not None:  # Only record connected inputs
                    if i in self._vector_inputs:
                        for val in self._vector_inputs[i]:
                            if trace_idx < len(self.values):
                                self.values[trace_idx].append(val)
                            trace_idx += 1
                    else:
                        if trace_idx < len(self.values):
                            self.values[trace_idx].append(self.inputs[i])
                        trace_idx += 1

            self._total_traces = total_traces

    def getData(self):
        """Get recorded data with input names for legend."""
        # Build the list of input names for connected inputs only
        all_names = []
        for i in range(self.num_inputs):
            if self.input_blocks[i] is not None:  # Only include connected inputs
                if i in self._vector_names:
                    all_names.extend(self._vector_names[i])
                elif i < len(self.input_names):
                    all_names.append(self.input_names[i])
                else:
                    all_names.append(f"Input {i + 1}")

        return {
            "times": self.times,
            "values": self.values,
            "inputNames": all_names,
            "numInputs": len(self.values),  # Return actual number of traces
        }

    def getOutput(self, port=0):
        if port < self.num_inputs:
            return self.inputs[port]
        return 0.0


class ToWorkspace(Block):
    """ToWorkspace block - logs signal to output data."""

    def __init__(self, variable_name="simout"):
        super().__init__()
        self.variable_name = variable_name
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.times = []
        self.values = []

    def init(self):
        self.times = []
        self.values = []

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0, source_port=0):
        """Connect an input block."""
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput(self.input_source_port)

    def rpt(self):
        if State.ready:
            self.times.append(State.t)
            self.values.append(self.input)

    def getData(self):
        """Get logged data."""
        return {"name": self.variable_name, "times": self.times, "values": self.values}

    def getOutput(self, port=0):
        return self.input


class Display(Block):
    """Display block - shows current signal value."""

    def __init__(self):
        super().__init__()
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.current_value = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput(self.input_source_port)

    def rpt(self):
        if State.ready:
            self.current_value = self.input

    def getOutput(self, port=0):
        return self.current_value


class Terminator(Block):
    """Terminator block - terminates unconnected outputs."""

    def __init__(self):
        super().__init__()
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        # Absorb the signal - optionally read from input block
        if self.input_block is not None:
            self.input = self.input_block.getOutput(self.input_source_port)

    def getOutput(self, port=0):
        return 0.0


class Scope3D(Block):
    """3D Scope block - records X, Y, Z signals for 3D visualization.

    Supports three inputs (X, Y, Z) and records them over time for
    3D trajectory or scatter plot visualization.
    """

    def __init__(self, x_label="X", y_label="Y", z_label="Z", **kwargs):
        super().__init__()
        self.x_label = x_label
        self.y_label = y_label
        self.z_label = z_label
        self.inputs = [0.0, 0.0, 0.0]  # X, Y, Z
        self.input_blocks = [None, None, None]
        self.input_source_ports = [0, 0, 0]
        self.times = []
        self.x_values = []
        self.y_values = []
        self.z_values = []

    def init(self):
        self.times = []
        self.x_values = []
        self.y_values = []
        self.z_values = []

    def setInput(self, value, port=0):
        if port < 3:
            self.inputs[port] = value

    def connectInput(self, block, port=0, source_port=0):
        """Connect an input block.

        Args:
            block: The source block to connect
            port: Which input port (0=X, 1=Y, 2=Z)
            source_port: Which output port on the source block to read from
        """
        if port < 3:
            self.input_blocks[port] = block
            self.input_source_ports[port] = source_port

    def update(self):
        # Get inputs from connected blocks
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                source_port = self.input_source_ports[i]
                self.inputs[i] = block.getOutput(source_port)

    def rpt(self):
        # Record data when ready
        if State.ready:
            self.times.append(State.t)
            self.x_values.append(self.inputs[0])
            self.y_values.append(self.inputs[1])
            self.z_values.append(self.inputs[2])

    def getData(self):
        """Get recorded 3D data."""
        return {
            "times": self.times,
            "x": self.x_values,
            "y": self.y_values,
            "z": self.z_values,
            "inputNames": [self.x_label, self.y_label, self.z_label],
        }

    def getOutput(self, port=0):
        if port < 3:
            return self.inputs[port]
        return 0.0
