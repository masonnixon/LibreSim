"""Python templates for nonlinear blocks."""

from ....models import BlockInfo


def lookup_table_1d_template(block: BlockInfo, class_name: str) -> str:
    """Generate LookupTable1D block code."""
    x_data = block.parameters.get("xData", [0.0, 1.0])
    y_data = block.parameters.get("yData", [0.0, 1.0])

    return f'''
class {class_name}:
    """1D Lookup Table: {block.name}"""

    def __init__(self):
        self.x_data = {x_data}
        self.y_data = {y_data}
        self.input = 0.0
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def update(self, t: float):
        x = self.input
        # Linear interpolation
        if len(self.x_data) < 2:
            self.output = self.y_data[0] if self.y_data else 0.0
            return

        # Clamp to table bounds
        if x <= self.x_data[0]:
            self.output = self.y_data[0]
        elif x >= self.x_data[-1]:
            self.output = self.y_data[-1]
        else:
            # Find interval
            for i in range(len(self.x_data) - 1):
                if self.x_data[i] <= x <= self.x_data[i + 1]:
                    # Linear interpolation
                    t_interp = (x - self.x_data[i]) / (self.x_data[i + 1] - self.x_data[i])
                    self.output = self.y_data[i] + t_interp * (self.y_data[i + 1] - self.y_data[i])
                    break

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def lookup_table_2d_template(block: BlockInfo, class_name: str) -> str:
    """Generate LookupTable2D block code."""
    x_data = block.parameters.get("xData", [0.0, 1.0])
    y_data = block.parameters.get("yData", [0.0, 1.0])
    z_data = block.parameters.get("zData", [[0.0, 0.0], [0.0, 1.0]])

    return f'''
class {class_name}:
    """2D Lookup Table: {block.name}"""

    def __init__(self):
        self.x_data = {x_data}
        self.y_data = {y_data}
        self.z_data = {z_data}
        self.input = 0.0   # X input
        self.input1 = 0.0  # Y input
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def update(self, t: float):
        x = self.input
        y = self.input1

        # Find x indices
        if x <= self.x_data[0]:
            xi, tx = 0, 0.0
        elif x >= self.x_data[-1]:
            xi, tx = len(self.x_data) - 2, 1.0
        else:
            for i in range(len(self.x_data) - 1):
                if self.x_data[i] <= x <= self.x_data[i + 1]:
                    xi = i
                    tx = (x - self.x_data[i]) / (self.x_data[i + 1] - self.x_data[i])
                    break

        # Find y indices
        if y <= self.y_data[0]:
            yi, ty = 0, 0.0
        elif y >= self.y_data[-1]:
            yi, ty = len(self.y_data) - 2, 1.0
        else:
            for i in range(len(self.y_data) - 1):
                if self.y_data[i] <= y <= self.y_data[i + 1]:
                    yi = i
                    ty = (y - self.y_data[i]) / (self.y_data[i + 1] - self.y_data[i])
                    break

        # Bilinear interpolation
        z00 = self.z_data[yi][xi]
        z01 = self.z_data[yi][xi + 1] if xi + 1 < len(self.x_data) else z00
        z10 = self.z_data[yi + 1][xi] if yi + 1 < len(self.y_data) else z00
        z11 = self.z_data[yi + 1][xi + 1] if yi + 1 < len(self.y_data) and xi + 1 < len(self.x_data) else z00

        z0 = z00 + tx * (z01 - z00)
        z1 = z10 + tx * (z11 - z10)
        self.output = z0 + ty * (z1 - z0)

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def quantizer_template(block: BlockInfo, class_name: str) -> str:
    """Generate Quantizer block code."""
    interval = block.parameters.get("interval", 1.0)

    return f'''
class {class_name}:
    """Quantizer: {block.name}"""

    def __init__(self):
        self.interval = {interval}
        self.input = 0.0
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def update(self, t: float):
        self.output = round(self.input / self.interval) * self.interval

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def relay_template(block: BlockInfo, class_name: str) -> str:
    """Generate Relay (hysteresis) block code."""
    # Support both camelCase (JSON) and snake_case parameter names
    on_point = block.parameters.get("switchOn", block.parameters.get("onPoint", 0.5))
    off_point = block.parameters.get("switchOff", block.parameters.get("offPoint", -0.5))
    on_output = block.parameters.get("outputOn", block.parameters.get("onOutput", 1.0))
    off_output = block.parameters.get("outputOff", block.parameters.get("offOutput", -1.0))

    return f'''
class {class_name}:
    """Relay (hysteresis): {block.name}"""

    def __init__(self):
        self.on_point = {on_point}
        self.off_point = {off_point}
        self.on_output = {on_output}
        self.off_output = {off_output}
        self.input = 0.0
        self.output = {off_output}
        self.state = False  # Relay state

    def init(self):
        self.output = self.off_output
        self.state = False

    def update(self, t: float):
        if self.state:  # Currently ON
            if self.input <= self.off_point:
                self.state = False
                self.output = self.off_output
            else:
                self.output = self.on_output
        else:  # Currently OFF
            if self.input >= self.on_point:
                self.state = True
                self.output = self.on_output
            else:
                self.output = self.off_output

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def coulomb_friction_template(block: BlockInfo, class_name: str) -> str:
    """Generate Coulomb friction block code."""
    offset = block.parameters.get("offset", 0.0)
    gain = block.parameters.get("gain", 1.0)

    return f'''
class {class_name}:
    """Coulomb friction: {block.name}"""

    def __init__(self):
        self.offset = {offset}
        self.gain = {gain}
        self.input = 0.0
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def update(self, t: float):
        if self.input > 0:
            self.output = self.gain
        elif self.input < 0:
            self.output = -self.gain
        else:
            self.output = 0.0
        self.output += self.offset

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def wrap_to_range_template(block: BlockInfo, class_name: str) -> str:
    """Generate WrapToRange block code."""
    lower = block.parameters.get("lower", -3.14159265)
    upper = block.parameters.get("upper", 3.14159265)

    return f'''
class {class_name}:
    """Wrap to range: {block.name}"""

    def __init__(self):
        self.lower = {lower}
        self.upper = {upper}
        self.input = 0.0
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def update(self, t: float):
        range_size = self.upper - self.lower
        if range_size <= 0:
            self.output = self.input
            return

        # Wrap to range
        val = self.input - self.lower
        val = val % range_size
        if val < 0:
            val += range_size
        self.output = val + self.lower

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def hit_crossing_template(block: BlockInfo, class_name: str) -> str:
    """Generate HitCrossing (zero crossing detector) block code."""
    offset = block.parameters.get("offset", 0.0)
    direction = block.parameters.get("direction", "rising")

    return f'''
class {class_name}:
    """Hit/Zero crossing detector: {block.name}"""

    def __init__(self):
        self.offset = {offset}
        self.direction = "{direction}"
        self.input = 0.0
        self.output = 0.0
        self.prev_input = 0.0
        self.first_step = True

    def init(self):
        self.output = 0.0
        self.prev_input = 0.0
        self.first_step = True

    def update(self, t: float):
        if self.first_step:
            self.first_step = False
            self.prev_input = self.input
            self.output = 0.0
            return

        prev_val = self.prev_input - self.offset
        curr_val = self.input - self.offset
        crossed = False

        if self.direction == "rising":
            crossed = prev_val < 0 and curr_val >= 0
        elif self.direction == "falling":
            crossed = prev_val > 0 and curr_val <= 0
        elif self.direction == "either":
            crossed = (prev_val < 0 and curr_val >= 0) or (prev_val > 0 and curr_val <= 0)

        self.output = 1.0 if crossed else 0.0
        self.prev_input = self.input

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


def stiction_template(block: BlockInfo, class_name: str) -> str:
    """Generate Stiction block code."""
    static_friction = block.parameters.get("staticFriction", 1.0)
    kinetic_friction = block.parameters.get("kineticFriction", 0.8)

    return f'''
class {class_name}:
    """Stiction (static + kinetic friction): {block.name}"""

    def __init__(self):
        self.static_friction = {static_friction}
        self.kinetic_friction = {kinetic_friction}
        self.input = 0.0
        self.output = 0.0
        self.is_moving = False
        self.prev_output = 0.0

    def init(self):
        self.output = 0.0
        self.is_moving = False
        self.prev_output = 0.0

    def update(self, t: float):
        if not self.is_moving:
            # Stationary: check if input exceeds static friction
            if abs(self.input) > self.static_friction:
                self.is_moving = True
                if self.input > 0:
                    self.output = self.input - self.kinetic_friction
                else:
                    self.output = self.input + self.kinetic_friction
            else:
                self.output = 0.0
        else:
            # Moving: apply kinetic friction
            if self.input > self.kinetic_friction:
                self.output = self.input - self.kinetic_friction
            elif self.input < -self.kinetic_friction:
                self.output = self.input + self.kinetic_friction
            else:
                # Come to rest
                self.is_moving = False
                self.output = 0.0

        self.prev_output = self.output

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


# Template registry for nonlinear blocks
NONLINEAR_TEMPLATES = {
    "lookup_table_1d": lookup_table_1d_template,
    "lookup_table_2d": lookup_table_2d_template,
    "quantizer": quantizer_template,
    "relay": relay_template,
    "coulomb": coulomb_friction_template,
    "wrap_to_range": wrap_to_range_template,
    "hit_crossing": hit_crossing_template,
    "stiction": stiction_template,
}
