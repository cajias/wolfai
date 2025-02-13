"""LangGraph agent for Prolog reasoning."""

from typing import List, Optional
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.messages import BaseMessage
import re
from ..runtime.prolog import PrologEngine

class PrologAgent:
    """Agent that converts natural language to Prolog and executes it."""
    
    # Game-specific Prolog rules
    GAME_RULES = """
    % Clear any existing rules with these names
    :- dynamic alive/1, vote_count/2, majority_voted/1.
    :- retractall(alive(_)).
    :- retractall(vote_count(_,_)).
    :- retractall(majority_voted(_)).
    
    % Basic game rules
    alive(X) :- 
        (werewolf(X) ; villager(X)), 
        \\+ defined_dead(X).
            
    % Rule for counting votes
    vote_count(Person, Count) :-
        findall(Voter, voted_for(Voter, Person), Voters),
        length(Voters, Count).
            
    % Rule for majority votes - must be alive
    majority_voted(X) :-
        vote_count(X, Count),
        Count >= 2,
        alive(X).
    
    % Helper predicate to find living werewolves
    living_werewolf(X) :-
        werewolf(X),
        alive(X).
    """

    def __init__(self, model):
        """Initialize with a language model for NL->Prolog conversion."""
        self.model = model
        self.engine = PrologEngine()
        self._clean_duplicates = True

    def convert_to_prolog(self, question: str) -> str:
        """Convert natural language question to Prolog code."""
        # Prompt template for converting to Prolog
        prompt = """Convert the following question into a Prolog program.
        Include any necessary facts and rules, and end with a query that would answer the question.

        Question: {question}

        Format your response as valid Prolog code without any explanations.
        """

        response = self.model.invoke(prompt.format(question=question))
        # Extract just the Prolog code from the response
        prolog_code = self._extract_prolog_code(response)
        return prolog_code

    def _extract_prolog_code(self, response: str) -> str:
        """Extract clean Prolog code from model response."""
        # Remove markdown code blocks if present
        code = re.sub(r'```prolog\n(.*?)\n```', r'\1', response, flags=re.DOTALL)
        code = re.sub(r'```\n(.*?)\n```', r'\1', code, flags=re.DOTALL)
        code = code.strip()
        
        if self._clean_duplicates:
            # Remove duplicate facts
            lines = code.split('\n')
            seen = set()
            cleaned = []
            for line in lines:
                line = line.strip()
                if line and line not in seen:
                    seen.add(line)
                    cleaned.append(line)
            code = '\n'.join(cleaned)
            
        return code

    def _format_solutions(self, result) -> str:
        """Format Prolog solutions into readable text."""
        if not result.success:
            return f"Error: {result.error}"
        
        if not result.solutions:
            return "No solutions found."
            
        # Format solutions nicely
        lines = []
        for solution in result.solutions:
            if not solution:  # Empty solution means the query was satisfied
                lines.append("Yes.")
                continue
                
            parts = []
            for var, value in solution.items():
                parts.append(f"{var} = {value}")
            lines.append(", ".join(parts))
            
        return "\n".join(lines)

    def __call__(
        self,
        messages: List[BaseMessage],
        config: Optional[RunnableConfig] = None,
    ) -> AIMessage:
        """Process messages and return a response."""
        # Extract the last question
        last_message = messages[-1]
        if not isinstance(last_message, HumanMessage):
            return AIMessage(content="Expected a question from a human.")

        question = last_message.content

        # Convert to Prolog
        prolog_code = self.convert_to_prolog(question)
        
        # Combine game rules with the generated code
        full_code = self.GAME_RULES + "\n\n" + prolog_code

        # Execute the Prolog code
        result = self.engine.execute(full_code)
        
        # Format the results
        response = self._format_solutions(result)

        return AIMessage(content=response)

def create_prolog_agent(model):
    """Create a new Prolog agent with the given language model."""
    return PrologAgent(model)