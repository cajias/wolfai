"""LangGraph agent for Prolog reasoning."""
import os
import logging
import sys
import asyncio
from typing import List, Optional, Dict, Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_tools import convert_mcp_to_langchain_tools

# Set up logging with more detail
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


class PrologAgent:
    """Agent that converts natural language to Prolog and executes it."""

    def __init__(self, model: BaseChatModel, session: ClientSession):
        """Initialize with a language model for NL->Prolog conversion."""
        self.model = model
        self.session = session
        self.tools = None
        logger.debug("PrologAgent initialized with model and session")

    async def initialize(self):
        """Initialize the MCP session."""
        try:
            logger.debug("Starting MCP session initialization")
            await asyncio.wait_for(self.session.initialize(), timeout=10.0)
            logger.debug("Session initialized successfully")

            # List tools with timeout
            logger.debug("Listing available tools")
            tools = await asyncio.wait_for(self.session.list_tools(), timeout=5.0)
            tools_map = {tool.name: tool for tool in tools}
            logger.debug(f"Available tools: {list(tools_map.keys())}")
            
            if "consult" not in tools_map:
                logger.error("Required 'consult' tool not found")
                raise ValueError("Prolog tool 'consult' not found in available tools")

            # Convert and bind tools
            logger.debug("Converting tools to LangChain format")
            self.tools = convert_mcp_to_langchain_tools(tools)
            logger.debug("Binding tools to model")
            self.model.bind_tools(self.tools)
            logger.info("Agent initialization completed successfully")
            
        except asyncio.TimeoutError as e:
            logger.error("Timeout during initialization", exc_info=True)
            raise Exception("Initialization timed out") from e
        except Exception as e:
            logger.error(f"Error during initialization: {str(e)}", exc_info=True)
            raise

    async def __call__(
        self,
        messages: List[BaseMessage],
        config: Optional[RunnableConfig] = None,
    ) -> AIMessage:
        """Process messages and return a response."""
        try:
            # Extract the last question
            last_message = messages[-1]
            if not isinstance(last_message, HumanMessage):
                logger.warning("Received non-human message")
                return AIMessage(content="Expected a question from a human.")

            logger.debug(f"Processing message: {last_message.content[:100]}...")

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
            logger.debug("Setting system message")
            self.model.system_message = system_message
            
            # Get response from model with tools
            logger.debug("Invoking model with message")
            try:
                response = await asyncio.wait_for(
                    self.model.ainvoke(last_message.content),
                    timeout=30.0
                )
                logger.debug("Model response received successfully")
                return AIMessage(content=response.content)
            except asyncio.TimeoutError:
                logger.error("Model invocation timed out")
                return AIMessage(content="I apologize, but the operation timed out. Please try again.")
                
        except Exception as e:
            logger.error(f"Error in agent call: {str(e)}", exc_info=True)
            return AIMessage(content=f"I encountered an error: {str(e)}")


async def create_prolog_agent(model: BaseChatModel, prolog_server_params: StdioServerParameters) -> PrologAgent:
    """Create a new Prolog agent with the given language model and server parameters."""
    logger.info("Creating Prolog agent")
    try:
        logger.debug("Creating stdio client")
        async with stdio_client(prolog_server_params) as (read, write):
            logger.debug("Creating MCP session")
            async with ClientSession(read, write) as session:
                logger.debug("Initializing PrologAgent")
                agent = PrologAgent(model, session)
                try:
                    logger.debug("Starting agent initialization")
                    await asyncio.wait_for(agent.initialize(), timeout=10.0)
                    logger.info("Prolog agent created successfully")
                    return agent
                except asyncio.TimeoutError:
                    logger.error("Agent initialization timed out")
                    raise Exception("Prolog agent initialization timed out")
                except Exception as e:
                    logger.error(f"Error initializing agent: {str(e)}", exc_info=True)
                    raise
    except Exception as e:
        logger.error(f"Error creating Prolog agent: {str(e)}", exc_info=True)
        raise


async def run_example():
    """Run an example Prolog agent session with error handling."""
    try:
        logger.info("Starting example Prolog agent session")
        
        # Set up server parameters
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "wolfai.tools.pl.prolog_mcp_server"],
            env=None
        )

        # Create language model
        from langchain_openai import ChatOpenAI
        logger.debug("Creating ChatOpenAI instance")
        model = ChatOpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            timeout=30.0
        )

        # Create and initialize agent
        logger.debug("Creating Prolog agent")
        try:
            agent = await asyncio.wait_for(
                create_prolog_agent(model, server_params),
                timeout=15.0
            )
        except asyncio.TimeoutError:
            logger.error("Agent creation timed out")
            print("Agent creation timed out. Please check the server status and try again.")
            return
        except Exception as e:
            logger.error(f"Failed to create agent: {str(e)}", exc_info=True)
            print(f"Failed to create agent: {str(e)}")
            return

        # Example usage
        logger.debug("Running example query")
        messages = [HumanMessage(content="If all humans are mortal and Socrates is human, is Socrates mortal?")]
        
        try:
            response = await asyncio.wait_for(
                agent(messages, config={"debug": True}),
                timeout=30.0
            )
            print(response.content)
        except asyncio.TimeoutError:
            logger.error("Query execution timed out")
            print("The query timed out. Please try again.")
        except Exception as e:
            logger.error(f"Error during query execution: {str(e)}", exc_info=True)
            print(f"Error during query execution: {str(e)}")
        
    except Exception as e:
        logger.error(f"Unexpected error in example run: {str(e)}", exc_info=True)
        print(f"An unexpected error occurred: {str(e)}")


async def main():
    """Main entry point with proper signal handling."""
    try:
        # Set up signal handlers
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(cleanup()))
            
        await run_example()
    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)
        sys.exit(1)


async def cleanup():
    """Cleanup function for graceful shutdown."""
    logger.info("Starting cleanup")
    try:
        # Add any cleanup code here
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    import signal
    from dotenv import load_dotenv

    load_dotenv()
    asyncio.run(main())