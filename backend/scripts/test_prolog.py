"""Test script for Prolog agent."""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from mcp import StdioServerParameters
from src.wolfai.agents.prolog import create_prolog_agent

# Load environment variables
load_dotenv()

def run_test():
    import asyncio
    
    async def _run_test():
        if not os.getenv("OPENAI_API_KEY"):
            print("Error: OPENAI_API_KEY not found in environment")
            return
        
        print("Starting Prolog test...")
        
        try:
            # Set up server parameters
            server_params = StdioServerParameters(
                command="python",
                args=["-m", "src.wolfai.tools.pl.prolog_mcp_server"],
                env=None
            )

            # Create language model
            print("Creating ChatOpenAI instance...")
            model = ChatOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                model="gpt-4-0125-preview",  # Using a specific model version
                temperature=0  # Use deterministic outputs for testing
            )

            print("Creating Prolog agent...")
            agent = await create_prolog_agent(model, server_params)
            
            print("Testing agent with sample query...")
            messages = [HumanMessage(content="If all humans are mortal and Socrates is human, is Socrates mortal?")]
            response = await agent(messages)
            print("\nResponse:")
            print(response.content)
            
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            raise e

    return asyncio.run(_run_test())

if __name__ == "__main__":
    print("Starting test script...")
    run_test()