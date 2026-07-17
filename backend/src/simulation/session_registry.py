"""Process-local registry for independently addressable simulation sessions."""

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import StrEnum

from ..models.simulation import SimulationStatus
from .runner import SimulationOperationToken, SimulationRunner


class SessionRegistryError(RuntimeError):
    """Base class for session registry failures."""


class SessionNotFound(SessionRegistryError):
    """Raised when an explicitly addressed session does not exist."""


class SessionUnavailable(SessionRegistryError):
    """Raised while a known session is being replaced or deleted."""


class SessionCapacityExceeded(SessionRegistryError):
    """Raised when no safe retained session can be pruned."""


class SessionStopFailed(SessionRegistryError):
    """Raised when a live session cannot be stopped for removal."""


class SessionLifecycle(StrEnum):
    """Registry lifecycle separate from a runner's simulation status."""

    ACTIVE = "active"
    DELETING = "deleting"


@dataclass(eq=False)
class SessionRecord:
    """One retained runner and the registry-owned execution metadata around it."""

    runner: SimulationRunner
    sequence: int
    lifecycle: SessionLifecycle = SessionLifecycle.ACTIVE
    task: asyncio.Task[None] | None = None
    operation_token: SimulationOperationToken | None = None
    active_leases: int = 0
    no_active_leases: asyncio.Event = field(default_factory=asyncio.Event)

    def __post_init__(self) -> None:
        self.no_active_leases.set()


RunnerOperation = Callable[[SimulationOperationToken], Awaitable[None]]


class SessionRegistry:
    """Bounded session registry with atomic replacement and leased resolution."""

    def __init__(self, max_sessions: int = 8):
        if max_sessions < 1:
            raise ValueError("max_sessions must be at least 1")
        self.max_sessions = max_sessions
        self._sessions: dict[str, SessionRecord] = {}
        self._current_session_id: str | None = None
        self._next_sequence = 0
        self._lock = asyncio.Lock()
        self._replacement_lock = asyncio.Lock()

    @property
    def current_runner(self) -> SimulationRunner | None:
        """Return the current runner for compatibility and test introspection."""
        if self._current_session_id is None:
            return None
        record = self._sessions.get(self._current_session_id)
        return record.runner if record is not None else None

    @property
    def session_count(self) -> int:
        """Return the number of retained records for diagnostics and tests."""
        return len(self._sessions)

    def get_record(self, session_id: str) -> SessionRecord | None:
        """Return a retained record without acquiring an operation lease."""
        return self._sessions.get(session_id)

    def _promote_current_locked(self) -> None:
        candidates = [
            record
            for record in self._sessions.values()
            if record.lifecycle == SessionLifecycle.ACTIVE
        ]
        self._current_session_id = (
            max(candidates, key=lambda record: record.sequence).runner.session_id
            if candidates
            else None
        )

    @staticmethod
    def _is_safe_prune_candidate(record: SessionRecord) -> bool:
        task_finished = record.task is None or record.task.done()
        return bool(
            record.lifecycle == SessionLifecycle.ACTIVE
            and record.active_leases == 0
            and task_finished
            and not record.runner.has_live_run
            and record.runner.status
            in (SimulationStatus.IDLE, SimulationStatus.COMPLETED, SimulationStatus.ERROR)
        )

    def _make_capacity_locked(self) -> None:
        while len(self._sessions) >= self.max_sessions:
            candidates = [
                record
                for record in self._sessions.values()
                if self._is_safe_prune_candidate(record)
            ]
            if not candidates:
                raise SessionCapacityExceeded("No safe retained simulation can be pruned")
            oldest = min(candidates, key=lambda record: record.sequence)
            self._sessions.pop(oldest.runner.session_id, None)
            if self._current_session_id == oldest.runner.session_id:
                self._promote_current_locked()

    def _task_done(
        self,
        record: SessionRecord,
        token: SimulationOperationToken,
        task: asyncio.Task[None],
    ) -> None:
        record.runner.release_unadopted_operation(token)
        if task.cancelled():
            return
        task.exception()

    def _start_owned_task(
        self,
        record: SessionRecord,
        token: SimulationOperationToken,
        operation: RunnerOperation,
    ) -> asyncio.Task[None]:
        async def execute() -> None:
            await operation(token)

        task = asyncio.create_task(
            execute(),
            name=f"simulation-{record.runner.session_id}-{token.kind}",
        )
        record.operation_token = token
        record.task = task
        task.add_done_callback(
            lambda completed: self._task_done(record, token, completed)
        )
        return task

    def _insert_locked(
        self,
        runner: SimulationRunner,
        *,
        run_operation: RunnerOperation | None,
    ) -> SessionRecord:
        self._make_capacity_locked()
        self._next_sequence += 1
        record = SessionRecord(runner=runner, sequence=self._next_sequence)
        token: SimulationOperationToken | None = None
        try:
            if run_operation is not None:
                token = runner.mark_scheduled()
                self._start_owned_task(record, token, run_operation)
            self._sessions[runner.session_id] = record
            self._current_session_id = runner.session_id
        except BaseException:
            if token is not None:
                runner.release_unadopted_operation(token)
            raise
        return record

    async def install(
        self,
        runner: SimulationRunner,
        *,
        replace_current: bool,
        run_operation: RunnerOperation | None = None,
    ) -> SessionRecord:
        """Install a runner, optionally replacing only the observed current record."""
        if not replace_current:
            async with self._lock:
                return self._insert_locked(runner, run_operation=run_operation)

        async with self._replacement_lock:
            replaced: SessionRecord | None = None
            async with self._lock:
                if self._current_session_id is not None:
                    replaced = self._sessions.get(self._current_session_id)
                    if replaced is not None:
                        replaced.lifecycle = SessionLifecycle.DELETING

            if replaced is not None:
                replaced.runner.stop()
                try:
                    await replaced.no_active_leases.wait()
                    if not await replaced.runner.stop_and_wait():
                        raise SessionStopFailed("Previous simulation did not stop")
                except BaseException:
                    async with self._lock:
                        retained = self._sessions.get(replaced.runner.session_id)
                        if retained is replaced:
                            replaced.lifecycle = SessionLifecycle.ACTIVE
                    raise

            try:
                async with self._lock:
                    if replaced is not None:
                        retained = self._sessions.get(replaced.runner.session_id)
                        if retained is replaced:
                            self._sessions.pop(replaced.runner.session_id)
                            if self._current_session_id == replaced.runner.session_id:
                                self._promote_current_locked()
                    return self._insert_locked(runner, run_operation=run_operation)
            except BaseException:
                if replaced is not None:
                    async with self._lock:
                        retained = self._sessions.get(replaced.runner.session_id)
                        if retained is replaced:
                            replaced.lifecycle = SessionLifecycle.ACTIVE
                raise

    @asynccontextmanager
    async def lease(self, session_id: str | None) -> AsyncIterator[SessionRecord | None]:
        """Resolve and pin an active record until the caller's operation completes."""
        record: SessionRecord | None
        async with self._lock:
            resolved_id = session_id if session_id is not None else self._current_session_id
            record = self._sessions.get(resolved_id) if resolved_id is not None else None
            if record is None:
                if session_id is not None:
                    raise SessionNotFound(session_id)
                yield_none = True
            elif record.lifecycle != SessionLifecycle.ACTIVE:
                raise SessionUnavailable(record.runner.session_id)
            else:
                yield_none = False
                record.active_leases += 1
                record.no_active_leases.clear()

        if yield_none:
            yield None
            return

        assert record is not None
        try:
            yield record
        finally:
            async with self._lock:
                record.active_leases -= 1
                if record.active_leases == 0:
                    record.no_active_leases.set()

    async def schedule(
        self,
        record: SessionRecord,
        token: SimulationOperationToken,
        operation: RunnerOperation,
    ) -> None:
        """Attach a newly reserved background operation to its exact record."""
        async with self._lock:
            retained = self._sessions.get(record.runner.session_id)
            if retained is not record or record.lifecycle != SessionLifecycle.ACTIVE:
                record.runner.release_unadopted_operation(token)
                raise SessionUnavailable(record.runner.session_id)
            self._start_owned_task(record, token, operation)

    async def delete(self, session_id: str) -> None:
        """Tombstone, quiesce, and remove one exact session record."""
        async with self._lock:
            record = self._sessions.get(session_id)
            if record is None:
                raise SessionNotFound(session_id)
            if record.lifecycle != SessionLifecycle.ACTIVE:
                raise SessionUnavailable(session_id)
            record.lifecycle = SessionLifecycle.DELETING

        async def finish() -> None:
            record.runner.stop()
            await record.no_active_leases.wait()
            if not await record.runner.stop_and_wait():
                async with self._lock:
                    retained = self._sessions.get(session_id)
                    if retained is record:
                        record.lifecycle = SessionLifecycle.ACTIVE
                raise SessionStopFailed("Simulation did not stop")
            if record.task is not None and not record.task.done():
                await asyncio.gather(record.task, return_exceptions=True)
            async with self._lock:
                retained = self._sessions.get(session_id)
                if retained is record:
                    self._sessions.pop(session_id)
                    if self._current_session_id == session_id:
                        self._promote_current_locked()

        cleanup = asyncio.create_task(finish(), name=f"delete-simulation-{session_id}")
        await asyncio.shield(cleanup)

    async def shutdown(self) -> None:
        """Stop and discard every retained session."""
        async with self._lock:
            session_ids = list(self._sessions)
        for session_id in session_ids:
            try:
                await self.delete(session_id)
            except SessionRegistryError:
                continue
