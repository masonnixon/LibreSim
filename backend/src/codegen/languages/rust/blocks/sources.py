"""Rust block templates for source blocks."""

from ....models import BlockInfo
from ....random_compat import python_mt19937_state


def template_constant(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Constant block."""
    value = block.parameters.get("value", 1.0)

    # Handle array values
    if isinstance(value, (list, tuple)):
        array_size = len(value)
        values_str = ", ".join(f"{v}_f64" for v in value)
        return f"""
/// {block.name} - Constant source (vector)
#[derive(Clone)]
pub struct {struct_name} {{
    pub output: [f64; {array_size}],
    pub value: [f64; {array_size}],
}}

impl {struct_name} {{
    pub const SIZE: usize = {array_size};

    pub fn new() -> Self {{
        Self {{
            value: [{values_str}],
            output: [{values_str}],
        }}
    }}

    pub fn init(&mut self) {{
        self.output = self.value;
    }}

    pub fn update(&mut self, _t: f64) {{
        self.output = self.value;
    }}

    pub fn get_output(&self, port: usize) -> f64 {{
        if port < {array_size} {{ self.output[port] }} else {{ 0.0 }}
    }}

    pub fn get_output_vector(&self) -> &[f64; {array_size}] {{
        &self.output
    }}
}}

impl Default for {struct_name} {{
    fn default() -> Self {{
        Self::new()
    }}
}}
"""
    else:
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
    step_time = block.parameters.get("step_time", block.parameters.get("stepTime", 1.0))
    initial_value = block.parameters.get("initial_value", block.parameters.get("initialValue", 0.0))
    final_value = block.parameters.get("final_value", block.parameters.get("finalValue", 1.0))
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
    """Generate Rust code for White Noise block.

    Matches OSK WhiteNoise block exactly:
    - Uses variance parameter (power maps to variance)
    - std_dev = sqrt(variance)
    - Uses Mersenne Twister for reproducible sequences matching Python's random.Random
    """
    # Support both 'variance' and 'power' (they map to the same thing)
    variance = block.parameters.get("variance", block.parameters.get("power", 1.0))
    mean = block.parameters.get("mean", 0.0)
    seed = block.parameters.get("seed", None)
    sample_time = block.parameters.get("sampleTime", block.parameters.get("sample_time", 0.0))

    seed_value = seed if seed is not None else 12345
    mt_state, mt_index = python_mt19937_state(seed_value)
    mt_state_values = ", ".join(f"{word}u32" for word in mt_state)

    return f"""
/// {block.name} - White Noise source (matches OSK WhiteNoise exactly)
/// Uses Mersenne Twister PRNG for Python compatibility
pub struct {struct_name} {{
    pub output: f64,
    mean: f64,
    variance: f64,
    std_dev: f64,
    sample_time: f64,
    last_sample_time: f64,
    // Mersenne Twister state
    mt: [u32; 624],
    mti: usize,
    // Gauss state
    spare: f64,
    has_spare: bool,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        let variance = {variance}_f64;
        Self {{
            output: 0.0,
            mean: {mean}_f64,
            variance,
            std_dev: variance.abs().sqrt(),
            sample_time: {sample_time}_f64,
            last_sample_time: f64::NEG_INFINITY,
            mt: [{mt_state_values}],
            mti: {mt_index},
            spare: 0.0,
            has_spare: false,
        }}
    }}

    fn mt_genrand(&mut self) -> u32 {{
        if self.mti >= 624 {{
            for kk in 0..227 {{
                let y = (self.mt[kk] & 0x80000000) | (self.mt[kk+1] & 0x7fffffff);
                self.mt[kk] = self.mt[kk + 397] ^ (y >> 1) ^ (if y & 1 == 1 {{ 0x9908b0df }} else {{ 0 }});
            }}
            for kk in 227..623 {{
                let y = (self.mt[kk] & 0x80000000) | (self.mt[kk+1] & 0x7fffffff);
                self.mt[kk] = self.mt[kk - 227] ^ (y >> 1) ^ (if y & 1 == 1 {{ 0x9908b0df }} else {{ 0 }});
            }}
            let y = (self.mt[623] & 0x80000000) | (self.mt[0] & 0x7fffffff);
            self.mt[623] = self.mt[396] ^ (y >> 1) ^ (if y & 1 == 1 {{ 0x9908b0df }} else {{ 0 }});
            self.mti = 0;
        }}

        let mut y = self.mt[self.mti];
        self.mti += 1;
        y ^= y >> 11;
        y ^= (y << 7) & 0x9d2c5680;
        y ^= (y << 15) & 0xefc60000;
        y ^= y >> 18;
        y
    }}

    fn random(&mut self) -> f64 {{
        let a = (self.mt_genrand() >> 5) as f64;
        let b = (self.mt_genrand() >> 6) as f64;
        (a * 67108864.0 + b) * (1.0 / 9007199254740992.0)
    }}

    // Polar Box-Muller with trig (matches Python's random.gauss() exactly)
    fn gauss(&mut self, mu: f64, sigma: f64) -> f64 {{
        if self.has_spare {{
            self.has_spare = false;
            return mu + sigma * self.spare;
        }}

        let x2pi = self.random() * std::f64::consts::TAU;  // 2*pi
        let g2rad = (-2.0 * (1.0 - self.random()).ln()).sqrt();
        let z = x2pi.cos() * g2rad;
        self.spare = x2pi.sin() * g2rad;
        self.has_spare = true;
        mu + sigma * z
    }}

    pub fn init(&mut self) {{
        // Generate initial noise sample (matches OSK init)
        self.output = self.gauss(self.mean, self.std_dev);
        self.last_sample_time = 0.0;
    }}

    pub fn update(&mut self, t: f64) {{
        // If sample_time is 0, generate new noise every step
        // Otherwise, only generate new noise at sample intervals
        if self.sample_time <= 0.0 {{
            self.output = self.gauss(self.mean, self.std_dev);
        }} else {{
            if t >= self.last_sample_time + self.sample_time {{
                self.output = self.gauss(self.mean, self.std_dev);
                self.last_sample_time = t;
            }}
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

impl Clone for {struct_name} {{
    fn clone(&self) -> Self {{
        Self {{
            output: self.output,
            mean: self.mean,
            variance: self.variance,
            std_dev: self.std_dev,
            sample_time: self.sample_time,
            last_sample_time: self.last_sample_time,
            mt: self.mt,
            mti: self.mti,
            spare: self.spare,
            has_spare: self.has_spare,
        }}
    }}
}}
"""


def template_band_limited_white_noise(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Band-Limited White Noise block.

    Matches OSK BandLimitedWhiteNoise block exactly:
    - Uses noise_power and sample_time parameters
    - std_dev = sqrt(noise_power / sample_time)
    """
    noise_power = block.parameters.get("noisePower", block.parameters.get("noise_power", 0.1))
    sample_time = block.parameters.get("sampleTime", block.parameters.get("sample_time", 0.1))
    seed = block.parameters.get("seed", None)

    # Ensure non-zero sample time
    if sample_time <= 0:
        sample_time = 1e-6

    seed_value = seed if seed is not None else 12345
    mt_state, mt_index = python_mt19937_state(seed_value)
    mt_state_values = ", ".join(f"{word}u32" for word in mt_state)

    return f"""
/// {block.name} - Band-Limited White Noise source (matches OSK BandLimitedWhiteNoise exactly)
pub struct {struct_name} {{
    pub output: f64,
    noise_power: f64,
    sample_time: f64,
    std_dev: f64,
    last_sample_time: f64,
    mt: [u32; 624],
    mti: usize,
    spare: f64,
    has_spare: bool,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        let noise_power = {noise_power}_f64;
        let sample_time = {sample_time}_f64.max(1e-6);
        Self {{
            output: 0.0,
            noise_power,
            sample_time,
            std_dev: (noise_power / sample_time).sqrt(),
            last_sample_time: f64::NEG_INFINITY,
            mt: [{mt_state_values}],
            mti: {mt_index},
            spare: 0.0,
            has_spare: false,
        }}
    }}

    fn mt_genrand(&mut self) -> u32 {{
        if self.mti >= 624 {{
            for kk in 0..227 {{
                let y = (self.mt[kk] & 0x80000000) | (self.mt[kk+1] & 0x7fffffff);
                self.mt[kk] = self.mt[kk + 397] ^ (y >> 1) ^ (if y & 1 == 1 {{ 0x9908b0df }} else {{ 0 }});
            }}
            for kk in 227..623 {{
                let y = (self.mt[kk] & 0x80000000) | (self.mt[kk+1] & 0x7fffffff);
                self.mt[kk] = self.mt[kk - 227] ^ (y >> 1) ^ (if y & 1 == 1 {{ 0x9908b0df }} else {{ 0 }});
            }}
            let y = (self.mt[623] & 0x80000000) | (self.mt[0] & 0x7fffffff);
            self.mt[623] = self.mt[396] ^ (y >> 1) ^ (if y & 1 == 1 {{ 0x9908b0df }} else {{ 0 }});
            self.mti = 0;
        }}

        let mut y = self.mt[self.mti];
        self.mti += 1;
        y ^= y >> 11;
        y ^= (y << 7) & 0x9d2c5680;
        y ^= (y << 15) & 0xefc60000;
        y ^= y >> 18;
        y
    }}

    fn random(&mut self) -> f64 {{
        let a = (self.mt_genrand() >> 5) as f64;
        let b = (self.mt_genrand() >> 6) as f64;
        (a * 67108864.0 + b) * (1.0 / 9007199254740992.0)
    }}

    // Polar Box-Muller with trig (matches Python's random.gauss() exactly)
    fn gauss(&mut self) -> f64 {{
        if self.has_spare {{
            self.has_spare = false;
            return self.spare * self.std_dev;
        }}

        let x2pi = self.random() * std::f64::consts::TAU;
        let g2rad = (-2.0 * (1.0 - self.random()).ln()).sqrt();
        let z = x2pi.cos() * g2rad;
        self.spare = x2pi.sin() * g2rad;
        self.has_spare = true;
        z * self.std_dev
    }}

    pub fn init(&mut self) {{
        self.output = self.gauss();
        self.last_sample_time = 0.0;
    }}

    pub fn update(&mut self, t: f64) {{
        if t >= self.last_sample_time + self.sample_time - 1e-10 {{
            self.output = self.gauss();
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

impl Clone for {struct_name} {{
    fn clone(&self) -> Self {{
        Self {{
            output: self.output,
            noise_power: self.noise_power,
            sample_time: self.sample_time,
            std_dev: self.std_dev,
            last_sample_time: self.last_sample_time,
            mt: self.mt,
            mti: self.mti,
            spare: self.spare,
            has_spare: self.has_spare,
        }}
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
    "band_limited_white_noise": template_band_limited_white_noise,
}
