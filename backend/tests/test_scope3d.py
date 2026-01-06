"""Tests for the Scope3D block."""

from src.osk.blocks.sinks import Scope3D
from src.osk.blocks.sources import Constant, SineWave
from src.osk.state import State


class TestScope3DBlock:
    """Tests for the Scope3D block."""

    def test_initialization_default(self):
        """Test Scope3D block initialization with default labels."""
        scope = Scope3D()
        assert scope.x_label == "X"
        assert scope.y_label == "Y"
        assert scope.z_label == "Z"
        assert len(scope.inputs) == 3
        assert len(scope.input_blocks) == 3
        assert len(scope.input_source_ports) == 3
        assert scope.times == []
        assert scope.x_values == []
        assert scope.y_values == []
        assert scope.z_values == []

    def test_initialization_custom_labels(self):
        """Test Scope3D block initialization with custom labels."""
        scope = Scope3D(x_label="Position", y_label="Velocity", z_label="Acceleration")
        assert scope.x_label == "Position"
        assert scope.y_label == "Velocity"
        assert scope.z_label == "Acceleration"

    def test_initialization_ignores_extra_kwargs(self):
        """Test that Scope3D ignores extra kwargs (like from JSON frontend)."""
        scope = Scope3D(x_label="X", unknown_param="ignored", sampleTime=0.01)
        assert scope.x_label == "X"

    def test_init_clears_data(self):
        """Test that init() clears all recorded data."""
        scope = Scope3D()
        scope.times = [1, 2, 3]
        scope.x_values = [1, 2, 3]
        scope.y_values = [4, 5, 6]
        scope.z_values = [7, 8, 9]

        scope.init()

        assert scope.times == []
        assert scope.x_values == []
        assert scope.y_values == []
        assert scope.z_values == []

    def test_set_input_x(self):
        """Test setting X input (port 0)."""
        scope = Scope3D()
        scope.setInput(1.5, port=0)
        assert scope.inputs[0] == 1.5
        assert scope.inputs[1] == 0.0
        assert scope.inputs[2] == 0.0

    def test_set_input_y(self):
        """Test setting Y input (port 1)."""
        scope = Scope3D()
        scope.setInput(2.5, port=1)
        assert scope.inputs[0] == 0.0
        assert scope.inputs[1] == 2.5
        assert scope.inputs[2] == 0.0

    def test_set_input_z(self):
        """Test setting Z input (port 2)."""
        scope = Scope3D()
        scope.setInput(3.5, port=2)
        assert scope.inputs[0] == 0.0
        assert scope.inputs[1] == 0.0
        assert scope.inputs[2] == 3.5

    def test_set_input_invalid_port(self):
        """Test setting input on invalid port does nothing."""
        scope = Scope3D()
        scope.setInput(99.0, port=3)  # Invalid port
        assert scope.inputs == [0.0, 0.0, 0.0]

    def test_connect_input(self):
        """Test connecting input blocks."""
        scope = Scope3D()
        const_x = Constant(value=1.0)
        const_y = Constant(value=2.0)
        const_z = Constant(value=3.0)

        scope.connectInput(const_x, port=0)
        scope.connectInput(const_y, port=1)
        scope.connectInput(const_z, port=2)

        assert scope.input_blocks[0] is const_x
        assert scope.input_blocks[1] is const_y
        assert scope.input_blocks[2] is const_z

    def test_connect_input_with_source_port(self):
        """Test connecting input with specific source port."""
        scope = Scope3D()
        const = Constant(value=1.0)

        scope.connectInput(const, port=0, source_port=2)
        assert scope.input_source_ports[0] == 2

    def test_connect_input_invalid_port(self):
        """Test connecting input on invalid port does nothing."""
        scope = Scope3D()
        const = Constant(value=1.0)

        scope.connectInput(const, port=3)  # Invalid port
        assert all(b is None for b in scope.input_blocks)

    def test_update_from_connected_blocks(self):
        """Test update reads from connected blocks."""
        scope = Scope3D()
        const_x = Constant(value=1.0)
        const_y = Constant(value=2.0)
        const_z = Constant(value=3.0)
        const_x.init()
        const_y.init()
        const_z.init()

        scope.connectInput(const_x, port=0)
        scope.connectInput(const_y, port=1)
        scope.connectInput(const_z, port=2)

        scope.update()

        assert scope.inputs[0] == 1.0
        assert scope.inputs[1] == 2.0
        assert scope.inputs[2] == 3.0

    def test_update_partial_connections(self):
        """Test update with only some ports connected."""
        scope = Scope3D()
        const = Constant(value=5.0)
        const.init()

        scope.connectInput(const, port=1)  # Only connect Y

        scope.update()

        assert scope.inputs[0] == 0.0
        assert scope.inputs[1] == 5.0
        assert scope.inputs[2] == 0.0

    def test_rpt_records_when_ready(self):
        """Test rpt() records data when State.ready is True."""
        scope = Scope3D()
        scope.setInput(1.0, port=0)
        scope.setInput(2.0, port=1)
        scope.setInput(3.0, port=2)

        State.t = 0.5
        State.ready = 1

        scope.rpt()

        assert scope.times == [0.5]
        assert scope.x_values == [1.0]
        assert scope.y_values == [2.0]
        assert scope.z_values == [3.0]

    def test_rpt_does_not_record_when_not_ready(self):
        """Test rpt() does not record when State.ready is False."""
        scope = Scope3D()
        scope.setInput(1.0, port=0)
        scope.setInput(2.0, port=1)
        scope.setInput(3.0, port=2)

        State.t = 0.5
        State.ready = 0  # Not ready

        scope.rpt()

        assert scope.times == []
        assert scope.x_values == []
        assert scope.y_values == []
        assert scope.z_values == []

    def test_rpt_multiple_records(self):
        """Test rpt() records multiple data points over time."""
        scope = Scope3D()
        State.ready = 1

        # Record first point
        State.t = 0.0
        scope.setInput(1.0, port=0)
        scope.setInput(1.0, port=1)
        scope.setInput(1.0, port=2)
        scope.rpt()

        # Record second point
        State.t = 0.1
        scope.setInput(2.0, port=0)
        scope.setInput(2.0, port=1)
        scope.setInput(2.0, port=2)
        scope.rpt()

        # Record third point
        State.t = 0.2
        scope.setInput(3.0, port=0)
        scope.setInput(3.0, port=1)
        scope.setInput(3.0, port=2)
        scope.rpt()

        assert scope.times == [0.0, 0.1, 0.2]
        assert scope.x_values == [1.0, 2.0, 3.0]
        assert scope.y_values == [1.0, 2.0, 3.0]
        assert scope.z_values == [1.0, 2.0, 3.0]

    def test_get_data(self):
        """Test getData() returns correct structure."""
        scope = Scope3D(x_label="Lat", y_label="Lon", z_label="Alt")
        scope.setInput(1.0, port=0)
        scope.setInput(2.0, port=1)
        scope.setInput(3.0, port=2)

        State.t = 0.0
        State.ready = 1
        scope.rpt()

        data = scope.getData()

        assert "times" in data
        assert "x" in data
        assert "y" in data
        assert "z" in data
        assert "inputNames" in data
        assert data["times"] == [0.0]
        assert data["x"] == [1.0]
        assert data["y"] == [2.0]
        assert data["z"] == [3.0]
        assert data["inputNames"] == ["Lat", "Lon", "Alt"]

    def test_get_output(self):
        """Test getOutput() returns correct input values."""
        scope = Scope3D()
        scope.setInput(1.5, port=0)
        scope.setInput(2.5, port=1)
        scope.setInput(3.5, port=2)

        assert scope.getOutput(0) == 1.5
        assert scope.getOutput(1) == 2.5
        assert scope.getOutput(2) == 3.5

    def test_get_output_invalid_port(self):
        """Test getOutput() returns 0.0 for invalid port."""
        scope = Scope3D()
        assert scope.getOutput(3) == 0.0
        assert scope.getOutput(100) == 0.0


class TestScope3DWithSineWaves:
    """Integration tests for Scope3D with dynamic signals."""

    def test_helix_trajectory(self):
        """Test recording a simple helix-like trajectory."""
        # Create scope
        scope = Scope3D(x_label="X", y_label="Y", z_label="Z")

        # Create sine waves for X and Y, ramp for Z
        sin_x = SineWave(amplitude=1.0, frequency=1.0)
        sin_y = SineWave(amplitude=1.0, frequency=1.0, phase=1.5708)  # 90° phase shift
        z_val = Constant(value=0.0)  # We'll simulate Z increasing

        sin_x.init()
        sin_y.init()
        z_val.init()

        scope.connectInput(sin_x, port=0)
        scope.connectInput(sin_y, port=1)
        scope.connectInput(z_val, port=2)

        State.ready = 1

        # Simulate 5 time steps
        for i in range(5):
            State.t = i * 0.1
            sin_x.update()
            sin_y.update()
            # Manually increase Z
            scope.setInput(float(i) * 0.1, port=2)
            scope.update()
            scope.rpt()

        data = scope.getData()

        assert len(data["times"]) == 5
        assert len(data["x"]) == 5
        assert len(data["y"]) == 5
        assert len(data["z"]) == 5


class TestScope3DSimulationIntegration:
    """Tests for Scope3D behavior in simulation context."""

    def test_full_update_cycle(self):
        """Test complete update/rpt cycle mimicking simulation."""
        scope = Scope3D()
        const_x = Constant(value=10.0)
        const_y = Constant(value=20.0)
        const_z = Constant(value=30.0)

        const_x.init()
        const_y.init()
        const_z.init()

        scope.connectInput(const_x, port=0)
        scope.connectInput(const_y, port=1)
        scope.connectInput(const_z, port=2)

        State.ready = 1

        # Run 10 steps
        for i in range(10):
            State.t = i * 0.01
            # Sources don't need update typically, but let's be thorough
            scope.update()
            scope.rpt()

        data = scope.getData()

        assert len(data["times"]) == 10
        # All X values should be 10.0
        assert all(v == 10.0 for v in data["x"])
        # All Y values should be 20.0
        assert all(v == 20.0 for v in data["y"])
        # All Z values should be 30.0
        assert all(v == 30.0 for v in data["z"])
