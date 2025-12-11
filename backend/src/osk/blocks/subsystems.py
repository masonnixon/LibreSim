"""Subsystem blocks for OSK-based simulation.

Provides Inport, Outport, and Subsystem blocks for hierarchical model organization.
Note: During simulation, subsystems are typically "flattened" - their internal
blocks are expanded into the main simulation with appropriate signal routing.
These blocks primarily serve as interface points for the flattening process.
"""

from ..block import Block
from ..state import State


class Inport(Block):
    """Subsystem input port - receives signal from parent level.

    When a subsystem is flattened, the Inport block is replaced with
    a direct connection to the signal feeding into the subsystem's
    corresponding input port.
    """

    def __init__(self, port_number=1):
        super().__init__()
        self.port_number = port_number
        self.output = 0.0
        self.input = 0.0
        self.input_block = None

    def init(self):
        self.output = 0.0
        self.input = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput()
        self.output = self.input

    def getOutput(self, port=0):
        return self.output


class Outport(Block):
    """Subsystem output port - sends signal to parent level.

    When a subsystem is flattened, the Outport block is replaced with
    a direct connection from the internal signal to the subsystem's
    corresponding output port destination.
    """

    def __init__(self, port_number=1):
        super().__init__()
        self.port_number = port_number
        self.output = 0.0
        self.input = 0.0
        self.input_block = None

    def init(self):
        self.output = 0.0
        self.input = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput()
        self.output = self.input

    def getOutput(self, port=0):
        return self.output


class Subsystem(Block):
    """Subsystem container block.

    This block represents a collection of blocks that are grouped together.
    During simulation setup, subsystems are "flattened" - their internal
    blocks are extracted and added to the main simulation with proper
    signal routing through Inport/Outport blocks.

    The Subsystem block itself doesn't perform simulation; it's a
    structural element for model organization. The OSK adapter handles
    the flattening process before simulation begins.
    """

    def __init__(self, num_inputs=0, num_outputs=0, **kwargs):
        super().__init__()
        self.num_inputs = num_inputs
        self.num_outputs = num_outputs
        self.inputs = [0.0] * max(num_inputs, 1)
        self.outputs = [0.0] * max(num_outputs, 1)
        self.input_blocks = [None] * max(num_inputs, 1)
        # Internal blocks and connections are handled by the adapter
        # during flattening - this block just passes through signals
        # for any case where it's used directly without flattening

    def init(self):
        self.inputs = [0.0] * len(self.inputs)
        self.outputs = [0.0] * len(self.outputs)

    def setInput(self, value, port=0):
        if port < len(self.inputs):
            self.inputs[port] = value

    def connectInput(self, block, port=0):
        if port < len(self.input_blocks):
            self.input_blocks[port] = block

    def update(self):
        # Get inputs from connected blocks
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                self.inputs[i] = block.getOutput()

        # In flattened mode, this block shouldn't be called
        # but if it is, just pass inputs to outputs
        for i in range(min(len(self.inputs), len(self.outputs))):
            self.outputs[i] = self.inputs[i]

    def getOutput(self, port=0):
        if port < len(self.outputs):
            return self.outputs[port]
        return 0.0
