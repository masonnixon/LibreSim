"""Simulation runner - executes compiled models."""

import asyncio
import math
import time
import uuid
from dataclasses import dataclass, field
from threading import Lock
from typing import Any

from ..models.model import Model
from ..models.simulation import (
    SimulationConfig,
    SimulationStatus,
)
from ..osk.context import SimContext
from .compiler import CompiledModel, ModelCompiler
from .osk_adapter import OSKAdapter
from .snapshot import (
    SNAPSHOT_SCHEMA_VERSION,
    PreparedAdapterRestore,
    ResultSeriesSnapshot,
    RunnerSnapshot,
    SnapshotValidationError,
)


class SimulationOperationConflict(RuntimeError):
    """Raised when a runner is already owned by another mutating operation."""


@dataclass(eq=False)
class SimulationOperationToken:
    """Opaque identity token proving ownership of one runner operation."""

    kind: str
    background: bool = False
    finished: asyncio.Event = field(default_factory=asyncio.Event)
    adopted: bool = False


@dataclass
class _PreparedRunnerRestore:
    """Validated runner and adapter values awaiting atomic assignment."""

    snapshot: RunnerSnapshot
    adapter: PreparedAdapterRestore
    results: dict[str, list[tuple[float, float]]]
    decimation: dict[str, int]
    generations: dict[str, int]


class SimulationRunner:
    """Runs simulations using the OSK backend."""

    def __init__(self, model: Model, config: SimulationConfig):
        self.model = model
        self.config = config
        self.session_id = str(uuid.uuid4())

        self._status = SimulationStatus.IDLE
        self._progress = 0.0
        self._current_time = config.start_time
        self._should_stop = False
        self._is_paused = False
        self._error_message: str | None = None
        self._run_started = False
        self._run_finished = asyncio.Event()
        self._run_finished.set()
        self._operation_lock = Lock()
        self._active_operation: SimulationOperationToken | None = None
        self._pending_handoff: SimulationOperationToken | None = None
        self._pause_acknowledged = asyncio.Event()
        self._pause_waiter: asyncio.Event | None = None
        self._resume_gate = asyncio.Event()
        self._resume_gate.set()
        self._transition_requested = False

        self._results: dict[str, list[tuple[float, float]]] = {}
        self._result_decimation: dict[str, int] = {}
        # Result history is append-only between decimation events.  A generation
        # checkpoint is materialized only when decimation rewrites that history,
        # allowing step-mode snapshots to remain compact and exact.  For K signals,
        # history limit H, and result limit M, normal forward execution retains
        # O(K * (H + M)); repeated rollback branches have a conservative
        # O(K * H * M) bound.  The O(M) copy occurs only at decimation or branching.
        self._result_generations: dict[str, int] = {}
        self._result_checkpoints: dict[
            str, dict[int, tuple[tuple[float, float], ...]]
        ] = {}
        self._next_result_generation = 0
        self._start_time: float = 0
        self._execution_time: float = 0
        self._total_steps: int = 0

        # Step mode state
        self._step_mode = False
        self._compiled: CompiledModel | None = None  # Compiled model cache
        self._state_history: list[RunnerSnapshot] = []  # For step backward
        self._max_history_size = 1000  # Limit history to prevent memory issues

        # Compile the model
        self._compiler = ModelCompiler()
        self.context = SimContext()
        self._adapter = OSKAdapter(self.context)

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
        with self._operation_lock:
            self._should_stop = True
            self._is_paused = False
            self._resume_gate.set()
            self._pause_acknowledged.clear()
            if self._pause_waiter is not None:
                self._pause_waiter.set()
                self._pause_waiter = None

    def _reserve_operation(
        self,
        kind: str,
        *,
        background: bool = False,
        reset_stop: bool = False,
    ) -> SimulationOperationToken:
        """Atomically reserve this runner for one mutating operation."""
        with self._operation_lock:
            if self._active_operation is not None:
                raise SimulationOperationConflict(
                    f"Simulation is busy with {self._active_operation.kind}"
                )
            token = SimulationOperationToken(kind=kind, background=background)
            self._active_operation = token
            if reset_stop:
                self._should_stop = False
            if background:
                self._run_started = True
                self._run_finished = token.finished
                self._pause_acknowledged.clear()
                if self._pause_waiter is not None:
                    self._pause_waiter.set()
                    self._pause_waiter = None
            return token

    def _claim_operation(
        self,
        kind: str,
        token: SimulationOperationToken,
        *,
        adopt: bool = False,
    ) -> None:
        """Validate that an opaque token still owns the requested operation."""
        with self._operation_lock:
            if self._active_operation is not token or token.kind != kind:
                raise SimulationOperationConflict(
                    f"Invalid or stale operation token for {kind}"
                )
            if adopt:
                if token.adopted:
                    raise SimulationOperationConflict(
                        f"Operation token for {kind} was already adopted"
                    )
                token.adopted = True

    def _release_operation(self, token: SimulationOperationToken) -> bool:
        """Release only the exact active token, transferring a queued handoff."""
        released = False
        with self._operation_lock:
            if self._active_operation is token:
                released = True
                if self._pending_handoff is not None:
                    self._active_operation = self._pending_handoff
                    self._pending_handoff = None
                else:
                    self._active_operation = None
                    if token.background and self._transition_requested:
                        # The handoff requester was cancelled after asking the
                        # background loop to stop. Leave a quiescent paused runner.
                        self._transition_requested = False
                        self._is_paused = True
                        self._resume_gate.clear()
                        self._status = SimulationStatus.PAUSED
        if released:
            token.finished.set()
        return released

    def mark_scheduled(
        self,
        *,
        reset_stop: bool = False,
        kind: str = "run",
    ) -> SimulationOperationToken:
        """Mark this runner as owning a scheduled background run."""
        token = self._reserve_operation(
            kind,
            background=True,
            reset_stop=reset_stop,
        )
        self._status = SimulationStatus.COMPILING
        return token

    def release_unadopted_operation(self, token: SimulationOperationToken) -> bool:
        """Release an operation whose scheduled coroutine never adopted its token."""
        with self._operation_lock:
            if token.adopted or self._active_operation is not token:
                return False
            self._active_operation = None
            self._should_stop = True
            self._is_paused = False
            self._status = SimulationStatus.IDLE
        token.finished.set()
        return True

    def schedule_continue(self) -> SimulationOperationToken:
        """Atomically validate and reserve a background step-mode continuation."""
        with self._operation_lock:
            if self._active_operation is not None:
                raise SimulationOperationConflict(
                    f"Simulation is busy with {self._active_operation.kind}"
                )
            if not (self._step_mode and self._compiled is not None):
                raise ValueError("Simulation is not in step mode")
            token = SimulationOperationToken(kind="continue", background=True)
            self._active_operation = token
            self._should_stop = False
            self._run_started = True
            self._run_finished = token.finished
            self._pause_acknowledged.clear()
            if self._pause_waiter is not None:
                self._pause_waiter.set()
                self._pause_waiter = None
            self._status = SimulationStatus.COMPILING
            return token

    @property
    def has_live_run(self) -> bool:
        with self._operation_lock:
            return bool(
                self._active_operation is not None
                and self._active_operation.background
                and not self._active_operation.finished.is_set()
            )

    @property
    def can_continue_from_step_mode(self) -> bool:
        """Whether a compiled step-mode simulation can continue in the background."""
        return self._step_mode and self._compiled is not None

    async def stop_and_wait(self, timeout: float = 5.0) -> bool:
        """Request stop and wait until the background run has exited."""
        with self._operation_lock:
            self._should_stop = True
            self._is_paused = False
            self._resume_gate.set()
            self._pause_acknowledged.clear()
            if self._pause_waiter is not None:
                self._pause_waiter.set()
                self._pause_waiter = None
            token = self._active_operation
            if token is None or not token.background:
                return True
        try:
            await asyncio.wait_for(token.finished.wait(), timeout=timeout)
        except TimeoutError:
            return False
        return True

    async def pause(self) -> None:
        """Pause at a committed step boundary and wait for acknowledgment."""
        with self._operation_lock:
            if self._is_paused and self._pause_acknowledged.is_set():
                return
            if self._pause_waiter is None:
                self._pause_waiter = asyncio.Event()
            waiter = self._pause_waiter
            self._is_paused = True
            self._resume_gate.clear()
            self._pause_acknowledged.clear()
            token = self._active_operation
            if token is None or not token.background:
                self._status = SimulationStatus.PAUSED
                self._pause_acknowledged.set()
                waiter.set()
        await waiter.wait()

    def resume(self):
        """Resume a paused simulation."""
        with self._operation_lock:
            self._is_paused = False
            self._pause_acknowledged.clear()
            self._resume_gate.set()
            if self._pause_waiter is not None:
                self._pause_waiter.set()
                self._pause_waiter = None
            self._status = SimulationStatus.RUNNING

    async def enter_step_mode(self) -> bool:
        """Enter step mode from a paused continuous simulation.

        Unlike initialize_step_mode(), this preserves the current simulation state
        and time position instead of reinitializing from the start.
        """
        with self._operation_lock:
            active = self._active_operation
            if active is not None and active.background:
                if not self._is_paused or not self._pause_acknowledged.is_set():
                    raise SimulationOperationConflict(
                        "Simulation must be paused before entering step mode"
                    )
                if self._pending_handoff is not None:
                    raise SimulationOperationConflict("A step-mode handoff is already pending")
                token = SimulationOperationToken(kind="step-enter")
                self._pending_handoff = token
                self._transition_requested = True
                self._is_paused = False
                self._resume_gate.set()
                active_finished = active.finished
            elif active is not None:
                raise SimulationOperationConflict(
                    f"Simulation is busy with {active.kind}"
                )
            else:
                token = SimulationOperationToken(kind="step-enter")
                self._active_operation = token
                active_finished = None

        try:
            if active_finished is not None:
                await active_finished.wait()
                self._claim_operation("step-enter", token)
            self._transition_requested = False
            return self._enter_step_mode_owned(token)
        except asyncio.CancelledError:
            with self._operation_lock:
                if self._pending_handoff is token:
                    self._pending_handoff = None
                elif self._active_operation is token:
                    self._active_operation = None
                    token.finished.set()
                    self._transition_requested = False
                    self._is_paused = True
                    self._resume_gate.clear()
                    self._status = SimulationStatus.PAUSED
            raise
        finally:
            self._release_operation(token)

    def _enter_step_mode_owned(self, token: SimulationOperationToken) -> bool:
        """Enter step mode while holding the supplied runner operation."""
        self._claim_operation("step-enter", token)
        print(
            f"[enter_step_mode] Entry: _compiled={self._compiled is not None}, _current_time={self._current_time}"
        )

        if self._compiled is None:
            # Not running yet, need to initialize
            print("[enter_step_mode] No compiled model, calling initialize_step_mode()")
            return self._initialize_step_mode_owned(token, kind="step-enter")

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
            self._save_state(token)

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
        token = self._reserve_operation("step-init")
        try:
            return self._initialize_step_mode_owned(token)
        finally:
            self._release_operation(token)

    def _initialize_step_mode_owned(
        self,
        token: SimulationOperationToken,
        *,
        kind: str = "step-init",
    ) -> bool:
        """Initialize step mode while holding the supplied runner operation."""
        self._claim_operation(kind, token)
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

            # A fresh step-mode lifecycle always starts from the configured
            # boundary, even when compilation is reused from an earlier run.
            self._current_time = self.config.start_time
            self._progress = 0.0
            self._total_steps = 0
            self._execution_time = 0.0
            self._error_message = None
            self._should_stop = False
            self._is_paused = False
            self._clear_result_history()
            self._state_history = []
            self._adapter.initialize(self._compiled, self.config)

            self._step_mode = True
            self._status = SimulationStatus.PAUSED
            self._start_time = time.time()

            # Save initial state
            self._save_state(token)

            return True
        except Exception as e:
            import traceback

            self._status = SimulationStatus.ERROR
            self._error_message = str(e)
            print(f"Step mode initialization error: {e}")
            traceback.print_exc()
            return False

    def capture_snapshot(self) -> RunnerSnapshot:
        """Capture a detached immutable checkpoint while owning the runner."""
        token = self._reserve_operation("snapshot-capture")
        try:
            return self._capture_snapshot_owned(token, compact=False)
        finally:
            self._release_operation(token)

    def _capture_snapshot_owned(
        self,
        token: SimulationOperationToken,
        *,
        compact: bool,
    ) -> RunnerSnapshot:
        self._claim_operation(token.kind, token)
        adapter = self._adapter.capture_snapshot(compact=compact)
        if not math.isclose(
            self._current_time,
            adapter.context.t,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise SnapshotValidationError("Runner and adapter times are inconsistent")
        results = tuple(
            ResultSeriesSnapshot(
                key=key,
                generation=self._result_generations[key],
                length=len(values),
                decimation=self._result_decimation[key],
                values=() if compact else tuple(values),
            )
            for key, values in self._results.items()
        )
        return RunnerSnapshot(
            schema_version=SNAPSHOT_SCHEMA_VERSION,
            compact=compact,
            adapter=adapter,
            current_time=self._current_time,
            progress=self._progress,
            total_steps=self._total_steps,
            execution_time=self._execution_time,
            status=self._status.value,
            step_mode=self._step_mode,
            next_result_generation=self._next_result_generation,
            results=results,
        )

    def restore_snapshot(self, snapshot: RunnerSnapshot) -> None:
        """Atomically restore a detached checkpoint into paused step mode."""
        token = self._reserve_operation("snapshot-restore")
        try:
            self._restore_snapshot_owned(snapshot, token)
        finally:
            self._release_operation(token)

    def _restore_snapshot_owned(
        self,
        snapshot: RunnerSnapshot,
        token: SimulationOperationToken,
    ) -> None:
        self._claim_operation("snapshot-restore", token)
        if snapshot.compact:
            raise SnapshotValidationError("Public restore requires a detached snapshot")
        target = self._prepare_snapshot_restore(snapshot)
        before = self._capture_snapshot_owned(token, compact=False)
        rollback = self._prepare_snapshot_restore(before)
        history_before = list(self._state_history)
        checkpoints_before = {
            key: dict(generations)
            for key, generations in self._result_checkpoints.items()
        }
        try:
            self._commit_snapshot_restore(target)
            self._state_history = []
            self._save_state(token)
        except Exception:
            self._commit_snapshot_restore(rollback)
            self._state_history = history_before
            self._result_checkpoints = checkpoints_before
            self._prune_result_checkpoints()
            raise

    def _prepare_snapshot_restore(self, snapshot: RunnerSnapshot) -> _PreparedRunnerRestore:
        if not isinstance(snapshot, RunnerSnapshot):
            raise SnapshotValidationError("Unsupported runner snapshot object")
        if snapshot.schema_version != SNAPSHOT_SCHEMA_VERSION:
            raise SnapshotValidationError(
                f"Unsupported snapshot schema version {snapshot.schema_version}"
            )
        if snapshot.compact != snapshot.adapter.compact:
            raise SnapshotValidationError("Runner and adapter snapshot modes disagree")
        snapshot.adapter.context.validate_boundary()
        if not math.isclose(
            snapshot.current_time,
            snapshot.adapter.context.t,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise SnapshotValidationError("Runner and adapter snapshot times disagree")
        expected_time = self.config.start_time + snapshot.total_steps * self.config.step_size
        duration = self.config.stop_time - self.config.start_time
        expected_progress = (
            (snapshot.current_time - self.config.start_time) / duration
            if duration > 0
            else math.nan
        )
        if (
            snapshot.total_steps < 0
            or not math.isfinite(snapshot.current_time)
            or not math.isfinite(snapshot.progress)
            or not math.isfinite(snapshot.execution_time)
            or snapshot.execution_time < 0
            or snapshot.status not in {status.value for status in SimulationStatus}
            or not isinstance(snapshot.step_mode, bool)
            or not math.isclose(
                snapshot.current_time,
                expected_time,
                rel_tol=1e-9,
                abs_tol=1e-9,
            )
            or not math.isclose(
                snapshot.progress,
                expected_progress,
                rel_tol=1e-9,
                abs_tol=1e-9,
            )
        ):
            raise SnapshotValidationError("Runner snapshot boundary metadata is inconsistent")
        if snapshot.next_result_generation < 0:
            raise SnapshotValidationError("Invalid next result generation")

        restored_results: dict[str, list[tuple[float, float]]] = {}
        restored_decimation: dict[str, int] = {}
        restored_generations: dict[str, int] = {}
        for ref in snapshot.results:
            if ref.key in restored_results:
                raise SnapshotValidationError(f"Duplicate result key '{ref.key}'")
            if ref.generation < 0 or ref.length < 0 or ref.decimation < 1:
                raise SnapshotValidationError(f"Invalid result metadata for '{ref.key}'")
            if snapshot.compact:
                source: list[tuple[float, float]] | tuple[tuple[float, float], ...]
                if self._result_generations.get(ref.key) == ref.generation:
                    source = self._results.get(ref.key, [])
                else:
                    try:
                        source = self._result_checkpoints[ref.key][ref.generation]
                    except KeyError as exc:
                        raise SnapshotValidationError(
                            f"Missing result generation for '{ref.key}'"
                        ) from exc
                if ref.length > len(source):
                    raise SnapshotValidationError(
                        f"Result length exceeds generation for '{ref.key}'"
                    )
                values = list(source[: ref.length])
            else:
                if ref.length != len(ref.values):
                    raise SnapshotValidationError(
                        f"Detached result length does not match for '{ref.key}'"
                    )
                values = list(ref.values)
            restored_results[ref.key] = values
            restored_decimation[ref.key] = ref.decimation
            restored_generations[ref.key] = ref.generation

        if restored_generations and snapshot.next_result_generation <= max(
            restored_generations.values()
        ):
            raise SnapshotValidationError("Next result generation is not monotonic")
        adapter = self._adapter.prepare_snapshot_restore(snapshot.adapter)
        return _PreparedRunnerRestore(
            snapshot=snapshot,
            adapter=adapter,
            results=restored_results,
            decimation=restored_decimation,
            generations=restored_generations,
        )

    def _commit_snapshot_restore(self, prepared: _PreparedRunnerRestore) -> None:
        adapter_before = self._adapter.capture_snapshot(compact=False)
        adapter_rollback = self._adapter.prepare_snapshot_restore(adapter_before)
        try:
            self._adapter.commit_snapshot_restore(prepared.adapter)
        except Exception:
            self._adapter.commit_snapshot_restore(adapter_rollback)
            raise

        snapshot = prepared.snapshot
        self._current_time = snapshot.current_time
        self._progress = snapshot.progress
        self._total_steps = snapshot.total_steps
        self._execution_time = snapshot.execution_time
        self._start_time = time.time() - snapshot.execution_time
        self._results = prepared.results
        self._result_decimation = prepared.decimation
        self._result_generations = prepared.generations
        self._next_result_generation = snapshot.next_result_generation
        if not snapshot.compact:
            self._result_checkpoints = {}
        self._step_mode = True
        self._status = SimulationStatus.PAUSED
        self._should_stop = False
        self._is_paused = False
        self._error_message = None
        self._transition_requested = False
        self._pending_handoff = None
        self._pause_waiter = None
        self._pause_acknowledged.clear()
        self._resume_gate.set()
        self._run_started = False
        self._run_finished.set()
        self._prune_result_checkpoints()

    def _save_state(self, token: SimulationOperationToken):
        """Save current simulation state for step backward."""
        self._claim_operation(token.kind, token)
        state = self._capture_snapshot_owned(token, compact=True)

        print(
            f"[_save_state] Saving state at time={self._current_time}, history_size will be {len(self._state_history) + 1}"
        )
        self._state_history.append(state)

        # Trim history if too large
        if len(self._state_history) > self._max_history_size:
            self._state_history = self._state_history[-self._max_history_size :]
        self._prune_result_checkpoints()

    def _new_result_generation(self) -> int:
        """Return a runner-local, monotonically increasing result generation."""
        generation = self._next_result_generation
        self._next_result_generation += 1
        return generation

    def _prune_result_checkpoints(self) -> None:
        """Drop immutable result generations no longer referenced by step history."""
        referenced: dict[str, set[int]] = {}
        for state in self._state_history:
            for ref in state.results:
                referenced.setdefault(ref.key, set()).add(ref.generation)

        for key in list(self._result_checkpoints):
            keep = referenced.get(key, set())
            checkpoints = self._result_checkpoints[key]
            self._result_checkpoints[key] = {
                generation: values
                for generation, values in checkpoints.items()
                if generation in keep and generation != self._result_generations.get(key)
            }
            if not self._result_checkpoints[key]:
                del self._result_checkpoints[key]

    def _clear_result_history(self) -> None:
        """Clear result data and all bookkeeping that describes it."""
        self._results = {}
        self._result_decimation = {}
        self._result_generations = {}
        self._result_checkpoints = {}
        self._next_result_generation = 0

    def _restore_state(
        self,
        state: RunnerSnapshot,
        token: SimulationOperationToken,
    ) -> None:
        """Restore simulation to a previous state."""
        self._claim_operation(token.kind, token)
        prepared = self._prepare_snapshot_restore(state)
        self._commit_snapshot_restore(prepared)

    def step_forward(self, num_steps: int = 1) -> dict[str, Any]:
        """Execute one or more simulation steps."""
        token = self._reserve_operation("step-forward")
        try:
            return self._step_forward_owned(token, num_steps)
        finally:
            self._release_operation(token)

    def _step_forward_owned(
        self,
        token: SimulationOperationToken,
        num_steps: int = 1,
    ) -> dict[str, Any]:
        """Step forward while holding the supplied runner operation."""
        self._claim_operation("step-forward", token)
        print(
            f"[step_forward] Entry: _step_mode={self._step_mode}, _current_time={self._current_time}"
        )

        if not self._step_mode:
            if not self._initialize_step_mode_owned(token, kind="step-forward"):
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

            # History entries represent committed states, including the current
            # result and adapter data, exactly once.
            self._save_state(token)

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
        token = self._reserve_operation("step-backward")
        try:
            return self._step_backward_owned(token, num_steps)
        finally:
            self._release_operation(token)

    def _step_backward_owned(
        self,
        token: SimulationOperationToken,
        num_steps: int = 1,
    ) -> dict[str, Any]:
        """Step backward while holding the supplied runner operation."""
        self._claim_operation("step-backward", token)
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

            # Validate and restore before discarding the current checkpoint so a
            # failed restore cannot destroy undo history.
            target = self._state_history[-2]
            self._restore_state(target, token)
            self._state_history.pop()
            self._prune_result_checkpoints()
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
        token = self._reserve_operation("step-reset")
        try:
            self._reset_step_mode_owned(token)
        finally:
            self._release_operation(token)

    def _reset_step_mode_owned(self, token: SimulationOperationToken) -> None:
        """Reset step mode while holding the supplied runner operation."""
        self._claim_operation("step-reset", token)
        if self._step_mode and self._compiled:
            self._current_time = self.config.start_time
            self._progress = 0.0
            self._total_steps = 0
            self._execution_time = 0.0
            self._start_time = time.time()
            self._error_message = None
            self._should_stop = False
            self._is_paused = False
            self._clear_result_history()
            self._state_history = []
            self._status = SimulationStatus.PAUSED
            self._adapter.initialize(self._compiled, self.config)
            self._save_state(token)

    def reset(self):
        """Reset simulation completely, ready to run again from the beginning.

        This can be called after a simulation completes, pauses, or in step mode.
        It resets all state to initial values while preserving the compiled model.
        """
        token = self._reserve_operation("reset")
        try:
            self._reset_owned(token)
        finally:
            self._release_operation(token)

    def _reset_owned(self, token: SimulationOperationToken) -> None:
        """Reset the runner while holding the supplied operation."""
        self._claim_operation("reset", token)
        self._status = SimulationStatus.IDLE
        self._progress = 0.0
        self._current_time = self.config.start_time
        self._should_stop = False
        self._is_paused = False
        self._error_message = None

        self._clear_result_history()
        self._execution_time = 0
        self._total_steps = 0

        # Clear step mode state
        self._step_mode = False
        self._state_history = []

        # Reinitialize the adapter if we have a compiled model
        if self._compiled:
            self._adapter.initialize(self._compiled, self.config)

    async def continue_from_step_mode(
        self,
        token: SimulationOperationToken | None = None,
    ):
        """Continue running simulation from current step mode position."""
        if token is None:
            try:
                token = self.schedule_continue()
            except ValueError:
                return
        self._claim_operation("continue", token, adopt=True)
        try:
            self._step_mode = False
            self._state_history = []  # Clear history since we're now running continuously
            self._prune_result_checkpoints()
            self._status = SimulationStatus.RUNNING
            self._is_paused = False

            # Run simulation loop from current position
            t = self._current_time
            dt = self.config.step_size
            t_end = self.config.stop_time

            while t < t_end and not self._should_stop and not self._transition_requested:
                await self._wait_while_paused()

                if self._should_stop or self._transition_requested:
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
                    await self._cooperate_after_step()

            # Finalize
            self._execution_time = time.time() - self._start_time

            if self._transition_requested:
                self._status = SimulationStatus.PAUSED
            elif self._should_stop:
                self._status = SimulationStatus.IDLE
            else:
                self._status = SimulationStatus.COMPLETED

        except Exception as e:
            import traceback

            self._status = SimulationStatus.ERROR
            self._error_message = str(e)
            print(f"Simulation error during continue: {e}")
            traceback.print_exc()
        finally:
            self._pause_acknowledged.set()
            if self._pause_waiter is not None:
                self._pause_waiter.set()
            self._release_operation(token)

    async def run(self, token: SimulationOperationToken | None = None):
        """Run the simulation."""
        if token is None:
            token = self.mark_scheduled()
        self._claim_operation("run", token, adopt=True)
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
            self._current_time = self.config.start_time

            # Initialize OSK adapter with compiled model
            self._adapter.initialize(self._compiled, self.config)

            # Run simulation loop
            t = self.config.start_time
            dt = self.config.step_size
            t_end = self.config.stop_time

            while (
                t < t_end
                and not self._should_stop
                and not self._step_mode
                and not self._transition_requested
            ):
                await self._wait_while_paused()

                if self._should_stop or self._step_mode or self._transition_requested:
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
                    await self._cooperate_after_step()

            # Finalize
            self._execution_time = time.time() - self._start_time

            if self._transition_requested:
                self._status = SimulationStatus.PAUSED
            elif self._should_stop or self._step_mode:
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
            self._pause_acknowledged.set()
            if self._pause_waiter is not None:
                self._pause_waiter.set()
            self._release_operation(token)

    async def _wait_while_paused(self) -> None:
        """Acknowledge a pause only between fully committed simulation steps."""
        while self._is_paused and not self._should_stop and not self._transition_requested:
            self._status = SimulationStatus.PAUSED
            self._pause_acknowledged.set()
            if self._pause_waiter is not None:
                self._pause_waiter.set()
            await self._resume_gate.wait()
        if not self._is_paused:
            self._pause_acknowledged.clear()
        if not self._should_stop and not self._transition_requested:
            self._status = SimulationStatus.RUNNING

    async def _cooperate_after_step(self) -> None:
        """Yield after a committed batch; tests may gate this boundary."""
        await asyncio.sleep(0)

    def _record_outputs(self, t: float, outputs: dict[str, float]):
        """Record simulation outputs."""
        for key, value in outputs.items():
            if key not in self._results:
                self._results[key] = []
                self._result_decimation[key] = 1
                self._result_generations[key] = self._new_result_generation()
            self._results[key].append((t, value))
            if len(self._results[key]) > self.config.max_result_points:
                generation = self._result_generations[key]
                self._result_checkpoints.setdefault(key, {})[generation] = tuple(
                    self._results[key]
                )
                latest = self._results[key][-1]
                self._results[key] = self._results[key][::2]
                if self._results[key][-1] != latest:
                    self._results[key].append(latest)
                self._result_decimation[key] *= 2
                self._result_generations[key] = self._new_result_generation()
                self._prune_result_checkpoints()

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
