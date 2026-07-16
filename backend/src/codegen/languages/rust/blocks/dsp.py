"""Rust templates for DSP (Digital Signal Processing) blocks."""

from ....dsp_utils import window_coefficients
from ....models import BlockInfo


def template_fft(block: BlockInfo, struct_name: str) -> str:
    """Generate a real-input DFT with OSK-compatible interleaved output."""
    n_points = block.parameters.get("nPoints", block.parameters.get("n_points", 64))
    return f"""
/// {block.name} - Real-input DFT
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: [f64; {n_points}],
    pub output: [f64; {2 * n_points}],
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{ input: [0.0; {n_points}], output: [0.0; {2 * n_points}] }}
    }}

    pub fn init(&mut self) {{
        self.input = [0.0; {n_points}];
        self.output = [0.0; {2 * n_points}];
    }}

    pub fn update(&mut self, _t: f64) {{
        for k in 0..{n_points} {{
            let mut real_sum = 0.0;
            let mut imag_sum = 0.0;
            for n in 0..{n_points} {{
                let angle = -std::f64::consts::TAU * (k * n) as f64 / {n_points}_f64;
                real_sum += self.input[n] * angle.cos();
                imag_sum += self.input[n] * angle.sin();
            }}
            self.output[2 * k] = real_sum;
            self.output[2 * k + 1] = imag_sum;
        }}
    }}

    pub fn get_output(&self, port: usize) -> f64 {{
        if port < {2 * n_points} {{ self.output[port] }} else {{ 0.0 }}
    }}

    pub fn get_output_vector(&self) -> &[f64; {2 * n_points}] {{
        &self.output
    }}
}}

impl Default for {struct_name} {{
    fn default() -> Self {{ Self::new() }}
}}
"""


def template_window_function(block: BlockInfo, struct_name: str) -> str:
    """Generate a frame window with coefficients identical to the OSK."""
    window_type = block.parameters.get("windowType", block.parameters.get("window_type", "hamming"))
    length = block.parameters.get("length", 64)
    beta = block.parameters.get("beta", 5.0)
    coefficients = window_coefficients(str(window_type), int(length), float(beta))
    values = ", ".join(f"{value}_f64" for value in coefficients)
    return f"""
/// {block.name} - {window_type} window
#[derive(Clone)]
pub struct {struct_name} {{
    pub window: [f64; {length}],
    pub input: [f64; {length}],
    pub output: [f64; {length}],
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            window: [{values}],
            input: [0.0; {length}],
            output: [0.0; {length}],
        }}
    }}

    pub fn init(&mut self) {{
        self.input = [0.0; {length}];
        self.output = [0.0; {length}];
    }}

    pub fn update(&mut self, _t: f64) {{
        for i in 0..{length} {{ self.output[i] = self.input[i] * self.window[i]; }}
    }}

    pub fn get_output(&self, port: usize) -> f64 {{
        if port < {length} {{ self.output[port] }} else {{ 0.0 }}
    }}

    pub fn get_output_vector(&self) -> &[f64; {length}] {{
        &self.output
    }}
}}

impl Default for {struct_name} {{
    fn default() -> Self {{ Self::new() }}
}}
"""


def template_fir_filter(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust FIR filter block code."""
    coefficients = block.parameters.get("coefficients", [1.0])
    if not isinstance(coefficients, list):
        coefficients = [coefficients]

    num_taps = len(coefficients)
    coef_init = ", ".join(f"{c}_f64" for c in coefficients)

    return f"""
/// {block.name} - FIR Filter
#[derive(Clone)]
pub struct {struct_name} {{
    pub coefficients: [f64; {num_taps}],
    pub buffer: [f64; {num_taps}],
    pub input: f64,
    pub output: f64,
}}

impl {struct_name} {{
    pub const NUM_TAPS: usize = {num_taps};

    pub fn new() -> Self {{
        Self {{
            coefficients: [{coef_init}],
            buffer: [0.0; {num_taps}],
            input: 0.0,
            output: 0.0,
        }}
    }}

    pub fn init(&mut self) {{
        self.buffer = [0.0; {num_taps}];
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        // Shift buffer and add new sample
        for i in (1..Self::NUM_TAPS).rev() {{
            self.buffer[i] = self.buffer[i - 1];
        }}
        self.buffer[0] = self.input;

        // Apply FIR filter
        self.output = 0.0;
        for i in 0..Self::NUM_TAPS {{
            self.output += self.coefficients[i] * self.buffer[i];
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


def template_iir_filter(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust IIR filter block code."""
    numerator = block.parameters.get("numerator", [1.0])
    denominator = block.parameters.get("denominator", [1.0])
    if not isinstance(numerator, list):
        numerator = [numerator]
    if not isinstance(denominator, list):
        denominator = [denominator]

    order = max(len(numerator), len(denominator))
    num_init = ", ".join(f"{c}_f64" for c in numerator)
    den_init = ", ".join(f"{c}_f64" for c in denominator)

    return f"""
/// {block.name} - IIR Filter
#[derive(Clone)]
pub struct {struct_name} {{
    pub numerator: [f64; {len(numerator)}],
    pub denominator: [f64; {len(denominator)}],
    pub x_buffer: [f64; {order}],
    pub y_buffer: [f64; {order}],
    pub input: f64,
    pub output: f64,
}}

impl {struct_name} {{
    pub const ORDER: usize = {order};
    pub const NUM_LEN: usize = {len(numerator)};
    pub const DEN_LEN: usize = {len(denominator)};

    pub fn new() -> Self {{
        let mut s = Self {{
            numerator: [{num_init}],
            denominator: [{den_init}],
            x_buffer: [0.0; {order}],
            y_buffer: [0.0; {order}],
            input: 0.0,
            output: 0.0,
        }};
        // Normalize by a0
        if s.denominator[0] != 0.0 {{
            let a0 = s.denominator[0];
            for i in 0..Self::NUM_LEN {{
                s.numerator[i] /= a0;
            }}
            for i in 0..Self::DEN_LEN {{
                s.denominator[i] /= a0;
            }}
        }}
        s
    }}

    pub fn init(&mut self) {{
        self.x_buffer = [0.0; {order}];
        self.y_buffer = [0.0; {order}];
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        // Shift input buffer
        for i in (1..Self::ORDER).rev() {{
            self.x_buffer[i] = self.x_buffer[i - 1];
        }}
        self.x_buffer[0] = self.input;

        // Apply IIR filter
        let mut y = 0.0;
        for i in 0..Self::NUM_LEN.min(Self::ORDER) {{
            y += self.numerator[i] * self.x_buffer[i];
        }}
        for i in 1..Self::DEN_LEN.min(Self::ORDER + 1) {{
            y -= self.denominator[i] * self.y_buffer[i - 1];
        }}

        self.output = y;
        for i in (1..Self::ORDER).rev() {{
            self.y_buffer[i] = self.y_buffer[i - 1];
        }}
        self.y_buffer[0] = y;
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


def template_mean(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust Mean block code."""
    window_size = block.parameters.get("windowSize", block.parameters.get("window_size", 10))

    return f"""
/// {block.name} - Running Mean
#[derive(Clone)]
pub struct {struct_name} {{
    pub buffer: [f64; {window_size}],
    pub count: usize,
    pub index: usize,
    pub sum: f64,
    pub input: f64,
    pub output: f64,
}}

impl {struct_name} {{
    pub const WINDOW_SIZE: usize = {window_size};

    pub fn new() -> Self {{
        Self {{
            buffer: [0.0; {window_size}],
            count: 0,
            index: 0,
            sum: 0.0,
            input: 0.0,
            output: 0.0,
        }}
    }}

    pub fn init(&mut self) {{
        self.buffer = [0.0; {window_size}];
        self.count = 0;
        self.index = 0;
        self.sum = 0.0;
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        // Subtract old value and add new value
        self.sum -= self.buffer[self.index];
        self.buffer[self.index] = self.input;
        self.sum += self.input;

        self.index = (self.index + 1) % Self::WINDOW_SIZE;
        if self.count < Self::WINDOW_SIZE {{
            self.count += 1;
        }}

        // Compute mean
        if self.count > 0 {{
            self.output = self.sum / self.count as f64;
        }} else {{
            self.output = 0.0;
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


def template_variance(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust Variance block code."""
    window_size = block.parameters.get("windowSize", block.parameters.get("window_size", 10))

    return f"""
/// {block.name} - Running Variance
#[derive(Clone)]
pub struct {struct_name} {{
    pub buffer: [f64; {window_size}],
    pub count: usize,
    pub index: usize,
    pub input: f64,
    pub output: f64,
}}

impl {struct_name} {{
    pub const WINDOW_SIZE: usize = {window_size};

    pub fn new() -> Self {{
        Self {{
            buffer: [0.0; {window_size}],
            count: 0,
            index: 0,
            input: 0.0,
            output: 0.0,
        }}
    }}

    pub fn init(&mut self) {{
        self.buffer = [0.0; {window_size}];
        self.count = 0;
        self.index = 0;
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        self.buffer[self.index] = self.input;
        self.index = (self.index + 1) % Self::WINDOW_SIZE;
        if self.count < Self::WINDOW_SIZE {{
            self.count += 1;
        }}

        if self.count > 1 {{
            let mean: f64 = self.buffer[..self.count].iter().sum::<f64>() / self.count as f64;
            let var: f64 = self.buffer[..self.count]
                .iter()
                .map(|&x| (x - mean).powi(2))
                .sum::<f64>() / (self.count - 1) as f64;
            self.output = var;
        }} else {{
            self.output = 0.0;
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


def template_rms(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust RMS block code."""
    window_size = block.parameters.get("windowSize", block.parameters.get("window_size", 10))

    return f"""
/// {block.name} - Running RMS
#[derive(Clone)]
pub struct {struct_name} {{
    pub buffer: [f64; {window_size}],
    pub count: usize,
    pub index: usize,
    pub sum_sq: f64,
    pub input: f64,
    pub output: f64,
}}

impl {struct_name} {{
    pub const WINDOW_SIZE: usize = {window_size};

    pub fn new() -> Self {{
        Self {{
            buffer: [0.0; {window_size}],
            count: 0,
            index: 0,
            sum_sq: 0.0,
            input: 0.0,
            output: 0.0,
        }}
    }}

    pub fn init(&mut self) {{
        self.buffer = [0.0; {window_size}];
        self.count = 0;
        self.index = 0;
        self.sum_sq = 0.0;
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        // Subtract old squared value and add new squared value
        self.sum_sq -= self.buffer[self.index].powi(2);
        self.buffer[self.index] = self.input;
        self.sum_sq += self.input.powi(2);

        self.index = (self.index + 1) % Self::WINDOW_SIZE;
        if self.count < Self::WINDOW_SIZE {{
            self.count += 1;
        }}

        // Compute RMS
        if self.count > 0 {{
            self.output = (self.sum_sq / self.count as f64).sqrt();
        }} else {{
            self.output = 0.0;
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


def template_downsampler(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust Downsampler block code."""
    factor = block.parameters.get("factor", 2)

    return f"""
/// {block.name} - Downsampler
#[derive(Clone)]
pub struct {struct_name} {{
    pub factor: usize,
    pub sample_count: usize,
    pub input: f64,
    pub output: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            factor: {factor},
            sample_count: 0,
            input: 0.0,
            output: 0.0,
        }}
    }}

    pub fn init(&mut self) {{
        self.sample_count = 0;
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        if self.sample_count % self.factor == 0 {{
            self.output = self.input;
        }}
        self.sample_count += 1;
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


def template_upsampler(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust Upsampler block code."""
    factor = block.parameters.get("factor", 2)

    return f"""
/// {block.name} - Upsampler
#[derive(Clone)]
pub struct {struct_name} {{
    pub factor: usize,
    pub phase: usize,
    pub current_sample: f64,
    pub input: f64,
    pub output: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            factor: {factor},
            phase: 0,
            current_sample: 0.0,
            input: 0.0,
            output: 0.0,
        }}
    }}

    pub fn init(&mut self) {{
        self.phase = 0;
        self.current_sample = 0.0;
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        if self.phase == 0 {{
            self.current_sample = self.input;
            self.output = self.current_sample;
        }} else {{
            self.output = 0.0;
        }}
        self.phase = (self.phase + 1) % self.factor;
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


def template_peak_detector(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust Peak Detector block code."""
    threshold = block.parameters.get("threshold", 0.0)

    return f"""
/// {block.name} - Peak Detector
#[derive(Clone)]
pub struct {struct_name} {{
    pub threshold: f64,
    pub prev_prev: f64,
    pub prev: f64,
    pub current: f64,
    pub input: f64,
    pub output: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            threshold: {threshold}_f64,
            prev_prev: 0.0,
            prev: 0.0,
            current: 0.0,
            input: 0.0,
            output: 0.0,
        }}
    }}

    pub fn init(&mut self) {{
        self.prev_prev = 0.0;
        self.prev = 0.0;
        self.current = 0.0;
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        self.prev_prev = self.prev;
        self.prev = self.current;
        self.current = self.input;

        if self.prev > self.prev_prev && self.prev > self.current && self.prev > self.threshold {{
            self.output = 1.0;
        }} else {{
            self.output = 0.0;
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


def template_zero_crossing_detector(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust Zero Crossing Detector block code."""
    direction = block.parameters.get("direction", "both")

    # Encode direction as int for Rust
    direction_code = 0  # both
    if direction == "rising":
        direction_code = 1
    elif direction == "falling":
        direction_code = 2

    return f"""
/// {block.name} - Zero Crossing Detector
#[derive(Clone)]
pub struct {struct_name} {{
    pub direction: i32,  // 0=both, 1=rising, 2=falling
    pub prev: f64,
    pub current: f64,
    pub input: f64,
    pub output: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            direction: {direction_code},
            prev: 0.0,
            current: 0.0,
            input: 0.0,
            output: 0.0,
        }}
    }}

    pub fn init(&mut self) {{
        self.prev = 0.0;
        self.current = 0.0;
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        self.prev = self.current;
        self.current = self.input;

        let is_crossing = match self.direction {{
            1 => self.prev <= 0.0 && self.current > 0.0,
            2 => self.prev >= 0.0 && self.current < 0.0,
            _ => (self.prev <= 0.0 && self.current > 0.0) || (self.prev >= 0.0 && self.current < 0.0),
        }};

        self.output = if is_crossing {{ 1.0 }} else {{ 0.0 }};
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


DSP_TEMPLATES = {
    "fft": template_fft,
    "window_function": template_window_function,
    "fir_filter": template_fir_filter,
    "iir_filter": template_iir_filter,
    "mean": template_mean,
    "variance": template_variance,
    "rms": template_rms,
    "downsampler": template_downsampler,
    "upsampler": template_upsampler,
    "peak_detector": template_peak_detector,
    "zero_crossing_detector": template_zero_crossing_detector,
}
