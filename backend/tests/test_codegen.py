"""Unit tests for code generation module."""

import pytest

from src.codegen.generator import (
    CodeGenerationConfig,
    CodeGenerationError,
    CodeGenerator,
)
from src.codegen.integration import IntegrationCodeGenerator
from src.codegen.models import (
    BlockInfo,
    CompiledModelInfo,
    GeneratedProject,
    IntegrationMethod,
    Language,
)


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
        assert "get_num_passes" in code
        assert "propagate_integrator" in code

    def test_c_source_generator(self):
        """Test C source generation."""
        code = IntegrationCodeGenerator.generate_c_source()
        assert '#include "integration.h"' in code
        assert "get_num_passes" in code
        assert "propagate_integrator" in code
        assert "euler" in code
        assert "rk4" in code

    def test_cpp_header_generator(self):
        """Test C++ header generation."""
        code = IntegrationCodeGenerator.generate_cpp_header()
        assert "#ifndef INTEGRATION_HPP" in code
        assert "get_num_passes" in code
        assert "propagate_integrator" in code

    def test_cpp_source_generator(self):
        """Test C++ source generation."""
        code = IntegrationCodeGenerator.generate_cpp_source()
        assert '#include "integration.hpp"' in code
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


class TestGeneratedProjectZip:
    """Tests for ZIP file generation."""

    def test_to_zip_creates_valid_zip(self):
        """Test that to_zip creates a valid ZIP archive."""
        import zipfile

        project = GeneratedProject(name="test_project", language=Language.PYTHON)
        project.add_file("main.py", "print('hello')")
        project.add_file("utils.py", "def helper(): pass")

        zip_buffer = project.to_zip()
        with zipfile.ZipFile(zip_buffer, "r") as zf:
            names = zf.namelist()
            assert "test_project/main.py" in names
            assert "test_project/utils.py" in names
            # Verify content
            content = zf.read("test_project/main.py").decode()
            assert "print('hello')" in content

    def test_to_zip_with_binary_file(self):
        """Test ZIP with binary files."""
        import zipfile

        project = GeneratedProject(name="test", language=Language.C)
        project.add_file("main.c", "int main() {}", is_binary=False)
        project.add_file("data.bin", "binary_content", is_binary=True)

        zip_buffer = project.to_zip()
        with zipfile.ZipFile(zip_buffer, "r") as zf:
            names = zf.namelist()
            assert "test/main.c" in names
            assert "test/data.bin" in names

    def test_to_zip_with_warnings(self):
        """Test project with warnings."""
        project = GeneratedProject(name="test", language=Language.PYTHON)
        project.warnings.append("Block X not fully supported")
        project.add_file("main.py", "# partial implementation")

        assert len(project.warnings) == 1
        assert "Block X" in project.warnings[0]


class TestCodegenControllerModels:
    """Tests for codegen controller request/response models."""

    def test_sanitize_project_name_basic(self):
        """Test basic project name sanitization."""
        from src.codegen.controller import sanitize_project_name

        assert sanitize_project_name("My Project") == "My_Project"
        assert sanitize_project_name("test-project") == "test_project"
        assert sanitize_project_name("test_project") == "test_project"

    def test_sanitize_project_name_special_chars(self):
        """Test sanitization of special characters."""
        from src.codegen.controller import sanitize_project_name

        assert sanitize_project_name("test@project!") == "testproject"
        assert sanitize_project_name("project#1") == "project1"
        assert sanitize_project_name("...project...") == "project"

    def test_sanitize_project_name_empty(self):
        """Test sanitization of empty/invalid names."""
        from src.codegen.controller import sanitize_project_name

        assert sanitize_project_name("") == "simulation"
        assert sanitize_project_name("@#$%") == "simulation"
        assert sanitize_project_name("   ") == "simulation"

    def test_codegen_request_defaults(self):
        """Test CodeGenRequest default values."""
        from src.codegen.controller import CodeGenRequest

        request = CodeGenRequest(model={"blocks": []})
        assert request.language == "python"
        assert request.integration_method == "rk4"
        assert request.step_size == 0.01
        assert request.stop_time == 10.0
        assert request.start_time == 0.0
        assert request.project_name == "simulation"
        assert request.include_csv_output is True
        assert request.include_main is True

    def test_codegen_request_custom(self):
        """Test CodeGenRequest with custom values."""
        from src.codegen.controller import CodeGenRequest

        request = CodeGenRequest(
            model={"blocks": []},
            language="c",
            integration_method="euler",
            step_size=0.001,
            stop_time=5.0,
            start_time=1.0,
            project_name="my_sim",
            include_csv_output=False,
            include_main=False,
        )
        assert request.language == "c"
        assert request.integration_method == "euler"
        assert request.step_size == 0.001
        assert request.stop_time == 5.0
        assert request.start_time == 1.0
        assert request.project_name == "my_sim"
        assert request.include_csv_output is False
        assert request.include_main is False


class TestCodegenModels:
    """Tests for codegen data models."""

    def test_signal_info(self):
        """Test SignalInfo dataclass."""
        from src.codegen.models import SignalInfo

        signal = SignalInfo(
            source_block_id="block-1",
            source_port=0,
            dimensions=[3],
            dtype="double",
        )
        assert signal.source_block_id == "block-1"
        assert signal.source_port == 0
        assert signal.dimensions == [3]
        assert signal.dtype == "double"

    def test_signal_info_defaults(self):
        """Test SignalInfo default values."""
        from src.codegen.models import SignalInfo

        signal = SignalInfo(
            source_block_id="block-1",
            source_port=0,
            dimensions=[1],
        )
        assert signal.dtype == "double"

    def test_block_template(self):
        """Test BlockTemplate dataclass."""
        from src.codegen.models import BlockTemplate

        template = BlockTemplate(
            block_type="gain",
            struct_definition="struct Gain { double k; };",
            init_code="block.k = 1.0;",
            update_code="output = input * block.k;",
            output_code="return output;",
            dependencies=["math.h"],
            num_states=0,
            has_state=False,
        )
        assert template.block_type == "gain"
        assert "struct Gain" in template.struct_definition
        assert template.dependencies == ["math.h"]
        assert template.num_states == 0
        assert template.has_state is False

    def test_block_template_defaults(self):
        """Test BlockTemplate default values."""
        from src.codegen.models import BlockTemplate

        template = BlockTemplate(
            block_type="test",
            struct_definition="",
            init_code="",
            update_code="",
            output_code="",
        )
        assert template.dependencies == []
        assert template.num_states == 0
        assert template.has_state is False

    def test_generated_file(self):
        """Test GeneratedFile dataclass."""
        from src.codegen.models import GeneratedFile

        file = GeneratedFile(
            path="src/main.c",
            content="int main() {}",
            is_binary=False,
        )
        assert file.path == "src/main.c"
        assert file.content == "int main() {}"
        assert file.is_binary is False

    def test_generated_file_defaults(self):
        """Test GeneratedFile default values."""
        from src.codegen.models import GeneratedFile

        file = GeneratedFile(path="test.py", content="pass")
        assert file.is_binary is False

    def test_block_info_with_dimensions(self):
        """Test BlockInfo with port dimensions."""
        info = BlockInfo(
            id="mux-1",
            type="mux",
            name="Mux",
            parameters={"numInputs": 2},
            input_connections=["const-1:0@0", "const-2:0@1"],
            output_connections=["scope-1:0"],
            execution_order=2,
            input_dimensions=[[1], [1]],
            output_dimensions=[[2]],
        )
        assert info.input_dimensions == [[1], [1]]
        assert info.output_dimensions == [[2]]

    def test_block_info_defaults(self):
        """Test BlockInfo default values."""
        info = BlockInfo(
            id="test",
            type="constant",
            name="Test",
            parameters={"value": 1},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        assert info.input_dimensions == []
        assert info.output_dimensions == []
        assert info.input_signals == []
        assert info.output_signals == []


class TestLanguageEnum:
    """Tests for Language enum."""

    def test_language_values(self):
        """Test Language enum values."""
        assert Language.PYTHON.value == "python"
        assert Language.C.value == "c"
        assert Language.CPP.value == "cpp"
        assert Language.RUST.value == "rust"

    def test_language_from_string(self):
        """Test creating Language from string."""
        assert Language("python") == Language.PYTHON
        assert Language("c") == Language.C
        assert Language("cpp") == Language.CPP
        assert Language("rust") == Language.RUST

    def test_language_invalid(self):
        """Test invalid Language value."""
        with pytest.raises(ValueError):
            Language("invalid")


class TestIntegrationMethodEnum:
    """Tests for IntegrationMethod enum."""

    def test_integration_method_values(self):
        """Test IntegrationMethod enum values."""
        assert IntegrationMethod.EULER.value == "euler"
        assert IntegrationMethod.RK2.value == "rk2"
        assert IntegrationMethod.RK4.value == "rk4"
        assert IntegrationMethod.MERSON.value == "merson"

    def test_integration_method_from_string(self):
        """Test creating IntegrationMethod from string."""
        assert IntegrationMethod("euler") == IntegrationMethod.EULER
        assert IntegrationMethod("rk4") == IntegrationMethod.RK4

    def test_integration_method_invalid(self):
        """Test invalid IntegrationMethod value."""
        with pytest.raises(ValueError):
            IntegrationMethod("invalid")


# =============================================================================
# Codegen Block Template Tests
# =============================================================================


class TestCMathOpsTemplates:
    """Tests for C math operations block templates."""

    def test_c_sum_template(self):
        """Test C Sum block template."""
        from src.codegen.languages.c.blocks.math_ops import template_sum

        block = BlockInfo(
            id="sum1",
            type="sum",
            name="Sum1",
            parameters={"signs": "+-"},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_sum(block, "Sum1_Block")
        assert "typedef struct" in code
        assert "Sum1_Block" in code
        assert "input0" in code
        assert "input1" in code
        assert "b->input0" in code
        assert "(-b->input1)" in code
        assert "_init" in code
        assert "_update" in code
        assert "_get_output" in code

    def test_c_sum_template_three_inputs(self):
        """Test C Sum block with three inputs."""
        from src.codegen.languages.c.blocks.math_ops import template_sum

        block = BlockInfo(
            id="sum2",
            type="sum",
            name="Sum2",
            parameters={"signs": "++-"},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_sum(block, "Sum2_Block")
        assert "input2" in code
        assert "b->input0" in code
        assert "b->input1" in code
        assert "(-b->input2)" in code

    def test_c_gain_template_scalar(self):
        """Test C Gain block template for scalar."""
        from src.codegen.languages.c.blocks.math_ops import template_gain

        block = BlockInfo(
            id="gain1",
            type="gain",
            name="Gain1",
            parameters={"gain": 2.5},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_gain(block, "Gain1_Block")
        assert "typedef struct" in code
        assert "2.5" in code
        assert "b->gain * b->input" in code
        assert "_init" in code
        assert "_update" in code

    def test_c_gain_template_vector(self):
        """Test C Gain block template for vector input."""
        from src.codegen.languages.c.blocks.math_ops import template_gain

        block = BlockInfo(
            id="gain2",
            type="gain",
            name="Gain2",
            parameters={"gain": 1.5},
            input_connections=[],
            output_connections=[],
            execution_order=0,
            input_dimensions=[[3]],
        )
        # Set the attribute that the template checks
        block.input_dimensions = [[3]]
        code = template_gain(block, "Gain2_Block")
        assert "double input[3]" in code
        assert "double output[3]" in code
        assert "get_output_vector" in code

    def test_c_product_template(self):
        """Test C Product block template."""
        from src.codegen.languages.c.blocks.math_ops import template_product

        block = BlockInfo(
            id="prod1",
            type="product",
            name="Product1",
            parameters={"inputs": "*/"},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_product(block, "Product1_Block")
        assert "typedef struct" in code
        assert "input0" in code
        assert "input1" in code
        assert "1.0 /" in code  # Division by input1

    def test_c_abs_template(self):
        """Test C Abs block template."""
        from src.codegen.languages.c.blocks.math_ops import template_abs

        block = BlockInfo(
            id="abs1",
            type="abs",
            name="Abs1",
            parameters={},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_abs(block, "Abs1_Block")
        assert "fabs(b->input)" in code

    def test_c_sign_template(self):
        """Test C Sign block template."""
        from src.codegen.languages.c.blocks.math_ops import template_sign

        block = BlockInfo(
            id="sign1",
            type="sign",
            name="Sign1",
            parameters={},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_sign(block, "Sign1_Block")
        assert "b->input > 0" in code
        assert "b->input < 0" in code
        assert "b->output = 1.0" in code
        assert "b->output = -1.0" in code
        assert "b->output = 0.0" in code

    def test_c_bias_template(self):
        """Test C Bias block template."""
        from src.codegen.languages.c.blocks.math_ops import template_bias

        block = BlockInfo(
            id="bias1",
            type="bias",
            name="Bias1",
            parameters={"bias": 5.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_bias(block, "Bias1_Block")
        assert "5.0" in code
        assert "b->input + b->bias" in code

    def test_c_saturation_template(self):
        """Test C Saturation block template."""
        from src.codegen.languages.c.blocks.math_ops import template_saturation

        block = BlockInfo(
            id="sat1",
            type="saturation",
            name="Saturation1",
            parameters={"upperLimit": 10.0, "lowerLimit": -10.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_saturation(block, "Saturation1_Block")
        assert "10.0" in code
        assert "-10.0" in code
        assert "b->upper" in code
        assert "b->lower" in code

    def test_c_dead_zone_template(self):
        """Test C Dead Zone block template."""
        from src.codegen.languages.c.blocks.math_ops import template_dead_zone

        block = BlockInfo(
            id="dz1",
            type="dead_zone",
            name="DeadZone1",
            parameters={"start": -1.0, "end": 1.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_dead_zone(block, "DeadZone1_Block")
        assert "-1.0" in code
        assert "zone_start" in code
        assert "zone_end" in code
        assert "b->zone_end" in code
        assert "b->zone_start" in code

    def test_c_switch_template(self):
        """Test C Switch block template."""
        from src.codegen.languages.c.blocks.math_ops import template_switch

        block = BlockInfo(
            id="switch1",
            type="switch",
            name="Switch1",
            parameters={"threshold": 0.5},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_switch(block, "Switch1_Block")
        assert "0.5" in code
        assert "threshold" in code
        assert "input0" in code
        assert "input1" in code
        assert "input2" in code
        assert ">= b->threshold" in code

    def test_c_math_function_template(self):
        """Test C Math Function block templates for different functions."""
        from src.codegen.languages.c.blocks.math_ops import template_math_function

        for func, expected in [
            ("exp", "exp(b->input)"),
            ("log", "log(b->input)"),
            ("log10", "log10(b->input)"),
            ("sqrt", "sqrt(b->input)"),
            ("square", "(b->input * b->input)"),
            ("reciprocal", "1.0 / "),
        ]:
            block = BlockInfo(
                id=f"math_{func}",
                type="math_function",
                name=f"Math_{func}",
                parameters={"function": func},
                input_connections=[],
                output_connections=[],
                execution_order=0,
            )
            code = template_math_function(block, f"Math_{func}_Block")
            assert expected in code

    def test_c_trigonometry_template(self):
        """Test C Trigonometry block templates for different functions."""
        from src.codegen.languages.c.blocks.math_ops import template_trigonometry

        for func in ["sin", "cos", "tan", "asin", "acos", "atan", "sinh", "cosh", "tanh"]:
            block = BlockInfo(
                id=f"trig_{func}",
                type="trigonometry",
                name=f"Trig_{func}",
                parameters={"function": func},
                input_connections=[],
                output_connections=[],
                execution_order=0,
            )
            code = template_trigonometry(block, f"Trig_{func}_Block")
            assert f"{func}(b->input)" in code

    def test_c_mux_template(self):
        """Test C Mux block template."""
        from src.codegen.languages.c.blocks.math_ops import template_mux

        block = BlockInfo(
            id="mux1",
            type="mux",
            name="Mux1",
            parameters={"numInputs": 3},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_mux(block, "Mux1_Block")
        assert "input0" in code
        assert "input1" in code
        assert "input2" in code
        assert "double output[3]" in code
        assert "get_output_vector" in code

    def test_c_demux_template(self):
        """Test C Demux block template."""
        from src.codegen.languages.c.blocks.math_ops import template_demux

        block = BlockInfo(
            id="demux1",
            type="demux",
            name="Demux1",
            parameters={"numOutputs": 2},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_demux(block, "Demux1_Block")
        assert "output0" in code
        assert "output1" in code
        assert "num_outputs" in code

    def test_c_math_templates_registry(self):
        """Test that C MATH_TEMPLATES registry has all expected entries."""
        from src.codegen.languages.c.blocks.math_ops import MATH_TEMPLATES

        expected = [
            "sum",
            "gain",
            "product",
            "abs",
            "sign",
            "bias",
            "saturation",
            "dead_zone",
            "switch",
            "math_function",
            "trigonometry",
            "mux",
            "demux",
        ]
        for key in expected:
            assert key in MATH_TEMPLATES


class TestPythonMathOpsTemplates:
    """Tests for Python math operations block templates."""

    def test_python_sum_template(self):
        """Test Python Sum block template."""
        from src.codegen.languages.python.blocks.math_ops import sum_template

        block = BlockInfo(
            id="sum1",
            type="sum",
            name="Sum1",
            parameters={"signs": "+-"},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = sum_template(block, "Sum1Class")
        assert "class Sum1Class" in code
        assert "self.input0" in code
        assert "self.input1" in code
        assert "-self.input1" in code

    def test_python_gain_template(self):
        """Test Python Gain block template."""
        from src.codegen.languages.python.blocks.math_ops import gain_template

        block = BlockInfo(
            id="gain1",
            type="gain",
            name="Gain1",
            parameters={"gain": 3.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = gain_template(block, "Gain1Class")
        assert "class Gain1Class" in code
        assert "self.gain = 3.0" in code
        assert "isinstance(self.input, (list, tuple))" in code
        assert "get_output_vector" in code

    def test_python_product_template(self):
        """Test Python Product block template."""
        from src.codegen.languages.python.blocks.math_ops import product_template

        block = BlockInfo(
            id="prod1",
            type="product",
            name="Product1",
            parameters={"operations": "*/"},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = product_template(block, "Product1Class")
        assert "class Product1Class" in code
        assert "result = 1.0" in code
        assert "result *=" in code
        assert "result /=" in code

    def test_python_abs_template(self):
        """Test Python Abs block template."""
        from src.codegen.languages.python.blocks.math_ops import abs_template

        block = BlockInfo(
            id="abs1",
            type="abs",
            name="Abs1",
            parameters={},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = abs_template(block, "Abs1Class")
        assert "abs(self.input)" in code

    def test_python_sign_template(self):
        """Test Python Sign block template."""
        from src.codegen.languages.python.blocks.math_ops import sign_template

        block = BlockInfo(
            id="sign1",
            type="sign",
            name="Sign1",
            parameters={},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = sign_template(block, "Sign1Class")
        assert "if self.input > 0" in code
        assert "self.output = 1.0" in code
        assert "self.output = -1.0" in code

    def test_python_bias_template(self):
        """Test Python Bias block template."""
        from src.codegen.languages.python.blocks.math_ops import bias_template

        block = BlockInfo(
            id="bias1",
            type="bias",
            name="Bias1",
            parameters={"bias": 2.5},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = bias_template(block, "Bias1Class")
        assert "self.bias = 2.5" in code
        assert "self.input + self.bias" in code

    def test_python_saturation_template(self):
        """Test Python Saturation block template."""
        from src.codegen.languages.python.blocks.math_ops import saturation_template

        block = BlockInfo(
            id="sat1",
            type="saturation",
            name="Sat1",
            parameters={"upperLimit": 5.0, "lowerLimit": -5.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = saturation_template(block, "Sat1Class")
        assert "self.upper_limit = 5.0" in code
        assert "self.lower_limit = -5.0" in code

    def test_python_dead_zone_template(self):
        """Test Python Dead Zone block template."""
        from src.codegen.languages.python.blocks.math_ops import dead_zone_template

        block = BlockInfo(
            id="dz1",
            type="dead_zone",
            name="DeadZone1",
            parameters={"start": -0.5, "end": 0.5},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = dead_zone_template(block, "DeadZone1Class")
        assert "self.start = -0.5" in code
        assert "self.end = 0.5" in code

    def test_python_switch_template(self):
        """Test Python Switch block template."""
        from src.codegen.languages.python.blocks.math_ops import switch_template

        block = BlockInfo(
            id="switch1",
            type="switch",
            name="Switch1",
            parameters={"threshold": 1.0, "criteria": ">="},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = switch_template(block, "Switch1Class")
        assert "self.threshold = 1.0" in code
        assert 'self.criteria = ">="' in code
        assert "self.input0" in code
        assert "self.input1" in code
        assert "self.input2" in code

    def test_python_math_function_template(self):
        """Test Python Math Function block templates."""
        from src.codegen.languages.python.blocks.math_ops import math_function_template

        for func, expected in [
            ("exp", "math.exp(self.input)"),
            ("log", "math.log(self.input)"),
            ("sqrt", "math.sqrt(abs(self.input))"),
            ("square", "self.input ** 2"),
        ]:
            block = BlockInfo(
                id=f"math_{func}",
                type="math_function",
                name=f"Math_{func}",
                parameters={"function": func},
                input_connections=[],
                output_connections=[],
                execution_order=0,
            )
            code = math_function_template(block, f"Math{func}Class")
            assert expected in code

    def test_python_trigonometry_template(self):
        """Test Python Trigonometry block templates."""
        from src.codegen.languages.python.blocks.math_ops import trigonometry_template

        for func in ["sin", "cos", "tan", "sinh", "cosh", "tanh"]:
            block = BlockInfo(
                id=f"trig_{func}",
                type="trigonometry",
                name=f"Trig_{func}",
                parameters={"function": func},
                input_connections=[],
                output_connections=[],
                execution_order=0,
            )
            code = trigonometry_template(block, f"Trig{func}Class")
            assert f"math.{func}(self.input)" in code

    def test_python_trigonometry_atan2_template(self):
        """Test Python Trigonometry atan2 template."""
        from src.codegen.languages.python.blocks.math_ops import trigonometry_template

        block = BlockInfo(
            id="trig_atan2",
            type="trigonometry",
            name="Trig_atan2",
            parameters={"function": "atan2"},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = trigonometry_template(block, "TrigAtan2Class")
        assert "self.input1 = 0.0" in code
        assert "math.atan2(self.input, self.input1)" in code

    def test_python_mux_template(self):
        """Test Python Mux block template."""
        from src.codegen.languages.python.blocks.math_ops import mux_template

        block = BlockInfo(
            id="mux1",
            type="mux",
            name="Mux1",
            parameters={"numInputs": 4},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = mux_template(block, "Mux1Class")
        assert "self.num_inputs = 4" in code
        assert "self.input0" in code
        assert "self.input1" in code
        assert "self.input2" in code
        assert "self.input3" in code
        assert "get_output_vector" in code

    def test_python_demux_template(self):
        """Test Python Demux block template."""
        from src.codegen.languages.python.blocks.math_ops import demux_template

        block = BlockInfo(
            id="demux1",
            type="demux",
            name="Demux1",
            parameters={"numOutputs": 3},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = demux_template(block, "Demux1Class")
        assert "self.num_outputs = 3" in code
        assert "self.outputs" in code
        assert "get_output_vector" in code

    def test_python_math_templates_registry(self):
        """Test that Python MATH_TEMPLATES registry has all expected entries."""
        from src.codegen.languages.python.blocks.math_ops import MATH_TEMPLATES

        expected = [
            "sum",
            "gain",
            "product",
            "abs",
            "sign",
            "bias",
            "saturation",
            "dead_zone",
            "switch",
            "math_function",
            "trigonometry",
            "mux",
            "demux",
        ]
        for key in expected:
            assert key in MATH_TEMPLATES


class TestCSourceTemplates:
    """Tests for C source block templates."""

    def test_c_constant_template(self):
        """Test C Constant block template."""
        from src.codegen.languages.c.blocks.sources import template_constant

        block = BlockInfo(
            id="const1",
            type="constant",
            name="Constant1",
            parameters={"value": 42.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_constant(block, "Const1_Block")
        assert "42.0" in code
        assert "typedef struct" in code

    def test_c_step_template(self):
        """Test C Step block template."""
        from src.codegen.languages.c.blocks.sources import template_step

        block = BlockInfo(
            id="step1",
            type="step",
            name="Step1",
            parameters={"step_time": 1.0, "initial_value": 0.0, "final_value": 1.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_step(block, "Step1_Block")
        assert "step_time" in code
        assert "1.0" in code
        assert "initial" in code.lower() or "final" in code.lower()

    def test_c_ramp_template(self):
        """Test C Ramp block template."""
        from src.codegen.languages.c.blocks.sources import template_ramp

        block = BlockInfo(
            id="ramp1",
            type="ramp",
            name="Ramp1",
            parameters={"slope": 2.0, "start_time": 0.5, "initial_output": 0.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_ramp(block, "Ramp1_Block")
        assert "slope" in code
        assert "2.0" in code

    def test_c_sine_wave_template(self):
        """Test C Sine Wave block template."""
        from src.codegen.languages.c.blocks.sources import template_sine_wave

        block = BlockInfo(
            id="sine1",
            type="sine_wave",
            name="Sine1",
            parameters={"amplitude": 1.0, "frequency": 10.0, "phase": 0.0, "bias": 0.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_sine_wave(block, "Sine1_Block")
        assert "amplitude" in code
        assert "frequency" in code
        assert "sin(" in code

    def test_c_clock_template(self):
        """Test C Clock block template."""
        from src.codegen.languages.c.blocks.sources import template_clock

        block = BlockInfo(
            id="clock1",
            type="clock",
            name="Clock1",
            parameters={},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_clock(block, "Clock1_Block")
        assert "output = t" in code or "b->output = t" in code

    def test_c_pulse_template(self):
        """Test C Pulse block template."""
        from src.codegen.languages.c.blocks.sources import template_pulse

        block = BlockInfo(
            id="pulse1",
            type="pulse",
            name="Pulse1",
            parameters={"amplitude": 1.0, "period": 1.0, "pulse_width": 50, "phase_delay": 0.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_pulse(block, "Pulse1_Block")
        assert "period" in code
        assert "amplitude" in code

    def test_c_ground_template(self):
        """Test C Ground block template."""
        from src.codegen.languages.c.blocks.sources import template_ground

        block = BlockInfo(
            id="ground1",
            type="ground",
            name="Ground1",
            parameters={},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_ground(block, "Ground1_Block")
        assert "typedef struct" in code
        assert "0.0" in code

    def test_c_white_noise_template(self):
        """Test C White Noise block template."""
        from src.codegen.languages.c.blocks.sources import template_white_noise

        block = BlockInfo(
            id="noise1",
            type="white_noise",
            name="WhiteNoise1",
            parameters={"power": 0.1, "sample_time": 0.01},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_white_noise(block, "WhiteNoise1_Block")
        assert "typedef struct" in code


class TestPythonSourceTemplates:
    """Tests for Python source block templates."""

    def test_python_constant_template(self):
        """Test Python Constant block template."""
        from src.codegen.languages.python.blocks.sources import constant_template

        block = BlockInfo(
            id="const1",
            type="constant",
            name="Constant1",
            parameters={"value": 3.14},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = constant_template(block, "Const1Class")
        assert "class Const1Class" in code
        assert "3.14" in code

    def test_python_step_template(self):
        """Test Python Step block template."""
        from src.codegen.languages.python.blocks.sources import step_template

        block = BlockInfo(
            id="step1",
            type="step",
            name="Step1",
            parameters={"step_time": 2.0, "initial_value": 0.0, "final_value": 5.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = step_template(block, "Step1Class")
        assert "class Step1Class" in code
        assert "step_time" in code
        assert "2.0" in code

    def test_python_ramp_template(self):
        """Test Python Ramp block template."""
        from src.codegen.languages.python.blocks.sources import ramp_template

        block = BlockInfo(
            id="ramp1",
            type="ramp",
            name="Ramp1",
            parameters={"slope": 1.5, "start_time": 0.0, "initial_output": 0.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = ramp_template(block, "Ramp1Class")
        assert "class Ramp1Class" in code
        assert "slope" in code

    def test_python_sine_wave_template(self):
        """Test Python Sine Wave block template."""
        from src.codegen.languages.python.blocks.sources import sine_wave_template

        block = BlockInfo(
            id="sine1",
            type="sine_wave",
            name="Sine1",
            parameters={"amplitude": 2.0, "frequency": 5.0, "phase": 0.0, "bias": 1.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = sine_wave_template(block, "Sine1Class")
        assert "class Sine1Class" in code
        assert "amplitude" in code
        assert "frequency" in code
        assert "math.sin" in code

    def test_python_clock_template(self):
        """Test Python Clock block template."""
        from src.codegen.languages.python.blocks.sources import clock_template

        block = BlockInfo(
            id="clock1",
            type="clock",
            name="Clock1",
            parameters={},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = clock_template(block, "Clock1Class")
        assert "class Clock1Class" in code
        assert "self.output = t" in code


class TestCSinkTemplates:
    """Tests for C sink block templates."""

    def test_c_scope_template(self):
        """Test C Scope block template."""
        from src.codegen.languages.c.blocks.sinks import template_scope

        block = BlockInfo(
            id="scope1",
            type="scope",
            name="Scope1",
            parameters={"numInputs": 2},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_scope(block, "Scope1_Block")
        assert "typedef struct" in code
        assert "_init" in code
        assert "_update" in code

    def test_c_to_workspace_template(self):
        """Test C ToWorkspace block template."""
        from src.codegen.languages.c.blocks.sinks import template_to_workspace

        block = BlockInfo(
            id="ws1",
            type="to_workspace",
            name="ToWorkspace1",
            parameters={"variable_name": "output_data"},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_to_workspace(block, "ToWorkspace1_Block")
        assert "typedef struct" in code

    def test_c_terminator_template(self):
        """Test C Terminator block template."""
        from src.codegen.languages.c.blocks.sinks import template_terminator

        block = BlockInfo(
            id="term1",
            type="terminator",
            name="Terminator1",
            parameters={},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_terminator(block, "Terminator1_Block")
        assert "typedef struct" in code


class TestPythonSinkTemplates:
    """Tests for Python sink block templates."""

    def test_python_scope_template(self):
        """Test Python Scope block template."""
        from src.codegen.languages.python.blocks.sinks import scope_template

        block = BlockInfo(
            id="scope1",
            type="scope",
            name="Scope1",
            parameters={"numInputs": 2},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = scope_template(block, "Scope1Class")
        assert "class Scope1Class" in code
        # Check for scope functionality - it has outputs for pass-through
        assert "outputs" in code

    def test_python_to_workspace_template(self):
        """Test Python ToWorkspace block template."""
        from src.codegen.languages.python.blocks.sinks import to_workspace_template

        block = BlockInfo(
            id="ws1",
            type="to_workspace",
            name="ToWorkspace1",
            parameters={"variable_name": "sim_out"},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = to_workspace_template(block, "ToWorkspace1Class")
        assert "class ToWorkspace1Class" in code

    def test_python_terminator_template(self):
        """Test Python Terminator block template."""
        from src.codegen.languages.python.blocks.sinks import terminator_template

        block = BlockInfo(
            id="term1",
            type="terminator",
            name="Terminator1",
            parameters={},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = terminator_template(block, "Terminator1Class")
        assert "class Terminator1Class" in code


class TestCContinuousTemplates:
    """Tests for C continuous block templates."""

    def test_c_integrator_template(self):
        """Test C Integrator block template."""
        from src.codegen.languages.c.blocks.continuous import template_integrator

        block = BlockInfo(
            id="integ1",
            type="integrator",
            name="Integrator1",
            parameters={"initial_condition": 0.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_integrator(block, "Integrator1_Block")
        assert "typedef struct" in code
        assert "state" in code
        assert "derivative" in code

    def test_c_derivative_template(self):
        """Test C Derivative block template."""
        from src.codegen.languages.c.blocks.continuous import template_derivative

        block = BlockInfo(
            id="deriv1",
            type="derivative",
            name="Derivative1",
            parameters={},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_derivative(block, "Derivative1_Block")
        assert "typedef struct" in code
        assert "prev" in code

    def test_c_transfer_function_template(self):
        """Test C Transfer Function block template."""
        from src.codegen.languages.c.blocks.continuous import template_transfer_function

        block = BlockInfo(
            id="tf1",
            type="transfer_function",
            name="TransferFunction1",
            parameters={"numerator": [1.0], "denominator": [1.0, 1.0]},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_transfer_function(block, "TransferFcn1_Block")
        assert "typedef struct" in code
        assert "state" in code


class TestPythonContinuousTemplates:
    """Tests for Python continuous block templates."""

    def test_python_integrator_template(self):
        """Test Python Integrator block template."""
        from src.codegen.languages.python.blocks.continuous import integrator_template

        block = BlockInfo(
            id="integ1",
            type="integrator",
            name="Integrator1",
            parameters={"initial_condition": 1.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = integrator_template(block, "Integrator1Class")
        assert "class Integrator1Class" in code
        assert "state" in code
        assert "derivative" in code

    def test_python_derivative_template(self):
        """Test Python Derivative block template."""
        from src.codegen.languages.python.blocks.continuous import derivative_template

        block = BlockInfo(
            id="deriv1",
            type="derivative",
            name="Derivative1",
            parameters={},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = derivative_template(block, "Derivative1Class")
        assert "class Derivative1Class" in code
        assert "prev" in code

    def test_python_transfer_function_template(self):
        """Test Python Transfer Function block template."""
        from src.codegen.languages.python.blocks.continuous import transfer_function_template

        block = BlockInfo(
            id="tf1",
            type="transfer_function",
            name="TransferFunction1",
            parameters={"numerator": [1.0], "denominator": [1.0, 0.5]},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = transfer_function_template(block, "TransferFcn1Class")
        assert "class TransferFcn1Class" in code
        assert "state" in code


class TestCDiscreteTemplates:
    """Tests for C discrete block templates."""

    def test_c_unit_delay_template(self):
        """Test C Unit Delay block template."""
        from src.codegen.languages.c.blocks.discrete import unit_delay_template

        block = BlockInfo(
            id="ud1",
            type="unit_delay",
            name="UnitDelay1",
            parameters={"initial_condition": 0.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = unit_delay_template(block, "UnitDelay1_Block")
        assert "typedef struct" in code
        assert "prev" in code

    def test_c_discrete_integrator_template(self):
        """Test C Discrete Integrator block template."""
        from src.codegen.languages.c.blocks.discrete import discrete_integrator_template

        block = BlockInfo(
            id="di1",
            type="discrete_integrator",
            name="DiscreteIntegrator1",
            parameters={"initial_condition": 0.0, "sample_time": 0.01},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = discrete_integrator_template(block, "DiscreteIntegrator1_Block")
        assert "typedef struct" in code
        assert "state" in code

    def test_c_zero_order_hold_template(self):
        """Test C Zero Order Hold block template."""
        from src.codegen.languages.c.blocks.discrete import zero_order_hold_template

        block = BlockInfo(
            id="zoh1",
            type="zero_order_hold",
            name="ZOH1",
            parameters={"sample_time": 0.01},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = zero_order_hold_template(block, "ZOH1_Block")
        assert "typedef struct" in code

    def test_c_memory_template(self):
        """Test C Memory block template."""
        from src.codegen.languages.c.blocks.discrete import memory_template

        block = BlockInfo(
            id="mem1",
            type="memory",
            name="Memory1",
            parameters={"initial_condition": 0.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = memory_template(block, "Memory1_Block")
        assert "typedef struct" in code


class TestPythonDiscreteTemplates:
    """Tests for Python discrete block templates."""

    def test_python_unit_delay_template(self):
        """Test Python Unit Delay block template."""
        from src.codegen.languages.python.blocks.discrete import unit_delay_template

        block = BlockInfo(
            id="ud1",
            type="unit_delay",
            name="UnitDelay1",
            parameters={"initial_condition": 0.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = unit_delay_template(block, "UnitDelay1Class")
        assert "class UnitDelay1Class" in code
        assert "prev" in code

    def test_python_discrete_integrator_template(self):
        """Test Python Discrete Integrator block template."""
        from src.codegen.languages.python.blocks.discrete import discrete_integrator_template

        block = BlockInfo(
            id="di1",
            type="discrete_integrator",
            name="DiscreteIntegrator1",
            parameters={"initial_condition": 0.0, "sample_time": 0.01},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = discrete_integrator_template(block, "DiscreteIntegrator1Class")
        assert "class DiscreteIntegrator1Class" in code
        assert "state" in code

    def test_python_memory_template(self):
        """Test Python Memory block template."""
        from src.codegen.languages.python.blocks.discrete import memory_template

        block = BlockInfo(
            id="mem1",
            type="memory",
            name="Memory1",
            parameters={"initial_condition": 0.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = memory_template(block, "Memory1Class")
        assert "class Memory1Class" in code


class TestCLogicTemplates:
    """Tests for C logic block templates."""

    def test_c_compare_to_zero_template(self):
        """Test C Compare to Zero block template."""
        from src.codegen.languages.c.blocks.logic import template_compare_to_zero

        block = BlockInfo(
            id="cmp1",
            type="compare_to_zero",
            name="CompareToZero1",
            parameters={"operator": ">="},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_compare_to_zero(block, "CompareToZero1_Block")
        assert "typedef struct" in code
        assert ">=" in code or "operator" in code

    def test_c_compare_to_constant_template(self):
        """Test C Compare to Constant block template."""
        from src.codegen.languages.c.blocks.logic import template_compare_to_constant

        block = BlockInfo(
            id="cmp2",
            type="compare_to_constant",
            name="CompareToConst1",
            parameters={"operator": ">", "value": 5.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_compare_to_constant(block, "CompareToConst1_Block")
        assert "typedef struct" in code

    def test_c_logical_operator_template(self):
        """Test C Logical Operator block template."""
        from src.codegen.languages.c.blocks.logic import template_logical_operator

        block = BlockInfo(
            id="logic1",
            type="logical_operator",
            name="LogicalOp1",
            parameters={"operator": "AND", "numInputs": 2},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_logical_operator(block, "LogicalOp1_Block")
        assert "typedef struct" in code
        assert "&&" in code or "AND" in code

    def test_c_relational_operator_template(self):
        """Test C Relational Operator block template."""
        from src.codegen.languages.c.blocks.logic import template_relational_operator

        block = BlockInfo(
            id="rel1",
            type="relational_operator",
            name="RelationalOp1",
            parameters={"operator": "<="},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_relational_operator(block, "RelationalOp1_Block")
        assert "typedef struct" in code


class TestPythonLogicTemplates:
    """Tests for Python logic block templates."""

    def test_python_compare_to_zero_template(self):
        """Test Python Compare to Zero block template."""
        from src.codegen.languages.python.blocks.logic import compare_to_zero_template

        block = BlockInfo(
            id="cmp1",
            type="compare_to_zero",
            name="CompareToZero1",
            parameters={"operator": ">"},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = compare_to_zero_template(block, "CompareToZero1Class")
        assert "class CompareToZero1Class" in code

    def test_python_compare_to_constant_template(self):
        """Test Python Compare to Constant block template."""
        from src.codegen.languages.python.blocks.logic import compare_to_constant_template

        block = BlockInfo(
            id="cmp2",
            type="compare_to_constant",
            name="CompareToConst1",
            parameters={"operator": ">=", "value": 10.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = compare_to_constant_template(block, "CompareToConst1Class")
        assert "class CompareToConst1Class" in code

    def test_python_logical_operator_template(self):
        """Test Python Logical Operator block template."""
        from src.codegen.languages.python.blocks.logic import logical_operator_template

        block = BlockInfo(
            id="logic1",
            type="logical_operator",
            name="LogicalOp1",
            parameters={"operator": "OR", "numInputs": 2},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = logical_operator_template(block, "LogicalOp1Class")
        assert "class LogicalOp1Class" in code

    def test_python_relational_operator_template(self):
        """Test Python Relational Operator block template."""
        from src.codegen.languages.python.blocks.logic import relational_operator_template

        block = BlockInfo(
            id="rel1",
            type="relational_operator",
            name="RelationalOp1",
            parameters={"operator": "!="},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = relational_operator_template(block, "RelationalOp1Class")
        assert "class RelationalOp1Class" in code


class TestRustMathOpsTemplates:
    """Tests for Rust math operations block templates."""

    def test_rust_sum_template(self):
        """Test Rust Sum block template."""
        from src.codegen.languages.rust.blocks.math_ops import template_sum

        block = BlockInfo(
            id="sum1",
            type="sum",
            name="Sum1",
            parameters={"signs": "+-"},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_sum(block, "Sum1Block")
        assert "struct Sum1Block" in code or "Sum1Block" in code
        assert "input0" in code
        assert "input1" in code
        assert "fn " in code

    def test_rust_gain_template(self):
        """Test Rust Gain block template."""
        from src.codegen.languages.rust.blocks.math_ops import template_gain

        block = BlockInfo(
            id="gain1",
            type="gain",
            name="Gain1",
            parameters={"gain": 2.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_gain(block, "Gain1Block")
        assert "struct" in code or "Gain1Block" in code
        assert "2.0" in code
        assert "gain" in code.lower()

    def test_rust_product_template(self):
        """Test Rust Product block template."""
        from src.codegen.languages.rust.blocks.math_ops import template_product

        block = BlockInfo(
            id="prod1",
            type="product",
            name="Product1",
            parameters={"inputs": "**"},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_product(block, "Product1Block")
        assert "struct" in code or "Product1Block" in code

    def test_rust_abs_template(self):
        """Test Rust Abs block template."""
        from src.codegen.languages.rust.blocks.math_ops import template_abs

        block = BlockInfo(
            id="abs1",
            type="abs",
            name="Abs1",
            parameters={},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_abs(block, "Abs1Block")
        assert "abs" in code.lower()

    def test_rust_math_templates_registry(self):
        """Test that Rust MATH_TEMPLATES registry has expected entries."""
        from src.codegen.languages.rust.blocks.math_ops import MATH_TEMPLATES

        expected = ["sum", "gain", "product", "abs"]
        for key in expected:
            assert key in MATH_TEMPLATES


class TestCppMathOpsTemplates:
    """Tests for C++ math operations block templates."""

    def test_cpp_sum_template(self):
        """Test C++ Sum block template."""
        from src.codegen.languages.cpp.blocks.math_ops import template_sum

        block = BlockInfo(
            id="sum1",
            type="sum",
            name="Sum1",
            parameters={"signs": "++"},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_sum(block, "Sum1Block")
        assert "class Sum1Block" in code or "struct Sum1Block" in code
        assert "input0" in code
        assert "input1" in code

    def test_cpp_gain_template(self):
        """Test C++ Gain block template."""
        from src.codegen.languages.cpp.blocks.math_ops import template_gain

        block = BlockInfo(
            id="gain1",
            type="gain",
            name="Gain1",
            parameters={"gain": 1.5},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_gain(block, "Gain1Block")
        assert "Gain1Block" in code
        assert "1.5" in code

    def test_cpp_product_template(self):
        """Test C++ Product block template."""
        from src.codegen.languages.cpp.blocks.math_ops import template_product

        block = BlockInfo(
            id="prod1",
            type="product",
            name="Product1",
            parameters={"inputs": "*/"},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_product(block, "Product1Block")
        assert "Product1Block" in code

    def test_cpp_math_templates_registry(self):
        """Test that C++ MATH_TEMPLATES registry has expected entries."""
        from src.codegen.languages.cpp.blocks.math_ops import MATH_TEMPLATES

        expected = ["sum", "gain", "product", "abs", "sign"]
        for key in expected:
            assert key in MATH_TEMPLATES


class TestRustSourceTemplates:
    """Tests for Rust source block templates."""

    def test_rust_constant_template(self):
        """Test Rust Constant block template."""
        from src.codegen.languages.rust.blocks.sources import template_constant

        block = BlockInfo(
            id="const1",
            type="constant",
            name="Constant1",
            parameters={"value": 5.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_constant(block, "Const1Block")
        assert "5.0" in code
        assert "struct" in code or "impl" in code

    def test_rust_step_template(self):
        """Test Rust Step block template."""
        from src.codegen.languages.rust.blocks.sources import template_step

        block = BlockInfo(
            id="step1",
            type="step",
            name="Step1",
            parameters={"step_time": 1.0, "initial_value": 0.0, "final_value": 1.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_step(block, "Step1Block")
        assert "step_time" in code
        assert "struct" in code or "impl" in code


class TestCppSourceTemplates:
    """Tests for C++ source block templates."""

    def test_cpp_constant_template(self):
        """Test C++ Constant block template."""
        from src.codegen.languages.cpp.blocks.sources import template_constant

        block = BlockInfo(
            id="const1",
            type="constant",
            name="Constant1",
            parameters={"value": 7.5},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_constant(block, "Const1Block")
        assert "7.5" in code
        assert "class" in code or "struct" in code

    def test_cpp_step_template(self):
        """Test C++ Step block template."""
        from src.codegen.languages.cpp.blocks.sources import template_step

        block = BlockInfo(
            id="step1",
            type="step",
            name="Step1",
            parameters={"step_time": 0.5, "initial_value": 0.0, "final_value": 2.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_step(block, "Step1Block")
        assert "step_time" in code or "0.5" in code


class TestCodegenNonlinearTemplates:
    """Tests for nonlinear block templates."""

    def test_c_relay_template(self):
        """Test C Relay block template."""
        from src.codegen.languages.c.blocks.nonlinear import template_relay

        block = BlockInfo(
            id="relay1",
            type="relay",
            name="Relay1",
            parameters={"onValue": 1.0, "offValue": 0.0, "onThreshold": 0.5, "offThreshold": 0.1},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_relay(block, "Relay1_Block")
        assert "typedef struct" in code
        # Check for output values in the generated code
        assert "on_output" in code or "state" in code

    def test_python_relay_template(self):
        """Test Python Relay block template."""
        from src.codegen.languages.python.blocks.nonlinear import relay_template

        block = BlockInfo(
            id="relay1",
            type="relay",
            name="Relay1",
            parameters={"onValue": 1.0, "offValue": -1.0, "onThreshold": 0.0, "offThreshold": 0.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = relay_template(block, "Relay1Class")
        assert "class Relay1Class" in code


class TestCodegenControlDesignTemplates:
    """Tests for control design block templates."""

    def test_c_pid_controller_template(self):
        """Test C PID Controller block template."""
        from src.codegen.languages.c.blocks.control_design import pid_controller_template

        block = BlockInfo(
            id="pid1",
            type="pid_controller",
            name="PID1",
            parameters={"Kp": 1.0, "Ki": 0.1, "Kd": 0.01},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = pid_controller_template(block, "PID1_Block")
        assert "typedef struct" in code
        assert "Kp" in code or "kp" in code

    def test_python_pid_controller_template(self):
        """Test Python PID Controller block template."""
        from src.codegen.languages.python.blocks.control_design import pid_controller_template

        block = BlockInfo(
            id="pid1",
            type="pid_controller",
            name="PID1",
            parameters={"Kp": 2.0, "Ki": 0.5, "Kd": 0.1},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = pid_controller_template(block, "PID1Class")
        assert "class PID1Class" in code

    def test_c_pi_controller_template(self):
        """Test C PI Controller block template."""
        from src.codegen.languages.c.blocks.control_design import pi_controller_template

        block = BlockInfo(
            id="pi1",
            type="pi_controller",
            name="PI1",
            parameters={"Kp": 1.0, "Ki": 0.2},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = pi_controller_template(block, "PI1_Block")
        assert "typedef struct" in code

    def test_python_pi_controller_template(self):
        """Test Python PI Controller block template."""
        from src.codegen.languages.python.blocks.control_design import pi_controller_template

        block = BlockInfo(
            id="pi1",
            type="pi_controller",
            name="PI1",
            parameters={"Kp": 1.5, "Ki": 0.3},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = pi_controller_template(block, "PI1Class")
        assert "class PI1Class" in code


class TestCodegenDSPTemplates:
    """Tests for DSP block templates."""

    def test_c_fir_filter_template(self):
        """Test C FIR Filter block template."""
        from src.codegen.languages.c.blocks.dsp import template_fir_filter

        block = BlockInfo(
            id="fir1",
            type="fir_filter",
            name="FIRFilter1",
            parameters={"coefficients": [0.25, 0.5, 0.25]},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_fir_filter(block, "FIRFilter1_Block")
        assert "typedef struct" in code

    def test_python_fir_filter_template(self):
        """Test Python FIR Filter block template."""
        from src.codegen.languages.python.blocks.dsp import fir_filter_template

        block = BlockInfo(
            id="fir1",
            type="fir_filter",
            name="FIRFilter1",
            parameters={"coefficients": [0.25, 0.5, 0.25]},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = fir_filter_template(block, "FIRFilter1Class")
        assert "class FIRFilter1Class" in code

    def test_c_mean_template(self):
        """Test C Mean block template."""
        from src.codegen.languages.c.blocks.dsp import template_mean

        block = BlockInfo(
            id="mean1",
            type="mean",
            name="Mean1",
            parameters={"window_size": 10},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_mean(block, "Mean1_Block")
        assert "typedef struct" in code

    def test_python_mean_template(self):
        """Test Python Mean block template."""
        from src.codegen.languages.python.blocks.dsp import mean_template

        block = BlockInfo(
            id="mean1",
            type="mean",
            name="Mean1",
            parameters={"window_size": 10},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = mean_template(block, "Mean1Class")
        assert "class Mean1Class" in code


class TestCodegenAerospaceTemplates:
    """Tests for aerospace block templates."""

    def test_c_isa_atmosphere_template(self):
        """Test C ISA Atmosphere block template."""
        from src.codegen.languages.c.blocks.aerospace import isa_atmosphere_template

        block = BlockInfo(
            id="isa1",
            type="isa_atmosphere",
            name="ISA1",
            parameters={},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = isa_atmosphere_template(block, "ISA1_Block")
        assert "typedef struct" in code

    def test_python_isa_atmosphere_template(self):
        """Test Python ISA Atmosphere block template."""
        from src.codegen.languages.python.blocks.aerospace import isa_atmosphere_template

        block = BlockInfo(
            id="isa1",
            type="isa_atmosphere",
            name="ISA1",
            parameters={},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = isa_atmosphere_template(block, "ISA1Class")
        assert "class ISA1Class" in code

    def test_c_quaternion_normalize_template(self):
        """Test C Quaternion Normalize block template."""
        from src.codegen.languages.c.blocks.aerospace import quaternion_normalize_template

        block = BlockInfo(
            id="qn1",
            type="quaternion_normalize",
            name="QuaternionNorm1",
            parameters={},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = quaternion_normalize_template(block, "QuatNorm1_Block")
        assert "typedef struct" in code

    def test_python_quaternion_normalize_template(self):
        """Test Python Quaternion Normalize block template."""
        from src.codegen.languages.python.blocks.aerospace import quaternion_normalize_template

        block = BlockInfo(
            id="qn1",
            type="quaternion_normalize",
            name="QuaternionNorm1",
            parameters={},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = quaternion_normalize_template(block, "QuatNorm1Class")
        assert "class QuatNorm1Class" in code


class TestCodegenSignalProcessingTemplates:
    """Tests for signal processing block templates."""

    def test_c_rate_limiter_template(self):
        """Test C Rate Limiter block template."""
        from src.codegen.languages.c.blocks.signal_processing import template_rate_limiter

        block = BlockInfo(
            id="rl1",
            type="rate_limiter",
            name="RateLimiter1",
            parameters={"rising_slew_limit": 1.0, "falling_slew_limit": -1.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_rate_limiter(block, "RateLimiter1_Block")
        assert "typedef struct" in code

    def test_c_moving_average_template(self):
        """Test C Moving Average block template."""
        from src.codegen.languages.c.blocks.signal_processing import template_moving_average

        block = BlockInfo(
            id="ma1",
            type="moving_average",
            name="MovingAvg1",
            parameters={"window_size": 5},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_moving_average(block, "MovingAvg1_Block")
        assert "typedef struct" in code


# =============================================================================
# Codegen Controller Tests
# =============================================================================


class TestCodegenController:
    """Tests for codegen controller functions."""

    def test_sanitize_project_name_simple(self):
        """Test sanitizing a simple project name."""
        from src.codegen.controller import sanitize_project_name

        assert sanitize_project_name("my_project") == "my_project"
        assert sanitize_project_name("my project") == "my_project"
        assert sanitize_project_name("MyProject") == "MyProject"

    def test_sanitize_project_name_special_chars(self):
        """Test sanitizing project name with special characters."""
        from src.codegen.controller import sanitize_project_name

        assert sanitize_project_name("my@project!test") == "myprojecttest"
        assert sanitize_project_name("test#123") == "test123"
        assert sanitize_project_name("project$%^") == "project"

    def test_sanitize_project_name_hyphens_spaces(self):
        """Test sanitizing project name with hyphens and spaces."""
        from src.codegen.controller import sanitize_project_name

        assert sanitize_project_name("my-project") == "my_project"
        assert sanitize_project_name("my - project") == "my_project"
        assert sanitize_project_name("my--project") == "my_project"

    def test_sanitize_project_name_empty(self):
        """Test sanitizing empty or special-char-only names."""
        from src.codegen.controller import sanitize_project_name

        assert sanitize_project_name("") == "simulation"
        assert sanitize_project_name("@#$%") == "simulation"
        assert sanitize_project_name("   ") == "simulation"

    def test_sanitize_project_name_with_underscores(self):
        """Test project names with leading/trailing underscores."""
        from src.codegen.controller import sanitize_project_name

        assert sanitize_project_name("_test_") == "test"
        assert sanitize_project_name("__test__") == "test"

    def test_codegen_request_defaults(self):
        """Test CodeGenRequest default values."""
        from src.codegen.controller import CodeGenRequest

        request = CodeGenRequest(model={})
        assert request.language == "python"
        assert request.integration_method == "rk4"
        assert request.step_size == 0.01
        assert request.stop_time == 10.0
        assert request.start_time == 0.0
        assert request.project_name == "simulation"
        assert request.include_csv_output is True
        assert request.include_main is True

    def test_codegen_request_custom(self):
        """Test CodeGenRequest with custom values."""
        from src.codegen.controller import CodeGenRequest

        request = CodeGenRequest(
            model={"name": "test"},
            language="c",
            integration_method="euler",
            step_size=0.001,
            stop_time=5.0,
            start_time=1.0,
            project_name="custom_project",
            include_csv_output=False,
            include_main=False,
        )
        assert request.language == "c"
        assert request.integration_method == "euler"
        assert request.step_size == 0.001
        assert request.stop_time == 5.0
        assert request.start_time == 1.0
        assert request.project_name == "custom_project"
        assert request.include_csv_output is False
        assert request.include_main is False

    def test_compile_request_defaults(self):
        """Test CompileRequest default values."""
        from src.codegen.controller import CompileRequest

        request = CompileRequest(model={})
        assert request.language == "python"
        assert request.integration_method == "rk4"
        assert request.step_size == 0.01

    def test_codegen_info_model(self):
        """Test CodeGenInfo model."""
        from src.codegen.controller import CodeGenInfo

        info = CodeGenInfo(
            languages=["python", "c"],
            integration_methods=["euler", "rk4"],
            supported_blocks=["sum", "gain"],
        )
        assert len(info.languages) == 2
        assert len(info.integration_methods) == 2
        assert len(info.supported_blocks) == 2

    def test_compile_status_response_model(self):
        """Test CompileStatusResponse model."""
        from src.codegen.controller import CompileStatusResponse

        response = CompileStatusResponse(
            docker_available=True, images_available={"python": True, "c": False}
        )
        assert response.docker_available is True
        assert response.images_available["python"] is True
        assert response.images_available["c"] is False


# =============================================================================
# Additional Codegen Language Block Tests for Rust and C++
# =============================================================================


class TestRustBlockTemplates:
    """Additional tests for Rust block templates."""

    def test_rust_trigonometry_template(self):
        """Test Rust trigonometry block template."""
        from src.codegen.languages.rust.blocks.math_ops import template_trigonometry

        block = BlockInfo(
            id="trig1",
            type="trigonometry",
            name="Trig1",
            parameters={"function": "sin"},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_trigonometry(block, "Trig1Block")
        assert "Trig1Block" in code
        assert "sin" in code.lower()

    def test_rust_saturation_template(self):
        """Test Rust saturation block template."""
        from src.codegen.languages.rust.blocks.math_ops import template_saturation

        block = BlockInfo(
            id="sat1",
            type="saturation",
            name="Saturation1",
            parameters={"upperLimit": 5.0, "lowerLimit": -5.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_saturation(block, "Sat1Block")
        assert "Sat1Block" in code

    def test_rust_mux_template(self):
        """Test Rust Mux block template."""
        from src.codegen.languages.rust.blocks.math_ops import template_mux

        block = BlockInfo(
            id="mux1",
            type="mux",
            name="Mux1",
            parameters={"numInputs": 3},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_mux(block, "Mux1Block")
        assert "Mux1Block" in code

    def test_rust_demux_template(self):
        """Test Rust Demux block template."""
        from src.codegen.languages.rust.blocks.math_ops import template_demux

        block = BlockInfo(
            id="demux1",
            type="demux",
            name="Demux1",
            parameters={"numOutputs": 2},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_demux(block, "Demux1Block")
        assert "Demux1Block" in code

    def test_rust_bias_template(self):
        """Test Rust Bias block template."""
        from src.codegen.languages.rust.blocks.math_ops import template_bias

        block = BlockInfo(
            id="bias1",
            type="bias",
            name="Bias1",
            parameters={"bias": 3.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_bias(block, "Bias1Block")
        assert "Bias1Block" in code


class TestCppBlockTemplates:
    """Additional tests for C++ block templates."""

    def test_cpp_saturation_template(self):
        """Test C++ saturation block template."""
        from src.codegen.languages.cpp.blocks.math_ops import template_saturation

        block = BlockInfo(
            id="sat1",
            type="saturation",
            name="Saturation1",
            parameters={"upperLimit": 10.0, "lowerLimit": -10.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_saturation(block, "Sat1Block")
        assert "Sat1Block" in code

    def test_cpp_bias_template(self):
        """Test C++ Bias block template."""
        from src.codegen.languages.cpp.blocks.math_ops import template_bias

        block = BlockInfo(
            id="bias1",
            type="bias",
            name="Bias1",
            parameters={"bias": 2.5},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_bias(block, "Bias1Block")
        assert "Bias1Block" in code

    def test_cpp_dead_zone_template(self):
        """Test C++ Dead Zone block template."""
        from src.codegen.languages.cpp.blocks.math_ops import template_dead_zone

        block = BlockInfo(
            id="dz1",
            type="dead_zone",
            name="DeadZone1",
            parameters={"start": -1.0, "end": 1.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_dead_zone(block, "DeadZone1Block")
        assert "DeadZone1Block" in code

    def test_cpp_switch_template(self):
        """Test C++ Switch block template."""
        from src.codegen.languages.cpp.blocks.math_ops import template_switch

        block = BlockInfo(
            id="switch1",
            type="switch",
            name="Switch1",
            parameters={"threshold": 0.0},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_switch(block, "Switch1Block")
        assert "Switch1Block" in code

    def test_cpp_math_function_template(self):
        """Test C++ Math Function block template."""
        from src.codegen.languages.cpp.blocks.math_ops import template_math_function

        block = BlockInfo(
            id="math1",
            type="math_function",
            name="MathFunc1",
            parameters={"function": "sqrt"},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_math_function(block, "MathFunc1Block")
        assert "MathFunc1Block" in code

    def test_cpp_trigonometry_template(self):
        """Test C++ Trigonometry block template."""
        from src.codegen.languages.cpp.blocks.math_ops import template_trigonometry

        block = BlockInfo(
            id="trig1",
            type="trigonometry",
            name="Trig1",
            parameters={"function": "cos"},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_trigonometry(block, "Trig1Block")
        assert "Trig1Block" in code

    def test_cpp_mux_template(self):
        """Test C++ Mux block template."""
        from src.codegen.languages.cpp.blocks.math_ops import template_mux

        block = BlockInfo(
            id="mux1",
            type="mux",
            name="Mux1",
            parameters={"numInputs": 4},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_mux(block, "Mux1Block")
        assert "Mux1Block" in code

    def test_cpp_demux_template(self):
        """Test C++ Demux block template."""
        from src.codegen.languages.cpp.blocks.math_ops import template_demux

        block = BlockInfo(
            id="demux1",
            type="demux",
            name="Demux1",
            parameters={"numOutputs": 3},
            input_connections=[],
            output_connections=[],
            execution_order=0,
        )
        code = template_demux(block, "Demux1Block")
        assert "Demux1Block" in code
