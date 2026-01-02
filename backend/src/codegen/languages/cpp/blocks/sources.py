"""C++ block templates for source blocks."""

from ....models import BlockInfo


def template_constant(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Constant block."""
    value = block.parameters.get("value", 1.0)
    return f"""
// {block.name} - Constant source
class {class_name} {{
public:
    double value = {value};

    void init() {{
        output_ = value;
    }}

    void update(double t) {{
        (void)t;
        output_ = value;
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output_;
    }}

private:
    double output_ = 0.0;
}};
"""


def template_step(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Step block."""
    step_time = block.parameters.get("step_time", 1.0)
    initial_value = block.parameters.get("initial_value", 0.0)
    final_value = block.parameters.get("final_value", 1.0)
    return f"""
// {block.name} - Step source
class {class_name} {{
public:
    double step_time = {step_time};
    double initial_value = {initial_value};
    double final_value = {final_value};

    void init() {{
        output_ = initial_value;
    }}

    void update(double t) {{
        output_ = (t >= step_time) ? final_value : initial_value;
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output_;
    }}

private:
    double output_ = 0.0;
}};
"""


def template_ramp(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Ramp block."""
    slope = block.parameters.get("slope", 1.0)
    start_time = block.parameters.get("start_time", 0.0)
    initial_output = block.parameters.get("initial_output", 0.0)
    return f"""
// {block.name} - Ramp source
class {class_name} {{
public:
    double slope = {slope};
    double start_time = {start_time};
    double initial_output = {initial_output};

    void init() {{
        output_ = initial_output;
    }}

    void update(double t) {{
        if (t >= start_time) {{
            output_ = initial_output + slope * (t - start_time);
        }} else {{
            output_ = initial_output;
        }}
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output_;
    }}

private:
    double output_ = 0.0;
}};
"""


def template_sine_wave(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Sine Wave block."""
    amplitude = block.parameters.get("amplitude", 1.0)
    frequency = block.parameters.get("frequency", 1.0)
    phase = block.parameters.get("phase", 0.0)
    bias = block.parameters.get("bias", 0.0)
    return f"""
// {block.name} - Sine wave source
class {class_name} {{
public:
    double amplitude = {amplitude};
    double frequency = {frequency};
    double phase = {phase};
    double bias = {bias};

    void init() {{
        output_ = bias + amplitude * std::sin(phase);
    }}

    void update(double t) {{
        output_ = bias + amplitude * std::sin(2.0 * M_PI * frequency * t + phase);
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output_;
    }}

private:
    double output_ = 0.0;
}};
"""


def template_pulse(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Pulse Generator block."""
    amplitude = block.parameters.get("amplitude", 1.0)
    period = block.parameters.get("period", 1.0)
    pulse_width = block.parameters.get("pulse_width", 50.0)
    phase_delay = block.parameters.get("phase_delay", 0.0)
    return f"""
// {block.name} - Pulse generator
class {class_name} {{
public:
    double amplitude = {amplitude};
    double period = {period};
    double duty_cycle = {pulse_width} / 100.0;
    double phase_delay = {phase_delay};

    void init() {{
        output_ = 0.0;
    }}

    void update(double t) {{
        double t_adj = t - phase_delay;
        if (t_adj < 0) {{
            output_ = 0.0;
        }} else {{
            double phase = std::fmod(t_adj, period) / period;
            output_ = (phase < duty_cycle) ? amplitude : 0.0;
        }}
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output_;
    }}

private:
    double output_ = 0.0;
}};
"""


def template_clock(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Clock block."""
    return f"""
// {block.name} - Clock (outputs simulation time)
class {class_name} {{
public:
    void init() {{
        output_ = 0.0;
    }}

    void update(double t) {{
        output_ = t;
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output_;
    }}

private:
    double output_ = 0.0;
}};
"""


def template_ground(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Ground block."""
    return f"""
// {block.name} - Ground (zero output)
class {class_name} {{
public:
    void init() {{
        output_ = 0.0;
    }}

    void update(double t) {{
        (void)t;
        output_ = 0.0;
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output_;
    }}

private:
    double output_ = 0.0;
}};
"""


def template_white_noise(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for White Noise block."""
    power = block.parameters.get("power", 1.0)
    sample_time = block.parameters.get("sampleTime", 0.1)
    seed = block.parameters.get("seed", 0)

    return f"""
// {block.name} - White Noise source
class {class_name} {{
public:
    {class_name}() : gen_({seed if seed else 'std::random_device{{}}()'}),
                     dist_(0.0, std::sqrt({power} / {sample_time})) {{}}

    void init() {{
        output_ = 0.0;
        last_sample_time_ = -std::numeric_limits<double>::infinity();
    }}

    void update(double t) {{
        if (t - last_sample_time_ >= {sample_time} - 1e-10) {{
            output_ = dist_(gen_);
            last_sample_time_ = t;
        }}
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output_;
    }}

private:
    std::mt19937 gen_;
    std::normal_distribution<double> dist_;
    double output_ = 0.0;
    double last_sample_time_ = -std::numeric_limits<double>::infinity();
}};
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
