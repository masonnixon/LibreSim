"""C++ templates for RF blocks."""

from ....models import BlockInfo


def rf_budget_element_template(block: BlockInfo, class_name: str) -> str:
    """Generate a three-port cascaded RF budget element."""
    gain_db = block.parameters.get("gainDb", 0.0)
    noise_figure_db = block.parameters.get("noiseFigureDb", 0.0)
    return f"""
// {block.name} - Cascaded RF budget element
#include <algorithm>
#include <array>
#include <cmath>

class {class_name} {{
public:
    double gain_db = {gain_db};
    double noise_figure_db = {noise_figure_db};
    double input = 0.0;
    double input1 = 0.0;
    double input2 = 0.0;
    std::array<double, 3> output = {{0.0, 0.0, 0.0}};

    void init() {{
        output = {{0.0, 0.0, 0.0}};
    }}

    void update(double t) {{
        (void)t;
        output[0] = input + gain_db;
        output[1] = input1 + gain_db;
        if (input1 == 0.0 && input2 == 0.0) {{
            output[2] = noise_figure_db;
        }} else {{
            double old_factor = std::pow(10.0, input2 / 10.0);
            double element_factor = std::pow(10.0, noise_figure_db / 10.0);
            double cascade_gain = std::pow(10.0, input1 / 10.0);
            double new_factor;
            if (cascade_gain > 1e-10) {{
                new_factor = old_factor + (element_factor - 1.0) / cascade_gain;
            }} else {{
                new_factor = old_factor + element_factor - 1.0;
            }}
            output[2] = 10.0 * std::log10(std::max(new_factor, 1.0));
        }}
    }}

    double get_output(int port = 0) const {{
        if (port >= 0 && port < 3) return output[port];
        return 0.0;
    }}
}};
"""


def am_modulator_template(block: BlockInfo, class_name: str) -> str:
    """Generate an AM modulator with external or internal carrier semantics."""
    modulation_index = block.parameters.get("modulationIndex", 0.5)
    carrier_freq = block.parameters.get(
        "carrierFreq", block.parameters.get("carrierFreqHz", 1e6)
    )
    carrier_amplitude = block.parameters.get("carrierAmplitude", 1.0)
    if len(block.input_dimensions) > 1:
        output_expression = "input1 * envelope"
    else:
        output_expression = (
            "carrier_amplitude * envelope * "
            "std::cos(2.0 * 3.14159265358979323846 * carrier_freq * t)"
        )
    return f"""
// {block.name} - Amplitude modulator
#include <cmath>

class {class_name} {{
public:
    double modulation_index = {modulation_index};
    double carrier_freq = {carrier_freq};
    double carrier_amplitude = {carrier_amplitude};
    double input = 0.0;
    double input1 = 0.0;
    double output = 0.0;

    void init() {{
        output = 0.0;
    }}

    void update(double t) {{
        (void)t;
        double envelope = 1.0 + modulation_index * input;
        output = {output_expression};
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output;
    }}
}};
"""


RF_TEMPLATES = {
    "rf_budget_element": rf_budget_element_template,
    "am_modulator": am_modulator_template,
}
