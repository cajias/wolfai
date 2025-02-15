import logging
from typing import Type, Dict, Any

from langchain_core.tools import StructuredTool
from mcp import ClientSession
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

    schema_map = {
        "run_query": RunQueryInput,
        "consult": ConsultInput,
        "parse_prolog_code": ParsePrologInput,
    }

    def create_tool(tool):
        # If there's no schema for this tool, skip it
        if tool.name not in schema_map:
            logging.error(f"Skipping tool {tool.name}: missing schema definition.")
            return None

        # Use **kwargs so the function accepts any named args (e.g. prolog=..., query=...)
        async def tool_function(**kwargs: Dict[str, Any]):
            # The kwargs dict will contain 'prolog', 'query', etc.
            # Pass these arguments on to your MCP tool call
            return await session.call_tool(tool.name, kwargs)

        return StructuredTool(
            name=tool.name,
            description=tool.description or f"{tool.name} tool",
            func=tool_function,
            args_schema=schema_map[tool.name],
        )

    structured_tools = [create_tool(tool) for tool in tools.tools]
    return [t for t in structured_tools if t is not None]
