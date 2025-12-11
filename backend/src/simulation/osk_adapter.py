"""OSK Adapter - Interface to the Object-oriented Simulation Kernel.

This module provides the bridge between LibreSim's compiled model and OSK's
simulation engine. It creates OSK block instances and manages simulation execution.
"""

from typing import Dict, Any, List, Type

from ..models.simulation import SimulationConfig, SolverType
from .compiler import CompiledModel, CompiledBlock

# Import OSK components
from ..osk import Block, State, Sim
from ..osk.blocks import (
    # Sources
    Constant, Step, Ramp, SineWave, Clock,
    # Sinks
    Scope, ToWorkspace,
    # Continuous
    Integrator, Derivative, TransferFunction, StateSpace, PIDController,
    # Discrete
    UnitDelay, ZeroOrderHold,
    # Math
    Sum, Gain, Product, Abs, Saturation,
    # Subsystems
    Inport, Outport, Subsystem,
    # Signal Processing
    RateLimiter, MovingAverage, LowPassFilter, HighPassFilter, BandPassFilter, Backlash,
    # Nonlinear
    LookupTable1D, LookupTable2D, Quantizer, Relay, Coulomb, VariableTransportDelay,
    # Observers
    LuenbergerObserver, KalmanFilter, ExtendedKalmanFilter,
)
from ..osk.blocks.math_ops import Switch, MathFunction, Trigonometry, DeadZone, Sign
from ..osk.blocks.sinks import Display, Terminator
from ..osk.blocks.sources import PulseGenerator
from ..osk.blocks.discrete import DiscreteIntegrator, DiscreteDerivative, DiscreteTransferFunction


# Mapping from LibreSim block types to OSK block classes
BLOCK_TYPE_MAP: Dict[str, Type[Block]] = {
    # Sources
    "constant": Constant,
    "step": Step,
    "ramp": Ramp,
    "sine_wave": SineWave,
    "pulse_generator": PulseGenerator,
    "clock": Clock,
    # Sinks
    "scope": Scope,
    "display": Display,
    "to_workspace": ToWorkspace,
    "terminator": Terminator,
    # Continuous
    "integrator": Integrator,
    "derivative": Derivative,
    "transfer_function": TransferFunction,
    "state_space": StateSpace,
    "pid_controller": PIDController,
    # Discrete
    "unit_delay": UnitDelay,
    "zero_order_hold": ZeroOrderHold,
    "discrete_integrator": DiscreteIntegrator,
    "discrete_derivative": DiscreteDerivative,
    "discrete_transfer_function": DiscreteTransferFunction,
    # Math
    "sum": Sum,
    "gain": Gain,
    "product": Product,
    "abs": Abs,
    "sign": Sign,
    "saturation": Saturation,
    "dead_zone": DeadZone,
    "math_function": MathFunction,
    "trigonometry": Trigonometry,
    "switch": Switch,
    # Subsystems
    "inport": Inport,
    "outport": Outport,
    "subsystem": Subsystem,
    # Signal Processing
    "rate_limiter": RateLimiter,
    "moving_average": MovingAverage,
    "low_pass_filter": LowPassFilter,
    "high_pass_filter": HighPassFilter,
    "band_pass_filter": BandPassFilter,
    "backlash": Backlash,
    # Nonlinear
    "lookup_table_1d": LookupTable1D,
    "lookup_table_2d": LookupTable2D,
    "quantizer": Quantizer,
    "relay": Relay,
    "coulomb_friction": Coulomb,
    "variable_transport_delay": VariableTransportDelay,
    # Observers
    "luenberger_observer": LuenbergerObserver,
    "kalman_filter": KalmanFilter,
    "extended_kalman_filter": ExtendedKalmanFilter,
}

# Parameter name mapping from LibreSim to OSK constructor arguments
PARAM_MAP: Dict[str, Dict[str, str]] = {
    "constant": {"value": "value"},
    "step": {"stepTime": "step_time", "initialValue": "initial_value", "finalValue": "final_value"},
    "ramp": {"slope": "slope", "startTime": "start_time", "initialOutput": "initial_output"},
    "sine_wave": {"amplitude": "amplitude", "frequency": "frequency", "phase": "phase", "bias": "bias"},
    "pulse_generator": {"amplitude": "amplitude", "period": "period", "dutyCycle": "duty_cycle", "phaseDelay": "phase_delay"},
    "scope": {"numInputs": "num_inputs"},
    "to_workspace": {"variableName": "variable_name"},
    "integrator": {"initialCondition": "initial_condition", "limitOutput": "limit_output", "upperLimit": "upper_limit", "lowerLimit": "lower_limit"},
    "derivative": {"coefficient": "coefficient"},
    "transfer_function": {"numerator": "numerator", "denominator": "denominator"},
    "state_space": {"A": "A", "B": "B", "C": "C", "D": "D", "initialCondition": "initial_state"},
    "pid_controller": {"Kp": "Kp", "Ki": "Ki", "Kd": "Kd", "N": "N", "initialConditionI": "initial_integrator"},
    "unit_delay": {"initialCondition": "initial_condition", "sampleTime": "sample_time"},
    "zero_order_hold": {"sampleTime": "sample_time"},
    "discrete_integrator": {"method": "method", "sampleTime": "sample_time", "initialCondition": "initial_condition"},
    "discrete_derivative": {"sampleTime": "sample_time", "initialCondition": "initial_condition"},
    "discrete_transfer_function": {"numerator": "numerator", "denominator": "denominator", "sampleTime": "sample_time"},
    "sum": {"signs": "signs"},
    "gain": {"gain": "gain"},
    "product": {"operations": "operations"},
    "saturation": {"upperLimit": "upper_limit", "lowerLimit": "lower_limit"},
    "dead_zone": {"start": "start", "end": "end"},
    "math_function": {"function": "function", "exponent": "exponent"},
    "trigonometry": {"function": "function"},
    "switch": {"threshold": "threshold", "criteria": "criteria"},
    # Subsystems
    "inport": {"portNumber": "port_number"},
    "outport": {"portNumber": "port_number"},
    "subsystem": {"numInputs": "num_inputs", "numOutputs": "num_outputs"},
    # Signal Processing
    "rate_limiter": {"risingLimit": "rising_limit", "fallingLimit": "falling_limit"},
    "moving_average": {"windowSize": "window_size"},
    "low_pass_filter": {"cutoffFrequency": "cutoff_freq"},
    "high_pass_filter": {"cutoffFrequency": "cutoff_freq"},
    "band_pass_filter": {"lowCutoff": "low_cutoff", "highCutoff": "high_cutoff"},
    "backlash": {"deadbandWidth": "deadband_width", "initialOutput": "initial_output"},
    # Nonlinear
    "lookup_table_1d": {"xData": "x_data", "yData": "y_data"},
    "lookup_table_2d": {"xData": "x_data", "yData": "y_data", "zData": "z_data"},
    "quantizer": {"interval": "interval"},
    "relay": {"switchOn": "switch_on", "switchOff": "switch_off", "outputOn": "output_on", "outputOff": "output_off"},
    "coulomb_friction": {"staticGain": "static_gain", "dynamicGain": "dynamic_gain", "velocityThreshold": "velocity_threshold"},
    "variable_transport_delay": {"maxDelay": "max_delay", "initialDelay": "initial_delay"},
    # Observers
    "luenberger_observer": {"A": "A", "B": "B", "C": "C", "L": "L", "initialState": "initial_state"},
    "kalman_filter": {"A": "A", "B": "B", "C": "C", "Q": "Q", "R": "R", "initialState": "initial_state", "initialP": "initial_P"},
    "extended_kalman_filter": {"nStates": "n_states", "Q": "Q", "R": "R", "initialState": "initial_state"},
}


class OSKAdapter:
    """Adapter for the Object-oriented Simulation Kernel.

    Creates OSK block instances from compiled LibreSim models and
    manages simulation execution using OSK's Sim class.
    """

    def __init__(self):
        self._compiled_model: CompiledModel | None = None
        self._config: SimulationConfig | None = None
        self._osk_blocks: Dict[str, Block] = {}
        self._block_map: Dict[str, CompiledBlock] = {}
        self._sink_blocks: List[str] = []
        # Track source block names for each scope input: scope_id -> [source_name, ...]
        self._scope_input_names: Dict[str, List[str]] = {}

    def initialize(self, compiled_model: CompiledModel, config: SimulationConfig):
        """Initialize the simulation with a compiled model.

        Args:
            compiled_model: The compiled model from ModelCompiler
            config: Simulation configuration (solver, step size, etc.)
        """
        self._compiled_model = compiled_model
        self._config = config
        self._osk_blocks = {}
        self._block_map = {}
        self._sink_blocks = []
        self._scope_input_names = {}

        # Set the integration method
        solver_method = self._get_solver_method(config.solver)
        State.method = solver_method

        # Create OSK block instances
        for block in compiled_model.blocks:
            self._create_osk_block(block)
            self._block_map[block.id] = block

        # Set up connections between blocks
        self._setup_connections()

    def _get_solver_method(self, solver: SolverType) -> str:
        """Convert SolverType to OSK method name."""
        return {
            SolverType.EULER: "Euler",
            SolverType.RK4: "RK4",
            SolverType.MERSON: "Merson",
        }.get(solver, "RK4")

    def _create_osk_block(self, compiled_block: CompiledBlock):
        """Create an OSK block instance from a compiled block."""
        block_type = compiled_block.type
        block_class = BLOCK_TYPE_MAP.get(block_type)

        if not block_class:
            # Unknown block type, create a pass-through block
            print(f"Warning: Unknown block type '{block_type}', using pass-through")
            self._osk_blocks[compiled_block.id] = Gain(gain=1.0)
            return

        # Map parameters
        osk_params = self._map_parameters(block_type, compiled_block.parameters)

        # Create the block instance
        try:
            osk_block = block_class(**osk_params)
            self._osk_blocks[compiled_block.id] = osk_block

            # Track sink blocks for output recording
            if block_type in ["scope", "display", "to_workspace"]:
                self._sink_blocks.append(compiled_block.id)

        except Exception as e:
            print(f"Error creating block '{compiled_block.name}': {e}")
            # Create a default block as fallback
            self._osk_blocks[compiled_block.id] = Gain(gain=1.0)

    def _map_parameters(self, block_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Map LibreSim parameter names to OSK constructor arguments."""
        param_mapping = PARAM_MAP.get(block_type, {})
        osk_params = {}

        for libresim_name, value in params.items():
            osk_name = param_mapping.get(libresim_name, libresim_name)
            osk_params[osk_name] = value

        return osk_params

    def _setup_connections(self):
        """Set up connections between OSK blocks."""
        if not self._compiled_model:
            return

        for block in self._compiled_model.blocks:
            osk_block = self._osk_blocks.get(block.id)
            if not osk_block:
                continue

            # For scope blocks, track the source block names for each input
            if block.type == "scope":
                num_inputs = len(block.input_connections)
                self._scope_input_names[block.id] = [""] * num_inputs

            # Connect inputs
            for i, conn in enumerate(block.input_connections):
                source_block_id, source_port = conn.split(":")
                source_osk_block = self._osk_blocks.get(source_block_id)
                source_compiled_block = self._block_map.get(source_block_id)

                if source_osk_block:
                    # Use connectInput if available, otherwise we'll handle in step()
                    if hasattr(osk_block, 'connectInput'):
                        osk_block.connectInput(source_osk_block, i)
                    elif hasattr(osk_block, 'input_block'):
                        osk_block.input_block = source_osk_block
                    elif hasattr(osk_block, 'input_blocks'):
                        if i < len(osk_block.input_blocks):
                            osk_block.input_blocks[i] = source_osk_block

                # Track source name for scope inputs
                if block.type == "scope" and source_compiled_block:
                    self._scope_input_names[block.id][i] = source_compiled_block.name

    def step(self, t: float, dt: float) -> Dict[str, float]:
        """Execute one simulation step.

        This method manually steps through the simulation, updating
        the OSK State class timing and calling block methods.

        Args:
            t: Current simulation time
            dt: Time step size

        Returns:
            Dictionary of outputs from sink blocks (for recording)
        """
        if not self._compiled_model:
            return {}

        # Set OSK timing
        State.t = t
        State.dt = dt
        State.dtp = dt
        State.ready = 1

        recorded_outputs: Dict[str, float] = {}

        # Execute blocks in topological order
        for block_id in self._compiled_model.execution_order:
            osk_block = self._osk_blocks.get(block_id)
            compiled_block = self._block_map.get(block_id)

            if not osk_block or not compiled_block:
                continue

            # For blocks without automatic input connection, set inputs manually
            if not hasattr(osk_block, 'input_block') or osk_block.input_block is None:
                for i, conn in enumerate(compiled_block.input_connections):
                    source_block_id, _ = conn.split(":")
                    source_block = self._osk_blocks.get(source_block_id)
                    if source_block:
                        value = source_block.getOutput()
                        osk_block.setInput(value, i)

            # Update block (computes derivatives)
            osk_block.update()

            # Record sink block outputs
            if block_id in self._sink_blocks:
                # For scopes with multiple inputs, record each input separately
                if block_id in self._scope_input_names and hasattr(osk_block, 'inputs'):
                    input_names = self._scope_input_names[block_id]
                    for i, (value, name) in enumerate(zip(osk_block.inputs, input_names)):
                        # Use source block name as the signal name
                        signal_name = name if name else f"Input {i+1}"
                        key = f"{block_id}:{i}:{signal_name}"
                        if isinstance(value, (int, float)):
                            recorded_outputs[key] = float(value)
                else:
                    # Single-input sink block
                    output = osk_block.getOutput()
                    compiled_block = self._block_map.get(block_id)
                    key = f"{block_id}:out:{compiled_block.name if compiled_block else block_id}"
                    if isinstance(output, (int, float)):
                        recorded_outputs[key] = float(output)

            # Report (for data recording in sink blocks)
            if State.ready:
                osk_block.rpt()

        # Propagate states for all blocks
        for osk_block in self._osk_blocks.values():
            osk_block.propagateStates()

        return recorded_outputs

    def run_simulation(self) -> Dict[str, Any]:
        """Run a complete simulation using OSK's Sim class.

        This is an alternative to using step() repeatedly,
        using OSK's native simulation loop.

        Returns:
            Simulation results with signals and statistics
        """
        if not self._compiled_model or not self._config:
            return {"signals": [], "statistics": {}}

        # Create stage with all blocks in execution order
        stage = [
            self._osk_blocks[bid]
            for bid in self._compiled_model.execution_order
            if bid in self._osk_blocks
        ]

        # Create and run simulation
        sim = Sim(
            dts=[self._config.step_size],
            tmax=self._config.stop_time,
            vStage=[stage]
        )

        results = sim.run()

        # Collect results from sink blocks
        signals = []
        for block_id in self._sink_blocks:
            osk_block = self._osk_blocks.get(block_id)
            if osk_block and hasattr(osk_block, 'getData'):
                data = osk_block.getData()
                signals.append({
                    "blockId": block_id,
                    "portId": "out",
                    "name": data.get("name", block_id),
                    "times": data.get("times", []),
                    "values": data.get("values", []) if "values" in data else data.get("values", [[]])[0]
                })

        return {
            "signals": signals,
            "statistics": {
                "totalSteps": len(results.get("times", [])),
                "executionTime": 0,  # Would need to measure
                "finalTime": results.get("times", [0])[-1] if results.get("times") else 0
            }
        }

    def get_solver(self, solver_type: SolverType) -> str:
        """Get OSK solver method name.

        Args:
            solver_type: The solver type enum

        Returns:
            OSK solver method name string
        """
        return self._get_solver_method(solver_type)

    def get_block(self, block_id: str) -> Block | None:
        """Get an OSK block instance by ID.

        Args:
            block_id: The block ID

        Returns:
            The OSK block instance or None
        """
        return self._osk_blocks.get(block_id)

    def get_all_blocks(self) -> Dict[str, Block]:
        """Get all OSK block instances.

        Returns:
            Dictionary mapping block IDs to OSK block instances
        """
        return self._osk_blocks.copy()
