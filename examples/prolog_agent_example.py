"""Example usage of the Prolog agent."""

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from src.wolfai.agents.prolog import create_prolog_agent

# Load environment variables (for API keys)
load_dotenv()


def main():
    """Run the Prolog agent example."""
    # Connect to MCP server
    client = Client("http://localhost:8000")
    prolog_tool = client.get_tool("consult")

    # Create language model
    model = ChatOpenAI()

    # Create agent
    agent = create_prolog_agent(model, prolog_tool)

    # Example questions
    questions = [
        "If all humans are mortal and Socrates is human, is Socrates mortal?",
        "If birds can fly, and penguins are birds but cannot fly, and tweety is a penguin, can tweety fly?",
        "If Alice likes Bob, and Bob likes Carol, and Carol likes David, who does Bob like?"
    ]

    # Process each question
    for question in questions:
        print(f"\nQuestion: {question}")
        messages = [HumanMessage(content=question)]

        # Get response with debug info
        response = agent(messages, config={"debug": True})
        print("\nResponse:")
        print(response.content)
        print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
