"""MCP prompt chain for natural language to Prolog reasoning."""

from mcp import types

from src.wolfai.tools.mcp_utils import MCPPrompt, create_text_message, prompt


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
                required=True,
            ),
        ],
        messages=[
            # Initial system instruction as assistant message
            create_text_message(
                "assistant",
                "I will help answer questions by converting them to Prolog code and executing it.",
            ),
            # Example interaction
            create_text_message(
                "user",
                "If all humans are mortal and Socrates is human, is Socrates mortal?",
            ),
            create_text_message(
                "assistant",
                "Let me convert this to Prolog code:\n\nhuman(socrates).\nmortal(X) :- human(X).\n?- mortal(socrates).",
            ),
            # Example execution result
            create_text_message(
                "assistant",
                "The execution shows that Socrates is indeed mortal, as this follows from our rules.",
            ),
            # Handle the actual question
            create_text_message("user", "{question}"),
            # Conversion result
            create_text_message("assistant", "I'll convert this to Prolog:\n\n{generated_prolog}"),
            # Execution result
            create_text_message("assistant", "Based on the Prolog execution: {execution_result}"),
            # Final interpretation
            create_text_message("assistant", "{interpretation}"),
        ],
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
                required=True,
            ),
        ],
        messages=[
            # Instructions as assistant message
            create_text_message(
                "assistant",
                "I will convert your question into valid Prolog code with necessary facts and rules.",
            ),
            create_text_message("user", "{question}"),
        ],
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
                required=True,
            ),
            types.PromptArgument(
                name="prolog_code",
                description="Generated Prolog code",
                required=True,
            ),
            types.PromptArgument(
                name="results",
                description="Execution results",
                required=True,
            ),
        ],
        messages=[
            # Instructions as assistant message
            create_text_message(
                "assistant",
                "I will interpret the Prolog execution results in the context of your question.",
            ),
            create_text_message(
                "user",
                "Question: {question}\nProlog Code:\n{prolog_code}\nResults:\n{results}",
            ),
        ],
    )
