"""Python templates for RF blocks."""

from ....models import BlockInfo


def rf_budget_element_template(block: BlockInfo, class_name: str) -> str:
    """Generate a three-port cascaded RF budget element."""
    gain_db = block.parameters.get("gainDb", 0.0)
    noise_figure_db = block.parameters.get("noiseFigureDb", 0.0)
    return f'''
import math

class {class_name}:
    """Cascaded RF budget element: {block.name}"""

    def __init__(self):
        self.gain_db = {gain_db}
        self.noise_figure_db = {noise_figure_db}
        self.input = 0.0
        self.input1 = 0.0
        self.input2 = 0.0
        self.output = [0.0, 0.0, 0.0]

    def init(self):
        self.output = [0.0, 0.0, 0.0]

    def update(self, t: float):
        self.output[0] = self.input + self.gain_db
        self.output[1] = self.input1 + self.gain_db
        if self.input1 == 0.0 and self.input2 == 0.0:
            self.output[2] = self.noise_figure_db
        else:
            old_factor = 10.0 ** (self.input2 / 10.0)
            element_factor = 10.0 ** (self.noise_figure_db / 10.0)
            cascade_gain = 10.0 ** (self.input1 / 10.0)
            if cascade_gain > 1e-10:
                new_factor = old_factor + (element_factor - 1.0) / cascade_gain
            else:
                new_factor = old_factor + element_factor - 1.0
            self.output[2] = 10.0 * math.log10(max(new_factor, 1.0))

    def get_output(self, port: int = 0) -> float:
        if 0 <= port < 3:
            return self.output[port]
        return 0.0
'''


def am_modulator_template(block: BlockInfo, class_name: str) -> str:
    """Generate an AM modulator with external or internal carrier semantics."""
    modulation_index = block.parameters.get("modulationIndex", 0.5)
    carrier_freq = block.parameters.get(
        "carrierFreq", block.parameters.get("carrierFreqHz", 1e6)
    )
    carrier_amplitude = block.parameters.get("carrierAmplitude", 1.0)
    if len(block.input_dimensions) > 1:
        output_expression = "self.input1 * envelope"
    else:
        output_expression = (
            "self.carrier_amplitude * envelope * "
            "math.cos(2.0 * math.pi * self.carrier_freq * t)"
        )
    return f'''
import math

class {class_name}:
    """Amplitude modulator: {block.name}"""

    def __init__(self):
        self.modulation_index = {modulation_index}
        self.carrier_freq = {carrier_freq}
        self.carrier_amplitude = {carrier_amplitude}
        self.input = 0.0
        self.input1 = 0.0
        self.output = 0.0

    def init(self):
        self.output = 0.0

    def update(self, t: float):
        envelope = 1.0 + self.modulation_index * self.input
        self.output = {output_expression}

    def get_output(self, port: int = 0) -> float:
        return self.output
'''


RF_TEMPLATES = {
    "rf_budget_element": rf_budget_element_template,
    "am_modulator": am_modulator_template,
}
