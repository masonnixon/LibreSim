"""Tests for simulation module: compiler, runner, and osk_adapter."""

import pytest

from src.models.block import Block, Connection, Port, Position
from src.models.model import Model, ModelMetadata
from src.models.simulation import SimulationConfig, SolverType
from src.simulation.compiler import CompiledBlock, CompiledModel, ModelCompiler
from src.simulation.osk_adapter import OSKAdapter, BLOCK_TYPE_MAP, PARAM_MAP


class TestCompiledBlock:
    """Tests for the CompiledBlock dataclass."""

    def test_compiled_block_creation(self):
        """Test creating a CompiledBlock."""
        block = CompiledBlock(
            id="block-1",
            type="constant",
            name="Constant1",
            parameters={"value": 5.0},
            input_connections=[],
            output_connections=["block-2:in-0"],
            execution_order=0,
        )

        assert block.id == "block-1"
        assert block.type == "constant"
        assert block.name == "Constant1"
        assert block.parameters == {"value": 5.0}
        assert block.execution_order == 0

    def test_compiled_block_defaults(self):
        """Test CompiledBlock default values."""
        block = CompiledBlock(
            id="block-1",
            type="gain",
            name="Gain1",
            parameters={},
        )

        assert block.input_connections == []
        assert block.output_connections == []
        assert block.execution_order == 0


class TestCompiledModel:
    """Tests for the CompiledModel dataclass."""

    def test_compiled_model_success(self):
        """Test successful CompiledModel."""
        model = CompiledModel(
            success=True,
            message="Compiled successfully",
            blocks=[],
            execution_order=["block-1", "block-2"],
        )

        assert model.success is True
        assert len(model.errors) == 0

    def test_compiled_model_failure(self):
        """Test failed CompiledModel."""
        model = CompiledModel(
            success=False,
            message="Compilation failed",
            errors=["Algebraic loop detected"],
        )

        assert model.success is False
        assert len(model.errors) == 1


class TestModelCompiler:
    """Tests for the ModelCompiler class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.compiler = ModelCompiler()

    def _create_block(self, block_id, block_type, name, params=None, inputs=None, outputs=None):
        """Helper to create a Block."""
        if params is None:
            params = {}
        if inputs is None:
            inputs = []
        if outputs is None:
            outputs = []
        return Block(
            id=block_id,
            type=block_type,
            name=name,
            position=Position(x=100, y=100),
            parameters=params,
            inputPorts=inputs,
            outputPorts=outputs,
        )

    def _create_connection(self, conn_id, src_block, src_port, tgt_block, tgt_port):
        """Helper to create a Connection."""
        return Connection(
            id=conn_id,
            sourceBlockId=src_block,
            sourcePortId=src_port,
            targetBlockId=tgt_block,
            targetPortId=tgt_port,
        )

    def test_compile_empty_model(self):
        """Test compiling a model with no blocks."""
        model = Model(
            id="model-1",
            metadata=ModelMetadata(name="Empty Model"),
            blocks=[],
            connections=[],
            simulationConfig=SimulationConfig(),
        )

        result = self.compiler.compile(model)
        assert result.success is False
        assert "no blocks" in result.message

    def test_compile_simple_model(self):
        """Test compiling a simple model."""
        const_block = self._create_block(
            "const-1", "constant", "Constant1", {"value": 5.0},
            outputs=[Port(id="const-1-out-0", name="out", dataType="double", dimensions=[1])]
        )
        scope_block = self._create_block(
            "scope-1", "scope", "Scope1", {},
            inputs=[Port(id="scope-1-in-0", name="in", dataType="double", dimensions=[1])]
        )

        conn = self._create_connection(
            "conn-1", "const-1", "const-1-out-0", "scope-1", "scope-1-in-0"
        )

        model = Model(
            id="model-1",
            metadata=ModelMetadata(name="Test Model"),
            blocks=[const_block, scope_block],
            connections=[conn],
            simulationConfig=SimulationConfig(),
        )

        result = self.compiler.compile(model)
        assert result.success is True
        assert len(result.blocks) == 2
        assert len(result.execution_order) == 2

    def test_compile_execution_order(self):
        """Test that execution order follows dependencies."""
        const_block = self._create_block(
            "const-1", "constant", "Constant1", {"value": 5.0},
            outputs=[Port(id="const-1-out-0", name="out", dataType="double", dimensions=[1])]
        )
        gain_block = self._create_block(
            "gain-1", "gain", "Gain1", {"gain": 2.0},
            inputs=[Port(id="gain-1-in-0", name="in", dataType="double", dimensions=[1])],
            outputs=[Port(id="gain-1-out-0", name="out", dataType="double", dimensions=[1])]
        )
        scope_block = self._create_block(
            "scope-1", "scope", "Scope1", {},
            inputs=[Port(id="scope-1-in-0", name="in", dataType="double", dimensions=[1])]
        )

        conn1 = self._create_connection(
            "conn-1", "const-1", "const-1-out-0", "gain-1", "gain-1-in-0"
        )
        conn2 = self._create_connection(
            "conn-2", "gain-1", "gain-1-out-0", "scope-1", "scope-1-in-0"
        )

        model = Model(
            id="model-1",
            metadata=ModelMetadata(name="Test Model"),
            blocks=[scope_block, const_block, gain_block],  # Scrambled order
            connections=[conn1, conn2],
            simulationConfig=SimulationConfig(),
        )

        result = self.compiler.compile(model)
        assert result.success is True

        # Constant should come before gain, gain before scope
        order = result.execution_order
        const_idx = order.index("const-1")
        gain_idx = order.index("gain-1")
        scope_idx = order.index("scope-1")

        assert const_idx < gain_idx < scope_idx

    def test_compile_algebraic_loop_detection(self):
        """Test that algebraic loops are detected."""
        # Create a loop: gain1 -> gain2 -> gain1
        gain1 = self._create_block(
            "gain-1", "gain", "Gain1", {"gain": 2.0},
            inputs=[Port(id="gain-1-in-0", name="in", dataType="double", dimensions=[1])],
            outputs=[Port(id="gain-1-out-0", name="out", dataType="double", dimensions=[1])]
        )
        gain2 = self._create_block(
            "gain-2", "gain", "Gain2", {"gain": 2.0},
            inputs=[Port(id="gain-2-in-0", name="in", dataType="double", dimensions=[1])],
            outputs=[Port(id="gain-2-out-0", name="out", dataType="double", dimensions=[1])]
        )

        conn1 = self._create_connection(
            "conn-1", "gain-1", "gain-1-out-0", "gain-2", "gain-2-in-0"
        )
        conn2 = self._create_connection(
            "conn-2", "gain-2", "gain-2-out-0", "gain-1", "gain-1-in-0"
        )

        model = Model(
            id="model-1",
            metadata=ModelMetadata(name="Loop Model"),
            blocks=[gain1, gain2],
            connections=[conn1, conn2],
            simulationConfig=SimulationConfig(),
        )

        result = self.compiler.compile(model)
        assert result.success is False
        assert "Algebraic loop" in result.message

    def test_compile_no_loop_with_integrator(self):
        """Test that loops with integrators are not algebraic loops."""
        # Create a feedback loop with integrator: sum -> integrator -> gain -> sum
        sum_block = self._create_block(
            "sum-1", "sum", "Sum1", {"signs": "+-"},
            inputs=[
                Port(id="sum-1-in-0", name="in1", dataType="double", dimensions=[1]),
                Port(id="sum-1-in-1", name="in2", dataType="double", dimensions=[1])
            ],
            outputs=[Port(id="sum-1-out-0", name="out", dataType="double", dimensions=[1])]
        )
        integrator = self._create_block(
            "int-1", "integrator", "Integrator1", {"initialCondition": 0.0},
            inputs=[Port(id="int-1-in-0", name="in", dataType="double", dimensions=[1])],
            outputs=[Port(id="int-1-out-0", name="out", dataType="double", dimensions=[1])]
        )
        gain_block = self._create_block(
            "gain-1", "gain", "Gain1", {"gain": 0.5},
            inputs=[Port(id="gain-1-in-0", name="in", dataType="double", dimensions=[1])],
            outputs=[Port(id="gain-1-out-0", name="out", dataType="double", dimensions=[1])]
        )
        const_block = self._create_block(
            "const-1", "constant", "Constant1", {"value": 1.0},
            outputs=[Port(id="const-1-out-0", name="out", dataType="double", dimensions=[1])]
        )

        # const -> sum (input 1)
        conn1 = self._create_connection(
            "conn-1", "const-1", "const-1-out-0", "sum-1", "sum-1-in-0"
        )
        # sum -> integrator
        conn2 = self._create_connection(
            "conn-2", "sum-1", "sum-1-out-0", "int-1", "int-1-in-0"
        )
        # integrator -> gain
        conn3 = self._create_connection(
            "conn-3", "int-1", "int-1-out-0", "gain-1", "gain-1-in-0"
        )
        # gain -> sum (input 2) - feedback
        conn4 = self._create_connection(
            "conn-4", "gain-1", "gain-1-out-0", "sum-1", "sum-1-in-1"
        )

        model = Model(
            id="model-1",
            metadata=ModelMetadata(name="Feedback Model"),
            blocks=[sum_block, integrator, gain_block, const_block],
            connections=[conn1, conn2, conn3, conn4],
            simulationConfig=SimulationConfig(),
        )

        result = self.compiler.compile(model)
        # Should succeed because integrator breaks the loop
        assert result.success is True

    def test_build_input_map(self):
        """Test building the input connection map."""
        conn = Connection(
            id="conn-1",
            sourceBlockId="block-1",
            sourcePortId="block-1-out-0",
            targetBlockId="block-2",
            targetPortId="block-2-in-0",
        )

        result = self.compiler._build_input_map([conn])
        assert "block-2" in result
        assert "block-1:block-1-out-0@block-2-in-0" in result["block-2"]

    def test_build_output_map(self):
        """Test building the output connection map."""
        conn = Connection(
            id="conn-1",
            sourceBlockId="block-1",
            sourcePortId="block-1-out-0",
            targetBlockId="block-2",
            targetPortId="block-2-in-0",
        )

        result = self.compiler._build_output_map([conn])
        assert "block-1" in result
        assert "block-2:block-2-in-0" in result["block-1"]

    def test_state_holding_blocks(self):
        """Test that STATE_HOLDING_BLOCKS contains expected block types."""
        assert "integrator" in ModelCompiler.STATE_HOLDING_BLOCKS
        assert "unit_delay" in ModelCompiler.STATE_HOLDING_BLOCKS
        assert "transfer_function" in ModelCompiler.STATE_HOLDING_BLOCKS
        assert "pid_controller" in ModelCompiler.STATE_HOLDING_BLOCKS
        # Non-state-holding blocks should not be in the set
        assert "gain" not in ModelCompiler.STATE_HOLDING_BLOCKS
        assert "sum" not in ModelCompiler.STATE_HOLDING_BLOCKS


class TestOSKAdapter:
    """Tests for the OSKAdapter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.adapter = OSKAdapter()

    def test_adapter_init(self):
        """Test OSKAdapter initialization."""
        assert self.adapter._compiled_model is None
        assert self.adapter._config is None
        assert self.adapter._osk_blocks == {}
        assert self.adapter._sink_blocks == []

    def test_get_solver_method(self):
        """Test solver method conversion."""
        assert self.adapter._get_solver_method(SolverType.EULER) == "Euler"
        assert self.adapter._get_solver_method(SolverType.RK4) == "RK4"
        assert self.adapter._get_solver_method(SolverType.MERSON) == "Merson"

    def test_get_solver(self):
        """Test public get_solver method."""
        assert self.adapter.get_solver(SolverType.EULER) == "Euler"
        assert self.adapter.get_solver(SolverType.RK4) == "RK4"

    def test_map_parameters_constant(self):
        """Test parameter mapping for constant block."""
        params = {"value": 5.0}
        result = self.adapter._map_parameters("constant", params)
        assert result == {"value": 5.0}

    def test_map_parameters_step(self):
        """Test parameter mapping for step block."""
        params = {"stepTime": 1.0, "initialValue": 0.0, "finalValue": 1.0}
        result = self.adapter._map_parameters("step", params)
        assert result == {"step_time": 1.0, "initial_value": 0.0, "final_value": 1.0}

    def test_map_parameters_gain(self):
        """Test parameter mapping for gain block."""
        params = {"gain": 2.5}
        result = self.adapter._map_parameters("gain", params)
        assert result == {"gain": 2.5}

    def test_map_parameters_unknown_block(self):
        """Test parameter mapping for unknown block type."""
        params = {"someParam": "value"}
        result = self.adapter._map_parameters("unknown_type", params)
        assert result == {"someParam": "value"}

    def test_block_type_map_coverage(self):
        """Test that BLOCK_TYPE_MAP covers major block types."""
        # Sources
        assert "constant" in BLOCK_TYPE_MAP
        assert "step" in BLOCK_TYPE_MAP
        assert "ramp" in BLOCK_TYPE_MAP
        assert "sine_wave" in BLOCK_TYPE_MAP

        # Sinks
        assert "scope" in BLOCK_TYPE_MAP
        assert "display" in BLOCK_TYPE_MAP
        assert "to_workspace" in BLOCK_TYPE_MAP

        # Continuous
        assert "integrator" in BLOCK_TYPE_MAP
        assert "derivative" in BLOCK_TYPE_MAP
        assert "transfer_function" in BLOCK_TYPE_MAP

        # Math
        assert "sum" in BLOCK_TYPE_MAP
        assert "gain" in BLOCK_TYPE_MAP
        assert "product" in BLOCK_TYPE_MAP

    def test_param_map_coverage(self):
        """Test that PARAM_MAP covers major block types."""
        assert "constant" in PARAM_MAP
        assert "step" in PARAM_MAP
        assert "gain" in PARAM_MAP
        assert "integrator" in PARAM_MAP
        assert "pid_controller" in PARAM_MAP

    def test_initialize_and_create_blocks(self):
        """Test initializing adapter with compiled model."""
        compiled_block = CompiledBlock(
            id="const-1",
            type="constant",
            name="Constant1",
            parameters={"value": 5.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )

        compiled_model = CompiledModel(
            success=True,
            message="OK",
            blocks=[compiled_block],
            execution_order=["const-1"],
        )

        config = SimulationConfig()
        self.adapter.initialize(compiled_model, config)

        assert self.adapter._compiled_model is compiled_model
        assert self.adapter._config is config
        assert "const-1" in self.adapter._osk_blocks

        # Check the created OSK block
        osk_block = self.adapter.get_block("const-1")
        assert osk_block is not None
        assert osk_block.value == 5.0

    def test_get_block_not_found(self):
        """Test getting a non-existent block."""
        result = self.adapter.get_block("nonexistent")
        assert result is None

    def test_get_all_blocks(self):
        """Test getting all blocks."""
        compiled_block = CompiledBlock(
            id="const-1",
            type="constant",
            name="Constant1",
            parameters={"value": 5.0},
        )

        compiled_model = CompiledModel(
            success=True,
            message="OK",
            blocks=[compiled_block],
            execution_order=["const-1"],
        )

        self.adapter.initialize(compiled_model, SimulationConfig())
        all_blocks = self.adapter.get_all_blocks()

        assert "const-1" in all_blocks
        assert len(all_blocks) == 1

    def test_step_no_model(self):
        """Test step with no initialized model."""
        result = self.adapter.step(0.0, 0.01)
        assert result == {}

    def test_step_with_simple_model(self):
        """Test step with a simple model."""
        const_block = CompiledBlock(
            id="const-1",
            type="constant",
            name="Constant1",
            parameters={"value": 5.0},
        )
        scope_block = CompiledBlock(
            id="scope-1",
            type="scope",
            name="Scope1",
            parameters={"numInputs": 1},
            input_connections=["const-1:const-1-out-0@scope-1-in-0"],
        )

        compiled_model = CompiledModel(
            success=True,
            message="OK",
            blocks=[const_block, scope_block],
            execution_order=["const-1", "scope-1"],
        )

        self.adapter.initialize(compiled_model, SimulationConfig())

        # Run a step
        outputs = self.adapter.step(0.0, 0.01)

        # Should have recorded the scope output
        assert len(outputs) > 0

    def test_run_simulation_no_model(self):
        """Test run_simulation with no model."""
        result = self.adapter.run_simulation()
        assert result["signals"] == []


class TestOSKBlockBase:
    """Tests for the OSK Block base class."""

    def test_block_init(self):
        """Test Block initialization."""
        from src.osk.block import Block
        block = Block()
        assert block.vState == []
        assert block.initCount == 0

    def test_add_integrator(self):
        """Test adding an integrator."""
        from src.osk.block import Block
        block = Block()
        x = block.addIntegrator([1.0, 0.5])

        assert len(block.vState) == 1
        assert x[0] == 1.0
        assert x[1] == 0.5

    def test_add_integrator_default(self):
        """Test adding an integrator with default values."""
        from src.osk.block import Block
        block = Block()
        x = block.addIntegrator()

        assert x[0] == 0.0
        assert x[1] == 0.0

    def test_set_method(self):
        """Test setting integration method."""
        from src.osk.block import Block
        from src.osk.state import State
        block = Block()
        block.set_method('Euler')
        assert State.method == 'Euler'

        block.set_method('RK4')
        assert State.method == 'RK4'

    def test_propagate_states(self):
        """Test propagating states."""
        from src.osk.block import Block
        from src.osk.state import State

        State.method = 'Euler'
        State.dt = 0.1
        State.kpass = 0

        block = Block()
        x = block.addIntegrator([0.0, 1.0])  # position=0, velocity=1

        block.propagateStates()

        # After Euler step: x = 0 + 0.1 * 1 = 0.1
        assert x[0] == pytest.approx(0.1)

    def test_get_output_default(self):
        """Test default getOutput."""
        from src.osk.block import Block
        block = Block()
        assert block.getOutput() == 0.0

    def test_get_output_with_state(self):
        """Test getOutput with state."""
        from src.osk.block import Block
        block = Block()
        x = block.addIntegrator([5.0, 0.0])
        assert block.getOutput(0) == 5.0

    def test_state_method(self):
        """Test state() method returns default."""
        from src.osk.block import Block
        block = Block()
        assert block.state() == [0.0, 0.0]

    def test_set_input_default(self):
        """Test setInput does nothing by default."""
        from src.osk.block import Block
        block = Block()
        # Should not raise
        block.setInput(5.0, 0)

    def test_init_update_rpt_methods(self):
        """Test that init, update, rpt can be called."""
        from src.osk.block import Block
        block = Block()
        # Should not raise
        block.init()
        block.update()
        block.rpt()


class TestSimulationRunner:
    """Tests for the SimulationRunner class."""

    def _create_simple_model(self):
        """Create a simple model for testing."""
        const_block = Block(
            id="const-1",
            type="constant",
            name="Constant1",
            position=Position(x=100, y=100),
            parameters={"value": 5.0},
            inputPorts=[],
            outputPorts=[Port(id="const-1-out-0", name="out", dataType="double", dimensions=[1])],
        )
        scope_block = Block(
            id="scope-1",
            type="scope",
            name="Scope1",
            position=Position(x=200, y=100),
            parameters={"numInputs": 1},
            inputPorts=[Port(id="scope-1-in-0", name="in", dataType="double", dimensions=[1])],
            outputPorts=[],
        )
        conn = Connection(
            id="conn-1",
            sourceBlockId="const-1",
            sourcePortId="const-1-out-0",
            targetBlockId="scope-1",
            targetPortId="scope-1-in-0",
        )
        return Model(
            id="model-1",
            metadata=ModelMetadata(name="Test Model"),
            blocks=[const_block, scope_block],
            connections=[conn],
            simulationConfig=SimulationConfig(stopTime=0.1, stepSize=0.01),
        )

    def test_runner_init(self):
        """Test SimulationRunner initialization."""
        from src.simulation.runner import SimulationRunner
        from src.models.simulation import SimulationStatus

        model = self._create_simple_model()
        config = SimulationConfig(stopTime=1.0, stepSize=0.01)
        runner = SimulationRunner(model, config)

        assert runner.model is model
        assert runner.config is config
        assert runner.session_id is not None
        assert runner.status == SimulationStatus.IDLE
        assert runner.progress == 0.0
        assert runner.current_time == 0.0
        assert runner.error_message is None

    def test_runner_stop(self):
        """Test requesting simulation stop."""
        from src.simulation.runner import SimulationRunner

        model = self._create_simple_model()
        runner = SimulationRunner(model, SimulationConfig())
        runner.stop()
        assert runner._should_stop is True

    def test_runner_pause_resume(self):
        """Test pause and resume."""
        from src.simulation.runner import SimulationRunner
        from src.models.simulation import SimulationStatus

        model = self._create_simple_model()
        runner = SimulationRunner(model, SimulationConfig())

        runner.pause()
        assert runner._is_paused is True
        assert runner.status == SimulationStatus.PAUSED

        runner.resume()
        assert runner._is_paused is False
        assert runner.status == SimulationStatus.RUNNING

    @pytest.mark.asyncio
    async def test_runner_run_simple(self):
        """Test running a simple simulation."""
        from src.simulation.runner import SimulationRunner
        from src.models.simulation import SimulationStatus

        model = self._create_simple_model()
        config = SimulationConfig(stopTime=0.05, stepSize=0.01)
        runner = SimulationRunner(model, config)

        await runner.run()

        assert runner.status == SimulationStatus.COMPLETED
        assert runner.current_time >= 0.05 - 0.001  # Allow small tolerance

    def test_runner_get_results(self):
        """Test getting simulation results."""
        from src.simulation.runner import SimulationRunner

        model = self._create_simple_model()
        runner = SimulationRunner(model, SimulationConfig())

        # Record some outputs manually
        runner._results["block-1:out:Signal"] = [(0.0, 1.0), (0.1, 2.0)]
        runner._total_steps = 2
        runner._execution_time = 0.1
        runner._current_time = 0.1

        results = runner.get_results()
        assert "signals" in results
        assert "statistics" in results
        assert results["statistics"]["totalSteps"] == 2

    def test_runner_record_outputs(self):
        """Test _record_outputs method."""
        from src.simulation.runner import SimulationRunner

        model = self._create_simple_model()
        runner = SimulationRunner(model, SimulationConfig())

        runner._record_outputs(0.0, {"block-1:out:Signal": 5.0})
        runner._record_outputs(0.1, {"block-1:out:Signal": 10.0})

        assert "block-1:out:Signal" in runner._results
        assert len(runner._results["block-1:out:Signal"]) == 2
        assert runner._results["block-1:out:Signal"][0] == (0.0, 5.0)
        assert runner._results["block-1:out:Signal"][1] == (0.1, 10.0)

    def test_runner_get_results_multi_trace(self):
        """Test get_results with multiple traces for same block."""
        from src.simulation.runner import SimulationRunner

        model = self._create_simple_model()
        runner = SimulationRunner(model, SimulationConfig())

        # Simulate multi-trace scope output
        runner._results["scope-1:0:Signal1"] = [(0.0, 1.0), (0.1, 2.0)]
        runner._results["scope-1:1:Signal2"] = [(0.0, 3.0), (0.1, 4.0)]
        runner._total_steps = 2
        runner._execution_time = 0.1
        runner._current_time = 0.1

        results = runner.get_results()
        # Should combine into one block entry with multiple traces
        assert len(results["signals"]) == 1
        block_data = results["signals"][0]
        assert block_data["numInputs"] == 2


class TestCompilerSubsystemFlattening:
    """Tests for subsystem flattening in the compiler."""

    def setup_method(self):
        self.compiler = ModelCompiler()

    def test_flatten_subsystems_no_children(self):
        """Test flattening subsystem with no children."""
        subsystem = Block(
            id="sub-1",
            type="subsystem",
            name="Subsystem1",
            position=Position(x=100, y=100),
            parameters={},
            inputPorts=[],
            outputPorts=[],
            children=None,
            childConnections=None,
        )

        blocks, connections = self.compiler._flatten_subsystems([subsystem], [])

        # Subsystem without children should be kept as-is
        assert len(blocks) == 1
        assert blocks[0].id == "sub-1"

    def test_flatten_subsystems_with_children(self):
        """Test flattening subsystem with children."""
        # Create child blocks
        inport = Block(
            id="in-1",
            type="inport",
            name="In1",
            position=Position(x=50, y=50),
            parameters={"portNumber": 1},
            inputPorts=[Port(id="in-1-in-0", name="in", dataType="double", dimensions=[1])],
            outputPorts=[Port(id="in-1-out-0", name="out", dataType="double", dimensions=[1])],
        )
        gain = Block(
            id="gain-1",
            type="gain",
            name="Gain1",
            position=Position(x=100, y=50),
            parameters={"gain": 2.0},
            inputPorts=[Port(id="gain-1-in-0", name="in", dataType="double", dimensions=[1])],
            outputPorts=[Port(id="gain-1-out-0", name="out", dataType="double", dimensions=[1])],
        )
        outport = Block(
            id="out-1",
            type="outport",
            name="Out1",
            position=Position(x=150, y=50),
            parameters={"portNumber": 1},
            inputPorts=[Port(id="out-1-in-0", name="in", dataType="double", dimensions=[1])],
            outputPorts=[Port(id="out-1-out-0", name="out", dataType="double", dimensions=[1])],
        )

        # Child connections
        conn1 = Connection(
            id="child-conn-1",
            sourceBlockId="in-1",
            sourcePortId="in-1-out-0",
            targetBlockId="gain-1",
            targetPortId="gain-1-in-0",
        )
        conn2 = Connection(
            id="child-conn-2",
            sourceBlockId="gain-1",
            sourcePortId="gain-1-out-0",
            targetBlockId="out-1",
            targetPortId="out-1-in-0",
        )

        # Create subsystem with children
        subsystem = Block(
            id="sub-1",
            type="subsystem",
            name="Subsystem1",
            position=Position(x=100, y=100),
            parameters={},
            inputPorts=[Port(id="sub-1-in-0", name="in", dataType="double", dimensions=[1])],
            outputPorts=[Port(id="sub-1-out-0", name="out", dataType="double", dimensions=[1])],
            children=[inport, gain, outport],
            childConnections=[conn1, conn2],
        )

        blocks, connections = self.compiler._flatten_subsystems([subsystem], [])

        # Should have 3 child blocks (prefixed IDs)
        assert len(blocks) == 3
        block_ids = [b.id for b in blocks]
        assert "sub-1__in-1" in block_ids
        assert "sub-1__gain-1" in block_ids
        assert "sub-1__out-1" in block_ids


class TestMDLParserComplete:
    """Extended tests for MDL parser to achieve full coverage."""

    def test_parse_blocks_from_system(self):
        """Test parsing blocks from system data."""
        from src.parsers.mdl_parser import MDLParser

        parser = MDLParser()
        system_data = {
            "Block": [
                {"BlockType": "Constant", "Name": "Constant1", "Position": "[100, 100, 150, 130]", "Value": "5.0"},
                {"BlockType": "Gain", "Name": "Gain1", "Position": "[200, 100, 250, 130]", "Gain": "2.0"},
                {"BlockType": "Scope", "Name": "Scope1", "Position": "[300, 100, 350, 130]"},
            ]
        }

        blocks = parser._parse_blocks(system_data)
        assert len(blocks) == 3
        assert blocks[0].type == "constant"
        assert blocks[1].type == "gain"
        assert blocks[2].type == "scope"

    def test_parse_step_block_params(self):
        """Test parsing Step block parameters."""
        from src.parsers.mdl_parser import MDLParser

        parser = MDLParser()
        block_data = {
            "BlockType": "Step",
            "Name": "Step1",
            "Position": "[100, 100, 150, 130]",
            "Time": "1.0",
            "Before": "0",
            "After": "1"
        }

        block = parser._convert_block(block_data, 0)
        assert block is not None
        assert block.type == "step"
        assert block.parameters.get("stepTime") == 1.0
        assert block.parameters.get("initialValue") == 0.0
        assert block.parameters.get("finalValue") == 1.0

    def test_parse_sin_block_params(self):
        """Test parsing Sin (sine wave) block parameters."""
        from src.parsers.mdl_parser import MDLParser

        parser = MDLParser()
        block_data = {
            "BlockType": "Sin",
            "Name": "Sine1",
            "Position": "[100, 100, 150, 130]",
            "Amplitude": "2.0",
            "Frequency": "1.0",
            "Phase": "0.5",
            "Bias": "0.1"
        }

        block = parser._convert_block(block_data, 0)
        assert block is not None
        assert block.type == "sine_wave"
        assert block.parameters.get("amplitude") == 2.0
        assert block.parameters.get("frequency") == 1.0
        assert block.parameters.get("phase") == 0.5
        assert block.parameters.get("bias") == 0.1

    def test_parse_saturation_block_params(self):
        """Test parsing Saturation block parameters."""
        from src.parsers.mdl_parser import MDLParser

        parser = MDLParser()
        block_data = {
            "BlockType": "Saturation",
            "Name": "Sat1",
            "Position": "[100, 100, 150, 130]",
            "UpperLimit": "10",
            "LowerLimit": "-5"
        }

        block = parser._convert_block(block_data, 0)
        assert block is not None
        assert block.type == "saturation"
        assert block.parameters.get("upperLimit") == 10.0
        assert block.parameters.get("lowerLimit") == -5.0

    def test_parse_transfer_function_block_params(self):
        """Test parsing TransferFcn block parameters."""
        from src.parsers.mdl_parser import MDLParser

        parser = MDLParser()
        block_data = {
            "BlockType": "TransferFcn",
            "Name": "TF1",
            "Position": "[100, 100, 150, 130]",
            "Numerator": "[1, 2]",
            "Denominator": "[1, 3, 2]"
        }

        block = parser._convert_block(block_data, 0)
        assert block is not None
        assert block.type == "transfer_function"

    def test_parse_connections(self):
        """Test parsing connections from system data."""
        from src.parsers.mdl_parser import MDLParser
        from src.models.block import Block, Position, Port

        parser = MDLParser()

        # Create some blocks
        blocks = [
            Block(
                id="block-1",
                type="constant",
                name="Constant1",
                position=Position(x=100, y=100),
                parameters={},
                inputPorts=[],
                outputPorts=[Port(id="block-1-out-0", name="out", dataType="double", dimensions=[1])],
            ),
            Block(
                id="block-2",
                type="gain",
                name="Gain1",
                position=Position(x=200, y=100),
                parameters={},
                inputPorts=[Port(id="block-2-in-0", name="in", dataType="double", dimensions=[1])],
                outputPorts=[Port(id="block-2-out-0", name="out", dataType="double", dimensions=[1])],
            ),
        ]

        system_data = {
            "Line": {
                "SrcBlock": "Constant1",
                "SrcPort": "1",
                "DstBlock": "Gain1",
                "DstPort": "1",
            }
        }

        connections = parser._parse_connections(system_data, blocks)
        assert len(connections) == 1
        assert connections[0].source_block_id == "block-1"
        assert connections[0].target_block_id == "block-2"

    def test_parse_connection_invalid_source(self):
        """Test that connections with invalid source blocks are skipped."""
        from src.parsers.mdl_parser import MDLParser
        from src.models.block import Block, Position, Port

        parser = MDLParser()

        blocks = [
            Block(
                id="block-1",
                type="constant",
                name="Constant1",
                position=Position(x=100, y=100),
                parameters={},
                inputPorts=[Port(id="block-1-in-0", name="in", dataType="double", dimensions=[1])],
                outputPorts=[],
            ),
        ]

        system_data = {
            "Line": {
                "SrcBlock": "NonExistent",
                "SrcPort": "1",
                "DstBlock": "Constant1",
                "DstPort": "1",
            }
        }

        connections = parser._parse_connections(system_data, blocks)
        # Connection should be skipped since source block doesn't exist
        assert len(connections) == 0

    def test_parse_connection_invalid_port(self):
        """Test that connections with invalid port indices are skipped."""
        from src.parsers.mdl_parser import MDLParser
        from src.models.block import Block, Position, Port

        parser = MDLParser()

        blocks = [
            Block(
                id="block-1",
                type="constant",
                name="Constant1",
                position=Position(x=100, y=100),
                parameters={},
                inputPorts=[],
                outputPorts=[Port(id="block-1-out-0", name="out", dataType="double", dimensions=[1])],
            ),
            Block(
                id="block-2",
                type="gain",
                name="Gain1",
                position=Position(x=200, y=100),
                parameters={},
                inputPorts=[Port(id="block-2-in-0", name="in", dataType="double", dimensions=[1])],
                outputPorts=[],
            ),
        ]

        system_data = {
            "Line": {
                "SrcBlock": "Constant1",
                "SrcPort": "5",  # Invalid - only 1 output port
                "DstBlock": "Gain1",
                "DstPort": "1",
            }
        }

        connections = parser._parse_connections(system_data, blocks)
        assert len(connections) == 0

    def test_convert_block_integrator(self):
        """Test converting integrator block."""
        from src.parsers.mdl_parser import MDLParser

        parser = MDLParser()
        block_data = {
            "BlockType": "Integrator",
            "Name": "Int1",
            "Position": "[100, 100, 150, 130]",
            "InitialCondition": "0.5"
        }

        block = parser._convert_block(block_data, 0)
        assert block is not None
        assert block.type == "integrator"
        assert block.parameters.get("initialCondition") == 0.5
