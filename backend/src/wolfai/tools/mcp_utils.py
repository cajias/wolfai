"""Utilities for MCP tool and prompt generation and inspection."""
import inspect
import typing
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Callable, Optional, get_args, get_origin

import docstring_parser
from mcp import types


PAIR_LENGTH = 2


@dataclass
class MCPPrompt:
    """Container for MCP prompt definition with messages."""
    name: str
    description: str
    arguments: list[types.PromptArgument]
    messages: list[types.PromptMessage]


def create_text_message(role: str, text: str) -> types.PromptMessage:
    """Create a PromptMessage with text content.

    Args:
        role: Message role ("user", "assistant", or "system")
        text: Text content of the message

    Returns:
        PromptMessage with TextContent
    """
    return types.PromptMessage(
        role=role,
        content=types.TextContent(
            type="text",
            text=text,
        ),
    )


def generate_example_value(annotation: Any) -> Any:
    """Generate a representative example value for a type."""
    if get_origin(annotation) is typing.Union and type(None) in get_args(annotation):
        annotation = next(arg for arg in get_args(annotation) if arg is not type(None))

    type_examples = {
        str: "example_text",
        int: 42,
        float: 3.14,
        bool: True,
        datetime: "2024-02-14T12:00:00",
        date: "2024-02-14",
    }

    if annotation in type_examples:
        return type_examples[annotation]

    if get_origin(annotation) is list:
        if get_args(annotation):
            inner_type = get_args(annotation)[0]
            return [generate_example_value(inner_type)]
        return ["example_item"]

    if get_origin(annotation) is dict:
        args = get_args(annotation)
        if len(args) == PAIR_LENGTH:
            key_type, value_type = args
            return {str(generate_example_value(key_type)): generate_example_value(value_type)}
        return {"key": "value"}

    return "example_value"


def get_type_validation_rules(annotation: Any) -> dict[str, Any]:
    """Extract validation rules from type hints."""
    # Mapping of basic types to JSON schema
    type_mapping = {
        int: {"type": "number", "format": "integer"},
        float: {"type": "number"},
        str: {"type": "string"},
        bool: {"type": "boolean"},
        datetime: {"type": "string", "format": "date-time", "pattern": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$"},
        date: {"type": "string", "format": "date", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
    }

    # Return basic type schema if available
    if annotation in type_mapping:
        return type_mapping[annotation]

    # Handle List types
    if get_origin(annotation) is list:
        inner_type = get_args(annotation)[0] if get_args(annotation) else str
        return {"type": "array", "items": get_type_validation_rules(inner_type)}

    # Handle Dict types (only string keys)
    if get_origin(annotation) is dict:
        value_type = get_args(annotation)[1] if len(get_args(annotation)) == PAIR_LENGTH else Any
        return {"type": "object", "additionalProperties": get_type_validation_rules(value_type)}

    return {}  # Return empty schema if type is unknown

def get_parameter_schema(
    param: inspect.Parameter,
    param_doc: Optional[docstring_parser.DocstringParam] = None,
) -> dict[str, Any]:
    """Extract comprehensive JSON schema information from a parameter.

    Args:
        param: Parameter to analyze
        param_doc: Optional docstring information for the parameter

    Returns:
        JSON schema object with type information, description, and examples
    """
    annotation = param.annotation
    if annotation == inspect.Parameter.empty:
        annotation = str  # Default to string

    # Get base validation rules
    schema = get_type_validation_rules(annotation)

    # Generate example value
    example = generate_example_value(annotation)

    # Build descriptions
    descriptions = []

    # Add docstring description if available
    if param_doc and param_doc.description:
        descriptions.append(param_doc.description)

    # Add type information
    if get_origin(annotation) is typing.Union and type(None) in get_args(annotation):
        descriptions.append("This parameter is optional.")
        inner_type = next(arg for arg in get_args(annotation) if arg is not None)
        descriptions.append(f"When provided, it should be a {inner_type.__name__}.")

    # Add default value info
    if param.default is not param.empty:
        if param.default is None:
            descriptions.append("Defaults to None if not provided.")
        else:
            descriptions.append(f"Defaults to {param.default!r} if not provided.")
    else:
        descriptions.append("This parameter is required.")

    # Add example usage
    descriptions.append(f"Example value: {example!r}")

    schema["description"] = " ".join(descriptions)

    # Add example
    schema["examples"] = [example]

    # Add default if present
    if param.default is not param.empty and param.default is not None:
        schema["default"] = param.default

    return schema


def function_to_mcp_tool(func: Callable, name: Optional[str] = None) -> types.Tool:
    """Convert a Python function to an MCP tool using type hints and docstrings.

    Args:
        func: The function to convert
        name: Optional custom name for the tool

    Returns:
        An MCP Tool object with schema derived from the function's signature
    """
    # Get function signature information
    sig = inspect.signature(func)
    doc = docstring_parser.parse(func.__doc__ or "")

    # Build parameter schema
    properties = {}
    required = []

    for param_name, param in sig.parameters.items():
        # Skip self/cls for methods
        if param_name in ("self", "cls"):
            continue

        # Get parameter description from docstring
        param_doc = next((p for p in doc.params if p.arg_name == param_name), None)

        # Build parameter schema
        param_schema = get_parameter_schema(param, param_doc)
        properties[param_name] = param_schema

        # Track required parameters
        if param.default == inspect.Parameter.empty:
            required.append(param_name)

    # Create input schema
    input_schema = {
        "type": "object",
        "properties": properties,
    }
    if required:
        input_schema["required"] = required

    # Build description
    descriptions = []

    # Main description
    if doc.short_description:
        descriptions.append(doc.short_description)
    if doc.long_description:
        descriptions.append(doc.long_description)

    # Add return info
    if doc.returns:
        descriptions.append(f"Returns: {doc.returns.description}")

    # Add example if available
    if doc.examples:
        descriptions.append("Examples:")
        for example in doc.examples:
            descriptions.append(example.description)

    # Create MCP tool
    tool_name = name or func.__name__
    return types.Tool(
        name=tool_name,
        description="\n\n".join(descriptions) or f"Execute {tool_name}",
        inputSchema=input_schema,
    )


def generate_tools_from_module(
    module: Any,
    *,
    include_private: bool = False,
    exclude: Optional[list[str]] = None,
) -> list[types.Tool]:
    """Generate MCP tools from all callable objects in a module.

    Args:
        module: Module or object containing callables.
        include_private: Whether to include private functions (prefixed with `_`).
        exclude: Optional list of function names to exclude.

    Returns:
        A list of generated Tool objects.
    """
    tools: list[types.Tool] = []
    exclude = set(exclude or [])

    for attr_name in dir(module):
        if attr_name in exclude:
            continue
        if not include_private and attr_name.startswith("_"):
            continue

        attr = getattr(module, attr_name)
        if callable(attr):
            try:
                tools.append(function_to_mcp_tool(attr, name=attr_name))
            except Exception:
                continue

    return tools


def function_to_mcp_prompt(func: Callable) -> types.Prompt:
    """Convert a Python function to an MCP prompt using type hints and docstrings.

    Args:
        func: Function that returns an MCPPrompt

    Returns:
        MCP Prompt object with schema derived from the function
    """
    sig = inspect.signature(func)
    doc = docstring_parser.parse(func.__doc__ or "")

    # Execute function to get MCPPrompt definition
    prompt_def = func()
    if not isinstance(prompt_def, MCPPrompt):
        msg = f"Function {func.__name__} must return MCPPrompt"
        raise ValueError(msg)

    # Build arguments from both signature and docstring
    arguments = []
    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue

        # Get parameter description from docstring
        param_doc = next((p for p in doc.params if p.arg_name == param_name), None)

        argument = types.PromptArgument(
            name=param_name,
            description=param_doc.description if param_doc else "",
            required=param.default == inspect.Parameter.empty,
        )
        arguments.append(argument)

    return types.Prompt(
        name=prompt_def.name or func.__name__,
        description=doc.short_description or "",
        arguments=arguments,
    )


def prompt(func: Optional[Callable] = None, *, name: Optional[str] = None):
    """Decorator to mark and configure functions as MCP prompts.

    Can be used as @prompt or @prompt(name="custom_name")
    """

    def decorator(f: Callable) -> Callable:
        f._is_mcp_prompt = True
        if name:
            f._mcp_prompt_name = name
        return f

    if func is None:
        return decorator
    return decorator(func)

def tool(func: Optional[Callable] = None, *, name: Optional[str] = None):
    """Decorator to mark and configure functions as MCP tool.

    Can be used as @tool or @prompt(name="custom_name")
    """

    def decorator(f: Callable) -> Callable:
        f._is_mcp_tool = True
        if name:
            f._mcp_tool_name = name
        return f

    if func is None:
        return decorator
    return decorator(func)


def generate_prompts_from_module(
    module: Any,
    include_private: bool = False,
    exclude: Optional[list[str]] = None,
) -> list[types.Prompt]:
    """Generate MCP prompts from all suitable functions in a module."""
    exclude = exclude or []
    prompts = []

    for name, obj in inspect.getmembers(module):
        # Skip if in exclude list
        if name in exclude:
            continue

        # Skip private functions unless explicitly included
        if not include_private and name.startswith("_"):
            continue

        # Check if it's a prompt function (either by decorator or return type)
        if not is_mp_prompt_type(obj):
            continue

        try:
            prompt = function_to_mcp_prompt(obj)
            # Override name if specified in decorator
            if hasattr(obj, "_mcp_prompt_name"):
                prompt.name = obj._mcp_prompt_name
            prompts.append(prompt)
        except Exception as e:
            print(f"Warning: Could not convert {name} to prompt: {e}")

    return prompts


def is_mp_prompt_type(obj):
    return (
        hasattr(obj, "_is_mcp_prompt") or
        (inspect.isfunction(obj) and
         obj.__annotations__.get("return") == MCPPrompt)
    )

def is_mp_tool_type(obj):
    return (
        hasattr(obj, "_is_mcp_tool") or
        (inspect.isfunction(obj) and obj.__annotations__.get("return") != MCPPrompt)
    )


def generate_from_module(
    module: Any,
    include_private: bool = False,
    exclude: Optional[list[str]] = None,
) -> tuple[list[types.Tool], list[types.Prompt]]:
    """Generate both MCP tools and prompts from a module."""
    tools = [function_to_mcp_tool(obj) for _, obj in inspect.getmembers(module, is_mp_tool_type)]
    prompts = [function_to_mcp_prompt(obj) for _, obj in inspect.getmembers(module, is_mp_prompt_type)]
    return tools, prompts
