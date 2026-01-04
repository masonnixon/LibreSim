"""C block templates for source blocks."""

from ....models import BlockInfo


def template_constant(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Constant block."""
    value = block.parameters.get("value", 1.0)

    # Handle array values
    if isinstance(value, (list, tuple)):
        array_size = len(value)
        values_str = ", ".join(str(v) for v in value)
        return f"""
// {block.name} - Constant source (vector)
#define {struct_name.upper()}_SIZE {array_size}
typedef struct {{
    double output[{array_size}];
    double value[{array_size}];
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    double init_vals[{array_size}] = {{{values_str}}};
    for (int i = 0; i < {array_size}; i++) {{
        b->value[i] = init_vals[i];
        b->output[i] = b->value[i];
    }}
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    for (int i = 0; i < {array_size}; i++) {{
        b->output[i] = b->value[i];
    }}
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    if (port >= 0 && port < {array_size}) return b->output[port];
    return 0.0;
}}

void {struct_name}_get_output_vector({struct_name}* b, double* out, int size) {{
    int n = size < {array_size} ? size : {array_size};
    for (int i = 0; i < n; i++) out[i] = b->output[i];
}}
"""
    else:
        return f"""
// {block.name} - Constant source
typedef struct {{
    double output;
    double value;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->value = {value};
    b->output = b->value;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;  // Unused
    b->output = b->value;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_step(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Step block."""
    step_time = block.parameters.get("step_time", block.parameters.get("stepTime", 1.0))
    initial_value = block.parameters.get("initial_value", block.parameters.get("initialValue", 0.0))
    final_value = block.parameters.get("final_value", block.parameters.get("finalValue", 1.0))
    return f"""
// {block.name} - Step source
typedef struct {{
    double output;
    double step_time;
    double initial_value;
    double final_value;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->step_time = {step_time};
    b->initial_value = {initial_value};
    b->final_value = {final_value};
    b->output = b->initial_value;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    b->output = (t >= b->step_time) ? b->final_value : b->initial_value;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_ramp(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Ramp block."""
    slope = block.parameters.get("slope", 1.0)
    start_time = block.parameters.get("start_time", 0.0)
    initial_output = block.parameters.get("initial_output", 0.0)
    return f"""
// {block.name} - Ramp source
typedef struct {{
    double output;
    double slope;
    double start_time;
    double initial_output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->slope = {slope};
    b->start_time = {start_time};
    b->initial_output = {initial_output};
    b->output = b->initial_output;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    if (t >= b->start_time) {{
        b->output = b->initial_output + b->slope * (t - b->start_time);
    }} else {{
        b->output = b->initial_output;
    }}
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_sine_wave(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Sine Wave block."""
    amplitude = block.parameters.get("amplitude", 1.0)
    frequency = block.parameters.get("frequency", 1.0)
    phase = block.parameters.get("phase", 0.0)
    bias = block.parameters.get("bias", 0.0)
    return f"""
// {block.name} - Sine wave source
typedef struct {{
    double output;
    double amplitude;
    double frequency;
    double phase;
    double bias;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->amplitude = {amplitude};
    b->frequency = {frequency};
    b->phase = {phase};
    b->bias = {bias};
    b->output = b->bias + b->amplitude * sin(b->phase);
}}

void {struct_name}_update({struct_name}* b, double t) {{
    b->output = b->bias + b->amplitude * sin(2.0 * M_PI * b->frequency * t + b->phase);
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_pulse(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Pulse Generator block."""
    amplitude = block.parameters.get("amplitude", 1.0)
    period = block.parameters.get("period", 1.0)
    pulse_width = block.parameters.get("pulse_width", 50.0)  # As percentage
    phase_delay = block.parameters.get("phase_delay", 0.0)
    return f"""
// {block.name} - Pulse generator
typedef struct {{
    double output;
    double amplitude;
    double period;
    double duty_cycle;
    double phase_delay;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->amplitude = {amplitude};
    b->period = {period};
    b->duty_cycle = {pulse_width} / 100.0;
    b->phase_delay = {phase_delay};
    b->output = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    double t_adj = t - b->phase_delay;
    if (t_adj < 0) {{
        b->output = 0.0;
    }} else {{
        double phase = fmod(t_adj, b->period) / b->period;
        b->output = (phase < b->duty_cycle) ? b->amplitude : 0.0;
    }}
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_clock(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Clock block."""
    return f"""
// {block.name} - Clock (outputs simulation time)
typedef struct {{
    double output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->output = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    b->output = t;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_ground(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Ground block."""
    return f"""
// {block.name} - Ground (zero output)
typedef struct {{
    double output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->output = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    b->output = 0.0;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_white_noise(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for White Noise block."""
    power = block.parameters.get("power", 1.0)
    sample_time = block.parameters.get("sampleTime", block.parameters.get("sample_time", 0.1))
    # Ensure sample_time is positive to avoid division by zero
    if sample_time <= 0:
        sample_time = 0.01  # Default to 100Hz sampling
    seed = block.parameters.get("seed", 0)

    return f"""
// {block.name} - White Noise source
typedef struct {{
    double power;
    double sample_time;
    double output;
    double last_sample_time;
    double std_dev;
    unsigned int seed;
}} {struct_name};

// Simple Box-Muller transform for Gaussian random numbers
static double {struct_name}_randn({struct_name}* b) {{
    static int have_spare = 0;
    static double spare;

    if (have_spare) {{
        have_spare = 0;
        return spare * b->std_dev;
    }}

    double u, v, s;
    do {{
        b->seed = b->seed * 1103515245 + 12345;
        u = ((double)(b->seed % 65536) / 32768.0) - 1.0;
        b->seed = b->seed * 1103515245 + 12345;
        v = ((double)(b->seed % 65536) / 32768.0) - 1.0;
        s = u * u + v * v;
    }} while (s >= 1.0 || s == 0.0);

    double mul = sqrt(-2.0 * log(s) / s);
    spare = v * mul;
    have_spare = 1;
    return u * mul * b->std_dev;
}}

void {struct_name}_init({struct_name}* b) {{
    b->power = {power};
    b->sample_time = {sample_time};
    b->output = 0.0;
    b->last_sample_time = -1e308;
    b->std_dev = sqrt(b->power / b->sample_time);
    b->seed = {seed if seed else 12345};
}}

void {struct_name}_update({struct_name}* b, double t) {{
    if (t - b->last_sample_time >= b->sample_time - 1e-10) {{
        b->output = {struct_name}_randn(b);
        b->last_sample_time = t;
    }}
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
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
