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


def test_convert_to_prolog(agent, mock_model):
    """Test conversion of natural language to Prolog."""
    question = "Is Socrates mortal?"
    prolog_code = agent.convert_to_prolog(question)
    
    # Check that model was called with appropriate prompt
    mock_model.invoke.assert_called_once()
    prompt = mock_model.invoke.call_args[0][0]
    assert "Question:" in prompt
    assert question in prompt
    
    # Check the extracted code
    assert "mortal(X) :- human(X)" in prolog_code
    assert "human(socrates)" in prolog_code
    assert "?- mortal(socrates)" in prolog_code


def test_prolog_code_extraction(agent):
    """Test extraction of Prolog code from model response."""
    # Test with markdown code blocks
    response = """```prolog
    human(socrates).
    mortal(X) :- human(X).
    ?- mortal(socrates).
    ```"""
    code = agent._extract_prolog_code(response)
    assert "```" not in code
    assert "human(socrates)" in code
    
    # Test duplicate removal
    response = """
    human(socrates).
    human(socrates).
    mortal(X) :- human(X).
    """
    code = agent._extract_prolog_code(response)
    assert len(code.split('\n')) == 2


def test_solution_formatting(agent):
    """Test formatting of Prolog solutions."""
    # Test successful query with no variables
    result = {
        "success": True,
        "solutions": [{}],
        "error": None
    }
    output = agent._format_solutions(result)
    assert output == "Yes."
    
    # Test query with variables
    result = {
        "success": True,
        "solutions": [{"X": "socrates", "Y": "human"}],
        "error": None
    }
    output = agent._format_solutions(result)
    assert "X = socrates" in output
    assert "Y = human" in output
    
    # Test failed query
    result = {
        "success": False,
        "error": "Syntax error",
        "solutions": []
    }
    output = agent._format_solutions(result)
    assert "Error:" in output
    assert "Syntax error" in output
    
    # Test no solutions
    result = {
        "success": True,
        "solutions": [],
        "error": None
    }
    output = agent._format_solutions(result)
    assert output == "No solutions found."


@pytest.mark.asyncio
async def test_agent_call(agent, mock_session):
    """Test the agent's main call method."""
    # Test normal question
    messages = [HumanMessage(content="Is Socrates mortal?")]
    response = await agent(messages)
    assert isinstance(response, AIMessage)
    assert "Yes" in response.content
    mock_session.call_tool.assert_called_once()
    
    # Test with debug config
    response = await agent(messages, config={"debug": True})
    assert "Generated Prolog code:" in response.content
    assert "Results:" in response.content
    
    # Test with non-human message
    messages = [AIMessage(content="Is Socrates mortal?")]
    response = await agent(messages)
    assert "Expected a question" in response.content


@pytest.mark.asyncio
async def test_error_handling(agent, mock_session):
    """Test handling of various error conditions."""
    messages = [HumanMessage(content="Is Socrates mortal?")]
    
    # Test Prolog execution error
    mock_session.call_tool.return_value = {
        "success": False,
        "error": "Syntax error",
        "solutions": []
    }
    response = await agent(messages)
    assert "Error:" in response.content
    assert "Syntax error" in response.content
    
    # Test empty model response
    agent.model.invoke.return_value = ""
    response = await agent(messages)
    assert isinstance(response, AIMessage)  # Should still return a valid message


@pytest.mark.asyncio
async def test_missing_tool(mock_model):
    """Test initialization with missing Prolog tool."""
    session = AsyncMock(spec=ClientSession)
    session.list_tools.return_value = []  # No tools available
    
    agent = PrologAgent(mock_model, session)
    with pytest.raises(ValueError, match="Prolog tool 'consult' not found"):
        await agent.initialize()