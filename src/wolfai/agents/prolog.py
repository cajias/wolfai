"""LangGraph agent for Prolog reasoning."""
import os
import re
from typing import List, Optional, Dict, Any, Tuple

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_tools import convert_mcp_to_langchain_tools


class PrologAgent:
    """Agent that converts natural language to Prolog and executes it."""

    def __init__(self, model: BaseChatModel, session: ClientSession):
        """Initialize with a language model for NL->Prolog conversion."""
        self.model = model
        self.session = session
        self._clean_duplicates = True

    async def initialize(self):
        """Initialize the MCP session."""
        await self.session.initialize()

        # Make sure Prolog tool is available
        tools = await self.session.list_tools()
        tools_map = {tool.name: tool for tool in tools}
        if "consult" not in tools_map:
            raise ValueError("Prolog tool 'consult' not found in available tools")

        # Convert MCP tools to LangChain format
        self.tools = convert_mcp_to_langchain_tools(tools)
        self.model.bind_tools(self.tools)

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

        # Prepare system message with instructions
        system_message = """You are an expert in Prolog programming. When given a question, you:
1. Convert it to Prolog facts and rules
2. Use the 'consult' tool to load the Prolog code
3. Use the 'query' tool to ask questions
4. Return both the Prolog code and the query results

For example, if asked "Is Socrates mortal?", you would:
1. Write Prolog code:
   human(socrates).
   mortal(X) :- human(X).
2. Load it with consult
3. Query with: mortal(socrates).
4. Return the results

Always show your work by including the Prolog code you wrote."""

        # Add system message to model
        self.model.system_message = system_message
        
        # Get response from model with tools
        response = await self.model.ainvoke(last_message.content)
        return AIMessage(content=response.content)


async def create_prolog_agent(model: BaseChatModel, prolog_server_params: StdioServerParameters) -> PrologAgent:
    """Create a new Prolog agent with the given language model and server parameters."""
    async with stdio_client(prolog_server_params) as (read, write):
        async with ClientSession(read, write) as session:
            agent = PrologAgent(model, session)
            await agent.initialize()
            return agent


async def main():
    """Run an example Prolog agent session."""
    # Set up server parameters for the Prolog MCP server
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "wolfai.tools.pl.prolog_mcp_server"],
        env=None
    )

    # Create language model
    from langchain_openai import ChatOpenAI
    model = ChatOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    # Create and initialize agent
    agent = await create_prolog_agent(model, server_params)

    # Example usage
    messages = [HumanMessage(content="If all humans are mortal and Socrates is human, is Socrates mortal?")]
    response = await agent(messages, config={"debug": True})
    print(response.content)


# Example usage
if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv

    load_dotenv()
    asyncio.run(main())