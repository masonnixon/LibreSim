"""C block templates for source blocks."""

from ....models import BlockInfo
from ....random_compat import python_mt19937_state


def _format_python_mt19937_state(seed: object) -> tuple[str, int]:
    """Format CPython's initialized MT19937 state for a C array literal."""
    words, index = python_mt19937_state(seed)
    rows = [
        ", ".join(f"{word}UL" for word in words[start : start + 8])
        for start in range(0, len(words), 8)
    ]
    return ",\n    ".join(rows), index


def _format_c_comment_value(value: object) -> str:
    """Format a Python value for inclusion in a generated C comment."""
    return repr(value).replace("*/", "* /").replace("\r", "\\r").replace("\n", "\\n")


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

static inline double* {struct_name}_get_output_vector({struct_name}* b) {{
    return b->output;
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
    """Generate C code for White Noise block.

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

    # Use a deterministic seed if none provided
    seed_value = seed if seed is not None else 12345
    mt_state, mt_index = _format_python_mt19937_state(seed_value)
    seed_comment = _format_c_comment_value(seed_value)

    return f"""
// {block.name} - White Noise source (matches OSK WhiteNoise exactly)
// Uses Mersenne Twister PRNG for Python compatibility

#define {struct_name.upper()}_MT_N 624
#define {struct_name.upper()}_MT_M 397

typedef struct {{
    double mean;
    double variance;
    double std_dev;
    double sample_time;
    double output;
    double _last_sample_time;
    // Mersenne Twister state
    unsigned long mt[{struct_name.upper()}_MT_N];
    int mti;
    // Gauss state for Box-Muller
    int have_spare;
    double spare;
}} {struct_name};

// CPython expands seeds with init_by_array; copy its initialized state so
// independent block instances retain independent PRNG streams.
// Configured seed: {seed_comment}
static const unsigned long {struct_name}_mt_initial_state[{struct_name.upper()}_MT_N] = {{
    {mt_state}
}};

// Mersenne Twister generate (matches Python's random.Random)
static unsigned long {struct_name}_mt_genrand({struct_name}* b) {{
    unsigned long y;
    static unsigned long mag01[2] = {{0x0UL, 0x9908b0dfUL}};

    if (b->mti >= {struct_name.upper()}_MT_N) {{
        int kk;
        for (kk = 0; kk < {struct_name.upper()}_MT_N - {struct_name.upper()}_MT_M; kk++) {{
            y = (b->mt[kk] & 0x80000000UL) | (b->mt[kk+1] & 0x7fffffffUL);
            b->mt[kk] = b->mt[kk + {struct_name.upper()}_MT_M] ^ (y >> 1) ^ mag01[y & 0x1UL];
        }}
        for (; kk < {struct_name.upper()}_MT_N - 1; kk++) {{
            y = (b->mt[kk] & 0x80000000UL) | (b->mt[kk+1] & 0x7fffffffUL);
            b->mt[kk] = b->mt[kk + ({struct_name.upper()}_MT_M - {struct_name.upper()}_MT_N)] ^ (y >> 1) ^ mag01[y & 0x1UL];
        }}
        y = (b->mt[{struct_name.upper()}_MT_N-1] & 0x80000000UL) | (b->mt[0] & 0x7fffffffUL);
        b->mt[{struct_name.upper()}_MT_N-1] = b->mt[{struct_name.upper()}_MT_M-1] ^ (y >> 1) ^ mag01[y & 0x1UL];
        b->mti = 0;
    }}

    y = b->mt[b->mti++];
    y ^= (y >> 11);
    y ^= (y << 7) & 0x9d2c5680UL;
    y ^= (y << 15) & 0xefc60000UL;
    y ^= (y >> 18);

    return y;
}}

// Generate uniform [0, 1) matching Python's random.random()
static double {struct_name}_random({struct_name}* b) {{
    unsigned long a = {struct_name}_mt_genrand(b) >> 5;
    unsigned long bb = {struct_name}_mt_genrand(b) >> 6;
    return (a * 67108864.0 + bb) * (1.0 / 9007199254740992.0);
}}

// Polar Box-Muller with trig (matches Python's random.gauss() exactly)
// Python uses: cos(2*pi*x) * sqrt(-2*log(1-y)) where x,y are uniform [0,1)
static double {struct_name}_gauss({struct_name}* b, double mu, double sigma) {{
    if (b->have_spare) {{
        b->have_spare = 0;
        return mu + sigma * b->spare;
    }}

    double x2pi = {struct_name}_random(b) * 6.283185307179586;  // 2*pi
    double g2rad = sqrt(-2.0 * log(1.0 - {struct_name}_random(b)));
    double z = cos(x2pi) * g2rad;
    b->spare = sin(x2pi) * g2rad;
    b->have_spare = 1;
    return mu + sigma * z;
}}

void {struct_name}_init({struct_name}* b) {{
    b->mean = {mean};
    b->variance = {variance};
    b->std_dev = sqrt(fabs(b->variance));
    b->sample_time = {sample_time};
    b->_last_sample_time = -1e308;
    b->have_spare = 0;
    b->spare = 0.0;
    for (int i = 0; i < {struct_name.upper()}_MT_N; i++) {{
        b->mt[i] = {struct_name}_mt_initial_state[i];
    }}
    b->mti = {mt_index};
    // Generate initial noise sample (matches OSK init)
    b->output = {struct_name}_gauss(b, b->mean, b->std_dev);
    b->_last_sample_time = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    // If sample_time is 0, generate new noise every step
    // Otherwise, only generate new noise at sample intervals
    if (b->sample_time <= 0) {{
        b->output = {struct_name}_gauss(b, b->mean, b->std_dev);
    }} else {{
        if (t >= b->_last_sample_time + b->sample_time) {{
            b->output = {struct_name}_gauss(b, b->mean, b->std_dev);
            b->_last_sample_time = t;
        }}
    }}
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_band_limited_white_noise(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Band-Limited White Noise block.

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
    mt_state, mt_index = _format_python_mt19937_state(seed_value)
    seed_comment = _format_c_comment_value(seed_value)

    return f"""
// {block.name} - Band-Limited White Noise source (matches OSK BandLimitedWhiteNoise exactly)

#define {struct_name.upper()}_MT_N 624
#define {struct_name.upper()}_MT_M 397

typedef struct {{
    double noise_power;
    double sample_time;
    double output;
    double _last_sample_time;
    double _std_dev;
    // Mersenne Twister state
    unsigned long mt[{struct_name.upper()}_MT_N];
    int mti;
    // Gauss state
    int have_spare;
    double spare;
}} {struct_name};

// CPython expands seeds with init_by_array; copy its initialized state so
// independent block instances retain independent PRNG streams.
// Configured seed: {seed_comment}
static const unsigned long {struct_name}_mt_initial_state[{struct_name.upper()}_MT_N] = {{
    {mt_state}
}};

static unsigned long {struct_name}_mt_genrand({struct_name}* b) {{
    unsigned long y;
    static unsigned long mag01[2] = {{0x0UL, 0x9908b0dfUL}};

    if (b->mti >= {struct_name.upper()}_MT_N) {{
        int kk;
        for (kk = 0; kk < {struct_name.upper()}_MT_N - {struct_name.upper()}_MT_M; kk++) {{
            y = (b->mt[kk] & 0x80000000UL) | (b->mt[kk+1] & 0x7fffffffUL);
            b->mt[kk] = b->mt[kk + {struct_name.upper()}_MT_M] ^ (y >> 1) ^ mag01[y & 0x1UL];
        }}
        for (; kk < {struct_name.upper()}_MT_N - 1; kk++) {{
            y = (b->mt[kk] & 0x80000000UL) | (b->mt[kk+1] & 0x7fffffffUL);
            b->mt[kk] = b->mt[kk + ({struct_name.upper()}_MT_M - {struct_name.upper()}_MT_N)] ^ (y >> 1) ^ mag01[y & 0x1UL];
        }}
        y = (b->mt[{struct_name.upper()}_MT_N-1] & 0x80000000UL) | (b->mt[0] & 0x7fffffffUL);
        b->mt[{struct_name.upper()}_MT_N-1] = b->mt[{struct_name.upper()}_MT_M-1] ^ (y >> 1) ^ mag01[y & 0x1UL];
        b->mti = 0;
    }}

    y = b->mt[b->mti++];
    y ^= (y >> 11);
    y ^= (y << 7) & 0x9d2c5680UL;
    y ^= (y << 15) & 0xefc60000UL;
    y ^= (y >> 18);

    return y;
}}

static double {struct_name}_random({struct_name}* b) {{
    unsigned long a = {struct_name}_mt_genrand(b) >> 5;
    unsigned long bb = {struct_name}_mt_genrand(b) >> 6;
    return (a * 67108864.0 + bb) * (1.0 / 9007199254740992.0);
}}

static double {struct_name}_gauss({struct_name}* b, double mu, double sigma) {{
    if (b->have_spare) {{
        b->have_spare = 0;
        return mu + sigma * b->spare;
    }}

    double x2pi = {struct_name}_random(b) * 6.283185307179586;
    double g2rad = sqrt(-2.0 * log(1.0 - {struct_name}_random(b)));
    double z = cos(x2pi) * g2rad;
    b->spare = sin(x2pi) * g2rad;
    b->have_spare = 1;
    return mu + sigma * z;
}}

void {struct_name}_init({struct_name}* b) {{
    b->noise_power = {noise_power};
    b->sample_time = {sample_time};
    if (b->sample_time < 1e-6) b->sample_time = 1e-6;
    b->_std_dev = sqrt(b->noise_power / b->sample_time);
    b->_last_sample_time = -1e308;
    b->have_spare = 0;
    b->spare = 0.0;
    for (int i = 0; i < {struct_name.upper()}_MT_N; i++) {{
        b->mt[i] = {struct_name}_mt_initial_state[i];
    }}
    b->mti = {mt_index};
    b->output = {struct_name}_gauss(b, 0.0, b->_std_dev);
    b->_last_sample_time = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    if (t >= b->_last_sample_time + b->sample_time - 1e-10) {{
        b->output = {struct_name}_gauss(b, 0.0, b->_std_dev);
        b->_last_sample_time = t;
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
    "band_limited_white_noise": template_band_limited_white_noise,
}
