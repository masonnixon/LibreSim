"""Subsystem blocks for OSK-based simulation.

Provides Inport, Outport, and Subsystem blocks for hierarchical model organization.
Note: During simulation, subsystems are typically "flattened" - their internal
blocks are expanded into the main simulation with appropriate signal routing.
These blocks primarily serve as interface points for the flattening process.
"""

from ..block import Block


class Inport(Block):
    """Subsystem input port - receives signal from parent level.

    When a subsystem is flattened, the Inport block is replaced with
    a direct connection to the signal feeding into the subsystem's
    corresponding input port. Supports both scalar and vector signals.
    """

    def __init__(self, port_number=1):
        super().__init__()
        # Ensure port_number is an integer (may come as float from JSON)
        self.port_number = int(port_number)
        self.output = 0.0
        self.input = 0.0
        self.input_block = None
        self._output_vector = None  # For vector pass-through

    def init(self):
        self.output = 0.0
        self.input = 0.0
        self._output_vector = None

    def setInput(self, value, port=0):
        if isinstance(value, (list, tuple)):
            self._output_vector = list(value)
            self.input = value[0] if value else 0.0
        else:
            self.input = value
            self._output_vector = None

    def connectInput(self, block, port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            # Check if source has vector output
            if hasattr(self.input_block, 'getOutputVector'):
                self._output_vector = self.input_block.getOutputVector()
                self.input = self._output_vector[0] if self._output_vector else 0.0
            else:
                self.input = self.input_block.getOutput()
                self._output_vector = None
        self.output = self.input

    def getOutput(self, port=0):
        return self.output

    def getOutputVector(self):
        """Get vector output if available."""
        return self._output_vector.copy() if self._output_vector else None


class Outport(Block):
    """Subsystem output port - sends signal to parent level.

    When a subsystem is flattened, the Outport block is replaced with
    a direct connection from the internal signal to the subsystem's
    corresponding output port destination. Supports both scalar and vector signals.
    """

    def __init__(self, port_number=1):
        super().__init__()
        # Ensure port_number is an integer (may come as float from JSON)
        self.port_number = int(port_number)
        self.output = 0.0
        self.input = 0.0
        self.input_block = None
        self._output_vector = None  # For vector pass-through

    def init(self):
        self.output = 0.0
        self.input = 0.0
        self._output_vector = None

    def setInput(self, value, port=0):
        if isinstance(value, (list, tuple)):
            self._output_vector = list(value)
            self.input = value[0] if value else 0.0
        else:
            self.input = value
            self._output_vector = None

    def connectInput(self, block, port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            # Check if source has vector output
            if hasattr(self.input_block, 'getOutputVector'):
                self._output_vector = self.input_block.getOutputVector()
                self.input = self._output_vector[0] if self._output_vector else 0.0
            else:
                self.input = self.input_block.getOutput()
                self._output_vector = None
        self.output = self.input

    def getOutput(self, port=0):
        return self.output

    def getOutputVector(self):
        """Get vector output if available."""
        return self._output_vector.copy() if self._output_vector else None


class Subsystem(Block):
    """Subsystem container block.

    This block represents a collection of blocks that are grouped together.
    During simulation setup, subsystems are "flattened" - their internal
    blocks are extracted and added to the main simulation with proper
    signal routing through Inport/Outport blocks.

    The Subsystem block itself doesn't perform simulation; it's a
    structural element for model organization. The OSK adapter handles
    the flattening process before simulation begins.

    Supports both scalar and vector signals on inputs/outputs.
    """

    def __init__(self, num_inputs=0, num_outputs=0, **kwargs):
        super().__init__()
        # Ensure num_inputs and num_outputs are integers (may come as float from JSON)
        self.num_inputs = int(num_inputs)
        self.num_outputs = int(num_outputs)
        self.inputs = [0.0] * max(self.num_inputs, 1)
        self.outputs = [0.0] * max(self.num_outputs, 1)
        self.input_blocks = [None] * max(self.num_inputs, 1)
        # Track vector outputs for each port
        self._output_vectors = {}  # port -> vector
        # Internal blocks and connections are handled by the adapter
        # during flattening - this block just passes through signals
        # for any case where it's used directly without flattening
        # Reference to outport blocks for vector retrieval
        self._outport_blocks = {}  # port_number -> outport block

    def init(self):
        self.inputs = [0.0] * len(self.inputs)
        self.outputs = [0.0] * len(self.outputs)
        self._output_vectors = {}

    def setInput(self, value, port=0):
        if port < len(self.inputs):
            self.inputs[port] = value

    def connectInput(self, block, port=0):
        if port < len(self.input_blocks):
            self.input_blocks[port] = block

    def setOutportBlock(self, port_number, block):
        """Register an outport block for vector output retrieval."""
        self._outport_blocks[port_number] = block

    def update(self):
        # Get inputs from connected blocks
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                self.inputs[i] = block.getOutput()

        # In flattened mode, this block shouldn't be called
        # but if it is, just pass inputs to outputs
        for i in range(min(len(self.inputs), len(self.outputs))):
            self.outputs[i] = self.inputs[i]

        # Update output vectors from outport blocks
        for port_num, outport in self._outport_blocks.items():
            if hasattr(outport, 'getOutputVector'):
                vec = outport.getOutputVector()
                if vec is not None:
                    self._output_vectors[port_num - 1] = vec  # port_number is 1-indexed

    def getOutput(self, port=0):
        if port < len(self.outputs):
            return self.outputs[port]
        return 0.0

    def getOutputVector(self, port=0):
        """Get vector output for a port if available."""
        if port in self._output_vectors:
            return self._output_vectors[port].copy()
        return None
