"""Instance-scoped Object-oriented Simulation Kernel orchestrator."""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from .block import _GRAPH_BIND_LOCK
from .context import (
    EPS,
    SimContext,
    activate_context,
    get_active_context,
    set_legacy_context,
)

_SIM_FIELDS = frozenset({"stop", "stop0", "dt", "tmax", "dts", "vStage", "clock"})
_SIM_DEFAULTS: dict[str, Any] = {
    "stop": 0,
    "stop0": 0,
    "dt": 0.0,
    "tmax": 0.0,
    "dts": [],
    "vStage": [],
    "clock": None,
}
_ACTIVE_SIM: ContextVar[Any] = ContextVar("osk_active_sim", default=None)
_LEGACY_SIM: Any = None


def _current_sim() -> Any:
    return _ACTIVE_SIM.get() or _LEGACY_SIM


@contextmanager
def _activate_sim(sim: "Sim") -> Iterator["Sim"]:
    token = _ACTIVE_SIM.set(sim)
    try:
        yield sim
    finally:
        _ACTIVE_SIM.reset(token)


class _SimFacade(type):
    """Route deprecated ``Sim.*`` class state to the active/legacy instance."""

    def __getattribute__(cls, name: str) -> Any:
        if name in _SIM_FIELDS:
            sim = _current_sim()
            if sim is not None:
                return getattr(sim, name)
            return _SIM_DEFAULTS[name]
        return super().__getattribute__(name)

    def __setattr__(cls, name: str, value: Any) -> None:
        if name in _SIM_FIELDS:
            sim = _current_sim()
            if sim is not None:
                setattr(sim, name, value)
            else:
                _SIM_DEFAULTS[name] = value
            return
        super().__setattr__(name, value)


class Sim(metaclass=_SimFacade):
    """Execute one block graph using one explicit simulation context."""

    def __init__(
        self,
        dts: list[float],
        tmax: float,
        vStage: list[list[Any]],
        *,
        context: SimContext | None = None,
        owner: object | None = None,
    ):
        native_context = context is None
        if context is None:
            context = SimContext(method=get_active_context().method)

        owner_token = owner if owner is not None else self
        unique_blocks = []
        seen_blocks: set[int] = set()
        for stage in vStage:
            for block in stage:
                if id(block) not in seen_blocks:
                    unique_blocks.append(block)
                    seen_blocks.add(id(block))

        with _GRAPH_BIND_LOCK:
            for block in unique_blocks:
                block.check_context_binding(context, owner_token)
            context.claim_owner(owner_token)
            for block in unique_blocks:
                block.bind_context(context, owner_token)

        self.context = context
        self._owner = owner_token
        self.dts = dts
        self.dt = 0.0
        self.tmax = tmax
        self.vStage = vStage
        self.clock = None
        self.context.stop = 0
        self.context.stop0 = 0

        if native_context or owner is None:
            global _LEGACY_SIM
            _LEGACY_SIM = self
            set_legacy_context(context)

    @property
    def stop(self) -> int:
        return self.context.stop

    @stop.setter
    def stop(self, value: int) -> None:
        self.context.stop = value

    @property
    def stop0(self) -> int:
        return self.context.stop0

    @stop0.setter
    def stop0(self, value: int) -> None:
        self.context.stop0 = value

    @classmethod
    def sample(cls, t_event: float) -> None:
        """Sample the active/legacy instance for class-level compatibility."""
        sim = _current_sim()
        if sim is not None:
            sim.context.sample(t_event)
        else:
            get_active_context().sample(t_event)

    @classmethod
    def terminate(cls, code: int = 1) -> None:
        """Terminate the active/legacy instance for class-level compatibility."""
        sim = _current_sim()
        if sim is not None:
            sim.context.request_stop(code)
        else:
            _SIM_DEFAULTS["stop"] = code

    def run(self) -> dict[str, Any]:
        """Execute this simulation with its context and facade active."""
        with activate_context(self.context), _activate_sim(self):
            return self._run()

    def _run(self) -> dict[str, Any]:
        results: dict[str, Any] = {"times": [], "outputs": {}}

        self.context.legacy_set()
        self.stop = 0
        self.stop0 = 0

        for stage in self.vStage:
            for obj in stage:
                obj.initCount = 0

        self.context.ticklast = 0
        last_stage = 0
        for stage_index, stage in enumerate(self.vStage):
            last_stage = stage_index
            self.dt = (
                self.dts[stage_index]
                if stage_index < len(self.dts)
                else self.dts[-1]
            )
            self.context.reset_step(self.dt)
            self.context.tickfirst = 1
            self.context.ready = 1

            for obj in stage:
                obj.init()
                obj.initCount += 1

            while True:
                if self.context.kpass == 0:
                    self.context.sample(self.tmax)

                for obj in stage:
                    obj.update()

                if self.context.ready:
                    results["times"].append(self.context.t)
                    for obj in stage:
                        obj.rpt()
                        block_id = getattr(obj, "block_id", None) or id(obj)
                        if block_id not in results["outputs"]:
                            results["outputs"][block_id] = []
                        results["outputs"][block_id].append(obj.getOutput())

                    self.context.tickfirst = 0
                    if self.stop != self.stop0:
                        self.stop0 = self.stop
                        break
                    if self.context.t + EPS >= self.tmax:
                        self.stop = -1
                        break

                for obj in stage:
                    obj.propagateStates()
                self.context.update_clock()

            if self.stop < 0:
                break

        self.context.ticklast = 1
        if self.vStage:
            for obj in self.vStage[last_stage]:
                obj.rpt()

        return results
