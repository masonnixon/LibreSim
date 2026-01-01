"""Rust templates for nonlinear blocks."""

from ....models import BlockInfo


def template_lookup_table_1d(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for LookupTable1D block."""
    x_data = block.parameters.get("xData", [0.0, 1.0])
    y_data = block.parameters.get("yData", [0.0, 1.0])
    n = len(x_data)

    x_str = ", ".join(f"{v}_f64" for v in x_data)
    y_str = ", ".join(f"{v}_f64" for v in y_data)

    return f"""
/// {block.name} - 1D Lookup Table
#[derive(Clone)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub x_data: Vec<f64>,
    pub y_data: Vec<f64>,
}}

impl Default for {struct_name} {{
    fn default() -> Self {{
        Self::new()
    }}
}}

impl {struct_name} {{
    pub const TABLE_SIZE: usize = {n};

    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: 0.0,
            x_data: vec![{x_str}],
            y_data: vec![{y_str}],
        }}
    }}

    pub fn init(&mut self) {{
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        let x = self.input;
        let n = self.x_data.len();

        if n < 2 {{
            self.output = self.y_data[0];
            return;
        }}

        if x <= self.x_data[0] {{
            self.output = self.y_data[0];
        }} else if x >= self.x_data[n - 1] {{
            self.output = self.y_data[n - 1];
        }} else {{
            for i in 0..n - 1 {{
                if self.x_data[i] <= x && x <= self.x_data[i + 1] {{
                    let t_interp = (x - self.x_data[i]) / (self.x_data[i + 1] - self.x_data[i]);
                    self.output = self.y_data[i] + t_interp * (self.y_data[i + 1] - self.y_data[i]);
                    break;
                }}
            }}
        }}
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_quantizer(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Quantizer block."""
    interval = block.parameters.get("interval", 1.0)

    return f"""
/// {block.name} - Quantizer
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub interval: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: 0.0,
            interval: {interval}_f64,
        }}
    }}

    pub fn init(&mut self) {{
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        self.output = (self.input / self.interval).round() * self.interval;
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_relay(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Relay (hysteresis) block."""
    on_point = block.parameters.get("onPoint", 0.5)
    off_point = block.parameters.get("offPoint", -0.5)
    on_output = block.parameters.get("onOutput", 1.0)
    off_output = block.parameters.get("offOutput", -1.0)

    return f"""
/// {block.name} - Relay (hysteresis)
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub on_point: f64,
    pub off_point: f64,
    pub on_output: f64,
    pub off_output: f64,
    pub state: bool,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: {off_output}_f64,
            on_point: {on_point}_f64,
            off_point: {off_point}_f64,
            on_output: {on_output}_f64,
            off_output: {off_output}_f64,
            state: false,
        }}
    }}

    pub fn init(&mut self) {{
        self.output = self.off_output;
        self.state = false;
    }}

    pub fn update(&mut self, _t: f64) {{
        if self.state {{
            if self.input <= self.off_point {{
                self.state = false;
                self.output = self.off_output;
            }} else {{
                self.output = self.on_output;
            }}
        }} else {{
            if self.input >= self.on_point {{
                self.state = true;
                self.output = self.on_output;
            }} else {{
                self.output = self.off_output;
            }}
        }}
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_coulomb(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Coulomb friction block."""
    offset = block.parameters.get("offset", 0.0)
    gain = block.parameters.get("gain", 1.0)

    return f"""
/// {block.name} - Coulomb Friction
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub offset: f64,
    pub gain: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: 0.0,
            offset: {offset}_f64,
            gain: {gain}_f64,
        }}
    }}

    pub fn init(&mut self) {{
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        if self.input > 0.0 {{
            self.output = self.gain;
        }} else if self.input < 0.0 {{
            self.output = -self.gain;
        }} else {{
            self.output = 0.0;
        }}
        self.output += self.offset;
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_wrap_to_range(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for WrapToRange block."""
    lower = block.parameters.get("lower", -3.14159265)
    upper = block.parameters.get("upper", 3.14159265)

    return f"""
/// {block.name} - Wrap to Range
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub lower: f64,
    pub upper: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: 0.0,
            lower: {lower}_f64,
            upper: {upper}_f64,
        }}
    }}

    pub fn init(&mut self) {{
        self.output = 0.0;
    }}

    pub fn update(&mut self, _t: f64) {{
        let range = self.upper - self.lower;
        if range <= 0.0 {{
            self.output = self.input;
            return;
        }}

        let mut val = (self.input - self.lower) % range;
        if val < 0.0 {{
            val += range;
        }}
        self.output = val + self.lower;
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_hit_crossing(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for HitCrossing block."""
    offset = block.parameters.get("offset", 0.0)
    direction = block.parameters.get("direction", "rising")

    dir_code = {
        "rising": "let crossed = prev_val < 0.0 && curr_val >= 0.0;",
        "falling": "let crossed = prev_val > 0.0 && curr_val <= 0.0;",
        "either": "let crossed = (prev_val < 0.0 && curr_val >= 0.0) || (prev_val > 0.0 && curr_val <= 0.0);",
    }.get(direction, "let crossed = false;")

    return f"""
/// {block.name} - Hit/Zero Crossing Detector
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub offset: f64,
    pub prev_input: f64,
    pub first_step: bool,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: 0.0,
            offset: {offset}_f64,
            prev_input: 0.0,
            first_step: true,
        }}
    }}

    pub fn init(&mut self) {{
        self.output = 0.0;
        self.prev_input = 0.0;
        self.first_step = true;
    }}

    pub fn update(&mut self, _t: f64) {{
        if self.first_step {{
            self.first_step = false;
            self.prev_input = self.input;
            self.output = 0.0;
            return;
        }}

        let prev_val = self.prev_input - self.offset;
        let curr_val = self.input - self.offset;
        {dir_code}

        self.output = if crossed {{ 1.0 }} else {{ 0.0 }};
        self.prev_input = self.input;
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


def template_stiction(block: BlockInfo, struct_name: str) -> str:
    """Generate Rust code for Stiction block."""
    static_friction = block.parameters.get("staticFriction", 1.0)
    kinetic_friction = block.parameters.get("kineticFriction", 0.8)

    return f"""
/// {block.name} - Stiction
#[derive(Clone, Default)]
pub struct {struct_name} {{
    pub input: f64,
    pub output: f64,
    pub static_friction: f64,
    pub kinetic_friction: f64,
    pub is_moving: bool,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            input: 0.0,
            output: 0.0,
            static_friction: {static_friction}_f64,
            kinetic_friction: {kinetic_friction}_f64,
            is_moving: false,
        }}
    }}

    pub fn init(&mut self) {{
        self.output = 0.0;
        self.is_moving = false;
    }}

    pub fn update(&mut self, _t: f64) {{
        if !self.is_moving {{
            if self.input.abs() > self.static_friction {{
                self.is_moving = true;
                self.output = if self.input > 0.0 {{
                    self.input - self.kinetic_friction
                }} else {{
                    self.input + self.kinetic_friction
                }};
            }} else {{
                self.output = 0.0;
            }}
        }} else {{
            if self.input > self.kinetic_friction {{
                self.output = self.input - self.kinetic_friction;
            }} else if self.input < -self.kinetic_friction {{
                self.output = self.input + self.kinetic_friction;
            }} else {{
                self.is_moving = false;
                self.output = 0.0;
            }}
        }}
    }}

    pub fn get_output(&self, _port: usize) -> f64 {{
        self.output
    }}
}}
"""


NONLINEAR_TEMPLATES = {
    "lookup_table_1d": template_lookup_table_1d,
    "quantizer": template_quantizer,
    "relay": template_relay,
    "coulomb": template_coulomb,
    "wrap_to_range": template_wrap_to_range,
    "hit_crossing": template_hit_crossing,
    "stiction": template_stiction,
}
