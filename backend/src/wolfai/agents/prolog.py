"""LangGraph agent for Prolog reasoning."""
import asyncio
import logging
import sys
from typing import List, Optional

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from wolfai.agents.utils import invoke_agent_with_retry
from wolfai.tools.langchain_utils import get_mcp_tools_as_langchain

# Set up logging with more detail
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


class PrologAgent:
    """Agent that converts natural language to Prolog and executes it.

    This agent integrates a language model and a Prolog reasoning engine. It converts natural
    language into Prolog logic and executes those logical statements through a Prolog server.
    Key features involve dynamic tool usage and zero-shot reasoning capabilities, enabled by
    LangChain's agent framework.

    Features:
    - Converts natural language into logical Prolog statements.
    - Executes the Prolog logic via the stdio protocol.
    - Dynamically retrieves and integrates tools for solving complex queries.
    - Applies advanced reasoning by leveraging the capabilities of LangChain's agent framework.

    Attributes:
        model (BaseChatModel): Language model performing natural language to Prolog conversion.
        prolog_server_params (StdioServerParameters): Configuration parameters for Prolog server connection.
        agent_executor (Optional): LangChain's agent executor for processing queries with Prolog tools.
    """

    def __init__(self, model: BaseChatModel, prolog_server_params: StdioServerParameters):
        """
        Initialize the Prolog Agent.

        This constructor sets up the agent by attaching the provided language model and
        server parameters to the internal attributes. The `agent_executor` remains uninitialized
        until the `initialize()` method is invoked.

        Args:
            model (BaseChatModel): Language model used to parse natural language into logical Prolog statements.
            prolog_server_params (StdioServerParameters): Parameters used to configure and establish a Prolog connection.

        Example:
            ```
            from langchain_core.language_models import SomeBaseChatModel
            model = SomeBaseChatModel(...)
            params = StdioServerParameters(client="path/to/prolog", ...)
            agent = PrologAgent(model, params)
            ```
        """
        self.model = model
        self.prolog_server_params = prolog_server_params
        self.agent_executor = None

    async def initialize(self):
        """
        Initialize communication with the Prolog server and setup tools.

        This method performs the critical task of connecting to the Prolog server, initializing
        its session, and integrating Prolog-compatible tools into the LangChain framework.
        It creates the `agent_executor` using the retrieved tools and binds it to the language model for
        dynamic query resolution.

        Detailed Workflow:
        1. Establishes a client session for Prolog communication through stdio.
        2. Dynamically retrieves Prolog tools as LangChain-compatible tools.
        3. Instantiates LangChain's agent executor in "zero-shot reasoning" mode.

        Key Functionalities:
        - Enables tool-based dynamic reasoning via LangChain.
        - Validates server responses, ensuring readiness for the Prolog engine.

        Raises:
            Exception: Any error during initialization is logged and re-raised to interrupt execution. Common errors include:
              - Failure to connect to the Prolog server.
              - Issues during tool fetching or integration.
              - Internal server errors.

        Logs:
            - Debug logs during every major checkpoint to trace progress and debugging.
            - Errors are logged alongside stack traces for detailed issue diagnosis.

        Example:
            ```
            agent = PrologAgent(model, prolog_server_params)
            await agent.initialize()  # Must be called before querying the agent
            ```

        Returns:
            None
        """
        try:
            logger.debug("Creating stdio client for Prolog communication")
            async with stdio_client(self.prolog_server_params) as (read, write):
                logger.debug("Stdio client created successfully, initializing session")
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    logger.debug("Session initialized successfully, retrieving tools")

                    langchain_mcp_tools = await get_mcp_tools_as_langchain(session)
                    logger.debug(f"Successfully retrieved {len(langchain_mcp_tools)} tools")

                    logger.debug("Initializing LangChain agent executor")
                    self.agent_executor = create_agent(
                        model=self.model,
                        tools=langchain_mcp_tools,
                        system_prompt="You are a helpful assistant that can reason using Prolog logic. Use the available tools to execute Prolog queries and provide logical reasoning.",
                        debug=True
                    )
                    logger.debug("Agent executor initialized successfully")
        except Exception as e:
            logger.error(f"Error during Prolog agent initialization: {str(e)}", exc_info=True)
            raise

    async def __call__(
        self,
        messages: List[BaseMessage],
        config: Optional[RunnableConfig] = None,
    ) -> AIMessage:
        """
        Process a sequence of messages and generate a Prolog reasoning-powered AI response.

        This method interprets incoming human-like messages, uses the `agent_executor` for
        reasoning, and generates a response based on the Prolog server tools and logic.

        Args:
            messages (List[BaseMessage]): Sequence of messages in the conversation.
                - The most recent message must be a `HumanMessage` containing the query.
                - Supports full conversational context but focuses on the last query.
            config (Optional[RunnableConfig]): Configuration details affecting response generation.

        Returns:
            AIMessage: The agent's response, containing reasoning or retrieval results.

        Workflow:
        1. Validates `agent_executor` initialization. If uninitialized, a `RuntimeError` is raised.
        2. Verifies if the last message is from a human. If not, returns a default clarification response.
        3. Processes the human query, invokes the `agent_executor` to compute a solution, and returns it.
        4. Handles timeouts and errors to ensure graceful degradation with explanatory responses.

        Raises:
            RuntimeError: Raised if called before invoking `initialize()`.
            Exception: Captures unexpected issues during runtime. Logs errors with stack traces.

        Logs:
            - Debug logs to trace message processing and logic execution results.
            - Warnings for unexpected message types and errors for unexpected system issues.

        Error Handling:
        - On timeout, it informs the user and guides a retry.
        - On general errors, returns a polite error message with no stack trace leakage.

        Example:
            ```
            messages = [HumanMessage(content="What is the capital of France?")]
            response = await agent(messages)
            print(response.content)  # Will print the computed or retrieved answer
            ```
        """
        if self.agent_executor is None:
            raise RuntimeError("Agent not initialized")

        try:
            # Extract the last question
            last_message = messages[-1]
            if not isinstance(last_message, HumanMessage):
                logger.warning("Received non-human message, returning a default response")
                return AIMessage(content="Expected a question from a human.")

            logger.debug(f"Processing last message: {last_message.content[:100]}...")

            # Get response from model with tools
            logger.debug("Invoking model with processed message")
            try:
                response = await invoke_agent_with_retry(self.agent_executor, last_message.content)
                logger.debug("Response from model successfully received")
                return AIMessage(content=response['output'])
            except asyncio.TimeoutError:
                logger.error("Timeout occurred during model response generation")
                return AIMessage(content="I apologize, but the operation timed out. Please try again.")

        except Exception as e:
            logger.error(f"Unexpected error in agent call: {str(e)}", exc_info=True)
            return AIMessage(content=f"I encountered an error: {str(e)}")
