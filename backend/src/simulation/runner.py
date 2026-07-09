"""Simulation runner - executes compiled models."""

import asyncio
import time
import uuid
from typing import Any

from ..models.model import Model
from ..models.simulation import (
    SimulationConfig,
    SimulationStatus,
)
from .compiler import ModelCompiler
from .osk_adapter import OSKAdapter


class SimulationRunner:
    """Runs simulations using the OSK backend."""

    def __init__(self, model: Model, config: SimulationConfig):
        self.model = model
        self.config = config
        self.session_id = str(uuid.uuid4())

        self._status = SimulationStatus.IDLE
        self._progress = 0.0
        self._current_time = 0.0
        self._should_stop = False
        self._is_paused = False
        self._error_message: str | None = None
        self._run_started = False
        self._run_finished = asyncio.Event()
        self._run_finished.set()

        self._results: dict[str, list[tuple[float, float]]] = {}
        self._result_decimation: dict[str, int] = {}
        self._start_time: float = 0
        self._execution_time: float = 0
        self._total_steps: int = 0

        # Step mode state
        self._step_mode = False
        self._compiled = None  # Compiled model cache
        self._state_history: list[dict[str, Any]] = []  # For step backward
        self._max_history_size = 1000  # Limit history to prevent memory issues

        # Compile the model
        self._compiler = ModelCompiler()
        self._adapter = OSKAdapter()

    @property
    def status(self) -> SimulationStatus:
        return self._status

    @property
    def progress(self) -> float:
        return self._progress

    @property
    def current_time(self) -> float:
        return self._current_time

    @property
    def error_message(self) -> str | None:
        return self._error_message

    def stop(self):
        """Request simulation stop."""
        self._should_stop = True

    def mark_scheduled(self) -> None:
        """Mark this runner as owning a scheduled background run."""
        self._run_started = True
        self._run_finished.clear()
        self._status = SimulationStatus.COMPILING

    @property
    def has_live_run(self) -> bool:
        return self._run_started and not self._run_finished.is_set()

    async def stop_and_wait(self, timeout: float = 5.0) -> bool:
        """Request stop and wait until the background run has exited."""
        self._should_stop = True
        self._is_paused = False
        if not self.has_live_run:
            return True
        try:
            await asyncio.wait_for(self._run_finished.wait(), timeout=timeout)
        except TimeoutError:
            return False
        return True

    def pause(self):
        """Pause the simulation."""
        self._is_paused = True
        self._status = SimulationStatus.PAUSED

    def resume(self):
        """Resume a paused simulation."""
        self._is_paused = False
        self._status = SimulationStatus.RUNNING

    def enter_step_mode(self) -> bool:
        """Enter step mode from a paused continuous simulation.

        Unlike initialize_step_mode(), this preserves the current simulation state
        and time position instead of reinitializing from the start.
        """
        print(
            f"[enter_step_mode] Entry: _compiled={self._compiled is not None}, _current_time={self._current_time}"
        )

        if self._compiled is None:
            # Not running yet, need to initialize
            print("[enter_step_mode] No compiled model, calling initialize_step_mode()")
            return self.initialize_step_mode()

        try:
            # IMPORTANT: Set should_stop FIRST to ensure the continuous run() loop exits
            # before we clear the paused flag. This prevents the run loop from executing
            # more steps while we're transitioning to step mode.
            self._should_stop = True
            self._step_mode = True
            self._is_paused = False  # Clear paused flag from continuous mode
            self._status = SimulationStatus.PAUSED

            # Save current state as first history entry
            self._state_history = []
            self._save_state()

            print(
                f"[enter_step_mode] Exit: _step_mode={self._step_mode}, _current_time={self._current_time}"
            )
            return True
        except Exception as e:
            import traceback

            self._status = SimulationStatus.ERROR
            self._error_message = str(e)
            print(f"Enter step mode error: {e}")
            traceback.print_exc()
            return False

    def initialize_step_mode(self) -> bool:
        """Initialize simulation for step mode (compile model, ready for stepping)."""
        try:
            # Compile model if not already compiled
            if self._compiled is None:
                self._status = SimulationStatus.COMPILING
                self._compiled = self._compiler.compile(self.model)

                if not self._compiled.success:
                    self._status = SimulationStatus.ERROR
                    self._error_message = self._compiled.message
                    if self._compiled.errors:
                        self._error_message = "; ".join(self._compiled.errors)
                    return False

                # Initialize OSK adapter with compiled model
                self._adapter.initialize(self._compiled, self.config)

            self._step_mode = True
            self._status = SimulationStatus.PAUSED
            self._current_time = self.config.start_time
            self._start_time = time.time()

            # Save initial state
            self._save_state()

            return True
        except Exception as e:
            import traceback

            self._status = SimulationStatus.ERROR
            self._error_message = str(e)
            print(f"Step mode initialization error: {e}")
            traceback.print_exc()
            return False

    def _save_state(self):
        """Save current simulation state for step backward."""
        # Get adapter state (integrator states, etc.)
        adapter_state = self._adapter.get_state() if hasattr(self._adapter, "get_state") else {}

        state = {
            "time": self._current_time,
            "progress": self._progress,
            "total_steps": self._total_steps,
            "result_lengths": {key: len(values) for key, values in self._results.items()},
            "adapter_state": adapter_state,
        }

        print(
            f"[_save_state] Saving state at time={self._current_time}, history_size will be {len(self._state_history) + 1}"
        )
        self._state_history.append(state)

        # Trim history if too large
        if len(self._state_history) > self._max_history_size:
            self._state_history = self._state_history[-self._max_history_size :]

    def _restore_state(self, state: dict[str, Any]):
        """Restore simulation to a previous state."""
        self._current_time = state["time"]
        self._progress = state["progress"]
        self._total_steps = state["total_steps"]
        lengths = state["result_lengths"]
        self._results = {
            key: values[: lengths[key]] for key, values in self._results.items() if key in lengths
        }

        # Restore adapter state if available
        if state.get("adapter_state") and hasattr(self._adapter, "set_state"):
            self._adapter.set_state(state["adapter_state"])

    def step_forward(self, num_steps: int = 1) -> dict[str, Any]:
        """Execute one or more simulation steps."""
        print(
            f"[step_forward] Entry: _step_mode={self._step_mode}, _current_time={self._current_time}"
        )

        if not self._step_mode:
            if not self.initialize_step_mode():
                return {"success": False, "error": self._error_message}

        dt = self.config.step_size
        t_end = self.config.stop_time

        print(
            f"[step_forward] Before loop: _current_time={self._current_time}, dt={dt}, t_end={t_end}"
        )

        steps_executed = 0
        for _ in range(num_steps):
            if self._current_time >= t_end:
                self._status = SimulationStatus.COMPLETED
                break

            # Save state before step (for undo)
            self._save_state()

            # Execute one step
            outputs = self._adapter.step(self._current_time, dt)
            self._record_outputs(self._current_time, outputs)

            # Update state
            old_time = self._current_time
            self._current_time += dt
            print(f"[step_forward] Step: {old_time} -> {self._current_time}")
            self._progress = (self._current_time - self.config.start_time) / (
                t_end - self.config.start_time
            )
            self._total_steps += 1
            steps_executed += 1

        self._execution_time = time.time() - self._start_time

        print(
            f"[step_forward] Exit: _current_time={self._current_time}, steps_executed={steps_executed}"
        )

        return {
            "success": True,
            "stepsExecuted": steps_executed,
            "currentTime": self._current_time,
            "progress": self._progress,
            "completed": self._status == SimulationStatus.COMPLETED,
            "historySize": len(self._state_history),
        }

    def step_backward(self, num_steps: int = 1) -> dict[str, Any]:
        """Step backward by restoring previous state."""
        print(
            f"[step_backward] Entry: _step_mode={self._step_mode}, history_size={len(self._state_history)}, _current_time={self._current_time}"
        )

        if not self._step_mode or len(self._state_history) <= 1:
            print(
                f"[step_backward] Cannot step back: _step_mode={self._step_mode}, history={len(self._state_history)}"
            )
            return {
                "success": False,
                "error": "Cannot step backward - no history available",
            }

        steps_executed = 0
        for _ in range(num_steps):
            if len(self._state_history) <= 1:
                break

            # Remove current state and restore previous
            self._state_history.pop()
            if self._state_history:
                self._restore_state(self._state_history[-1])
                steps_executed += 1

        # Reset status to paused (not completed) when stepping back
        self._status = SimulationStatus.PAUSED

        return {
            "success": True,
            "stepsExecuted": steps_executed,
            "currentTime": self._current_time,
            "progress": self._progress,
            "historySize": len(self._state_history),
        }

    def reset_step_mode(self):
        """Reset step mode simulation to start."""
        if self._step_mode and self._compiled:
            self._current_time = self.config.start_time
            self._progress = 0.0
            self._total_steps = 0
            self._results = {}
            self._state_history = []
            self._status = SimulationStatus.PAUSED
            self._adapter.initialize(self._compiled, self.config)
            self._save_state()

    def reset(self):
        """Reset simulation completely, ready to run again from the beginning.

        This can be called after a simulation completes, pauses, or in step mode.
        It resets all state to initial values while preserving the compiled model.
        """
        self._status = SimulationStatus.IDLE
        self._progress = 0.0
        self._current_time = 0.0
        self._should_stop = False
        self._is_paused = False
        self._error_message = None

        self._results = {}
        self._execution_time = 0
        self._total_steps = 0

        # Clear step mode state
        self._step_mode = False
        self._state_history = []

        # Reinitialize the adapter if we have a compiled model
        if self._compiled:
            self._adapter.initialize(self._compiled, self.config)

    async def continue_from_step_mode(self):
        """Continue running simulation from current step mode position."""
        if not self._step_mode or self._compiled is None:
            return

        try:
            self._step_mode = False
            self._state_history = []  # Clear history since we're now running continuously
            self._status = SimulationStatus.RUNNING
            self._is_paused = False
            self._should_stop = False

            # Run simulation loop from current position
            t = self._current_time
            dt = self.config.step_size
            t_end = self.config.stop_time

            while t < t_end and not self._should_stop:
                # Handle pause
                while self._is_paused and not self._should_stop:
                    await asyncio.sleep(0.1)

                if self._should_stop:
                    break

                # Execute one step
                outputs = self._adapter.step(t, dt)

                # Record outputs for sink blocks
                self._record_outputs(t, outputs)

                # Update state
                t += dt
                self._current_time = t
                self._progress = (t - self.config.start_time) / (t_end - self.config.start_time)
                self._total_steps += 1

                # Yield to allow other tasks (and prevent blocking)
                if self._total_steps % 100 == 0:
                    await asyncio.sleep(0)

            # Finalize
            self._execution_time = time.time() - self._start_time

            if self._should_stop:
                self._status = SimulationStatus.IDLE
            else:
                self._status = SimulationStatus.COMPLETED

        except Exception as e:
            import traceback

            self._status = SimulationStatus.ERROR
            self._error_message = str(e)
            print(f"Simulation error during continue: {e}")
            traceback.print_exc()

    async def run(self):
        """Run the simulation."""
        if not self._run_started:
            self.mark_scheduled()
        try:
            # Compile model
            self._status = SimulationStatus.COMPILING
            self._compiled = self._compiler.compile(self.model)

            if not self._compiled.success:
                self._status = SimulationStatus.ERROR
                self._error_message = self._compiled.message
                if self._compiled.errors:
                    self._error_message = "; ".join(self._compiled.errors)
                return

            # Initialize simulation
            self._status = SimulationStatus.RUNNING
            self._start_time = time.time()

            # Initialize OSK adapter with compiled model
            self._adapter.initialize(self._compiled, self.config)

            # Run simulation loop
            t = self.config.start_time
            dt = self.config.step_size
            t_end = self.config.stop_time

            while t < t_end and not self._should_stop and not self._step_mode:
                # Handle pause - also exit if step mode was entered while paused
                while self._is_paused and not self._should_stop and not self._step_mode:
                    await asyncio.sleep(0.1)

                if self._should_stop or self._step_mode:
                    break

                # Execute one step
                outputs = self._adapter.step(t, dt)

                # Record outputs for sink blocks
                self._record_outputs(t, outputs)

                # Update state
                t += dt
                self._current_time = t
                self._progress = (t - self.config.start_time) / (t_end - self.config.start_time)
                self._total_steps += 1

                # Yield to allow other tasks (and prevent blocking)
                if self._total_steps % 100 == 0:
                    await asyncio.sleep(0)

            # Finalize
            self._execution_time = time.time() - self._start_time

            if self._should_stop or self._step_mode:
                # Don't set to IDLE if we switched to step mode - keep PAUSED status
                if not self._step_mode:
                    self._status = SimulationStatus.IDLE
            else:
                self._status = SimulationStatus.COMPLETED

        except Exception as e:
            import traceback

            self._status = SimulationStatus.ERROR
            self._error_message = str(e)
            print(f"Simulation error: {e}")
            traceback.print_exc()
        finally:
            self._run_finished.set()

    def _record_outputs(self, t: float, outputs: dict[str, float]):
        """Record simulation outputs."""
        for key, value in outputs.items():
            if key not in self._results:
                self._results[key] = []
                self._result_decimation[key] = 1
            self._results[key].append((t, value))
            if len(self._results[key]) > self.config.max_result_points:
                latest = self._results[key][-1]
                self._results[key] = self._results[key][::2]
                if self._results[key][-1] != latest:
                    self._results[key].append(latest)
                self._result_decimation[key] *= 2

    def get_results(self) -> dict[str, Any]:
        """Get simulation results."""
        # Group signals by block ID to combine multi-trace scopes
        block_signals: dict[str, dict] = {}

        for key, data in self._results.items():
            # Key format: "blockId:portId:signalName" or "blockId:inputIndex:sourceName"
            parts = key.split(":")
            block_id = parts[0] if len(parts) > 0 else ""
            parts[1] if len(parts) > 1 else ""
            # Use the signal name from the key (source block name for scope inputs)
            signal_name = parts[2] if len(parts) > 2 else key

            times = [d[0] for d in data]
            values = [d[1] for d in data]

            if block_id not in block_signals:
                block_signals[block_id] = {
                    "blockId": block_id,
                    "portId": "out",
                    "name": block_id,
                    "times": times,
                    "values": [],
                    "inputNames": [],
                    "numInputs": 0,
                }

            # Add this trace to the block's signal data
            block_signals[block_id]["values"].append(values)
            block_signals[block_id]["inputNames"].append(signal_name)
            block_signals[block_id]["numInputs"] += 1

        # Convert to list and handle single-trace case
        signals = []
        for block_data in block_signals.values():
            if block_data["numInputs"] == 1:
                # Single trace - flatten values array
                block_data["values"] = block_data["values"][0]
                block_data["name"] = block_data["inputNames"][0]
                del block_data["inputNames"]
                del block_data["numInputs"]
            signals.append(block_data)

        # Collect data from special sink blocks that use getData() (3D scopes, etc.)
        # These blocks accumulate data internally rather than outputting scalars per step
        signals.extend(self._adapter.get_scope_data())

        # Get analysis data from control analysis blocks
        analyses = self._adapter.get_analysis_data()

        return {
            "signals": signals,
            "analyses": analyses,
            "statistics": {
                "totalSteps": self._total_steps,
                "executionTime": self._execution_time * 1000,  # ms
                "finalTime": self._current_time,
                "decimationFactors": dict(self._result_decimation),
            },
        }
