"""C++ templates for nonlinear blocks."""

from ....models import BlockInfo


def template_lookup_table_1d(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for LookupTable1D block."""
    x_data = block.parameters.get("xData", [0.0, 1.0])
    y_data = block.parameters.get("yData", [0.0, 1.0])
    n = len(x_data)

    x_str = ", ".join(str(v) for v in x_data)
    y_str = ", ".join(str(v) for v in y_data)

    return f"""
// {block.name} - 1D Lookup Table
class {class_name} {{
public:
    static constexpr int TABLE_SIZE = {n};
    double input = 0.0;
    double output = 0.0;
    std::array<double, TABLE_SIZE> x_data = {{{{{x_str}}}}};
    std::array<double, TABLE_SIZE> y_data = {{{{{y_str}}}}};

    void init() {{
        output = 0.0;
    }}

    void update(double t) {{
        (void)t;
        double x = input;

        if (TABLE_SIZE < 2) {{
            output = y_data[0];
            return;
        }}

        if (x <= x_data[0]) {{
            output = y_data[0];
        }} else if (x >= x_data[TABLE_SIZE - 1]) {{
            output = y_data[TABLE_SIZE - 1];
        }} else {{
            for (int i = 0; i < TABLE_SIZE - 1; i++) {{
                if (x_data[i] <= x && x <= x_data[i + 1]) {{
                    double t_interp = (x - x_data[i]) / (x_data[i + 1] - x_data[i]);
                    output = y_data[i] + t_interp * (y_data[i + 1] - y_data[i]);
                    break;
                }}
            }}
        }}
    }}

    double get_output(int port) const {{
        (void)port;
        return output;
    }}
}};
"""


def template_quantizer(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Quantizer block."""
    interval = block.parameters.get("interval", 1.0)

    return f"""
// {block.name} - Quantizer
class {class_name} {{
public:
    double input = 0.0;
    double output = 0.0;
    double interval = {interval};

    void init() {{
        output = 0.0;
    }}

    void update(double t) {{
        (void)t;
        output = std::round(input / interval) * interval;
    }}

    double get_output(int port) const {{
        (void)port;
        return output;
    }}
}};
"""


def template_relay(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Relay (hysteresis) block."""
    on_point = block.parameters.get("onPoint", 0.5)
    off_point = block.parameters.get("offPoint", -0.5)
    on_output = block.parameters.get("onOutput", 1.0)
    off_output = block.parameters.get("offOutput", -1.0)

    return f"""
// {block.name} - Relay (hysteresis)
class {class_name} {{
public:
    double input = 0.0;
    double output = {off_output};
    double on_point = {on_point};
    double off_point = {off_point};
    double on_output = {on_output};
    double off_output = {off_output};
    bool state = false;

    void init() {{
        output = off_output;
        state = false;
    }}

    void update(double t) {{
        (void)t;
        if (state) {{
            if (input <= off_point) {{
                state = false;
                output = off_output;
            }} else {{
                output = on_output;
            }}
        }} else {{
            if (input >= on_point) {{
                state = true;
                output = on_output;
            }} else {{
                output = off_output;
            }}
        }}
    }}

    double get_output(int port) const {{
        (void)port;
        return output;
    }}
}};
"""


def template_coulomb(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Coulomb friction block."""
    offset = block.parameters.get("offset", 0.0)
    gain = block.parameters.get("gain", 1.0)

    return f"""
// {block.name} - Coulomb Friction
class {class_name} {{
public:
    double input = 0.0;
    double output = 0.0;
    double offset = {offset};
    double gain = {gain};

    void init() {{
        output = 0.0;
    }}

    void update(double t) {{
        (void)t;
        if (input > 0) {{
            output = gain;
        }} else if (input < 0) {{
            output = -gain;
        }} else {{
            output = 0.0;
        }}
        output += offset;
    }}

    double get_output(int port) const {{
        (void)port;
        return output;
    }}
}};
"""


def template_wrap_to_range(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for WrapToRange block."""
    lower = block.parameters.get("lower", -3.14159265)
    upper = block.parameters.get("upper", 3.14159265)

    return f"""
// {block.name} - Wrap to Range
class {class_name} {{
public:
    double input = 0.0;
    double output = 0.0;
    double lower = {lower};
    double upper = {upper};

    void init() {{
        output = 0.0;
    }}

    void update(double t) {{
        (void)t;
        double range = upper - lower;
        if (range <= 0) {{
            output = input;
            return;
        }}

        double val = std::fmod(input - lower, range);
        if (val < 0) val += range;
        output = val + lower;
    }}

    double get_output(int port) const {{
        (void)port;
        return output;
    }}
}};
"""


def template_hit_crossing(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for HitCrossing block."""
    offset = block.parameters.get("offset", 0.0)
    direction = block.parameters.get("direction", "rising")

    dir_code = {
        "rising": "crossed = (prev_val < 0 && curr_val >= 0);",
        "falling": "crossed = (prev_val > 0 && curr_val <= 0);",
        "either": "crossed = (prev_val < 0 && curr_val >= 0) || (prev_val > 0 && curr_val <= 0);",
    }.get(direction, "crossed = false;")

    return f"""
// {block.name} - Hit/Zero Crossing Detector
class {class_name} {{
public:
    double input = 0.0;
    double output = 0.0;
    double offset = {offset};
    double prev_input = 0.0;
    bool first_step = true;

    void init() {{
        output = 0.0;
        prev_input = 0.0;
        first_step = true;
    }}

    void update(double t) {{
        (void)t;
        if (first_step) {{
            first_step = false;
            prev_input = input;
            output = 0.0;
            return;
        }}

        double prev_val = prev_input - offset;
        double curr_val = input - offset;
        bool crossed = false;

        {dir_code}

        output = crossed ? 1.0 : 0.0;
        prev_input = input;
    }}

    double get_output(int port) const {{
        (void)port;
        return output;
    }}
}};
"""


def template_stiction(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Stiction block."""
    static_friction = block.parameters.get("staticFriction", 1.0)
    kinetic_friction = block.parameters.get("kineticFriction", 0.8)

    return f"""
// {block.name} - Stiction
class {class_name} {{
public:
    double input = 0.0;
    double output = 0.0;
    double static_friction = {static_friction};
    double kinetic_friction = {kinetic_friction};
    bool is_moving = false;

    void init() {{
        output = 0.0;
        is_moving = false;
    }}

    void update(double t) {{
        (void)t;
        if (!is_moving) {{
            if (std::abs(input) > static_friction) {{
                is_moving = true;
                output = input > 0 ? input - kinetic_friction : input + kinetic_friction;
            }} else {{
                output = 0.0;
            }}
        }} else {{
            if (input > kinetic_friction) {{
                output = input - kinetic_friction;
            }} else if (input < -kinetic_friction) {{
                output = input + kinetic_friction;
            }} else {{
                is_moving = false;
                output = 0.0;
            }}
        }}
    }}

    double get_output(int port) const {{
        (void)port;
        return output;
    }}
}};
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
