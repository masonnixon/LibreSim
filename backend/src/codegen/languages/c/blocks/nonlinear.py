"""C templates for nonlinear blocks."""

from ....models import BlockInfo


def template_lookup_table_1d(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for LookupTable1D block."""
    x_data = block.parameters.get("xData", [0.0, 1.0])
    y_data = block.parameters.get("yData", [0.0, 1.0])
    n = len(x_data)

    x_str = ", ".join(str(v) for v in x_data)
    y_str = ", ".join(str(v) for v in y_data)

    return f"""
// {block.name} - 1D Lookup Table
#define {struct_name.upper()}_TABLE_SIZE {n}

typedef struct {{
    double input;
    double output;
    double x_data[{n}];
    double y_data[{n}];
    int size;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    double x[] = {{{x_str}}};
    double y[] = {{{y_str}}};
    b->input = 0.0;
    b->output = 0.0;
    b->size = {n};
    for (int i = 0; i < {n}; i++) {{
        b->x_data[i] = x[i];
        b->y_data[i] = y[i];
    }}
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    double x = b->input;

    if (b->size < 2) {{
        b->output = b->y_data[0];
        return;
    }}

    // Clamp and interpolate
    if (x <= b->x_data[0]) {{
        b->output = b->y_data[0];
    }} else if (x >= b->x_data[b->size - 1]) {{
        b->output = b->y_data[b->size - 1];
    }} else {{
        for (int i = 0; i < b->size - 1; i++) {{
            if (b->x_data[i] <= x && x <= b->x_data[i + 1]) {{
                double t_interp = (x - b->x_data[i]) / (b->x_data[i + 1] - b->x_data[i]);
                b->output = b->y_data[i] + t_interp * (b->y_data[i + 1] - b->y_data[i]);
                break;
            }}
        }}
    }}
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_quantizer(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Quantizer block."""
    interval = block.parameters.get("interval", 1.0)

    return f"""
// {block.name} - Quantizer
typedef struct {{
    double input;
    double output;
    double interval;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
    b->interval = {interval};
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    b->output = round(b->input / b->interval) * b->interval;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_relay(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Relay (hysteresis) block."""
    # Support both camelCase (JSON) and snake_case parameter names
    on_point = block.parameters.get("switchOn", block.parameters.get("onPoint", 0.5))
    off_point = block.parameters.get("switchOff", block.parameters.get("offPoint", -0.5))
    on_output = block.parameters.get("outputOn", block.parameters.get("onOutput", 1.0))
    off_output = block.parameters.get("outputOff", block.parameters.get("offOutput", -1.0))

    return f"""
// {block.name} - Relay (hysteresis)
typedef struct {{
    double input;
    double output;
    double on_point;
    double off_point;
    double on_output;
    double off_output;
    int state;  // 0=off, 1=on
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = {off_output};
    b->on_point = {on_point};
    b->off_point = {off_point};
    b->on_output = {on_output};
    b->off_output = {off_output};
    b->state = 0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    if (b->state) {{
        if (b->input <= b->off_point) {{
            b->state = 0;
            b->output = b->off_output;
        }} else {{
            b->output = b->on_output;
        }}
    }} else {{
        if (b->input >= b->on_point) {{
            b->state = 1;
            b->output = b->on_output;
        }} else {{
            b->output = b->off_output;
        }}
    }}
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_coulomb(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Coulomb friction block."""
    offset = block.parameters.get("offset", 0.0)
    gain = block.parameters.get("gain", 1.0)

    return f"""
// {block.name} - Coulomb Friction
typedef struct {{
    double input;
    double output;
    double offset;
    double gain;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
    b->offset = {offset};
    b->gain = {gain};
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    if (b->input > 0) {{
        b->output = b->gain;
    }} else if (b->input < 0) {{
        b->output = -b->gain;
    }} else {{
        b->output = 0.0;
    }}
    b->output += b->offset;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_wrap_to_range(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for WrapToRange block."""
    lower = block.parameters.get("lower", -3.14159265)
    upper = block.parameters.get("upper", 3.14159265)

    return f"""
// {block.name} - Wrap to Range
typedef struct {{
    double input;
    double output;
    double lower;
    double upper;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
    b->lower = {lower};
    b->upper = {upper};
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    double range = b->upper - b->lower;
    if (range <= 0) {{
        b->output = b->input;
        return;
    }}

    double val = fmod(b->input - b->lower, range);
    if (val < 0) val += range;
    b->output = val + b->lower;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_hit_crossing(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for HitCrossing block."""
    offset = block.parameters.get("offset", 0.0)
    direction = block.parameters.get("direction", "rising")

    dir_code = {
        "rising": "crossed = (prev_val < 0 && curr_val >= 0);",
        "falling": "crossed = (prev_val > 0 && curr_val <= 0);",
        "either": "crossed = (prev_val < 0 && curr_val >= 0) || (prev_val > 0 && curr_val <= 0);",
    }.get(direction, "crossed = 0;")

    return f"""
// {block.name} - Hit/Zero Crossing Detector
typedef struct {{
    double input;
    double output;
    double offset;
    double prev_input;
    int first_step;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
    b->offset = {offset};
    b->prev_input = 0.0;
    b->first_step = 1;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    if (b->first_step) {{
        b->first_step = 0;
        b->prev_input = b->input;
        b->output = 0.0;
        return;
    }}

    double prev_val = b->prev_input - b->offset;
    double curr_val = b->input - b->offset;
    int crossed = 0;

    {dir_code}

    b->output = crossed ? 1.0 : 0.0;
    b->prev_input = b->input;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_stiction(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Stiction block."""
    static_friction = block.parameters.get("staticFriction", 1.0)
    kinetic_friction = block.parameters.get("kineticFriction", 0.8)

    return f"""
// {block.name} - Stiction
typedef struct {{
    double input;
    double output;
    double static_friction;
    double kinetic_friction;
    int is_moving;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
    b->static_friction = {static_friction};
    b->kinetic_friction = {kinetic_friction};
    b->is_moving = 0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    if (!b->is_moving) {{
        if (fabs(b->input) > b->static_friction) {{
            b->is_moving = 1;
            if (b->input > 0) {{
                b->output = b->input - b->kinetic_friction;
            }} else {{
                b->output = b->input + b->kinetic_friction;
            }}
        }} else {{
            b->output = 0.0;
        }}
    }} else {{
        if (b->input > b->kinetic_friction) {{
            b->output = b->input - b->kinetic_friction;
        }} else if (b->input < -b->kinetic_friction) {{
            b->output = b->input + b->kinetic_friction;
        }} else {{
            b->is_moving = 0;
            b->output = 0.0;
        }}
    }}
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
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
