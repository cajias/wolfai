"""Factory for creating generic MCP servers from Python modules."""

import inspect
from collections.abc import Callable
from typing import Any

import anyio
from mcp import types
from mcp.server.lowlevel import Server

from wolfai.tools.mcp_utils import generate_from_module


PAIR_LENGTH = 2


class ModuleServer:
    """A generic MCP server that can expose any module's functions."""

    def __init__(self, module: Any, name: str, session_store: dict | None = None) -> None:
        """Initialize the server with a module to expose.

        Args:
            module: The Python module whose functions to expose
            name: Name for the server
            session_store: Optional dictionary to use for session storage
        """
        self.module = module
        tools, self.prompts = generate_from_module(module)
        self.tools  = []
        self.name = name
        self.session_store = session_store or {}
        self.function_cache = {}  # Cache function lookup
        for tool in tools:
            tool.inputSchema["properties"]["session_id"] = {
                "type": "string",
                "description": "Session identifier for state management",
                "default": "default",
            }
            self.tools.append(tool)

    def _get_function(self, name: str) -> Callable:
        """Get function from module by name."""
        if name not in self.function_cache:
            self.function_cache[name] = getattr(self.module, name)
        return self.function_cache[name]

    @staticmethod
    def _format_result(result: Any) -> list[types.TextContent]:
        """Format any result into MCP text content."""
        if isinstance(result, (list, tuple)) and len(result) == PAIR_LENGTH:
            # Handle case where function returns (result, state)
            result, _state = result

        if isinstance(result, types.TextContent):
            return [result]
        if isinstance(result, list) and all(isinstance(x, types.TextContent) for x in result):
            return result
        # Convert any other result to string representation
        return [types.TextContent(type="text", text=str(result))]

    async def handle_tool_call(self, name: str, arguments: dict) -> list[types.TextContent]:
        """Generic handler for tool calls."""
        try:
            # Extract session management
            session_id = arguments.pop("session_id", "default")

            # Get the function
            func = self._get_function(name)
            sig = inspect.signature(func)

            # Handle state if function takes state parameter
            if "state" in sig.parameters:
                state = self.session_store.get(session_id)
                if state is not None:
                    arguments["state"] = state

            # Call function
            result = func(**arguments)

            # Update session state if returned
            if isinstance(result, tuple) and len(result) == PAIR_LENGTH:
                result, new_state = result
                self.session_store[session_id] = new_state

            return self._format_result(result)

        except Exception as e:
            return [types.TextContent(type="text", text=f"Error: {e!s}")]

    def create_server(self) -> Server:
        """Create and configure the MCP server."""
        app = Server(self.name)

        @app.call_tool()
        async def tool_handler(name: str, arguments: dict) -> list[types.TextContent]:
            return await self.handle_tool_call(name, arguments)

        @app.list_tools()
        async def list_tools() -> list[types.Tool]:
            return self.tools

        return app

def run_server(
    module: Any,
    name: str | None = None,
    port: int = 8000,
    transport: str = "stdio",
    session_store: dict | None = None,
) -> None:
    """Run an MCP server for a module.

    Args:
        module: The Python module to expose
        name: Optional name for the server (defaults to module name)
        port: Port to use for SSE transport
        transport: Transport type ("stdio" or "sse")
        session_store: Optional dictionary to use for session storage
    """
    if name is None:
        name = f"mcp-{module.__name__.split('.')[-1]}"

    server = ModuleServer(module, name, session_store)
    app = server.create_server()

    if transport == "stdio":
        from mcp.server.stdio import stdio_server

        async def arun() -> None:
            async with stdio_server() as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options(),
                )

        anyio.run(arun)
    else:
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route

        sse = SseServerTransport("/messages/")

        async def handle_sse(request) -> None:
            async with sse.connect_sse(
                request.scope, request.receive, request._send,
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options(),
                )

        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        import uvicorn
        uvicorn.run(starlette_app, host="0.0.0.0", port=port)

