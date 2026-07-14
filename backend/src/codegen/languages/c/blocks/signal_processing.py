"""C templates for signal processing blocks."""

import math

from ....filter_design import design_analog_filter
from ....models import BlockInfo


def template_rate_limiter(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for RateLimiter block."""
    rising_slew = abs(
        block.parameters.get("risingLimit", block.parameters.get("risingSlewRate", 1.0))
    )
    falling_limit = block.parameters.get(
        "fallingLimit", block.parameters.get("fallingSlewRate", -1.0)
    )
    falling_slew = -abs(falling_limit) if falling_limit < 0 else -rising_slew

    return f"""
// {block.name} - Rate Limiter
typedef struct {{
    double input;
    double output;
    double rising_slew;
    double falling_slew;
    double prev_output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
    b->rising_slew = {rising_slew};
    b->falling_slew = {falling_slew};
    b->prev_output = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t, double dt) {{
    (void)t;
    double delta = b->input - b->prev_output;
    double max_rise = b->rising_slew * dt;
    double max_fall = b->falling_slew * dt;

    if (delta > max_rise) {{
        b->output = b->prev_output + max_rise;
    }} else if (delta < max_fall) {{
        b->output = b->prev_output + max_fall;
    }} else {{
        b->output = b->input;
    }}
    b->prev_output = b->output;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_moving_average(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for MovingAverage block."""
    window_size = block.parameters.get("windowSize", 10)

    return f"""
// {block.name} - Moving Average Filter
#define {struct_name.upper()}_WINDOW_SIZE {window_size}

typedef struct {{
    double input;
    double output;
    double buffer[{struct_name.upper()}_WINDOW_SIZE];
    int index;
    int count;
    double sum;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
    for (int i = 0; i < {struct_name.upper()}_WINDOW_SIZE; i++) {{
        b->buffer[i] = 0.0;
    }}
    b->index = 0;
    b->count = 0;
    b->sum = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    // Remove old value from sum
    b->sum -= b->buffer[b->index];
    // Add new value
    b->buffer[b->index] = b->input;
    b->sum += b->input;
    // Update index
    b->index = (b->index + 1) % {struct_name.upper()}_WINDOW_SIZE;
    if (b->count < {struct_name.upper()}_WINDOW_SIZE) {{
        b->count++;
    }}
    // Compute average
    b->output = (b->count > 0) ? b->sum / b->count : 0.0;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_low_pass_filter(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for first-order LowPassFilter block."""
    cutoff_freq = block.parameters.get("cutoffFrequency", 10.0)
    sample_time = block.step_size

    # Pre-calculate alpha
    tau = 1.0 / (2.0 * math.pi * cutoff_freq)
    alpha = sample_time / (tau + sample_time)

    return f"""
// {block.name} - First-Order Low-Pass Filter
typedef struct {{
    double input;
    double output;
    double alpha;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
    b->alpha = {alpha};
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    // y[n] = alpha * x[n] + (1-alpha) * y[n-1]
    b->output = b->alpha * b->input + (1.0 - b->alpha) * b->output;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_analog_filter(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for an OSK-compatible cascaded analog filter."""
    sections = design_analog_filter(block.parameters, block.step_size)
    initializers = "\n".join(
        f"    b->sections[{index}] = ({struct_name}_Section)"
        f"{{{section.b0!r}, {section.b1!r}, {section.b2!r}, "
        f"{section.a1!r}, {section.a2!r}, 0.0, 0.0, 0.0, 0.0}};"
        for index, section in enumerate(sections)
    )

    return f"""
// {block.name} - Cascaded Analog Filter
typedef struct {{
    double b0, b1, b2, a1, a2;
    double x1, x2, y1, y2;
}} {struct_name}_Section;

typedef struct {{
    double input;
    double output;
    {struct_name}_Section sections[{len(sections)}];
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
{initializers}
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    double value = b->input;
    for (int i = 0; i < {len(sections)}; i++) {{
        {struct_name}_Section* section = &b->sections[i];
        double output = section->b0 * value + section->b1 * section->x1
                      + section->b2 * section->x2 - section->a1 * section->y1
                      - section->a2 * section->y2;
        section->x2 = section->x1;
        section->x1 = value;
        section->y2 = section->y1;
        section->y1 = output;
        value = output;
    }}
    b->output = value;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_high_pass_filter(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for first-order HighPassFilter block."""
    cutoff_freq = block.parameters.get("cutoffFrequency", 10.0)
    sample_time = block.parameters.get("sampleTime", 0.01)

    # Pre-calculate alpha
    tau = 1.0 / (2.0 * math.pi * cutoff_freq)
    alpha = tau / (tau + sample_time)

    return f"""
// {block.name} - First-Order High-Pass Filter
typedef struct {{
    double input;
    double output;
    double alpha;
    double prev_input;
    double prev_output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
    b->alpha = {alpha};
    b->prev_input = 0.0;
    b->prev_output = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    // y[n] = alpha * (y[n-1] + x[n] - x[n-1])
    b->output = b->alpha * (b->prev_output + b->input - b->prev_input);
    b->prev_input = b->input;
    b->prev_output = b->output;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_band_pass_filter(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for BandPassFilter block."""
    low_cutoff = block.parameters.get("lowCutoffFrequency", 5.0)
    high_cutoff = block.parameters.get("highCutoffFrequency", 50.0)
    sample_time = block.parameters.get("sampleTime", 0.01)

    # Pre-calculate coefficients
    tau_hp = 1.0 / (2.0 * math.pi * low_cutoff)
    alpha_hp = tau_hp / (tau_hp + sample_time)
    tau_lp = 1.0 / (2.0 * math.pi * high_cutoff)
    alpha_lp = sample_time / (tau_lp + sample_time)

    return f"""
// {block.name} - Band-Pass Filter (cascaded HP + LP)
typedef struct {{
    double input;
    double output;
    double alpha_hp;
    double alpha_lp;
    double hp_prev_input;
    double hp_prev_output;
    double lp_output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
    b->alpha_hp = {alpha_hp};
    b->alpha_lp = {alpha_lp};
    b->hp_prev_input = 0.0;
    b->hp_prev_output = 0.0;
    b->lp_output = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    // High-pass stage
    double hp_out = b->alpha_hp * (b->hp_prev_output + b->input - b->hp_prev_input);
    b->hp_prev_input = b->input;
    b->hp_prev_output = hp_out;

    // Low-pass stage
    b->lp_output = b->alpha_lp * hp_out + (1.0 - b->alpha_lp) * b->lp_output;
    b->output = b->lp_output;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_backlash(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Backlash block."""
    deadband = block.parameters.get("deadband", 1.0)
    initial_output = block.parameters.get("initialOutput", 0.0)
    half_width = deadband / 2.0

    return f"""
// {block.name} - Backlash
typedef struct {{
    double input;
    double output;
    double deadband;
    double half_width;
    double prev_output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = {initial_output};
    b->deadband = {deadband};
    b->half_width = {half_width};
    b->prev_output = {initial_output};
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    double diff = b->input - b->prev_output;
    if (diff > b->half_width) {{
        b->output = b->input - b->half_width;
    }} else if (diff < -b->half_width) {{
        b->output = b->input + b->half_width;
    }} else {{
        b->output = b->prev_output;
    }}
    b->prev_output = b->output;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_notch_filter(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for NotchFilter block."""
    notch_freq = block.parameters.get("notchFrequency", 60.0)
    bandwidth = block.parameters.get("bandwidth", 10.0)
    sample_time = block.parameters.get("sampleTime", 0.01)

    # Pre-compute coefficients
    fs = 1.0 / sample_time
    omega_0 = 2.0 * math.pi * notch_freq / fs
    bw = 2.0 * math.pi * bandwidth / fs

    alpha = math.sin(omega_0) * math.sinh(math.log(2.0) / 2.0 * bw * omega_0 / math.sin(omega_0))

    b0 = 1.0
    b1 = -2.0 * math.cos(omega_0)
    b2 = 1.0
    a0 = 1.0 + alpha
    a1 = -2.0 * math.cos(omega_0)
    a2 = 1.0 - alpha

    # Normalized coefficients
    b0n = b0 / a0
    b1n = b1 / a0
    b2n = b2 / a0
    a1n = a1 / a0
    a2n = a2 / a0

    return f"""
// {block.name} - Notch Filter
typedef struct {{
    double input;
    double output;
    double b[3];
    double a[3];
    double x[3];  // Input history
    double y[3];  // Output history
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
    b->b[0] = {b0n}; b->b[1] = {b1n}; b->b[2] = {b2n};
    b->a[0] = 1.0; b->a[1] = {a1n}; b->a[2] = {a2n};
    for (int i = 0; i < 3; i++) {{
        b->x[i] = 0.0;
        b->y[i] = 0.0;
    }}
}}

void {struct_name}_update({struct_name}* blk, double t) {{
    (void)t;
    // Shift history
    blk->x[2] = blk->x[1];
    blk->x[1] = blk->x[0];
    blk->x[0] = blk->input;
    blk->y[2] = blk->y[1];
    blk->y[1] = blk->y[0];

    // Compute output
    blk->y[0] = blk->b[0] * blk->x[0] + blk->b[1] * blk->x[1] + blk->b[2] * blk->x[2]
               - blk->a[1] * blk->y[1] - blk->a[2] * blk->y[2];
    blk->output = blk->y[0];
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


SIGNAL_PROCESSING_TEMPLATES = {
    "rate_limiter": template_rate_limiter,
    "moving_average": template_moving_average,
    "low_pass_filter": template_low_pass_filter,
    "analog_filter": template_analog_filter,
    "high_pass_filter": template_high_pass_filter,
    "band_pass_filter": template_band_pass_filter,
    "backlash": template_backlash,
    "notch_filter": template_notch_filter,
}
