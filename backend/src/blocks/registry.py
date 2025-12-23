"""Block registry - defines all available block types."""

from typing import Any


class BlockRegistry:
    """Registry of all available block definitions."""

    def __init__(self):
        self._blocks: dict[str, dict[str, Any]] = {}
        self._register_all_blocks()

    def _register_all_blocks(self):
        """Register all block definitions."""
        self._register_sources()
        self._register_sinks()
        self._register_continuous()
        self._register_discrete()
        self._register_math()
        self._register_routing()

    def _register_sources(self):
        """Register source blocks."""
        blocks = [
            {
                "type": "constant",
                "category": "sources",
                "name": "Constant",
                "description": "Output a constant value",
                "inputs": [],
                "outputs": [{"name": "out", "dataType": "double", "dimensions": [1]}],
                "parameters": [
                    {"name": "value", "type": "number", "default": 1, "label": "Constant Value"}
                ],
                "icon": "1",
            },
            {
                "type": "step",
                "category": "sources",
                "name": "Step",
                "description": "Output a step signal",
                "inputs": [],
                "outputs": [{"name": "out", "dataType": "double", "dimensions": [1]}],
                "parameters": [
                    {"name": "stepTime", "type": "number", "default": 1, "label": "Step Time"},
                    {"name": "initialValue", "type": "number", "default": 0, "label": "Initial Value"},
                    {"name": "finalValue", "type": "number", "default": 1, "label": "Final Value"},
                ],
                "icon": "⌐",
            },
            {
                "type": "ramp",
                "category": "sources",
                "name": "Ramp",
                "description": "Output a ramp signal",
                "inputs": [],
                "outputs": [{"name": "out", "dataType": "double", "dimensions": [1]}],
                "parameters": [
                    {"name": "slope", "type": "number", "default": 1, "label": "Slope"},
                    {"name": "startTime", "type": "number", "default": 0, "label": "Start Time"},
                    {"name": "initialOutput", "type": "number", "default": 0, "label": "Initial Output"},
                ],
                "icon": "/",
            },
            {
                "type": "sine_wave",
                "category": "sources",
                "name": "Sine Wave",
                "description": "Output a sinusoidal signal",
                "inputs": [],
                "outputs": [{"name": "out", "dataType": "double", "dimensions": [1]}],
                "parameters": [
                    {"name": "amplitude", "type": "number", "default": 1, "label": "Amplitude"},
                    {"name": "frequency", "type": "number", "default": 1, "label": "Frequency (Hz)"},
                    {"name": "phase", "type": "number", "default": 0, "label": "Phase (rad)"},
                    {"name": "bias", "type": "number", "default": 0, "label": "Bias"},
                ],
                "icon": "∿",
            },
            {
                "type": "clock",
                "category": "sources",
                "name": "Clock",
                "description": "Output simulation time",
                "inputs": [],
                "outputs": [{"name": "out", "dataType": "double", "dimensions": [1]}],
                "parameters": [],
                "icon": "⏱",
            },
        ]
        for block in blocks:
            self._blocks[block["type"]] = block

    def _register_sinks(self):
        """Register sink blocks."""
        blocks = [
            {
                "type": "scope",
                "category": "sinks",
                "name": "Scope",
                "description": "Display signal over time",
                "inputs": [{"name": "in", "dataType": "double", "dimensions": [1]}],
                "outputs": [],
                "parameters": [
                    {"name": "numInputs", "type": "number", "default": 1, "label": "Number of Inputs"},
                ],
                "icon": "📊",
            },
            {
                "type": "display",
                "category": "sinks",
                "name": "Display",
                "description": "Display current signal value",
                "inputs": [{"name": "in", "dataType": "double", "dimensions": [1]}],
                "outputs": [],
                "parameters": [],
                "icon": "🔢",
            },
            {
                "type": "to_workspace",
                "category": "sinks",
                "name": "To Workspace",
                "description": "Log signal to output data",
                "inputs": [{"name": "in", "dataType": "double", "dimensions": [1]}],
                "outputs": [],
                "parameters": [
                    {"name": "variableName", "type": "string", "default": "simout", "label": "Variable Name"},
                ],
                "icon": "💾",
            },
        ]
        for block in blocks:
            self._blocks[block["type"]] = block

    def _register_continuous(self):
        """Register continuous blocks."""
        blocks = [
            {
                "type": "integrator",
                "category": "continuous",
                "name": "Integrator",
                "description": "Integrate input signal",
                "inputs": [{"name": "in", "dataType": "double", "dimensions": [1]}],
                "outputs": [{"name": "out", "dataType": "double", "dimensions": [1]}],
                "parameters": [
                    {"name": "initialCondition", "type": "number", "default": 0, "label": "Initial Condition"},
                ],
                "icon": "∫",
            },
            {
                "type": "derivative",
                "category": "continuous",
                "name": "Derivative",
                "description": "Differentiate input signal",
                "inputs": [{"name": "in", "dataType": "double", "dimensions": [1]}],
                "outputs": [{"name": "out", "dataType": "double", "dimensions": [1]}],
                "parameters": [],
                "icon": "d/dt",
            },
            {
                "type": "transfer_function",
                "category": "continuous",
                "name": "Transfer Function",
                "description": "Continuous-time transfer function",
                "inputs": [{"name": "in", "dataType": "double", "dimensions": [1]}],
                "outputs": [{"name": "out", "dataType": "double", "dimensions": [1]}],
                "parameters": [
                    {"name": "numerator", "type": "array", "default": [1], "label": "Numerator"},
                    {"name": "denominator", "type": "array", "default": [1, 1], "label": "Denominator"},
                ],
                "icon": "H(s)",
            },
            {
                "type": "state_space",
                "category": "continuous",
                "name": "State-Space",
                "description": "State-space model (A, B, C, D)",
                "inputs": [{"name": "in", "dataType": "double", "dimensions": [1]}],
                "outputs": [{"name": "out", "dataType": "double", "dimensions": [1]}],
                "parameters": [
                    {"name": "A", "type": "array", "default": [[0]], "label": "A Matrix"},
                    {"name": "B", "type": "array", "default": [[1]], "label": "B Matrix"},
                    {"name": "C", "type": "array", "default": [[1]], "label": "C Matrix"},
                    {"name": "D", "type": "array", "default": [[0]], "label": "D Matrix"},
                ],
                "icon": "SS",
            },
            {
                "type": "pid_controller",
                "category": "continuous",
                "name": "PID Controller",
                "description": "Continuous PID controller",
                "inputs": [{"name": "in", "dataType": "double", "dimensions": [1]}],
                "outputs": [{"name": "out", "dataType": "double", "dimensions": [1]}],
                "parameters": [
                    {"name": "Kp", "type": "number", "default": 1, "label": "Proportional (Kp)"},
                    {"name": "Ki", "type": "number", "default": 0, "label": "Integral (Ki)"},
                    {"name": "Kd", "type": "number", "default": 0, "label": "Derivative (Kd)"},
                    {"name": "N", "type": "number", "default": 100, "label": "Filter Coefficient (N)"},
                ],
                "icon": "PID",
            },
        ]
        for block in blocks:
            self._blocks[block["type"]] = block

    def _register_discrete(self):
        """Register discrete blocks."""
        blocks = [
            {
                "type": "unit_delay",
                "category": "discrete",
                "name": "Unit Delay",
                "description": "Delay signal by one sample period",
                "inputs": [{"name": "in", "dataType": "double", "dimensions": [1]}],
                "outputs": [{"name": "out", "dataType": "double", "dimensions": [1]}],
                "parameters": [
                    {"name": "initialCondition", "type": "number", "default": 0, "label": "Initial Condition"},
                    {"name": "sampleTime", "type": "number", "default": 0.1, "label": "Sample Time"},
                ],
                "icon": "1/z",
            },
            {
                "type": "zero_order_hold",
                "category": "discrete",
                "name": "Zero-Order Hold",
                "description": "Sample and hold input signal",
                "inputs": [{"name": "in", "dataType": "double", "dimensions": [1]}],
                "outputs": [{"name": "out", "dataType": "double", "dimensions": [1]}],
                "parameters": [
                    {"name": "sampleTime", "type": "number", "default": 0.1, "label": "Sample Time"},
                ],
                "icon": "ZOH",
            },
        ]
        for block in blocks:
            self._blocks[block["type"]] = block

    def _register_math(self):
        """Register math operation blocks."""
        blocks = [
            {
                "type": "sum",
                "category": "math",
                "name": "Sum",
                "description": "Add or subtract inputs",
                "inputs": [
                    {"name": "in1", "dataType": "double", "dimensions": [1]},
                    {"name": "in2", "dataType": "double", "dimensions": [1]},
                ],
                "outputs": [{"name": "out", "dataType": "double", "dimensions": [1]}],
                "parameters": [
                    {"name": "signs", "type": "string", "default": "++", "label": "Sign List"},
                ],
                "icon": "Σ",
            },
            {
                "type": "gain",
                "category": "math",
                "name": "Gain",
                "description": "Multiply input by constant",
                "inputs": [{"name": "in", "dataType": "double", "dimensions": [1]}],
                "outputs": [{"name": "out", "dataType": "double", "dimensions": [1]}],
                "parameters": [
                    {"name": "gain", "type": "number", "default": 1, "label": "Gain"},
                ],
                "icon": "K",
            },
            {
                "type": "product",
                "category": "math",
                "name": "Product",
                "description": "Multiply or divide inputs",
                "inputs": [
                    {"name": "in1", "dataType": "double", "dimensions": [1]},
                    {"name": "in2", "dataType": "double", "dimensions": [1]},
                ],
                "outputs": [{"name": "out", "dataType": "double", "dimensions": [1]}],
                "parameters": [
                    {"name": "operations", "type": "string", "default": "**", "label": "Operations"},
                ],
                "icon": "×",
            },
            {
                "type": "abs",
                "category": "math",
                "name": "Abs",
                "description": "Absolute value",
                "inputs": [{"name": "in", "dataType": "double", "dimensions": [1]}],
                "outputs": [{"name": "out", "dataType": "double", "dimensions": [1]}],
                "parameters": [],
                "icon": "|u|",
            },
            {
                "type": "saturation",
                "category": "math",
                "name": "Saturation",
                "description": "Limit signal to range",
                "inputs": [{"name": "in", "dataType": "double", "dimensions": [1]}],
                "outputs": [{"name": "out", "dataType": "double", "dimensions": [1]}],
                "parameters": [
                    {"name": "upperLimit", "type": "number", "default": 1, "label": "Upper Limit"},
                    {"name": "lowerLimit", "type": "number", "default": -1, "label": "Lower Limit"},
                ],
                "icon": "⊏⊐",
            },
        ]
        for block in blocks:
            self._blocks[block["type"]] = block

    def _register_routing(self):
        """Register signal routing blocks."""
        blocks = [
            {
                "type": "mux",
                "category": "routing",
                "name": "Mux",
                "description": "Combine signals into vector",
                "inputs": [
                    {"name": "in1", "dataType": "double", "dimensions": [1]},
                    {"name": "in2", "dataType": "double", "dimensions": [1]},
                ],
                "outputs": [{"name": "out", "dataType": "double", "dimensions": [2]}],
                "parameters": [
                    {"name": "numInputs", "type": "number", "default": 2, "label": "Number of Inputs"},
                ],
                "icon": "⋮→",
            },
            {
                "type": "demux",
                "category": "routing",
                "name": "Demux",
                "description": "Split vector into signals",
                "inputs": [{"name": "in", "dataType": "double", "dimensions": [2]}],
                "outputs": [
                    {"name": "out1", "dataType": "double", "dimensions": [1]},
                    {"name": "out2", "dataType": "double", "dimensions": [1]},
                ],
                "parameters": [
                    {"name": "numOutputs", "type": "number", "default": 2, "label": "Number of Outputs"},
                ],
                "icon": "→⋮",
            },
            {
                "type": "switch",
                "category": "routing",
                "name": "Switch",
                "description": "Switch between inputs based on control",
                "inputs": [
                    {"name": "in1", "dataType": "double", "dimensions": [1]},
                    {"name": "control", "dataType": "double", "dimensions": [1]},
                    {"name": "in2", "dataType": "double", "dimensions": [1]},
                ],
                "outputs": [{"name": "out", "dataType": "double", "dimensions": [1]}],
                "parameters": [
                    {"name": "threshold", "type": "number", "default": 0, "label": "Threshold"},
                ],
                "icon": "⇋",
            },
        ]
        for block in blocks:
            self._blocks[block["type"]] = block

    def get(self, block_type: str) -> dict[str, Any] | None:
        """Get a block definition by type."""
        return self._blocks.get(block_type)

    def get_all_definitions(self) -> list[dict[str, Any]]:
        """Get all block definitions."""
        return list(self._blocks.values())

    def get_categories(self) -> list[str]:
        """Get all block categories."""
        return list(set(b["category"] for b in self._blocks.values()))

    def get_by_category(self, category: str) -> list[dict[str, Any]]:
        """Get all blocks in a category."""
        return [b for b in self._blocks.values() if b["category"] == category]


# Global registry instance
block_registry = BlockRegistry()
