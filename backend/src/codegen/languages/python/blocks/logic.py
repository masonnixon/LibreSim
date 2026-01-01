"""Python templates for logic blocks."""

from ....models import BlockInfo


def compare_to_zero_template(block: BlockInfo, class_name: str) -> str:
    """Generate CompareToZero block code."""
    operator = block.parameters.get("operator", "==")
    return f'''
class {class_name}:
    """Compare to zero block: {block.name}"""

    def __init__(self):
        self.operator = "{operator}"
        self.input = 0.0
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def update(self, t: float):
        if self.operator == "==":
            self.output = 1.0 if self.input == 0 else 0.0
        elif self.operator == "!=":
            self.output = 1.0 if self.input != 0 else 0.0
        elif self.operator == ">":
            self.output = 1.0 if self.input > 0 else 0.0
        elif self.operator == ">=":
            self.output = 1.0 if self.input >= 0 else 0.0
        elif self.operator == "<":
            self.output = 1.0 if self.input < 0 else 0.0
        elif self.operator == "<=":
            self.output = 1.0 if self.input <= 0 else 0.0
        else:
            self.output = 0.0

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def compare_to_constant_template(block: BlockInfo, class_name: str) -> str:
    """Generate CompareToConstant block code."""
    operator = block.parameters.get("operator", "==")
    constant = block.parameters.get("constant", 0.0)
    return f'''
class {class_name}:
    """Compare to constant block: {block.name}"""

    def __init__(self):
        self.operator = "{operator}"
        self.constant = {constant}
        self.input = 0.0
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def update(self, t: float):
        if self.operator == "==":
            self.output = 1.0 if self.input == self.constant else 0.0
        elif self.operator == "!=":
            self.output = 1.0 if self.input != self.constant else 0.0
        elif self.operator == ">":
            self.output = 1.0 if self.input > self.constant else 0.0
        elif self.operator == ">=":
            self.output = 1.0 if self.input >= self.constant else 0.0
        elif self.operator == "<":
            self.output = 1.0 if self.input < self.constant else 0.0
        elif self.operator == "<=":
            self.output = 1.0 if self.input <= self.constant else 0.0
        else:
            self.output = 0.0

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def relational_operator_template(block: BlockInfo, class_name: str) -> str:
    """Generate RelationalOperator block code."""
    operator = block.parameters.get("operator", "==")
    return f'''
class {class_name}:
    """Relational operator block: {block.name}"""

    def __init__(self):
        self.operator = "{operator}"
        self.input = 0.0   # First input
        self.input1 = 0.0  # Second input
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def update(self, t: float):
        if self.operator == "==":
            self.output = 1.0 if self.input == self.input1 else 0.0
        elif self.operator == "!=":
            self.output = 1.0 if self.input != self.input1 else 0.0
        elif self.operator == ">":
            self.output = 1.0 if self.input > self.input1 else 0.0
        elif self.operator == ">=":
            self.output = 1.0 if self.input >= self.input1 else 0.0
        elif self.operator == "<":
            self.output = 1.0 if self.input < self.input1 else 0.0
        elif self.operator == "<=":
            self.output = 1.0 if self.input <= self.input1 else 0.0
        else:
            self.output = 0.0

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def logical_operator_template(block: BlockInfo, class_name: str) -> str:
    """Generate LogicalOperator block code."""
    operator = block.parameters.get("operator", "AND")
    num_inputs = block.parameters.get("numInputs", 2)

    input_attrs = ["self.input = 0.0"]
    for i in range(1, num_inputs):
        input_attrs.append(f"self.input{i} = 0.0")

    input_list = ["self.input"]
    for i in range(1, num_inputs):
        input_list.append(f"self.input{i}")

    input_attrs_code = "\n        ".join(input_attrs)

    return f'''
class {class_name}:
    """Logical operator block: {block.name}"""

    def __init__(self):
        self.operator = "{operator}"
        self.num_inputs = {num_inputs}
        {input_attrs_code}
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def update(self, t: float):
        inputs = [{', '.join(input_list)}]
        bool_inputs = [x != 0 for x in inputs]

        if self.operator == "AND":
            self.output = 1.0 if all(bool_inputs) else 0.0
        elif self.operator == "OR":
            self.output = 1.0 if any(bool_inputs) else 0.0
        elif self.operator == "NAND":
            self.output = 0.0 if all(bool_inputs) else 1.0
        elif self.operator == "NOR":
            self.output = 0.0 if any(bool_inputs) else 1.0
        elif self.operator == "XOR":
            result = False
            for b in bool_inputs:
                result = result != b
            self.output = 1.0 if result else 0.0
        elif self.operator == "NOT":
            self.output = 0.0 if bool_inputs[0] else 1.0
        else:
            self.output = 0.0

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def bit_operator_template(block: BlockInfo, class_name: str) -> str:
    """Generate BitOperator block code."""
    operator = block.parameters.get("operator", "AND")
    return f'''
class {class_name}:
    """Bit operator block: {block.name}"""

    def __init__(self):
        self.operator = "{operator}"
        self.input = 0.0   # First input
        self.input1 = 0.0  # Second input
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def update(self, t: float):
        a = int(self.input)
        b = int(self.input1)

        if self.operator == "AND":
            self.output = float(a & b)
        elif self.operator == "OR":
            self.output = float(a | b)
        elif self.operator == "XOR":
            self.output = float(a ^ b)
        elif self.operator == "NOT":
            self.output = float(~a)
        elif self.operator == "SHIFT_LEFT":
            self.output = float(a << b)
        elif self.operator == "SHIFT_RIGHT":
            self.output = float(a >> b)
        else:
            self.output = 0.0

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


# Template registry for logic blocks
LOGIC_TEMPLATES = {
    "compare_to_zero": compare_to_zero_template,
    "compare_to_constant": compare_to_constant_template,
    "relational_operator": relational_operator_template,
    "logical_operator": logical_operator_template,
    "bit_operator": bit_operator_template,
}
