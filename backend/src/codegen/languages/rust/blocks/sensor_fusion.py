"""Rust templates for sensor-fusion tracking blocks."""

from ....models import BlockInfo


def alpha_beta_filter_template(block: BlockInfo, struct_name: str) -> str:
    """Generate an alpha-beta position and velocity tracking filter."""
    alpha = block.parameters.get("alpha", 0.5)
    beta = block.parameters.get("beta", 0.1)
    sample_time = block.parameters.get("sampleTime", 0.1)
    return f"""
/// {block.name} - Alpha-beta tracking filter
#[derive(Clone)]
pub struct {struct_name} {{
    pub alpha: f64,
    pub beta: f64,
    pub sample_time: f64,
    pub input: f64,
    pub position: f64,
    pub velocity: f64,
    pub output: [f64; 2],
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            alpha: {alpha},
            beta: {beta},
            sample_time: {sample_time},
            input: 0.0,
            position: 0.0,
            velocity: 0.0,
            output: [0.0, 0.0],
        }}
    }}

    pub fn init(&mut self) {{
        self.position = 0.0;
        self.velocity = 0.0;
        self.output = [0.0, 0.0];
    }}

    pub fn update(&mut self, _t: f64) {{
        let predicted_position = self.position + self.velocity * self.sample_time;
        let residual = self.input - predicted_position;
        self.position = predicted_position + self.alpha * residual;
        self.velocity += (self.beta / self.sample_time) * residual;
        self.output = [self.position, self.velocity];
    }}

    pub fn get_output(&self, port: usize) -> f64 {{
        if port < 2 {{ self.output[port] }} else {{ 0.0 }}
    }}
}}
"""


def alpha_beta_gamma_filter_template(block: BlockInfo, struct_name: str) -> str:
    """Generate an alpha-beta-gamma position, velocity, and acceleration filter."""
    alpha = block.parameters.get("alpha", 0.5)
    beta = block.parameters.get("beta", 0.3)
    gamma = block.parameters.get("gamma", 0.1)
    sample_time = block.parameters.get("sampleTime", 0.1)
    return f"""
/// {block.name} - Alpha-beta-gamma tracking filter
#[derive(Clone)]
pub struct {struct_name} {{
    pub alpha: f64,
    pub beta: f64,
    pub gamma: f64,
    pub sample_time: f64,
    pub input: f64,
    pub position: f64,
    pub velocity: f64,
    pub acceleration: f64,
    pub output: [f64; 3],
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            alpha: {alpha},
            beta: {beta},
            gamma: {gamma},
            sample_time: {sample_time},
            input: 0.0,
            position: 0.0,
            velocity: 0.0,
            acceleration: 0.0,
            output: [0.0, 0.0, 0.0],
        }}
    }}

    pub fn init(&mut self) {{
        self.position = 0.0;
        self.velocity = 0.0;
        self.acceleration = 0.0;
        self.output = [0.0, 0.0, 0.0];
    }}

    pub fn update(&mut self, _t: f64) {{
        let dt = self.sample_time;
        let predicted_position =
            self.position + self.velocity * dt + 0.5 * self.acceleration * dt * dt;
        let predicted_velocity = self.velocity + self.acceleration * dt;
        let residual = self.input - predicted_position;
        self.position = predicted_position + self.alpha * residual;
        self.velocity = predicted_velocity + (self.beta / dt) * residual;
        self.acceleration += (2.0 * self.gamma / (dt * dt)) * residual;
        self.output = [self.position, self.velocity, self.acceleration];
    }}

    pub fn get_output(&self, port: usize) -> f64 {{
        if port < 3 {{ self.output[port] }} else {{ 0.0 }}
    }}
}}
"""


SENSOR_FUSION_TEMPLATES = {
    "alpha_beta_filter": alpha_beta_filter_template,
    "alpha_beta_gamma_filter": alpha_beta_gamma_filter_template,
}
