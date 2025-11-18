"""Mock session implementation for MCP testing."""

from dataclasses import dataclass
from typing import Any, Optional

import pytest
from mcp import types

from wolfai.tools.mcp_utils import create_text_message


@dataclass
class MockPromptResult:
    """Mock result from prompt execution."""
    messages: list[types.PromptMessage]


class MockMCPSession:
    """Mock MCP session for testing."""

    def __init__(self) -> None:
        """Initialize with default mock data."""
        self.prompts = {}
        self.tools = {}
        self._setup_default_mocks()

    def _setup_default_mocks(self) -> None:
        """Set up default mock responses."""
        # Mock Prolog conversion
        self._add_mock_prompt("convert-to-prolog", self._mock_convert_to_prolog)

        # Mock the main reasoning chain
        self._add_mock_prompt("prolog-reasoning", self._mock_prolog_chain)

        # Mock the interpreter
        self._add_mock_prompt("interpret-results", self._mock_interpret_results)

        # Mock Prolog tool
        self._add_mock_tool("consult", self._mock_consult)

    def _add_mock_prompt(self, name: str, handler) -> None:
        """Add a mock prompt handler."""
        self.prompts[name] = handler

    def _add_mock_tool(self, name: str, handler) -> None:
        """Add a mock tool handler."""
        self.tools[name] = handler

    async def list_prompts(self) -> list[types.Prompt]:
        """List available prompts."""
        return [
            types.Prompt(
                name=name,
                description=f"Mock prompt for {name}",
                arguments=[
                    types.PromptArgument(
                        name="question",
                        description="Test question",
                        required=True,
                    ),
                ],
            )
            for name in self.prompts
        ]

    async def list_tools(self) -> list[types.Tool]:
        """List available tools."""
        return [
            types.Tool(
                name=name,
                description=f"Mock tool for {name}",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                    },
                },
            )
            for name in self.tools
        ]

    async def get_prompt(
        self,
        name: str,
        arguments: Optional[dict[str, Any]] = None,
    ) -> MockPromptResult:
        """Get and execute a prompt."""
        if name not in self.prompts:
            msg = f"Prompt not found: {name}"
            raise ValueError(msg)

        return await self.prompts[name](arguments or {})

    async def call_tool(
        self,
        name: str,
        arguments: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Call a mock tool."""
        if name not in self.tools:
            msg = f"Tool not found: {name}"
            raise ValueError(msg)

        return await self.tools[name](arguments or {})

    # Mock handlers for prompts

    async def _mock_convert_to_prolog(self, arguments: dict[str, Any]) -> MockPromptResult:
        """Mock the Prolog conversion prompt."""
        question = arguments.get("question", "")

        # Example mappings
        mappings = {
            "If all humans are mortal and Socrates is human, is Socrates mortal?":
                "human(socrates).\nmortal(X) :- human(X).\n?- mortal(socrates).",

            "If John is a parent of Mary, and Mary is a parent of Bob, is John a grandparent of Bob?":
                "parent(john, mary).\nparent(mary, bob).\ngrandparent(X, Z) :- parent(X, Y), parent(Y, Z).\n?- grandparent(john, bob).",

            "If all birds can fly, and tweety is a bird, can tweety fly?":
                "bird(tweety).\nfly(X) :- bird(X).\n?- fly(tweety).",
        }

        prolog_code = mappings.get(question, "error('Unknown question').")

        return MockPromptResult(
            messages=[create_text_message("assistant", prolog_code)],
        )

    async def _mock_prolog_chain(self, arguments: dict[str, Any]) -> MockPromptResult:
        """Mock the main Prolog reasoning chain."""
        question = arguments.get("question", "")

        # First get the Prolog code
        conversion = await self._mock_convert_to_prolog({"question": question})
        prolog_code = conversion.messages[0].content.text

        # Then simulate execution
        execution = await self._mock_consult({"code": prolog_code})

        # Finally interpret
        interpretation = await self._mock_interpret_results({
            "question": question,
            "prolog_code": prolog_code,
            "results": str(execution),
        })

        # Build the chain response
        return MockPromptResult(
            messages=[
                # Original question
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=question,
                    ),
                ),
                # Conversion
                types.PromptMessage(
                    role="assistant",
                    content=types.TextContent(
                        type="text",
                        text=f"I'll convert this to Prolog:\n\n{prolog_code}",
                    ),
                ),
                # Execution result as assistant message
                types.PromptMessage(
                    role="assistant",
                    content=types.TextContent(
                        type="text",
                        text=f"Let me execute this Prolog code:\n{execution!s}",
                    ),
                ),
                # Final interpretation
                interpretation.messages[0],
            ],
        )

    async def _mock_interpret_results(self, arguments: dict[str, Any]) -> MockPromptResult:
        """Mock the results interpretation prompt."""
        results = arguments.get("results", "")

        # Simulate an interpretation based on the results
        success = "success': True" in results
        interpretation = (
            "Based on the Prolog execution, the answer is Yes."
            if success else
            "The query could not be proven based on the given facts and rules."
        )

        return MockPromptResult(
            messages=[create_text_message("assistant", interpretation)],
        )

    # Mock handlers for tools

    async def _mock_consult(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Mock the Prolog consult tool."""
        code = arguments.get("code", "")

        # Simple mock execution - just check if the code contains a query
        if "?-" in code:
            return {
                "success": True,
                "solutions": [{}],  # Empty solution means query was satisfied
                "error": None,
            }
        return {
            "success": False,
            "solutions": [],
            "error": "No query found in code",
        }


@pytest.fixture
async def mock_session():
    """Provide a mock MCP session for testing."""
    return MockMCPSession()
