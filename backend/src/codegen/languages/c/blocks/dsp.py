"""C templates for DSP (Digital Signal Processing) blocks."""

from ....models import BlockInfo


def template_fir_filter(block: BlockInfo, struct_name: str) -> str:
    """Generate C FIR filter block code."""
    coefficients = block.parameters.get("coefficients", [1.0])
    if not isinstance(coefficients, list):
        coefficients = [coefficients]

    num_taps = len(coefficients)
    coef_init = ", ".join(str(c) for c in coefficients)

    return f"""
// {block.name} - FIR Filter
#define {struct_name.upper()}_NUM_TAPS {num_taps}

typedef struct {{
    double coefficients[{struct_name.upper()}_NUM_TAPS];
    double buffer[{struct_name.upper()}_NUM_TAPS];
    double input;
    double output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    double coefs[] = {{{coef_init}}};
    for (int i = 0; i < {struct_name.upper()}_NUM_TAPS; i++) {{
        b->coefficients[i] = coefs[i];
        b->buffer[i] = 0.0;
    }}
    b->input = 0.0;
    b->output = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    // Shift buffer and add new sample
    for (int i = {struct_name.upper()}_NUM_TAPS - 1; i > 0; i--) {{
        b->buffer[i] = b->buffer[i - 1];
    }}
    b->buffer[0] = b->input;

    // Apply FIR filter
    b->output = 0.0;
    for (int i = 0; i < {struct_name.upper()}_NUM_TAPS; i++) {{
        b->output += b->coefficients[i] * b->buffer[i];
    }}
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_iir_filter(block: BlockInfo, struct_name: str) -> str:
    """Generate C IIR filter block code."""
    numerator = block.parameters.get("numerator", [1.0])
    denominator = block.parameters.get("denominator", [1.0])
    if not isinstance(numerator, list):
        numerator = [numerator]
    if not isinstance(denominator, list):
        denominator = [denominator]

    order = max(len(numerator), len(denominator))
    num_init = ", ".join(str(c) for c in numerator)
    den_init = ", ".join(str(c) for c in denominator)

    return f"""
// {block.name} - IIR Filter
#define {struct_name.upper()}_ORDER {order}
#define {struct_name.upper()}_NUM_LEN {len(numerator)}
#define {struct_name.upper()}_DEN_LEN {len(denominator)}

typedef struct {{
    double numerator[{struct_name.upper()}_NUM_LEN];
    double denominator[{struct_name.upper()}_DEN_LEN];
    double x_buffer[{struct_name.upper()}_ORDER];
    double y_buffer[{struct_name.upper()}_ORDER];
    double input;
    double output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    double nums[] = {{{num_init}}};
    double dens[] = {{{den_init}}};
    for (int i = 0; i < {struct_name.upper()}_NUM_LEN; i++) b->numerator[i] = nums[i];
    for (int i = 0; i < {struct_name.upper()}_DEN_LEN; i++) b->denominator[i] = dens[i];
    for (int i = 0; i < {struct_name.upper()}_ORDER; i++) {{
        b->x_buffer[i] = 0.0;
        b->y_buffer[i] = 0.0;
    }}
    b->input = 0.0;
    b->output = 0.0;

    // Normalize by a0
    if (b->denominator[0] != 0.0) {{
        double a0 = b->denominator[0];
        for (int i = 0; i < {struct_name.upper()}_NUM_LEN; i++) b->numerator[i] /= a0;
        for (int i = 0; i < {struct_name.upper()}_DEN_LEN; i++) b->denominator[i] /= a0;
    }}
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    // Shift input buffer
    for (int i = {struct_name.upper()}_ORDER - 1; i > 0; i--) {{
        b->x_buffer[i] = b->x_buffer[i - 1];
    }}
    b->x_buffer[0] = b->input;

    // Apply IIR filter
    double y = 0.0;
    for (int i = 0; i < {struct_name.upper()}_NUM_LEN && i < {struct_name.upper()}_ORDER; i++) {{
        y += b->numerator[i] * b->x_buffer[i];
    }}
    for (int i = 1; i < {struct_name.upper()}_DEN_LEN && i <= {struct_name.upper()}_ORDER; i++) {{
        y -= b->denominator[i] * b->y_buffer[i - 1];
    }}

    b->output = y;
    for (int i = {struct_name.upper()}_ORDER - 1; i > 0; i--) {{
        b->y_buffer[i] = b->y_buffer[i - 1];
    }}
    b->y_buffer[0] = y;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_mean(block: BlockInfo, struct_name: str) -> str:
    """Generate C Mean block code."""
    window_size = block.parameters.get("windowSize", block.parameters.get("window_size", 10))

    return f"""
// {block.name} - Running Mean
#define {struct_name.upper()}_WINDOW_SIZE {window_size}

typedef struct {{
    double buffer[{struct_name.upper()}_WINDOW_SIZE];
    int count;
    int index;
    double sum;
    double input;
    double output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    for (int i = 0; i < {struct_name.upper()}_WINDOW_SIZE; i++) {{
        b->buffer[i] = 0.0;
    }}
    b->count = 0;
    b->index = 0;
    b->sum = 0.0;
    b->input = 0.0;
    b->output = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    // Subtract old value and add new value
    b->sum -= b->buffer[b->index];
    b->buffer[b->index] = b->input;
    b->sum += b->input;

    b->index = (b->index + 1) % {struct_name.upper()}_WINDOW_SIZE;
    if (b->count < {struct_name.upper()}_WINDOW_SIZE) b->count++;

    // Compute mean
    if (b->count > 0) {{
        b->output = b->sum / b->count;
    }} else {{
        b->output = 0.0;
    }}
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_variance(block: BlockInfo, struct_name: str) -> str:
    """Generate C Variance block code."""
    window_size = block.parameters.get("windowSize", block.parameters.get("window_size", 10))

    return f"""
// {block.name} - Running Variance
#define {struct_name.upper()}_WINDOW_SIZE {window_size}

typedef struct {{
    double buffer[{struct_name.upper()}_WINDOW_SIZE];
    int count;
    int index;
    double input;
    double output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    for (int i = 0; i < {struct_name.upper()}_WINDOW_SIZE; i++) {{
        b->buffer[i] = 0.0;
    }}
    b->count = 0;
    b->index = 0;
    b->input = 0.0;
    b->output = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    b->buffer[b->index] = b->input;
    b->index = (b->index + 1) % {struct_name.upper()}_WINDOW_SIZE;
    if (b->count < {struct_name.upper()}_WINDOW_SIZE) b->count++;

    if (b->count > 1) {{
        double mean = 0.0;
        for (int i = 0; i < b->count; i++) {{
            mean += b->buffer[i];
        }}
        mean /= b->count;

        double var = 0.0;
        for (int i = 0; i < b->count; i++) {{
            double diff = b->buffer[i] - mean;
            var += diff * diff;
        }}
        b->output = var / (b->count - 1);
    }} else {{
        b->output = 0.0;
    }}
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_rms(block: BlockInfo, struct_name: str) -> str:
    """Generate C RMS block code."""
    window_size = block.parameters.get("windowSize", block.parameters.get("window_size", 10))

    return f"""
// {block.name} - Running RMS
#include <math.h>
#define {struct_name.upper()}_WINDOW_SIZE {window_size}

typedef struct {{
    double buffer[{struct_name.upper()}_WINDOW_SIZE];
    int count;
    int index;
    double sum_sq;
    double input;
    double output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    for (int i = 0; i < {struct_name.upper()}_WINDOW_SIZE; i++) {{
        b->buffer[i] = 0.0;
    }}
    b->count = 0;
    b->index = 0;
    b->sum_sq = 0.0;
    b->input = 0.0;
    b->output = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    // Subtract old squared value and add new squared value
    b->sum_sq -= b->buffer[b->index] * b->buffer[b->index];
    b->buffer[b->index] = b->input;
    b->sum_sq += b->input * b->input;

    b->index = (b->index + 1) % {struct_name.upper()}_WINDOW_SIZE;
    if (b->count < {struct_name.upper()}_WINDOW_SIZE) b->count++;

    // Compute RMS
    if (b->count > 0) {{
        b->output = sqrt(b->sum_sq / b->count);
    }} else {{
        b->output = 0.0;
    }}
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_downsampler(block: BlockInfo, struct_name: str) -> str:
    """Generate C Downsampler block code."""
    factor = block.parameters.get("factor", 2)

    return f"""
// {block.name} - Downsampler
typedef struct {{
    int factor;
    int sample_count;
    double input;
    double output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->factor = {factor};
    b->sample_count = 0;
    b->input = 0.0;
    b->output = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    if (b->sample_count % b->factor == 0) {{
        b->output = b->input;
    }}
    b->sample_count++;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_upsampler(block: BlockInfo, struct_name: str) -> str:
    """Generate C Upsampler block code."""
    factor = block.parameters.get("factor", 2)

    return f"""
// {block.name} - Upsampler
typedef struct {{
    int factor;
    int phase;
    double current_sample;
    double input;
    double output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->factor = {factor};
    b->phase = 0;
    b->current_sample = 0.0;
    b->input = 0.0;
    b->output = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    if (b->phase == 0) {{
        b->current_sample = b->input;
        b->output = b->current_sample;
    }} else {{
        b->output = 0.0;
    }}
    b->phase = (b->phase + 1) % b->factor;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_peak_detector(block: BlockInfo, struct_name: str) -> str:
    """Generate C Peak Detector block code."""
    threshold = block.parameters.get("threshold", 0.0)

    return f"""
// {block.name} - Peak Detector
typedef struct {{
    double threshold;
    double prev_prev;
    double prev;
    double current;
    double input;
    double output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->threshold = {threshold};
    b->prev_prev = 0.0;
    b->prev = 0.0;
    b->current = 0.0;
    b->input = 0.0;
    b->output = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    b->prev_prev = b->prev;
    b->prev = b->current;
    b->current = b->input;

    if (b->prev > b->prev_prev && b->prev > b->current && b->prev > b->threshold) {{
        b->output = 1.0;
    }} else {{
        b->output = 0.0;
    }}
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_zero_crossing_detector(block: BlockInfo, struct_name: str) -> str:
    """Generate C Zero Crossing Detector block code."""
    direction = block.parameters.get("direction", "both")

    # Encode direction as int for C
    direction_code = 0  # both
    if direction == "rising":
        direction_code = 1
    elif direction == "falling":
        direction_code = 2

    return f"""
// {block.name} - Zero Crossing Detector
typedef struct {{
    int direction;  // 0=both, 1=rising, 2=falling
    double prev;
    double current;
    double input;
    double output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->direction = {direction_code};
    b->prev = 0.0;
    b->current = 0.0;
    b->input = 0.0;
    b->output = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    b->prev = b->current;
    b->current = b->input;

    int is_crossing = 0;
    if (b->direction == 1) {{
        is_crossing = (b->prev <= 0.0 && b->current > 0.0);
    }} else if (b->direction == 2) {{
        is_crossing = (b->prev >= 0.0 && b->current < 0.0);
    }} else {{
        is_crossing = (b->prev <= 0.0 && b->current > 0.0) || (b->prev >= 0.0 && b->current < 0.0);
    }}

    b->output = is_crossing ? 1.0 : 0.0;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


DSP_TEMPLATES = {
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
