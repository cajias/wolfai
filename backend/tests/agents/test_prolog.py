"""Tests for the Prolog agent."""

import pytest

# Skip entire module if SWI-Prolog is not available
try:
    import pyswip  # noqa: F401
except Exception:
    pytest.skip("SWI-Prolog not available", allow_module_level=True)

from unittest.mock import Mock, AsyncMock
from mcp import ClientSession
from src.wolfai.agents.prolog import PrologAgent


@pytest.fixture
def mock_model():
    """Create a mock language model."""
    model = Mock()
    model.invoke.return_value = """
    % Facts
    mortal(X) :- human(X).
    human(socrates).

    % Query
    ?- mortal(socrates).
    """
    return model


@pytest.fixture
def mock_session():
    """Create a mock MCP session."""
    session = AsyncMock(spec=ClientSession)

    # Set up list_tools response
    # Create a mock Tool
    mock_tool = Mock()
    mock_tool.name = "consult"
    mock_tool.description = "Execute Prolog code"
    mock_tool.inputSchema = {"type": "object"}

    session.list_tools.return_value = [mock_tool]

    # Set up call_tool response
    session.call_tool.return_value = {
        "success": True,
        "solutions": [{}],  # Empty solution means "Yes"
        "error": None
    }

    return session


@pytest.fixture
async def agent(mock_model, mock_session):
    """Create a Prolog agent with mock components."""
    agent = PrologAgent(mock_model, mock_session)
    await agent.initialize()
    return agent

