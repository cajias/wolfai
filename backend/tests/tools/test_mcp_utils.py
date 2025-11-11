"""Tests for MCP utility functions that generate tools from Python code."""

import inspect
from datetime import date, datetime
from typing import Any, Optional

import pytest

from wolfai.tools.mcp_utils import (
    function_to_mcp_tool,
    generate_example_value,
    generate_tools_from_module,
    get_parameter_schema,
    get_type_validation_rules,
)


# Test functions to convert to tools
def simple_function(x: int, y: str = "default") -> str:
    """A simple function with basic types.

    Args:
        x: An integer parameter
        y: A string parameter with default
    """
    return f"{y}: {x}"


def complex_function(
    items: list[dict[str, Any]],
    filter_by: Optional[str] = None,
    limit: int = 10,
    created_at: Optional[datetime] = None,
    active_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """A function with more complex types.

    Args:
        items: List of dictionaries to process
        filter_by: Optional filter key
        limit: Maximum items to return
        created_at: Timestamp of creation
        active_date: Date of activation
    """
    return []


class TestTypeConversion:
    """Test type conversion and validation rules."""

    @pytest.mark.parametrize(("py_type", "expected_type", "expected_format"), [
        (str, "string", None),
        (int, "number", "integer"),
        (float, "number", None),
        (bool, "boolean", None),
        (datetime, "string", "date-time"),
        (date, "string", "date"),
    ])
    def test_type_validation_rules(self, py_type, expected_type, expected_format):
        """Test generation of type validation rules."""
        rules = get_type_validation_rules(py_type)
        assert rules["type"] == expected_type
        if expected_format:
            assert rules["format"] == expected_format

    def test_list_validation_rules(self):
        """Test validation rules for List types."""
        rules = get_type_validation_rules(list[int])
        assert rules["type"] == "array"
        assert rules["items"]["type"] == "number"
        assert rules["items"]["format"] == "integer"

    def test_dict_validation_rules(self):
        """Test validation rules for Dict types."""
        rules = get_type_validation_rules(dict[str, int])
        assert rules["type"] == "object"
        assert rules["additionalProperties"]["type"] == "number"
        assert rules["additionalProperties"]["format"] == "integer"


class TestExampleGeneration:
    """Test example value generation for different types."""

    @pytest.mark.parametrize(("py_type", "expected"), [
        (str, "example_text"),
        (int, 42),
        (float, 3.14),
        (bool, True),
        (datetime, "2024-02-14T12:00:00"),
        (date, "2024-02-14"),
    ])
    def test_basic_example_generation(self, py_type, expected):
        """Test generation of example values for basic types."""
        assert generate_example_value(py_type) == expected

    def test_list_example_generation(self):
        """Test example generation for List types."""
        assert generate_example_value(list[int]) == [42]
        assert generate_example_value(list[str]) == ["example_text"]

    def test_dict_example_generation(self):
        """Test example generation for Dict types."""
        example = generate_example_value(dict[str, int])
        assert isinstance(example, dict)
        assert next(iter(example.values())) == 42

    def test_optional_example_generation(self):
        """Test example generation for Optional types."""
        assert generate_example_value(Optional[int]) == 42


class TestParameterSchema:
    """Test parameter schema generation."""

    def test_required_parameter_schema(self):
        """Test schema for required parameters."""
        param = inspect.Parameter(
            "test",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=int,
        )
        schema = get_parameter_schema(param)
        assert schema["type"] == "number"
        assert schema["format"] == "integer"
        assert "required" in schema["description"].lower()
        assert "example value: 42" in schema["description"].lower()

    def test_optional_parameter_schema(self):
        """Test schema for optional parameters."""
        param = inspect.Parameter(
            "test",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=Optional[str],
            default=None,
        )
        schema = get_parameter_schema(param)
        assert "description" in schema
        assert "optional" in schema["description"].lower()
        assert "defaults to none" in schema["description"].lower()

    def test_datetime_parameter_schema(self):
        """Test schema for datetime parameters."""
        param = inspect.Parameter(
            "timestamp",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=datetime,
        )
        schema = get_parameter_schema(param)
        assert schema["type"] == "string"
        assert schema["format"] == "date-time"
        assert "pattern" in schema


class TestFunctionToTool:
    """Test conversion of Python functions to MCP tools."""

    def test_simple_function_conversion(self):
        """Test converting a simple function with basic types."""
        tool = function_to_mcp_tool(simple_function)

        assert tool.name == "simple_function"
        assert "simple function with basic types" in tool.description.lower()

        schema = tool.inputSchema
        assert schema["type"] == "object"
        assert "x" in schema["properties"]
        assert "y" in schema["properties"]
        assert schema["properties"]["x"]["type"] == "number"
        assert schema["properties"]["y"]["type"] == "string"
        assert schema["required"] == ["x"]

    def test_complex_function_conversion(self):
        """Test converting a function with more complex types."""
        tool = function_to_mcp_tool(complex_function)

        schema = tool.inputSchema

        # Check items parameter
        assert "items" in schema["properties"]
        assert schema["properties"]["items"]["type"] == "array"

        # Check datetime parameter
        assert schema["properties"]["created_at"]["type"] == "string"
        assert schema["properties"]["created_at"]["format"] == "date-time"

        # Check date parameter
        assert schema["properties"]["active_date"]["type"] == "string"
        assert schema["properties"]["active_date"]["format"] == "date"

        assert "filter_by" in schema["properties"]
        assert "limit" in schema["properties"]
        assert schema["required"] == ["items"]

    def test_custom_tool_name(self):
        """Test providing a custom name for the tool."""
        tool = function_to_mcp_tool(simple_function, name="custom_name")
        assert tool.name == "custom_name"


class TestModuleTools:
    """Test generating tools from entire modules."""

    def test_exclude_private_functions(self):
        """Test that private functions are excluded by default."""
        module = type("TestModule", (), {
            "public_func": lambda: None,
            "_private_func": lambda: None,
        })

        tools = generate_tools_from_module(module)
        names = [t.name for t in tools]

        assert "public_func" in names
        assert "_private_func" not in names

    def test_include_private_functions(self):
        """Test including private functions when specified."""
        module = type("TestModule", (), {
            "public_func": lambda: None,
            "_private_func": lambda: None,
        })

        tools = generate_tools_from_module(module, include_private=True)
        names = [t.name for t in tools]

        assert "_private_func" in names

    def test_exclude_specific_functions(self):
        """Test excluding specific functions."""
        module = type("TestModule", (), {
            "func1": lambda: None,
            "func2": lambda: None,
            "func3": lambda: None,
        })

        tools = generate_tools_from_module(module, exclude=["func2"])
        names = [t.name for t in tools]

        assert "func1" in names
        assert "func2" not in names
        assert "func3" in names


class TestErrorHandling:
    """Test error handling in tool generation."""

    def test_invalid_function(self):
        """Test handling functions that can't be converted to tools."""
        def bad_function(*args, **kwargs) -> None:
            pass

        tool = function_to_mcp_tool(bad_function)
        assert tool.name == "bad_function"
        assert tool.inputSchema["type"] == "object"

    def test_missing_docstring(self):
        """Test handling functions without docstrings."""
        def no_doc(x: int) -> None:
            pass

        tool = function_to_mcp_tool(no_doc)
        assert tool.name == "no_doc"
        assert tool.description  # Should have some default description

    def test_missing_type_hints(self):
        """Test handling functions without type hints."""
        def no_types(x, y="default") -> None:
            """Function without type hints."""

        tool = function_to_mcp_tool(no_types)
        assert tool.inputSchema["properties"]["x"]["type"] == "string"  # Default to string
        assert "y" in tool.inputSchema["properties"]
