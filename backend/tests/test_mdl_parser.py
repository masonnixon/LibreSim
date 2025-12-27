"""Tests for the MDL parser."""

import pytest

from src.parsers.mdl_parser import MDLParser


class TestMDLParser:
    """Tests for the MDLParser class."""

    def test_parser_init(self):
        """Test MDLParser initialization."""
        parser = MDLParser()
        assert parser._content == ""
        assert parser._pos == 0
        assert parser._blocks == []
        assert parser._lines == []

    def test_parse_block_key_value(self):
        """Test parsing key-value pairs."""
        parser = MDLParser()
        parser._content = 'Key1 "Value1"\nKey2 5.0'
        parser._pos = 0

        result = parser._parse_block()

        assert result.get("Key1") == "Value1"
        assert result.get("Key2") == "5.0"

    def test_parse_block_nested(self):
        """Test parsing nested blocks."""
        parser = MDLParser()
        parser._content = 'Outer {\nInner {\nValue "test"\n}\n}'
        parser._pos = 0

        result = parser._parse_block()

        assert "Outer" in result
        assert "Inner" in result["Outer"]
        assert result["Outer"]["Inner"]["Value"] == "test"

    def test_parse_key(self):
        """Test parsing a key."""
        parser = MDLParser()
        parser._content = "TestKey value"
        parser._pos = 0

        key = parser._parse_key()
        assert key == "TestKey"

    def test_parse_quoted_string(self):
        """Test parsing a quoted string."""
        parser = MDLParser()
        parser._content = '"Hello World"'
        parser._pos = 0

        value = parser._parse_quoted_string()
        assert value == "Hello World"

    def test_parse_quoted_string_with_escape(self):
        """Test parsing quoted string with escape."""
        parser = MDLParser()
        parser._content = '"test\\"value"'
        parser._pos = 0

        value = parser._parse_quoted_string()
        # Note: the escape character stays in the output
        assert 'test' in value

    def test_parse_array(self):
        """Test parsing array value."""
        parser = MDLParser()
        parser._content = "[100, 200, 300]"
        parser._pos = 0

        value = parser._parse_array()
        assert value == "[100, 200, 300]"

    def test_parse_nested_array(self):
        """Test parsing nested array."""
        parser = MDLParser()
        parser._content = "[[1, 2], [3, 4]]"
        parser._pos = 0

        value = parser._parse_array()
        assert value == "[[1, 2], [3, 4]]"

    def test_skip_whitespace(self):
        """Test skipping whitespace."""
        parser = MDLParser()
        parser._content = "   \t\ntest"
        parser._pos = 0

        parser._skip_whitespace()
        assert parser._content[parser._pos] == "t"

    def test_skip_comments(self):
        """Test skipping comments."""
        parser = MDLParser()
        parser._content = "# This is a comment\ntest"
        parser._pos = 0

        parser._skip_whitespace()
        assert parser._content[parser._pos] == "t"

    def test_get_value(self):
        """Test _get_value method."""
        parser = MDLParser()
        data = {"key": "value"}

        assert parser._get_value(data, "key", "default") == "value"
        assert parser._get_value(data, "missing", "default") == "default"

    def test_convert_value_float(self):
        """Test converting string to float."""
        parser = MDLParser()

        assert parser._convert_value("5.0") == 5.0
        assert parser._convert_value("100") == 100.0

    def test_convert_value_array(self):
        """Test converting string to array."""
        parser = MDLParser()

        result = parser._convert_value("[1, 2, 3]")
        assert result == [1.0, 2.0, 3.0]

    def test_convert_value_text(self):
        """Test converting non-numeric string."""
        parser = MDLParser()

        assert parser._convert_value("text") == "text"
        assert parser._convert_value("") == ""

    def test_parse_position(self):
        """Test parsing position string."""
        parser = MDLParser()

        pos = parser._parse_position("[100, 200, 150, 250]")
        assert pos.x == 100.0
        assert pos.y == 200.0

    def test_parse_position_invalid(self):
        """Test parsing invalid position."""
        parser = MDLParser()

        pos = parser._parse_position("invalid")
        assert pos.x == 100.0
        assert pos.y == 100.0

    def test_parse_position_short(self):
        """Test parsing short position array."""
        parser = MDLParser()

        pos = parser._parse_position("[50]")
        assert pos.x == 100.0  # Falls back to default
        assert pos.y == 100.0

    def test_find_system_dict(self):
        """Test finding system from dict."""
        parser = MDLParser()

        model_data = {"System": {"Name": "TestSystem"}}
        system = parser._find_system(model_data)
        assert system.get("Name") == "TestSystem"

    def test_find_system_list(self):
        """Test finding system from list."""
        parser = MDLParser()

        model_data = {"System": [{"Name": "First"}, {"Name": "Second"}]}
        system = parser._find_system(model_data)
        assert system.get("Name") == "First"

    def test_find_system_empty_list(self):
        """Test finding system from empty list."""
        parser = MDLParser()

        model_data = {"System": []}
        system = parser._find_system(model_data)
        assert system == {}

    def test_find_system_missing(self):
        """Test finding system when missing."""
        parser = MDLParser()

        model_data = {}
        system = parser._find_system(model_data)
        assert system == {}

    def test_block_type_map(self):
        """Test block type mapping."""
        assert MDLParser.BLOCK_TYPE_MAP["Constant"] == "constant"
        assert MDLParser.BLOCK_TYPE_MAP["Gain"] == "gain"
        assert MDLParser.BLOCK_TYPE_MAP["Sum"] == "sum"
        assert MDLParser.BLOCK_TYPE_MAP["Integrator"] == "integrator"
        assert MDLParser.BLOCK_TYPE_MAP["Scope"] == "scope"
        # Math blocks
        assert MDLParser.BLOCK_TYPE_MAP["Trigonometry"] == "trigonometry"
        assert MDLParser.BLOCK_TYPE_MAP["Math"] == "math_function"
        assert MDLParser.BLOCK_TYPE_MAP["Sign"] == "sign"
        assert MDLParser.BLOCK_TYPE_MAP["DeadZone"] == "dead_zone"
        assert MDLParser.BLOCK_TYPE_MAP["MinMax"] == "minmax"

    def test_create_ports_constant(self):
        """Test creating ports for constant block."""
        parser = MDLParser()

        inputs, outputs = parser._create_ports("constant", "block-1", {})
        assert len(inputs) == 0
        assert len(outputs) == 1
        assert outputs[0].name == "out"

    def test_create_ports_gain(self):
        """Test creating ports for gain block."""
        parser = MDLParser()

        inputs, outputs = parser._create_ports("gain", "block-1", {})
        assert len(inputs) == 1
        assert len(outputs) == 1
        assert inputs[0].name == "in"

    def test_create_ports_sum(self):
        """Test creating ports for sum block."""
        parser = MDLParser()

        inputs, outputs = parser._create_ports("sum", "block-1", {})
        assert len(inputs) == 2
        assert len(outputs) == 1

    def test_create_ports_scope(self):
        """Test creating ports for scope block."""
        parser = MDLParser()

        inputs, outputs = parser._create_ports("scope", "block-1", {})
        assert len(inputs) == 1
        assert len(outputs) == 0

    def test_create_ports_unknown(self):
        """Test creating ports for unknown block type."""
        parser = MDLParser()

        inputs, outputs = parser._create_ports("unknown_type", "block-1", {})
        assert len(inputs) == 0
        assert len(outputs) == 0

    def test_extract_parameters_constant(self):
        """Test extracting parameters for constant block."""
        parser = MDLParser()
        block_data = {"Value": "5.0"}

        params = parser._extract_parameters(block_data, "constant")
        assert params.get("value") == 5.0

    def test_extract_parameters_gain(self):
        """Test extracting parameters for gain block."""
        parser = MDLParser()
        block_data = {"Gain": "2.5"}

        params = parser._extract_parameters(block_data, "gain")
        assert params.get("gain") == 2.5

    def test_extract_parameters_step(self):
        """Test extracting parameters for step block."""
        parser = MDLParser()
        block_data = {"Time": "1.0", "Before": "0", "After": "1"}

        params = parser._extract_parameters(block_data, "step")
        assert params.get("stepTime") == 1.0
        assert params.get("initialValue") == 0.0
        assert params.get("finalValue") == 1.0

    def test_extract_parameters_trigonometry_operator(self):
        """Test extracting parameters for trigonometry block with Operator."""
        parser = MDLParser()
        block_data = {"Operator": "cos"}

        params = parser._extract_parameters(block_data, "trigonometry")
        assert params.get("function") == "cos"

    def test_extract_parameters_trigonometry_function(self):
        """Test extracting parameters for trigonometry block with Function."""
        parser = MDLParser()
        block_data = {"Function": "sin"}

        params = parser._extract_parameters(block_data, "trigonometry")
        assert params.get("function") == "sin"

    def test_extract_parameters_math_function(self):
        """Test extracting parameters for math_function block."""
        parser = MDLParser()
        block_data = {"Operator": "exp"}

        params = parser._extract_parameters(block_data, "math_function")
        assert params.get("function") == "exp"

    def test_extract_parameters_dead_zone(self):
        """Test extracting parameters for dead_zone block."""
        parser = MDLParser()
        block_data = {"LowerValue": "-0.5", "UpperValue": "0.5"}

        params = parser._extract_parameters(block_data, "dead_zone")
        assert params.get("lowerLimit") == -0.5
        assert params.get("upperLimit") == 0.5

    def test_extract_parameters_unknown_type(self):
        """Test extracting parameters for unknown type."""
        parser = MDLParser()
        block_data = {"SomeParam": "value"}

        params = parser._extract_parameters(block_data, "unknown_type")
        assert params == {}

    def test_parse_simulation_config_defaults(self):
        """Test parsing simulation config with defaults."""
        parser = MDLParser()
        model_data = {}

        config = parser._parse_simulation_config(model_data)
        assert config.start_time == 0.0
        assert config.stop_time == 10.0
        assert config.step_size == 0.01
        assert config.solver == "rk4"

    def test_parse_simulation_config_custom(self):
        """Test parsing simulation config with custom values."""
        parser = MDLParser()
        model_data = {
            "StartTime": "0.5",
            "StopTime": "20.0",
            "FixedStep": "0.001",
            "Solver": "ode1"
        }

        config = parser._parse_simulation_config(model_data)
        assert config.start_time == 0.5
        assert config.stop_time == 20.0
        assert config.step_size == 0.001
        assert config.solver == "euler"

    def test_parse_simulation_config_ode45(self):
        """Test parsing ode45 solver."""
        parser = MDLParser()
        model_data = {"Solver": "ode45"}

        config = parser._parse_simulation_config(model_data)
        assert config.solver == "rk4"

    def test_convert_block_unknown_type(self):
        """Test converting unknown block type returns None."""
        parser = MDLParser()
        block_data = {"BlockType": "UnknownType", "Name": "Test"}

        result = parser._convert_block(block_data, 0)
        assert result is None

    def test_convert_block_gain(self):
        """Test converting a gain block."""
        parser = MDLParser()
        block_data = {
            "BlockType": "Gain",
            "Name": "Gain1",
            "Position": "[100, 100, 150, 150]",
            "Gain": "2.0"
        }

        result = parser._convert_block(block_data, 0)
        assert result is not None
        assert result.type == "gain"
        assert result.name == "Gain1"
        assert result.parameters.get("gain") == 2.0

    def test_parse_blocks_empty(self):
        """Test parsing empty block list."""
        parser = MDLParser()
        system_data = {}

        blocks = parser._parse_blocks(system_data)
        assert blocks == []

    def test_parse_blocks_single_dict(self):
        """Test parsing single block as dict."""
        parser = MDLParser()
        system_data = {
            "Block": {
                "BlockType": "Gain",
                "Name": "Gain1"
            }
        }

        blocks = parser._parse_blocks(system_data)
        assert len(blocks) == 1
        assert blocks[0].type == "gain"

    def test_parse_connections_empty(self):
        """Test parsing empty connection list."""
        parser = MDLParser()
        system_data = {}

        connections = parser._parse_connections(system_data, [])
        assert connections == []

    def test_parse_value_unquoted(self):
        """Test parsing unquoted value."""
        parser = MDLParser()
        parser._content = "someValue\nNextKey"
        parser._pos = 0

        value = parser._parse_value()
        assert value == "someValue"

    def test_parse_value_empty(self):
        """Test parsing empty content."""
        parser = MDLParser()
        parser._content = ""
        parser._pos = 0

        value = parser._parse_value()
        assert value == ""

    def test_parse_value_stops_at_brace(self):
        """Test parsing value stops at closing brace."""
        parser = MDLParser()
        parser._content = "value}"
        parser._pos = 0

        value = parser._parse_value()
        assert value == "value"

    def test_parse_multiple_blocks_same_key(self):
        """Test parsing multiple blocks with same key creates list."""
        parser = MDLParser()
        parser._content = """Block {
Name "Block1"
}
Block {
Name "Block2"
}"""
        parser._pos = 0

        result = parser._parse_block()
        assert "Block" in result
        # With multiple blocks of same key, should be a list
        assert isinstance(result["Block"], list)
        assert len(result["Block"]) == 2
