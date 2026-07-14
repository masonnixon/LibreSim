"""C++ templates for signal processing blocks."""

import math

from ....filter_design import design_analog_filter
from ....models import BlockInfo


def template_rate_limiter(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for RateLimiter block."""
    rising_slew = abs(
        block.parameters.get("risingLimit", block.parameters.get("risingSlewRate", 1.0))
    )
    falling_limit = block.parameters.get(
        "fallingLimit", block.parameters.get("fallingSlewRate", -1.0)
    )
    falling_slew = -abs(falling_limit) if falling_limit < 0 else -rising_slew

    return f"""
// {block.name} - Rate Limiter
class {class_name} {{
public:
    double input = 0.0;
    double output = 0.0;
    double rising_slew = {rising_slew};
    double falling_slew = {falling_slew};
    double prev_output = 0.0;

    void init() {{
        output = 0.0;
        prev_output = 0.0;
    }}

    void update(double t, double dt) {{
        (void)t;
        double delta = input - prev_output;
        double max_rise = rising_slew * dt;
        double max_fall = falling_slew * dt;

        if (delta > max_rise) {{
            output = prev_output + max_rise;
        }} else if (delta < max_fall) {{
            output = prev_output + max_fall;
        }} else {{
            output = input;
        }}
        prev_output = output;
    }}

    double get_output(int port) const {{
        (void)port;
        return output;
    }}
}};
"""


def template_moving_average(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for MovingAverage block."""
    window_size = block.parameters.get("windowSize", 10)

    return f"""
// {block.name} - Moving Average Filter
class {class_name} {{
public:
    static constexpr int WINDOW_SIZE = {window_size};
    double input = 0.0;
    double output = 0.0;
    std::array<double, WINDOW_SIZE> buffer{{}};
    int index = 0;
    int count = 0;
    double sum = 0.0;

    void init() {{
        output = 0.0;
        buffer.fill(0.0);
        index = 0;
        count = 0;
        sum = 0.0;
    }}

    void update(double t) {{
        (void)t;
        // Remove old value from sum
        sum -= buffer[index];
        // Add new value
        buffer[index] = input;
        sum += input;
        // Update index
        index = (index + 1) % WINDOW_SIZE;
        if (count < WINDOW_SIZE) {{
            count++;
        }}
        // Compute average
        output = (count > 0) ? sum / count : 0.0;
    }}

    double get_output(int port) const {{
        (void)port;
        return output;
    }}
}};
"""


def template_low_pass_filter(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for first-order LowPassFilter block."""
    cutoff_freq = block.parameters.get("cutoffFrequency", 10.0)
    sample_time = block.step_size

    tau = 1.0 / (2.0 * math.pi * cutoff_freq)
    alpha = sample_time / (tau + sample_time)

    return f"""
// {block.name} - First-Order Low-Pass Filter
class {class_name} {{
public:
    double input = 0.0;
    double output = 0.0;
    double alpha = {alpha};

    void init() {{
        output = 0.0;
    }}

    void update(double t) {{
        (void)t;
        output = alpha * input + (1.0 - alpha) * output;
    }}

    double get_output(int port) const {{
        (void)port;
        return output;
    }}
}};
"""


def template_analog_filter(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for an OSK-compatible cascaded analog filter."""
    sections = design_analog_filter(block.parameters, block.step_size)
    initializers = ",\n            ".join(
        "Biquad{"
        + ", ".join(
            repr(value)
            for value in (
                section.b0,
                section.b1,
                section.b2,
                section.a1,
                section.a2,
                0.0,
                0.0,
                0.0,
                0.0,
            )
        )
        + "}"
        for section in sections
    )

    return f"""
// {block.name} - Cascaded Analog Filter
class {class_name} {{
public:
    struct Biquad {{
        double b0, b1, b2, a1, a2;
        double x1, x2, y1, y2;
    }};

    double input = 0.0;
    double output = 0.0;
    std::array<Biquad, {len(sections)}> sections{{{{
            {initializers}
    }}}};

    void init() {{
        output = 0.0;
        for (auto& section : sections) {{
            section.x1 = section.x2 = section.y1 = section.y2 = 0.0;
        }}
    }}

    void update(double t) {{
        (void)t;
        double value = input;
        for (auto& section : sections) {{
            double next = section.b0 * value + section.b1 * section.x1
                        + section.b2 * section.x2 - section.a1 * section.y1
                        - section.a2 * section.y2;
            section.x2 = section.x1;
            section.x1 = value;
            section.y2 = section.y1;
            section.y1 = next;
            value = next;
        }}
        output = value;
    }}

    double get_output(int port) const {{
        (void)port;
        return output;
    }}
}};
"""


def template_high_pass_filter(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for first-order HighPassFilter block."""
    cutoff_freq = block.parameters.get("cutoffFrequency", 10.0)
    sample_time = block.parameters.get("sampleTime", 0.01)

    tau = 1.0 / (2.0 * math.pi * cutoff_freq)
    alpha = tau / (tau + sample_time)

    return f"""
// {block.name} - First-Order High-Pass Filter
class {class_name} {{
public:
    double input = 0.0;
    double output = 0.0;
    double alpha = {alpha};
    double prev_input = 0.0;
    double prev_output = 0.0;

    void init() {{
        output = 0.0;
        prev_input = 0.0;
        prev_output = 0.0;
    }}

    void update(double t) {{
        (void)t;
        output = alpha * (prev_output + input - prev_input);
        prev_input = input;
        prev_output = output;
    }}

    double get_output(int port) const {{
        (void)port;
        return output;
    }}
}};
"""


def template_band_pass_filter(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for BandPassFilter block."""
    low_cutoff = block.parameters.get("lowCutoffFrequency", 5.0)
    high_cutoff = block.parameters.get("highCutoffFrequency", 50.0)
    sample_time = block.parameters.get("sampleTime", 0.01)

    tau_hp = 1.0 / (2.0 * math.pi * low_cutoff)
    alpha_hp = tau_hp / (tau_hp + sample_time)
    tau_lp = 1.0 / (2.0 * math.pi * high_cutoff)
    alpha_lp = sample_time / (tau_lp + sample_time)

    return f"""
// {block.name} - Band-Pass Filter (cascaded HP + LP)
class {class_name} {{
public:
    double input = 0.0;
    double output = 0.0;
    double alpha_hp = {alpha_hp};
    double alpha_lp = {alpha_lp};
    double hp_prev_input = 0.0;
    double hp_prev_output = 0.0;
    double lp_output = 0.0;

    void init() {{
        output = 0.0;
        hp_prev_input = 0.0;
        hp_prev_output = 0.0;
        lp_output = 0.0;
    }}

    void update(double t) {{
        (void)t;
        // High-pass stage
        double hp_out = alpha_hp * (hp_prev_output + input - hp_prev_input);
        hp_prev_input = input;
        hp_prev_output = hp_out;

        // Low-pass stage
        lp_output = alpha_lp * hp_out + (1.0 - alpha_lp) * lp_output;
        output = lp_output;
    }}

    double get_output(int port) const {{
        (void)port;
        return output;
    }}
}};
"""


def template_backlash(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Backlash block."""
    deadband = block.parameters.get("deadband", 1.0)
    initial_output = block.parameters.get("initialOutput", 0.0)
    half_width = deadband / 2.0

    return f"""
// {block.name} - Backlash
class {class_name} {{
public:
    double input = 0.0;
    double output = {initial_output};
    double deadband = {deadband};
    double half_width = {half_width};
    double prev_output = {initial_output};

    void init() {{
        output = {initial_output};
        prev_output = {initial_output};
    }}

    void update(double t) {{
        (void)t;
        double diff = input - prev_output;
        if (diff > half_width) {{
            output = input - half_width;
        }} else if (diff < -half_width) {{
            output = input + half_width;
        }} else {{
            output = prev_output;
        }}
        prev_output = output;
    }}

    double get_output(int port) const {{
        (void)port;
        return output;
    }}
}};
"""


def template_notch_filter(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for NotchFilter block."""
    notch_freq = block.parameters.get("notchFrequency", 60.0)
    bandwidth = block.parameters.get("bandwidth", 10.0)
    sample_time = block.parameters.get("sampleTime", 0.01)

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

    b0n = b0 / a0
    b1n = b1 / a0
    b2n = b2 / a0
    a1n = a1 / a0
    a2n = a2 / a0

    return f"""
// {block.name} - Notch Filter
class {class_name} {{
public:
    double input = 0.0;
    double output = 0.0;
    std::array<double, 3> b = {{{{{b0n}, {b1n}, {b2n}}}}};
    std::array<double, 3> a = {{{{1.0, {a1n}, {a2n}}}}};
    std::array<double, 3> x{{}};  // Input history
    std::array<double, 3> y{{}};  // Output history

    void init() {{
        output = 0.0;
        x.fill(0.0);
        y.fill(0.0);
    }}

    void update(double t) {{
        (void)t;
        // Shift history
        x[2] = x[1];
        x[1] = x[0];
        x[0] = input;
        y[2] = y[1];
        y[1] = y[0];

        // Compute output
        y[0] = b[0] * x[0] + b[1] * x[1] + b[2] * x[2]
             - a[1] * y[1] - a[2] * y[2];
        output = y[0];
    }}

    double get_output(int port) const {{
        (void)port;
        return output;
    }}
}};
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
