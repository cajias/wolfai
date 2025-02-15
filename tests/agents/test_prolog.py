"""Tests for the Prolog agent."""

import pytest
from unittest.mock import Mock, AsyncMock
from langchain_core.messages import HumanMessage, AIMessage
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


@pytest.mark.asyncio
async def test_initialize(mock_model, mock_session):
    """Test agent initialization."""
    agent = PrologAgent(mock_model, mock_session)
    await agent.initialize()

    # Check that tools were listed
    mock_session.list_tools.assert_called_once()


@pytest.mark.asyncio
async def test_missing_tool(mock_model):
    """Test initialization with missing Prolog tool."""
    session = AsyncMock(spec=ClientSession)
    session.list_tools.return_value = []  # No tools available

    agent = PrologAgent(mock_model, session)
    with pytest.raises(ValueError, match="Prolog tool 'consult' not found"):
        await agent.initialize()
