"""Sink blocks for OSK-based simulation."""

from ..block import Block
from ..state import State


class Scope(Block):
    """Scope block - records signal over time."""

    def __init__(self, num_inputs=1, **kwargs):
        # Accept **kwargs to ignore extra params like sampleTime from frontend
        super().__init__()
        self.num_inputs = num_inputs
        self.inputs = [0.0] * num_inputs
        self.input_blocks = [None] * num_inputs
        self.times = []
        self.values = [[] for _ in range(num_inputs)]

    def init(self):
        self.times = []
        self.values = [[] for _ in range(self.num_inputs)]

    def setInput(self, value, port=0):
        if port < self.num_inputs:
            self.inputs[port] = value

    def connectInput(self, block, port=0):
        """Connect an input block."""
        if port < self.num_inputs:
            self.input_blocks[port] = block

    def update(self):
        # Get inputs from connected blocks
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                self.inputs[i] = block.getOutput()

    def rpt(self):
        # Record data when ready
        if State.ready:
            self.times.append(State.t)
            for i in range(self.num_inputs):
                self.values[i].append(self.inputs[i])

    def getData(self):
        """Get recorded data."""
        return {
            'times': self.times,
            'values': self.values
        }

    def getOutput(self, port=0):
        if port < self.num_inputs:
            return self.inputs[port]
        return 0.0


class ToWorkspace(Block):
    """ToWorkspace block - logs signal to output data."""

    def __init__(self, variable_name='simout'):
        super().__init__()
        self.variable_name = variable_name
        self.input = 0.0
        self.input_block = None
        self.times = []
        self.values = []

    def init(self):
        self.times = []
        self.values = []

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0):
        """Connect an input block."""
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput()

    def rpt(self):
        if State.ready:
            self.times.append(State.t)
            self.values.append(self.input)

    def getData(self):
        """Get logged data."""
        return {
            'name': self.variable_name,
            'times': self.times,
            'values': self.values
        }

    def getOutput(self, port=0):
        return self.input


class Display(Block):
    """Display block - shows current signal value."""

    def __init__(self):
        super().__init__()
        self.input = 0.0
        self.input_block = None
        self.current_value = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0):
        self.input_block = block

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput()

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

    def setInput(self, value, port=0):
        self.input = value

    def update(self):
        pass  # Do nothing - just absorb the signal

    def getOutput(self, port=0):
        return 0.0
