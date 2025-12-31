"""Logic and comparison blocks for OSK-based simulation."""

from ..block import Block


class CompareToZero(Block):
    """Compare To Zero block - compares input to zero.

    Outputs 1 if comparison is true, 0 otherwise.
    """

    def __init__(self, operator='=='):
        super().__init__()
        self.operator = operator  # '==', '~=', '<', '<=', '>', '>='
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput(self.input_source_port)

        if self.operator == '==':
            self.output = 1.0 if self.input == 0.0 else 0.0
        elif self.operator == '~=' or self.operator == '!=':
            self.output = 1.0 if self.input != 0.0 else 0.0
        elif self.operator == '<':
            self.output = 1.0 if self.input < 0.0 else 0.0
        elif self.operator == '<=':
            self.output = 1.0 if self.input <= 0.0 else 0.0
        elif self.operator == '>':
            self.output = 1.0 if self.input > 0.0 else 0.0
        elif self.operator == '>=':
            self.output = 1.0 if self.input >= 0.0 else 0.0
        else:
            self.output = 0.0

    def getOutput(self, port=0):
        return self.output


class CompareToConstant(Block):
    """Compare To Constant block - compares input to a constant value.

    Outputs 1 if comparison is true, 0 otherwise.
    """

    def __init__(self, constant=0.0, operator='=='):
        super().__init__()
        self.constant = constant
        self.operator = operator  # '==', '~=', '<', '<=', '>', '>='
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput(self.input_source_port)

        if self.operator == '==':
            self.output = 1.0 if self.input == self.constant else 0.0
        elif self.operator == '~=' or self.operator == '!=':
            self.output = 1.0 if self.input != self.constant else 0.0
        elif self.operator == '<':
            self.output = 1.0 if self.input < self.constant else 0.0
        elif self.operator == '<=':
            self.output = 1.0 if self.input <= self.constant else 0.0
        elif self.operator == '>':
            self.output = 1.0 if self.input > self.constant else 0.0
        elif self.operator == '>=':
            self.output = 1.0 if self.input >= self.constant else 0.0
        else:
            self.output = 0.0

    def getOutput(self, port=0):
        return self.output


class RelationalOperator(Block):
    """Relational Operator block - compares two inputs.

    Outputs 1 if comparison is true, 0 otherwise.
    Supports vector inputs.
    """

    def __init__(self, operator='=='):
        super().__init__()
        self.operator = operator  # '==', '~=', '<', '<=', '>', '>='
        self.inputs = [0.0, 0.0]
        self.input_blocks = [None, None]
        self.input_source_ports = [0, 0]
        self.output = 0.0

        # Vector support
        self._is_vector = False
        self._n = 1
        self._input_vectors = [None, None]
        self._output_vector = None

    def init(self):
        self.output = 0.0
        self._output_vector = None

    def setInput(self, value, port=0):
        if port < 2:
            if isinstance(value, (list, tuple)):
                self._setup_vector_mode(len(value))
                self._input_vectors[port] = list(value)
                self.inputs[port] = value[0] if value else 0.0
            else:
                self.inputs[port] = value

    def _setup_vector_mode(self, n):
        if not self._is_vector or self._n != n:
            self._is_vector = True
            self._n = n
            self._output_vector = [0.0] * n

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block
            self.input_source_ports[port] = source_port

    def _compare(self, a, b):
        """Perform comparison and return 1.0 or 0.0."""
        if self.operator == '==':
            return 1.0 if a == b else 0.0
        elif self.operator == '~=' or self.operator == '!=':
            return 1.0 if a != b else 0.0
        elif self.operator == '<':
            return 1.0 if a < b else 0.0
        elif self.operator == '<=':
            return 1.0 if a <= b else 0.0
        elif self.operator == '>':
            return 1.0 if a > b else 0.0
        elif self.operator == '>=':
            return 1.0 if a >= b else 0.0
        return 0.0

    def update(self):
        # Read inputs
        for i in range(2):
            block = self.input_blocks[i]
            if block is not None:
                if hasattr(block, 'getOutputVector'):
                    vec = block.getOutputVector()
                    if vec is not None:
                        self._setup_vector_mode(len(vec))
                        self._input_vectors[i] = list(vec)
                        self.inputs[i] = vec[0] if vec else 0.0
                    else:
                        self.inputs[i] = block.getOutput(self.input_source_ports[i])
                else:
                    self.inputs[i] = block.getOutput(self.input_source_ports[i])

        if self._is_vector and self._output_vector:
            for i in range(self._n):
                a = self._input_vectors[0][i] if self._input_vectors[0] and i < len(self._input_vectors[0]) else self.inputs[0]
                b = self._input_vectors[1][i] if self._input_vectors[1] and i < len(self._input_vectors[1]) else self.inputs[1]
                self._output_vector[i] = self._compare(a, b)
            self.output = self._output_vector[0]
        else:
            self.output = self._compare(self.inputs[0], self.inputs[1])

    def getOutput(self, port=0):
        if self._is_vector and self._output_vector and port < len(self._output_vector):
            return self._output_vector[port]
        return self.output

    def getOutputVector(self):
        if self._is_vector and self._output_vector:
            return self._output_vector.copy()
        return None


class LogicalOperator(Block):
    """Logical Operator block - performs logical operations on inputs.

    Supports AND, OR, NAND, NOR, XOR, NOT operations.
    Inputs are treated as boolean (non-zero = true).
    """

    def __init__(self, operator='AND', num_inputs=2):
        super().__init__()
        self.operator = operator.upper()  # 'AND', 'OR', 'NAND', 'NOR', 'XOR', 'NOT'
        self.num_inputs = max(1, num_inputs) if operator.upper() != 'NOT' else 1
        self.inputs = [0.0] * self.num_inputs
        self.input_blocks = [None] * self.num_inputs
        self.input_source_ports = [0] * self.num_inputs
        self.output = 0.0

        # Vector support
        self._is_vector = False
        self._n = 1
        self._input_vectors = [None] * self.num_inputs
        self._output_vector = None

    def init(self):
        self.output = 0.0
        self._output_vector = None

    def setInput(self, value, port=0):
        if port < self.num_inputs:
            if isinstance(value, (list, tuple)):
                self._setup_vector_mode(len(value))
                self._input_vectors[port] = list(value)
                self.inputs[port] = value[0] if value else 0.0
            else:
                self.inputs[port] = value

    def _setup_vector_mode(self, n):
        if not self._is_vector or self._n != n:
            self._is_vector = True
            self._n = n
            self._output_vector = [0.0] * n
            # Expand input vectors array if needed
            while len(self._input_vectors) < self.num_inputs:
                self._input_vectors.append(None)

    def connectInput(self, block, port=0, source_port=0):
        if port < self.num_inputs:
            self.input_blocks[port] = block
            self.input_source_ports[port] = source_port

    def _to_bool(self, value):
        """Convert value to boolean (non-zero = True)."""
        return value != 0.0

    def _logic_op(self, values):
        """Perform logical operation on list of values."""
        bools = [self._to_bool(v) for v in values]

        if self.operator == 'AND':
            result = all(bools)
        elif self.operator == 'OR':
            result = any(bools)
        elif self.operator == 'NAND':
            result = not all(bools)
        elif self.operator == 'NOR':
            result = not any(bools)
        elif self.operator == 'XOR':
            # XOR: True if odd number of inputs are true
            result = sum(bools) % 2 == 1
        elif self.operator == 'NOT':
            result = not bools[0] if bools else True
        else:
            result = False

        return 1.0 if result else 0.0

    def update(self):
        # Read inputs
        for i in range(self.num_inputs):
            block = self.input_blocks[i]
            if block is not None:
                if hasattr(block, 'getOutputVector'):
                    vec = block.getOutputVector()
                    if vec is not None:
                        self._setup_vector_mode(len(vec))
                        self._input_vectors[i] = list(vec)
                        self.inputs[i] = vec[0] if vec else 0.0
                    else:
                        self.inputs[i] = block.getOutput(self.input_source_ports[i])
                else:
                    self.inputs[i] = block.getOutput(self.input_source_ports[i])

        if self._is_vector and self._output_vector:
            for i in range(self._n):
                values = []
                for j in range(self.num_inputs):
                    if self._input_vectors[j] and i < len(self._input_vectors[j]):
                        values.append(self._input_vectors[j][i])
                    else:
                        values.append(self.inputs[j])
                self._output_vector[i] = self._logic_op(values)
            self.output = self._output_vector[0]
        else:
            self.output = self._logic_op(self.inputs)

    def getOutput(self, port=0):
        if self._is_vector and self._output_vector and port < len(self._output_vector):
            return self._output_vector[port]
        return self.output

    def getOutputVector(self):
        if self._is_vector and self._output_vector:
            return self._output_vector.copy()
        return None


class BitOperator(Block):
    """Bit-wise logical operator block.

    Performs bit-wise operations on integer representations of inputs.
    """

    def __init__(self, operator='AND'):
        super().__init__()
        self.operator = operator.upper()  # 'AND', 'OR', 'XOR', 'NOT', 'NAND', 'NOR'
        self.inputs = [0.0, 0.0]
        self.input_blocks = [None, None]
        self.input_source_ports = [0, 0]
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def setInput(self, value, port=0):
        if port < 2:
            self.inputs[port] = value

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block
            self.input_source_ports[port] = source_port

    def update(self):
        for i in range(2):
            if self.input_blocks[i] is not None:
                self.inputs[i] = self.input_blocks[i].getOutput(self.input_source_ports[i])

        a = int(self.inputs[0])
        b = int(self.inputs[1])

        if self.operator == 'AND':
            self.output = float(a & b)
        elif self.operator == 'OR':
            self.output = float(a | b)
        elif self.operator == 'XOR':
            self.output = float(a ^ b)
        elif self.operator == 'NOT':
            self.output = float(~a)
        elif self.operator == 'NAND':
            self.output = float(~(a & b))
        elif self.operator == 'NOR':
            self.output = float(~(a | b))
        else:
            self.output = 0.0

    def getOutput(self, port=0):
        return self.output
