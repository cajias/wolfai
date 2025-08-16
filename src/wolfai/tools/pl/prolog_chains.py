"""MCP prompt chain for natural language to Prolog reasoning."""

from src.wolfai.tools.mcp_utils import MCPPrompt, prompt
from mcp import types


@prompt(name="prolog-reasoning")
def create_prolog_chain_prompt() -> MCPPrompt:
    """Create a prompt chain that converts NL to Prolog and executes it."""
    return MCPPrompt(
        name="prolog-reasoning",
        description="Answer questions by converting them to Prolog and executing the logic",
        arguments=[
            types.PromptArgument(
                name="question",
                description="Natural language question to answer",
                required=True
            )
        ],
        messages=[
            # Initial system instruction as assistant message
            types.PromptMessage(
                role="assistant",
                content=types.TextContent(
                    type="text",
                    text="I will help answer questions by converting them to Prolog code and executing it."
                )
            ),
            # Example interaction
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text="If all humans are mortal and Socrates is human, is Socrates mortal?"
                )
            ),
            types.PromptMessage(
                role="assistant",
                content=types.TextContent(
                    type="text",
                    text="Let me convert this to Prolog code:\n\nhuman(socrates).\nmortal(X) :- human(X).\n?- mortal(socrates)."
                )
            ),
            # Example execution result
            types.PromptMessage(
                role="assistant",
                content=types.TextContent(
                    type="text",
                    text="The execution shows that Socrates is indeed mortal, as this follows from our rules."
                )
            ),
            # Handle the actual question
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text="{question}"
                )
            ),
            # Conversion result
            types.PromptMessage(
                role="assistant",
                content=types.TextContent(
                    type="text",
                    text="I'll convert this to Prolog:\n\n{generated_prolog}"
                )
            ),
            # Execution result
            types.PromptMessage(
                role="assistant",
                content=types.TextContent(
                    type="text",
                    text="Based on the Prolog execution: {execution_result}"
                )
            ),
            # Final interpretation
            types.PromptMessage(
                role="assistant",
                content=types.TextContent(
                    type="text",
                    text="{interpretation}"
                )
            )
        ]
    )


@prompt(name="convert-to-prolog")
def create_converter_prompt() -> MCPPrompt:
    """Prompt specifically for the NL to Prolog conversion step."""
    return MCPPrompt(
        name="convert-to-prolog",
        description=""""Convert the following question into a Prolog program.
        Include any necessary facts and rules, and end with a query that would answer the question.""",
        arguments=[
            types.PromptArgument(
                name="question",
                description="Question to convert to Prolog",
                required=True
            )
        ],
        messages=[
            # Instructions as assistant message
            types.PromptMessage(
                role="assistant",
                content=types.TextContent(
                    type="text",
                    text="I will convert your question into valid Prolog code with necessary facts and rules."
                )
            ),
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text="{question}"
                )
            )
        ]
    )


@prompt(name="interpret-results")
def create_interpreter_prompt() -> MCPPrompt:
    """Prompt for interpreting Prolog results back to natural language."""
    return MCPPrompt(
        name="interpret-results",
        description="Interpret Prolog execution results",
        arguments=[
            types.PromptArgument(
                name="question",
                description="Original question",
                required=True
            ),
            types.PromptArgument(
                name="prolog_code",
                description="Generated Prolog code",
                required=True
            ),
            types.PromptArgument(
                name="results",
                description="Execution results",
                required=True
            )
        ],
        messages=[
            # Instructions as assistant message
            types.PromptMessage(
                role="assistant",
                content=types.TextContent(
                    type="text",
                    text="I will interpret the Prolog execution results in the context of your question."
                )
            ),
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text="Question: {question}\nProlog Code:\n{prolog_code}\nResults:\n{results}"
                )
            )
        ]
    )
