"""MCP prompt chain for natural language to Prolog reasoning."""

from src.wolfai.tools.mcp_utils import MCPPrompt, prompt
import mcp.types as types


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
            # Initial system instruction
            types.PromptMessage(
                role="system",
                content=types.TextContent(
                    type="text",
                    text="You will help answer questions by converting them to Prolog code and executing it."
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
            # Execute the example
            types.PromptMessage(
                role="function",
                function={
                    "name": "consult",
                    "arguments": {
                        "code": "human(socrates).\nmortal(X) :- human(X).\n?- mortal(socrates)."
                    }
                }
            ),
            types.PromptMessage(
                role="assistant",
                content=types.TextContent(
                    type="text",
                    text="Based on the Prolog execution, yes, Socrates is mortal. This follows from our rules that all humans are mortal and Socrates is human."
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
            # Assistant converts to Prolog
            types.PromptMessage(
                role="assistant",
                content=types.FunctionCallContent(
                    type="function_call",
                    function_call={
                        "name": "convert_to_prolog",
                        "arguments": {
                            "question": "{question}"
                        }
                    }
                )
            ),
            # Execute the generated Prolog
            types.PromptMessage(
                role="function",
                function={
                    "name": "consult",
                    "arguments": {
                        "code": "{generated_prolog}"
                    }
                }
            ),
            # Final interpretation
            types.PromptMessage(
                role="assistant",
                content=types.TextContent(
                    type="text",
                    text="Based on the Prolog execution results, let me explain the answer: {interpretation}"
                )
            )
        ]
    )


@prompt(name="convert-to-prolog")
def create_converter_prompt() -> MCPPrompt:
    """Prompt specifically for the NL to Prolog conversion step."""
    return MCPPrompt(
        name="convert-to-prolog",
        description="Convert natural language to Prolog code",
        arguments=[
            types.PromptArgument(
                name="question",
                description="Question to convert to Prolog",
                required=True
            )
        ],
        messages=[
            types.PromptMessage(
                role="system",
                content=types.TextContent(
                    type="text",
                    text="Convert the question into valid Prolog code. Include necessary facts and rules, ending with a query."
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
            types.PromptMessage(
                role="system",
                content=types.TextContent(
                    type="text",
                    text="Interpret the Prolog execution results in the context of the original question."
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
