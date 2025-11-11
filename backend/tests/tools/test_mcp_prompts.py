"""Tests for MCP prompt functionality in mcp_utils."""

import pytest
from mcp import types

from wolfai.tools.mcp_utils import (
    MCPPrompt,
    create_text_message,
    function_to_mcp_prompt,
    generate_from_module,
    generate_prompts_from_module,
    prompt,
)


def create_test_prompt() -> MCPPrompt:
    """Create a test prompt for testing."""
    return MCPPrompt(
        name="test_prompt",
        description="A test prompt",
        arguments=[
            types.PromptArgument(
                name="test_arg",
                description="A test argument",
                required=True,
            ),
        ],
        messages=[create_text_message("assistant", "Test message")],
    )


class TestMCPPrompt:
    """Test the MCPPrompt dataclass."""

    def test_prompt_creation(self):
        """Test creating an MCPPrompt instance."""
        prompt_obj = create_test_prompt()
        assert prompt_obj.name == "test_prompt"
        assert prompt_obj.description == "A test prompt"
        assert len(prompt_obj.arguments) == 1
        assert len(prompt_obj.messages) == 1
        assert prompt_obj.messages[0].role == "assistant"


class TestPromptDecorator:
    """Test the @prompt decorator."""

    def test_basic_decorator(self):
        """Test basic @prompt decorator usage."""

        @prompt
        def test_prompt() -> MCPPrompt:
            return create_test_prompt()

        assert hasattr(test_prompt, "_is_mcp_prompt")
        assert test_prompt._is_mcp_prompt is True

    def test_decorator_with_name(self):
        """Test @prompt decorator with custom name."""

        @prompt(name="custom_name")
        def test_prompt() -> MCPPrompt:
            return create_test_prompt()

        assert hasattr(test_prompt, "_mcp_prompt_name")
        assert test_prompt._mcp_prompt_name == "custom_name"

    def test_decorator_preserves_function(self):
        """Test that decorator preserves function attributes."""

        @prompt
        def test_prompt() -> MCPPrompt:
            """Test docstring."""
            return create_test_prompt()

        assert test_prompt.__doc__ == "Test docstring."
        result = test_prompt()
        assert isinstance(result, MCPPrompt)


class TestPromptConversion:
    """Test converting functions to MCP prompts."""

    def test_basic_conversion(self):
        """Test basic conversion of a function to an MCP prompt."""

        def test_prompt() -> MCPPrompt:
            """A test prompt function."""
            return create_test_prompt()

        mcp_prompt = function_to_mcp_prompt(test_prompt)
        assert isinstance(mcp_prompt, types.Prompt)
        assert mcp_prompt.name == "test_prompt"
        assert len(mcp_prompt.arguments) == 0

    def test_invalid_return_type(self):
        """Test handling functions that don't return MCPPrompt."""

        def invalid_func() -> str:
            return "not a prompt"

        with pytest.raises(ValueError):
            function_to_mcp_prompt(invalid_func)


class TestModulePrompts:
    """Test generating prompts from modules."""

    def test_module_discovery(self):
        """Test discovering prompts in a module."""

        # Create a test module with some functions
        def prompt1() -> MCPPrompt:
            return create_test_prompt()

        prompt1 = prompt(prompt1)

        def prompt2() -> MCPPrompt:
            return create_test_prompt()

        prompt2 = prompt(prompt2)

        def not_a_prompt() -> str:
            return "regular function"

        module = type("TestModule", (), {
            "prompt1": prompt1,
            "prompt2": prompt2,
            "not_a_prompt": not_a_prompt,
        })

        prompts = generate_prompts_from_module(module)
        assert len(prompts) == 2
        assert all(isinstance(p, types.Prompt) for p in prompts)

    def test_module_exclusions(self):
        """Test excluding specific prompts during generation."""

        def create_prompt() -> MCPPrompt:
            return create_test_prompt()

        create_prompt = prompt(create_prompt)

        module = type("TestModule", (), {
            "prompt1": create_prompt,
            "prompt2": create_prompt,
        })

        prompts = generate_prompts_from_module(module, exclude=["prompt1"])
        print(prompts)
        assert len(prompts) == 1

    def test_combined_generation(self):
        """Test generating both tools and prompts from a module."""

        def tool_func(x: int) -> int:
            """A test tool."""
            return x

        def prompt_func() -> MCPPrompt:
            """A test prompt."""
            return create_test_prompt()

        prompt_func = prompt(prompt_func)

        module = type("TestModule", (), {
            "tool_func": tool_func,
            "prompt_func": prompt_func,
        })

        self.module = generate_from_module(module)
        self.self_module = self.module
        tools, prompts = self.self_module

        # Check tools
        assert len(tools) == 1
        assert tools[0].name == "tool_func"
        assert isinstance(tools[0], types.Tool)

        # Check prompts
        assert len(prompts) == 1
        assert isinstance(prompts[0], types.Prompt)


class TestErrorHandling:
    """Test error handling in prompt functionality."""

    def test_invalid_prompt_definition(self):
        """Test handling invalid prompt definitions."""

        @prompt
        def invalid_prompt() -> MCPPrompt:
            return "not a prompt"  # Invalid return type

        with pytest.raises(ValueError):
            function_to_mcp_prompt(invalid_prompt)

    def test_prompt_validation(self):
        """Test validation of prompt messages."""

        def test_prompt() -> MCPPrompt:
            return MCPPrompt(
                name="test",
                description="test",
                arguments=[],
                messages=[create_text_message("assistant", "test")],
            )

        prompt_obj = test_prompt()
        assert isinstance(prompt_obj, MCPPrompt)
        assert prompt_obj.messages[0].role == "assistant"
