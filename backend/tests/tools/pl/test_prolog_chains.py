"""Tests for Prolog chain prompts."""

import pytest

# Skip entire module if SWI-Prolog is not available
try:
    import pyswip  # noqa: F401
except Exception:
    pytest.skip("SWI-Prolog not available", allow_module_level=True)

from wolfai.tools.pl.prolog_chains import (
    create_prolog_chain_prompt,
    create_converter_prompt,
    create_interpreter_prompt
)
from tests.tools.pl.test_mcp_mock import MockMCPSession


class TestPrologChainPrompt:
    """Test suite for the main Prolog chain prompt."""

    def test_chain_prompt_structure(self):
        """Test the structure of the chain prompt."""
        prompt = create_prolog_chain_prompt()
        
        # Check basic properties
        assert prompt.name == "prolog-reasoning"
        assert isinstance(prompt.description, str)
        assert len(prompt.arguments) == 1
        assert prompt.arguments[0].name == "question"
        assert prompt.arguments[0].required is True
        
        # Check message sequence
        messages = prompt.messages
        
        # Verify initial instruction
        assert messages[0].role == "assistant"
        assert messages[0].content.type == "text"
        assert "help answer questions" in messages[0].content.text
        
        # Verify example sequence
        example_start = None
        for i, msg in enumerate(messages):
            if msg.role == "user" and "Socrates" in msg.content.text:
                example_start = i
                break
        
        assert example_start is not None
        assert messages[example_start + 1].role == "assistant"  # Conversion
        assert messages[example_start + 2].role == "assistant"  # Interpretation
        
        # Verify placeholders
        assert any(
            "{question}" in msg.content.text
            for msg in messages
        )

    def test_chain_placeholders(self):
        """Test that the chain has all necessary placeholders."""
        prompt = create_prolog_chain_prompt()
        
        # Collect all text content
        all_text = ""
        for msg in prompt.messages:
            all_text += msg.content.text
        
        # Check for required placeholders
        assert "{question}" in all_text
        assert "{generated_prolog}" in all_text
        assert "{interpretation}" in all_text
        assert "{execution_result}" in all_text


class TestConverterPrompt:
    """Test suite for the NL to Prolog converter prompt."""

    def test_converter_structure(self):
        """Test the structure of the converter prompt."""
        prompt = create_converter_prompt()
        
        assert prompt.name == "convert-to-prolog"
        assert isinstance(prompt.description, str)
        assert len(prompt.arguments) == 1
        assert prompt.arguments[0].name == "question"
        
        # Check message sequence
        messages = prompt.messages
        assert len(messages) >= 2  # At least instruction and template
        
        # Verify instruction message
        assert messages[0].role == "assistant"
        assert messages[0].content.type == "text"
        assert "convert" in messages[0].content.text.lower()
        
        # Verify template
        assert messages[-1].role == "user"
        assert "{question}" in messages[-1].content.text


class TestInterpreterPrompt:
    """Test suite for the result interpreter prompt."""

    def test_interpreter_structure(self):
        """Test the structure of the interpreter prompt."""
        prompt = create_interpreter_prompt()
        
        assert prompt.name == "interpret-results"
        assert isinstance(prompt.description, str)
        
        # Check arguments
        args = {arg.name: arg for arg in prompt.arguments}
        assert "question" in args
        assert "prolog_code" in args
        assert "results" in args
        assert all(arg.required for arg in prompt.arguments)
        
        # Check message sequence
        messages = prompt.messages
        assert len(messages) >= 2
        
        # Verify system message
        assert messages[0].role == "assistant"
        assert messages[0].content.type == "text"
        assert "interpret" in messages[0].content.text.lower()
        
        # Verify template contains all placeholders
        final_msg = messages[-1].content.text
        assert "{question}" in final_msg
        assert "{prolog_code}" in final_msg
        assert "{results}" in final_msg


class TestIntegration:
    """Integration tests for the complete prompt chain."""

    def test_chain_compatibility(self):
        """Test that prompts in the chain are compatible."""
        chain = create_prolog_chain_prompt()
        converter = create_converter_prompt()
        interpreter = create_interpreter_prompt()
        
        # Check that the chain includes conversion and interpretation stages
        assert any(
            "convert" in msg.content.text.lower()
            for msg in chain.messages
            if msg.role == "assistant"
        )
        
        assert any(
            "execution" in msg.content.text.lower()
            for msg in chain.messages
            if msg.role == "assistant"
        )
        
        # Verify arguments match between prompts
        chain_args = {arg.name for arg in chain.arguments}
        converter_args = {arg.name for arg in converter.arguments}
        interpreter_args = {arg.name for arg in interpreter.arguments}
        
        assert "question" in chain_args
        assert "question" in converter_args
        assert all(
            arg in interpreter_args
            for arg in ["question", "prolog_code", "results"]
        )

    @pytest.mark.asyncio
    async def test_chain_execution(self, mock_session):
        """
        Test the execution flow of the chain.
        
        This test requires a mock MCP session that provides:
        - prompt execution
        - Prolog tool execution
        """
        # Example question
        question = "If all humans are mortal and Socrates is human, is Socrates mortal?"
        
        # Get the chain prompt
        result = await mock_session.get_prompt(
            "prolog-reasoning",
            arguments={"question": question}
        )
        
        # Verify the execution sequence
        messages = result.messages
        assert len(messages) > 0
        
        # Check that we get Prolog code
        prolog_msg = next(
            (msg for msg in messages 
             if msg.role == "assistant" and "mortal(X) :-" in msg.content.text),
            None
        )
        assert prolog_msg is not None
        
        # Check that we get a meaningful interpretation
        final_msg = messages[-1]
        assert final_msg.role == "assistant"
        assert "yes" in final_msg.content.text.lower()


@pytest.fixture
async def mock_session():
    """Provide a mock MCP session for testing."""
    return MockMCPSession()
