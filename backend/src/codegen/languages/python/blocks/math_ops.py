"""Python templates for math operation blocks."""

from ....models import BlockInfo


def sum_template(block: BlockInfo, class_name: str) -> str:
    """Generate Sum block code."""
    signs_param = block.parameters.get("signs", "++")
    signs = list(signs_param)
    num_inputs = len(signs)

    # Generate input attributes (use input0, input1, etc. for consistency)
    input_attrs = []
    for i in range(num_inputs):
        input_attrs.append(f"self.input{i} = 0.0")

    # Generate sum computation
    sum_terms = []
    for i, sign in enumerate(signs):
        var = f"self.input{i}"
        if sign == "+":
            sum_terms.append(var)
        else:
            sum_terms.append(f"-{var}")

    # Join input attrs with proper indentation (newline + 8 spaces)
    input_attrs_code = "\n        ".join(input_attrs)

    return f'''
class {class_name}:
    """Sum block: {block.name}"""

    def __init__(self):
        {input_attrs_code}
        self.output = 0.0
        self.signs = "{signs_param}"

    def init(self):
        self.output = 0.0

    def update(self, t: float):
        self.output = {" + ".join(sum_terms) if sum_terms else "0.0"}

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def gain_template(block: BlockInfo, class_name: str) -> str:
    """Generate Gain block code.

    Supports both scalar and vector inputs - applies element-wise gain.
    """
    gain = block.parameters.get("gain", 1.0)
    return f'''
class {class_name}:
    """Gain block: {block.name} - supports scalar and vector inputs"""

    def __init__(self):
        self.gain = {gain}
        self.input = 0.0  # Can be scalar or list/vector
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def update(self, t: float):
        if isinstance(self.input, (list, tuple)):
            # Vector input: apply gain to each element
            self.output = [self.gain * x for x in self.input]
        else:
            # Scalar input
            self.output = self.gain * self.input

    def get_output(self, port: int = 0) -> float:
        if isinstance(self.output, (list, tuple)):
            if port < len(self.output):
                return self.output[port]
            return 0.0
        return self.output

    def get_output_vector(self) -> list:
        if isinstance(self.output, (list, tuple)):
            return list(self.output)
        return [self.output]
'''


def product_template(block: BlockInfo, class_name: str) -> str:
    """Generate Product block code."""
    operations = block.parameters.get("operations", "**")
    num_inputs = len(operations)

    # Generate input attributes (use input0, input1, etc. for consistency)
    input_attrs = []
    for i in range(num_inputs):
        input_attrs.append(f"self.input{i} = 0.0")

    # Generate product computation
    product_lines = ["result = 1.0"]
    for i, op in enumerate(operations):
        var = f"self.input{i}"
        if op == "*":
            product_lines.append(f"result *= {var}")
        else:
            product_lines.append(f"result /= {var} if {var} != 0 else 1e-10")

    # Join with proper indentation
    input_attrs_code = "\n        ".join(input_attrs)
    product_code = "\n        ".join(product_lines)

    return f'''
class {class_name}:
    """Product block: {block.name}"""

    def __init__(self):
        {input_attrs_code}
        self.output = 0.0
        self.operations = "{operations}"

    def init(self):
        self.output = 0.0

    def update(self, t: float):
        {product_code}
        self.output = result

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def abs_template(block: BlockInfo, class_name: str) -> str:
    """Generate Abs block code."""
    return f'''
class {class_name}:
    """Absolute value block: {block.name}"""

    def __init__(self):
        self.input = 0.0
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def update(self, t: float):
        self.output = abs(self.input)

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def sign_template(block: BlockInfo, class_name: str) -> str:
    """Generate Sign block code."""
    return f'''
class {class_name}:
    """Sign block: {block.name}"""

    def __init__(self):
        self.input = 0.0
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def update(self, t: float):
        if self.input > 0:
            self.output = 1.0
        elif self.input < 0:
            self.output = -1.0
        else:
            self.output = 0.0

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def bias_template(block: BlockInfo, class_name: str) -> str:
    """Generate Bias block code."""
    bias = block.parameters.get("bias", 0.0)
    return f'''
class {class_name}:
    """Bias block: {block.name}"""

    def __init__(self):
        self.bias = {bias}
        self.input = 0.0
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def update(self, t: float):
        self.output = self.input + self.bias

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def saturation_template(block: BlockInfo, class_name: str) -> str:
    """Generate Saturation block code."""
    upper_limit = block.parameters.get("upperLimit", 1.0)
    lower_limit = block.parameters.get("lowerLimit", -1.0)
    return f'''
class {class_name}:
    """Saturation block: {block.name}"""

    def __init__(self):
        self.upper_limit = {upper_limit}
        self.lower_limit = {lower_limit}
        self.input = 0.0
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def update(self, t: float):
        if self.input > self.upper_limit:
            self.output = self.upper_limit
        elif self.input < self.lower_limit:
            self.output = self.lower_limit
        else:
            self.output = self.input

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def dead_zone_template(block: BlockInfo, class_name: str) -> str:
    """Generate DeadZone block code."""
    start = block.parameters.get("start", -0.5)
    end = block.parameters.get("end", 0.5)
    return f'''
class {class_name}:
    """Dead zone block: {block.name}"""

    def __init__(self):
        self.start = {start}
        self.end = {end}
        self.input = 0.0
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def update(self, t: float):
        if self.input > self.end:
            self.output = self.input - self.end
        elif self.input < self.start:
            self.output = self.input - self.start
        else:
            self.output = 0.0

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def switch_template(block: BlockInfo, class_name: str) -> str:
    """Generate Switch block code."""
    threshold = block.parameters.get("threshold", 0.0)
    criteria = block.parameters.get("criteria", ">=")
    return f'''
class {class_name}:
    """Switch block: {block.name}"""

    def __init__(self):
        self.threshold = {threshold}
        self.criteria = "{criteria}"
        self.input0 = 0.0  # First input (when condition true)
        self.input1 = 0.0  # Control signal
        self.input2 = 0.0  # Third input (when condition false)
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def update(self, t: float):
        condition = False
        if self.criteria == ">=":
            condition = self.input1 >= self.threshold
        elif self.criteria == ">":
            condition = self.input1 > self.threshold
        elif self.criteria == "!=":
            condition = self.input1 != self.threshold

        self.output = self.input0 if condition else self.input2

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def math_function_template(block: BlockInfo, class_name: str) -> str:
    """Generate MathFunction block code."""
    function = block.parameters.get("function", "exp")
    func_map = {
        "exp": "math.exp(self.input)",
        "log": "math.log(self.input) if self.input > 0 else float('-inf')",
        "log10": "math.log10(self.input) if self.input > 0 else float('-inf')",
        "sqrt": "math.sqrt(abs(self.input))",
        "pow": "self.input ** 2",
        "square": "self.input ** 2",
        "reciprocal": "1.0 / self.input if self.input != 0 else float('inf')",
    }
    func_code = func_map.get(function, "self.input")
    return f'''
class {class_name}:
    """Math function block: {block.name}"""

    def __init__(self):
        self.function = "{function}"
        self.input = 0.0
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def update(self, t: float):
        self.output = {func_code}

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def trigonometry_template(block: BlockInfo, class_name: str) -> str:
    """Generate Trigonometry block code."""
    function = block.parameters.get("function", "sin")
    func_map = {
        "sin": "math.sin(self.input)",
        "cos": "math.cos(self.input)",
        "tan": "math.tan(self.input)",
        "asin": "math.asin(max(-1, min(1, self.input)))",
        "acos": "math.acos(max(-1, min(1, self.input)))",
        "atan": "math.atan(self.input)",
        "atan2": "math.atan2(self.input, self.input1)",
        "sinh": "math.sinh(self.input)",
        "cosh": "math.cosh(self.input)",
        "tanh": "math.tanh(self.input)",
    }
    func_code = func_map.get(function, "self.input")

    extra_input = ""
    if function == "atan2":
        extra_input = "\n        self.input1 = 0.0  # Second input for atan2"

    return f'''
class {class_name}:
    """Trigonometry block: {block.name}"""

    def __init__(self):
        self.function = "{function}"
        self.input = 0.0{extra_input}
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def update(self, t: float):
        self.output = {func_code}

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def mux_template(block: BlockInfo, class_name: str) -> str:
    """Generate Mux block code."""
    num_inputs = block.parameters.get("numInputs", 2)
    # Use input0, input1, etc. for consistency
    input_attrs = []
    for i in range(num_inputs):
        input_attrs.append(f"self.input{i} = 0.0")

    output_list = []
    for i in range(num_inputs):
        output_list.append(f"self.input{i}")

    # Join with proper indentation
    input_attrs_code = "\n        ".join(input_attrs)

    return f'''
class {class_name}:
    """Mux block: {block.name}"""

    def __init__(self):
        self.num_inputs = {num_inputs}
        {input_attrs_code}
        self.output = [0.0] * {num_inputs}

    def init(self):
        self.output = [0.0] * self.num_inputs

    def update(self, t: float):
        self.output = [{", ".join(output_list)}]

    def get_output(self, port: int = 0) -> float:
        if port < len(self.output):
            return self.output[port]
        return 0.0

    def get_output_vector(self) -> list:
        return self.output
'''


def demux_template(block: BlockInfo, class_name: str) -> str:
    """Generate Demux block code."""
    num_outputs = block.parameters.get("numOutputs", 2)
    return f'''
class {class_name}:
    """Demux block: {block.name}"""

    def __init__(self):
        self.num_outputs = {num_outputs}
        self.input = [0.0] * {num_outputs}  # Vector input
        self.outputs = [0.0] * {num_outputs}

    def init(self):
        self.outputs = [0.0] * self.num_outputs

    def update(self, t: float):
        if isinstance(self.input, (list, tuple)):
            for i in range(min(len(self.input), self.num_outputs)):
                self.outputs[i] = self.input[i]
        else:
            self.outputs[0] = self.input

    def get_output(self, port: int = 0) -> float:
        if port < len(self.outputs):
            return self.outputs[port]
        return 0.0

    def get_output_vector(self) -> list:
        return list(self.outputs)
'''


# Template registry for math operation blocks
MATH_TEMPLATES = {
    "sum": sum_template,
    "gain": gain_template,
    "product": product_template,
    "abs": abs_template,
    "sign": sign_template,
    "bias": bias_template,
    "saturation": saturation_template,
    "dead_zone": dead_zone_template,
    "switch": switch_template,
    "math_function": math_function_template,
    "trigonometry": trigonometry_template,
    "mux": mux_template,
    "demux": demux_template,
}
