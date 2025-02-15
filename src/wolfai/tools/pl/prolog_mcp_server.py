"""MCP server for the Prolog module with integrated prompts."""
import asyncio
from typing import Dict, List, Optional, Any
import click
from mcp.server.fastmcp import FastMCP
import swiplserver
from contextlib import asynccontextmanager


class PrologMCPServer:
    """A Model Context Protocol server for Prolog integration."""

    def __init__(self):
        """Initialize the Prolog server."""
        self._prolog = None
        self._mqi = None
        self._initialized = False

    async def __aenter__(self):
        """Async context manager entry."""
        if not self._initialized:
            await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

    async def initialize(self):
        """Initialize Prolog connections.
        
        Raises:
            Exception: If Prolog initialization fails
        """
        if self._initialized:
            return
            
        try:
            self._mqi = swiplserver.PrologMQI()
            self._prolog = self._mqi.create_thread()
            self._initialized = True
        except Exception as e:
            raise Exception(f"Failed to initialize Prolog: {str(e)}")

    async def cleanup(self):
        """Clean up Prolog resources.
        
        This method suppresses any cleanup errors to ensure graceful shutdown.
        """
        if self._prolog:
            try:
                self._prolog.stop()
            except Exception:
                pass  # Suppress cleanup errors
            finally:
                self._prolog = None
                
        if self._mqi:
            try:
                self._mqi.stop()
            except Exception:
                pass  # Suppress cleanup errors
            finally:
                self._mqi = None
                
        self._initialized = False

    async def consult(self, code: str) -> Dict[str, Any]:
        """Load Prolog code into the knowledge base.
        
        Args:
            code: Prolog code to load
            
        Returns:
            Dict containing success status and any error message
            
        Raises:
            AttributeError: If server not initialized
        """
        if not self._initialized or not self._prolog:
            raise AttributeError("Prolog server not initialized")
            
        if not isinstance(code, str):
            raise AttributeError("Code must be a string")

        try:
            # Clean and process the code
            code = code.strip()
            if not code:
                return {"success": False, "error": "Empty code", "solutions": []}

            # Execute the code
            self._prolog.query(code)
            return {"success": True, "error": None, "solutions": [{}]}

        except swiplserver.PrologError as e:
            return {"success": False, "error": str(e), "solutions": []}
        except Exception as e:
            return {"success": False, "error": f"Execution error: {str(e)}", "solutions": []}

    async def query(self, query: str) -> Dict[str, Any]:
        """Execute a Prolog query.
        
        Args:
            query: Prolog query to execute
            
        Returns:
            Dict containing results and status
            
        Raises:
            AttributeError: If server not initialized or query invalid
        """
        if not self._initialized or not self._prolog:
            raise AttributeError("Prolog server not initialized")
            
        if not isinstance(query, str):
            raise AttributeError("Query must be a string")

        try:
            # Clean and process the query
            query = query.strip()
            if not query:
                return {"success": False, "error": "Empty query", "solutions": []}

            # Execute query and get solutions
            solutions = self._prolog.query(query)
            return {
                "success": True,
                "error": None,
                "solutions": solutions if solutions else []
            }

        except swiplserver.PrologError as e:
            return {"success": False, "error": str(e), "solutions": []}
        except Exception as e:
            return {"success": False, "error": f"Execution error: {str(e)}", "solutions": []}


@asynccontextmanager
async def create_server_context():
    """Create a context manager for the Prolog server lifecycle."""
    server = PrologMCPServer()
    try:
        await server.initialize()
        yield server
    finally:
        await server.cleanup()


async def create_prolog_server() -> FastMCP:
    """Create and configure a FastMCP server with Prolog integration.
    
    Returns:
        Configured FastMCP server instance
    """
    mcp = FastMCP("Prolog MCP Server")
    
    # Create Prolog server instance
    prolog_server = PrologMCPServer()
    await prolog_server.initialize()
    
    # Register tools
    @mcp.tool()
    async def consult(code: str) -> Dict[str, Any]:
        """Load Prolog code into the knowledge base."""
        return await prolog_server.consult(code)

    @mcp.tool()
    async def query(query: str) -> Dict[str, Any]:
        """Execute a Prolog query."""
        return await prolog_server.query(query)

    # Store cleanup handler for later use
    async def cleanup():
        await prolog_server.cleanup()
    
    # Attach cleanup to FastMCP instance
    setattr(mcp, '_cleanup_handler', cleanup)
    
    return mcp


def main():
    """Run the Prolog MCP server."""
    async def _run_server(port: int, transport: str) -> int:
        mcp = await create_prolog_server()
        
        try:
            if transport == "sse":
                await mcp.serve_sse(port=port)
            else:
                await mcp.serve_stdio()
        finally:
            if hasattr(mcp, '_cleanup_handler'):
                await mcp._cleanup_handler()
                
        return 0

    @click.command()
    @click.option("--port", default=8000, help="Port to listen on for SSE")
    @click.option(
        "--transport",
        type=click.Choice(["stdio", "sse"]),
        default="stdio",
        help="Transport type",
    )
    def cli(port: int, transport: str):
        asyncio.run(_run_server(port, transport))

    cli()