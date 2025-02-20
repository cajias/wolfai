# mcp_langchain_tools.py
import asyncio
import logging
from typing import List, Any

from langchain_core.tools import StructuredTool
from mcp import ClientSession
from mcp.types import CallToolResult,Tool



async def get_mcp_tools_as_langchain(session: ClientSession) -> List[StructuredTool]:
    """
    Fetch MCP tools from session and convert them to LangChain StructuredTools.
    """
    # 1. Fetch raw MCP tools
    raw_tools = await session.list_tools()

    # 2. Build a known schema map
    schema_map = {
        "run_query": RunQueryInput,
        "consult": ConsultInput,
        "parse_prolog_code": ParsePrologInput,
    }

    # 3. For each tool definition, build a structured tool
    structured_tools = [create_structured_tool(tool,session, schema_map) for tool in raw_tools.tools]
    return [t for t in structured_tools if t is not None]

def create_structured_tool(
    tool: Tool,
    session,
) -> StructuredTool | None:
    """
    Create a StructuredTool from an MCP tool definition,
    using the known schema_map for type-checking.
    """
    if tool.name not in schema_map:
        logging.error(f"Skipping tool {tool.name}: missing schema definition.")
        return None

    async def tool_function_sync(*args: Any, **kwargs: Any) -> CallToolResult:
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
        final_args = {k: v for k, v in kwargs.items()}

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

    return StructuredTool(
        name=tool.name,
        description=tool.description or f"{tool.name} tool",
        func=tool_function_sync,
        args_schema=schema_map[tool.name],
    )
