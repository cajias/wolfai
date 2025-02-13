"""LangGraph agent for Prolog reasoning."""

from typing import List, Optional
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import HumanMessage, AssistantMessage
from langchain_core.messages import BaseMessage
import re
from ..gamelib.prolog import PrologEngine

class PrologAgent:
    """Agent that converts natural language to Prolog and executes it."""
    
    def __init__(self, model):
        """Initialize with a language model for NL->Prolog conversion."""
        self.model = model
        self.prolog = PrologEngine()
        
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
        result = self.prolog.execute(prolog_code)
        
        # Format response
        if not result.success:
            response = f"Error: {result.error}"
        else:
            if result.solutions:
                response = "Results:\n" + "\n".join(str(s) for s in result.solutions)
            else:
                response = "No solutions found."
            
        return AssistantMessage(content=response)

def create_prolog_agent(model):
    """Create a new Prolog agent with the given language model."""
    return PrologAgent(model)