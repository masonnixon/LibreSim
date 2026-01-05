"""Data type conversion blocks for LibreSim.

These blocks handle data type conversions similar to Simulink's
Data Type Conversion blocks.
"""

import math

from ..block import Block


class DataTypeConversion(Block):
    """Convert signal to specified data type.

    Supports: double, single, int8, int16, int32, uint8, uint16, uint32, boolean
    """

    def __init__(self, output_type="double", saturate=True, round_mode="round"):
        super().__init__()
        self.output_type = output_type
        self.saturate = saturate
        self.round_mode = round_mode  # 'round', 'floor', 'ceil', 'fix'
        self.input = 0.0
        self.output = 0.0
        self.input_block = None
        self.input_source_port = 0

        # Type limits
        self.type_limits = {
            "int8": (-128, 127),
            "int16": (-32768, 32767),
            "int32": (-2147483648, 2147483647),
            "uint8": (0, 255),
            "uint16": (0, 65535),
            "uint32": (0, 4294967295),
        }

    def init(self):
        self.output = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def _round_value(self, value):
        """Apply rounding mode to value."""
        if self.round_mode == "round":
            return round(value)
        elif self.round_mode == "floor":
            return math.floor(value)
        elif self.round_mode == "ceil":
            return math.ceil(value)
        elif self.round_mode == "fix":
            return int(value)
        return round(value)

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput(self.input_source_port)

        value = self.input

        if self.output_type == "double":
            self.output = float(value)
        elif self.output_type == "single":
            self.output = float(value)  # Python doesn't distinguish single/double
        elif self.output_type == "boolean":
            self.output = 1.0 if value != 0 else 0.0
        elif self.output_type in self.type_limits:
            # Integer conversion
            value = self._round_value(value)
            min_val, max_val = self.type_limits[self.output_type]
            if self.saturate:
                value = max(min_val, min(max_val, value))
            else:
                # Wrap around
                range_size = max_val - min_val + 1
                value = min_val + ((value - min_val) % range_size)
            self.output = float(value)
        else:
            self.output = float(value)

    def getOutput(self, port=0):
        return self.output


class RealImagToComplex(Block):
    """Convert real and imaginary parts to complex number.

    Since we work with real signals, outputs magnitude at port 0
    and phase at port 1 (or as a 2-element vector).
    """

    def __init__(self):
        super().__init__()
        self.inputs = [0.0, 0.0]  # [real, imag]
        self.output_magnitude = 0.0
        self.output_phase = 0.0
        self.input_blocks = [None, None]

    def init(self):
        self.output_magnitude = 0.0
        self.output_phase = 0.0

    def setInput(self, value, port=0):
        if port < 2:
            self.inputs[port] = value

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block

    def update(self):
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                self.inputs[i] = block.getOutput()

        real = self.inputs[0]
        imag = self.inputs[1]

        self.output_magnitude = math.sqrt(real * real + imag * imag)
        self.output_phase = math.atan2(imag, real)

    def getOutput(self, port=0):
        if port == 0:
            return self.output_magnitude
        elif port == 1:
            return self.output_phase
        return 0.0

    def getOutputVector(self):
        return [self.output_magnitude, self.output_phase]


class ComplexToRealImag(Block):
    """Convert complex (magnitude/phase) to real and imaginary parts."""

    def __init__(self):
        super().__init__()
        self.inputs = [0.0, 0.0]  # [magnitude, phase]
        self.output_real = 0.0
        self.output_imag = 0.0
        self.input_blocks = [None, None]

    def init(self):
        self.output_real = 0.0
        self.output_imag = 0.0

    def setInput(self, value, port=0):
        if port < 2:
            self.inputs[port] = value

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block

    def update(self):
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                self.inputs[i] = block.getOutput()

        magnitude = self.inputs[0]
        phase = self.inputs[1]

        self.output_real = magnitude * math.cos(phase)
        self.output_imag = magnitude * math.sin(phase)

    def getOutput(self, port=0):
        if port == 0:
            return self.output_real
        elif port == 1:
            return self.output_imag
        return 0.0

    def getOutputVector(self):
        return [self.output_real, self.output_imag]
