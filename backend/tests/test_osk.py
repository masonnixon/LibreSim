"""Tests for OSK State and Sim classes."""

import pytest

from src.osk.block import Block
from src.osk.sim import Sim
from src.osk.state import State


class TestStateClass:
    """Tests for the State class."""

    def test_state_init_default(self):
        """Test State initialization with default values."""
        state = State()
        assert state.x == [0.0, 0.0]

    def test_state_init_custom(self):
        """Test State initialization with custom values."""
        state = State([5.0, 1.0])
        assert state.x == [5.0, 1.0]

    def test_state_set(self):
        """Test State set method."""
        state = State()
        State.t = 10.0  # Modify time
        state.set()
        assert State.t == 0.0
        assert State.kpass == 0
        assert State.ready == 1

    def test_state_reset(self):
        """Test State reset method."""
        state = State()
        state.reset(0.05)
        assert State.dtp == 0.05
        assert State.dt == 0.05
        assert State.kpass == 0

    def test_state_propagate_euler(self):
        """Test Euler integration."""
        State.method = 'Euler'
        State.dt = 0.1
        State.kpass = 0

        state = State([0.0, 1.0])  # Initial position 0, velocity 1
        state.propagate()

        # After Euler step: x = x + dt * v = 0 + 0.1 * 1 = 0.1
        assert state.x[0] == pytest.approx(0.1)

    def test_state_propagate_rk2_pass0(self):
        """Test RK2 integration pass 0."""
        State.method = 'RK2'
        State.dt = 0.1
        State.kpass = 0

        state = State([0.0, 1.0])
        state.propagate()

        # After pass 0: half step
        assert state.x[0] == pytest.approx(0.05)

    def test_state_propagate_rk2_pass1(self):
        """Test RK2 integration pass 1."""
        State.method = 'RK2'
        State.dt = 0.1

        state = State([0.0, 1.0])

        # Pass 0
        State.kpass = 0
        state.propagate()

        # Pass 1
        State.kpass = 1
        state.x[1] = 1.0  # Derivative at midpoint
        state.propagate()

        # After pass 1: x = x0 + dt * k2
        assert state.x[0] == pytest.approx(0.1)

    def test_state_propagate_rk4_all_passes(self):
        """Test RK4 integration all passes."""
        State.method = 'RK4'
        State.dt = 0.1

        state = State([0.0, 1.0])

        # Pass 0
        State.kpass = 0
        state.propagate()
        assert state.x[0] == pytest.approx(0.05)

        # Pass 1
        State.kpass = 1
        state.x[1] = 1.0
        state.propagate()
        assert state.x[0] == pytest.approx(0.05)

        # Pass 2
        State.kpass = 2
        state.x[1] = 1.0
        state.propagate()
        assert state.x[0] == pytest.approx(0.1)

        # Pass 3
        State.kpass = 3
        state.x[1] = 1.0
        state.propagate()
        # Final: x = x0 + dt/6 * (k1 + 2*k2 + 2*k3 + k4)
        # = 0 + 0.1/6 * (1 + 2 + 2 + 1) = 0.1
        assert state.x[0] == pytest.approx(0.1)

    def test_state_propagate_merson(self):
        """Test Merson integration."""
        State.method = 'Merson'
        State.dt = 0.1

        state = State([0.0, 1.0])

        # Pass 0
        State.kpass = 0
        state.propagate()

        # Pass 1
        State.kpass = 1
        state.x[1] = 1.0
        state.propagate()

        # Pass 2
        State.kpass = 2
        state.x[1] = 1.0
        state.propagate()

        # Pass 3
        State.kpass = 3
        state.x[1] = 1.0
        state.propagate()

        # Pass 4
        State.kpass = 4
        state.x[1] = 1.0
        state.propagate()

        # Should produce result
        assert isinstance(state.x[0], float)

    def test_state_propagate_unknown_method(self):
        """Test propagate with unknown method defaults to RK4."""
        State.method = 'Unknown'
        State.dt = 0.1
        State.kpass = 0

        state = State([0.0, 1.0])
        state.propagate()

        # Should use RK4 (half step first)
        assert state.x[0] == pytest.approx(0.05)

    def test_state_updateclock_euler(self):
        """Test clock update for Euler method."""
        State.method = 'Euler'
        State.t = 0.0
        State.dtp = 0.1
        State.kpass = 0

        state = State()
        state.updateclock()

        # Euler has 1 pass, so time should advance
        assert State.t == pytest.approx(0.1)
        assert State.kpass == 0
        assert State.ready == 1

    def test_state_updateclock_rk4(self):
        """Test clock update for RK4 method."""
        State.method = 'RK4'
        State.t = 0.0
        State.dtp = 0.1
        State.kpass = 0

        state = State()

        # Pass 0 -> 1
        state.updateclock()
        assert State.kpass == 1
        assert State.ready == 0

        # Pass 1 -> 2
        state.updateclock()
        assert State.kpass == 2
        assert State.ready == 0

        # Pass 2 -> 3
        state.updateclock()
        assert State.kpass == 3
        assert State.ready == 0

        # Pass 3 -> 0, time advances
        state.updateclock()
        assert State.kpass == 0
        assert State.t == pytest.approx(0.1)
        assert State.ready == 1

    def test_state_sample_event(self):
        """Test event-driven sampling."""
        State.t = 5.0
        state = State()

        # Event at t=5
        state.sample(State.EVENT, 5.0)
        assert State.ready == 1

    def test_state_sample_periodic(self):
        """Test periodic sampling."""
        state = State()
        state.sample(0.1, 0.0)  # Non-event sample
        assert State.ready == 1


class TestSimClass:
    """Tests for the Sim class."""

    def test_sim_init(self):
        """Test Sim initialization."""
        stage = []
        sim = Sim(dts=[0.01], tmax=1.0, vStage=[stage])

        assert Sim.tmax == 1.0
        assert Sim.dts == [0.01]
        assert Sim.stop == 0

    def test_sim_terminate(self):
        """Test Sim terminate method."""
        Sim.stop = 0
        Sim.terminate(1)
        assert Sim.stop == 1

    def test_sim_sample(self):
        """Test Sim sample class method."""
        Sim.clock = State()
        State.t = 5.0
        Sim.sample(State.EVENT, 5.0)
        assert State.ready == 1


class SimpleBlock(Block):
    """A simple test block for Sim testing."""

    def __init__(self, value=1.0):
        super().__init__()
        self.value = value
        self.output = 0.0
        self.initCount = 0

    def init(self):
        self.output = self.value

    def update(self):
        self.output = self.value * State.t

    def rpt(self):
        pass

    def getOutput(self, port=0):
        return self.output

    def propagateStates(self):
        pass


class TestSimRun:
    """Tests for Sim.run() method."""

    def test_sim_run_empty_stage(self):
        """Test running simulation with empty stage."""
        sim = Sim(dts=[0.1], tmax=0.5, vStage=[[]])
        results = sim.run()

        assert 'times' in results
        assert 'outputs' in results

    def test_sim_run_single_block(self):
        """Test running simulation with single block."""
        block = SimpleBlock(value=2.0)
        sim = Sim(dts=[0.1], tmax=0.2, vStage=[[block]])
        results = sim.run()

        assert len(results['times']) >= 2
        assert State.t >= 0.2 - State.EPS

    def test_sim_run_multiple_blocks(self):
        """Test running simulation with multiple blocks."""
        block1 = SimpleBlock(value=1.0)
        block2 = SimpleBlock(value=2.0)
        sim = Sim(dts=[0.1], tmax=0.2, vStage=[[block1, block2]])
        results = sim.run()

        assert len(results['times']) >= 2
