"""Rust block templates for source blocks."""

from ....models import BlockInfo


def template_constant(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Constant block."""
    value = block.parameters.get("value", 1.0)
    return f"""
/// {block.name} - Constant source
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub output: f64,
    pub value: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            value: {value}_f64,
            output: {value}_f64,
        }}
    }}

    pub fn init(&mut self) {{
        self.output = self.value;
    }}

    pub fn update(&mut self, _t: f64) {{
        self.output = self.value;
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_step(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Step block."""
    step_time = block.parameters.get("step_time", 1.0)
    initial_value = block.parameters.get("initial_value", 0.0)
    final_value = block.parameters.get("final_value", 1.0)
    return f"""
/// {block.name} - Step source
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub output: f64,
    pub step_time: f64,
    pub initial_value: f64,
    pub final_value: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            step_time: {step_time}_f64,
            initial_value: {initial_value}_f64,
            final_value: {final_value}_f64,
            output: {initial_value}_f64,
        }}
    }}

    pub fn init(&mut self) {{
        self.output = self.initial_value;
    }}

    pub fn update(&mut self, t: f64) {{
        self.output = if t >= self.step_time {{
            self.final_value
        }} else {{
            self.initial_value
        }};
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_ramp(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Ramp block."""
    slope = block.parameters.get("slope", 1.0)
    start_time = block.parameters.get("start_time", 0.0)
    initial_output = block.parameters.get("initial_output", 0.0)
    return f"""
/// {block.name} - Ramp source
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub output: f64,
    pub slope: f64,
    pub start_time: f64,
    pub initial_output: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            slope: {slope}_f64,
            start_time: {start_time}_f64,
            initial_output: {initial_output}_f64,
            output: {initial_output}_f64,
        }}
    }}

    pub fn init(&mut self) {{
        self.output = self.initial_output;
    }}

    pub fn update(&mut self, t: f64) {{
        if t >= self.start_time {{
            self.output = self.initial_output + self.slope * (t - self.start_time);
        }} else {{
            self.output = self.initial_output;
        }}
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_sine_wave(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Sine Wave block."""
    amplitude = block.parameters.get("amplitude", 1.0)
    frequency = block.parameters.get("frequency", 1.0)
    phase = block.parameters.get("phase", 0.0)
    bias = block.parameters.get("bias", 0.0)
    return f"""
/// {block.name} - Sine wave source
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub output: f64,
    pub amplitude: f64,
    pub frequency: f64,
    pub phase: f64,
    pub bias: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        let amplitude = {amplitude}_f64;
        let phase = {phase}_f64;
        let bias = {bias}_f64;
        Self {{
            amplitude,
            frequency: {frequency}_f64,
            phase,
            bias,
            output: bias + amplitude * phase.sin(),
        }}
    }}

    pub fn init(&mut self) {{
        self.output = self.bias + self.amplitude * self.phase.sin();
    }}

    pub fn update(&mut self, t: f64) {{
        self.output = self.bias + self.amplitude *
            (2.0 * std::f64::consts::PI * self.frequency * t + self.phase).sin();
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_pulse(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Pulse Generator block."""
    amplitude = block.parameters.get("amplitude", 1.0)
    period = block.parameters.get("period", 1.0)
    pulse_width = block.parameters.get("pulse_width", 50.0)
    phase_delay = block.parameters.get("phase_delay", 0.0)
    return f"""
/// {block.name} - Pulse generator
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub output: f64,
    pub amplitude: f64,
    pub period: f64,
    pub duty_cycle: f64,
    pub phase_delay: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            amplitude: {amplitude}_f64,
            period: {period}_f64,
            duty_cycle: {pulse_width}_f64 / 100.0,
            phase_delay: {phase_delay}_f64,
            output: 0.0,
        }}
    }}

    pub fn init(&mut self) {{
        self.output = 0.0;
    }}

    pub fn update(&mut self, t: f64) {{
        let t_adj = t - self.phase_delay;
        if t_adj < 0.0 {{
            self.output = 0.0;
        }} else {{
            let phase = (t_adj % self.period) / self.period;
            self.output = if phase < self.duty_cycle {{
                self.amplitude
            }} else {{
                0.0
            }};
        }}
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_clock(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Clock block."""
    return f"""
/// {block.name} - Clock (outputs simulation time)
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub output: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{ output: 0.0 }}
    }}

    pub fn init(&mut self) {{
        self.output = 0.0;
    }}

    pub fn update(&mut self, t: f64) {{
        self.output = t;
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_ground(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Ground block."""
    return f"""
/// {block.name} - Ground (zero output)
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub output: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{ output: 0.0 }}
    }}

    pub fn init(&mut self) {{
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        self.output = 0.0;
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_white_noise(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for White Noise block."""
    power = block.parameters.get("power", 1.0)
    sample_time = block.parameters.get("sampleTime", 0.1)
    seed = block.parameters.get("seed", 0)

    return f"""
/// {block.name} - White Noise source
/// Uses a simple LCG-based Box-Muller transform for Gaussian random numbers
pub struct {struct_name} {{
    pub output: f64,
    power: f64,
    sample_time: f64,
    std_dev: f64,
    last_sample_time: f64,
    seed: u64,
    spare: f64,
    has_spare: bool,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        let power = {power}_f64;
        let sample_time = {sample_time}_f64;
        Self {{
            output: 0.0,
            power,
            sample_time,
            std_dev: (power / sample_time).sqrt(),
            last_sample_time: f64::NEG_INFINITY,
            seed: {seed if seed else 12345},
            spare: 0.0,
            has_spare: false,
        }}
    }}

    pub fn init(&mut self) {{
        self.output = 0.0;
        self.last_sample_time = f64::NEG_INFINITY;
        self.has_spare = false;
    }}

    fn randn(&mut self) -> f64 {{
        if self.has_spare {{
            self.has_spare = false;
            return self.spare * self.std_dev;
        }}

        loop {{
            self.seed = self.seed.wrapping_mul(1103515245).wrapping_add(12345);
            let u = ((self.seed % 65536) as f64 / 32768.0) - 1.0;
            self.seed = self.seed.wrapping_mul(1103515245).wrapping_add(12345);
            let v = ((self.seed % 65536) as f64 / 32768.0) - 1.0;
            let s = u * u + v * v;
            if s < 1.0 && s != 0.0 {{
                let mul = (-2.0 * s.ln() / s).sqrt();
                self.spare = v * mul;
                self.has_spare = true;
                return u * mul * self.std_dev;
            }}
        }}
    }}

    pub fn update(&mut self, t: f64) {{
        if t - self.last_sample_time >= self.sample_time - 1e-10 {{
            self.output = self.randn();
            self.last_sample_time = t;
        }}
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}

impl Default for {struct_name} {{
    fn default() -> Self {{
        Self::new()
    }}
}}
"""


SOURCE_TEMPLATES = {
    "constant": template_constant,
    "step": template_step,
    "ramp": template_ramp,
    "sine_wave": template_sine_wave,
    "pulse": template_pulse,
    "clock": template_clock,
    "ground": template_ground,
    "white_noise": template_white_noise,
}
