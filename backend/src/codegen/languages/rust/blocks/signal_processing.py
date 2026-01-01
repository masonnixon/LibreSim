"""Rust templates for signal processing blocks."""

import math
from ....models import BlockInfo


def template_rate_limiter(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for RateLimiter block."""
    rising_slew = block.parameters.get("risingSlewRate", 1.0)
    falling_slew = block.parameters.get("fallingSlewRate", -1.0)
    sample_time = block.parameters.get("sampleTime", 0.01)

    return f"""
/// {block.name} - Rate Limiter
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub rising_slew: f64,
    pub falling_slew: f64,
    pub sample_time: f64,
    pub prev_output: f64,
    pub first_step: bool,
}}

impl Default for {struct_name} {{
    fn default() -> Self {{
        Self::new()
    }}
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: 0.0,
            rising_slew: {rising_slew}_f64,
            falling_slew: {falling_slew}_f64,
            sample_time: {sample_time}_f64,
            prev_output: 0.0,
            first_step: true,
        }}
    }}

    pub fn init(&mut self) {{
        self.output = 0.0;
        self.prev_output = 0.0;
        self.first_step = true;
    }}

    pub fn update(&mut self, _t: f64) {{
        if self.first_step {{
            self.output = self.input;
            self.first_step = false;
        }} else {{
            let delta = self.input - self.prev_output;
            let max_rise = self.rising_slew * self.sample_time;
            let max_fall = self.falling_slew * self.sample_time;

            if delta > max_rise {{
                self.output = self.prev_output + max_rise;
            }} else if delta < max_fall {{
                self.output = self.prev_output + max_fall;
            }} else {{
                self.output = self.input;
            }}
        }}
        self.prev_output = self.output;
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_moving_average(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for MovingAverage block."""
    window_size = block.parameters.get("windowSize", 10)

    return f"""
/// {block.name} - Moving Average Filter
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub buffer: Vec<f64>,
    pub index: usize,
    pub count: usize,
    pub sum: f64,
}}

impl Default for {struct_name} {{
    fn default() -> Self {{
        Self::new()
    }}
}}

impl {struct_name} {{
    pub const WINDOW_SIZE: usize = {window_size};

    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: 0.0,
            buffer: vec![0.0; Self::WINDOW_SIZE],
            index: 0,
            count: 0,
            sum: 0.0,
        }}
    }}

    pub fn init(&mut self) {{
        self.output = 0.0;
        self.buffer.fill(0.0);
        self.index = 0;
        self.count = 0;
        self.sum = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        // Remove old value from sum
        self.sum -= self.buffer[self.index];
        // Add new value
        self.buffer[self.index] = self.input;
        self.sum += self.input;
        // Update index
        self.index = (self.index + 1) % Self::WINDOW_SIZE;
        if self.count < Self::WINDOW_SIZE {{
            self.count += 1;
        }}
        // Compute average
        self.output = if self.count > 0 {{ self.sum / self.count as f64 }} else {{ 0.0 }};
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_low_pass_filter(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for first-order LowPassFilter block."""
    cutoff_freq = block.parameters.get("cutoffFrequency", 10.0)
    sample_time = block.parameters.get("sampleTime", 0.01)

    tau = 1.0 / (2.0 * math.pi * cutoff_freq)
    alpha = sample_time / (tau + sample_time)

    return f"""
/// {block.name} - First-Order Low-Pass Filter
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub alpha: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: 0.0,
            alpha: {alpha}_f64,
        }}
    }}

    pub fn init(&mut self) {{
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        self.output = self.alpha * self.input + (1.0 - self.alpha) * self.output;
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_high_pass_filter(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for first-order HighPassFilter block."""
    cutoff_freq = block.parameters.get("cutoffFrequency", 10.0)
    sample_time = block.parameters.get("sampleTime", 0.01)

    tau = 1.0 / (2.0 * math.pi * cutoff_freq)
    alpha = tau / (tau + sample_time)

    return f"""
/// {block.name} - First-Order High-Pass Filter
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub alpha: f64,
    pub prev_input: f64,
    pub prev_output: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: 0.0,
            alpha: {alpha}_f64,
            prev_input: 0.0,
            prev_output: 0.0,
        }}
    }}

    pub fn init(&mut self) {{
        self.output = 0.0;
        self.prev_input = 0.0;
        self.prev_output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        self.output = self.alpha * (self.prev_output + self.input - self.prev_input);
        self.prev_input = self.input;
        self.prev_output = self.output;
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_band_pass_filter(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for BandPassFilter block."""
    low_cutoff = block.parameters.get("lowCutoffFrequency", 5.0)
    high_cutoff = block.parameters.get("highCutoffFrequency", 50.0)
    sample_time = block.parameters.get("sampleTime", 0.01)

    tau_hp = 1.0 / (2.0 * math.pi * low_cutoff)
    alpha_hp = tau_hp / (tau_hp + sample_time)
    tau_lp = 1.0 / (2.0 * math.pi * high_cutoff)
    alpha_lp = sample_time / (tau_lp + sample_time)

    return f"""
/// {block.name} - Band-Pass Filter (cascaded HP + LP)
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub alpha_hp: f64,
    pub alpha_lp: f64,
    pub hp_prev_input: f64,
    pub hp_prev_output: f64,
    pub lp_output: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: 0.0,
            alpha_hp: {alpha_hp}_f64,
            alpha_lp: {alpha_lp}_f64,
            hp_prev_input: 0.0,
            hp_prev_output: 0.0,
            lp_output: 0.0,
        }}
    }}

    pub fn init(&mut self) {{
        self.output = 0.0;
        self.hp_prev_input = 0.0;
        self.hp_prev_output = 0.0;
        self.lp_output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        // High-pass stage
        let hp_out = self.alpha_hp * (self.hp_prev_output + self.input - self.hp_prev_input);
        self.hp_prev_input = self.input;
        self.hp_prev_output = hp_out;

        // Low-pass stage
        self.lp_output = self.alpha_lp * hp_out + (1.0 - self.alpha_lp) * self.lp_output;
        self.output = self.lp_output;
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_backlash(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Backlash block."""
    deadband = block.parameters.get("deadband", 1.0)
    initial_output = block.parameters.get("initialOutput", 0.0)
    half_width = deadband / 2.0

    return f"""
/// {block.name} - Backlash
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub deadband: f64,
    pub half_width: f64,
    pub prev_output: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: {initial_output}_f64,
            deadband: {deadband}_f64,
            half_width: {half_width}_f64,
            prev_output: {initial_output}_f64,
        }}
    }}

    pub fn init(&mut self) {{
        self.output = {initial_output}_f64;
        self.prev_output = {initial_output}_f64;
    }}

    pub fn update(&mut self, _t: f64) {{
        let diff = self.input - self.prev_output;
        if diff > self.half_width {{
            self.output = self.input - self.half_width;
        }} else if diff < -self.half_width {{
            self.output = self.input + self.half_width;
        }} else {{
            self.output = self.prev_output;
        }}
        self.prev_output = self.output;
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_notch_filter(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for NotchFilter block."""
    notch_freq = block.parameters.get("notchFrequency", 60.0)
    bandwidth = block.parameters.get("bandwidth", 10.0)
    sample_time = block.parameters.get("sampleTime", 0.01)

    fs = 1.0 / sample_time
    omega_0 = 2.0 * math.pi * notch_freq / fs
    bw = 2.0 * math.pi * bandwidth / fs
    alpha = math.sin(omega_0) * math.sinh(
        math.log(2.0) / 2.0 * bw * omega_0 / math.sin(omega_0)
    )

    b0 = 1.0
    b1 = -2.0 * math.cos(omega_0)
    b2 = 1.0
    a0 = 1.0 + alpha
    a1 = -2.0 * math.cos(omega_0)
    a2 = 1.0 - alpha

    b0n = b0 / a0
    b1n = b1 / a0
    b2n = b2 / a0
    a1n = a1 / a0
    a2n = a2 / a0

    return f"""
/// {block.name} - Notch Filter
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub b: [f64; 3],
    pub a: [f64; 3],
    pub x: [f64; 3],  // Input history
    pub y: [f64; 3],  // Output history
}}

impl Default for {struct_name} {{
    fn default() -> Self {{
        Self::new()
    }}
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: 0.0,
            b: [{b0n}_f64, {b1n}_f64, {b2n}_f64],
            a: [1.0_f64, {a1n}_f64, {a2n}_f64],
            x: [0.0; 3],
            y: [0.0; 3],
        }}
    }}

    pub fn init(&mut self) {{
        self.output = 0.0;
        self.x = [0.0; 3];
        self.y = [0.0; 3];
    }}

    pub fn update(&mut self, _t: f64) {{
        // Shift history
        self.x[2] = self.x[1];
        self.x[1] = self.x[0];
        self.x[0] = self.input;
        self.y[2] = self.y[1];
        self.y[1] = self.y[0];

        // Compute output
        self.y[0] = self.b[0] * self.x[0] + self.b[1] * self.x[1] + self.b[2] * self.x[2]
                  - self.a[1] * self.y[1] - self.a[2] * self.y[2];
        self.output = self.y[0];
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


SIGNAL_PROCESSING_TEMPLATES = {
    "rate_limiter": template_rate_limiter,
    "moving_average": template_moving_average,
    "low_pass_filter": template_low_pass_filter,
    "high_pass_filter": template_high_pass_filter,
    "band_pass_filter": template_band_pass_filter,
    "backlash": template_backlash,
    "notch_filter": template_notch_filter,
}
