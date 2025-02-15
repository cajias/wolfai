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
from langchain_mcp_tools import convert_mcp_to_langchain_tools, McpServerCleanupFn


class PrologAgent:
    """Agent that converts natural language to Prolog and executes it."""

    def __init__(self, model: BaseChatModel, session: ClientSession):
        """Initialize with a language model for NL->Prolog conversion."""
        self.model = model
        self.session = session
        self._clean_duplicates = True

    async def initialize(self):
        """Initialize the MCP session."""
        print("Initializing MCP session...")
        await self.session.initialize()
        print("MCP session initialized.")
        # Make sure Prolog tool is available
        tools = await self.session.list_tools()
        tools_map = {tool.name: tool for tool in tools}
        if "consult" not in tools_map:
            raise ValueError("Prolog tool 'consult' not found in available tools")
        self.model.bind_tools(tools_map)

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
        response = await self.model.ainvoke(question)
        print(response)
        return AIMessage(content=response.content)


async def create_prolog_agent(model, prolog_server_params: StdioServerParameters):
    """Create a new Prolog agent with the given language model and server parameters."""
    print("Creating Prolog agent")
    async with stdio_client(prolog_server_params) as (read, write):
        print("Creating Session")
        async with ClientSession(read, write) as session:
            print("Prolog agent session created")
            agent = PrologAgent(model, session)
            print("Prolog agent created")
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
            args=["-m", "wolfai.tools.pl.prolog_mcp_server"],
            env=None
        )

        # Create language model
        model = ChatOpenAI(api_key=os.environ.get("OPEN_AI_API_KEY"))

        # Create and initialize agent
        agent = await create_prolog_agent(model, server_params)

        # Example usage
        messages = [HumanMessage(content="If all humans are mortal and Socrates is human, is Socrates mortal?")]
        response = await agent(messages, config={"debug": True})
        print(response.content)


    asyncio.run(main())
