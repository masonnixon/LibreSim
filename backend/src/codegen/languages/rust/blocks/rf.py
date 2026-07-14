"""Rust templates for RF blocks."""

from ....models import BlockInfo


def rf_budget_element_template(block: BlockInfo, struct_name: str) -> str:
    """Generate a three-port cascaded RF budget element."""
    gain_db = block.parameters.get("gainDb", 0.0)
    noise_figure_db = block.parameters.get("noiseFigureDb", 0.0)
    return f"""
/// {block.name} - Cascaded RF budget element
#[derive(Clone)]
pub struct {struct_name} {{
    pub gain_db: f64,
    pub noise_figure_db: f64,
    pub input: f64,
    pub input1: f64,
    pub input2: f64,
    pub output: [f64; 3],
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            gain_db: {gain_db},
            noise_figure_db: {noise_figure_db},
            input: 0.0,
            input1: 0.0,
            input2: 0.0,
            output: [0.0, 0.0, 0.0],
        }}
    }}

    pub fn init(&mut self) {{
        self.output = [0.0, 0.0, 0.0];
    }}

    pub fn update(&mut self, _t: f64) {{
        self.output[0] = self.input + self.gain_db;
        self.output[1] = self.input1 + self.gain_db;
        if self.input1 == 0.0 && self.input2 == 0.0 {{
            self.output[2] = self.noise_figure_db;
        }} else {{
            let old_factor = 10.0_f64.powf(self.input2 / 10.0);
            let element_factor = 10.0_f64.powf(self.noise_figure_db / 10.0);
            let cascade_gain = 10.0_f64.powf(self.input1 / 10.0);
            let new_factor = if cascade_gain > 1e-10 {{
                old_factor + (element_factor - 1.0) / cascade_gain
            }} else {{
                old_factor + element_factor - 1.0
            }};
            self.output[2] = 10.0 * new_factor.max(1.0).log10();
        }}
    }}

    pub fn get_output(&self, port: usize) -> f64 {{
        if port < 3 {{ self.output[port] }} else {{ 0.0 }}
    }}
}}
"""


def am_modulator_template(block: BlockInfo, struct_name: str) -> str:
    """Generate an AM modulator with external or internal carrier semantics."""
    modulation_index = block.parameters.get("modulationIndex", 0.5)
    carrier_freq = block.parameters.get(
        "carrierFreq", block.parameters.get("carrierFreqHz", 1e6)
    )
    carrier_amplitude = block.parameters.get("carrierAmplitude", 1.0)
    if len(block.input_dimensions) > 1:
        output_expression = "self.input1 * envelope"
    else:
        output_expression = (
            "self.carrier_amplitude * envelope * "
            "(2.0 * std::f64::consts::PI * self.carrier_freq * t).cos()"
        )
    return f"""
/// {block.name} - Amplitude modulator
#[derive(Clone)]
pub struct {struct_name} {{
    pub modulation_index: f64,
    pub carrier_freq: f64,
    pub carrier_amplitude: f64,
    pub input: f64,
    pub input1: f64,
    pub output: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            modulation_index: {modulation_index},
            carrier_freq: {carrier_freq},
            carrier_amplitude: {carrier_amplitude},
            input: 0.0,
            input1: 0.0,
            output: 0.0,
        }}
    }}

    pub fn init(&mut self) {{
        self.output = 0.0;
    }}

    pub fn update(&mut self, t: f64) {{
        let _ = t;
        let envelope = 1.0 + self.modulation_index * self.input;
        self.output = {output_expression};
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


RF_TEMPLATES = {
    "rf_budget_element": rf_budget_element_template,
    "am_modulator": am_modulator_template,
}
