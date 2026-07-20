"""Behavioral coverage for explicit OSK simulation context edge cases."""

from unittest.mock import Mock

import pytest

from src.osk import context as context_module
from src.osk import sim as sim_module
from src.osk.block import Block
from src.osk.context import SimContext
from src.osk.sim import Sim


class StopProbe(Block):
    def __init__(self, stop_code: int | None = None) -> None:
        super().__init__()
        self.stop_code = stop_code
        self.updates = 0
        self.reports = 0

    def update(self) -> None:
        self.updates += 1
        if self.stop_code is not None:
            Sim.terminate(self.stop_code)

    def rpt(self) -> None:
        self.reports += 1


@pytest.fixture
def no_legacy_sim(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sim_module, "_LEGACY_SIM", None)


def test_facade_uses_defaults_without_a_legacy_instance(
    no_legacy_sim: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(sim_module._SIM_DEFAULTS, "dt", 1.25)
    assert Sim.dt == pytest.approx(1.25)

    Sim.dt = 2.5
    assert sim_module._SIM_DEFAULTS["dt"] == pytest.approx(2.5)

    monkeypatch.setattr(Sim, "coverage_marker", "initial", raising=False)
    Sim.coverage_marker = "updated"
    assert Sim.coverage_marker == "updated"


def test_class_helpers_use_the_default_context_without_a_simulation(
    no_legacy_sim: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    context = SimContext(t=2.0, ready=0)
    monkeypatch.setattr(context_module, "_LEGACY_CONTEXT", context)
    monkeypatch.setitem(sim_module._SIM_DEFAULTS, "stop", 0)

    Sim.sample(2.0)
    Sim.terminate(7)

    assert context.ready == 1
    assert sim_module._SIM_DEFAULTS["stop"] == 7


def test_empty_stage_list_returns_empty_results() -> None:
    sim = Sim(dts=[], tmax=1.0, vStage=[])

    assert sim.run() == {"times": [], "outputs": {}}
    assert sim.context.ticklast == 1


@pytest.mark.parametrize(
    ("stop_code", "second_stage_runs"),
    [(3, True), (-3, False)],
)
def test_stop_code_controls_whether_later_stages_run(
    stop_code: int, second_stage_runs: bool
) -> None:
    first = StopProbe(stop_code)
    second = StopProbe()
    sim = Sim(dts=[0.1], tmax=0.0, vStage=[[first], [second]])

    result = sim.run()

    assert first.initCount == 1
    assert (second.initCount == 1) is second_stage_runs
    assert len(result["times"]) == (2 if second_stage_runs else 1)


def test_duplicate_stage_block_is_bound_once_during_construction() -> None:
    block = StopProbe()
    block.check_context_binding = Mock(wraps=block.check_context_binding)
    block.bind_context = Mock(wraps=block.bind_context)
    context = SimContext()
    owner = object()

    Sim(dts=[0.1, 0.1], tmax=0.0, vStage=[[block], [block]], context=context, owner=owner)

    assert block.check_context_binding.call_count == 2
    block.check_context_binding.assert_called_with(context, owner)
    block.bind_context.assert_called_once_with(context, owner)
