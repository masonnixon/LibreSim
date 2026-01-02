"""Rust templates for discrete blocks."""

from ....models import BlockInfo


def unit_delay_template(block: BlockInfo, struct_name: str) -> str:
    """Generate UnitDelay block code."""
    initial_condition = block.parameters.get("initialCondition", 0.0)
    sample_time = block.parameters.get("sampleTime", 0.1)

    return f'''
#[derive(Clone)]
pub struct {struct_name} {{
    pub initial_condition: f64,
    pub sample_time: f64,
    pub input: f64,
    pub output: f64,
    prev_value: f64,
    last_sample_time: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            initial_condition: {initial_condition},
            sample_time: {sample_time},
            input: 0.0,
            output: {initial_condition},
            prev_value: {initial_condition},
            last_sample_time: f64::NEG_INFINITY,
        }}
    }}

    pub fn init(&mut self) {{
        self.output = self.initial_condition;
        self.prev_value = self.initial_condition;
        self.last_sample_time = f64::NEG_INFINITY;
    }}

    pub fn update(&mut self, t: f64) {{
        if t - self.last_sample_time >= self.sample_time - 1e-10 {{
            self.output = self.prev_value;
            self.prev_value = self.input;
            self.last_sample_time = t;
        }}
    }}

    pub fn get_output(&self, _port: i32) -> f64 {{
        self.output
    }}
}}

impl Default for {struct_name} {{
    fn default() -> Self {{
        Self::new()
    }}
}}
'''


def zero_order_hold_template(block: BlockInfo, struct_name: str) -> str:
    """Generate ZeroOrderHold block code."""
    sample_time = block.parameters.get("sampleTime", 0.1)

    return f'''
#[derive(Clone)]
pub struct {struct_name} {{
    pub sample_time: f64,
    pub input: f64,
    pub output: f64,
    held_value: f64,
    last_sample_time: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            sample_time: {sample_time},
            input: 0.0,
            output: 0.0,
            held_value: 0.0,
            last_sample_time: f64::NEG_INFINITY,
        }}
    }}

    pub fn init(&mut self) {{
        self.held_value = 0.0;
        self.output = 0.0;
        self.last_sample_time = f64::NEG_INFINITY;
    }}

    pub fn update(&mut self, t: f64) {{
        if t - self.last_sample_time >= self.sample_time - 1e-10 {{
            self.held_value = self.input;
            self.last_sample_time = t;
        }}
        self.output = self.held_value;
    }}

    pub fn get_output(&self, _port: i32) -> f64 {{
        self.output
    }}
}}

impl Default for {struct_name} {{
    fn default() -> Self {{
        Self::new()
    }}
}}
'''


def first_order_hold_template(block: BlockInfo, struct_name: str) -> str:
    """Generate FirstOrderHold block code."""
    sample_time = block.parameters.get("sampleTime", 0.1)

    return f'''
#[derive(Clone)]
pub struct {struct_name} {{
    pub sample_time: f64,
    pub input: f64,
    pub output: f64,
    prev_value: f64,
    curr_value: f64,
    last_sample_time: f64,
    slope: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            sample_time: {sample_time},
            input: 0.0,
            output: 0.0,
            prev_value: 0.0,
            curr_value: 0.0,
            last_sample_time: f64::NEG_INFINITY,
            slope: 0.0,
        }}
    }}

    pub fn init(&mut self) {{
        self.prev_value = 0.0;
        self.curr_value = 0.0;
        self.slope = 0.0;
        self.output = 0.0;
        self.last_sample_time = f64::NEG_INFINITY;
    }}

    pub fn update(&mut self, t: f64) {{
        if t - self.last_sample_time >= self.sample_time - 1e-10 {{
            self.prev_value = self.curr_value;
            self.curr_value = self.input;
            self.slope = (self.curr_value - self.prev_value) / self.sample_time;
            self.last_sample_time = t;
        }}
        // Linear interpolation
        let dt = t - self.last_sample_time;
        self.output = self.curr_value + self.slope * dt;
    }}

    pub fn get_output(&self, _port: i32) -> f64 {{
        self.output
    }}
}}

impl Default for {struct_name} {{
    fn default() -> Self {{
        Self::new()
    }}
}}
'''


def discrete_integrator_template(block: BlockInfo, struct_name: str) -> str:
    """Generate DiscreteIntegrator block code."""
    initial_condition = block.parameters.get("initialCondition", 0.0)
    sample_time = block.parameters.get("sampleTime", 0.1)
    method = block.parameters.get("method", "forward")

    # Map method to enum
    method_map = {"forward": "Forward", "backward": "Backward", "trapezoidal": "Trapezoidal"}
    method_enum = method_map.get(method, "Forward")

    return f'''
#[derive(Clone, Copy, PartialEq)]
pub enum IntegrationMethod {{
    Forward,
    Backward,
    Trapezoidal,
}}

#[derive(Clone)]
pub struct {struct_name} {{
    pub initial_condition: f64,
    pub sample_time: f64,
    pub method: IntegrationMethod,
    pub input: f64,
    pub output: f64,
    prev_input: f64,
    state: f64,
    last_sample_time: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            initial_condition: {initial_condition},
            sample_time: {sample_time},
            method: IntegrationMethod::{method_enum},
            input: 0.0,
            output: {initial_condition},
            prev_input: 0.0,
            state: {initial_condition},
            last_sample_time: f64::NEG_INFINITY,
        }}
    }}

    pub fn init(&mut self) {{
        self.state = self.initial_condition;
        self.output = self.initial_condition;
        self.prev_input = 0.0;
        self.last_sample_time = f64::NEG_INFINITY;
    }}

    pub fn update(&mut self, t: f64) {{
        if t - self.last_sample_time >= self.sample_time - 1e-10 {{
            match self.method {{
                IntegrationMethod::Forward => {{
                    self.state += self.sample_time * self.prev_input;
                }}
                IntegrationMethod::Backward => {{
                    self.state += self.sample_time * self.input;
                }}
                IntegrationMethod::Trapezoidal => {{
                    self.state += self.sample_time / 2.0 * (self.input + self.prev_input);
                }}
            }}
            self.prev_input = self.input;
            self.last_sample_time = t;
        }}
        self.output = self.state;
    }}

    pub fn get_output(&self, _port: i32) -> f64 {{
        self.output
    }}
}}

impl Default for {struct_name} {{
    fn default() -> Self {{
        Self::new()
    }}
}}
'''


def discrete_derivative_template(block: BlockInfo, struct_name: str) -> str:
    """Generate DiscreteDerivative block code."""
    sample_time = block.parameters.get("sampleTime", 0.1)

    return f'''
#[derive(Clone)]
pub struct {struct_name} {{
    pub sample_time: f64,
    pub input: f64,
    pub output: f64,
    prev_input: f64,
    last_sample_time: f64,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            sample_time: {sample_time},
            input: 0.0,
            output: 0.0,
            prev_input: 0.0,
            last_sample_time: f64::NEG_INFINITY,
        }}
    }}

    pub fn init(&mut self) {{
        self.prev_input = 0.0;
        self.output = 0.0;
        self.last_sample_time = f64::NEG_INFINITY;
    }}

    pub fn update(&mut self, t: f64) {{
        if t - self.last_sample_time >= self.sample_time - 1e-10 {{
            self.output = (self.input - self.prev_input) / self.sample_time;
            self.prev_input = self.input;
            self.last_sample_time = t;
        }}
    }}

    pub fn get_output(&self, _port: i32) -> f64 {{
        self.output
    }}
}}

impl Default for {struct_name} {{
    fn default() -> Self {{
        Self::new()
    }}
}}
'''


def discrete_transfer_function_template(block: BlockInfo, struct_name: str) -> str:
    """Generate DiscreteTransferFunction block code."""
    numerator = block.parameters.get("numerator", [1.0])
    denominator = block.parameters.get("denominator", [1.0, -0.5])
    sample_time = block.parameters.get("sampleTime", 0.1)

    if not isinstance(numerator, list):
        numerator = [numerator]
    if not isinstance(denominator, list):
        denominator = [denominator]

    order = max(len(numerator), len(denominator)) - 1
    num_len = len(numerator)
    den_len = len(denominator)

    # Format arrays for Rust
    num_str = ", ".join(f"{n}_f64" for n in numerator)
    den_str = ", ".join(f"{d}_f64" for d in denominator)

    return f'''
#[derive(Clone)]
pub struct {struct_name} {{
    pub numerator: [f64; {num_len}],
    pub denominator: [f64; {den_len}],
    pub sample_time: f64,
    pub input: f64,
    pub output: f64,
    input_history: [f64; {order + 1}],
    output_history: [f64; {order + 1}],
    last_sample_time: f64,
}}

impl {struct_name} {{
    pub const ORDER: usize = {order};

    pub fn new() -> Self {{
        Self {{
            numerator: [{num_str}],
            denominator: [{den_str}],
            sample_time: {sample_time},
            input: 0.0,
            output: 0.0,
            input_history: [0.0; {order + 1}],
            output_history: [0.0; {order + 1}],
            last_sample_time: f64::NEG_INFINITY,
        }}
    }}

    pub fn init(&mut self) {{
        self.input_history = [0.0; {order + 1}];
        self.output_history = [0.0; {order + 1}];
        self.output = 0.0;
        self.last_sample_time = f64::NEG_INFINITY;
    }}

    pub fn update(&mut self, t: f64) {{
        if t - self.last_sample_time >= self.sample_time - 1e-10 {{
            // Shift histories
            for i in (1..={order}).rev() {{
                self.input_history[i] = self.input_history[i - 1];
                self.output_history[i] = self.output_history[i - 1];
            }}
            self.input_history[0] = self.input;

            // Compute new output
            let a0 = self.denominator[0];
            let mut new_output = 0.0;

            for (i, &b) in self.numerator.iter().enumerate() {{
                if i < self.input_history.len() {{
                    new_output += (b / a0) * self.input_history[i];
                }}
            }}

            for (i, &a) in self.denominator.iter().enumerate().skip(1) {{
                if i < self.output_history.len() {{
                    new_output -= (a / a0) * self.output_history[i];
                }}
            }}

            self.output_history[0] = new_output;
            self.output = new_output;
            self.last_sample_time = t;
        }}
    }}

    pub fn get_output(&self, _port: i32) -> f64 {{
        self.output
    }}
}}

impl Default for {struct_name} {{
    fn default() -> Self {{
        Self::new()
    }}
}}
'''


def memory_template(block: BlockInfo, struct_name: str) -> str:
    """Generate Memory block code."""
    initial_condition = block.parameters.get("initialCondition", 0.0)

    return f'''
#[derive(Clone)]
pub struct {struct_name} {{
    pub initial_condition: f64,
    pub input: f64,
    pub output: f64,
    prev_value: f64,
    first_step: bool,
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            initial_condition: {initial_condition},
            input: 0.0,
            output: {initial_condition},
            prev_value: {initial_condition},
            first_step: true,
        }}
    }}

    pub fn init(&mut self) {{
        self.prev_value = self.initial_condition;
        self.output = self.initial_condition;
        self.first_step = true;
    }}

    pub fn update(&mut self, t: f64) {{
        let _ = t;  // unused
        if self.first_step {{
            self.output = self.initial_condition;
            self.first_step = false;
        }} else {{
            self.output = self.prev_value;
        }}
        self.prev_value = self.input;
    }}

    pub fn get_output(&self, _port: i32) -> f64 {{
        self.output
    }}
}}

impl Default for {struct_name} {{
    fn default() -> Self {{
        Self::new()
    }}
}}
'''


# Template registry for discrete blocks
DISCRETE_TEMPLATES = {
    "unit_delay": unit_delay_template,
    "zero_order_hold": zero_order_hold_template,
    "first_order_hold": first_order_hold_template,
    "discrete_integrator": discrete_integrator_template,
    "discrete_derivative": discrete_derivative_template,
    "discrete_transfer_function": discrete_transfer_function_template,
    "memory": memory_template,
}
