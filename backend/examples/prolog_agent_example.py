"""Example usage of the Prolog agent.

This script demonstrates how to use the PrologAgent for integrating natural language queries
with a Prolog reasoning engine. It uses LangChain's framework for connecting a language model
to a Prolog MCP server, enabling the execution of Prolog logic statements derived from natural language.

Key functionalities:
- Loads environment variables required for API keys and configurations.
- Configures and logs system parameters for debugging and monitoring.
- Initializes a Prolog MCP server for handling logical operations.
- Creates and sets up a ChatOpenAI-based model, integrating it with the PrologAgent.
- Demonstrates an example Prolog query, showing how the agent works in practice.
"""

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from mcp import StdioServerParameters

from wolfai.agents import PrologAgent

# Configure logging to track execution details
logging.basicConfig(
    level=logging.DEBUG,  # Set logging level to DEBUG for detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Log format
    stream=sys.stdout  # Output logs to standard output
)
logger = logging.getLogger(__name__)  # Create a logger instance for the script


async def main():
    """
    Main entry point for demonstrating the usage of the PrologAgent.

    This function performs the following tasks:
    1. Loads environment variables for system configuration.
    2. Initializes the Prolog MCP server parameters.
    3. Creates and configures a ChatOpenAI-based language model.
    4. Initializes the PrologAgent with the model and server parameters.
    5. Runs a Prolog query example to demonstrate agent functionality.
    """
    load_dotenv()  # Load environment variables from a .env file

    # Set up Prolog MCP server parameters
    server_params = StdioServerParameters(
        command=sys.executable,  # Use the current Python executable
        args=["-m", "wolfai.tools.pl.prolog_mcp_server"]  # Module to start the Prolog MCP server
    )

    # Configure a ChatOpenAI model with the required API key and settings
    model = ChatOpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),  # API key loaded from the environment
        model="gpt-3.5-turbo",  # Specify the language model to use
        timeout=30.0  # Set a timeout for model responses
    )

    # Initialize the PrologAgent with the Prolog server and language model
    agent = PrologAgent(model, server_params)
    await agent.initialize()  # Perform necessary asynchronous initialization

    try:
        # Define an example natural language query to be converted into Prolog
        messages = [
            HumanMessage(content=(
                "Can you help me solve this problem in Prolog? "
                "I need to check if Socrates is mortal, given that "
                "all humans are mortal and Socrates is human."
            ))
        ]

        # Execute the query using the PrologAgent and retrieve the response
        response = await agent(messages)
        print(f"\nResponse: {response.content}")  # Output the agent's response to the console

    except Exception as e:
        # Log any errors encountered during execution
        logger.error(f"Error during execution: {e}", exc_info=True)


if __name__ == "__main__":
    # Run the main function within an asyncio event loop
    asyncio.run(main())
