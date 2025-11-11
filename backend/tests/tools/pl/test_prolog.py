"""Tests for the functional Prolog execution engine."""

import pytest


# Skip entire module if SWI-Prolog is not available
try:
    import pyswip  # noqa: F401
except Exception:
    pytest.skip("SWI-Prolog not available", allow_module_level=True)

from wolfai.tools.pl.prolog import _execute, consult, parse_prolog_code


def test_parse_prolog_code():
    """Test parsing Prolog code into statements."""
    code = """
    % Basic facts
    parent(john, mary).
    parent(john, peter).

    % Rules
    grandparent(X, Y) :-
        parent(X, Z),
        parent(Z, Y).

    % Empty lines and comments should be ignored
    % Like this one
    parent(mary, paul).
    """

    facts = parse_prolog_code(code)
    assert len(facts) == 4
    assert "parent(john, mary)." in facts
    assert "parent(john, peter)." in facts
    assert "parent(mary, paul)." in facts
    assert any("grandparent(X, Y)" in f and "parent(X, Z)" in f for f in facts)

def test_consult_basic():
    """Test loading basic Prolog code."""
    code = """
    person(peter).
    person(john).
    person(mary).
    """

    state = consult(code)
    assert len(state.facts) == 3
    assert state.query is None

def test_execute_simple_query():
    """Test executing a simple query."""
    # Create initial state
    state = consult("""
    person(peter).
    person(john).
    person(mary).
    """)

    # Execute query
    result, new_state = _execute(state, "person(X)")

    # Check result
    assert result.success
    assert len(result.solutions) == 3
    solutions = [sol["X"] for sol in result.solutions]
    assert "peter" in solutions
    assert "john" in solutions
    assert "mary" in solutions

    # Check new state
    assert new_state.facts == state.facts
    assert new_state.query == "person(X)"

def test_execute_with_rules():
    """Test executing queries with rules."""
    state = consult("""
    parent(john, mary).
    parent(john, peter).
    parent(mary, paul).

    grandparent(X, Y) :-
        parent(X, Z),
        parent(Z, Y).
    """)

    result, _new_state = _execute(state, "grandparent(john, Y)")

    assert result.success
    assert len(result.solutions) == 1
    assert result.solutions[0]["Y"] == "paul"

def test_execute_error_handling():
    """Test handling of invalid Prolog code."""
    # Invalid syntax in facts
    state = consult("""
    invalid(((()))).
    person(x).
    """)

    result, new_state = _execute(state, "person(X)")
    assert not result.success
    assert result.error is not None

    # Invalid query
    state = consult("person(john).")
    result, _new_state = _execute(state, "invalid_query(")
    assert not result.success
    assert result.error is not None

def test_empty_query():
    """Test handling of empty queries."""
    state = consult("person(john).")
    result, _new_state = _execute(state, "")
    assert not result.success
    assert "Empty query" in result.error

def test_state_isolation():
    """Test that state doesn't leak between executions."""
    # First execution
    state1 = consult("person(john).")
    result1, _ = _execute(state1, "person(X)")
    assert result1.success
    assert len(result1.solutions) == 1
    assert result1.solutions[0]["X"] == "john"

    # Second execution with different facts
    state2 = consult("city(london).")
    result2, _ = _execute(state2, "person(X)")
    assert result2.success  # Query succeeds but finds no solutions
    assert not result2.solutions  # Should not see facts from state1
