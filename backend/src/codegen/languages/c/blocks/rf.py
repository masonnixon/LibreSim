"""C templates for RF blocks."""

from ....models import BlockInfo


def rf_budget_element_template(block: BlockInfo, struct_name: str) -> str:
    """Generate a three-port cascaded RF budget element."""
    gain_db = block.parameters.get("gainDb", 0.0)
    noise_figure_db = block.parameters.get("noiseFigureDb", 0.0)
    return f"""
// {block.name} - Cascaded RF budget element
#include <math.h>

typedef struct {{
    double gain_db;
    double noise_figure_db;
    double input;
    double input1;
    double input2;
    double output[3];
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->gain_db = {gain_db};
    b->noise_figure_db = {noise_figure_db};
    b->input = 0.0;
    b->input1 = 0.0;
    b->input2 = 0.0;
    b->output[0] = 0.0;
    b->output[1] = 0.0;
    b->output[2] = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    b->output[0] = b->input + b->gain_db;
    b->output[1] = b->input1 + b->gain_db;
    if (b->input1 == 0.0 && b->input2 == 0.0) {{
        b->output[2] = b->noise_figure_db;
    }} else {{
        double old_factor = pow(10.0, b->input2 / 10.0);
        double element_factor = pow(10.0, b->noise_figure_db / 10.0);
        double cascade_gain = pow(10.0, b->input1 / 10.0);
        double new_factor;
        if (cascade_gain > 1e-10) {{
            new_factor = old_factor + (element_factor - 1.0) / cascade_gain;
        }} else {{
            new_factor = old_factor + element_factor - 1.0;
        }}
        b->output[2] = 10.0 * log10(fmax(new_factor, 1.0));
    }}
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    if (port >= 0 && port < 3) return b->output[port];
    return 0.0;
}}
"""


def am_modulator_template(block: BlockInfo, struct_name: str) -> str:
    """Generate an AM modulator with external or internal carrier semantics."""
    modulation_index = block.parameters.get("modulationIndex", 0.5)
    carrier_freq = block.parameters.get(
        "carrierFreq", block.parameters.get("carrierFreqHz", 1e6)
    )
    carrier_amplitude = block.parameters.get("carrierAmplitude", 1.0)
    if len(block.input_dimensions) > 1:
        output_expression = "b->input1 * envelope"
    else:
        output_expression = (
            "b->carrier_amplitude * envelope * "
            "cos(2.0 * 3.14159265358979323846 * b->carrier_freq * t)"
        )
    return f"""
// {block.name} - Amplitude modulator
#include <math.h>

typedef struct {{
    double modulation_index;
    double carrier_freq;
    double carrier_amplitude;
    double input;
    double input1;
    double output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->modulation_index = {modulation_index};
    b->carrier_freq = {carrier_freq};
    b->carrier_amplitude = {carrier_amplitude};
    b->input = 0.0;
    b->input1 = 0.0;
    b->output = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    double envelope = 1.0 + b->modulation_index * b->input;
    b->output = {output_expression};
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


RF_TEMPLATES = {
    "rf_budget_element": rf_budget_element_template,
    "am_modulator": am_modulator_template,
}
