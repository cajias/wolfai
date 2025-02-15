from typing import List, Type
from pydantic import create_model
from langchain.tools import Tool
from mcp import ClientSession


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


async def get_mcp_tools_as_langchain(session: ClientSession) -> List[Tool]:
    """Fetch MCP tools and convert them to LangChain tools with correct input schemas."""
    tools = await session.list_tools()
    langchain_tools = []

    for tool in tools.tools:
        if not tool.inputSchema:
            continue  # Skip tools without an input schema

        pydantic_model = schema_to_pydantic(tool.name, tool.inputSchema)

        async def async_func(args, tool_name=tool.name):
            return await session.call_tool(tool_name, args)

        langchain_tool = Tool(
            name=tool.name,
            func=async_func,  # ✅ Async function instead of lambda
            description=tool.description,
            args_schema=pydantic_model  # ✅ Explicitly define args_schema
        )

        langchain_tools.append(langchain_tool)

    return langchain_tools
