import asyncio
import logging
from typing import Type, Any, Dict

from langchain_core.tools import StructuredTool
from mcp import ClientSession, types as mcp_types
from pydantic import BaseModel, create_model


def schema_to_pydantic(name: str, schema: dict) -> Type:
    """Convert an MCP tool's inputSchema to a Pydantic model."""
    fields = {}

    if not schema:  # Ensure schema exists
        return create_model(name)  # Create an empty schema if none is provided

    for param_name, param_info in schema.get("properties", {}).items():
        field_type = str  # Default type

        if param_info.get("type") == "integer":
            field_type = int
        elif param_info.get("type") == "number":
            field_type = float
        elif param_info.get("type") == "boolean":
            field_type = bool

        # Handle required vs. optional fields
        if "required" in schema and param_name in schema["required"]:
            fields[param_name] = (field_type, ...)
        else:
            fields[param_name] = (field_type, None)

    return create_model(name, **fields)

class RunQueryInput(BaseModel):
    """Schema for run_query tool input."""
    prolog: str
    query: str
    namespace: str

class ConsultInput(BaseModel):
    """Schema for consult tool input."""
    code: str
    session_id: str = None

class ParsePrologInput(BaseModel):
    """Schema for parse_prolog_code tool input."""
    code: str
    session_id: str = None


async def get_mcp_tools_as_langchain(session: ClientSession) -> list[StructuredTool]:
    """Fetch MCP tools and convert them to LangChain StructuredTools."""
    tools = await session.list_tools()

    def create_tool(tool: mcp_types.Tool):

        # Use **kwargs so the function accepts any named args (e.g. prolog=..., query=...)
        async def tool_function_sync(*args: Any, **kwargs: Any) -> mcp_types.CallToolResult:
            """
            A synchronous function that:
              - Accepts unlimited positional args (*args)
              - Accepts unlimited keyword args (**kwargs)
              - Merges them into a final dictionary
              - Uses the tool's schema to decide how to handle the positional args
              - Calls an async function with asyncio.run()

            Returns:
              The result of calling the MCP tool with the merged arguments.
            """
            schema = tool.inputSchema or {}
            required_fields = schema.get("required", [])
            props = schema.get("properties", {})

            # Start with the named (keyword) arguments
            final_args = {k:v for k, v in kwargs.items()}

            # If the user provided positional arguments, decide how to handle them:
            if args:
                # 1) If there's exactly one required field in the schema, store *args under that field
                if len(required_fields) == 1:
                    field_name = required_fields[0]

                    # If that field is not in 'props', fallback or just assume it
                    if field_name not in props:
                        logging.warning(f"Field '{field_name}' not found in properties. Using anyway.")

                    # If there's exactly one positional argument, store it directly
                    # If there's multiple, store them as a list, or handle them differently
                    if len(args) == 1:
                        final_args[field_name] = args[0]
                    else:
                        # If you want to store multiple positional arguments as a list
                        final_args[field_name] = list(args)

                # 2) If there's a single property but not necessarily 'required'
                elif len(props) == 1:
                    (single_prop,) = props.keys()
                    if len(args) == 1:
                        final_args[single_prop] = args[0]
                    else:
                        final_args[single_prop] = list(args)

                # 3) Otherwise, store them in a fallback 'positional' key
                else:
                    # We put all *args in a separate key named e.g. "positional"
                    final_args["positional"] = list(args)

            result = asyncio.run(session.call_tool(tool.name, final_args)).result()
            return result

        dynamic_tool_schema = create_pydantic_model(f"{tool.name.capitalize()}ToolSchema", dict(tool.inputSchema["properties"]))
        return StructuredTool(
            name=tool.name,
            description=tool.description or f"{tool.name} tool",
            func=tool_function_sync,
            args_schema =dynamic_tool_schema,
        )

    structured_tools = [create_tool(tool) for tool in tools.tools]
    return [t for t in structured_tools if t is not None]


JSON_TYPE_MAPPING = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list,
    "object": dict
}


def create_pydantic_model(name: str, schema: Dict[str, Any]) -> Type[BaseModel]:
    """Dynamically creates a Pydantic model class from a dictionary schema, supporting multiple types."""
    fields = {}

    for key, value in schema.items():
        if value is None:
            continue  # Skip None values

        # Get type from mapping or fallback to Any
        field_type = JSON_TYPE_MAPPING.get(value.get("type"), Any)

        # Handle default values if they exist in the schema
        if "default" in value:
            fields[key] = (field_type, value["default"])
        else:
            fields[key] = (field_type, ...)

    return create_model(name, **fields)
