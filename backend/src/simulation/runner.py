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

        self._results: dict[str, list[tuple[float, float]]] = {}
        self._start_time: float = 0
        self._execution_time: float = 0
        self._total_steps: int = 0

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

    def pause(self):
        """Pause the simulation."""
        self._is_paused = True
        self._status = SimulationStatus.PAUSED

    def resume(self):
        """Resume a paused simulation."""
        self._is_paused = False
        self._status = SimulationStatus.RUNNING

    async def run(self):
        """Run the simulation."""
        try:
            # Compile model
            self._status = SimulationStatus.COMPILING
            compiled = self._compiler.compile(self.model)

            if not compiled.success:
                self._status = SimulationStatus.ERROR
                self._error_message = compiled.message
                if compiled.errors:
                    self._error_message = "; ".join(compiled.errors)
                return

            # Initialize simulation
            self._status = SimulationStatus.RUNNING
            self._start_time = time.time()

            # Initialize OSK adapter with compiled model
            self._adapter.initialize(compiled, self.config)

            # Run simulation loop
            t = self.config.start_time
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
            print(f"Simulation error: {e}")
            traceback.print_exc()

    def _record_outputs(self, t: float, outputs: dict[str, float]):
        """Record simulation outputs."""
        for key, value in outputs.items():
            if key not in self._results:
                self._results[key] = []
            self._results[key].append((t, value))

    def get_results(self) -> dict[str, Any]:
        """Get simulation results."""
        # Group signals by block ID to combine multi-trace scopes
        block_signals: dict[str, dict] = {}

        for key, data in self._results.items():
            # Key format: "blockId:portId:signalName" or "blockId:inputIndex:sourceName"
            parts = key.split(":")
            block_id = parts[0] if len(parts) > 0 else ""
            port_id = parts[1] if len(parts) > 1 else ""
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

        return {
            "signals": signals,
            "statistics": {
                "totalSteps": self._total_steps,
                "executionTime": self._execution_time * 1000,  # ms
                "finalTime": self._current_time,
            },
        }
