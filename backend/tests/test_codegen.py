"""Unit tests for code generation module."""

import pytest
from src.codegen.generator import (
    CodeGenerator,
    CodeGenerationConfig,
    CodeGenerationError,
)
from src.codegen.models import (
    Language,
    IntegrationMethod,
    GeneratedProject,
    CompiledModelInfo,
    BlockInfo,
)
from src.codegen.integration import IntegrationCodeGenerator


class TestCodeGenerationConfig:
    """Tests for CodeGenerationConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = CodeGenerationConfig()
        assert config.language == Language.PYTHON
        assert config.integration_method == IntegrationMethod.RK4
        assert config.step_size == 0.01
        assert config.stop_time == 10.0
        assert config.start_time == 0.0
        assert config.project_name == "simulation"
        assert config.include_csv_output is True
        assert config.include_main is True
        assert config.optimization_level == 0

    def test_custom_config(self):
        """Test custom configuration values."""
        config = CodeGenerationConfig(
            language=Language.C,
            integration_method=IntegrationMethod.EULER,
            step_size=0.001,
            stop_time=5.0,
            start_time=1.0,
            project_name="my_sim",
        )
        assert config.language == Language.C
        assert config.integration_method == IntegrationMethod.EULER
        assert config.step_size == 0.001
        assert config.stop_time == 5.0
        assert config.start_time == 1.0
        assert config.project_name == "my_sim"


class TestGeneratedProject:
    """Tests for GeneratedProject class."""

    def test_add_file(self):
        """Test adding files to a project."""
        project = GeneratedProject(name="test", language=Language.PYTHON)
        project.add_file("main.py", "print('hello')")
        # files is a list of GeneratedFile objects
        assert len(project.files) == 1
        assert project.files[0].path == "main.py"
        assert project.files[0].content == "print('hello')"

    def test_get_file(self):
        """Test getting a file by path."""
        project = GeneratedProject(name="test", language=Language.C)
        project.add_file("src/main.c", "int main() {}")
        project.add_file("include/sim.h", "#ifndef SIM_H")

        # get_file returns GeneratedFile or None
        main_file = project.get_file("src/main.c")
        assert main_file is not None
        assert main_file.content == "int main() {}"

        header_file = project.get_file("include/sim.h")
        assert header_file is not None
        assert "#ifndef SIM_H" in header_file.content

        # Non-existent file returns None
        assert project.get_file("nonexistent.c") is None

    def test_file_paths(self):
        """Test getting file paths from project."""
        project = GeneratedProject(name="test", language=Language.C)
        project.add_file("src/main.c", "int main() {}")
        project.add_file("include/sim.h", "#ifndef SIM_H")

        # Get all file paths
        paths = [f.path for f in project.files]
        assert len(paths) == 2
        assert "src/main.c" in paths
        assert "include/sim.h" in paths


class TestIntegrationCodeGenerator:
    """Tests for integration code generators."""

    def test_get_passes(self):
        """Test getting number of passes for each method."""
        assert IntegrationCodeGenerator.get_passes(IntegrationMethod.EULER) == 1
        assert IntegrationCodeGenerator.get_passes(IntegrationMethod.RK2) == 2
        assert IntegrationCodeGenerator.get_passes(IntegrationMethod.RK4) == 4
        assert IntegrationCodeGenerator.get_passes(IntegrationMethod.MERSON) == 5

    def test_python_euler_generator(self):
        """Test Python Euler code generation."""
        code = IntegrationCodeGenerator.generate_python_euler()
        assert "def euler_propagate" in code
        assert "integ.state += dt * integ.derivative" in code

    def test_python_rk4_generator(self):
        """Test Python RK4 code generation."""
        code = IntegrationCodeGenerator.generate_python_rk4()
        assert "def rk4_propagate" in code
        assert "kpass == 0" in code
        assert "kpass == 3" in code
        # Uses integ.xd0, integ.xd1, etc. for the integrator objects
        assert "integ.xd0 + 2.0 * integ.xd1 + 2.0 * integ.xd2 + integ.xd3" in code

    def test_python_all_methods(self):
        """Test all Python methods generator."""
        code = IntegrationCodeGenerator.generate_python_all()
        assert "euler_propagate" in code
        assert "rk2_propagate" in code
        assert "rk4_propagate" in code
        assert "merson_propagate" in code
        assert "get_propagate_function" in code
        assert "get_num_passes" in code

    def test_c_header_generator(self):
        """Test C header generation."""
        code = IntegrationCodeGenerator.generate_c_header()
        assert "#ifndef INTEGRATION_H" in code
        assert "IntegratorState" in code
        assert "IntegrationMethod" in code
        assert "integration_get_passes" in code

    def test_c_source_generator(self):
        """Test C source generation."""
        code = IntegrationCodeGenerator.generate_c_source()
        assert "#include \"integration.h\"" in code
        assert "euler_propagate" in code
        assert "rk4_propagate" in code
        assert "integration_propagate" in code

    def test_cpp_header_generator(self):
        """Test C++ header generation."""
        code = IntegrationCodeGenerator.generate_cpp_header()
        assert "#ifndef INTEGRATION_HPP" in code
        assert "get_num_passes" in code
        assert "propagate_integrator" in code

    def test_cpp_source_generator(self):
        """Test C++ source generation."""
        code = IntegrationCodeGenerator.generate_cpp_source()
        assert "#include \"integration.hpp\"" in code
        assert "euler_step" in code
        assert "rk4_step" in code
        assert "merson_step" in code

    def test_rust_generator(self):
        """Test Rust integration code generation."""
        code = IntegrationCodeGenerator.generate_rust()
        assert "pub enum IntegrationMethod" in code
        assert "Euler" in code
        assert "Rk4" in code
        assert "fn euler_step" in code
        assert "fn rk4_step" in code
        assert "pub fn propagate_integrator" in code
        assert "pub fn get_num_passes" in code
        assert "from_str" in code


class TestCodeGenerator:
    """Tests for the main CodeGenerator class."""

    @pytest.fixture
    def generator(self):
        """Create a CodeGenerator instance."""
        return CodeGenerator()

    @pytest.fixture
    def simple_model(self):
        """Create a simple test model with step -> gain -> scope."""
        return {
            "id": "test-model-1",
            "metadata": {
                "name": "Test Model",
                "description": "A simple test model",
                "author": "Test",
                "version": "1.0.0",
            },
            "blocks": [
                {
                    "id": "step-1",
                    "type": "step",
                    "name": "Step",
                    "position": {"x": 100, "y": 100},
                    "parameters": {
                        "step_time": 1.0,
                        "initial_value": 0.0,
                        "final_value": 1.0,
                    },
                    "inputPorts": [],
                    "outputPorts": [{"id": "step-1-out-0", "name": "out"}],
                },
                {
                    "id": "gain-1",
                    "type": "gain",
                    "name": "Gain",
                    "position": {"x": 250, "y": 100},
                    "parameters": {"gain": 2.0},
                    "inputPorts": [{"id": "gain-1-in-0", "name": "in"}],
                    "outputPorts": [{"id": "gain-1-out-0", "name": "out"}],
                },
                {
                    "id": "scope-1",
                    "type": "scope",
                    "name": "Scope",
                    "position": {"x": 400, "y": 100},
                    "parameters": {},
                    "inputPorts": [{"id": "scope-1-in-0", "name": "in"}],
                    "outputPorts": [],
                },
            ],
            "connections": [
                {
                    "id": "conn-1",
                    "sourceBlockId": "step-1",
                    "sourcePortId": "step-1-out-0",
                    "targetBlockId": "gain-1",
                    "targetPortId": "gain-1-in-0",
                },
                {
                    "id": "conn-2",
                    "sourceBlockId": "gain-1",
                    "sourcePortId": "gain-1-out-0",
                    "targetBlockId": "scope-1",
                    "targetPortId": "scope-1-in-0",
                },
            ],
            "simulationConfig": {
                "startTime": 0.0,
                "stopTime": 10.0,
                "stepSize": 0.01,
                "solver": "rk4",
            },
        }

    def test_get_supported_languages(self, generator):
        """Test getting supported languages."""
        languages = generator.get_supported_languages()
        assert "python" in languages
        assert "c" in languages
        assert "cpp" in languages
        assert "rust" in languages

    def test_get_supported_methods(self, generator):
        """Test getting supported integration methods."""
        methods = generator.get_supported_methods()
        assert "euler" in methods
        assert "rk2" in methods
        assert "rk4" in methods
        assert "merson" in methods

    def _has_file(self, project, path: str) -> bool:
        """Helper to check if project has a file with given path."""
        return project.get_file(path) is not None

    def test_generate_python_project(self, generator, simple_model):
        """Test generating a Python project."""
        config = CodeGenerationConfig(
            language=Language.PYTHON,
            project_name="test_sim",
        )
        project = generator.generate(simple_model, config)

        assert project.name == "test_sim"
        assert project.language == Language.PYTHON
        assert self._has_file(project, "simulation.py")
        assert self._has_file(project, "blocks.py")
        assert self._has_file(project, "integration.py")
        assert self._has_file(project, "main.py")
        assert self._has_file(project, "requirements.txt")

    def test_generate_c_project(self, generator, simple_model):
        """Test generating a C project."""
        config = CodeGenerationConfig(
            language=Language.C,
            project_name="test_sim",
        )
        project = generator.generate(simple_model, config)

        assert project.name == "test_sim"
        assert project.language == Language.C
        assert self._has_file(project, "include/blocks.h")
        assert self._has_file(project, "include/simulation.h")
        assert self._has_file(project, "include/integration.h")
        assert self._has_file(project, "src/main.c")
        assert self._has_file(project, "CMakeLists.txt")

    def test_generate_cpp_project(self, generator, simple_model):
        """Test generating a C++ project."""
        config = CodeGenerationConfig(
            language=Language.CPP,
            project_name="test_sim",
        )
        project = generator.generate(simple_model, config)

        assert project.name == "test_sim"
        assert project.language == Language.CPP
        assert self._has_file(project, "include/blocks.hpp")
        assert self._has_file(project, "include/simulation.hpp")
        assert self._has_file(project, "include/integration.hpp")
        assert self._has_file(project, "src/main.cpp")
        assert self._has_file(project, "CMakeLists.txt")

    def test_generate_rust_project(self, generator, simple_model):
        """Test generating a Rust project."""
        config = CodeGenerationConfig(
            language=Language.RUST,
            project_name="test_sim",
        )
        project = generator.generate(simple_model, config)

        assert project.name == "test_sim"
        assert project.language == Language.RUST
        assert self._has_file(project, "src/lib.rs")
        assert self._has_file(project, "src/blocks.rs")
        assert self._has_file(project, "src/integration.rs")
        assert self._has_file(project, "src/main.rs")
        assert self._has_file(project, "Cargo.toml")

    def test_generate_without_main(self, generator, simple_model):
        """Test generating without main file."""
        config = CodeGenerationConfig(
            language=Language.PYTHON,
            include_main=False,
        )
        project = generator.generate(simple_model, config)
        assert not self._has_file(project, "main.py")

    def test_empty_model_fails(self, generator):
        """Test that empty model fails compilation."""
        empty_model = {
            "id": "empty-model",
            "metadata": {"name": "Empty", "description": ""},
            "blocks": [],
            "connections": [],
            "simulationConfig": {},
        }
        config = CodeGenerationConfig()

        with pytest.raises(CodeGenerationError) as exc_info:
            generator.generate(empty_model, config)
        assert "no blocks" in str(exc_info.value).lower()


class TestBlockTemplates:
    """Tests for block template generation."""

    @pytest.fixture
    def generator(self):
        """Create a CodeGenerator instance."""
        return CodeGenerator()

    @pytest.fixture
    def integrator_model(self):
        """Create a model with an integrator for integration testing."""
        return {
            "id": "integrator-model",
            "metadata": {"name": "Integrator Test", "description": ""},
            "blocks": [
                {
                    "id": "const-1",
                    "type": "constant",
                    "name": "Constant",
                    "position": {"x": 100, "y": 100},
                    "parameters": {"value": 1.0},
                    "inputPorts": [],
                    "outputPorts": [{"id": "const-1-out-0", "name": "out"}],
                },
                {
                    "id": "integ-1",
                    "type": "integrator",
                    "name": "Integrator",
                    "position": {"x": 250, "y": 100},
                    "parameters": {"initial_condition": 0.0},
                    "inputPorts": [{"id": "integ-1-in-0", "name": "in"}],
                    "outputPorts": [{"id": "integ-1-out-0", "name": "out"}],
                },
                {
                    "id": "scope-1",
                    "type": "scope",
                    "name": "Scope",
                    "position": {"x": 400, "y": 100},
                    "parameters": {},
                    "inputPorts": [{"id": "scope-1-in-0", "name": "in"}],
                    "outputPorts": [],
                },
            ],
            "connections": [
                {
                    "id": "conn-1",
                    "sourceBlockId": "const-1",
                    "sourcePortId": "const-1-out-0",
                    "targetBlockId": "integ-1",
                    "targetPortId": "integ-1-in-0",
                },
                {
                    "id": "conn-2",
                    "sourceBlockId": "integ-1",
                    "sourcePortId": "integ-1-out-0",
                    "targetBlockId": "scope-1",
                    "targetPortId": "scope-1-in-0",
                },
            ],
            "simulationConfig": {},
        }

    def test_python_integrator_template(self, generator, integrator_model):
        """Test that Python integrator template is generated correctly."""
        config = CodeGenerationConfig(language=Language.PYTHON)
        project = generator.generate(integrator_model, config)

        blocks_file = project.get_file("blocks.py")
        assert blocks_file is not None
        blocks_code = blocks_file.content
        assert "class Integrator" in blocks_code or "integ" in blocks_code.lower()

        # Check integration method support
        integration_file = project.get_file("integration.py")
        assert integration_file is not None
        assert "propagate" in integration_file.content

    def test_c_integrator_template(self, generator, integrator_model):
        """Test that C integrator template is generated correctly."""
        config = CodeGenerationConfig(language=Language.C)
        project = generator.generate(integrator_model, config)

        blocks_file = project.get_file("include/blocks.h")
        assert blocks_file is not None
        blocks_code = blocks_file.content
        # Should have integrator struct with state
        assert "state" in blocks_code or "State" in blocks_code

    def test_cpp_integrator_template(self, generator, integrator_model):
        """Test that C++ integrator template is generated correctly."""
        config = CodeGenerationConfig(language=Language.CPP)
        project = generator.generate(integrator_model, config)

        blocks_file = project.get_file("include/blocks.hpp")
        assert blocks_file is not None
        blocks_code = blocks_file.content
        assert "state" in blocks_code or "State" in blocks_code

    def test_rust_integrator_template(self, generator, integrator_model):
        """Test that Rust integrator template is generated correctly."""
        config = CodeGenerationConfig(language=Language.RUST)
        project = generator.generate(integrator_model, config)

        blocks_file = project.get_file("src/blocks.rs")
        assert blocks_file is not None
        blocks_code = blocks_file.content
        assert "state" in blocks_code or "State" in blocks_code


class TestLanguageEnums:
    """Tests for language and method enums."""

    def test_language_values(self):
        """Test language enum values."""
        assert Language.PYTHON.value == "python"
        assert Language.C.value == "c"
        assert Language.CPP.value == "cpp"
        assert Language.RUST.value == "rust"

    def test_integration_method_values(self):
        """Test integration method enum values."""
        assert IntegrationMethod.EULER.value == "euler"
        assert IntegrationMethod.RK2.value == "rk2"
        assert IntegrationMethod.RK4.value == "rk4"
        assert IntegrationMethod.MERSON.value == "merson"


class TestCompiledModelInfo:
    """Tests for CompiledModelInfo dataclass."""

    def test_compiled_model_info_creation(self):
        """Test creating CompiledModelInfo."""
        blocks = [
            BlockInfo(
                id="block-1",
                type="constant",
                name="Constant",
                parameters={"value": 1.0},
                input_connections=[],
                output_connections=["block-2:0"],
                execution_order=0,
            ),
            BlockInfo(
                id="block-2",
                type="scope",
                name="Scope",
                parameters={},
                input_connections=["block-1:0@0"],
                output_connections=[],
                execution_order=1,
            ),
        ]

        model_info = CompiledModelInfo(
            blocks=blocks,
            execution_order=["block-1", "block-2"],
            integrator_blocks=[],
            source_blocks=["block-1"],
            sink_blocks=["block-2"],
            step_size=0.01,
            stop_time=10.0,
            start_time=0.0,
        )

        assert len(model_info.blocks) == 2
        assert model_info.execution_order == ["block-1", "block-2"]
        assert model_info.source_blocks == ["block-1"]
        assert model_info.sink_blocks == ["block-2"]
