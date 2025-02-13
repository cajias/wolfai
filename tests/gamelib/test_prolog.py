"""Tests for the Prolog execution engine."""

import pytest
from wolfai.gamelib.prolog import PrologEngine, PrologResult

@pytest.fixture
def engine():
    """Create a fresh Prolog engine for each test."""
    return PrologEngine()

def test_basic_facts(engine):
    """Test loading and querying basic facts."""
    code = """
    werewolf(peter).
    werewolf(john).
    villager(mary).
    query(X) :- werewolf(X).
    """
    
    result = engine.execute(code)
    assert result.success
    assert len(result.solutions) == 2
    assert any('peter' in str(s) for s in result.solutions)
    assert any('john' in str(s) for s in result.solutions)

def test_rules_and_inference(engine):
    """Test rules and inference capabilities."""
    code = """
    werewolf(peter).
    werewolf(john).
    dead(peter).
    alive(X) :- werewolf(X), not(dead(X)).
    alive(X).
    """
    
    result = engine.execute(code)
    assert result.success
    assert len(result.solutions) == 1
    assert 'john' in str(result.solutions[0])
    assert 'peter' not in str(result.solutions[0])

def test_error_handling(engine):
    """Test handling of invalid Prolog code."""
    # Invalid syntax
    result = engine.execute("invalid_code !!! )")
    assert not result.success
    assert result.error is not None
    assert "Error" in result.error
    
    # Empty program
    result = engine.execute("")
    assert not result.success
    assert "Empty" in result.error

def test_state_management(engine):
    """Test that state is properly managed."""
    # Load initial facts
    engine.consult("""
    werewolf(peter).
    werewolf(john).
    """)
    
    # First query
    result1 = engine.query("werewolf(peter)")
    assert result1.success
    assert len(result1.solutions) == 1
    
    # Reset state
    engine.reset()
    
    # Query should now find nothing
    result2 = engine.query("werewolf(peter)")
    assert result2.success
    assert len(result2.solutions) == 0

def test_complex_queries(engine):
    """Test more complex game logic queries."""
    code = """
    % Game state
    werewolf(peter).
    werewolf(john).
    villager(mary).
    villager(sarah).
    voted_for(mary, peter).
    voted_for(sarah, peter).
    voted_for(peter, john).
    
    % Rules
    majority_vote(X) :-
        findall(Y, voted_for(Y, X), Voters),
        length(Voters, Count),
        Count >= 2.
        
    % Query
    majority_vote(X), werewolf(X).
    """
    
    result = engine.execute(code)
    assert result.success
    assert len(result.solutions) == 1
    assert 'peter' in str(result.solutions[0])