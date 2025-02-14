"""Mock session implementation for MCP testing."""

import pytest
from typing import Dict, Any, List, Optional
import mcp.types as types
from dataclasses import dataclass


@dataclass
class MockPromptResult:
    """Mock result from prompt execution."""
    messages: List[types.PromptMessage]


class MockMCPSession:
    """Mock MCP session for testing."""
    
    def __init__(self):
        """Initialize with default mock data."""
        self.prompts = {}
        self.tools = {}
        self._setup_default_mocks()
    
    def _setup_default_mocks(self):
        """Set up default mock responses."""
        # Mock Prolog conversion
        self._add_mock_prompt("convert-to-prolog", self._mock_convert_to_prolog)
        
        # Mock the main reasoning chain
        self._add_mock_prompt("prolog-reasoning", self._mock_prolog_chain)
        
        # Mock the interpreter
        self._add_mock_prompt("interpret-results", self._mock_interpret_results)
        
        # Mock Prolog tool
        self._add_mock_tool("consult", self._mock_consult)
    
    def _add_mock_prompt(self, name: str, handler):
        """Add a mock prompt handler."""
        self.prompts[name] = handler
    
    def _add_mock_tool(self, name: str, handler):
        """Add a mock tool handler."""
        self.tools[name] = handler
    
    async def list_prompts(self) -> List[types.Prompt]:
        """List available prompts."""
        return [
            types.Prompt(
                name=name,
                description=f"Mock prompt for {name}",
                arguments=[
                    types.PromptArgument(
                        name="question",
                        description="Test question",
                        required=True
                    )
                ]
            )
            for name in self.prompts
        ]

    async def list_tools(self) -> List[types.Tool]:
        """List available tools."""
        return [
            types.Tool(
                name=name,
                description=f"Mock tool for {name}",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"}
                    }
                }
            )
            for name in self.tools
        ]
    
    async def get_prompt(
        self,
        name: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> MockPromptResult:
        """Get and execute a prompt."""
        if name not in self.prompts:
            raise ValueError(f"Prompt not found: {name}")
        
        return await self.prompts[name](arguments or {})
    
    async def call_tool(
        self,
        name: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Call a mock tool."""
        if name not in self.tools:
            raise ValueError(f"Tool not found: {name}")
        
        return await self.tools[name](arguments or {})
    
    # Mock handlers for prompts
    
    async def _mock_convert_to_prolog(self, arguments: Dict[str, Any]) -> MockPromptResult:
        """Mock the Prolog conversion prompt."""
        question = arguments.get("question", "")
        
        # Example mappings
        mappings = {
            "If all humans are mortal and Socrates is human, is Socrates mortal?":
                "human(socrates).\nmortal(X) :- human(X).\n?- mortal(socrates).",
            
            "If John is a parent of Mary, and Mary is a parent of Bob, is John a grandparent of Bob?":
                "parent(john, mary).\nparent(mary, bob).\ngrandparent(X, Z) :- parent(X, Y), parent(Y, Z).\n?- grandparent(john, bob).",
            
            "If all birds can fly, and tweety is a bird, can tweety fly?":
                "bird(tweety).\nfly(X) :- bird(X).\n?- fly(tweety)."
        }
        
        prolog_code = mappings.get(question, "error('Unknown question').")
        
        return MockPromptResult(
            messages=[
                types.PromptMessage(
                    role="assistant",
                    content=types.TextContent(
                        type="text",
                        text=prolog_code
                    )
                )
            ]
        )
    
    async def _mock_prolog_chain(self, arguments: Dict[str, Any]) -> MockPromptResult:
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
            "results": str(execution)
        })
        
        # Build the chain response
        return MockPromptResult(
            messages=[
                # Original question
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=question
                    )
                ),
                # Conversion
                types.PromptMessage(
                    role="assistant",
                    content=types.TextContent(
                        type="text",
                        text=f"I'll convert this to Prolog:\n\n{prolog_code}"
                    )
                ),
                # Execution result as assistant message
                types.PromptMessage(
                    role="assistant",
                    content=types.TextContent(
                        type="text",
                        text=f"Let me execute this Prolog code:\n{str(execution)}"
                    )
                ),
                # Final interpretation
                interpretation.messages[0]
            ]
        )
    
    async def _mock_interpret_results(self, arguments: Dict[str, Any]) -> MockPromptResult:
        """Mock the results interpretation prompt."""
        question = arguments.get("question", "")
        results = arguments.get("results", "")
        
        # Simulate an interpretation based on the results
        success = "success': True" in results
        interpretation = (
            "Based on the Prolog execution, the answer is Yes."
            if success else
            "The query could not be proven based on the given facts and rules."
        )
        
        return MockPromptResult(
            messages=[
                types.PromptMessage(
                    role="assistant",
                    content=types.TextContent(
                        type="text",
                        text=interpretation
                    )
                )
            ]
        )
    
    # Mock handlers for tools
    
    async def _mock_consult(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Mock the Prolog consult tool."""
        code = arguments.get("code", "")
        
        # Simple mock execution - just check if the code contains a query
        if "?-" in code:
            return {
                "success": True,
                "solutions": [{}],  # Empty solution means query was satisfied
                "error": None
            }
        else:
            return {
                "success": False,
                "solutions": [],
                "error": "No query found in code"
            }


@pytest.fixture
async def mock_session():
    """Provide a mock MCP session for testing."""
    return MockMCPSession()
