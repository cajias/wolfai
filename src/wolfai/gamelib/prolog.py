"""Prolog execution engine for game logic."""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from pyswip import Prolog

@dataclass
class PrologResult:
    """Result of a Prolog query execution."""
    success: bool
    solutions: List[Dict[str, Any]]
    error: Optional[str] = None

class PrologEngine:
    """Engine for executing Prolog code."""
    
    def __init__(self):
        """Initialize the Prolog engine."""
        self.prolog = Prolog()
        
    def reset(self):
        """Clear all facts and rules."""
        self.prolog.retractall()
        
    def consult(self, code: str) -> PrologResult:
        """Load facts and rules into the engine.
        
        Args:
            code: Prolog code containing facts and rules
            
        Returns:
            PrologResult indicating success/failure and any errors
        """
        try:
            self.prolog.consult(code)
            return PrologResult(success=True, solutions=[])
        except Exception as e:
            return PrologResult(
                success=False,
                solutions=[],
                error=f"Error loading Prolog code: {str(e)}"
            )
    
    def query(self, query: str) -> PrologResult:
        """Execute a Prolog query.
        
        Args:
            query: Prolog query to execute
            
        Returns:
            PrologResult containing query solutions or error
        """
        try:
            solutions = list(self.prolog.query(query))
            return PrologResult(
                success=True,
                solutions=solutions if solutions else []
            )
        except Exception as e:
            return PrologResult(
                success=False,
                solutions=[],
                error=f"Error executing query: {str(e)}"
            )
    
    def execute(self, code: str) -> PrologResult:
        """Execute complete Prolog program including query.
        
        The last line of the code is treated as the query.
        Previous lines are treated as facts and rules.
        
        Args:
            code: Complete Prolog program
            
        Returns:
            PrologResult containing solutions or error
        """
        # Split into statements and query
        statements = code.strip().split('\n')
        if not statements:
            return PrologResult(
                success=False,
                solutions=[],
                error="Empty Prolog program"
            )
            
        query = statements[-1].strip()  # Last line is query
        facts_and_rules = '\n'.join(statements[:-1])
        
        # Clear previous state
        self.reset()
        
        # Load facts and rules
        result = self.consult(facts_and_rules)
        if not result.success:
            return result
            
        # Execute query
        return self.query(query)