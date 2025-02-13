"""LangGraph agent for Prolog reasoning."""

import re
from typing import List, Optional, Dict, Any

from langchain_core.messages import BaseMessage
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class PrologAgent:
    """Agent that converts natural language to Prolog and executes it."""

    def __init__(self, model, session: ClientSession):
        """Initialize with a language model for NL->Prolog conversion."""
        self.model = model
        self.session = session
        self._clean_duplicates = True

    async def initialize(self):
        """Initialize the MCP session."""
        await self.session.initialize()
        # Make sure Prolog tool is available
        tools = await self.session.list_tools()
        if not any(t.name == "consult" for t in tools):
            raise ValueError("Prolog tool 'consult' not found in available tools")

    def convert_to_prolog(self, question: str) -> str:
        """Convert natural language question to Prolog code."""
        # Prompt template for converting to Prolog
        prompt = """Convert the following question into a Prolog program.
        Include any necessary facts and rules, and end with a query that would answer the question.

        Question: {question}

        Format your response as valid Prolog code without any explanations or markdown.
        Make sure to end queries with a period.
        """

        response = self.model.invoke(prompt.format(question=question))
        # Extract just the Prolog code from the response
        prolog_code = self._extract_prolog_code(response)
        return prolog_code

    def _extract_prolog_code(self, response: str) -> str:
        """Extract clean Prolog code from model response."""
        # First try to find code blocks
        matches = re.findall(r'```(?:prolog)?\s*(.*?)\s*```', response, flags=re.DOTALL)
        if matches:
            code = matches[0]  # Take the first code block
        else:
            # No code blocks found, use the entire response
            code = response

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

    def _format_solutions(self, result: Dict[str, Any]) -> str:
        """Format Prolog solutions into readable text."""
        if not result.get('success', False):
            return f"Error: {result.get('error', 'Unknown error')}"

        solutions = result.get('solutions', [])
        if not solutions:
            return "No solutions found."

        # Format solutions nicely
        lines = []
        for solution in solutions:
            if not solution:  # Empty solution means the query was satisfied
                lines.append("Yes.")
                continue

            parts = []
            for var, value in solution.items():
                parts.append(f"{var} = {value}")
            lines.append(", ".join(parts))

        return "\n".join(lines)

    async def __call__(
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

        # Execute the Prolog code using the MCP session
        result = await self.session.call_tool("consult", arguments={"code": prolog_code})

        # Format the results
        response = self._format_solutions(result)

        # Include the generated Prolog code in debug mode
        if config and config.get('debug'):
            response = f"Generated Prolog code:\n{prolog_code}\n\nResults:\n{response}"

        return AIMessage(content=response)


async def create_prolog_agent(model, prolog_server_params: StdioServerParameters):
    """Create a new Prolog agent with the given language model and server parameters."""
    async with stdio_client(prolog_server_params) as (read, write):
        async with ClientSession(read, write) as session:
            agent = PrologAgent(model, session)
            await agent.initialize()
            return agent


# Example usage
if __name__ == "__main__":
    import asyncio
    from langchain_openai import ChatOpenAI
    from dotenv import load_dotenv

    load_dotenv()


    async def main():
        # Set up server parameters for the Prolog MCP server
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "src.wolfai.tools.pl.prolog_mcp_server"],
            env=None
        )

        # Create language model
        model = ChatOpenAI()

        # Create and initialize agent
        agent = await create_prolog_agent(model, server_params)

        # Example usage
        messages = [HumanMessage(content="If all humans are mortal and Socrates is human, is Socrates mortal?")]
        response = await agent(messages, config={"debug": True})
        print(response.content)


    asyncio.run(main())
