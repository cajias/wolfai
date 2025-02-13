"""Tests for the Prolog LangGraph agent."""

import pytest
from unittest.mock import Mock
from langchain_core.messages import HumanMessage, AssistantMessage
from wolfai.agents.prolog import create_prolog_agent

@pytest.fixture
def mock_model():
    """Create a mock language model."""
    model = Mock()
    model.invoke.return_value = """
    % Facts about werewolves and villagers
    werewolf(peter).
    werewolf(john).
    villager(mary).
    villager(sarah).
    villager(james).
    
    % Rules for determining if someone is alive
    alive(X) :- werewolf(X), not(dead(X)).
    alive(X) :- villager(X), not(dead(X)).
    
    % Query to find all alive werewolves
    alive(X), werewolf(X).
    """
    return model

def test_prolog_agent_basic(mock_model):
    """Test basic Prolog agent functionality."""
    agent = create_prolog_agent(mock_model)
    
    # Test processing a question
    messages = [
        HumanMessage(content="Who are the living werewolves?")
    ]
    
    response = agent(messages)
    assert isinstance(response, AssistantMessage)
    assert "peter" in response.content.lower()
    assert "john" in response.content.lower()

def test_prolog_agent_error_handling(mock_model):
    """Test error handling in Prolog agent."""
    mock_model.invoke.return_value = "invalid prolog code !!!"
    agent = create_prolog_agent(mock_model)
    
    messages = [
        HumanMessage(content="Who are the living werewolves?")
    ]
    
    response = agent(messages)
    assert isinstance(response, AssistantMessage)
    assert "error" in response.content.lower()

def test_prolog_conversion(mock_model):
    """Test natural language to Prolog conversion."""
    agent = create_prolog_agent(mock_model)
    
    prolog_code = agent.convert_to_prolog(
        "Who are the villagers that are still alive?"
    )
    
    assert "villager" in prolog_code
    assert "alive" in prolog_code
    assert ":-" in prolog_code  # Check for rule definition

def test_complex_query(mock_model):
    """Test handling of more complex game scenarios."""
    # Update mock to return a more complex Prolog program
    mock_model.invoke.return_value = """
    % Game state facts
    werewolf(peter).
    werewolf(john).
    villager(mary).
    villager(sarah).
    villager(james).
    doctor(james).
    dead(peter).
    voted_for(mary, peter).
    voted_for(sarah, peter).
    voted_for(james, john).
    
    % Game rules
    alive(X) :- werewolf(X), not(dead(X)).
    alive(X) :- villager(X), not(dead(X)).
    
    % Voting rules
    majority_voted(X) :- 
        findall(Y, voted_for(Y, X), Voters),
        length(Voters, Count),
        Count >= 2.
        
    % Query to find who got the majority vote
    majority_voted(X), werewolf(X).
    """
    
    agent = create_prolog_agent(mock_model)
    messages = [
        HumanMessage(content="Which werewolf received the majority of votes?")
    ]
    
    response = agent(messages)
    assert isinstance(response, AssistantMessage)
    assert "peter" in response.content.lower()
    assert "john" not in response.content.lower()

def test_state_management(mock_model):
    """Test that Prolog state is properly managed between queries."""
    agent = create_prolog_agent(mock_model)
    
    # First query
    mock_model.invoke.return_value = """
    werewolf(peter).
    alive(peter).
    query(X) :- werewolf(X), alive(X).
    query(X).
    """
    
    messages1 = [HumanMessage(content="Is Peter alive?")]
    response1 = agent(messages1)
    
    # Second query with different state
    mock_model.invoke.return_value = """
    werewolf(john).
    dead(john).
    query(X) :- werewolf(X), not(dead(X)).
    query(X).
    """
    
    messages2 = [HumanMessage(content="Is John alive?")]
    response2 = agent(messages2)
    
    # Verify that states don't interfere
    assert "peter" not in response2.content.lower()
    assert "no solutions found" in response2.content.lower()
