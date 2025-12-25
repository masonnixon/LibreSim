"""OSK Adapter - Interface to the Object-oriented Simulation Kernel.

This module provides the bridge between LibreSim's compiled model and OSK's
simulation engine. It creates OSK block instances and manages simulation execution.
"""

from typing import Any

from ..models.simulation import SimulationConfig, SolverType

# Import OSK components
from ..osk import Block, Sim, State
from ..osk.blocks import (
    Abs,
    AnalogFilter,
    Backlash,
    BandPassFilter,
    # Control Analysis
    BodePlot,
    Clock,
    # Sources
    Constant,
    Coulomb,
    Derivative,
    ExtendedKalmanFilter,
    Gain,
    HighPassFilter,
    # Subsystems
    Inport,
    # Continuous
    Integrator,
    KalmanFilter,
    # Nonlinear
    LookupTable1D,
    LookupTable2D,
    LowPassFilter,
    # Observers
    LuenbergerObserver,
    MovingAverage,
    NotchFilter,
    NyquistPlot,
    Outport,
    PIDController,
    PoleZeroMap,
    Product,
    Quantizer,
    Ramp,
    # Signal Processing
    RateLimiter,
    Relay,
    Saturation,
    # Sinks
    Scope,
    SineWave,
    StateSpace,
    Step,
    StepInfo,
    Subsystem,
    # Math
    Sum,
    ToWorkspace,
    TransferFunction,
    # Discrete
    UnitDelay,
    VariableTransportDelay,
    ZeroOrderHold,
)
from ..osk.blocks.discrete import DiscreteDerivative, DiscreteIntegrator, DiscreteTransferFunction
from ..osk.blocks.math_ops import (
    DeadZone,
    Demux,
    MathFunction,
    Mux,
    Reshape,
    Sign,
    Switch,
    Trigonometry,
)
from ..osk.blocks.sinks import Display, Terminator
from ..osk.blocks.sources import PulseGenerator, UniformNoise, WhiteNoise
from .compiler import CompiledBlock, CompiledModel

# Mapping from LibreSim block types to OSK block classes
BLOCK_TYPE_MAP: dict[str, type[Block]] = {
    # Sources
    "constant": Constant,
    "step": Step,
    "ramp": Ramp,
    "sine_wave": SineWave,
    "pulse_generator": PulseGenerator,
    "clock": Clock,
    "white_noise": WhiteNoise,
    "uniform_noise": UniformNoise,
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
    "mux": Mux,
    "demux": Demux,
    "reshape": Reshape,
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
    "analog_filter": AnalogFilter,
    "notch_filter": NotchFilter,
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
    # Control Analysis
    "bode_plot": BodePlot,
    "nyquist_plot": NyquistPlot,
    "pole_zero_map": PoleZeroMap,
    "step_info": StepInfo,
}

# Parameter name mapping from LibreSim to OSK constructor arguments
PARAM_MAP: dict[str, dict[str, str]] = {
    "constant": {"value": "value"},
    "step": {"stepTime": "step_time", "initialValue": "initial_value", "finalValue": "final_value"},
    "ramp": {"slope": "slope", "startTime": "start_time", "initialOutput": "initial_output"},
    "sine_wave": {"amplitude": "amplitude", "frequency": "frequency", "phase": "phase", "bias": "bias"},
    "pulse_generator": {"amplitude": "amplitude", "period": "period", "dutyCycle": "duty_cycle", "phaseDelay": "phase_delay"},
    "white_noise": {"mean": "mean", "variance": "variance", "seed": "seed", "sampleTime": "sample_time"},
    "uniform_noise": {"minimum": "minimum", "maximum": "maximum", "seed": "seed", "sampleTime": "sample_time"},
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
    "mux": {"numInputs": "num_inputs"},
    "demux": {"numOutputs": "num_outputs"},
    "reshape": {"outputDimensions": "output_dimensions"},
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
    "analog_filter": {
        "design": "design", "response": "response", "order": "order",
        "cutoffFrequency": "cutoff_freq", "lowCutoff": "low_cutoff", "highCutoff": "high_cutoff",
        "passbandRipple": "passband_ripple", "stopbandAtten": "stopband_atten"
    },
    "notch_filter": {"notchFrequency": "notch_freq", "bandwidth": "bandwidth", "depth": "depth"},
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
    # Control Analysis
    "bode_plot": {"numerator": "numerator", "denominator": "denominator", "minFrequency": "minFrequency", "maxFrequency": "maxFrequency", "numPoints": "numPoints"},
    "nyquist_plot": {"numerator": "numerator", "denominator": "denominator", "minFrequency": "minFrequency", "maxFrequency": "maxFrequency", "numPoints": "numPoints"},
    "pole_zero_map": {"numerator": "numerator", "denominator": "denominator"},
    "step_info": {"numerator": "numerator", "denominator": "denominator", "simulationTime": "simulationTime", "numPoints": "numPoints", "settlingPercent": "settlingPercent"},
}


class OSKAdapter:
    """Adapter for the Object-oriented Simulation Kernel.

    Creates OSK block instances from compiled LibreSim models and
    manages simulation execution using OSK's Sim class.
    """

    def __init__(self):
        self._compiled_model: CompiledModel | None = None
        self._config: SimulationConfig | None = None
        self._osk_blocks: dict[str, Block] = {}
        self._block_map: dict[str, CompiledBlock] = {}
        self._sink_blocks: list[str] = []
        # Track source block names for each scope input: scope_id -> [source_name, ...]
        self._scope_input_names: dict[str, list[str]] = {}

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

    def _map_parameters(self, block_type: str, params: dict[str, Any]) -> dict[str, Any]:
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
                # Get the actual number of inputs from the block parameters
                num_inputs = int(block.parameters.get('numInputs', 1))
                self._scope_input_names[block.id] = [""] * num_inputs

            # Connect inputs
            # Connection format: "source_block_id:source_port_id@target_port_id"
            for conn in block.input_connections:
                # Parse the connection string to get source and target port info
                if "@" in conn:
                    source_part, target_port_id = conn.split("@")
                    source_block_id, source_port = source_part.split(":")
                else:
                    # Fallback for old format without target port
                    source_block_id, source_port = conn.split(":")
                    target_port_id = None

                source_osk_block = self._osk_blocks.get(source_block_id)
                source_compiled_block = self._block_map.get(source_block_id)

                # Extract the port index from target_port_id
                # Handles formats like:
                #   "block-in-0", "block-in-1" (numeric suffix, 0-indexed)
                #   "sum1-in1", "sum1-in2" (named suffix like in1/in2, 1-indexed)
                target_port_index = 0
                if target_port_id:
                    # Parse port index from ID
                    parts = target_port_id.rsplit("-", 1)
                    if len(parts) == 2:
                        suffix = parts[1]
                        if suffix.isdigit():
                            # Pure numeric: "block-in-0" -> index 0
                            target_port_index = int(suffix)
                        elif suffix.startswith("in") and suffix[2:].isdigit():
                            # Named format: "sum1-in1" -> index 0, "sum1-in2" -> index 1
                            target_port_index = int(suffix[2:]) - 1
                        elif suffix.startswith("out") and suffix[3:].isdigit():
                            # Output format: "block-out1" -> index 0
                            target_port_index = int(suffix[3:]) - 1

                # Extract the source port index from source_port
                # Handles formats like:
                #   "demux1-out2" (block-out# format, 1-indexed)
                #   "block-out-0" (block-out-# format, 0-indexed)
                #   "out1", "out2" (simple format, 1-indexed)
                source_port_index = 0
                if source_port:
                    # Parse the port suffix from the source_port ID
                    parts = source_port.rsplit("-", 1)
                    if len(parts) == 2:
                        suffix = parts[1]
                        if suffix.isdigit():
                            # Format: "block-out-0" -> index 0
                            source_port_index = int(suffix)
                        elif suffix.startswith("out") and suffix[3:].isdigit():
                            # Format: "demux1-out2" -> index 1
                            source_port_index = int(suffix[3:]) - 1
                    elif source_port.startswith("out") and source_port[3:].isdigit():
                        # Format: "out1", "out2" (1-indexed)
                        source_port_index = int(source_port[3:]) - 1

                if source_osk_block:
                    # Use connectInput if available, otherwise we'll handle in step()
                    if hasattr(osk_block, 'connectInput'):
                        # For Scope blocks, pass the source port index
                        if block.type == "scope":
                            osk_block.connectInput(source_osk_block, target_port_index, source_port_index)
                        else:
                            osk_block.connectInput(source_osk_block, target_port_index)
                    elif hasattr(osk_block, 'input_block'):
                        osk_block.input_block = source_osk_block
                    elif hasattr(osk_block, 'input_blocks'):
                        if target_port_index < len(osk_block.input_blocks):
                            osk_block.input_blocks[target_port_index] = source_osk_block

                # Track source name for scope inputs and set on the scope block
                if block.type == "scope" and source_compiled_block:
                    if target_port_index < len(self._scope_input_names[block.id]):
                        self._scope_input_names[block.id][target_port_index] = source_compiled_block.name
                    # Also set the input name on the scope block itself for legend display
                    if hasattr(osk_block, 'setInputName'):
                        osk_block.setInputName(source_compiled_block.name, target_port_index)

    def step(self, t: float, dt: float) -> dict[str, float]:
        """Execute one simulation step.

        This method manually steps through the simulation, updating
        the OSK State class timing and calling block methods.

        For multi-pass integration methods (RK4, RK2, Merson), this runs
        all required passes to complete one time step.

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
        State.kpass = 0
        State.ready = 1

        # Number of passes for each integration method
        passes = {'Euler': 1, 'RK2': 2, 'RK4': 4, 'Merson': 5}
        num_passes = passes.get(State.method, 1)

        recorded_outputs: dict[str, float] = {}

        # Execute all integration passes for this time step
        for kpass in range(num_passes):
            State.kpass = kpass
            # ready is 1 only on the final pass
            State.ready = 1 if kpass == num_passes - 1 else 0

            # Execute blocks in topological order
            for block_id in self._compiled_model.execution_order:
                osk_block = self._osk_blocks.get(block_id)
                compiled_block = self._block_map.get(block_id)

                if not osk_block or not compiled_block:
                    continue

                # For blocks without automatic input connection, set inputs manually
                # Skip blocks that have input_blocks (like Scope) - they get inputs via connectInput
                has_input_block = hasattr(osk_block, 'input_block') and osk_block.input_block is not None
                has_input_blocks = hasattr(osk_block, 'input_blocks') and any(b is not None for b in osk_block.input_blocks)
                if not has_input_block and not has_input_blocks:
                    for i, conn in enumerate(compiled_block.input_connections):
                        source_block_id, _ = conn.split(":")
                        source_block = self._osk_blocks.get(source_block_id)
                        if source_block:
                            value = source_block.getOutput()
                            osk_block.setInput(value, i)

                # Update block (computes derivatives)
                osk_block.update()

                # Only record outputs and report on final pass
                if State.ready:
                    # Record sink block outputs
                    if block_id in self._sink_blocks:
                        # For scopes with multiple inputs or vector inputs, record each trace separately
                        # Only record CONNECTED inputs (where input_blocks[i] is not None)
                        if block_id in self._scope_input_names and hasattr(osk_block, 'inputs'):
                            input_names = self._scope_input_names[block_id]
                            input_blocks = getattr(osk_block, 'input_blocks', [])
                            trace_idx = 0
                            for i in range(len(osk_block.inputs)):
                                # Skip unconnected inputs
                                if i < len(input_blocks) and input_blocks[i] is None:
                                    continue

                                base_name = input_names[i] if i < len(input_names) else f"Input {i+1}"
                                # Check if this input is a vector (from Mux)
                                if hasattr(osk_block, '_vector_inputs') and i in osk_block._vector_inputs:
                                    vec = osk_block._vector_inputs[i]
                                    for j, val in enumerate(vec):
                                        signal_name = f"{base_name}[{j+1}]"
                                        key = f"{block_id}:{trace_idx}:{signal_name}"
                                        if isinstance(val, (int, float)):
                                            recorded_outputs[key] = float(val)
                                        trace_idx += 1
                                else:
                                    # Scalar input
                                    value = osk_block.inputs[i] if i < len(osk_block.inputs) else 0.0
                                    key = f"{block_id}:{trace_idx}:{base_name}"
                                    if isinstance(value, (int, float)):
                                        recorded_outputs[key] = float(value)
                                    trace_idx += 1
                        else:
                            # Single-input sink block
                            output = osk_block.getOutput()
                            compiled_block = self._block_map.get(block_id)
                            key = f"{block_id}:out:{compiled_block.name if compiled_block else block_id}"
                            if isinstance(output, (int, float)):
                                recorded_outputs[key] = float(output)

                    # Report (for data recording in sink blocks)
                    osk_block.rpt()

            # Propagate states for all blocks after each pass
            for osk_block in self._osk_blocks.values():
                osk_block.propagateStates()

        # Reset kpass to 0 for next step (avoid polluting global state)
        State.kpass = 0

        return recorded_outputs

    def run_simulation(self) -> dict[str, Any]:
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
                num_inputs = data.get("numInputs", 1)
                input_names = data.get("inputNames", [])
                values = data.get("values", [])
                times = data.get("times", [])

                if num_inputs > 1 and isinstance(values, list) and len(values) == num_inputs:
                    # Multi-input scope: create a signal entry with all traces
                    signals.append({
                        "blockId": block_id,
                        "portId": "out",
                        "name": data.get("name", block_id),
                        "times": times,
                        "values": values,  # List of lists, one per input
                        "inputNames": input_names,
                        "numInputs": num_inputs
                    })
                else:
                    # Single-input scope or backward compatibility
                    signals.append({
                        "blockId": block_id,
                        "portId": "out",
                        "name": data.get("name", block_id),
                        "times": times,
                        "values": values[0] if isinstance(values, list) and len(values) > 0 and isinstance(values[0], list) else values
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

    def get_all_blocks(self) -> dict[str, Block]:
        """Get all OSK block instances.

        Returns:
            Dictionary mapping block IDs to OSK block instances
        """
        return self._osk_blocks.copy()
