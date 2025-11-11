"""A functional Prolog execution engine implementing safe, isolated program execution.

This module provides a clean interface for running Prolog programs with proper state
management and isolation. It uses immutable state objects and automatic namespacing
to prevent conflicts between different executions.

The module follows functional programming principles where possible:
- State is represented by immutable PrologState objects
- Functions don't modify their inputs
- Each execution creates a fresh environment

Key features:
- Automatic namespacing of predicates
- Clean state management
- Comprehensive error handling
- Safe query execution
"""

import contextlib
import uuid
from collections.abc import Generator
from dataclasses import dataclass
from typing import Any, Optional

from pyswip import Prolog

from wolfai.tools.mcp_utils import tool


@dataclass(frozen=True)
class PrologState:
    """Immutable representation of a Prolog program's state.

    This class captures the complete state of a Prolog program, including all facts
    and rules, as well as the last executed query. Being immutable (frozen=True)
    ensures that program state can't be accidentally modified.

    Attributes:
        facts: List of strings, each representing a Prolog fact or rule
        query: Optional string containing the last executed query, if any
    """
    facts: list[str]  # Each fact/rule as a string
    query: Optional[str] = None


@dataclass
class PrologResult:
    """Encapsulates the result of a Prolog query evaluation.

    This class provides a structured way to handle both successful query results
    and potential errors. For successful queries, it contains a list of variable
    bindings. For failed queries, it includes an error message.

    Attributes:
        success: Boolean indicating if the query executed successfully
        solutions: List of dictionaries mapping variable names to their bindings
        error: Optional string containing error message if the query failed
    """
    success: bool
    solutions: list[dict[str, Any]]
    error: Optional[str] = None


@contextlib.contextmanager
def _temporary_prolog_env() -> Generator[tuple[Prolog, str], None, None]:
    """Create an isolated Prolog environment for safe query execution.

    This context manager ensures that each query execution happens in a fresh,
    isolated environment. It:
    1. Creates a new Prolog instance
    2. Generates a unique namespace for predicates
    3. Declares common predicates as dynamic
    4. Cleans up resources when done

    The namespace prevents conflicts between different executions and ensures
    that each query runs in isolation.

    Yields:
        tuple: (Prolog instance, namespace string)
    """
    prolog = Prolog()

    # Generate a unique namespace to prevent predicate conflicts
    namespace = f"ns_{uuid.uuid4().hex}"

    try:
        # Declare common predicates as dynamic within our namespace
        # This allows us to assert facts at runtime
        for pred in ["person", "city", "parent", "grandparent"]:
            list(prolog.query(f"dynamic({namespace}_{pred}/1), dynamic({namespace}_{pred}/2)"))

        yield prolog, namespace

    finally:
        # Ensure proper cleanup of Prolog environment
        prolog = None


def _namespace_predicate(pred: str, namespace: str) -> str:
    """Add namespace prefix to a predicate to prevent naming conflicts.

    This function handles both simple predicates and complex rules with body clauses.
    For rules (containing ':-'), it namespaces both the head and each predicate in
    the body, being careful not to namespace built-in predicates.

    Args:
        pred: The predicate or rule to namespace
        namespace: The namespace prefix to add

    Returns:
        The predicate with namespace prefix added

    Examples:
        >>> _namespace_predicate("person(john)", "ns1")
        "ns1_person(john)"
        >>> _namespace_predicate("parent(X, Y) :- person(X), person(Y)", "ns1")
        "ns1_parent(X, Y) :- ns1_person(X), ns1_person(Y)"
    """
    if ":-" in pred:
        # For rules, we need to namespace both head and body
        head, body = pred.split(":-", 1)
        head = _namespace_predicate(head.strip(), namespace)
        # Namespace each predicate in the body, but not built-ins
        body_parts = []
        for part in body.split(","):
            part = part.strip()
            if "(" in part:  # Only namespace predicates, not built-ins
                body_parts.append(_namespace_predicate(part, namespace))
            else:
                body_parts.append(part)
        return f"{head} :- {', '.join(body_parts)}"

    if "(" not in pred:  # No arguments
        return f"{namespace}_{pred}"

    pred_name = pred[:pred.index("(")]
    pred_args = pred[pred.index("("):]
    return f"{namespace}_{pred_name}{pred_args}"


@tool()
def parse_prolog_code(code: str) -> list[str]:
    """Parse raw Prolog code into individual statements.

    This function handles various formats of Prolog code, including:
    - Multiple statements per line
    - Statements split across lines
    - Comments (starting with %)
    - Empty lines

    Args:
        code: String containing Prolog code

    Returns:
        List of individual Prolog statements, with comments and empty lines removed

    The function ensures that each statement is complete (ends with a period) and
    properly formatted for execution.
    """
    lines = []
    current = []

    for line in code.split("\n"):
        line = line.strip()
        if not line or line.startswith("%"):
            continue

        current.append(line)
        if line.endswith("."):
            # Complete statement found
            lines.append(" ".join(current).strip())
            current = []

    # Handle any remaining content without trailing period
    if current:
        lines.append(" ".join(current).strip())

    return lines


def _load_facts(prolog: Prolog, facts: list[str], namespace: str) -> Optional[str]:
    """Load facts and rules into a Prolog environment with proper namespacing.

    This function:
    1. Analyzes predicates to determine their arity
    2. Declares all predicates as dynamic with correct arity
    3. Adds namespace prefix to all predicates
    4. Asserts facts in the Prolog environment

    The function handles both simple facts and complex rules, ensuring that
    all predicates are properly declared before use.

    Args:
        prolog: Prolog environment to load facts into
        facts: List of facts and rules to load
        namespace: Namespace prefix for predicates

    Returns:
        None if successful, error message string if failed
    """
    if not facts:
        return None

    try:
        seen_predicates, arity_map = _analyze_predicates(facts)
        _declare_predicates(prolog, namespace, seen_predicates, arity_map)

        for fact in facts:
            fact = fact.strip()
            if not fact or fact.startswith("%"):
                continue

            if fact.endswith("."):
                fact = fact[:-1]

            fact = _namespace_predicate(fact, namespace)
            list(prolog.query(f"asserta(({fact}))"))

        return None
    except Exception as e:
        return str(e)


DEFAULT_ARITY = 2


def _analyze_predicates(facts: list[str]) -> tuple[set[str], dict[str, int]]:
    """Analyze predicates and determine arity for each."""
    seen_predicates: set[str] = set()
    arity_map: dict[str, int] = {}
    for fact in facts:
        original = fact
        if fact.endswith("."):
            fact = fact[:-1]
        if ":-" in fact:
            head = fact[:fact.index("(")]
            arity = fact.count(",") + 1 if "(" in fact else 0
            seen_predicates.add(head)
            arity_map[head] = arity
            for part in original.split(":-")[1].split(","):
                part = part.strip()
                if "(" in part:
                    pred = part[:part.index("(")]
                    arity = part.count(",") + 1
                    seen_predicates.add(pred)
                    arity_map[pred] = arity
        else:
            pred = fact[:fact.index("(")] if "(" in fact else fact
            arity = fact.count(",") + 1 if "(" in fact else 0
            seen_predicates.add(pred)
            arity_map[pred] = arity
    return seen_predicates, arity_map


def _declare_predicates(
    prolog: Prolog, namespace: str, seen_predicates: set[str], arity_map: dict[str, int],
) -> None:
    """Declare predicates as dynamic with the correct arity."""
    for pred in seen_predicates:
        arity = arity_map.get(pred, DEFAULT_ARITY)
        list(prolog.query(f"dynamic({namespace}_{pred}/{arity})"))


@tool
def run_query(prolog: Prolog, query: str, namespace: str) -> PrologResult:
    """Execute a query in a Prolog environment and collect results.

    This function:
    1. Adds namespace prefix to the query
    2. Executes the query and collects all solutions
    3. Formats solutions as dictionaries of variable bindings
    4. Handles errors and provides meaningful error messages

    Args:
        prolog: Prolog environment to run query in
        query: Query string to execute
        namespace: Namespace prefix for predicates

    Returns:
        PrologResult containing either:
        - List of solutions (dictionaries of variable bindings)
        - Error message if query failed
    """
    query = query.strip().rstrip(".")
    if not query:
        return PrologResult(
            success=False,
            solutions=[],
            error="Empty query",
        )

    try:
        # Add namespace prefix to query predicates
        query = _namespace_predicate(query, namespace)

        # Collect and format solutions
        solutions = []
        for sol in prolog.query(query):
            solution = {}
            for k, v in sol.items():
                # Skip unbound variables
                if hasattr(v, "__class__") and v.__class__.__name__ == "Variable":
                    continue
                solution[k] = str(v)
            if solution:
                solutions.append(solution)

        return PrologResult(success=True, solutions=solutions)
    except Exception as e:
        # Extract meaningful part of error message
        error_msg = str(e)
        if "Caused by" in error_msg:
            error_msg = error_msg.split("Caused by: ")[1].split("Returned:")[0].strip()
        return PrologResult(
            success=False,
            solutions=[],
            error=f"Error executing query: {error_msg}",
        )

@tool
def consult(code: str) -> PrologState:
    """Parse Prolog code and create initial program state.

    This is typically the first function called when working with a Prolog program.
    It takes raw Prolog code and creates a PrologState object containing the parsed
    facts and rules.

    Args:
        code: String containing Prolog code (facts and rules)

    Returns:
        PrologState object containing parsed facts

    Example:
        >>> code = '''
        ...     person(john).
        ...     person(mary).
        ...     parent(john, mary).
        ... '''
        >>> state = consult(code)
    """
    facts = parse_prolog_code(code)
    return PrologState(facts=facts)


def _execute(state: PrologState, query: str) -> tuple[PrologResult, PrologState]:
    """Execute a query against a program state with proper isolation.

    This function:
    1. Creates a fresh Prolog environment
    2. Loads the program state (facts and rules)
    3. Executes the query
    4. Returns results and updated state

    The function ensures that each query runs in isolation by using a unique
    namespace and fresh Prolog environment.

    Args:
        state: Current PrologState containing facts and rules
        query: Query string to execute

    Returns:
        Tuple containing:
        - PrologResult with query solutions or error
        - New PrologState with updated query history

    Example:
        >>> result, new_state = _execute(state, "parent(X, Y)")
        >>> if result.success:
        ...     for solution in result.solutions:
        ...         print(f"X = {solution['X']}, Y = {solution['Y']}")
    """
    with _temporary_prolog_env() as (prolog, namespace):
        # Load facts with proper namespacing
        error = _load_facts(prolog, state.facts, namespace)
        if error:
            result = PrologResult(
                success=False,
                solutions=[],
                error=f"Error loading program: {error}",
            )
        else:
            # Execute query in isolated environment
            result = run_query(prolog, query, namespace)

    # Create new state with updated query history
    new_state = PrologState(
        facts=state.facts,
        query=query,
    )
    return result, new_state
