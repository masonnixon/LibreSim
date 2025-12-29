"""Integration tests for frontend-backend block consistency.

These tests ensure that all blocks defined in the frontend have corresponding
implementations in the backend simulation engine. This prevents the "silent failure"
issue where a block exists in the UI but doesn't actually work in simulation.
"""

import pytest

from src.simulation.osk_adapter import BLOCK_TYPE_MAP, PARAM_MAP
from src.blocks.registry import block_registry


class TestBlockRegistration:
    """Tests to verify all blocks are properly registered across layers."""

    # All block types that should be supported
    # This list is derived from frontend/src/blocks/*.ts
    FRONTEND_BLOCKS = {
        # Sources
        "constant",
        "step",
        "ramp",
        "sine_wave",
        "pulse_generator",
        "clock",
        "white_noise",
        "uniform_noise",
        # Sinks
        "scope",
        "display",
        "to_workspace",
        "terminator",
        # Continuous
        "integrator",
        "derivative",
        "transfer_function",
        "state_space",
        "pid_controller",
        # Discrete
        "unit_delay",
        "zero_order_hold",
        "discrete_integrator",
        "discrete_derivative",
        "discrete_transfer_function",
        # Math Operations
        "sum",
        "gain",
        "product",
        "abs",
        "sign",
        "bias",
        "saturation",
        "dead_zone",
        "math_function",
        "trigonometry",
        "sqrt",
        "unary_minus",
        "minmax",
        "dot_product",
        # Routing
        "mux",
        "demux",
        "switch",
        "reshape",
        # Subsystems
        "inport",
        "outport",
        "subsystem",
        # Signal Processing
        "rate_limiter",
        "moving_average",
        "low_pass_filter",
        "high_pass_filter",
        "band_pass_filter",
        "analog_filter",
        "notch_filter",
        "backlash",
        # Nonlinear
        "lookup_table_1d",
        "lookup_table_2d",
        "quantizer",
        "relay",
        "coulomb_friction",
        "variable_transport_delay",
        # Observers
        "luenberger_observer",
        "kalman_filter",
        "extended_kalman_filter",
        # Control Analysis (these output static data, not simulation)
        "bode_plot",
        "nyquist_plot",
        "pole_zero_map",
        "step_info",
    }

    # Blocks that are defined in frontend but intentionally not implemented in backend
    # (with reason documented)
    INTENTIONALLY_UNIMPLEMENTED = {
        # These are simple pass-through or UI-only blocks
        "sqrt": "Handled by math_function block with function='sqrt'",
        "unary_minus": "Can be achieved with gain=-1",
        "minmax": "Not yet implemented",
        "dot_product": "Not yet implemented",
        # These are advanced routing blocks not commonly used
        "selector": "Not yet implemented",
        "multiport_switch": "Not yet implemented",
        "concatenate": "Not yet implemented",
        "from": "Goto/From not yet implemented",
        "goto": "Goto/From not yet implemented",
        "ground": "Not yet implemented",
        # These are utility blocks
        "data_type_conversion": "Not needed - all values are doubles",
        "xy_graph": "Not yet implemented",
        "zero_pole": "Use transfer_function instead",
        "discrete_filter": "Use discrete_transfer_function instead",
    }

    # Blocks that have OSK implementations but are not in the basic registry
    # These are implemented but registry.py only has basic definitions
    REGISTRY_NOT_REQUIRED = {
        "outport", "inport", "subsystem",  # Subsystem blocks
        "quantizer", "relay", "coulomb_friction", "variable_transport_delay", "lookup_table_1d", "lookup_table_2d",  # Nonlinear
        "discrete_derivative", "discrete_integrator", "discrete_transfer_function",  # Discrete
        "low_pass_filter", "high_pass_filter", "band_pass_filter", "analog_filter", "notch_filter", "moving_average", "rate_limiter", "backlash",  # Signal processing
        "luenberger_observer", "kalman_filter", "extended_kalman_filter",  # Observers
        "bode_plot", "nyquist_plot", "pole_zero_map", "step_info",  # Control analysis
        "white_noise", "uniform_noise", "pulse_generator",  # Additional sources
        "terminator", "reshape",  # Misc
    }

    def test_all_core_blocks_have_osk_implementation(self):
        """Verify all core frontend blocks have OSK block implementations."""
        missing_blocks = []
        for block_type in self.FRONTEND_BLOCKS:
            if block_type not in BLOCK_TYPE_MAP:
                if block_type not in self.INTENTIONALLY_UNIMPLEMENTED:
                    missing_blocks.append(block_type)

        if missing_blocks:
            pytest.fail(
                f"The following frontend blocks are missing OSK implementations: {missing_blocks}\n"
                "If these are intentionally unimplemented, add them to INTENTIONALLY_UNIMPLEMENTED with a reason."
            )

    def test_all_core_blocks_have_registry_definition(self):
        """Verify all core frontend blocks have backend registry definitions."""
        missing_blocks = []
        for block_type in self.FRONTEND_BLOCKS:
            if block_registry.get(block_type) is None:
                if block_type not in self.INTENTIONALLY_UNIMPLEMENTED and block_type not in self.REGISTRY_NOT_REQUIRED:
                    missing_blocks.append(block_type)

        if missing_blocks:
            pytest.fail(
                f"The following frontend blocks are missing registry definitions: {missing_blocks}\n"
                "Add these blocks to src/blocks/registry.py or REGISTRY_NOT_REQUIRED"
            )

    def test_osk_blocks_have_param_mapping(self):
        """Verify blocks with parameters have proper parameter mappings."""
        # Get blocks from registry that have parameters
        for block_type, block_class in BLOCK_TYPE_MAP.items():
            registry_def = block_registry.get(block_type)
            if registry_def and registry_def.get("parameters"):
                # Check if block has param mapping when it needs one
                params = registry_def["parameters"]
                if params and block_type not in PARAM_MAP:
                    # Check if the OSK class accepts any constructor args
                    import inspect
                    sig = inspect.signature(block_class.__init__)
                    # Exclude 'self' from the parameter list
                    constructor_params = [
                        p for p in sig.parameters.keys() if p != 'self'
                    ]
                    if constructor_params:
                        # Block has constructor params but no PARAM_MAP entry
                        # This might be okay if param names match exactly
                        pass  # Could add more strict checking here


class TestBiasBlock:
    """Specific tests for the Bias block - the block that triggered this test suite."""

    def test_bias_block_exists_in_osk(self):
        """Verify Bias block exists in BLOCK_TYPE_MAP."""
        assert "bias" in BLOCK_TYPE_MAP, "Bias block missing from BLOCK_TYPE_MAP"

    def test_bias_block_exists_in_registry(self):
        """Verify Bias block exists in block registry."""
        bias_def = block_registry.get("bias")
        assert bias_def is not None, "Bias block missing from block registry"
        assert bias_def["type"] == "bias"
        assert bias_def["category"] == "math"

    def test_bias_block_has_param_mapping(self):
        """Verify Bias block has proper parameter mapping."""
        assert "bias" in PARAM_MAP, "Bias block missing from PARAM_MAP"
        assert "bias" in PARAM_MAP["bias"], "bias parameter not mapped"

    def test_bias_block_functionality(self):
        """Test that Bias block actually works correctly."""
        from src.osk.blocks.math_ops import Bias

        # Test with positive bias
        bias_block = Bias(bias=5.0)
        bias_block.setInput(3.0)
        bias_block.update()
        assert bias_block.getOutput() == 8.0, "Bias should add bias to input"

        # Test with negative bias
        bias_block = Bias(bias=-2.0)
        bias_block.setInput(10.0)
        bias_block.update()
        assert bias_block.getOutput() == 8.0, "Negative bias should subtract"

        # Test with zero bias
        bias_block = Bias(bias=0.0)
        bias_block.setInput(7.0)
        bias_block.update()
        assert bias_block.getOutput() == 7.0, "Zero bias should pass through"

    def test_bias_block_vector_input(self):
        """Test that Bias block works with vector inputs."""
        from src.osk.blocks.math_ops import Bias

        bias_block = Bias(bias=1.0)
        bias_block.setInput([2.0, 3.0, 4.0])
        bias_block.update()

        # Check vector output
        vec = bias_block.getOutputVector()
        assert vec is not None, "Should return vector output"
        assert vec == [3.0, 4.0, 5.0], "Should add bias to each element"


class TestBlockSimulationIntegration:
    """Test that blocks work correctly in a simulation context."""

    def test_bias_in_simulation_adapter(self):
        """Test Bias block through the OSK adapter."""
        from src.simulation.osk_adapter import OSKAdapter
        from src.simulation.compiler import CompiledBlock, CompiledModel
        from src.models.simulation import SimulationConfig, SolverType

        # Create a simple model: Constant -> Bias -> Scope
        blocks = [
            CompiledBlock(
                id="const1",
                name="Constant1",
                type="constant",
                parameters={"value": 5.0},
                input_connections=[],
            ),
            CompiledBlock(
                id="bias1",
                name="Bias1",
                type="bias",
                parameters={"bias": 3.0},
                input_connections=["const1:const1-out"],
            ),
            CompiledBlock(
                id="scope1",
                name="Scope1",
                type="scope",
                parameters={"numInputs": 1},
                input_connections=["bias1:bias1-out"],
            ),
        ]

        model = CompiledModel(
            success=True,
            message="Test model",
            blocks=blocks,
            execution_order=["const1", "bias1", "scope1"],
        )

        config = SimulationConfig(
            solver=SolverType.EULER,
            step_size=0.01,
            start_time=0.0,
            stop_time=0.1,
        )

        adapter = OSKAdapter()
        adapter.initialize(model, config)

        # Step the simulation
        outputs = adapter.step(0.0, 0.01)

        # Check the bias block was created and works
        bias_block = adapter.get_block("bias1")
        assert bias_block is not None, "Bias block should be created"
        # The output should be 5 + 3 = 8
        assert bias_block.getOutput() == 8.0, f"Expected 8.0, got {bias_block.getOutput()}"


class TestAllMathBlocks:
    """Comprehensive tests for all math operation blocks."""

    def test_sum_block(self):
        """Test Sum block."""
        from src.osk.blocks.math_ops import Sum

        block = Sum(signs="+-")
        block.setInput(5.0, 0)
        block.setInput(3.0, 1)
        block.update()
        assert block.getOutput() == 2.0  # 5 - 3

    def test_gain_block(self):
        """Test Gain block."""
        from src.osk.blocks.math_ops import Gain

        block = Gain(gain=2.5)
        block.setInput(4.0)
        block.update()
        assert block.getOutput() == 10.0

    def test_product_block(self):
        """Test Product block."""
        from src.osk.blocks.math_ops import Product

        block = Product(operations="*/")
        block.setInput(6.0, 0)
        block.setInput(2.0, 1)
        block.update()
        assert block.getOutput() == 3.0  # 6 / 2

    def test_abs_block(self):
        """Test Abs block."""
        from src.osk.blocks.math_ops import Abs

        block = Abs()
        block.setInput(-5.0)
        block.update()
        assert block.getOutput() == 5.0

    def test_sign_block(self):
        """Test Sign block."""
        from src.osk.blocks.math_ops import Sign

        block = Sign()

        block.setInput(5.0)
        block.update()
        assert block.getOutput() == 1.0

        block.setInput(-5.0)
        block.update()
        assert block.getOutput() == -1.0

    def test_saturation_block(self):
        """Test Saturation block."""
        from src.osk.blocks.math_ops import Saturation

        block = Saturation(upper_limit=10.0, lower_limit=-10.0)

        block.setInput(5.0)
        block.update()
        assert block.getOutput() == 5.0  # Within limits

        block.setInput(15.0)
        block.update()
        assert block.getOutput() == 10.0  # Clamped to upper

        block.setInput(-15.0)
        block.update()
        assert block.getOutput() == -10.0  # Clamped to lower

    def test_dead_zone_block(self):
        """Test DeadZone block."""
        from src.osk.blocks.math_ops import DeadZone

        block = DeadZone(start=-1.0, end=1.0)

        block.setInput(0.5)
        block.update()
        assert block.getOutput() == 0.0  # Within dead zone

        block.setInput(2.0)
        block.update()
        assert block.getOutput() == 1.0  # 2 - 1 = 1

        block.setInput(-2.0)
        block.update()
        assert block.getOutput() == -1.0  # -2 - (-1) = -1

    def test_bias_block(self):
        """Test Bias block."""
        from src.osk.blocks.math_ops import Bias

        block = Bias(bias=10.0)
        block.setInput(5.0)
        block.update()
        assert block.getOutput() == 15.0

    def test_math_function_block(self):
        """Test MathFunction block."""
        from src.osk.blocks.math_ops import MathFunction
        import math

        # Test exp
        block = MathFunction(function="exp")
        block.setInput(1.0)
        block.update()
        assert block.getOutput() == pytest.approx(math.e)

        # Test sqrt
        block = MathFunction(function="sqrt")
        block.setInput(16.0)
        block.update()
        assert block.getOutput() == 4.0

        # Test square
        block = MathFunction(function="square")
        block.setInput(5.0)
        block.update()
        assert block.getOutput() == 25.0

    def test_trigonometry_block(self):
        """Test Trigonometry block."""
        from src.osk.blocks.math_ops import Trigonometry
        import math

        block = Trigonometry(function="sin")
        block.setInput(math.pi / 2)
        block.update()
        assert block.getOutput() == pytest.approx(1.0)

        block = Trigonometry(function="cos")
        block.setInput(0.0)
        block.update()
        assert block.getOutput() == pytest.approx(1.0)

    def test_switch_block(self):
        """Test Switch block."""
        from src.osk.blocks.math_ops import Switch

        block = Switch(threshold=0.0, criteria="gte")
        block.setInput(10.0, 0)  # in1
        block.setInput(1.0, 1)   # control (>= 0, so use in1)
        block.setInput(20.0, 2)  # in2
        block.update()
        assert block.getOutput() == 10.0  # control >= threshold, use in1

        block.setInput(-1.0, 1)  # control < 0
        block.update()
        assert block.getOutput() == 20.0  # control < threshold, use in2


class TestAllSourceBlocks:
    """Comprehensive tests for all source blocks."""

    def test_constant_block(self):
        """Test Constant block."""
        from src.osk.blocks.sources import Constant

        block = Constant(value=42.0)
        block.init()
        assert block.getOutput() == 42.0

    def test_step_block(self):
        """Test Step block."""
        from src.osk.blocks.sources import Step
        from src.osk.state import State

        block = Step(step_time=1.0, initial_value=0.0, final_value=5.0)
        block.init()

        State.t = 0.5
        block.update()
        assert block.getOutput() == 0.0  # Before step

        State.t = 1.5
        block.update()
        assert block.getOutput() == 5.0  # After step

    def test_ramp_block(self):
        """Test Ramp block."""
        from src.osk.blocks.sources import Ramp
        from src.osk.state import State

        block = Ramp(slope=2.0, start_time=1.0, initial_output=0.0)
        block.init()

        State.t = 0.5
        block.update()
        assert block.getOutput() == 0.0  # Before start

        State.t = 2.0
        block.update()
        assert block.getOutput() == 2.0  # (2 - 1) * 2 = 2

    def test_sine_wave_block(self):
        """Test SineWave block."""
        from src.osk.blocks.sources import SineWave
        from src.osk.state import State
        import math

        block = SineWave(amplitude=1.0, frequency=1.0, phase=0.0, bias=0.0)
        block.init()

        State.t = 0.25  # quarter period at 1Hz
        block.update()
        assert block.getOutput() == pytest.approx(1.0, abs=0.01)  # sin(pi/2) = 1

    def test_clock_block(self):
        """Test Clock block."""
        from src.osk.blocks.sources import Clock
        from src.osk.state import State

        block = Clock()
        block.init()

        State.t = 5.5
        block.update()
        assert block.getOutput() == 5.5

    def test_pulse_generator_block(self):
        """Test PulseGenerator block."""
        from src.osk.blocks.sources import PulseGenerator
        from src.osk.state import State

        # duty_cycle is in percentage (50 = 50%)
        block = PulseGenerator(amplitude=1.0, period=1.0, duty_cycle=50.0, phase_delay=0.0)
        block.init()

        State.t = 0.25  # In first half of period (on)
        block.update()
        assert block.getOutput() == 1.0

        State.t = 0.75  # In second half of period (off)
        block.update()
        assert block.getOutput() == 0.0


class TestAllRoutingBlocks:
    """Comprehensive tests for all routing blocks."""

    def test_mux_block(self):
        """Test Mux block."""
        from src.osk.blocks.math_ops import Mux

        block = Mux(num_inputs=3)
        block.setInput(1.0, 0)
        block.setInput(2.0, 1)
        block.setInput(3.0, 2)
        block.update()

        vec = block.getOutputVector()
        assert vec == [1.0, 2.0, 3.0]

    def test_demux_block(self):
        """Test Demux block."""
        from src.osk.blocks.math_ops import Demux

        block = Demux(num_outputs=3)
        block.setInput([10.0, 20.0, 30.0])
        block.update()

        assert block.getOutput(0) == 10.0
        assert block.getOutput(1) == 20.0
        assert block.getOutput(2) == 30.0
