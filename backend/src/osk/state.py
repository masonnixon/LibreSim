"""Numerical integrator with instance-scoped simulation timing."""

from typing import Any

from .context import (
    EPS,
    EVENT,
    STAGE_TIME_OFFSETS,
    SimContext,
    get_active_context,
)

_CONTEXT_FIELDS = frozenset(
    {
        "t",
        "t1",
        "dt",
        "dtp",
        "ready",
        "kpass",
        "method",
        "tickfirst",
        "ticklast",
    }
)


class _StateFacade(type):
    """Map legacy class attributes to the active simulation context."""

    def __getattribute__(cls, name: str) -> Any:
        if name in _CONTEXT_FIELDS:
            return getattr(get_active_context(), name)
        return super().__getattribute__(name)

    def __setattr__(cls, name: str, value: Any) -> None:
        if name in _CONTEXT_FIELDS:
            setattr(get_active_context(), name, value)
            return
        super().__setattr__(name, value)


class State(metaclass=_StateFacade):
    """A numerical state explicitly bound to one :class:`SimContext`."""

    # Concrete placeholders keep class-introspection and pytest monkeypatch teardown
    # compatible. The metaclass always serves runtime values from the active context.
    t: float = 0.0
    t1: float = 0.0
    dt: float = 0.01
    dtp: float = 0.01
    ready: int = 1
    kpass: int = 0
    method: str = "RK4"
    tickfirst: int = 1
    ticklast: int = 0

    EPS = EPS
    EVENT = EVENT

    def __init__(self, x=None, *, context: SimContext | None = None):
        if x is None:
            x = [0.0, 0.0]
        self.x = list(x)
        self.context = context or get_active_context()

        self.x0 = 0.0
        self.xd0 = 0.0
        self.xd1 = 0.0
        self.xd2 = 0.0
        self.xd3 = 0.0
        self.xd4 = 0.0

    def set(self) -> None:
        """Initialize simulation timing on this state's bound context."""
        self.context.legacy_set()

    def reset(self, dtp: float) -> None:
        """Reset time-step parameters on this state's bound context."""
        self.context.reset_step(dtp)

    def sample(self, t_event: float) -> None:
        """Mark outputs ready when an event time has been reached."""
        self.context.sample(t_event)

    def propagate(self) -> None:
        """Advance the state using its context's selected integration method."""
        method = self.context.effective_method
        if method == "Euler":
            self._propagate_euler()
        elif method == "RK2":
            self._propagate_rk2()
        elif method == "Merson":
            self._propagate_merson()
        else:
            self._propagate_rk4()

    def _propagate_euler(self) -> None:
        if self.context.kpass == 0:
            self.xd0 = self.x[1]
            self.x[0] = self.x[0] + self.context.dt * self.xd0

    def _propagate_rk2(self) -> None:
        if self.context.kpass == 0:
            self.x0 = self.x[0]
            self.xd0 = self.x[1]
            self.x[0] = self.x0 + self.context.dt / 2.0 * self.xd0
        elif self.context.kpass == 1:
            self.xd1 = self.x[1]
            self.x[0] = self.x0 + self.context.dt * self.xd1

    def _propagate_rk4(self) -> None:
        if self.context.kpass == 0:
            self.x0 = self.x[0]
            self.xd0 = self.x[1]
            self.x[0] = self.x0 + self.context.dt / 2.0 * self.xd0
        elif self.context.kpass == 1:
            self.xd1 = self.x[1]
            self.x[0] = self.x0 + self.context.dt / 2.0 * self.xd1
        elif self.context.kpass == 2:
            self.xd2 = self.x[1]
            self.x[0] = self.x0 + self.context.dt * self.xd2
        elif self.context.kpass == 3:
            self.xd3 = self.x[1]
            self.x[0] = self.x0 + self.context.dt / 6.0 * (
                self.xd0 + 2.0 * self.xd1 + 2.0 * self.xd2 + self.xd3
            )

    def _propagate_merson(self) -> None:
        if self.context.kpass == 0:
            self.x0 = self.x[0]
            self.xd0 = self.x[1]
            self.x[0] = self.x0 + self.context.dt / 3.0 * self.xd0
        elif self.context.kpass == 1:
            self.xd1 = self.x[1]
            self.x[0] = self.x0 + self.context.dt / 6.0 * (self.xd0 + self.xd1)
        elif self.context.kpass == 2:
            self.xd2 = self.x[1]
            self.x[0] = self.x0 + self.context.dt / 8.0 * (self.xd0 + 3.0 * self.xd2)
        elif self.context.kpass == 3:
            self.xd3 = self.x[1]
            self.x[0] = self.x0 + self.context.dt / 2.0 * (
                self.xd0 - 3.0 * self.xd2 + 4.0 * self.xd3
            )
        elif self.context.kpass == 4:
            self.xd4 = self.x[1]
            self.x[0] = self.x0 + self.context.dt / 6.0 * (self.xd0 + 4.0 * self.xd3 + self.xd4)

    def updateclock(self) -> None:
        """Advance the bound simulation clock by one integration stage."""
        self.context.update_clock()


__all__ = ["EPS", "EVENT", "STAGE_TIME_OFFSETS", "State"]
