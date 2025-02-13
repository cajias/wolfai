"""LangGraph agent for Prolog reasoning."""

from typing import Dict, List, Any, Optional
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import ToolMessage, HumanMessage, AssistantMessage
from langchain_core.messages import BaseMessage
from pyswip import Prolog
import re

class PrologAgent:
    """Agent that converts natural language to Prolog and executes it."""
    
    def __init__(self, model):
        """Initialize with a language model for NL->Prolog conversion."""
        self.model = model
        self.prolog = Prolog()
        
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
        return code.strip()
    
    def execute_prolog(self, code: str) -> List[Dict[str, Any]]:
        """Execute Prolog code and return results."""
        # Clear previous state
        self.prolog.retractall()
        
        # Split into statements and query
        statements = code.split('\n')
        query = statements[-1]  # Last line should be the query
        facts_and_rules = '\n'.join(statements[:-1])
        
        # Assert facts and rules
        try:
            self.prolog.consult(facts_and_rules)
        except Exception as e:
            return [{"error": f"Error loading Prolog code: {str(e)}"}]
            
        # Execute query
        try:
            results = list(self.prolog.query(query))
            return results if results else [{"result": "No solutions found"}]
        except Exception as e:
            return [{"error": f"Error executing query: {str(e)}"}]
    
    def __call__(
        self,
        messages: List[BaseMessage],
        config: Optional[RunnableConfig] = None,
    ) -> AssistantMessage:
        """Process messages and return a response."""
        # Extract the last question
        last_message = messages[-1]
        if not isinstance(last_message, HumanMessage):
            return AssistantMessage(content="Expected a question from a human.")
            
        question = last_message.content
        
        # Convert to Prolog
        prolog_code = self.convert_to_prolog(question)
        
        # Execute and get results
        results = self.execute_prolog(prolog_code)
        
        # Format response
        if "error" in results[0]:
            response = f"Error: {results[0]['error']}"
        else:
            response = "Results:\n" + "\n".join(str(r) for r in results)
            
        return AssistantMessage(content=response)

def create_prolog_agent(model):
    """Create a new Prolog agent with the given language model."""
    return PrologAgent(model)