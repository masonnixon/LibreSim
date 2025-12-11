"""Simulation runner - executes compiled models."""

import asyncio
import time
import uuid
from typing import Dict, List, Any

from ..models.model import Model
from ..models.simulation import (
    SimulationConfig,
    SimulationStatus,
    SimulationResults,
    SignalData,
    SimulationStatistics,
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

        self._results: Dict[str, List[tuple[float, float]]] = {}
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
            self._status = SimulationStatus.ERROR
            print(f"Simulation error: {e}")

    def _record_outputs(self, t: float, outputs: Dict[str, float]):
        """Record simulation outputs."""
        for key, value in outputs.items():
            if key not in self._results:
                self._results[key] = []
            self._results[key].append((t, value))

    def get_results(self) -> Dict[str, Any]:
        """Get simulation results."""
        signals = []

        for key, data in self._results.items():
            # Key format: "blockId:portId:signalName" or "blockId:inputIndex:sourceName"
            parts = key.split(":")
            block_id = parts[0] if len(parts) > 0 else ""
            port_id = parts[1] if len(parts) > 1 else ""
            # Use the signal name from the key (source block name for scope inputs)
            signal_name = parts[2] if len(parts) > 2 else key

            times = [d[0] for d in data]
            values = [d[1] for d in data]

            signals.append({
                "blockId": block_id,
                "portId": port_id,
                "name": signal_name,
                "times": times,
                "values": values,
            })

        return {
            "signals": signals,
            "statistics": {
                "totalSteps": self._total_steps,
                "executionTime": self._execution_time * 1000,  # ms
                "finalTime": self._current_time,
            },
        }
