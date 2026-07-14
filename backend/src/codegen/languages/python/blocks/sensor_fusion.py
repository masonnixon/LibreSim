"""Python templates for sensor-fusion tracking blocks."""

from ....models import BlockInfo


def alpha_beta_filter_template(block: BlockInfo, class_name: str) -> str:
    """Generate an alpha-beta position and velocity tracking filter."""
    alpha = block.parameters.get("alpha", 0.5)
    beta = block.parameters.get("beta", 0.1)
    sample_time = block.parameters.get("sampleTime", 0.1)
    return f'''
class {class_name}:
    """Alpha-beta tracking filter: {block.name}"""

    def __init__(self):
        self.alpha = {alpha}
        self.beta = {beta}
        self.sample_time = {sample_time}
        self.input = 0.0
        self.position = 0.0
        self.velocity = 0.0
        self.output = [0.0, 0.0]

    def init(self):
        self.position = 0.0
        self.velocity = 0.0
        self.output = [0.0, 0.0]

    def update(self, t: float):
        predicted_position = self.position + self.velocity * self.sample_time
        residual = self.input - predicted_position
        self.position = predicted_position + self.alpha * residual
        self.velocity += (self.beta / self.sample_time) * residual
        self.output = [self.position, self.velocity]

    def get_output(self, port: int = 0) -> float:
        if 0 <= port < 2:
            return self.output[port]
        return 0.0
'''


def alpha_beta_gamma_filter_template(block: BlockInfo, class_name: str) -> str:
    """Generate an alpha-beta-gamma position, velocity, and acceleration filter."""
    alpha = block.parameters.get("alpha", 0.5)
    beta = block.parameters.get("beta", 0.3)
    gamma = block.parameters.get("gamma", 0.1)
    sample_time = block.parameters.get("sampleTime", 0.1)
    return f'''
class {class_name}:
    """Alpha-beta-gamma tracking filter: {block.name}"""

    def __init__(self):
        self.alpha = {alpha}
        self.beta = {beta}
        self.gamma = {gamma}
        self.sample_time = {sample_time}
        self.input = 0.0
        self.position = 0.0
        self.velocity = 0.0
        self.acceleration = 0.0
        self.output = [0.0, 0.0, 0.0]

    def init(self):
        self.position = 0.0
        self.velocity = 0.0
        self.acceleration = 0.0
        self.output = [0.0, 0.0, 0.0]

    def update(self, t: float):
        dt = self.sample_time
        predicted_position = (
            self.position + self.velocity * dt + 0.5 * self.acceleration * dt * dt
        )
        predicted_velocity = self.velocity + self.acceleration * dt
        residual = self.input - predicted_position
        self.position = predicted_position + self.alpha * residual
        self.velocity = predicted_velocity + (self.beta / dt) * residual
        self.acceleration += (2.0 * self.gamma / (dt * dt)) * residual
        self.output = [self.position, self.velocity, self.acceleration]

    def get_output(self, port: int = 0) -> float:
        if 0 <= port < 3:
            return self.output[port]
        return 0.0
'''


SENSOR_FUSION_TEMPLATES = {
    "alpha_beta_filter": alpha_beta_filter_template,
    "alpha_beta_gamma_filter": alpha_beta_gamma_filter_template,
}
