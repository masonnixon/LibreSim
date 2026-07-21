"""Focused lifecycle and rollback coverage for the session registry."""

import asyncio

import pytest

from src.models.simulation import SimulationStatus
from src.simulation.runner import SimulationOperationToken
from src.simulation.session_registry import (
    SessionLifecycle,
    SessionRecord,
    SessionRegistry,
    SessionStopFailed,
    SessionUnavailable,
)


class FakeRunner:
    def __init__(self, session_id: str, *, stops: bool = True, on_wait=None):
        self.session_id = session_id
        self.status = SimulationStatus.IDLE
        self.has_live_run = False
        self.stops = stops
        self.on_wait = on_wait
        self.released = []

    def stop(self):
        return None

    async def stop_and_wait(self):
        if self.on_wait is not None:
            self.on_wait()
        return self.stops

    def mark_scheduled(self):
        return SimulationOperationToken("run")

    def release_unadopted_operation(self, token):
        self.released.append(token)


async def _operation(token):
    token.adopted = True


def test_registry_constructor_capacity_promotion_and_insert_rollback(monkeypatch):
    with pytest.raises(ValueError, match="at least 1"):
        SessionRegistry(0)
    registry = SessionRegistry(max_sessions=1)
    assert registry.current_runner is None

    first = FakeRunner("first")
    registry._insert_locked(first, run_operation=None)  # type: ignore[arg-type]
    second = FakeRunner("second")
    registry._insert_locked(second, run_operation=None)  # type: ignore[arg-type]
    assert registry.current_runner is second

    failing = FakeRunner("failing")

    def fail_start(*args):
        raise RuntimeError("task start failed")

    monkeypatch.setattr(registry, "_start_owned_task", fail_start)
    with pytest.raises(RuntimeError, match="task start failed"):
        registry._insert_locked(failing, run_operation=_operation)  # type: ignore[arg-type]
    assert len(failing.released) == 1

    class ExplodingDict(dict):
        def __setitem__(self, key, value):
            raise RuntimeError("mapping failed")

    no_token = SessionRegistry()
    no_token._sessions = ExplodingDict()
    with pytest.raises(RuntimeError, match="mapping failed"):
        no_token._insert_locked(FakeRunner("no-token"), run_operation=None)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_replacement_ghost_stop_failures_and_install_rollbacks(monkeypatch):
    empty = SessionRegistry()
    assert (
        await empty.install(FakeRunner("empty"), replace_current=True)  # type: ignore[arg-type]
    ).runner.session_id == "empty"

    ghost_registry = SessionRegistry()
    ghost_registry._current_session_id = "ghost"
    replacement = FakeRunner("replacement")
    assert (
        await ghost_registry.install(replacement, replace_current=True)  # type: ignore[arg-type]
    ).runner is replacement

    registry = SessionRegistry()
    old = FakeRunner("old", stops=False)
    record = await registry.install(old, replace_current=False)  # type: ignore[arg-type]
    with pytest.raises(SessionStopFailed):
        await registry.install(FakeRunner("new"), replace_current=True)  # type: ignore[arg-type]
    assert record.lifecycle == SessionLifecycle.ACTIVE

    removed = SessionRegistry()
    old_removed = FakeRunner("old")
    removed_record = await removed.install(old_removed, replace_current=False)  # type: ignore[arg-type]
    old_removed.stops = False
    old_removed.on_wait = lambda: removed._sessions.pop("old")
    with pytest.raises(SessionStopFailed):
        await removed.install(FakeRunner("new"), replace_current=True)  # type: ignore[arg-type]
    assert removed_record.lifecycle == SessionLifecycle.DELETING

    changed = SessionRegistry()
    changed_old = FakeRunner("old")
    await changed.install(changed_old, replace_current=False)  # type: ignore[arg-type]
    peer = SessionRecord(FakeRunner("peer"), sequence=99)  # type: ignore[arg-type]
    changed_old.on_wait = lambda: changed._sessions.__setitem__("old", peer)
    await changed.install(FakeRunner("new"), replace_current=True)  # type: ignore[arg-type]
    assert changed._sessions["old"] is peer

    rollback = SessionRegistry()
    old_rollback = FakeRunner("old")
    rollback_record = await rollback.install(old_rollback, replace_current=False)  # type: ignore[arg-type]

    def reinsert_then_fail(*args, **kwargs):
        rollback._sessions["old"] = rollback_record
        raise RuntimeError("insert failed")

    monkeypatch.setattr(rollback, "_insert_locked", reinsert_then_fail)
    with pytest.raises(RuntimeError, match="insert failed"):
        await rollback.install(FakeRunner("new"), replace_current=True)  # type: ignore[arg-type]
    assert rollback_record.lifecycle == SessionLifecycle.ACTIVE

    absent = SessionRegistry()

    def fail_insert(*args, **kwargs):
        raise RuntimeError("insert failed")

    monkeypatch.setattr(absent, "_insert_locked", fail_insert)
    with pytest.raises(RuntimeError, match="insert failed"):
        await absent.install(FakeRunner("new"), replace_current=True)  # type: ignore[arg-type]

    popped = SessionRegistry()
    popped_record = await popped.install(FakeRunner("old"), replace_current=False)  # type: ignore[arg-type]
    monkeypatch.setattr(popped, "_insert_locked", fail_insert)
    with pytest.raises(RuntimeError, match="insert failed"):
        await popped.install(FakeRunner("new"), replace_current=True)  # type: ignore[arg-type]
    assert popped_record.lifecycle == SessionLifecycle.DELETING


@pytest.mark.asyncio
async def test_lease_schedule_and_delete_defensive_paths():
    empty = SessionRegistry()
    async with empty.lease(None) as leased:
        assert leased is None

    registry = SessionRegistry()
    runner = FakeRunner("session")
    record = await registry.install(runner, replace_current=False)  # type: ignore[arg-type]

    async with registry.lease("session") as leased:
        assert leased is record
        record.active_leases += 1
    assert record.active_leases == 1
    record.active_leases = 0
    record.no_active_leases.set()

    token = SimulationOperationToken("step")
    registry._sessions.pop("session")
    with pytest.raises(SessionUnavailable):
        await registry.schedule(record, token, _operation)
    assert runner.released == [token]

    registry._sessions["session"] = record
    record.lifecycle = SessionLifecycle.DELETING
    with pytest.raises(SessionUnavailable):
        await registry.delete("session")


@pytest.mark.asyncio
async def test_delete_stop_failure_pending_task_and_noncurrent_cleanup():
    failing = SessionRegistry()
    fail_runner = FakeRunner("fail", stops=False)
    fail_record = await failing.install(fail_runner, replace_current=False)  # type: ignore[arg-type]
    with pytest.raises(SessionStopFailed):
        await failing.delete("fail")
    assert fail_record.lifecycle == SessionLifecycle.ACTIVE

    registry = SessionRegistry()
    current = FakeRunner("current")
    await registry.install(current, replace_current=False)  # type: ignore[arg-type]
    other = FakeRunner("other")
    other_record = await registry.install(other, replace_current=False)  # type: ignore[arg-type]
    registry._current_session_id = "current"
    other_record.task = asyncio.create_task(asyncio.sleep(0))
    await registry.delete("other")
    assert registry.current_runner is current

    removed = SessionRegistry()
    removed_runner = FakeRunner("removed")
    await removed.install(removed_runner, replace_current=False)  # type: ignore[arg-type]
    removed_runner.on_wait = lambda: removed._sessions.pop("removed")
    await removed.delete("removed")

    replaced = SessionRegistry()
    replaced_runner = FakeRunner("replaced", stops=False)
    await replaced.install(replaced_runner, replace_current=False)  # type: ignore[arg-type]
    replacement_record = SessionRecord(FakeRunner("replacement"), sequence=2)  # type: ignore[arg-type]
    replaced_runner.on_wait = lambda: replaced._sessions.__setitem__("replaced", replacement_record)
    with pytest.raises(SessionStopFailed):
        await replaced.delete("replaced")
    assert replaced._sessions["replaced"] is replacement_record

    shutdown = SessionRegistry()
    shutdown_runner = FakeRunner("shutdown", stops=False)
    await shutdown.install(shutdown_runner, replace_current=False)  # type: ignore[arg-type]
    await shutdown.shutdown()
    assert shutdown.session_count == 1
