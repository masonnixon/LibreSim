"""OSK Adapter - Interface to the Object-oriented Simulation Kernel.

This module provides the bridge between LibreSim's block model and OSK's
simulation engine. It translates compiled blocks to OSK objects and
manages the simulation execution.

TODO: Replace stub implementations with actual OSK integration once
the OSK code is available.
"""

import math
from typing import Dict, Any, List, Callable
from dataclasses import dataclass

from ..models.simulation import SimulationConfig, SolverType
from .compiler import CompiledModel, CompiledBlock


@dataclass
class BlockState:
    """Runtime state for a block."""

    outputs: Dict[str, float]
    state: Dict[str, float]  # For stateful blocks like integrators


class OSKAdapter:
    """Adapter for the Object-oriented Simulation Kernel.

    This class wraps OSK functionality and provides a clean interface
    for the simulation runner. Currently contains stub implementations
    that will be replaced with actual OSK calls.
    """

    def __init__(self):
        self._compiled_model: CompiledModel | None = None
        self._config: SimulationConfig | None = None
        self._block_states: Dict[str, BlockState] = {}
        self._block_functions: Dict[str, Callable] = {}

    def initialize(self, compiled_model: CompiledModel, config: SimulationConfig):
        """Initialize the simulation with a compiled model.

        Args:
            compiled_model: The compiled model from ModelCompiler
            config: Simulation configuration (solver, step size, etc.)
        """
        self._compiled_model = compiled_model
        self._config = config
        self._block_states = {}

        # Initialize each block
        for block in compiled_model.blocks:
            self._initialize_block(block)

    def _initialize_block(self, block: CompiledBlock):
        """Initialize a single block's state and function."""
        # Initialize state
        state = BlockState(outputs={}, state={})

        # Set up initial conditions based on block type
        if block.type == "integrator":
            state.state["integral"] = block.parameters.get("initialCondition", 0.0)
        elif block.type == "derivative":
            state.state["prev_input"] = 0.0
            state.state["prev_time"] = 0.0
        elif block.type == "pid_controller":
            state.state["integral"] = block.parameters.get("initialConditionI", 0.0)
            state.state["prev_error"] = 0.0
        elif block.type == "unit_delay":
            state.state["prev_value"] = block.parameters.get("initialCondition", 0.0)
        elif block.type == "transfer_function":
            # Initialize state vector for transfer function
            num = block.parameters.get("numerator", [1])
            den = block.parameters.get("denominator", [1, 1])
            order = len(den) - 1
            state.state["x"] = [0.0] * order

        self._block_states[block.id] = state
        self._block_functions[block.id] = self._get_block_function(block)

    def _get_block_function(self, block: CompiledBlock) -> Callable:
        """Get the computation function for a block type."""
        block_type = block.type
        params = block.parameters

        # Source blocks
        if block_type == "constant":
            value = params.get("value", 1.0)
            return lambda t, inputs, state: {"out": value}

        elif block_type == "step":
            step_time = params.get("stepTime", 1.0)
            initial = params.get("initialValue", 0.0)
            final = params.get("finalValue", 1.0)
            return lambda t, inputs, state: {"out": final if t >= step_time else initial}

        elif block_type == "ramp":
            slope = params.get("slope", 1.0)
            start_time = params.get("startTime", 0.0)
            initial = params.get("initialOutput", 0.0)
            return lambda t, inputs, state: {
                "out": initial + slope * (t - start_time) if t >= start_time else initial
            }

        elif block_type == "sine_wave":
            amp = params.get("amplitude", 1.0)
            freq = params.get("frequency", 1.0)
            phase = params.get("phase", 0.0)
            bias = params.get("bias", 0.0)
            return lambda t, inputs, state: {
                "out": amp * math.sin(2 * math.pi * freq * t + phase) + bias
            }

        elif block_type == "clock":
            return lambda t, inputs, state: {"out": t}

        # Math blocks
        elif block_type == "gain":
            gain = params.get("gain", 1.0)
            return lambda t, inputs, state: {"out": gain * inputs.get("in", 0.0)}

        elif block_type == "sum":
            signs = params.get("signs", "++")
            def sum_func(t, inputs, state):
                result = 0.0
                for i, sign in enumerate(signs):
                    input_key = f"in{i+1}" if i > 0 else "in1"
                    val = inputs.get(input_key, 0.0)
                    result += val if sign == "+" else -val
                return {"out": result}
            return sum_func

        elif block_type == "product":
            ops = params.get("operations", "**")
            def product_func(t, inputs, state):
                result = 1.0
                for i, op in enumerate(ops):
                    input_key = f"in{i+1}"
                    val = inputs.get(input_key, 1.0)
                    if op == "*":
                        result *= val
                    else:
                        result /= val if val != 0 else 1e-10
                return {"out": result}
            return product_func

        elif block_type == "abs":
            return lambda t, inputs, state: {"out": abs(inputs.get("in", 0.0))}

        elif block_type == "saturation":
            upper = params.get("upperLimit", 1.0)
            lower = params.get("lowerLimit", -1.0)
            return lambda t, inputs, state: {
                "out": max(lower, min(upper, inputs.get("in", 0.0)))
            }

        # Continuous blocks
        elif block_type == "integrator":
            def integrator_func(t, inputs, state):
                # Simple forward Euler integration
                dt = self._config.step_size if self._config else 0.01
                state["integral"] += inputs.get("in", 0.0) * dt
                return {"out": state["integral"]}
            return integrator_func

        elif block_type == "derivative":
            def derivative_func(t, inputs, state):
                current_input = inputs.get("in", 0.0)
                dt = t - state.get("prev_time", 0.0)
                if dt > 0:
                    deriv = (current_input - state.get("prev_input", 0.0)) / dt
                else:
                    deriv = 0.0
                state["prev_input"] = current_input
                state["prev_time"] = t
                return {"out": deriv}
            return derivative_func

        elif block_type == "pid_controller":
            kp = params.get("Kp", 1.0)
            ki = params.get("Ki", 0.0)
            kd = params.get("Kd", 0.0)
            n = params.get("N", 100.0)

            def pid_func(t, inputs, state):
                error = inputs.get("in", 0.0)
                dt = self._config.step_size if self._config else 0.01

                # Proportional
                p_term = kp * error

                # Integral
                state["integral"] += error * dt
                i_term = ki * state["integral"]

                # Derivative (with filter)
                d_error = (error - state.get("prev_error", 0.0)) / dt if dt > 0 else 0.0
                d_term = kd * d_error

                state["prev_error"] = error
                return {"out": p_term + i_term + d_term}
            return pid_func

        elif block_type == "transfer_function":
            num = params.get("numerator", [1])
            den = params.get("denominator", [1, 1])

            def tf_func(t, inputs, state):
                # Simple first-order approximation for demo
                # TODO: Implement proper state-space realization
                u = inputs.get("in", 0.0)
                dt = self._config.step_size if self._config else 0.01

                if len(den) == 2:
                    # First order: num[0] / (den[0]*s + den[1])
                    # y' = (-den[1]/den[0])*y + (num[0]/den[0])*u
                    a = -den[1] / den[0] if den[0] != 0 else 0
                    b = num[0] / den[0] if den[0] != 0 else 0
                    y = state.get("x", [0.0])[0]
                    y_new = y + dt * (a * y + b * u)
                    state["x"] = [y_new]
                    return {"out": y_new}
                else:
                    # Higher order - simplified
                    return {"out": num[0] * u / den[0] if den[0] != 0 else 0}
            return tf_func

        # Discrete blocks
        elif block_type == "unit_delay":
            def delay_func(t, inputs, state):
                output = state.get("prev_value", 0.0)
                state["prev_value"] = inputs.get("in", 0.0)
                return {"out": output}
            return delay_func

        elif block_type == "zero_order_hold":
            sample_time = params.get("sampleTime", 0.1)
            def zoh_func(t, inputs, state):
                if "last_sample_time" not in state:
                    state["last_sample_time"] = 0.0
                    state["held_value"] = inputs.get("in", 0.0)

                if t - state["last_sample_time"] >= sample_time:
                    state["held_value"] = inputs.get("in", 0.0)
                    state["last_sample_time"] = t

                return {"out": state["held_value"]}
            return zoh_func

        # Sink blocks (just pass through for recording)
        elif block_type in ["scope", "display", "to_workspace", "terminator"]:
            return lambda t, inputs, state: {"out": inputs.get("in", 0.0)}

        # Routing blocks
        elif block_type == "mux":
            num_inputs = params.get("numInputs", 2)
            def mux_func(t, inputs, state):
                values = [inputs.get(f"in{i+1}", 0.0) for i in range(num_inputs)]
                return {"out": values}
            return mux_func

        elif block_type == "switch":
            threshold = params.get("threshold", 0.0)
            def switch_func(t, inputs, state):
                control = inputs.get("control", 0.0)
                if control >= threshold:
                    return {"out": inputs.get("in1", 0.0)}
                else:
                    return {"out": inputs.get("in2", 0.0)}
            return switch_func

        # Default: pass-through
        return lambda t, inputs, state: {"out": inputs.get("in", 0.0)}

    def step(self, t: float, dt: float) -> Dict[str, float]:
        """Execute one simulation step.

        Args:
            t: Current simulation time
            dt: Time step size

        Returns:
            Dictionary of outputs from sink blocks (for recording)
        """
        if not self._compiled_model:
            return {}

        # Dictionary to hold all block outputs for this step
        all_outputs: Dict[str, Dict[str, float]] = {}
        recorded_outputs: Dict[str, float] = {}

        # Execute blocks in order
        for block_id in self._compiled_model.execution_order:
            block = next(
                (b for b in self._compiled_model.blocks if b.id == block_id), None
            )
            if not block:
                continue

            # Gather inputs from connected blocks
            inputs = {}
            state = self._block_states[block_id]

            for i, conn in enumerate(block.input_connections):
                source_block_id, source_port = conn.split(":")
                if source_block_id in all_outputs:
                    # Map source output to input name
                    input_name = f"in{i+1}" if i > 0 else "in" if len(block.input_connections) == 1 else f"in{i+1}"
                    source_output = all_outputs[source_block_id].get("out", 0.0)
                    inputs[input_name] = source_output

            # Execute block function
            func = self._block_functions.get(block_id)
            if func:
                outputs = func(t, inputs, state.state)
                all_outputs[block_id] = outputs
                state.outputs = outputs

                # Record sink block outputs
                if block.type in ["scope", "display", "to_workspace"]:
                    for port_name, value in outputs.items():
                        key = f"{block_id}:{port_name}"
                        if isinstance(value, (int, float)):
                            recorded_outputs[key] = float(value)

        return recorded_outputs

    def get_solver(self, solver_type: SolverType):
        """Get an OSK solver instance.

        TODO: Return actual OSK solver objects when integrated.
        """
        # Placeholder for OSK solver integration
        return {
            SolverType.EULER: "EulerSolver",
            SolverType.RK4: "RK4Solver",
            SolverType.MERSON: "MersonSolver",
        }.get(solver_type, "RK4Solver")
