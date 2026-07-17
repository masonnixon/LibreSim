"""Instance-scoped execution state for the Object-oriented Simulation Kernel."""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from threading import RLock

EPS = 1e-10
EVENT = -1
STAGE_TIME_OFFSETS = {
    "Euler": (0.0,),
    "RK2": (0.0, 0.5),
    "RK4": (0.0, 0.5, 0.5, 1.0),
    "Merson": (0.0, 1.0 / 3.0, 1.0 / 3.0, 0.5, 1.0),
}
_CONTEXT_OWNER_LOCK = RLock()


@dataclass
class SimContext:
    """Mutable timing and control state owned by one simulation graph."""

    t: float = 0.0
    t1: float = 0.0
    dt: float = 0.01
    dtp: float = 0.01
    method: str = "RK4"
    kpass: int = 0
    ready: int = 1
    tickfirst: int = 1
    ticklast: int = 0
    stop: int = 0
    stop0: int = 0
    _owner: object | None = field(default=None, init=False, repr=False, compare=False)

    @property
    def owner(self) -> object | None:
        """Return the graph that permanently claimed this context, if any."""
        return self._owner

    def claim_owner(self, owner: object) -> None:
        """Claim this context for one graph, allowing idempotent repeat claims."""
        with _CONTEXT_OWNER_LOCK:
            if self._owner is None:
                self._owner = owner
            elif self._owner is not owner:
                raise ValueError("SimContext is already owned by another simulation graph")

    @property
    def effective_method(self) -> str:
        """Return the selected method, preserving the legacy RK4 fallback."""
        if self.method in STAGE_TIME_OFFSETS:
            return self.method
        return "RK4"

    @property
    def pass_count(self) -> int:
        """Return the number of integration stages for the effective method."""
        return len(STAGE_TIME_OFFSETS[self.effective_method])

    def reset(
        self,
        *,
        start_time: float = 0.0,
        dtp: float = 0.01,
        method: str = "RK4",
    ) -> None:
        """Reset execution state in place without releasing graph ownership."""
        self.t = start_time
        self.t1 = start_time
        self.dt = dtp
        self.dtp = dtp
        self.method = method
        self.kpass = 0
        self.ready = 1
        self.tickfirst = 1
        self.ticklast = 0
        self.stop = 0
        self.stop0 = 0

    def legacy_set(self, start_time: float = 0.0) -> None:
        """Implement the historical ``State.set`` clock reset."""
        self.t = start_time
        self.t1 = start_time
        self.kpass = 0
        self.ready = 1

    def reset_step(self, dtp: float) -> None:
        """Implement the historical ``State.reset`` step-size reset."""
        self.dtp = dtp
        self.dt = dtp
        self.kpass = 0
        self.ready = 1

    def sample(self, t_event: float) -> None:
        """Mark outputs ready when an event time has been reached."""
        if self.t >= t_event - EPS:
            self.ready = 1

    def begin_step(self, t: float, dt: float) -> None:
        """Start a committed integration step at ``t`` with size ``dt``."""
        self.t = t
        self.t1 = t
        self.dt = dt
        self.dtp = dt
        self.kpass = 0
        self.ready = 1

    def enter_stage(self, kpass: int) -> None:
        """Enter a validated integration stage for the current step."""
        if kpass < 0 or kpass >= self.pass_count:
            raise ValueError(
                f"Invalid stage {kpass} for {self.effective_method} ({self.pass_count} stages)"
            )
        self.kpass = kpass
        self.t = self.t1 + STAGE_TIME_OFFSETS[self.effective_method][kpass] * self.dtp
        self.ready = 0

    def complete_step(self) -> None:
        """Advance to the next committed step boundary."""
        self.t = self.t1 + self.dtp
        self.t1 = self.t
        self.dt = self.dtp
        self.kpass = 0
        self.ready = 1

    def update_clock(self) -> None:
        """Advance one stage using the historical ``State.updateclock`` contract."""
        offsets = STAGE_TIME_OFFSETS[self.effective_method]
        if self.kpass < 0 or self.kpass >= len(offsets):
            raise ValueError(
                f"Invalid current stage {self.kpass} for {self.effective_method} "
                f"({len(offsets)} stages)"
            )
        if self.kpass == 0:
            self.t1 = self.t

        next_pass = self.kpass + 1
        self.dt = self.dtp
        if next_pass >= len(offsets):
            self.complete_step()
        else:
            self.kpass = next_pass
            self.ready = 0
            self.t = self.t1 + offsets[next_pass] * self.dtp

    def request_stop(self, code: int = 1) -> None:
        """Request termination without mutating clock state."""
        self.stop = code


_DEFAULT_CONTEXT = SimContext()
_LEGACY_CONTEXT = _DEFAULT_CONTEXT
_ACTIVE_CONTEXT: ContextVar[SimContext | None] = ContextVar("osk_active_sim_context", default=None)


def get_active_context() -> SimContext:
    """Return the active context or the sequential legacy default."""
    return _ACTIVE_CONTEXT.get() or _LEGACY_CONTEXT


def set_legacy_context(context: SimContext) -> None:
    """Select the fallback used by sequential direct-OSK compatibility calls."""
    global _LEGACY_CONTEXT
    _LEGACY_CONTEXT = context


@contextmanager
def activate_context(context: SimContext) -> Iterator[SimContext]:
    """Temporarily expose ``context`` to legacy ``State.*`` callers."""
    token = _ACTIVE_CONTEXT.set(context)
    try:
        yield context
    finally:
        _ACTIVE_CONTEXT.reset(token)
