"""Python templates for sink blocks."""

from ....models import BlockInfo


def scope_template(block: BlockInfo, class_name: str) -> str:
    """Generate Scope block code."""
    num_inputs = block.parameters.get("numInputs", 1)
    return f'''
class {class_name}:
    """Scope sink: {block.name}"""

    def __init__(self):
        self.num_inputs = {num_inputs}
        self.input = 0.0
{chr(10).join(f"        self.input{i+1} = 0.0" for i in range(1, num_inputs))}
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def update(self, t: float):
        # Scope just passes through the first input
        self.output = self.input

    def get_output(self, port: int = 0) -> float:
        if port == 0:
            return self.input
{chr(10).join(f"        elif port == {i}:" + chr(10) + f"            return self.input{i+1}" for i in range(1, num_inputs))}
        return self.input
'''


def display_template(block: BlockInfo, class_name: str) -> str:
    """Generate Display block code."""
    return f'''
class {class_name}:
    """Display sink: {block.name}"""

    def __init__(self):
        self.input = 0.0
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def update(self, t: float):
        self.output = self.input

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def terminator_template(block: BlockInfo, class_name: str) -> str:
    """Generate Terminator block code."""
    return f'''
class {class_name}:
    """Terminator sink: {block.name}"""

    def __init__(self):
        self.input = 0.0

    def init(self):
        pass

    def update(self, t: float):
        pass  # Terminator discards input

    def get_output(self, port: int = 0) -> float:
        return 0.0
'''


def to_workspace_template(block: BlockInfo, class_name: str) -> str:
    """Generate ToWorkspace block code."""
    variable_name = block.parameters.get("variableName", "simout")
    return f'''
class {class_name}:
    """ToWorkspace sink: {block.name}"""

    def __init__(self):
        self.variable_name = "{variable_name}"
        self.input = 0.0
        self.output = 0.0
        self.data = []

    def init(self):
        self.data = []
        self.output = 0.0

    def update(self, t: float):
        self.output = self.input
        self.data.append(self.input)

    def get_output(self, port: int = 0) -> float:
        return self.output

    def get_data(self) -> list:
        return self.data
'''


def xy_graph_template(block: BlockInfo, class_name: str) -> str:
    """Generate XY Graph block code."""
    return f'''
class {class_name}:
    """XY Graph sink: {block.name}"""

    def __init__(self):
        self.input = 0.0   # X input
        self.input1 = 0.0  # Y input
        self.x_data = []
        self.y_data = []

    def init(self):
        self.x_data = []
        self.y_data = []

    def update(self, t: float):
        self.x_data.append(self.input)
        self.y_data.append(self.input1)

    def get_output(self, port: int = 0) -> float:
        return self.input if port == 0 else self.input1

    def get_data(self) -> tuple:
        return (self.x_data, self.y_data)
'''


# Template registry for sink blocks
SINK_TEMPLATES = {
    "scope": scope_template,
    "display": display_template,
    "terminator": terminator_template,
    "to_workspace": to_workspace_template,
    "xy_graph": xy_graph_template,
}
