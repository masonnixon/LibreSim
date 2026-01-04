"""C++ templates for DSP (Digital Signal Processing) blocks."""

from ....models import BlockInfo


def template_fir_filter(block: BlockInfo, class_name: str) -> str:
    """Generate C++ FIR filter block code."""
    coefficients = block.parameters.get("coefficients", [1.0])
    if not isinstance(coefficients, list):
        coefficients = [coefficients]

    num_taps = len(coefficients)
    coef_init = ", ".join(str(c) for c in coefficients)

    return f"""
// {block.name} - FIR Filter
#include <array>

class {class_name} {{
public:
    static constexpr int NUM_TAPS = {num_taps};
    std::array<double, NUM_TAPS> coefficients = {{{coef_init}}};
    std::array<double, NUM_TAPS> buffer = {{}};
    double input = 0.0;
    double output = 0.0;

    void init() {{
        buffer.fill(0.0);
        output = 0.0;
    }}

    void update(double t) {{
        (void)t;
        // Shift buffer and add new sample
        for (int i = NUM_TAPS - 1; i > 0; i--) {{
            buffer[i] = buffer[i - 1];
        }}
        buffer[0] = input;

        // Apply FIR filter
        output = 0.0;
        for (int i = 0; i < NUM_TAPS; i++) {{
            output += coefficients[i] * buffer[i];
        }}
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output;
    }}
}};
"""


def template_iir_filter(block: BlockInfo, class_name: str) -> str:
    """Generate C++ IIR filter block code."""
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
#include <array>

class {class_name} {{
public:
    static constexpr int ORDER = {order};
    static constexpr int NUM_LEN = {len(numerator)};
    static constexpr int DEN_LEN = {len(denominator)};
    std::array<double, NUM_LEN> numerator = {{{num_init}}};
    std::array<double, DEN_LEN> denominator = {{{den_init}}};
    std::array<double, ORDER> x_buffer = {{}};
    std::array<double, ORDER> y_buffer = {{}};
    double input = 0.0;
    double output = 0.0;

    void init() {{
        x_buffer.fill(0.0);
        y_buffer.fill(0.0);
        output = 0.0;

        // Normalize by a0
        if (denominator[0] != 0.0) {{
            double a0 = denominator[0];
            for (int i = 0; i < NUM_LEN; i++) numerator[i] /= a0;
            for (int i = 0; i < DEN_LEN; i++) denominator[i] /= a0;
        }}
    }}

    void update(double t) {{
        (void)t;
        // Shift input buffer
        for (int i = ORDER - 1; i > 0; i--) {{
            x_buffer[i] = x_buffer[i - 1];
        }}
        x_buffer[0] = input;

        // Apply IIR filter
        double y = 0.0;
        for (int i = 0; i < NUM_LEN && i < ORDER; i++) {{
            y += numerator[i] * x_buffer[i];
        }}
        for (int i = 1; i < DEN_LEN && i <= ORDER; i++) {{
            y -= denominator[i] * y_buffer[i - 1];
        }}

        output = y;
        for (int i = ORDER - 1; i > 0; i--) {{
            y_buffer[i] = y_buffer[i - 1];
        }}
        y_buffer[0] = y;
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output;
    }}
}};
"""


def template_mean(block: BlockInfo, class_name: str) -> str:
    """Generate C++ Mean block code."""
    window_size = block.parameters.get("windowSize", block.parameters.get("window_size", 10))

    return f"""
// {block.name} - Running Mean
#include <array>

class {class_name} {{
public:
    static constexpr int WINDOW_SIZE = {window_size};
    std::array<double, WINDOW_SIZE> buffer = {{}};
    int count = 0;
    int index = 0;
    double sum = 0.0;
    double input = 0.0;
    double output = 0.0;

    void init() {{
        buffer.fill(0.0);
        count = 0;
        index = 0;
        sum = 0.0;
        output = 0.0;
    }}

    void update(double t) {{
        (void)t;
        // Subtract old value and add new value
        sum -= buffer[index];
        buffer[index] = input;
        sum += input;

        index = (index + 1) % WINDOW_SIZE;
        if (count < WINDOW_SIZE) count++;

        // Compute mean
        if (count > 0) {{
            output = sum / count;
        }} else {{
            output = 0.0;
        }}
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output;
    }}
}};
"""


def template_variance(block: BlockInfo, class_name: str) -> str:
    """Generate C++ Variance block code."""
    window_size = block.parameters.get("windowSize", block.parameters.get("window_size", 10))

    return f"""
// {block.name} - Running Variance
#include <array>

class {class_name} {{
public:
    static constexpr int WINDOW_SIZE = {window_size};
    std::array<double, WINDOW_SIZE> buffer = {{}};
    int count = 0;
    int index = 0;
    double input = 0.0;
    double output = 0.0;

    void init() {{
        buffer.fill(0.0);
        count = 0;
        index = 0;
        output = 0.0;
    }}

    void update(double t) {{
        (void)t;
        buffer[index] = input;
        index = (index + 1) % WINDOW_SIZE;
        if (count < WINDOW_SIZE) count++;

        if (count > 1) {{
            double mean = 0.0;
            for (int i = 0; i < count; i++) {{
                mean += buffer[i];
            }}
            mean /= count;

            double var = 0.0;
            for (int i = 0; i < count; i++) {{
                double diff = buffer[i] - mean;
                var += diff * diff;
            }}
            output = var / (count - 1);
        }} else {{
            output = 0.0;
        }}
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output;
    }}
}};
"""


def template_rms(block: BlockInfo, class_name: str) -> str:
    """Generate C++ RMS block code."""
    window_size = block.parameters.get("windowSize", block.parameters.get("window_size", 10))

    return f"""
// {block.name} - Running RMS
#include <array>
#include <cmath>

class {class_name} {{
public:
    static constexpr int WINDOW_SIZE = {window_size};
    std::array<double, WINDOW_SIZE> buffer = {{}};
    int count = 0;
    int index = 0;
    double sum_sq = 0.0;
    double input = 0.0;
    double output = 0.0;

    void init() {{
        buffer.fill(0.0);
        count = 0;
        index = 0;
        sum_sq = 0.0;
        output = 0.0;
    }}

    void update(double t) {{
        (void)t;
        // Subtract old squared value and add new squared value
        sum_sq -= buffer[index] * buffer[index];
        buffer[index] = input;
        sum_sq += input * input;

        index = (index + 1) % WINDOW_SIZE;
        if (count < WINDOW_SIZE) count++;

        // Compute RMS
        if (count > 0) {{
            output = std::sqrt(sum_sq / count);
        }} else {{
            output = 0.0;
        }}
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output;
    }}
}};
"""


def template_downsampler(block: BlockInfo, class_name: str) -> str:
    """Generate C++ Downsampler block code."""
    factor = block.parameters.get("factor", 2)

    return f"""
// {block.name} - Downsampler
class {class_name} {{
public:
    int factor = {factor};
    int sample_count = 0;
    double input = 0.0;
    double output = 0.0;

    void init() {{
        sample_count = 0;
        output = 0.0;
    }}

    void update(double t) {{
        (void)t;
        if (sample_count % factor == 0) {{
            output = input;
        }}
        sample_count++;
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output;
    }}
}};
"""


def template_upsampler(block: BlockInfo, class_name: str) -> str:
    """Generate C++ Upsampler block code."""
    factor = block.parameters.get("factor", 2)

    return f"""
// {block.name} - Upsampler
class {class_name} {{
public:
    int factor = {factor};
    int phase = 0;
    double current_sample = 0.0;
    double input = 0.0;
    double output = 0.0;

    void init() {{
        phase = 0;
        current_sample = 0.0;
        output = 0.0;
    }}

    void update(double t) {{
        (void)t;
        if (phase == 0) {{
            current_sample = input;
            output = current_sample;
        }} else {{
            output = 0.0;
        }}
        phase = (phase + 1) % factor;
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output;
    }}
}};
"""


def template_peak_detector(block: BlockInfo, class_name: str) -> str:
    """Generate C++ Peak Detector block code."""
    threshold = block.parameters.get("threshold", 0.0)

    return f"""
// {block.name} - Peak Detector
class {class_name} {{
public:
    double threshold = {threshold};
    double prev_prev = 0.0;
    double prev = 0.0;
    double current = 0.0;
    double input = 0.0;
    double output = 0.0;

    void init() {{
        prev_prev = 0.0;
        prev = 0.0;
        current = 0.0;
        output = 0.0;
    }}

    void update(double t) {{
        (void)t;
        prev_prev = prev;
        prev = current;
        current = input;

        if (prev > prev_prev && prev > current && prev > threshold) {{
            output = 1.0;
        }} else {{
            output = 0.0;
        }}
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output;
    }}
}};
"""


def template_zero_crossing_detector(block: BlockInfo, class_name: str) -> str:
    """Generate C++ Zero Crossing Detector block code."""
    direction = block.parameters.get("direction", "both")

    return f"""
// {block.name} - Zero Crossing Detector
#include <string>

class {class_name} {{
public:
    std::string direction = "{direction}";
    double prev = 0.0;
    double current = 0.0;
    double input = 0.0;
    double output = 0.0;

    void init() {{
        prev = 0.0;
        current = 0.0;
        output = 0.0;
    }}

    void update(double t) {{
        (void)t;
        prev = current;
        current = input;

        bool is_crossing = false;
        if (direction == "rising") {{
            is_crossing = (prev <= 0.0 && current > 0.0);
        }} else if (direction == "falling") {{
            is_crossing = (prev >= 0.0 && current < 0.0);
        }} else {{  // both
            is_crossing = (prev <= 0.0 && current > 0.0) || (prev >= 0.0 && current < 0.0);
        }}

        output = is_crossing ? 1.0 : 0.0;
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output;
    }}
}};
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
